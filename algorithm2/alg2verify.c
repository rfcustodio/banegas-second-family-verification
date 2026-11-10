/*
 * alg2verify.c -- symbolic verification of Algorithm 2 (chain construction) for the
 * reduction modulo f_{b,c} = x^{b+2c}+x^{b+c}+x^b+x^c+1, all b>c>=1, MLO<=m<=MHI.
 * Checks: (1) outputs equal the rows of the reduction matrix; (2) number of XOR gates
 * equals 3m-3-N(b,c), N = #{1<=u<=b+c-1 : floor(u/c) = 2 mod 3}; (3) the closed formula
 * N = c*floor((b+c)/3c) + max(0,(b+c) mod 3c - 2c); (4) depth statistics and the bound
 * depth <= 2*floor((n-c)/3c) + 6. Also counts members improved over 3m-c-3.
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#define MAXM 1100
#define NWMAX ((2 * MAXM) / 64 + 2)
typedef struct { uint64_t w[NWMAX]; } bs;
static int NW;
static inline void bclr(bs *a) { memset(a->w, 0, sizeof(uint64_t) * NW); }
static inline void bset(bs *a, int i) { a->w[i >> 6] |= 1ULL << (i & 63); }
static inline void bxor(bs *r, const bs *a, const bs *b) { for (int k = 0; k < NW; k++) r->w[k] = a->w[k] ^ b->w[k]; }
static inline void bcpy(bs *r, const bs *a) { memcpy(r->w, a->w, sizeof(uint64_t) * NW); }
static inline int beq(const bs *a, const bs *b) { return memcmp(a->w, b->w, sizeof(uint64_t) * NW) == 0; }
static inline int bzero_(const bs *a) { for (int k = 0; k < NW; k++) if (a->w[k]) return 0; return 1; }
static bs IN[2 * MAXM], E[MAXM], P[2 * MAXM], U[MAXM], R[MAXM], ROW[MAXM], ZERO;
static int dE[MAXM], dP[2 * MAXM], dU[MAXM];
static int hasE[MAXM], hasP[2 * MAXM];
static int imax(int a, int b) { return a > b ? a : b; }
int main(int argc, char **argv) {
    int MLO = atoi(argv[1]), MHI = atoi(argv[2]);
    long npairs = 0, fail = 0, improved = 0, worse = 0; int maxExcess = -100;
    for (int m = MLO; m <= MHI; m++) for (int c = 1; 3 * c + 1 <= m; c++) {
        int b = m - 2 * c; if (b <= c) continue;
        npairs++;
        int n = m - 2, NN = 2 * m - 1, gates = 0, bad = 0, depth = 0;
        NW = (NN + 63) / 64; bclr(&ZERO);
        for (int j = 0; j < NN; j++) { bclr(&IN[j]); bset(&IN[j], j); }
#define H(s) (((s) >= 0 && (s) <= n) ? &IN[m + (s)] : &ZERO)
#define SIG(t) ((((t) + 1) / c) % 3)
        /* free values: E_t = h_t for t > n-c ; P_k = h_{k-c} for k > n-c */
        memset(hasE, 0, sizeof(int) * m); memset(hasP, 0, sizeof(int) * 2 * m);
        for (int t = n - c + 1; t <= n + 2 * c && t < MAXM; t++) { bcpy(&E[t], H(t)); dE[t] = 0; hasE[t] = 1; }
        for (int k = n - c + 1; k <= n + 3 * c && k < 2 * MAXM; k++) { bcpy(&P[k], H(k - c)); dP[k] = 0; hasP[k] = 1; }
        /* loop 1: strands, descending */
        for (int i = n - c; i >= 0; i--) {
            if (i >= 2 * c - 1 && SIG(i) != 1) {
                if (!hasE[i + c]) bad |= 8;
                bxor(&P[i], H(i - c), &E[i + c]); dP[i] = dE[i + c] + 1; hasP[i] = 1; gates++;
            }
            if (SIG(i) != 2) {
                if (!hasP[i + 2 * c]) bad |= 8;
                bxor(&E[i], H(i), &P[i + 2 * c]); dE[i] = dP[i + 2 * c] + 1; hasE[i] = 1; gates++;
            }
        }
        /* loop 2: remaining P_k */
        for (int k = 2 * c - 1; k <= n - c; k++) if (SIG(k) == 1) {
            if (!hasE[k - c] || !hasE[k]) bad |= 8;
            bxor(&P[k], &E[k - c], &E[k]); dP[k] = imax(dE[k - c], dE[k]) + 1; hasP[k] = 1; gates++;
        }
        /* U */
        for (int k = 0; k < m; k++) {
            if (k <= c - 2) { bxor(&U[k], &E[k], H(k + b + c)); dU[k] = dE[k] + 1; gates++; }
            else if (k == c - 1) { bcpy(&U[k], &E[k]); dU[k] = dE[k]; }
            else if (k <= 2 * c - 2) { bxor(&U[k], &U[k - c], &E[k]); dU[k] = imax(dU[k - c], dE[k]) + 1; gates++; }
            else if (k <= n - c) { bcpy(&U[k], &P[k]); dU[k] = dP[k]; }
            else { bcpy(&U[k], H(k - c)); dU[k] = 0; }
        }
        for (int i = 0; i < m; i++) {
            bs t; bxor(&t, &IN[i], &U[i]); int dt = dU[i] + 1; gates++;
            if (i >= b) { bxor(&R[i], &t, &U[i - b]); dt = imax(dt, dU[i - b]) + 1; gates++; } else bcpy(&R[i], &t);
            depth = imax(depth, dt);
        }
        /* reduction matrix */
        static uint8_t col[MAXM + 1];
        for (int i = 0; i < m; i++) bclr(&ROW[i]);
        memset(col, 0, m + 1); col[0] = 1;
        for (int j = 0; j < NN; j++) {
            if (j > 0) { int top = col[m - 1]; memmove(col + 1, col, m - 1); col[0] = 0;
                if (top) { col[0] ^= 1; col[c] ^= 1; col[b] ^= 1; col[b + c] ^= 1; } }
            for (int i = 0; i < m; i++) if (col[i]) bset(&ROW[i], j);
        }
        for (int i = 0; i < m; i++) if (!beq(&R[i], &ROW[i])) { bad |= 1; break; }
        int N = 0; for (int u = 1; u <= b + c - 1; u++) if ((u / c) % 3 == 2) N++;
        int Nf = c * ((b + c) / (3 * c)) + imax(0, (b + c) % (3 * c) - 2 * c);
        if (N != Nf) bad |= 4;
        if (gates != 3 * m - 3 - N) bad |= 2;
        int bound = 2 * ((n - c) / (3 * c)) + 6;
        if (depth > bound) bad |= 16;
        if (depth - bound > maxExcess) maxExcess = depth - bound;
        if (3 * m - 3 - N < 3 * m - c - 3) improved++;
        if (3 * m - 3 - N > 3 * m - c - 3) worse++;
        if ((N > c) != (b >= 4 * c + 1)) bad |= 32;
        if (argc > 3 && b == atoi(argv[3]) && c == atoi(argv[4])) printf("INFO b=%d c=%d gates=%d depth=%d\n", b, c, gates, depth);
        if (bad) { fail++; if (fail < 20) printf("FAIL m=%d b=%d c=%d code=%d gates=%d N=%d\n", m, b, c, bad, gates, N); }
    }
    printf("SUMMARY m=[%d,%d] pairs=%ld failures=%ld improved=%ld worse=%ld max(depth-bound)=%d\n", MLO, MHI, npairs, fail, improved, worse, maxExcess);
    return 0;
}
