#!/usr/bin/env python3
"""
Conta-XOR — implementacao de referencia em Python puro.

Algoritmo da dissertacao de Gustavo Souza Banegas, "Pentanomios irredutiveis
sobre GF(2^m) para reducao modular eficiente" (UFSC, 2015), Capitulo 4.

Entram dois polinomios sobre GF(2) — os dois operandos a multiplicar — mais o
polinomio irredutivel f que define o corpo GF(2^m). Saem:

  * o polinomio resultado, isto e' A(x) * B(x) mod f(x)
  * o custo em portas logicas para realizar essa operacao em hardware

Um ponto conceitual que vale destacar, porque nao e' obvio:

    o RESULTADO depende dos operandos A e B;
    o CUSTO depende apenas de f.

Trocar A e B muda o polinomio de saida mas nao muda uma unica porta do circuito.
E' por isso que a busca por bons polinomios irredutiveis faz sentido: voce
escolhe f uma vez e paga o preco dele em toda multiplicacao do corpo.

Sem dependencias externas. Testado contra os numeros publicados na dissertacao.
"""

from __future__ import annotations

import argparse
import re
import sys
from heapq import heapify, heappush, heappop


# ---------------------------------------------------------------------------
# Representacao: um polinomio sobre GF(2) e' um inteiro Python.
# O bit i vale 1 se o coeficiente de x^i for 1.
# Ex.: x^10 + x^4 + x^3 + x + 1  ->  0b10000011011  ->  1051
# ---------------------------------------------------------------------------

def parse_poly(texto: str) -> int:
    """Le um polinomio em qualquer um dos formatos aceitos.

    Algebrico :  "x^10+x^4+x^3+x+1"   (espacos opcionais, aceita 'X')
    Expoentes :  "10,4,3,1,0"  ou  "10 4 3 1 0"
    Binario   :  "0b10000011011"
    Hexa      :  "0x41b"
    """
    t = texto.strip()
    if not t:
        raise ValueError("polinomio vazio")

    if t.startswith(("0b", "0B", "0x", "0X")):
        return int(t, 0)

    # Lista de expoentes. Exige separador, para que "1" sozinho continue sendo
    # a constante 1 (e nao o expoente 1, que seria x).
    if re.fullmatch(r"\d+(?:\s*[,\s]\s*\d+)+", t):
        p = 0
        for e in re.split(r"[,\s]+", t):
            if e:
                p ^= 1 << int(e)
        return p

    # notacao algebrica
    t = t.replace(" ", "")
    p = 0
    for termo in t.replace("-", "+").split("+"):
        if not termo:
            continue
        m = re.fullmatch(r"(?:([xX])(?:\^(\d+))?|(\d+))", termo)
        if not m:
            raise ValueError(f"termo nao reconhecido: {termo!r}")
        if m.group(3) is not None:          # constante: 1 -> x^0, 0 -> nada
            if int(m.group(3)) % 2 == 1:
                p ^= 1
        else:                                # x, ou x^k
            p ^= 1 << int(m.group(2) or 1)
    return p


def poly_str(p: int) -> str:
    """Escreve o polinomio em notacao algebrica, do maior grau para o menor."""
    if p == 0:
        return "0"
    partes = []
    for e in range(p.bit_length() - 1, -1, -1):
        if p >> e & 1:
            partes.append("1" if e == 0 else "x" if e == 1 else f"x^{e}")
    return " + ".join(partes)


def expoentes(p: int) -> list[int]:
    """Lista dos expoentes com coeficiente 1, do maior para o menor."""
    return [e for e in range(p.bit_length() - 1, -1, -1) if p >> e & 1]


def grau(p: int) -> int:
    """Grau do polinomio; -1 para o polinomio nulo."""
    return p.bit_length() - 1


# ---------------------------------------------------------------------------
# Aritmetica em GF(2)[x]
# ---------------------------------------------------------------------------

