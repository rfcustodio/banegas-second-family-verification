"""Reducao em nivel de palavra para f = x^{b+2c} + x^{b+c} + x^b + x^c + 1 (Corolario 10).
Uso: python3 wordlevel.py b c   (testa contra a divisao polinomial)"""
import sys, random
def reduz(D, b, c):
    m = b + 2 * c; n = m - 2; mask = (1 << m) - 1
    L, H = D & mask, D >> m
    C, s = H, 3 * c
    while s <= n:                     # somas-pente por duplicacao
        C ^= C >> s; s *= 2
    Q = C ^ (C >> c) ^ (H >> (b + c))  # quociente em forma fechada
    U = Q ^ (Q << c)
    return (L ^ U ^ (U << b)) & mask
def pmod(a, f):
    df = f.bit_length() - 1
    while a and a.bit_length() - 1 >= df: a ^= f << (a.bit_length() - 1 - df)
    return a
if __name__ == '__main__':
    b, c = int(sys.argv[1]), int(sys.argv[2]); m = b + 2 * c
    f = (1 << m) | (1 << (b + c)) | (1 << b) | (1 << c) | 1
    ok = all(reduz(D, b, c) == pmod(D, f) for D in (random.getrandbits(2 * m - 1) for _ in range(10000)))
    print(f"m={m}: 10000 testes aleatorios, {'ok' if ok else 'FALHOU'}")
