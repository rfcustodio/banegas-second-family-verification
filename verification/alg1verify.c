/*
 * alg1verify.c -- independent verification of Algorithm 1 (closed-form reduction
 * modulo f_{b,c} = x^{b+2c}+x^{b+c}+x^b+x^c+1) for all b>c>=1 with MLO<=m<=MHI.
 *
 * For each pair it checks, exactly (symbolically over the 2m-1 inputs):
 *   (1) Algorithm 1 outputs equal the rows of the reduction matrix R_f;
 *   (2) the number of XOR gates equals 3m-c-3;
 *   (3) the depth is <= floor(n/3c)+4 (and <=5 when b<=4c+1); records depth stats;
 *   (4) the low-depth (doubling) variant computes the same comb sums, uses exactly
 *       3m-c-3 + sum_{j=1}^{s-1} max(0,n+1-3c 2^j) gates and has depth <= s+4;
 *   (5) if g=gcd(b,c)>1: every gate stays in one strip (index class mod g),
 *       strip g-1 uses 3k-c'-3 gates and every other strip 3k-c' gates;
 *   (6) the word-level formulas (Corollary) on NRAND random inputs.
 * Prints one line per failure and a summary.
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>

#define MAXM 1100
#define NWMAX ((2 * MAXM) / 64 + 2)
#define NRAND 8

typedef struct { uint64_t w[NWMAX]; } bs;
static int NW;

static inline void bclr(bs *a) { memset(a->w, 0, sizeof(uint64_t) * NW); }
static inline void bset(bs *a, int i) { a->w[i >> 6] |= 1ULL << (i & 63); }
static inline int bget(const bs *a, int i) { return (a->w[i >> 6] >> (i & 63)) & 1; }
static inline void bxor(bs *r, const bs *a, const bs *b) { for (int k = 0; k < NW; k++) r->w[k] = a->w[k] ^ b->w[k]; }
static inline void bcpy(bs *r, const bs *a) { memcpy(r->w, a->w, sizeof(uint64_t) * NW); }
static inline int beq(const bs *a, const bs *b) { return memcmp(a->w, b->w, sizeof(uint64_t) * NW) == 0; }

static bs TV[MAXM]; static long coincGeneric=0, coincSpecial=0, coincSpecialNonEq=0;
static bs Hs[MAXM], C[MAXM], Cd[MAXM], Z[MAXM], U[MAXM], R[MAXM], ROW[MAXM], IN[2 * MAXM];
static int dH[MAXM], dC[MAXM], dCd[MAXM], dZ[MAXM], dU[MAXM], dR[MAXM];
static int cZ[MAXM], cU[MAXM]; /* for strip check: is value a plain wire (0) or computed */

static uint64_t rng = 88172645463325252ULL;
static inline uint64_t xr(void) { rng ^= rng << 13; rng ^= rng >> 7; rng ^= rng << 17; return rng; }

static int gcd(int a, int b) { while (b) { int t = a % b; a = b; b = t; } return a; }
static int imax(int a, int b) { return a > b ? a : b; }

/* bit-level polynomial long division of D (2m-1 bits) by f_{b,c}: remainder in D */
static void longdiv(uint8_t *D, int m, int b, int c) {
    for (int i = 2 * m - 2; i >= m; i--) if (D[i]) {
        D[i] = 0; int s = i - m;
        D[s + b + c] ^= 1; D[s + b] ^= 1; D[s + c] ^= 1; D[s] ^= 1;
    }
}