def mul(a: int, b: int) -> int:
    """Multiplicacao sem transporte (carry-less). Soma em GF(2) e' XOR."""
    r = 0
    while b:
        if b & 1:
            r ^= a
        a <<= 1
        b >>= 1
    return r


# tabela de "espalhamento": byte -> os mesmos bits, um zero entre cada par.
# Serve para elevar ao quadrado: em GF(2), (u+v)^2 = u^2 + v^2 (Frobenius),
# entao quadrado e' so' afastar os expoentes, sem termos cruzados.
_ESPALHA = [sum(((b >> i) & 1) << (2 * i) for i in range(8)) for b in range(256)]


def sqr(a: int) -> int:
    """Quadrado em GF(2)[x] — muito mais barato que uma multiplicacao geral."""
    r, sh = 0, 0
    while a:
        r |= _ESPALHA[a & 0xFF] << sh
        a >>= 8
        sh += 16
    return r


def mod(d: int, f: int) -> int:
    """Resto da divisao de d por f."""
    gf = grau(f)
    if gf < 0:
        raise ZeroDivisionError("modulo nulo")
    while grau(d) >= gf:
        d ^= f << (grau(d) - gf)
    return d


def gcd(a: int, b: int) -> int:
    while b:
        a, b = b, mod(a, b)
    return a


