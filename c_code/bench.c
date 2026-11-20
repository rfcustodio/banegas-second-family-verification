/* bench.c — correctness tests and cycle counts for the reduction kernels of
 * gf2m.h.
 *
 * Every kernel is first checked against an independent bit-by-bit reference.
 * The timing then measures four operations per field:
 *   red      one reduction of independent precomputed products (throughput)
 *   sqr+red  one step of a chain of squarings (latency)
 *   mul      one product, without reduction (latency chain); it is the same
 *            routine for every field of a degree and serves as a control
 *   mul+red  one step of a chain of field multiplications (latency)
 * A sample is one timed loop of one operation on one field. Each trial runs
 * every (field, operation) pair once, in an order shuffled anew for every
 * trial, and each sample runs with the stack moved by a random multiple of 16
 * bytes below 4 KiB, so that neither the order of the measurements nor the
 * position of the stack buffers favours a kernel. The summary gives, over the
 * trials, the minimum, quartiles, median and maximum of each pair.
 */
#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <time.h>
#include <sched.h>
#include <unistd.h>
#include <alloca.h>
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

/* gates: XOR gates of the best known reduction circuit, as in Tables 9 and 10
 * of the paper (second family: better of Theorems 8 and 13; first family:
 * 3m-2 [BCP2019]; NIST pentanomials: Conta-XOR; trinomials: 2m-2). The
 * software kernels of the second family follow Corollary 16 in all cases. */
typedef struct {
  const char *name; int m, W, ne, e[3];
  bin_t mul; un_t sqr, red; int gates;
} field_t;

