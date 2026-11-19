/* gf2m.h — PCLMULQDQ carry-less multiply + reduction kernels.
 * Bit i of poly = limb[i>>6] bit (i&63).
 * Elements: uint64_t[EL].  Products: uint64_t[PL].  m <= 640.
 * Reduction: r may alias p; r needs EL limbs, p needs PL limbs.
 * Build: -O3 -march=native -mpclmul, with auto-vectorization off (see the
 * Makefile): vectorized, these loops read with wide loads what they have just
 * written with narrow stores, and the blocked store-to-load forwards cost
 * more than the kernels themselves.
 */
#ifndef GF2M_H
#define GF2M_H
#include <stdint.h>
#include <string.h>
#include <emmintrin.h>
#include <wmmintrin.h>
#include <immintrin.h>

#define EL 12
#define PL 24
#define AI static inline __attribute__((always_inline))
#define LIMBS(m) (((m)+63)/64)

#if defined(__clang__)
#  define UNROLL8 _Pragma("unroll 8")
#else
#  define UNROLL8 _Pragma("GCC unroll 8")
#endif

/* ---- 64x64 -> 128 carry-less.
 * imm8 selects SOURCE halves; the 128-bit RESULT is split with psrldq. ---- */
AI void clmul64(uint64_t a, uint64_t b, uint64_t *lo, uint64_t *hi){
  __m128i A = _mm_cvtsi64_si128((long long)a);
  __m128i B = _mm_cvtsi64_si128((long long)b);
  __m128i P = _mm_clmulepi64_si128(A, B, 0x00);
  *lo = (uint64_t)_mm_cvtsi128_si64(P);
  *hi = (uint64_t)_mm_cvtsi128_si64(_mm_srli_si128(P, 8));
}
AI uint64_t cllo(uint64_t a, uint64_t b){ uint64_t l,h; clmul64(a,b,&l,&h); return l; }
AI uint64_t clhi(uint64_t a, uint64_t b){ uint64_t l,h; clmul64(a,b,&l,&h); return h; }

/* ---- limb-vector helpers (lengths/shifts are literals at call sites) ---- */
AI void cpy(uint64_t *d, const uint64_t *s, int n){ for(int i=0;i<n;i++) d[i]=s[i]; }
AI void xr (uint64_t *d, const uint64_t *s, int n){ for(int i=0;i<n;i++) d[i]^=s[i]; }
AI void zro(uint64_t *d, int n){ for(int i=0;i<n;i++) d[i]=0; }

AI void shr_(uint64_t *d, const uint64_t *s, unsigned k, int nd, int ns){
  unsigned w=k>>6, b=k&63;
  for(int i=0;i<nd;i++){
    unsigned j=i+w;
    uint64_t v = (j<(unsigned)ns)? s[j] : 0;
    if(b){ uint64_t u = (j+1<(unsigned)ns)? s[j+1] : 0; v = (v>>b)|(u<<(64-b)); }
    d[i]=v;
  }
}
/* in-place OK: ascending i reads only indices >= i */
AI void xshr(uint64_t *d, const uint64_t *s, unsigned k, int nd, int ns){
  unsigned w=k>>6, b=k&63;
  for(int i=0;i<nd;i++){
    unsigned j=i+w;
    uint64_t v = (j<(unsigned)ns)? s[j] : 0;
    if(b){ uint64_t u = (j+1<(unsigned)ns)? s[j+1] : 0; v = (v>>b)|(u<<(64-b)); }
    d[i]^=v;
  }
}
/* d and s MUST differ */
AI void xshl(uint64_t *d, const uint64_t *s, unsigned k, int nd, int ns){
  unsigned w=k>>6, b=k&63;
  for(int i=0;i<nd;i++){
    int j=i-(int)w; uint64_t v=0;
    if(j>=0 && j<ns){ v = s[j]<<b; if(b && j>0) v |= s[j-1]>>(64-b); }
    d[i]^=v;
  }
}
AI uint64_t topmask(unsigned m){ unsigned r=m&63; return r? ((1ULL<<r)-1) : ~0ULL; }

