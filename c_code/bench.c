#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <time.h>
#include <sched.h>
#include <unistd.h>
#include <sys/syscall.h>
#include <linux/perf_event.h>
#include "gf2m.h"

#if defined(__clang__)
#  define COMPILER "clang " __clang_version__
#else
#  define COMPILER "gcc " __VERSION__
#endif
#ifndef BUILD_FLAGS
#  define BUILD_FLAGS "(not recorded: build with the Makefile)"
#endif

typedef void (*bin_t)(uint64_t*, const uint64_t*, const uint64_t*);
typedef void (*un_t )(uint64_t*, const uint64_t*);

typedef struct {
  const char *name; int m, W, ne, e[3];
  bin_t mul; un_t sqr, red; int gates;
} field_t;

static const field_t F[] = {
 {"128 GCM",                 128,2,3,{1,2,7},      mul2,sqr2,red_128_gcm,        0},
 {"163 second(71,46) COMB",  163,3,3,{46,71,117},  mul3,sqr3,red_163_s7146,    440},
 {"163 second(71,46) fold",  163,3,3,{46,71,117},  mul3,sqr3,red_163_s7146_f,  440},
 {"163 first(63,37)",        163,3,3,{37,63,100},  mul3,sqr3,red_163_f6337,    487},
 {"163 first(74,15)",        163,3,3,{15,74,89},   mul3,sqr3,red_163_f7415,    487},
 {"163 NIST",                163,3,3,{3,6,7},      mul3,sqr3,red_163_nist,     571},
 {"233 trinomial(74)",       233,4,1,{74,0,0},     mul4,sqr4,red_233_t74,      464},
 {"233 second(83,75) COMB",  233,4,3,{75,83,158},  mul4,sqr4,red_233_s8375,    621},
 {"283 NIST",                283,5,3,{5,7,12},     mul5,sqr5,red_283_nist,     862},
 {"283 first(111,61)",       283,5,3,{61,111,172}, mul5,sqr5,red_283_f11161,   847},
 {"409 trinomial(87)",       409,7,1,{87,0,0},     mul7,sqr7,red_409_t87,      816},
 {"409 second(179,115) COMB",409,7,3,{115,179,294},mul7,sqr7,red_409_s179115, 1109},
 {"571 second(207,182) COMB",571,9,3,{182,207,389},mul9,sqr9,red_571_s207182, 1528},
 {"571 second(207,182) fold",571,9,3,{182,207,389},mul9,sqr9,red_571_s207182_f,1528},
 {"571 second(359,106) COMB",571,9,3,{106,359,465},mul9,sqr9,red_571_s359106, 1604},
 {"571 second(527,22) COMB", 571,9,3,{22,527,549}, mul9,sqr9,red_571_s52722,  1688},
 {"571 second(527,22) fold", 571,9,3,{22,527,549}, mul9,sqr9,red_571_s52722_f,1688},
 {"571 first(218,135)",      571,9,3,{135,218,353},mul9,sqr9,red_571_f218135, 1711},
 {"571 NIST",                571,9,3,{2,5,10},     mul9,sqr9,red_571_nist,    2003},
};
#define NF ((int)(sizeof F / sizeof F[0]))

/* ---------- independent bitwise reference ---------- */
static void ref_mod(uint64_t *r, const uint64_t *acc, int m, const uint64_t *f){
  uint64_t t[PL]; memcpy(t,acc,sizeof t);
  for(int d=2*m-2; d>=m; d--)
    if((t[d>>6]>>(d&63))&1)
      for(int k=0;k<=m;k++)
        if((f[k>>6]>>(k&63))&1){ int j=d-m+k; t[j>>6]^=1ULL<<(j&63); }
  for(int i=0;i<EL;i++) r[i]=0;
  memcpy(r,t,(size_t)((m+63)/64)*8);
}
static void ref_mulmod(uint64_t *r,const uint64_t*a,const uint64_t*b,int m,const uint64_t*f){
  uint64_t acc[PL]; memset(acc,0,sizeof acc);
  for(int i=0;i<m;i++) if((a[i>>6]>>(i&63))&1)
    for(int j=0;j<m;j++) if((b[j>>6]>>(j&63))&1){ int k=i+j; acc[k>>6]^=1ULL<<(k&63); }
  ref_mod(r,acc,m,f);
}
static void build_f(uint64_t *f, const field_t *fl){
  memset(f,0,PL*8);
  f[fl->m>>6] |= 1ULL<<(fl->m&63);
  f[0] |= 1;
  for(int i=0;i<fl->ne;i++) f[fl->e[i]>>6] |= 1ULL<<(fl->e[i]&63);
}

