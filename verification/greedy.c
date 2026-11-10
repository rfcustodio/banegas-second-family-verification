/*
 * greedy.c -- Paar-style greedy pair substitution (as in Conta-XOR) on the
 * reduction matrix of a sparse polynomial over F_2.
 *
 *   greedy fam2 MLO MHI RUNS     all second-family members b>c>=1, MLO<=m<=MHI
 *       prints: m b c dXOR CX(lexicographic) bestRandom(RUNS runs, -1 if RUNS=0) closed
 *   greedy one RUNS m e1 ... 0   arbitrary sparse polynomial
 *
 * Rows: row i = { j : coefficient of x^i in x^j mod f is 1 }, j = 0..2m-2.
 * Step: count pair frequencies over all rows; take the most frequent pair
 * (ties: lexicographically smallest (a,b), a<b, with temporaries numbered after
 * the inputs in creation order; or uniformly random among tied pairs); replace
 * it by a new temporary in every row containing both. Stop when no pair occurs
 * twice. Cost = #temporaries + sum over rows of (|row|-1).
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>

#define MAXV 8000
static int *rows[1200], rlen[1200], rcap[1200];
static int M, NR;
static uint16_t *cnt; /* V x V */
static int V;
static uint64_t rs = 0x9E3779B97F4A7C15ULL;
static inline uint64_t xr(void) { rs ^= rs << 13; rs ^= rs >> 7; rs ^= rs << 17; return rs; }