/* ---- Karatsuba over limbs, PCLMUL base case ---- */
static void kara(uint64_t *r, const uint64_t *a, const uint64_t *b, int n, uint64_t *sc){
  if(n==1){ clmul64(a[0],b[0],&r[0],&r[1]); return; }
  int k=(n+1)/2, na=n-k;
  uint64_t *sa=sc, *sb=sc+k, *mid=sc+2*k, *nsc=sc+4*k;
  for(int i=0;i<k;i++){
    sa[i]=a[i]^((i<na)?a[k+i]:0);
    sb[i]=b[i]^((i<na)?b[k+i]:0);
  }
  kara(r,     a,   b,   k,  nsc);   /* r[0 .. 2k-1]   */
  kara(r+2*k, a+k, b+k, na, nsc);   /* r[2k .. 2n-1]  */
  kara(mid,   sa,  sb,  k,  nsc);   /* mid[0 .. 2k-1] */
  for(int i=0;i<2*k; i++) mid[i]^=r[i];
  for(int i=0;i<2*na;i++) mid[i]^=r[2*k+i];
  for(int i=0;i<2*k; i++) r[k+i]^=mid[i];
}

/* static scratch: zero-initialised at load, no per-call memset.
 * Single-threaded benchmark only. */
#define GEN_MUL(NAME,W) \
static void NAME(uint64_t *p, const uint64_t *a, const uint64_t *b){ \
  static uint64_t sc[512]; \
  kara(p,a,b,(W),sc); \
  for(int i=2*(W);i<PL;i++) p[i]=0; }

#define GEN_SQR(NAME,W) \
static void NAME(uint64_t *p, const uint64_t *a){ \
  for(int i=0;i<(W);i++) clmul64(a[i],a[i],&p[2*i],&p[2*i+1]); \
  for(int i=2*(W);i<PL;i++) p[i]=0; }

/* =========================================================================
 * COMB — Corollary 16:  f_{b,c} = x^{b+2c}+x^{b+c}+x^b+x^c+1
 *   C = sum_l (H >> 3c*l)      (doubling)
 *   Q = C ^ (C>>c) ^ (H>>(b+c))
 *   U = Q ^ (Q<<c)
 *   R = (L ^ U ^ (U<<b)) mod x^m
 * Final op is a pure truncation, so L need not be masked early here.
 * ========================================================================= */
#define COMB_RED(NAME,M,B,C) \
static void NAME(uint64_t *r, const uint64_t *p){ \
  enum{ W=LIMBS(M), N=(M)-2, S3=3*(C) }; \
  uint64_t h[W+1], q[W+1], u[W+1], cb[W+1]; \
  zro(h,W+1); zro(q,W+1); zro(u,W+1); zro(cb,W+1); \
  shr_(h,p,(M),W,2*W); \
  cpy(q,h,W); \
  UNROLL8 \
  for(unsigned s=S3; s<=(unsigned)N; s<<=1){ \
    int nd=(int)(((M)-1-s+63)/64); if(nd>0) xshr(q,q,s,nd,W); } \
  cpy(cb,q,W); \
  xshr(q,cb,(C),W,W); \
  { int nd=(int)(((C)-1+63)/64); if(nd>0) xshr(q,h,(B)+(C),nd,W); } \
  cpy(u,q,W); xshl(u,q,(C),W,W); \
  cpy(r,p,W); xr(r,u,W); \
  { unsigned w=(B)>>6; xshl(r+w,u,(B)&63,W-(int)w,W); } \
  r[W-1]&=topmask(M); r[W]=0; r[W+1]=0; }

/* SMALL — x^m+x^e3+x^e2+x^e1+1, e1<e2<e3<=32. Two rounds, second is scalar.
 * L MUST be masked to m bits before folding.
 * H = D>>m has at most m-1 bits and fits in W limbs. The first round
 * L^H^(H<<e1)^(H<<e2)^(H<<e3) has degree at most m-2+e3, so it needs X=1
 * extra limb only when that reaches bit 64W (128 and 571; not 163 or 283).
 * What it leaves above x^m has fewer than e3 bits: the second round is one
 * limb, and no pass runs over more limbs than the field needs. */
