/*
 * xorred.c  --  XOR cost of modular reduction in GF(2)[x]/(f), f a pentanomial.
 *
 *   irreducibility test (Rabin/Ben-Or, full for any m),
 *   reduction matrix R_f (m x (2m-1)),
 *   d-XOR (naive count), Paar's greedy (= Conta-XOR step 3) with deterministic
 *   or random tie-breaking, XOR depth, and circuit verification.
 *
 * usage:
 *   xorred scan m amax K seed        all a>b>c>=1, a<=amax; prints irreducible ones
 *   xorred one  m a b c K seed       single polynomial, verbose
 *   xorred tri  m k K seed           trinomial x^m+x^k+1
 * output columns: m a b c dxor paar paar_depth rpaar rpaar_depth
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>

#define MAXM 1100
#define W ((2*MAXM)/64+2)
typedef struct { uint64_t w[W]; } poly;

static int NW; /* words in use */

static inline int getb(const poly *p, int i) { return (p->w[i >> 6] >> (i & 63)) & 1; }
static inline void flip(poly *p, int i) { p->w[i >> 6] ^= 1ULL << (i & 63); }

static int deg(const poly *p) {
    for (int k = NW - 1; k >= 0; k--) if (p->w[k]) return 64 * k + 63 - __builtin_clzll(p->w[k]);
    return -1;
}
static int E[8], NE; /* exponents of f, E[0]=m */
static void reduce(poly *p) {
    int m = E[0];
    for (int i = deg(p); i >= m; i--) if (getb(p, i)) {
        for (int t = 0; t < NE; t++) flip(p, i - m + E[t]);
    }
}
static uint16_t SPR[256];
static void shr_into(const poly *p, int s, poly *t) { /* t = p >> s */
    int ws = s >> 6, bs = s & 63;
    for (int k = 0; k < NW; k++) {
        uint64_t lo = (k + ws < NW) ? p->w[k + ws] : 0, hi = (k + ws + 1 < NW) ? p->w[k + ws + 1] : 0;
        t->w[k] = bs ? (lo >> bs) | (hi << (64 - bs)) : lo;
    }
}
static void xor_shl(poly *p, const poly *t, int s) { /* p ^= t << s */
    int ws = s >> 6, bs = s & 63;
    for (int k = NW - 1; k >= ws; k--) {
        uint64_t lo = t->w[k - ws], lo2 = (k - ws - 1 >= 0) ? t->w[k - ws - 1] : 0;
        p->w[k] ^= bs ? (lo << bs) | (lo2 >> (64 - bs)) : lo;
    }
}
static void reduce_fast(poly *p) {
    int m = E[0];
    for (;;) {
        if (deg(p) < m) return;
        poly t; shr_into(p, m, &t);
        /* clear bits >= m */
        int wm = m >> 6, bm = m & 63;
        p->w[wm] &= bm ? ((1ULL << bm) - 1) : 0;
        for (int k = wm + 1; k < NW; k++) p->w[k] = 0;
        for (int e = 1; e < NE; e++) xor_shl(p, &t, E[e]);
    }
}
static void sqr(const poly *a, poly *r) {
    poly t; memset(&t, 0, sizeof t);
    if (!SPR[1]) for (int i = 0; i < 256; i++) { uint16_t v = 0; for (int j = 0; j < 8; j++) if (i >> j & 1) v |= 1 << (2 * j); SPR[i] = v; }
    for (int k = 0; 2 * k + 1 < NW; k++) {
        uint64_t w = a->w[k], lo = 0, hi = 0;
        for (int j = 0; j < 4; j++) { lo |= (uint64_t)SPR[(w >> (8 * j)) & 255] << (16 * j); hi |= (uint64_t)SPR[(w >> (32 + 8 * j)) & 255] << (16 * j); }
        t.w[2 * k] = lo; t.w[2 * k + 1] = hi;
    }
    reduce_fast(&t); *r = t;
}
/* general polynomial gcd over GF(2) with bit ops (small helper) */
static void pmod_general(poly *a, const poly *b) {
    int db = deg(b);
    for (int i = deg(a); i >= db; i--) if (getb(a, i))
        for (int j = 0; j <= db; j++) if (getb(b, j)) flip(a, i - db + j);
}
static int gcd_is_one(poly a, poly b) {
    while (deg(&b) >= 0) { poly t = a; pmod_general(&t, &b); a = b; b = t; }
    return deg(&a) == 0;
}
static int irreducible(void) {
    int m = E[0];
    /* x^(2^k) mod f for k=1..m; Rabin: x^(2^m)=x and gcd(x^(2^(m/q))-x,f)=1 */
    static poly pw[MAXM + 1];
    poly x; memset(&x, 0, sizeof x); flip(&x, 1);
    pw[0] = x;
    for (int k = 1; k <= m; k++) sqr(&pw[k - 1], &pw[k]);
    for (int i = 0; i < NW; i++) if (pw[m].w[i] != x.w[i]) return 0;
    poly f; memset(&f, 0, sizeof f); for (int t = 0; t < NE; t++) flip(&f, E[t]);
    int n = m;
    for (int q = 2; q <= n; q++) if (n % q == 0) {
        int pr = 1; for (int d = 2; d * d <= q; d++) if (q % d == 0) pr = 0;
        if (!pr) continue;
        poly g = pw[m / q]; flip(&g, 1);
        if (!gcd_is_one(f, g)) return 0;
    }
    return 1;
}