static int TOP = -1;
static void build(int m, int *ex, int ne) {
    int top = TOP >= 0 ? TOP : 2 * m - 2;
    M = m; NR = m;
    static uint8_t col[1300];
    memset(col, 0, sizeof col); col[0] = 1;
    for (int i = 0; i < m; i++) rlen[i] = 0;
    for (int j = 0; j <= top; j++) {
        if (j > 0) { int top = col[m - 1]; memmove(col + 1, col, m - 1); col[0] = 0; if (top) for (int t = 1; t < ne; t++) col[ex[t]] ^= 1; }
        for (int i = 0; i < m; i++) if (col[i]) {
            if (rlen[i] == rcap[i]) { rcap[i] = rcap[i] ? 2 * rcap[i] : 16; rows[i] = realloc(rows[i], sizeof(int) * rcap[i]); }
            rows[i][rlen[i]++] = j; /* ascending */
        }
    }
}
static int cmpint(const void *a, const void *b) { return *(int *)a - *(int *)b; }
/* returns cost; rows are modified */
static int run(int randomize, int *dxor) {
    int next = (TOP >= 0 ? TOP + 1 : 2 * M - 1), temps = 0;
    int dx = 0; for (int i = 0; i < NR; i++) dx += rlen[i] > 0 ? rlen[i] - 1 : 0;
    if (dxor) *dxor = dx;
    for (;;) {
        V = next + 1;
        int best = 0, ba = -1, bb = -1; long nties = 0;
        for (int i = 0; i < NR; i++) {
            int *r = rows[i], L = rlen[i];
            for (int x = 0; x < L; x++) for (int y = x + 1; y < L; y++) {
                int a = r[x], b = r[y]; /* rows kept sorted => a<b */
                int v = ++cnt[(long)a * MAXV + b];
                if (v > best) { best = v; ba = a; bb = b; nties = 1; }
                else if (v == best) {
                    if (!randomize) { if (a < ba || (a == ba && b < bb)) { ba = a; bb = b; } }
                }
            }
        }
        if (randomize && best >= 2) { /* reservoir over distinct pairs with count == best */
            nties = 0;
            for (int i = 0; i < NR; i++) {
                int *r = rows[i], L = rlen[i];
                for (int x = 0; x < L; x++) for (int y = x + 1; y < L; y++) {
                    long idx = (long)r[x] * MAXV + r[y];
                    if (cnt[idx] == best) { nties++; if (xr() % nties == 0) { ba = r[x]; bb = r[y]; } cnt[idx] = 0xFFFF; }
                }
            }
        }
        for (int i = 0; i < NR; i++) { int *r = rows[i], L = rlen[i]; for (int x = 0; x < L; x++) for (int y = x + 1; y < L; y++) cnt[(long)r[x] * MAXV + r[y]] = 0; }
        if (best < 2) break;
        int t = next++; temps++;
        if (next >= MAXV) { fprintf(stderr, "MAXV exceeded\n"); exit(1); }
        for (int i = 0; i < NR; i++) {
            int *r = rows[i], L = rlen[i], ha = 0, hb = 0;
            for (int x = 0; x < L; x++) { if (r[x] == ba) ha = 1; if (r[x] == bb) hb = 1; }
            if (ha && hb) { int k = 0; for (int x = 0; x < L; x++) if (r[x] != ba && r[x] != bb) r[k++] = r[x]; r[k++] = t; rlen[i] = k; /* t is the largest id: stays sorted */ }
        }
    }
    int cost = temps; for (int i = 0; i < NR; i++) cost += rlen[i] > 0 ? rlen[i] - 1 : 0;
    return cost;
}
int main(int argc, char **argv) {
    cnt = calloc((size_t)MAXV * MAXV, sizeof(uint16_t));
    if (!strcmp(argv[1], "strip")) {
        int RUNS = atoi(argv[2]), KMAX = atoi(argv[3]);
        for (int k = 4; k <= KMAX; k++) for (int cp = 1; cp < k; cp++) {
            int bp = k - 2 * cp; if (bp <= cp) continue;
            int a = bp, bb = cp; while (bb) { int t = a % bb; a = bb; bb = t; } if (a != 1) continue;
            int ex[5] = {k, bp + cp, bp, cp, 0}; int res[2];
            for (int which = 0; which < 2; which++) {
                TOP = which == 0 ? 2 * k - 2 : 2 * k - 1;
                build(k, ex, 5); int best = run(0, NULL);
                for (int r = 0; r < RUNS; r++) { build(k, ex, 5); int v = run(1, NULL); if (v < best) best = v; }
                res[which] = best;
            }
            TOP = -1;
            printf("k=%d (%d,%d) R2=%d closedG=%d R1=%d 3k-c'=%d %s\n", k, bp, cp, res[0], 3 * k - cp - 3, res[1], 3 * k - cp, (res[0] < 3 * k - cp - 3 || res[1] < 3 * k - cp) ? "SHORTER" : "");
            fflush(stdout);
        }
        return 0;
    }
    if (!strcmp(argv[1], "fam2")) {
        int MLO = atoi(argv[2]), MHI = atoi(argv[3]), RUNS = atoi(argv[4]);
        for (int m = MLO; m <= MHI; m++) for (int c = 1; 3 * c + 1 <= m; c++) {
            int b = m - 2 * c; if (b <= c) continue;
            int ex[5] = {m, b + c, b, c, 0};
            int dx; build(m, ex, 5); int cx = run(0, &dx);
            int br = -1;
            for (int k = 0; k < RUNS; k++) { build(m, ex, 5); int v = run(1, NULL); if (br < 0 || v < br) br = v; }
            printf("%d %d %d %d %d %d %d\n", m, b, c, dx, cx, br, 3 * m - c - 3); fflush(stdout);
        }
    } else {
        int RUNS = atoi(argv[2]); int ex[8], ne = 0; for (int i = 3; i < argc; i++) ex[ne++] = atoi(argv[i]);
        int dx; build(ex[0], ex, ne); int cx = run(0, &dx); int br = -1;
        for (int k = 0; k < RUNS; k++) { build(ex[0], ex, ne); int v = run(1, NULL); if (br < 0 || v < br) br = v; }
        printf("m=%d dXOR=%d CX=%d bestRandom=%d\n", ex[0], dx, cx, br);
    }
    return 0;
}