/* ---------- rng / timing ---------- */
static uint64_t rs = 0x243F6A8885A308D3ULL;
AI uint64_t rnd(void){ rs^=rs<<13; rs^=rs>>7; rs^=rs<<17; return rs; }
static void rfe(uint64_t *a,int m,int W){
  for(int i=0;i<EL;i++) a[i]=0;
  for(int i=0;i<W;i++)  a[i]=rnd();
  a[W-1] &= topmask((unsigned)m);
}
static volatile uint64_t sink;
AI uint64_t tsc0(void){
  unsigned a,d;
  __asm__ __volatile__("lfence\n\trdtsc":"=a"(a),"=d"(d)::"memory");
  return ((uint64_t)d<<32)|a;
}
AI uint64_t tsc1(void){
  unsigned a,d,c;
  __asm__ __volatile__("rdtscp":"=a"(a),"=d"(d),"=c"(c)::"memory");
  __asm__ __volatile__("lfence":::"memory");
  return ((uint64_t)d<<32)|a;
}
static double ns_per_tick(void){
  struct timespec a,b; clock_gettime(CLOCK_MONOTONIC,&a);
  uint64_t t0=tsc0();
  do{ clock_gettime(CLOCK_MONOTONIC,&b); }
  while((b.tv_sec-a.tv_sec)*1e9+(b.tv_nsec-a.tv_nsec) < 5e7);
  uint64_t t1=tsc1();
  return ((b.tv_sec-a.tv_sec)*1e9+(b.tv_nsec-a.tv_nsec))/(double)(t1-t0);
}

/* ---------- counters ----------
 * Core cycles and instructions, user space only, from perf_event, read around
 * each timed loop; --raw adds one raw PMU event (e.g. blocked store-to-load
 * forwards). Without perf_event the unit falls back to TSC ticks, which are
 * NOT core cycles whenever the core runs off its nominal frequency. */
enum{ NCTR=3 };                       /* cycles (group leader), instructions, raw */
static int pfd[NCTR]={-1,-1,-1}, have_perf=0, have_raw=0;

/* Hybrid CPUs have one PMU per core type: return the type id of the PMU that
 * owns `cpu`, or -1 on a non-hybrid machine. */
static int pmu_type_for_cpu(int cpu){
  static const char *pm[]={"cpu_core","cpu_atom"};
  for(int k=0;k<2;k++){
    char path[128],buf[256]; FILE *f; int in=0,type=-1;
    snprintf(path,sizeof path,"/sys/bus/event_source/devices/%s/cpus",pm[k]);
    if(!(f=fopen(path,"r"))) continue;
    if(fgets(buf,sizeof buf,f))
      for(char *s=buf,*e; ; s=e){
        long a=strtol(s,&e,10),b=a; if(e==s) break;
        if(*e=='-'){ s=e+1; b=strtol(s,&e,10); if(e==s) break; }
        if(cpu>=a && cpu<=b) in=1;
        if(*e==',') e++;
      }
    fclose(f);
    if(!in) continue;
    snprintf(path,sizeof path,"/sys/bus/event_source/devices/%s/type",pm[k]);
    if((f=fopen(path,"r"))){ if(fscanf(f,"%d",&type)!=1) type=-1; fclose(f); }
    return type;
  }
  return -1;
}
static int ctr_open(uint32_t type,uint64_t config,int group){
  struct perf_event_attr at; memset(&at,0,sizeof at);
  at.size=sizeof at; at.type=type; at.config=config;
  at.exclude_kernel=1; at.exclude_hv=1;
  at.read_format=PERF_FORMAT_GROUP;
  return (int)syscall(SYS_perf_event_open,&at,0,-1,group,0);
}
static void ctr_init(int cpu,const char *raw){
  int pt=pmu_type_for_cpu(cpu);
  uint64_t hi = pt>=0 ? (uint64_t)pt<<32 : 0;          /* PERF_PMU_TYPE_SHIFT */
  pfd[0]=ctr_open(PERF_TYPE_HARDWARE,hi|PERF_COUNT_HW_CPU_CYCLES,-1);
  if(pfd[0]<0){ perror("perf_event_open (falling back to TSC ticks)"); return; }
  pfd[1]=ctr_open(PERF_TYPE_HARDWARE,hi|PERF_COUNT_HW_INSTRUCTIONS,pfd[0]);
  if(pfd[1]<0){ perror("perf_event_open (falling back to TSC ticks)"); close(pfd[0]); return; }
  have_perf=1;
  if(raw){
    pfd[2]=ctr_open(pt>=0?(uint32_t)pt:PERF_TYPE_RAW,strtoull(raw,NULL,0),pfd[0]);
    if(pfd[2]<0) perror("raw event (column left at 0)"); else have_raw=1;
  }
}
AI void ctr_read(uint64_t v[NCTR],int end){
  v[0]=v[1]=v[2]=0;
  if(have_perf){
    uint64_t b[1+NCTR]={0};
    if(read(pfd[0],b,sizeof b)<0){ perror("read counters"); exit(1); }
    v[0]=b[1]; v[1]=b[2]; if(have_raw) v[2]=b[3];
  } else v[0] = end? tsc1() : tsc0();
}
typedef struct{ double cyc,ins,raw; } meas_t;
static meas_t per_op(const uint64_t a[NCTR],const uint64_t b[NCTR],int it){
  meas_t m={ (double)(b[0]-a[0])/it, (double)(b[1]-a[1])/it, (double)(b[2]-a[2])/it };
  return m;
}