static const field_t F[] = {
 {"163 second(71,46)",   163,3,3,{46,71,117},  mul3,sqr3,red_163_s7146,    440},
 {"163 first(74,15)",    163,3,3,{15,74,89},   mul3,sqr3,red_163_f7415,    487},
 {"163 first(63,37)",    163,3,3,{37,63,100},  mul3,sqr3,red_163_f6337,    487},
 {"163 NIST",            163,3,3,{3,6,7},      mul3,sqr3,red_163_nist,     571},
 {"233 second(83,75)",   233,4,3,{75,83,158},  mul4,sqr4,red_233_s8375,    621},
 {"233 second(201,16)",  233,4,3,{16,201,217}, mul4,sqr4,red_233_s20116,   632},
 {"233 first(95,43)",    233,4,3,{43,95,138},  mul4,sqr4,red_233_f9543,    697},
 {"233 first(79,75)",    233,4,3,{75,79,154},  mul4,sqr4,red_233_f7975,    697},
 {"233 trinomial(74)",   233,4,1,{74,0,0},     mul4,sqr4,red_233_t74,      464},
 {"283 first(123,37)",   283,5,3,{37,123,160}, mul5,sqr5,red_283_f12337,   847},
 {"283 first(111,61)",   283,5,3,{61,111,172}, mul5,sqr5,red_283_f11161,   847},
 {"283 NIST",            283,5,3,{5,7,12},     mul5,sqr5,red_283_nist,     862},
 {"409 second(179,115)", 409,7,3,{115,179,294},mul7,sqr7,red_409_s179115, 1109},
 {"409 second(265,72)",  409,7,3,{72,265,337}, mul7,sqr7,red_409_s26572,  1152},
 {"409 trinomial(87)",   409,7,1,{87,0,0},     mul7,sqr7,red_409_t87,      816},
 {"571 second(207,182)", 571,9,3,{182,207,389},mul9,sqr9,red_571_s207182, 1528},
 {"571 second(359,106)", 571,9,3,{106,359,465},mul9,sqr9,red_571_s359106, 1604},
 {"571 second(527,22)",  571,9,3,{22,527,549}, mul9,sqr9,red_571_s52722,  1534},
 {"571 first(218,135)",  571,9,3,{135,218,353},mul9,sqr9,red_571_f218135, 1711},
 {"571 NIST",            571,9,3,{2,5,10},     mul9,sqr9,red_571_nist,    2003},
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

/* ---------- random numbers: field data, and the schedule (order, offsets) ---------- */
static uint64_t rs = 0x243F6A8885A308D3ULL;           /* field elements */
static uint64_t ss = 0x13198A2E03707344ULL;           /* schedule; --seed */
AI uint64_t xs(uint64_t *s){ *s^=*s<<13; *s^=*s>>7; *s^=*s<<17; return *s; }
AI uint64_t rnd(void){ return xs(&rs); }
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
static double now_ns(void){
  struct timespec t; clock_gettime(CLOCK_MONOTONIC,&t); return t.tv_sec*1e9+t.tv_nsec;
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
/* per operation: cycles, instructions, raw event; ghz = cycles per ns of the loop */
typedef struct{ double cyc,ins,raw,ghz; } meas_t;
static meas_t per_op(const uint64_t a[NCTR],const uint64_t b[NCTR],int it,double ns){
  meas_t m={ (double)(b[0]-a[0])/it, (double)(b[1]-a[1])/it, (double)(b[2]-a[2])/it,
             (double)(b[0]-a[0])/ns };
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

/* ---------- timed loops ----------
 * noinline keeps each loop's buffers in its own frame, below the padding that
 * run_at() allocates, so the padding moves them. */
#define NOINL __attribute__((noinline))
enum{ OP_RED, OP_SQR, OP_MUL, OP_MULRED, NOP };
static const char *const opname[NOP]={"red","sqr+red","mul","mul+red"};

NOINL static meas_t b_red(const field_t *fl,int it){
  uint64_t P[16*PL],r[EL],a[EL],b[EL],acc=0,c0[NCTR],c1[NCTR];
  for(int k=0;k<16;k++){ rfe(a,fl->m,fl->W); rfe(b,fl->m,fl->W); fl->mul(P+k*PL,a,b); }
  double t0=now_ns(); ctr_read(c0,0);
  for(int i=0;i<it;i++){ fl->red(r,P+(i&15)*PL); acc^=r[0]; }
  ctr_read(c1,1); double t1=now_ns(); sink^=acc; return per_op(c0,c1,it,t1-t0);
}
NOINL static meas_t b_sqr(const field_t *fl,int it){
  uint64_t a[EL],p[PL],c0[NCTR],c1[NCTR]; rfe(a,fl->m,fl->W);
  double t0=now_ns(); ctr_read(c0,0);
  for(int i=0;i<it;i++){ fl->sqr(p,a); fl->red(a,p); }
  ctr_read(c1,1); double t1=now_ns(); sink^=a[0]; return per_op(c0,c1,it,t1-t0);
}
NOINL static meas_t b_mul(const field_t *fl,int it){
  uint64_t a[EL],b[EL],p[PL],c0[NCTR],c1[NCTR]; rfe(a,fl->m,fl->W); rfe(b,fl->m,fl->W);
  double t0=now_ns(); ctr_read(c0,0);
  for(int i=0;i<it;i++){ fl->mul(p,a,b); a[0]^=p[0]; }
  ctr_read(c1,1); double t1=now_ns(); sink^=a[0]; return per_op(c0,c1,it,t1-t0);
}
NOINL static meas_t b_mulred(const field_t *fl,int it){
  uint64_t a[EL],b[EL],p[PL],c0[NCTR],c1[NCTR]; rfe(a,fl->m,fl->W); rfe(b,fl->m,fl->W);
  double t0=now_ns(); ctr_read(c0,0);
  for(int i=0;i<it;i++){ fl->mul(p,a,b); fl->red(a,p); }
  ctr_read(c1,1); double t1=now_ns(); sink^=a[0]; return per_op(c0,c1,it,t1-t0);
}
NOINL static meas_t run_at(unsigned off,int op,const field_t *fl,int it){
  volatile char *pad=alloca(off+16); pad[0]=0;
  meas_t m;
  switch(op){
    case OP_RED: m=b_red(fl,it);    break;
    case OP_SQR: m=b_sqr(fl,it);    break;
    case OP_MUL: m=b_mul(fl,it);    break;
    default:     m=b_mulred(fl,it); break;
  }
  pad[off]=0;
  return m;
}

/* ---------- statistics ---------- */
static int dcmp(const void*x,const void*y){
  double a=*(const double*)x, b=*(const double*)y; return (a>b)-(a<b);
}
/* quantile by linear interpolation; v is sorted */
static double qtl(const double *v,int n,double q){
  double h=(n-1)*q; int i=(int)h; if(i>=n-1) return v[n-1];
  return v[i]+(h-i)*(v[i+1]-v[i]);
}

int main(int argc,char**argv){
  int cpu=2,it=200000,tr=21,testonly=0,ntests=60,vectors=0;
  const char*filt=NULL,*raw=NULL,*csv=NULL;
  for(int i=1;i<argc;i++){
    if(!strcmp(argv[i],"--cpu")&&i+1<argc) cpu=atoi(argv[++i]);
    else if(!strcmp(argv[i],"--raw")&&i+1<argc) raw=argv[++i];
    else if(!strcmp(argv[i],"--iters")&&i+1<argc) it=atoi(argv[++i]);
    else if(!strcmp(argv[i],"--trials")&&i+1<argc) tr=atoi(argv[++i]);
    else if(!strcmp(argv[i],"--tests")&&i+1<argc) ntests=atoi(argv[++i]);
    else if(!strcmp(argv[i],"--seed")&&i+1<argc) ss=strtoull(argv[++i],NULL,0)|1;
    else if(!strcmp(argv[i],"--csv")&&i+1<argc) csv=argv[++i];
    else if(!strcmp(argv[i],"--test")) testonly=1;
    else if(!strcmp(argv[i],"--vectors")) vectors=1;
    else if(!strcmp(argv[i],"--filter")&&i+1<argc) filt=argv[++i];
    else{ fprintf(stderr,"usage: %s [--cpu N] [--iters N] [--trials N] [--seed N] [--csv FILE]"
                         " [--tests N] [--test] [--vectors] [--filter S] [--raw EVENT]\n",argv[0]); return 2; }
  }
  if(tr<1) tr=1;
  if(it<8) it=8;

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
  if(!testonly){
    printf("# cpu %d, trials=%d, iterations per sample: %d (red, sqr+red), %d (mul, mul+red)\n",
           cpu,tr,it,it/8);
    printf("# order of the samples shuffled in every trial, stack moved by a random offset in [0,4096) per sample\n");
    printf("# unit: %s\n",have_perf? "core cycles/op (perf_event, user space)"
                                   : "TSC ticks/op (perf_event unavailable; NOT core cycles)");
    if(have_raw) printf("# raw event: %s, per op\n",raw);
  }
  printf("# clmul self-test ok\n");

  int sel[64],ns=0,bad=0;
  for(int i=0;i<NF;i++){
    if(filt && !strstr(F[i].name,filt)) continue;
    int ok=test_field(&F[i],ntests,1);
    printf("# test %-24s %s\n",F[i].name,ok?"ok":"FAIL");
    if(!ok) bad=1;
    sel[ns++]=i;
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
  if(testonly || ns==0) return 0;

  /* samples[(s*NOP+op)*tr + t] */
  const int npair=ns*NOP;
  meas_t *smp=calloc((size_t)npair*tr,sizeof *smp);
  int *perm=malloc(sizeof(int)*(size_t)npair);
  FILE *cf = csv? fopen(csv,"w") : NULL;
  if(csv && !cf){ perror(csv); return 1; }
  if(cf) fprintf(cf,"field,op,trial,position,stack_offset,cycles_per_op,ins_per_op,raw_per_op,ghz\n");

  for(int p=0;p<npair;p++){                              /* warm-up, untimed */
    const field_t *fl=&F[sel[p/NOP]]; int op=p%NOP;
    run_at(0,op,fl,(op>=OP_MUL? it/8 : it)/4);
  }
  for(int t=0;t<tr;t++){
    for(int p=0;p<npair;p++) perm[p]=p;
    for(int p=npair-1;p>0;p--){ int j=(int)(xs(&ss)%(uint64_t)(p+1)); int x=perm[p]; perm[p]=perm[j]; perm[j]=x; }
    for(int k=0;k<npair;k++){
      int p=perm[k], s=p/NOP, op=p%NOP; const field_t *fl=&F[sel[s]];
      unsigned off=(unsigned)(xs(&ss)&0xff0);
      meas_t m=run_at(off,op,fl,op>=OP_MUL? it/8 : it);
      smp[(size_t)p*tr+t]=m;
      if(cf) fprintf(cf,"\"%s\",%s,%d,%d,%u,%.3f,%.3f,%.4f,%.4f\n",
                     fl->name,opname[op],t,k,off,m.cyc,m.ins,m.raw,m.ghz);
    }
  }
  if(cf) fclose(cf);

  /* summary */
  double *v=malloc(sizeof(double)*(size_t)tr), *g=malloc(sizeof(double)*(size_t)npair*tr);
  int ng=0;
  for(int p=0;p<npair*tr;p++) g[ng++]=smp[p].ghz;
  qsort(g,(size_t)ng,sizeof(double),dcmp);
  if(have_perf)
    printf("# effective core frequency over all samples: min %.2f, median %.2f, max %.2f GHz\n",
           g[0],qtl(g,ng,0.5),g[ng-1]);
  printf("\n%-21s %4s %5s %-8s %8s %8s %8s %8s %8s %6s %8s %8s\n",
         "field","m","gates","op","min","p25","median","p75","max","IQR%","ins/op","raw/op");
  for(int s=0;s<ns;s++){
    const field_t *fl=&F[sel[s]];
    for(int op=0;op<NOP;op++){
      const meas_t *ms=&smp[(size_t)(s*NOP+op)*tr];
      for(int t=0;t<tr;t++) v[t]=ms[t].cyc;
      qsort(v,(size_t)tr,sizeof(double),dcmp);
      double med=qtl(v,tr,0.5), q1=qtl(v,tr,0.25), q3=qtl(v,tr,0.75);
      /* instructions and raw event: median over trials */
      double ins[tr>0?tr:1], rw[tr>0?tr:1];
      for(int t=0;t<tr;t++){ ins[t]=ms[t].ins; rw[t]=ms[t].raw; }
      qsort(ins,(size_t)tr,sizeof(double),dcmp); qsort(rw,(size_t)tr,sizeof(double),dcmp);
      printf("%-21s %4d %5d %-8s %8.1f %8.1f %8.1f %8.1f %8.1f %6.1f %8.1f %8.2f\n",
             fl->name,fl->m,fl->gates,opname[op],v[0],q1,med,q3,v[tr-1],
             100*(q3-q1)/med,qtl(ins,tr,0.5),qtl(rw,tr,0.5));
    }
  }
  if(!have_perf){
    struct timespec a,b; clock_gettime(CLOCK_MONOTONIC,&a); uint64_t t0=tsc0();
    do{ clock_gettime(CLOCK_MONOTONIC,&b); } while((b.tv_sec-a.tv_sec)*1e9+(b.tv_nsec-a.tv_nsec)<5e7);
    uint64_t t1=tsc1();
    printf("\n# ns/op = ticks * %.4f\n",((b.tv_sec-a.tv_sec)*1e9+(b.tv_nsec-a.tv_nsec))/(double)(t1-t0));
  }
  free(v); free(g); free(perm); free(smp);
  return 0;
}