/* ---------------- reduction matrix and Paar greedy ---------------- */
#define MAXV 8192
static int nin;                       /* 2m-1 inputs */
static int *row[MAXM], rlen[MAXM], rcap[MAXM];
static int opA[MAXV], opB[MAXV], dep[MAXV];
static int NR;

static void build_rows(void) {
    int m = E[0]; nin = 2 * m - 1; NR = m;
    for (int i = 0; i < m; i++) { rlen[i] = 0; if (!row[i]) { rcap[i] = 64; row[i] = malloc(64 * sizeof(int)); } }
    poly c; memset(&c, 0, sizeof c); flip(&c, 0);
    for (int j = 0; j < nin; j++) {
        for (int i = 0; i < m; i++) if (getb(&c, i)) {
            if (rlen[i] == rcap[i]) { rcap[i] *= 2; row[i] = realloc(row[i], rcap[i] * sizeof(int)); }
            row[i][rlen[i]++] = j;
        }
        /* c <- x*c mod f */
        poly t; memset(&t, 0, sizeof t);
        for (int k = 0; k < NW; k++) t.w[k] = (c.w[k] << 1) | (k ? c.w[k - 1] >> 63 : 0);
        reduce(&t); c = t;
    }
}
static int dxor(void) { int s = 0; for (int i = 0; i < NR; i++) s += rlen[i] - 1; return s; }

/* hash map pair -> count */
#define HS (1 << 20)
static uint32_t hkey[HS]; static int hcnt[HS]; static int htouch[HS], nt;
static inline void hinc(uint32_t key) {
    uint32_t h = (key * 2654435761u) & (HS - 1);
    while (hkey[h] && hkey[h] != key) h = (h + 1) & (HS - 1);
    if (!hkey[h]) { hkey[h] = key; hcnt[h] = 0; htouch[nt++] = h; }
    hcnt[h]++;
}
static uint64_t rng;
static inline uint64_t rnd(void) { rng ^= rng << 13; rng ^= rng >> 7; rng ^= rng << 17; return rng; }