/* ---------- primitive self-test ---------- */
static uint64_t ref_clmul(uint64_t a, uint64_t b, int hi){
  uint64_t lo=0,h=0;
  for(int i=0;i<64;i++) if((b>>i)&1){
    lo ^= (i==0)? a : (a<<i);
    h  ^= (i==0)? 0 : (a>>(64-i));
  }
  return hi? h : lo;
}
static int clmul_selftest(void){
  static const uint64_t v[]={0,1,2,3,0x8000000000000000ULL,~0ULL,
                             0xAAAAAAAAAAAAAAAAULL,0x5555555555555555ULL};
  for(int i=0;i<8;i++) for(int j=0;j<8;j++)
    if(cllo(v[i],v[j])!=ref_clmul(v[i],v[j],0) || clhi(v[i],v[j])!=ref_clmul(v[i],v[j],1)){
      fprintf(stderr,"CLMUL edge mismatch a=%016llx b=%016llx\n",
              (unsigned long long)v[i],(unsigned long long)v[j]); return 0; }
  for(int t=0;t<2000;t++){
    uint64_t a=rnd(), b=rnd();
    if(cllo(a,b)!=ref_clmul(a,b,0) || clhi(a,b)!=ref_clmul(a,b,1)){
      fprintf(stderr,"CLMUL mismatch a=%016llx b=%016llx\n",
              (unsigned long long)a,(unsigned long long)b); return 0; }
  }
  return 1;
}

/* ---------- correctness ---------- */
static int test_field(const field_t *fl,int ntests,int verbose){
  uint64_t f[PL],a[EL],b[EL],c[EL],p[PL],got[EL],want[EL],x[EL],y[EL],z[EL];
  const size_t nb=(size_t)fl->W*8;
  build_f(f,fl);
  for(int t=0;t<ntests;t++){
    rfe(a,fl->m,fl->W); rfe(b,fl->m,fl->W); rfe(c,fl->m,fl->W);

    fl->mul(p,a,b); fl->red(got,p); ref_mulmod(want,a,b,fl->m,f);
    if(memcmp(got,want,nb)){ if(verbose) printf("  FAIL mul  %s t=%d\n",fl->name,t); return 0; }

    for(int i=0;i<PL;i++) p[i]=0;
    for(int i=0;i<2*fl->W;i++) p[i]=rnd();
    p[(2*fl->m-2)>>6] &= topmask((unsigned)(2*fl->m-1));
    for(int i=(2*fl->m-1+63)/64;i<PL;i++) p[i]=0;
    fl->red(got,p); ref_mod(want,p,fl->m,f);
    if(memcmp(got,want,nb)){ if(verbose) printf("  FAIL red  %s t=%d\n",fl->name,t); return 0; }

    fl->sqr(p,a); fl->red(got,p); ref_mulmod(want,a,a,fl->m,f);
    if(memcmp(got,want,nb)){ if(verbose) printf("  FAIL sqr  %s t=%d\n",fl->name,t); return 0; }

    for(int i=0;i<fl->W;i++) z[i]=a[i]^b[i];
    fl->mul(p,z,c); fl->red(x,p);
    fl->mul(p,a,c); fl->red(y,p);
    fl->mul(p,b,c); fl->red(z,p);
    for(int i=0;i<fl->W;i++) y[i]^=z[i];
    if(memcmp(x,y,nb)){ if(verbose) printf("  FAIL dist %s t=%d\n",fl->name,t); return 0; }
  }
  return 1;
}