#define SMALL_RED(NAME,M,E1,E2,E3) \
static void NAME(uint64_t *r, const uint64_t *p){ \
  enum{ W=LIMBS(M), S=(M)&63, X=((M)-2+(E3) >= 64*LIMBS(M)) }; \
  _Static_assert((E3)<=32, "SMALL_RED needs e3 <= 32"); \
  uint64_t h[W+1]; \
  shr_(h,p,(M),W,2*W); h[W]=0; \
  cpy(r,p,W); r[W-1]&=topmask(M); r[W]=0; r[W+1]=0; \
  xr(r,h,W); xshl(r,h,(E1),W+X,W+1); xshl(r,h,(E2),W+X,W+1); xshl(r,h,(E3),W+X,W+1); \
  uint64_t t = S ? (r[W-1]>>S) | (X ? r[W]<<((64-S)&63) : 0) : r[W]; \
  r[W-1]&=topmask(M); r[W]=0; \
  r[0]^=t^(t<<(E1))^(t<<(E2))^(t<<(E3)); }

/* TRI — x^m+x^E+1 with 2E<m */
#define TRI_RED(NAME,M,E) \
static void NAME(uint64_t *r, const uint64_t *p){ \
  enum{ W=LIMBS(M) }; \
  uint64_t h[W+2], t[W+2]; zro(h,W+2); zro(t,W+2); \
  shr_(h,p,(M),W+2,2*W); \
  cpy(r,p,W); r[W-1]&=topmask(M); r[W]=0; r[W+1]=0; \
  xr(r,h,W+2); xshl(r,h,(E),W+2,W+2); \
  shr_(t,r,(M),W+2,W+2); \
  r[W-1]&=topmask(M); r[W]=0; r[W+1]=0; \
  xr(r,t,W+2); xshl(r,t,(E),W+2,W+2); \
  r[W-1]&=topmask(M); r[W]=0; r[W+1]=0; }

/* FOLD — naive serial folding baseline */
#define FOLD_RED(NAME,M,E1,E2,E3) \
static void NAME(uint64_t *r, const uint64_t *p){ \
  enum{ W=LIMBS(M), NB=2*W+1 }; \
  uint64_t buf[NB], h[NB]; zro(buf,NB); cpy(buf,p,2*W); \
  for(int it=0; it<64; it++){ \
    zro(h,NB); shr_(h,buf,(M),NB,NB); \
    uint64_t nz=0; for(int i=0;i<NB;i++) nz|=h[i]; if(!nz) break; \
    buf[W-1]&=topmask(M); for(int i=W;i<NB;i++) buf[i]=0; \
    xr(buf,h,NB); xshl(buf,h,(E1),NB,NB); xshl(buf,h,(E2),NB,NB); xshl(buf,h,(E3),NB,NB); } \
  cpy(r,buf,W); r[W]=0; r[W+1]=0; }

/* ---- instantiations ---- */
GEN_MUL(mul2,2) GEN_MUL(mul3,3) GEN_MUL(mul4,4)
GEN_MUL(mul5,5) GEN_MUL(mul7,7) GEN_MUL(mul9,9)
GEN_SQR(sqr2,2) GEN_SQR(sqr3,3) GEN_SQR(sqr4,4)
GEN_SQR(sqr5,5) GEN_SQR(sqr7,7) GEN_SQR(sqr9,9)

SMALL_RED(red_128_gcm,       128,  1,  2,  7)
COMB_RED (red_163_s7146,     163, 71, 46)
FOLD_RED (red_163_s7146_f,   163, 46, 71,117)
FOLD_RED (red_163_f6337,     163, 37, 63,100)
FOLD_RED (red_163_f7415,     163, 15, 74, 89)
SMALL_RED(red_163_nist,      163,  3,  6,  7)
TRI_RED  (red_233_t74,       233, 74)
COMB_RED (red_233_s8375,     233, 83, 75)
SMALL_RED(red_283_nist,      283,  5,  7, 12)
FOLD_RED (red_283_f11161,    283, 61,111,172)
TRI_RED  (red_409_t87,       409, 87)
COMB_RED (red_409_s179115,   409,179,115)
COMB_RED (red_571_s207182,   571,207,182)
FOLD_RED (red_571_s207182_f, 571,182,207,389)
COMB_RED (red_571_s359106,   571,359,106)
COMB_RED (red_571_s52722,    571,527, 22)
FOLD_RED (red_571_s52722_f,  571, 22,527,549)
FOLD_RED (red_571_f218135,   571,135,218,353)
SMALL_RED(red_571_nist,      571,  2,  5, 10)
#endif