static int R[MAXM][512], RL[MAXM];
static int huff_depth(int *d, int n) { /* optimal depth combining n signals with given depths */
    int a[512]; memcpy(a, d, n * sizeof(int));
    while (n > 1) {
        int i1 = 0; for (int i = 1; i < n; i++) if (a[i] < a[i1]) i1 = i;
        int v1 = a[i1]; a[i1] = a[--n];
        int i2 = 0; for (int i = 1; i < n; i++) if (a[i] < a[i2]) i2 = i;
        a[i2] = (a[i2] > v1 ? a[i2] : v1) + 1;
    }
    return n ? a[0] : 0;
}
/* returns XOR count; *depth set; random tie-breaking if rand_ties */
static int nv;
static int paar(int rand_ties, int *depth) {
    for (int i = 0; i < NR; i++) { RL[i] = rlen[i]; memcpy(R[i], row[i], rlen[i] * sizeof(int)); }
    nv = nin; for (int v = 0; v < nin; v++) dep[v] = 0;
    for (;;) {
        nt = 0;
        for (int i = 0; i < NR; i++)
            for (int x = 0; x < RL[i]; x++) for (int y = x + 1; y < RL[i]; y++) {
                int u = R[i][x], v = R[i][y]; if (u > v) { int t = u; u = v; v = t; }
                hinc(((uint32_t)(u + 1) << 16) | (uint32_t)(v + 1));
            }
        int best = 1, bh = -1, ties = 0; uint32_t bkey = 0xffffffff;
        for (int k = 0; k < nt; k++) {
            int h = htouch[k];
            if (hcnt[h] > best) { best = hcnt[h]; bh = h; ties = 1; bkey = hkey[h]; }
            else if (hcnt[h] == best && best > 1) {
                ties++;
                if (rand_ties) { if (rnd() % ties == 0) { bh = h; bkey = hkey[h]; } }
                else if (hkey[h] < bkey) { bh = h; bkey = hkey[h]; }
            }
        }
        for (int k = 0; k < nt; k++) hkey[htouch[k]] = 0;
        if (bh < 0) break;
        int u = (bkey >> 16) - 1, v = (bkey & 0xffff) - 1;
        int w = nv++; opA[w] = u; opB[w] = v; dep[w] = (dep[u] > dep[v] ? dep[u] : dep[v]) + 1;
        for (int i = 0; i < NR; i++) {
            int iu = -1, iv = -1;
            for (int x = 0; x < RL[i]; x++) { if (R[i][x] == u) iu = x; else if (R[i][x] == v) iv = x; }
            if (iu >= 0 && iv >= 0) {
                R[i][iu] = w; R[i][iv] = R[i][--RL[i]];
            }
        }
    }
    int cost = nv - nin, dm = 0;
    for (int i = 0; i < NR; i++) {
        cost += RL[i] - 1;
        int d[512]; for (int x = 0; x < RL[i]; x++) d[x] = dep[R[i][x]];
        int dd = huff_depth(d, RL[i]); if (dd > dm) dm = dd;
    }
    *depth = dm; return cost;
}
/* verify: evaluate the program on random inputs vs direct reduction */
static int verify(void) {
    int m = E[0];
    for (int trial = 0; trial < 200; trial++) {
        static uint8_t val[MAXV];
        poly D; memset(&D, 0, sizeof D);
        for (int j = 0; j < nin; j++) { val[j] = rnd() & 1; if (val[j]) flip(&D, j); }
        for (int w = nin; w < nv; w++) val[w] = val[opA[w]] ^ val[opB[w]];
        reduce(&D);
        for (int i = 0; i < m; i++) { int s = 0; for (int x = 0; x < RL[i]; x++) s ^= val[R[i][x]]; if (s != getb(&D, i)) return 0; }
    }
    return 1;
}