/* ---------- benchmarks ---------- */
/* b_mul, b_fmul and b_sqr feed each result into the next call (latency chain);
 * b_red reduces independent precomputed products (throughput). */
static meas_t b_mul(const field_t *fl,int it){
  uint64_t a[EL],b[EL],p[PL],c0[NCTR],c1[NCTR]; rfe(a,fl->m,fl->W); rfe(b,fl->m,fl->W);
  ctr_read(c0,0);
  for(int i=0;i<it;i++){ fl->mul(p,a,b); a[0]^=p[0]; }
  ctr_read(c1,1); sink^=a[0]; return per_op(c0,c1,it);
}
static meas_t b_fmul(const field_t *fl,int it){
  uint64_t a[EL],b[EL],p[PL],c0[NCTR],c1[NCTR]; rfe(a,fl->m,fl->W); rfe(b,fl->m,fl->W);
  ctr_read(c0,0);
  for(int i=0;i<it;i++){ fl->mul(p,a,b); fl->red(a,p); }
  ctr_read(c1,1); sink^=a[0]; return per_op(c0,c1,it);
}
static meas_t b_sqr(const field_t *fl,int it){
  uint64_t a[EL],p[PL],c0[NCTR],c1[NCTR]; rfe(a,fl->m,fl->W);
  ctr_read(c0,0);
  for(int i=0;i<it;i++){ fl->sqr(p,a); fl->red(a,p); }
  ctr_read(c1,1); sink^=a[0]; return per_op(c0,c1,it);
}
static meas_t b_red(const field_t *fl,int it){
  uint64_t P[16*PL],r[EL],a[EL],b[EL],acc=0,c0[NCTR],c1[NCTR];
  for(int k=0;k<16;k++){ rfe(a,fl->m,fl->W); rfe(b,fl->m,fl->W); fl->mul(P+k*PL,a,b); }
  ctr_read(c0,0);
  for(int i=0;i<it;i++){ fl->red(r,P+(i&15)*PL); acc^=r[0]; }
  ctr_read(c1,1); sink^=acc; return per_op(c0,c1,it);
}
static int dcmp(const void*x,const void*y){
  double a=*(const double*)x, b=*(const double*)y; return (a>b)-(a<b);
}
static double medi(const double*v,int n){ double t[64]; memcpy(t,v,(size_t)n*8);
  qsort(t,(size_t)n,sizeof(double),dcmp); return t[n/2]; }