def eh_irredutivel(f: int) -> bool:
    """Teste de Rabin: f e' irredutivel sse

        x^(2^m) == x (mod f)   e   gcd(x^(2^(m/q)) - x, f) == 1
        para todo primo q que divide m.

    E' o analogo polinomial de um teste de primalidade — a primeira condicao e'
    o pequeno teorema de Fermat traduzido para corpos finitos.
    """
    m = grau(f)
    if m < 1:
        return False
    if f & 1 == 0:          # sem termo constante => x divide f
        return False
    if bin(f).count("1") % 2 == 0:   # numero par de termos => (x+1) divide f
        return False
    # todos os expoentes pares => quadrado perfeito
    if all(e % 2 == 0 for e in expoentes(f)):
        return False

    def primos(n):
        ps, d = set(), 2
        while d * d <= n:
            if n % d == 0:
                ps.add(d)
                while n % d == 0:
                    n //= d
            d += 1
        if n > 1:
            ps.add(n)
        return ps

    marcos = sorted({m // q for q in primos(m)})
    cur, i = 0b10, 0                    # cur = x^(2^0) = x
    for k in range(1, m + 1):
        cur = mod(sqr(cur), f)          # eleva ao quadrado
        while i < len(marcos) and marcos[i] == k:
            if grau(gcd(cur ^ 0b10, f)) > 0:
                return False
            i += 1
    return cur == 0b10


# ---------------------------------------------------------------------------
# ETAPAS 1 e 2 — matriz de reducao
# ---------------------------------------------------------------------------

def matriz_reducao(f: int) -> list[list[int]]:
    """Colunas da matriz de reducao de f.

    Devolve `col`, onde `col[i]` e' a lista dos indices j tais que o bit de
    entrada d_j alimenta o bit de saida e_i. Ou seja:

        e_i = XOR de { d_j : j em col[i] }

    Etapa 1 da dissertacao monta essa tabela aplicando x^m = (termos menores)
    repetidamente; a etapa 2 cancela termos iguais aos pares, porque a XOR a = 0.
    Aqui as duas saem juntas de graca: cancelar iguais aos pares E' somar modulo
    2, entao basta acumular com XOR enquanto se constroi.
    """
    m = grau(f)
    col: list[list[int]] = [[] for _ in range(m)]
    v = 1                                   # v = x^j mod f, comecando em j=0
    for j in range(2 * m - 1):
        w = v
        while w:                            # percorre os bits 1 de v
            i = (w & -w).bit_length() - 1
            col[i].append(j)
            w &= w - 1
        v <<= 1                             # multiplica por x
        if v >> m & 1:                      # estourou o grau: reduz
            v ^= f
    return col


def custo_sem_otimizacao(col) -> int:
    """Quantas portas seriam precisas sem reaproveitar nada.

    Uma coluna com c termos precisa de c-1 portas XOR de duas entradas.
    """
    return sum(len(c) - 1 for c in col if c)


def profundidade_sem_otimizacao(col) -> int:
    """Profundidade do circuito SEM CSE nenhuma: cada bit de saida e' sua
    propria arvore balanceada de XOR sobre os termos da coluna (nada
    compartilhado entre colunas), entao a profundidade minima por coluna e'
    ceil(log2(len(coluna)))."""
    pior = 0
    for c in col:
        n = len(c)
        if n > 1:
            pior = max(pior, (n - 1).bit_length())
    return pior


def equacoes_reducao(f: int) -> list[tuple[int, int]]:
    """As equacoes x^j = (termos de grau < m), para j de m ate 2m-2.

    Sao elas que a etapa 1 aplica para derrubar cada termo alto. Note que as
    primeiras costumam ter poucos termos e as ultimas mais: quando x^j precisa
    de mais de uma passada de reducao, os termos se espalham.
    """
    m = grau(f)
    v, out = 1, []
    for j in range(2 * m - 1):
        if j >= m:
            out.append((j, v))
        v <<= 1
        if v >> m & 1:
            v ^= f
    return out


def mostra_etapas_1_e_2(f: int, col) -> None:
    """Imprime as equacoes de reducao e a matriz MR."""
    m = grau(f)
    print("ETAPA 1 - equacoes de reducao (so' as que precisam reduzir):")
    for j, v in equacoes_reducao(f):
        print(f"   x^{j:<3} = {poly_str(v)}")

    print()
    print("ETAPA 2 - matriz MR ja' com os termos repetidos cancelados")
    print("   (coluna i = quais bits de entrada d_j entram no bit de saida i)")
    for i in range(m - 1, -1, -1):
        print(f"   bit {i:<3}: " + " + ".join(f"d{j}" for j in col[i]))
    total = sum(len(c) for c in col)
    print()
    print(f"   custo SEM otimizacao: soma(c(i)-1) = {total} - {m} "
          f"= {custo_sem_otimizacao(col)} XORs")


# ---------------------------------------------------------------------------
# ETAPAS 3 e 4 — eliminacao de subexpressoes comuns, e contagem
# ---------------------------------------------------------------------------

class Resultado:
    """Custo de um circuito de reducao, e o proprio circuito."""

    def __init__(self, bruto, xors, temps, prof, slp, col):
        self.bruto = bruto      # portas sem otimizacao alguma
        self.xors = xors        # portas depois da etapa 3  (o N_xor da tese)
        self.temps = temps      # quantas variaveis temporarias (matriz MER)
        self.prof = prof        # profundidade do circuito, em portas XOR
        self.slp = slp          # lista (t, a, b): t = a XOR b, em ordem
        self.col = col          # colunas finais, ja' com as temporarias


def conta_xor(col, primeira_temp: int, trace: bool = False, rng=None) -> Resultado:
    """Etapa 3 (otimizacao gulosa, ou com desempate aleatorio se `rng` for dado)
    seguida da etapa 4 (contagem).

    A ideia: se o par (d_a, d_b) aparece junto em varias colunas, nao adianta
    calcular d_a XOR d_b varias vezes. Calcula uma vez, guarda numa variavel
    temporaria, e reusa. Sem `rng`: escolhe-se sempre o par MAIS repetido,
    empate vai para o menor termo, depois para o segundo menor (regra da
    dissertacao) — determinístico. Com `rng`: sorteia entre os pares empatados
    no maior numero de ocorrencias (usado por `conta_xor_sorteado`).

    ATENCAO — isto e' uma heuristica, nao o otimo. E' o Algoritmo 1 de Paar
    (ISIT 1997). Achar o minimo verdadeiro e' o problema do menor programa
    linear, que e' NP-dificil. Portanto todo numero devolvido aqui e' um LIMITE
    SUPERIOR: existe circuito com no maximo tantas portas, talvez menos.

    Implementacao: mantem a contagem de pares INCREMENTALMENTE — um dict
    (par -> contagem) mais um heap com remocao preguicosa para achar o maximo
    — em vez de reconstruir a contagem inteira do zero a cada substituicao.
    Cada substituicao so' toca os pares que envolvem os termos substituidos,
    entao o custo por passo cai de O(n^2) para O(grau do termo). Mesma regra
    de desempate, mesma saida — so' a contabilidade e' mais esperta. (E' a
    mesma tecnica da reimplementacao em Rust do mesmo algoritmo, em
    ../pentanomials/src/paar.rs.)
    """
    col = [list(c) for c in col]
    bruto = custo_sem_otimizacao(col)

    contagens: dict[tuple[int, int], int] = {}
    for c in col:
        for x in range(len(c)):
            for y in range(x + 1, len(c)):
                k = (c[x], c[y]) if c[x] < c[y] else (c[y], c[x])
                contagens[k] = contagens.get(k, 0) + 1
    heap = [(-q, k) for k, q in contagens.items() if q >= 2]
    heapify(heap)

    # occ[termo] = colunas que contem esse termo, para achar a interseccao
    # occ[a] & occ[b] direto em vez de escanear todas as colunas.
    occ: dict[int, list[int]] = {}
    for i, c in enumerate(col):
        for x in c:
            occ.setdefault(x, []).append(i)

    def bump(k, delta):
        nv = contagens.get(k, 0) + delta
        if nv <= 0:
            contagens.pop(k, None)
        else:
            contagens[k] = nv
            if nv >= 2:
                heappush(heap, (-nv, k))

    prox = primeira_temp
    prof = {}                                # profundidade de cada termo
    slp = []                                 # o circuito, em ordem de execucao

    if trace:
        print()
        print("ETAPA 3 - substituicao gulosa do par mais repetido")

    while True:
        # descarta entradas obsoletas do heap ate achar uma contagem valida
        melhor, n = None, 0
        while heap:
            negq, k = heap[0]
            q = -negq
            if contagens.get(k, 0) == q and q >= 2:
                melhor, n = k, q
                break
            heappop(heap)
        if melhor is None:
            break                            # nao ha' mais nada a reaproveitar
        heappop(heap)

        if rng is not None:
            # sorteia entre TODOS os pares empatados no maior n encontrado
            pool = [melhor]
            while heap and heap[0][0] == -n:
                _, k = heappop(heap)
                if contagens.get(k, 0) == n:
                    pool.append(k)
            escolhido = rng.choice(pool)
            for k in pool:
                if k != escolhido:
                    heappush(heap, (-n, k))
            a, b = escolhido
        else:
            a, b = melhor

        t = prox
        prox += 1
        prof[t] = 1 + max(prof.get(a, 0), prof.get(b, 0))
        slp.append((t, a, b))

        onde = sorted(set(occ.get(a, ())) & set(occ.get(b, ())))
        if trace:
            top = sorted(contagens.items(), key=lambda kv: (-kv[1], kv[0]))[:3]
            print("   pares mais repetidos: "
                  + ", ".join(f"({p[0]},{p[1]})x{q}" for p, q in top))
            print(f"   -> substitui (d{a},d{b}), que aparece em {n} colunas "
                  f"{onde}, por t{t}")

        for i in onde:
            c = col[i]
            outros = [x for x in c if x != a and x != b]
            for u in outros:
                bump((a, u) if a < u else (u, a), -1)
                bump((b, u) if b < u else (u, b), -1)
                bump((t, u) if t < u else (u, t), 1)
            bump((a, b), -1)
            col[i] = sorted(outros + [t])

        onde_set = set(onde)
        occ[a] = [i for i in occ.get(a, ()) if i not in onde_set]
        occ[b] = [i for i in occ.get(b, ()) if i not in onde_set]
        occ[t] = onde

    # ETAPA 4: cada coluna com c termos custa c-1 portas; some as temporarias
    resto = custo_sem_otimizacao(col)
    xors = resto + len(slp)

    if trace:
        print(f"   ... total de {len(slp)} substituicoes")
        print()
        print("ETAPA 4 - contagem")
        print(f"   XORs restantes na MR : {resto}")
        print(f"   temporarias (MER)    : {len(slp)}")
        print(f"   TOTAL                : {resto} + {len(slp)} = {xors} XORs")

    # profundidade: cada coluna e' uma arvore de XORs sobre os termos que
    # sobraram. Combinando sempre os dois mais rasos primeiro (Huffman) se
    # obtem a menor profundidade possivel para aquela arvore.
    pior = 0
    for c in col:
        if not c:
            continue
        h = []
        for termo in c:
            heappush(h, prof.get(termo, 0))
        while len(h) > 1:
            x, y = heappop(h), heappop(h)
            heappush(h, max(x, y) + 1)
        pior = max(pior, heappop(h))

    return Resultado(bruto, xors, len(slp), pior, slp, col)


def avalia_slp(res: Resultado, d: int, m: int) -> int:
    """Executa o circuito gerado sobre os bits de d e devolve o resultado.

    Serve de conferencia independente: o valor tem de bater com mod(d, f),
    que e' calculado por outro caminho, sem compartilhar codigo.
    """
    val = {j: (d >> j) & 1 for j in range(2 * m - 1)}
    for t, a, b in res.slp:
        val[t] = val[a] ^ val[b]
    saida = 0
    for i, c in enumerate(res.col):
        bit = 0
        for termo in c:
            bit ^= val[termo]
        saida |= bit << i
    return saida


# ---------------------------------------------------------------------------
# Interface de alto nivel
# ---------------------------------------------------------------------------

def otimiza(col, primeira_temp, modo="guloso", trace=False, reinicios=50,
            max_nos=400_000):
    """Escolhe a estrategia da etapa 3. Devolve (Resultado, aviso_ou_None)."""
    if modo == "sorteado":
        return conta_xor_sorteado(col, primeira_temp, reinicios), None
    if modo == "exato":
        res, completou = conta_xor_exato(col, primeira_temp, max_nos)
        aviso = None if completou else (
            f"orcamento de {max_nos} nos esgotado — o numero abaixo e' o melhor "
            f"encontrado, nao necessariamente o otimo")
        return res, aviso
    return conta_xor(col, primeira_temp, trace), None


def multiplica(a: int, b: int, f: int, trace: bool = False, modo="guloso"):
    """Multiplica A por B no corpo GF(2^m) definido por f.

    Devolve (resultado, Resultado_de_custo).
    """
    m = grau(f)
    if grau(a) >= m or grau(b) >= m:
        raise ValueError(
            f"os operandos precisam ter grau < {m}; "
            f"recebi graus {grau(a)} e {grau(b)}"
        )
    produto = mul(a, b)                      # grau ate 2m-2
    col = matriz_reducao(f)
    if trace:
        mostra_etapas_1_e_2(f, col)
    res, aviso = otimiza(col, 2 * m - 1, modo, trace)
    if aviso:
        print(f"  AVISO   : {aviso}")
    reduzido = mod(produto, f)

    # conferencia: o circuito tem de produzir o mesmo que a reducao direta
    if avalia_slp(res, produto, m) != reduzido:
        raise AssertionError("circuito gerado nao confere com a reducao direta")

    return reduzido, res


def reduz(d: int, f: int, trace: bool = False, modo="guloso"):
    """Reduz d modulo f. Devolve (resultado, Resultado_de_custo)."""
    m = grau(f)
    if grau(d) > 2 * m - 2:
        raise ValueError(
            f"grau {grau(d)} alto demais; a reducao e' projetada para grau "
            f"ate 2m-2 = {2*m-2}, que e' o maximo de um produto no corpo"
        )
    col = matriz_reducao(f)
    if trace:
        mostra_etapas_1_e_2(f, col)
    res, aviso = otimiza(col, 2 * m - 1, modo, trace)
    if aviso:
        print(f"  AVISO   : {aviso}")
    reduzido = mod(d, f)
    if avalia_slp(res, d, m) != reduzido:
        raise AssertionError("circuito gerado nao confere com a reducao direta")
    return reduzido, res


# ---------------------------------------------------------------------------
# Linha de comando
# ---------------------------------------------------------------------------

def _relatorio(f, res, m, com_multiplicacao, trace=False, modo="guloso"):
    if trace:
        print()
        print("=" * 68)
    print()
    rotulo = {"guloso": "Paar1 guloso", "sorteado": "Paar sorteado",
              "exato": "busca exaustiva"}[modo]
    print(f"  custo do circuito  (depende so' de f, nao dos operandos)"
          f"   [etapa 3: {rotulo}]")
    print(f"    XORs da reducao        : {res.xors}"
          f"      (sem otimizacao seriam {res.bruto})")
    print(f"    temporarias (MER)      : {res.temps}")
    print(f"    profundidade           : {res.prof} T_X")
    if com_multiplicacao:
        ands, xors_mul = m * m, (m - 1) ** 2
        print(f"    ---")
        print(f"    ANDs da multiplicacao  : {ands}")
        print(f"    XORs da multiplicacao  : {xors_mul}   (metodo escolar)")
        print(f"    TOTAL de XORs          : {xors_mul + res.xors}")


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="Conta-XOR: multiplica em GF(2^m) e informa o custo em portas.",
        epilog="Formatos aceitos: 'x^10+x^4+x^3+x+1', '10,4,3,1,0', '0b100...', '0x41b'",
    )
    ap.add_argument("polinomios", nargs="*",
                    help="dois operandos A e B (ou um so' polinomio, para apenas reduzir)")
    ap.add_argument("-m", "--mod", required=True, metavar="F",
                    help="o polinomio irredutivel que define o corpo")
    ap.add_argument("--trace", action="store_true",
                    help="mostra o algoritmo passo a passo: equacoes de reducao, "
                         "matriz MR, cada substituicao e a contagem final")
    ap.add_argument("--sorteado", action="store_true",
                    help="Paar com desempate aleatorio, varias rodadas, fica com "
                         "o melhor. Quase de graca e costuma achar menos portas.")
    ap.add_argument("--exato", action="store_true",
                    help="busca exaustiva da melhor sequencia de substituicoes. "
                         "So' viavel em graus pequenos — veja o README.")
    ap.add_argument("--reinicios", type=int, default=50, metavar="N",
                    help="quantas rodadas em --sorteado (padrao 50)")
    ap.add_argument("--max-nos", type=int, default=400_000, metavar="N",
                    help="orcamento de busca em --exato (padrao 400000)")
    ap.add_argument("--slp", action="store_true",
                    help="imprime o circuito gerado, porta a porta")
    args = ap.parse_args(argv)

    try:
        f = parse_poly(args.mod)
        ops = [parse_poly(p) for p in args.polinomios]
    except ValueError as e:
        ap.error(str(e))

    m = grau(f)
    if m < 2:
        ap.error("o modulo precisa ter grau >= 2")
    if args.sorteado and args.exato:
        ap.error("escolha --sorteado OU --exato, nao os dois")
    modo = "exato" if args.exato else "sorteado" if args.sorteado else "guloso"

    if args.trace:
        print(f"Conta-XOR sobre f(x) = {poly_str(f)}   (m = {m})")
        print("=" * 68)
        print()
    else:
        print(f"  corpo   : GF(2^{m}) definido por f(x) = {poly_str(f)}")
    if not eh_irredutivel(f):
        print(f"  AVISO   : f NAO e' irredutivel — GF(2^{m}) nao e' corpo com esse f")
        print(f"            (havera divisores de zero; o custo ainda e' calculado)")

    if len(ops) == 2:
        a, b = ops
        try:
            r, res = multiplica(a, b, f, args.trace, modo)
        except ValueError as e:
            ap.error(str(e))
        print(f"  A(x)    = {poly_str(a)}")
        print(f"  B(x)    = {poly_str(b)}")
        print(f"  A*B     = {poly_str(mul(a, b))}")
        print()
        print(f"  RESULTADO  A(x)*B(x) mod f(x) = {poly_str(r)}")
        print(f"             expoentes: {expoentes(r)}")
        _relatorio(f, res, m, com_multiplicacao=True, trace=args.trace, modo=modo)
    elif len(ops) == 1:
        d = ops[0]
        try:
            r, res = reduz(d, f, args.trace, modo)
        except ValueError as e:
            ap.error(str(e))
        print(f"  D(x)    = {poly_str(d)}")
        print()
        print(f"  RESULTADO  D(x) mod f(x) = {poly_str(r)}")
        print(f"             expoentes: {expoentes(r)}")
        _relatorio(f, res, m, com_multiplicacao=False, trace=args.trace, modo=modo)
    else:
        col = matriz_reducao(f)
        if args.trace:
            mostra_etapas_1_e_2(f, col)
        res, aviso = otimiza(col, 2 * m - 1, modo, args.trace,
                             args.reinicios, args.max_nos)
        print(f"  (nenhum operando dado — so' o custo do corpo)")
        if aviso:
            print(f"  AVISO   : {aviso}")
        _relatorio(f, res, m, com_multiplicacao=True, trace=args.trace, modo=modo)

    if args.slp:
        print()
        print("  circuito gerado (variaveis temporarias, em ordem de execucao):")
        for t, a, b in res.slp:
            print(f"    t{t} = d{a} XOR d{b}")
        print("  bits de saida:")
        for i in range(len(res.col) - 1, -1, -1):
            termos = " XOR ".join(
                (f"t{x}" if x >= 2 * m - 1 else f"d{x}") for x in res.col[i])
            print(f"    e{i} = {termos}")
    return 0



# ---------------------------------------------------------------------------
# ALTERNATIVAS AO GULOSO
#
# O Paar1 acima escolhe sempre o par mais repetido. E' rapido mas nao e' otimo.
# Aqui vao duas alternativas, em ordem crescente de custo e de qualidade.
# ---------------------------------------------------------------------------

def conta_xor_sorteado(col, primeira_temp, reinicios=50, semente=0):
    """Paar com desempate ALEATORIO, repetido varias vezes; fica com o melhor.

    Quando varios pares empatam em numero de ocorrencias, o Paar1 escolhe
    sempre o de menor indice. Essa regra nao tem nada de especial — e' so' um
    criterio para o algoritmo ser deterministico. Sorteando entre os empatados
    e repetindo, costuma-se achar circuitos menores de graca.

    E' a alternativa que melhor escala: cada rodada custa o mesmo que o guloso
    (usa o mesmo motor incremental de `conta_xor`, so' com desempate por `rng`
    em vez de sempre o menor par).
    """
    import random

    melhor = conta_xor(col, primeira_temp)           # a rodada deterministica
    rnd = random.Random(semente)
    for _ in range(reinicios):
        cand = conta_xor(col, primeira_temp, rng=rnd)
        if cand.xors < melhor.xors:
            melhor = cand
    return melhor


def conta_xor_exato(col, primeira_temp, max_nos=400_000):
    """Busca EXAUSTIVA da melhor sequencia de substituicoes.

    Explora todas as escolhas possiveis, nao so' a gulosa, com memoizacao.
    Devolve (Resultado, completou) — se `completou` for False, o orcamento de
    nos acabou antes e o numero e' apenas o melhor encontrado ate ali.

    ATENCAO ao que "exato" quer dizer aqui. Isto acha o otimo DENTRO do espaco
    de movimentos do Paar: substituir um par de termos que aparece junto em duas
    ou mais colunas. Circuitos fora desse espaco — por exemplo os que usam
    cancelamento, a XOR a = 0, para criar atalhos — nao sao considerados. Entao
    o numero continua sendo um limite superior do otimo verdadeiro, so' que bem
    mais apertado que o guloso.

    O otimo verdadeiro exigiria um solver SAT ou ILP. O problema e' NP-dificil
    (Boyar, Matthews, Peralta, 2013), entao nao ha' atalho.

    O truque que torna a memoizacao possivel: identificar cada termo pela sua
    ASSINATURA, o conjunto dos d_j originais que o compoem, em vez de pelo nome
    da variavel temporaria. Dois caminhos diferentes que chegam na mesma
    configuracao passam a ser reconhecidos como o mesmo estado.
    """
    est0 = tuple(sorted(tuple(sorted(1 << j for j in c)) for c in col))
    memo = {}
    nos = [0]
    completou = [True]

    def g(est):
        """Menor custo possivel a partir deste estado."""
        if est in memo:
            return memo[est]
        if nos[0] >= max_nos:
            completou[0] = False
            return (sum(len(c) - 1 for c in est), None)
        nos[0] += 1

        cont = {}
        for c in est:
            for i in range(len(c)):
                for j in range(i + 1, len(c)):
                    k = (c[i], c[j]) if c[i] < c[j] else (c[j], c[i])
                    cont[k] = cont.get(k, 0) + 1

        melhor, mov = sum(len(c) - 1 for c in est), None   # opcao: parar aqui
        for (a, b), n in sorted(cont.items(), key=lambda kv: -kv[1]):
            if n < 2:
                continue
            novo = []
            for c in est:
                if a in c and b in c:
                    novo.append(tuple(sorted(
                        [x for x in c if x != a and x != b] + [a | b])))
                else:
                    novo.append(c)
            v = 1 + g(tuple(sorted(novo)))[0]
            if v < melhor:
                melhor, mov = v, (a, b)

        memo[est] = (melhor, mov)
        return memo[est]

    custo, _ = g(est0)

    # refaz o caminho otimo para montar o circuito de verdade
    est = est0
    assin = {1 << j: j for j in range(2 * len(col) - 1)}   # assinatura -> nome
    c_reais = [list(x) for x in col]
    prox, prof, slp = primeira_temp, {}, []
    while True:
        mov = memo.get(est, (None, None))[1]
        if mov is None:
            break
        a, b = mov
        na, nb = assin[a], assin[b]
        t = prox
        prox += 1
        assin[a | b] = t
        prof[t] = 1 + max(prof.get(na, 0), prof.get(nb, 0))
        slp.append((t, na, nb))
        novo = []
        for c in est:
            if a in c and b in c:
                novo.append(tuple(sorted([x for x in c if x != a and x != b] + [a | b])))
            else:
                novo.append(c)
        est = tuple(sorted(novo))
        for i, c in enumerate(c_reais):
            if na in c and nb in c:
                c_reais[i] = sorted([x for x in c if x != na and x != nb] + [t])

    pior = 0
    for c in c_reais:
        if not c:
            continue
        h = []
        for termo in c:
            heappush(h, prof.get(termo, 0))
        while len(h) > 1:
            x, y = heappop(h), heappop(h)
            heappush(h, max(x, y) + 1)
        pior = max(pior, heappop(h))

    bruto = custo_sem_otimizacao(col)
    return Resultado(bruto, custo, len(slp), pior, slp, c_reais), completou[0]

if __name__ == "__main__":
    sys.exit(main())