int main(int argc, char **argv) {
    int MLO = atoi(argv[1]), MHI = atoi(argv[2]);
    long npairs = 0, fail = 0, depthStatN = 0, depthStatEq = 0, depthStatN300 = 0;
    long hist[8] = {0};
    long maxDepthExcess = -100;
    for (int m = MLO; m <= MHI; m++) {
        for (int c = 1; 3 * c + 1 <= m; c++) {
            int b = m - 2 * c; if (b <= c) continue;
            npairs++;
            int n = m - 2, N = 2 * m - 1;
            NW = (N + 63) / 64;
            /* inputs */
            for (int j = 0; j < N; j++) { bclr(&IN[j]); bset(&IN[j], j); }
            for (int s = 0; s <= n; s++) { bcpy(&Hs[s], &IN[m + s]); dH[s] = 0; }
            int g = gcd(b, c);
            int gates = 0, depth = 0, bad = 0;
            /* strip bookkeeping */
            long stripGates[MAXM]; if (g > 1) memset(stripGates, 0, sizeof(long) * g);
#define CLS(idx) ((idx) % g)
#define GATE(cls_out, cls_a, cls_b) do { gates++; if (g > 1) { if ((cls_a) != (cls_out) || (cls_b) != (cls_out)) bad |= 16; stripGates[cls_out]++; } } while (0)
            /* comb sums, descending; class of C_t is t mod g (h_t = d_{m+t}, m = 0 mod g) */
            for (int t = n; t >= 0; t--) {
                if (t + 3 * c <= n) { bxor(&C[t], &Hs[t], &C[t + 3 * c]); dC[t] = imax(dH[t], dC[t + 3 * c]) + 1; GATE(CLS(t), CLS(m + t), CLS(t + 3 * c)); }
                else { bcpy(&C[t], &Hs[t]); dC[t] = 0; }
            }
            /* shared pairs */
            for (int i = 0; i <= c - 2; i++) { bxor(&Z[i], &C[i], &Hs[i + b + c]); dZ[i] = imax(dC[i], 0) + 1; GATE(CLS(i), CLS(i), CLS(m + i + b + c)); }
            /* U */
            for (int k = 0; k < m; k++) {
                if (k <= c - 2) { bxor(&U[k], &Z[k], &C[k + c]); dU[k] = imax(dZ[k], dC[k + c]) + 1; GATE(CLS(k), CLS(k), CLS(k + c)); }
                else if (k == c - 1) { bxor(&U[k], &C[c - 1], &C[2 * c - 1]); dU[k] = imax(dC[c - 1], dC[2 * c - 1]) + 1; GATE(CLS(k), CLS(c - 1), CLS(2 * c - 1)); }
                else if (k <= 2 * c - 2) { bxor(&U[k], &Z[k - c], &C[k + c]); dU[k] = imax(dZ[k - c], dC[k + c]) + 1; GATE(CLS(k), CLS(k - c), CLS(k + c)); }
                else if (k <= b + c - 2) { bxor(&U[k], &C[k - c], &C[k + c]); dU[k] = imax(dC[k - c], dC[k + c]) + 1; GATE(CLS(k), CLS(k - c), CLS(k + c)); }
                else { bcpy(&U[k], &C[k - c]); dU[k] = dC[k - c]; }
            }
            /* outputs */
            for (int i = 0; i < m; i++) {
                bs t; bxor(&t, &IN[i], &U[i]); bcpy(&TV[i], &t); int dt = dU[i] + 1; GATE(CLS(i), CLS(i), CLS(i));
                if (i >= b) { bxor(&R[i], &t, &U[i - b]); dR[i] = imax(dt, dU[i - b]) + 1; GATE(CLS(i), CLS(i), CLS(i - b)); }
                else { bcpy(&R[i], &t); dR[i] = dt; }
                depth = imax(depth, dR[i]);
            }

            /* coincidence check: any computed gate value equal to 0, an input, or another gate value */
            {
                static uint64_t hv[8 * MAXM]; static const bs *hp[8 * MAXM]; int nh = 0;
                #define HASHB(x) ({ uint64_t _h = 1469598103934665603ULL; for (int _k = 0; _k < NW; _k++) { _h ^= (x)->w[_k]; _h *= 1099511628211ULL; _h ^= _h >> 29; } _h; })
                for (int j = 0; j < N; j++) { hp[nh] = &IN[j]; hv[nh++] = HASHB(&IN[j]); }
                { static bs z; bclr(&z); hp[nh] = &z; hv[nh++] = HASHB(&z); }
                int base0 = nh;
                for (int t = 0; t <= n; t++) if (t + 3 * c <= n) { hp[nh] = &C[t]; hv[nh++] = HASHB(&C[t]); }
                for (int i = 0; i <= c - 2; i++) { hp[nh] = &Z[i]; hv[nh++] = HASHB(&Z[i]); }
                for (int k = 0; k <= b + c - 2 && k < m; k++) { hp[nh] = &U[k]; hv[nh++] = HASHB(&U[k]); }
                for (int i = 0; i < m; i++) { hp[nh] = &TV[i]; hv[nh++] = HASHB(&TV[i]); if (i >= b) { hp[nh] = &R[i]; hv[nh++] = HASHB(&R[i]); } }
                int coinc = 0;
                /* sort and look for duplicates involving a gate value */
                int cmpu(const void *x, const void *y) { uint64_t a = *(uint64_t *)x, b2 = *(uint64_t *)y; return a < b2 ? -1 : a > b2; }
                (void)base0;
                (void)cmpu;
                /* exact O(nh^2/blocks) check via sorting indices by hash */
                static int idx[8 * MAXM]; for (int q = 0; q < nh; q++) idx[q] = q;
                int cmpi(const void *x, const void *y) { uint64_t a = hv[*(int *)x], b2 = hv[*(int *)y]; return a < b2 ? -1 : a > b2; }
                qsort(idx, nh, sizeof(int), cmpi);
                for (int q = 1; q < nh && !coinc; q++) {
                    int r0 = q - 1;
                    while (r0 >= 0 && hv[idx[r0]] == hv[idx[q]]) { if (beq(hp[idx[r0]], hp[idx[q]])) { coinc = 1; break; } r0--; }
                }
                int bp = b / g, cp = c / g;
                int special = (bp == 2 && cp == 1) || (bp == 3 && cp == 1) || (bp == 4 && cp == 1) || (bp == 5 && cp == 1) || (bp == 3 && cp == 2);
                if (coinc) { if (special) { coincSpecial++; if (!(bp == 2 && cp == 1)) coincSpecialNonEq++; } else { coincGeneric++; printf("COINC generic m=%d b=%d c=%d\n", m, b, c); } }
            }
            /* reduction matrix rows */
            for (int i = 0; i < m; i++) bclr(&ROW[i]);
            {
                static uint8_t col[MAXM + 1];
                memset(col, 0, m + 1); col[0] = 1;
                for (int j = 0; j < N; j++) {
                    if (j > 0) { /* col = x*col mod f */
                        int top = col[m - 1];
                        memmove(col + 1, col, m - 1); col[0] = 0;
                        if (top) { col[0] ^= 1; col[c] ^= 1; col[b] ^= 1; col[b + c] ^= 1; }
                    }
                    for (int i = 0; i < m; i++) if (col[i]) bset(&ROW[i], j);
                }
            }
            for (int i = 0; i < m; i++) if (!beq(&R[i], &ROW[i])) { bad |= 1; break; }
            if (gates != 3 * m - c - 3) bad |= 2;
            int delta = n / (3 * c);
            if (depth > delta + 4) bad |= 4;
            if (b <= 4 * c + 1 && depth > 5) bad |= 4;
            if (depth - delta > maxDepthExcess) maxDepthExcess = depth - delta;
            if (depth - delta >= 0 && depth - delta < 8) hist[depth - delta]++;
            if (m >= 7 && m < 300) { depthStatN++; if (depth == delta + 3) depthStatEq++; }
            if (m <= 300) depthStatN300++;
            /* strip check */
            if (g > 1) {
                int bp = b / g, cp = c / g, k = bp + 2 * cp;
                for (int r = 0; r < g; r++) {
                    long expect = (r == g - 1) ? 3 * k - cp - 3 : 3 * k - cp;
                    if (stripGates[r] != expect) { bad |= 32; break; }
                }
            }
            /* low-depth variant */
            {
                int s = 0; while ((long)3 * c * (1L << s) < n + 1) s++;
                int extra = 0, combGates = 0;
                for (int t = 0; t <= n; t++) { bcpy(&Cd[t], &Hs[t]); dCd[t] = 0; }
                for (int j = 0; j < s; j++) {
                    int sh = 3 * c * (1 << j);
                    for (int t = 0; t + sh <= n; t++) { /* ascending: Cd[t+sh] still old */
                        bxor(&Cd[t], &Cd[t], &Cd[t + sh]); dCd[t] = imax(dCd[t], dCd[t + sh]) + 1; combGates++;
                    }
                    if (j >= 1) extra += imax(0, n + 1 - sh);
                }
                for (int t = 0; t <= n; t++) if (!beq(&Cd[t], &C[t])) { bad |= 64; break; }
                int totalLD = (3 * m - c - 3) - (b - c - 1) + combGates;
                if (totalLD != 3 * m - c - 3 + extra) bad |= 128;
                /* depth of rest with doubling comb depths */
                int dZ2[MAXM], dU2[MAXM], dmax = 0;
                for (int i = 0; i <= c - 2; i++) dZ2[i] = dCd[i] + 1;
                for (int k = 0; k < m; k++) {
                    if (k <= c - 2) dU2[k] = imax(dZ2[k], dCd[k + c]) + 1;
                    else if (k == c - 1) dU2[k] = imax(dCd[c - 1], dCd[2 * c - 1]) + 1;
                    else if (k <= 2 * c - 2) dU2[k] = imax(dZ2[k - c], dCd[k + c]) + 1;
                    else if (k <= b + c - 2) dU2[k] = imax(dCd[k - c], dCd[k + c]) + 1;
                    else dU2[k] = dCd[k - c];
                }
                for (int i = 0; i < m; i++) { int d = dU2[i] + 1; if (i >= b) d = imax(d, dU2[i - b]) + 1; dmax = imax(dmax, d); }
                if (dmax > s + 4) bad |= 256;
                if (b == 527 && c == 22) printf("INFO 571-member: chain gates=%d depth=%d | doubling gates=%d depth=%d s=%d maxteeth=%d\n", gates, depth, totalLD, dmax, s, n / (3 * c) + 1);
            }
            /* word-level corollary on random inputs (bit arrays) */
            {
                static uint8_t D[2 * MAXM], Rref[2 * MAXM], H[MAXM], Cw[MAXM], Q[MAXM], Uw[MAXM], tmp[MAXM];
                int s = 0; while ((long)3 * c * (1L << s) < n + 1) s++;
                for (int trial = 0; trial < NRAND; trial++) {
                    for (int j = 0; j < N; j++) D[j] = xr() & 1;
                    memcpy(Rref, D, N); longdiv(Rref, m, b, c);
                    for (int t = 0; t <= n; t++) H[t] = D[m + t];
                    memcpy(Cw, H, n + 1);
                    for (int j = 0; 3 * c * (1 << j) <= n; j++) {
                        int sh = 3 * c * (1 << j);
                        memcpy(tmp, Cw, n + 1);
                        for (int t = 0; t <= n; t++) Cw[t] ^= (t + sh <= n) ? tmp[t + sh] : 0;
                    }
                    for (int t = 0; t <= n; t++) Q[t] = Cw[t] ^ ((t + c <= n) ? Cw[t + c] : 0) ^ ((t + b + c <= n) ? H[t + b + c] : 0);
                    for (int t = 0; t < m; t++) Uw[t] = ((t <= n) ? Q[t] : 0) ^ ((t - c >= 0 && t - c <= n) ? Q[t - c] : 0);
                    for (int i = 0; i < m; i++) { int r = D[i] ^ Uw[i] ^ ((i - b >= 0) ? Uw[i - b] : 0); if (r != Rref[i]) { bad |= 512; break; } }
                    if (bad & 512) break;
                }
            }
            if (bad) { fail++; printf("FAIL m=%d b=%d c=%d code=%d gates=%d depth=%d\n", m, b, c, bad, gates, depth); }
        }
    }
    printf("SUMMARY m=[%d,%d] pairs=%ld failures=%ld pairs(m<=300 in range)=%ld depth==delta+3 for 7<=m<300: %ld/%ld maxExcess=%ld\n",
           MLO, MHI, npairs, fail, depthStatN300, depthStatEq, depthStatN, maxDepthExcess);
    printf("COINCIDENCES generic=%ld special=%ld (special not equally spaced=%ld)\n", coincGeneric, coincSpecial, coincSpecialNonEq);
    printf("HIST depth-delta:"); for (int i = 0; i < 8; i++) printf(" %d:%ld", i, hist[i]); printf("\n");
    return 0;
}