int main(int argc,char**argv){
  int cpu=0,it=100000,tr=7,testonly=0,ntests=60,vectors=0;
  const char*filt=NULL,*raw=NULL;
  for(int i=1;i<argc;i++){
    if(!strcmp(argv[i],"--cpu")&&i+1<argc) cpu=atoi(argv[++i]);
    else if(!strcmp(argv[i],"--raw")&&i+1<argc) raw=argv[++i];
    else if(!strcmp(argv[i],"--iters")&&i+1<argc) it=atoi(argv[++i]);
    else if(!strcmp(argv[i],"--trials")&&i+1<argc) tr=atoi(argv[++i]);
    else if(!strcmp(argv[i],"--tests")&&i+1<argc) ntests=atoi(argv[++i]);
    else if(!strcmp(argv[i],"--test")) testonly=1;
    else if(!strcmp(argv[i],"--vectors")) vectors=1;
    else if(!strcmp(argv[i],"--filter")&&i+1<argc) filt=argv[++i];
    else{ fprintf(stderr,"usage: %s [--cpu N] [--iters N] [--trials N] [--tests N] [--test] [--vectors] [--filter S] [--raw EVENT]\n",argv[0]); return 2; }
  }
  if(tr>64) tr=64;
  if(it<1) it=1;

  cpu_set_t set; CPU_ZERO(&set); CPU_SET(cpu,&set);
  if(sched_setaffinity(0,sizeof set,&set)) perror("sched_setaffinity");

  __builtin_cpu_init();
  if(!__builtin_cpu_supports("pclmul")){ fprintf(stderr,"CPU has no PCLMULQDQ\n"); return 1; }
  if(!clmul_selftest()) return 1;

  char model[256]="unknown";
  FILE*ci=fopen("/proc/cpuinfo","r");
  if(ci){
    char ln[512];
    while(fgets(ln,sizeof ln,ci)){
      if(!strncmp(ln,"model name",10)){
        char*q=strchr(ln,':');
        if(q){ snprintf(model,sizeof model,"%s",q+2); model[strcspn(model,"\n")]=0; }
        break;
      }
    }
    fclose(ci);
  }
  if(!testonly) ctr_init(cpu,raw);
  printf("# CPU: %s\n# compiler: %s\n# flags: %s\n",model,COMPILER,BUILD_FLAGS);
  printf("# cpu %d, iters=%d trials=%d, minimum over trials\n",cpu,it,tr);
  if(!testonly){
    printf("# unit: %s\n",have_perf? "core cycles/op (perf_event, user space)"
                                   : "TSC ticks/op (perf_event unavailable; NOT core cycles)");
    if(have_raw) printf("# raw event: %s, per op\n",raw);
  }
  printf("# clmul self-test ok\n");

  int bad=0;
  for(int i=0;i<NF;i++){
    if(filt && !strstr(F[i].name,filt)) continue;
    int ok=test_field(&F[i],ntests,1);
    printf("# test %-28s %s\n",F[i].name,ok?"ok":"FAIL");
    if(!ok) bad=1;
  }
  if(bad){ fprintf(stderr,"correctness failures - not benchmarking\n"); return 1; }

  if(vectors){
    for(int i=0;i<NF;i++){
      uint64_t a[EL],b[EL],p[PL],r[EL];
      rfe(a,F[i].m,F[i].W); rfe(b,F[i].m,F[i].W);
      F[i].mul(p,a,b); F[i].red(r,p);
      printf("V %d %d",F[i].m,F[i].ne);
      for(int k=0;k<F[i].ne;k++) printf(" %d",F[i].e[k]);
      for(int w=0;w<F[i].W;w++) printf(" %016llx",(unsigned long long)a[w]);
      for(int w=0;w<F[i].W;w++) printf(" %016llx",(unsigned long long)b[w]);
      for(int w=0;w<F[i].W;w++) printf(" %016llx",(unsigned long long)r[w]);
      printf("\n");
    }
  }
  if(testonly) return 0;

  /* red(tp) and sqr+red also report instructions and the raw event per op,
   * taken from the trial with the fewest cycles. */
  printf("\n%-28s %4s %6s %8s %8s %8s %8s %8s %8s %8s %8s %8s %8s\n",
         "field","m","gates","mul","mul+red","red(tp)","red=sub","sqr+red","m+r med",
         "red:ins","red:raw","sqr:ins","sqr:raw");
  for(int i=0;i<NF;i++){
    if(filt && !strstr(F[i].name,filt)) continue;
    meas_t (*const fn[4])(const field_t*,int)={b_mul,b_fmul,b_red,b_sqr};
    meas_t best[4]; double v2[64];
    for(int t=0;t<tr;t++)
      for(int k=0;k<4;k++){
        meas_t m=fn[k](&F[i],it);
        if(t==0 || m.cyc<best[k].cyc) best[k]=m;
        if(k==1) v2[t]=m.cyc;
      }
    printf("%-28s %4d %6d %8.1f %8.1f %8.1f %8.1f %8.1f %8.1f %8.1f %8.2f %8.1f %8.2f\n",
           F[i].name,F[i].m,F[i].gates,best[0].cyc,best[1].cyc,best[2].cyc,
           best[1].cyc-best[0].cyc,best[3].cyc,medi(v2,tr),
           best[2].ins,best[2].raw,best[3].ins,best[3].raw);
  }
  if(!have_perf) printf("\n# ns/op = ticks * %.4f\n",ns_per_tick());
  return 0;
}