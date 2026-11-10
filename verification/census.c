/*
 * census.c -- independent irreducibility census over F_2 for sparse polynomials.
 *
 *   census sec MLO MHI     irreducible second-family members  x^m+x^{b+c}+x^b+x^c+1, m=b+2c, b>c>=1
 *   census fst MLO MHI     irreducible first-family members   x^m+x^{b+c}+x^b+x^c+1, m=2b+c, b>c>=1
 *   census tri MLO MHI     for each m: smallest k<=m/2 with x^m+x^k+1 irreducible (0 if none)
 *   census one m e1 e2 ... arbitrary sparse polynomial x^m + sum x^ei (must include 0)
 *
 * Test: trial division by all irreducible polynomials of degree <= min(12, m/2)
 * (fast sieve), then Rabin's test: x^(2^m) = x mod f and gcd(x^(2^(m/p)) - x, f) = 1
 * for every prime p | m.
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>

#define MAXM 1200
#define NWM ((2 * MAXM) / 64 + 4)
typedef struct { uint64_t w[NWM]; } P;

static int E[8], NE, M, NW;   /* f = sum x^E[i], E[0] = M */

static inline int getbit(const P *a, int i) { return (a->w[i >> 6] >> (i & 63)) & 1; }
static int degp(const P *a, int nw) { for (int k = nw - 1; k >= 0; k--) if (a->w[k]) return 64 * k + 63 - __builtin_clzll(a->w[k]); return -1; }
static inline uint64_t get64(const P *a, int pos) { /* bits pos..pos+63 */
    int q = pos >> 6, r = pos & 63;
    uint64_t lo = a->w[q] >> r;
    if (r) lo |= a->w[q + 1] << (64 - r);
    return lo;
}
static inline void xor64(P *a, int pos, uint64_t v) {
    int q = pos >> 6, r = pos & 63;
    a->w[q] ^= v << r;
    if (r) a->w[q + 1] ^= v >> (64 - r);
}
/* reduce a (degree < 2M) modulo f, word-chunked */
static void reduce(P *a) {
    int gap = E[0] - E[1];
    int top = degp(a, 2 * NW + 1);
    while (top >= M) {
        int w = 64; if (w > gap) w = gap; if (w > top - M + 1) w = top - M + 1;
        int lo = top - w + 1;
        uint64_t v = get64(a, lo); if (w < 64) v &= (1ULL << w) - 1;
        xor64(a, lo, v);                      /* clear chunk */
        for (int t = 1; t < NE; t++) xor64(a, lo - M + E[t], v);
        top = degp(a, (top >> 6) + 1);
    }
}
static uint16_t SPR[256];
static void sqr(P *r, const P *a) {
    P t; memset(&t, 0, sizeof(uint64_t) * (2 * NW + 2));
    for (int k = 0; k < NW; k++) {
        uint64_t x = a->w[k], lo = 0, hi = 0;
        for (int j = 0; j < 4; j++) { lo |= (uint64_t)SPR[(x >> (8 * j)) & 255] << (16 * j); hi |= (uint64_t)SPR[(x >> (32 + 8 * j)) & 255] << (16 * j); }
        t.w[2 * k] = lo; t.w[2 * k + 1] = hi;
    }
    reduce(&t);
    memcpy(r->w, t.w, sizeof(uint64_t) * NW);
    for (int k = NW; k < NWM; k++) r->w[k] = 0;
}
static void shlxor(P *a, const P *b, int s, int nw) { /* a ^= b << s */
    int q = s >> 6, r = s & 63;
    for (int k = nw - 1; k >= 0; k--) {
        if (b->w[k] == 0) continue;
        a->w[k + q] ^= b->w[k] << r;
        if (r) a->w[k + q + 1] ^= b->w[k] >> (64 - r);
    }
}
static int gcd_is_one(P a, P b) { /* both degree <= M */
    int nw = NW + 1;
    int da = degp(&a, nw), db = degp(&b, nw);
    while (db >= 0) {
        while (da >= db) { shlxor(&a, &b, da - db, nw); da = degp(&a, nw); }
        P t = a; a = b; b = t; int dt = da; da = db; db = dt;
    }
    return da == 0;
}
/* small irreducibles for sieve */
#define SMAXD 12
static int nsmall; static int sdeg[2000], sord[2000]; static uint16_t *spow[2000];
static int poly_mod_small(uint32_t a, uint32_t g) { int dg = 31 - __builtin_clz(g); while (a && 31 - __builtin_clz(a) >= dg) a ^= g << ((31 - __builtin_clz(a)) - dg); return a; }
static void build_small(void) {
    for (uint32_t g = 2; g < (1u << (SMAXD + 1)); g++) {
        int d = 31 - __builtin_clz(g);
        if (d < 1) continue; if (d >= 1 && !(g & 1) && g != 2) continue;
        int irr = 1;
        for (uint32_t h = 2; h < g && irr; h++) { int dh = 31 - __builtin_clz(h); if (2 * dh > d) break; if (poly_mod_small(g, h) == 0) irr = 0; }
        if (!irr) continue;
        if (g == 2) continue; /* x: f has constant term 1 */
        /* order of x mod g and powers */
        uint16_t *pw = malloc(sizeof(uint16_t) * (1 << d));
        uint32_t v = 1; int o = 0;
        do { pw[o++] = v; v <<= 1; if (v >> d & 1) v ^= g; } while (v != 1);
        sdeg[nsmall] = d; sord[nsmall] = o; spow[nsmall] = pw; nsmall++;
    }
}
static int irreducible(void) {
    /* sieve */
    for (int i = 0; i < nsmall; i++) {
        if (2 * sdeg[i] > M) break;
        uint32_t r = 0; for (int t = 0; t < NE; t++) r ^= spow[i][E[t] % sord[i]];
        if (r == 0) return 0;
    }
    /* Rabin */
    NW = (M + 63) / 64 + 1;
    int primes[16], np = 0, mm = M;
    for (int p = 2; p * p <= mm; p++) if (mm % p == 0) { primes[np++] = p; while (mm % p == 0) mm /= p; }
    if (mm > 1) primes[np++] = mm;
    P x; memset(&x, 0, sizeof x); x.w[0] = 2;
    if (M == 1) return 1;
    P fpoly; memset(&fpoly, 0, sizeof fpoly); for (int t = 0; t < NE; t++) fpoly.w[E[t] >> 6] ^= 1ULL << (E[t] & 63);
    P cur = x; /* x^(2^0) */
    P saved[16]; int need[16]; for (int i = 0; i < np; i++) need[i] = M / primes[i];
    for (int i = 1; i <= M; i++) {
        P nx; sqr(&nx, &cur); cur = nx;
        for (int j = 0; j < np; j++) if (need[j] == i) saved[j] = cur;
    }
    if (!(cur.w[0] == 2 && degp(&cur, NW) == 1)) return 0;
    for (int j = 0; j < np; j++) { P h = saved[j]; h.w[0] ^= 2; if (!gcd_is_one(fpoly, h)) return 0; }
    return 1;
}
static void setf(int m, int *ex, int ne) { /* ex sorted descending, ex[0]=m */
    M = m; NE = ne; for (int i = 0; i < ne; i++) E[i] = ex[i]; NW = (M + 63) / 64 + 1;
}
int main(int argc, char **argv) {
    for (int i = 0; i < 256; i++) { uint16_t s = 0; for (int j = 0; j < 8; j++) if (i >> j & 1) s |= 1 << (2 * j); SPR[i] = s; }
    build_small();
    const char *mode = argv[1];
    if (!strcmp(mode, "one")) {
        int ex[8], ne = 0; for (int i = 2; i < argc; i++) ex[ne++] = atoi(argv[i]);
        setf(ex[0], ex, ne); printf("%d\n", irreducible()); return 0;
    }
    int MLO = atoi(argv[2]), MHI = atoi(argv[3]);
    for (int m = MLO; m <= MHI; m++) {
        if (!strcmp(mode, "sec")) {
            for (int c = 1; 3 * c + 1 <= m; c++) { int b = m - 2 * c; if (b <= c) continue;
                int ex[5] = {m, b + c, b, c, 0}; setf(m, ex, 5); if (irreducible()) printf("%d %d %d\n", m, b, c); }
        } else if (!strcmp(mode, "fst")) {
            for (int c = 1; c < m; c++) { if ((m - c) % 2) continue; int b = (m - c) / 2; if (b <= c) continue;
                int ex[5] = {m, b + c, b, c, 0}; setf(m, ex, 5); if (irreducible()) printf("%d %d %d\n", m, b, c); }
        } else if (!strcmp(mode, "tri")) {
            int found = 0;
            for (int k = 1; 2 * k <= m && !found; k++) { int ex[3] = {m, k, 0}; setf(m, ex, 3); if (irreducible()) found = k; }
            printf("%d %d\n", m, found);
        }
        fflush(stdout);
    }
    return 0;
}