static void setpoly(int m, int *ex, int k) {
    NE = 0; E[NE++] = m; for (int i = 0; i < k; i++) E[NE++] = ex[i]; E[NE++] = 0;
    NW = (2 * m) / 64 + 2;
}
static void run(int K, int verbose) {
    build_rows();
    int d0 = dxor(), dp, p = paar(0, &dp);
    if (!verify()) { fprintf(stderr, "VERIFY FAIL paar\n"); exit(1); }
    int best = p, bd = dp;
    for (int r = 0; r < K; r++) {
        int dd, c = paar(1, &dd);
        if (c < best || (c == best && dd < bd)) { best = c; bd = dd; if (!verify()) { fprintf(stderr, "VERIFY FAIL\n"); exit(1); } }
    }
    printf("%d", E[0]); for (int t = 1; t < NE - 1; t++) printf(" %d", E[t]);
    printf(" %d %d %d %d %d\n", d0, p, dp, best, bd); fflush(stdout);
}
int main(int argc, char **argv) {
    if (argc < 2) return 1;
    if (!strcmp(argv[1], "scan")) {
        int m = atoi(argv[2]), amax = atoi(argv[3]), K = atoi(argv[4]); rng = atoll(argv[5]) | 1;
        int bmin = argc > 6 ? atoi(argv[6]) : 1; /* optional: minimum a */
        for (int a = 3; a <= amax && a < m; a++) {
            if (a < bmin) continue;
            for (int b = 2; b < a; b++) for (int c = 1; c < b; c++) {
                int ex[3] = {a, b, c}; setpoly(m, ex, 3);
                if (irreducible()) run(K, 0);
            }
        }
    } else if (!strcmp(argv[1], "one")) {
        int m = atoi(argv[2]); int ex[3] = {atoi(argv[3]), atoi(argv[4]), atoi(argv[5])};
        int K = atoi(argv[6]); rng = atoll(argv[7]) | 1;
        setpoly(m, ex, 3);
        printf("# irreducible=%d\n", irreducible()); run(K, 1);
    } else if (!strcmp(argv[1], "tri1")) {
        int m = atoi(argv[2]); int ex[1] = {atoi(argv[3])}; int K = atoi(argv[4]); rng = atoll(argv[5]) | 1;
        setpoly(m, ex, 1);
        printf("# irreducible=%d\n", irreducible()); run(K, 1);
    } else if (!strcmp(argv[1], "list")) { /* stdin: m a b c ; no irreducibility test */
        int K = atoi(argv[2]); rng = atoll(argv[3]) | 1; int m, a, b, c;
        while (scanf("%d %d %d %d", &m, &a, &b, &c) == 4) { int ex[3] = {a, b, c}; setpoly(m, ex, 3); run(K, 0); }
    } else if (!strcmp(argv[1], "qmp") || !strcmp(argv[1], "fact")) { /* list irreducible QMPs / factorable */
        int m = atoi(argv[2]); int isq = !strcmp(argv[1], "qmp");
        for (int a = 3; a < m; a++) for (int b = 2; b < a; b++) for (int c = 1; c < b; c++) {
            int ok = 0;
            if (isq) {
                int g[4] = {c, b - c, a - b, m - a}, sums[10], n = 0;
                for (int i = 0; i < 4; i++) { int s2 = 0; for (int j = i; j < 4; j++) { s2 += g[j]; sums[n++] = s2; } }
                for (int x = 0; x < 10 && !ok; x++) { int cnt = 0; for (int y = 0; y < 10; y++) cnt += sums[y] == sums[x]; if (cnt >= 3) ok = 1; }
            } else ok = (a == b + c);
            if (!ok) continue;
            int ex[3] = {a, b, c}; setpoly(m, ex, 3);
            if (irreducible()) printf("%d %d %d %d\n", m, a, b, c);
        }
    } else if (!strcmp(argv[1], "cube")) { /* x^m+(x^c+1)^3 irreducible, m<=M */
        int M = atoi(argv[2]);
        for (int m = 4; m <= M; m++) for (int c = 1; 3 * c < m; c++) {
            int ex[3] = {3 * c, 2 * c, c}; setpoly(m, ex, 3);
            if (irreducible()) printf("%d %d\n", m, c);
        }
    } else if (!strcmp(argv[1], "fam2")) { /* x^{b+2c}+x^{b+c}+x^b+x^c+1 irreducible, m in [M0,M1] */
        int M0 = atoi(argv[2]), M1 = atoi(argv[3]);
        for (int m = M0; m <= M1; m++) for (int c = 1; 3 * c < m; c++) {
            int b = m - 2 * c; int ex[3] = {b + c, b, c}; setpoly(m, ex, 3);
            if (irreducible()) printf("%d %d %d\n", m, b, c);
        }
    } else if (!strcmp(argv[1], "fam1")) { /* BCP: x^{2b+c}+x^{b+c}+x^b+x^c+1 */
        int M0 = atoi(argv[2]), M1 = atoi(argv[3]);
        for (int m = M0; m <= M1; m++) for (int c = 1; 3 * c < m; c++) {
            if ((m - c) % 2) continue; int b = (m - c) / 2; if (b <= c) continue;
            int ex[3] = {b + c, b, c}; setpoly(m, ex, 3);
            if (irreducible()) printf("%d %d %d\n", m, b, c);
        }
    } else if (!strcmp(argv[1], "tri")) {
        int M0 = atoi(argv[2]), M1 = atoi(argv[3]);
        for (int m = M0; m <= M1; m++) { int found = 0; for (int k = 1; k <= m / 2 && !found; k++) { int ex[1] = {k}; setpoly(m, ex, 1); if (irreducible()) { printf("%d %d\n", m, k); found = 1; } } }
    } else if (!strcmp(argv[1], "irr")) { /* list irreducible pentanomials only */
        int m = atoi(argv[2]), amax = atoi(argv[3]);
        for (int a = 3; a <= amax && a < m; a++) for (int b = 2; b < a; b++) for (int c = 1; c < b; c++) {
            int ex[3] = {a, b, c}; setpoly(m, ex, 3);
            if (irreducible()) printf("%d %d %d %d\n", m, a, b, c);
        }
    }
    return 0;
}
