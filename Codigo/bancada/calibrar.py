"""Conduz a calibracao do no de bancada pela serial (TCC 3.4.2 a 3.4.4).

Precisa do sketch bancada/calibracao/calibracao.ino gravado no ESP32.

    # 1) Ajuste do comprimento da fita: repita cortando/emendando ate "OK"
    python -m bancada.calibrar teto

    # 2) Calibracao completa (grava sessao_medicao + calibracao no banco)
    python -m bancada.calibrar completa --comprimento-cm 30

Opcoes comuns: --porta COM3, --simulada (sem hardware, para testar o script).

O que a calibracao completa produz:
  - residual com a luz apagada e sessao descartada se > 5 % da classe (3.4.3);
  - varredura duty x lux em series independentes (monotonicidade, 3.4.4);
  - duty de 10 lux e de 5 lux ENCONTRADOS POR MEDICAO, nao interpolados (3.4.2);
  - dispersao entre series (repetibilidade -> tolerancia do diagnostico, 3.4.5);
  - firmware/no/calibracao.h com a tabela nivel -> duty para o firmware (3.3);
  - bancada/resultados/sessao_<id>.json com tudo o que foi medido.
"""

from __future__ import annotations

import argparse
import json
import random
import statistics
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

import psycopg

from decisao import config

RAIZ = Path(__file__).resolve().parent.parent
DUTY_MAX = 4095
POTENCIA_W_POR_M = 14.4  # especificacao eletrica da fita 5050, 60 LED/m (Quadro 4)
TETO_MIN, TETO_MAX = 1.5, 2.0  # teto fisico / valor da classe (3.4.2)
RESIDUAL_MAX = 0.05  # fracao do valor da classe (3.4.3)
ACOMODACAO_S = 0.3  # espera apos trocar o duty, antes de medir


# ---------------------------------------------------------------------------
# Acesso ao no
# ---------------------------------------------------------------------------
class Bancada:
    """Fala com o sketch de calibracao pela serial."""

    def __init__(self, porta: str) -> None:
        import serial  # pyserial

        self.s = serial.Serial(porta, 115200, timeout=30)
        # Abrir a porta reinicia o ESP32: espera a identificacao.
        fim = time.monotonic() + 8
        while time.monotonic() < fim:
            if "ID calibracao" in self._linha(timeout_ok=True):
                return
            self.s.write(b"?\n")
        raise RuntimeError(f"sketch de calibracao nao respondeu em {porta}")

    def _linha(self, timeout_ok: bool = False) -> str:
        l = self.s.readline().decode(errors="replace").strip()
        if l.startswith("ERRO"):
            raise RuntimeError(f"no respondeu: {l}")
        if not l and not timeout_ok:
            raise RuntimeError("no nao respondeu (timeout)")
        return l

    def duty(self, n: int) -> None:
        self.s.write(f"D {n}\n".encode())
        while not self._linha().startswith("OK D"):
            pass
        time.sleep(ACOMODACAO_S)

    def medir(self, k: int) -> list[float]:
        self.s.write(f"M {k}\n".encode())
        leituras = []
        while (l := self._linha()) != "FIM":
            if l.startswith("L "):
                leituras.append(float(l[2:]))
        return leituras


class BancadaSimulada:
    """Curva sintetica para testar o script; NUNCA use seus numeros no TCC."""

    def __init__(self, residual: float = 0.3, teto: float = 18.0, gama: float = 1.15) -> None:
        self.residual, self.teto, self.gama = residual, teto, gama
        self.d = 0
        self.rng = random.Random(42)

    def duty(self, n: int) -> None:
        self.d = n

    def medir(self, k: int) -> list[float]:
        base = self.teto * (self.d / DUTY_MAX) ** self.gama + self.residual
        return [round(max(0.0, base + self.rng.gauss(0, 0.05)), 2) for _ in range(k)]


# ---------------------------------------------------------------------------
# Procedimentos
# ---------------------------------------------------------------------------
@dataclass
class Relatorio:
    ponto: str
    classe: str
    lux_classe: float
    lux_piso: float
    residual: float
    lux_teto: float
    comprimento_cm: float | None
    series: dict[int, list[tuple[int, float]]] = field(default_factory=dict)
    duty_pleno: int | None = None
    duty_piso: int | None = None
    repeticoes_pleno: list[float] = field(default_factory=list)
    repeticoes_piso: list[float] = field(default_factory=list)
    monotona: bool | None = None
    sessao_id: int | None = None


def media(b, duty: int, k: int = 3) -> float:
    b.duty(duty)
    return statistics.fmean(b.medir(k))


def medir_residual(b) -> float:
    b.duty(0)
    return statistics.fmean(b.medir(10))


def buscar_duty(b, alvo_liquido: float, residual: float, lo: int = 0, hi: int = DUTY_MAX) -> int:
    """Bissecao NO HARDWARE: o duty e o que o sensor mede, nao uma conta."""
    while hi - lo > 1:
        meio = (lo + hi) // 2
        if media(b, meio) - residual < alvo_liquido:
            lo = meio
        else:
            hi = meio
    # Dos dois vizinhos, o mais proximo do alvo.
    e_lo = abs(media(b, lo) - residual - alvo_liquido)
    e_hi = abs(media(b, hi) - residual - alvo_liquido)
    return lo if e_lo < e_hi else hi


def repetir(b, duty: int, vezes: int, residual: float) -> list[float]:
    """Repeticoes independentes: apaga e volta ao duty a cada uma."""
    valores = []
    for _ in range(vezes):
        b.duty(0)
        valores.append(round(media(b, duty) - residual, 3))
    return valores


def duties_varredura(pontos: int) -> list[int]:
    return sorted({round(i * DUTY_MAX / (pontos - 1)) for i in range(pontos)})


def classe_do_ponto(conn, ponto: str) -> tuple[int, str, float, float]:
    linha = conn.execute(
        """
        SELECT p.id, c.codigo, c.iluminancia_media_min_lux, cm.iluminancia_media_min_lux
          FROM ponto_de_luz p
          JOIN classe_iluminacao c ON c.codigo = p.classe_codigo
          LEFT JOIN classe_iluminacao cm ON cm.codigo = c.classe_min_dimerizacao
         WHERE p.codigo = %s
        """,
        (ponto,),
    ).fetchone()
    if linha is None:
        raise SystemExit(f"ponto {ponto!r} nao cadastrado")
    pid, classe, lux, lux_piso = linha
    return pid, classe, float(lux), float(lux_piso if lux_piso is not None else lux)


def cmd_teto(b, lux_classe: float) -> None:
    residual = medir_residual(b)
    teto = media(b, DUTY_MAX, k=5) - residual
    b.duty(0)
    razao = teto / lux_classe
    print(f"residual (apagado): {residual:.2f} lx")
    print(f"teto liquido (duty 4095): {teto:.2f} lx  = {razao:.2f} x o valor da classe")
    if residual > RESIDUAL_MAX * lux_classe:
        print(f"ATENCAO: residual acima de {RESIDUAL_MAX:.0%} da classe - melhore o anteparo (3.4.3)")
    if razao < TETO_MIN:
        print(f"FITA CURTA: aumente o segmento (alvo {TETO_MIN}x a {TETO_MAX}x)")
    elif razao > TETO_MAX:
        print(f"FITA LONGA: encurte o segmento (alvo {TETO_MIN}x a {TETO_MAX}x)")
    else:
        print("OK: comprimento dentro do criterio de 3.4.2")


def cmd_completa(b, conn, args) -> Relatorio:
    pid, classe, lux_classe, lux_piso = classe_do_ponto(conn, args.ponto)
    residual = medir_residual(b)
    teto = media(b, DUTY_MAX, k=5) - residual
    r = Relatorio(args.ponto, classe, lux_classe, lux_piso, round(residual, 3), round(teto, 3),
                  args.comprimento_cm)
    print(f"residual {residual:.2f} lx | teto liquido {teto:.2f} lx ({teto / lux_classe:.2f}x)")

    with conn.transaction():
        r.sessao_id, descartada = conn.execute(
            "INSERT INTO sessao_medicao (ponto_de_luz_id, lux_residual, lux_classe, observacao)"
            " VALUES (%s, %s, %s, %s) RETURNING id, descartada",
            (pid, round(residual, 2), lux_classe, "calibracao (bancada/calibrar.py)"),
        ).fetchone()
    if descartada:
        print(f"SESSAO {r.sessao_id} DESCARTADA: residual > {RESIDUAL_MAX:.0%} da classe (3.4.3).")
        print("Melhore o anteparo e repita. Nada mais foi medido.")
        return r
    if not (TETO_MIN <= teto / lux_classe <= TETO_MAX):
        print(f"ATENCAO: teto fora de {TETO_MIN}x-{TETO_MAX}x; rode 'teto' e ajuste a fita (3.4.2).")
        if not args.forcar:
            raise SystemExit("interrompido (use --forcar para seguir assim mesmo)")

    # Varredura em series independentes (3.4.4).
    duties = duties_varredura(args.pontos)
    for serie in range(1, args.series + 1):
        b.duty(0)
        r.series[serie] = [(d, round(media(b, d) - residual, 3)) for d in duties]
        print(f"serie {serie}/{args.series} ok")

    # Duty da iluminacao plena da classe e do piso, por medicao (3.4.2).
    r.duty_pleno = buscar_duty(b, lux_classe, residual)
    r.duty_piso = buscar_duty(b, lux_piso, residual, hi=r.duty_pleno)
    r.repeticoes_pleno = repetir(b, r.duty_pleno, args.series, residual)
    r.repeticoes_piso = repetir(b, r.duty_piso, args.series, residual)
    b.duty(0)

    curva = curva_media(r)
    r.monotona = all(b2 >= b1 - 0.1 for (_, b1), (_, b2) in zip(curva, curva[1:]))

    with conn.transaction():
        for serie, pontos in r.series.items():
            for d, lux in pontos:
                conn.execute(
                    "INSERT INTO calibracao (sessao_id, serie, duty, lux_medido)"
                    " VALUES (%s, %s, %s, %s)",
                    (r.sessao_id, serie, d / DUTY_MAX, max(lux, 0) + residual),
                )
        for d, reps in ((r.duty_pleno, r.repeticoes_pleno), (r.duty_piso, r.repeticoes_piso)):
            for serie, lux in enumerate(reps, start=1):
                conn.execute(
                    "INSERT INTO calibracao (sessao_id, serie, duty, lux_medido)"
                    " VALUES (%s, %s, %s, %s) ON CONFLICT DO NOTHING",
                    (r.sessao_id, serie, d / DUTY_MAX, max(lux, 0) + residual),
                )
        if args.comprimento_cm:
            conn.execute(
                "UPDATE ponto_de_luz SET potencia_plena_w = %s WHERE id = %s",
                (round(POTENCIA_W_POR_M * args.comprimento_cm / 100, 2), pid),
            )
        conn.execute("UPDATE sessao_medicao SET encerrada_em = now() WHERE id = %s", (r.sessao_id,))
    return r


# ---------------------------------------------------------------------------
# Resultados
# ---------------------------------------------------------------------------
def curva_media(r: Relatorio) -> list[tuple[int, float]]:
    por_duty: dict[int, list[float]] = {}
    for pontos in r.series.values():
        for d, lux in pontos:
            por_duty.setdefault(d, []).append(lux)
    return sorted((d, statistics.fmean(v)) for d, v in por_duty.items())


def dispersao(valores: list[float]) -> float:
    """Desvio padrao relativo (fracao). 0 se ha uma so medida."""
    if len(valores) < 2 or statistics.fmean(valores) == 0:
        return 0.0
    return statistics.stdev(valores) / statistics.fmean(valores)


def tabela_firmware(r: Relatorio) -> list[tuple[float, int]]:
    """Pontos (nivel, duty) monotonos, com 1,0 e piso EXATAMENTE nos duties medidos."""
    pontos = [(lux / r.lux_classe, d) for d, lux in curva_media(r) if d not in (0,)]
    pontos = [(n, d) for n, d in pontos if 0 < n < 1 and d < r.duty_pleno]
    pontos += [(0.0, 0), (r.lux_piso / r.lux_classe, r.duty_piso), (1.0, r.duty_pleno)]
    pontos.sort()
    monotonos: list[tuple[float, int]] = []
    for n, d in pontos:
        if not monotonos or (n > monotonos[-1][0] and d > monotonos[-1][1]):
            monotonos.append((round(n, 4), d))
    return monotonos


def gravar_saidas(r: Relatorio, simulada: bool) -> None:
    tabela = tabela_firmware(r)
    rep = {
        "gerado_em": datetime.now(timezone.utc).isoformat(),
        "simulada": simulada,
        "sessao_id": r.sessao_id,
        "ponto": r.ponto,
        "classe": r.classe,
        "lux_classe": r.lux_classe,
        "lux_piso": r.lux_piso,
        "residual_lux": r.residual,
        "teto_liquido_lux": r.lux_teto,
        "teto_sobre_classe": round(r.lux_teto / r.lux_classe, 3),
        "comprimento_cm": r.comprimento_cm,
        "duty_pleno": r.duty_pleno,
        "duty_piso": r.duty_piso,
        "repeticoes_pleno_lux": r.repeticoes_pleno,
        "repeticoes_piso_lux": r.repeticoes_piso,
        "dispersao_relativa_pleno": round(dispersao(r.repeticoes_pleno), 4),
        "dispersao_relativa_piso": round(dispersao(r.repeticoes_piso), 4),
        "monotona": r.monotona,
        "series": {s: p for s, p in r.series.items()},
        "tabela_firmware": tabela,
    }
    pasta = RAIZ / "bancada" / "resultados"
    pasta.mkdir(parents=True, exist_ok=True)
    nome = f"sessao_{r.sessao_id}{'_SIMULADA' if simulada else ''}.json"
    (pasta / nome).write_text(json.dumps(rep, indent=2, ensure_ascii=False), encoding="utf-8")

    cab = RAIZ / "firmware" / "no" / ("calibracao_SIMULADA.h" if simulada else "calibracao.h")
    cab.parent.mkdir(parents=True, exist_ok=True)
    linhas = ",\n".join(f"  {{{n:.4f}f, {d}}}" for n, d in tabela)
    cab.write_text(
        f"""// GERADO por bancada/calibrar.py - nao edite a mao.
// Sessao {r.sessao_id} ({'SIMULADA - nao usar no TCC' if simulada else 'bancada real'}),
// {rep['gerado_em']}. Classe {r.classe}: 1,0 = {r.lux_classe} lx, piso = {r.lux_piso} lx.
// duty(1,0) = {r.duty_pleno} e duty(piso) = {r.duty_piso} foram MEDIDOS (3.4.2).
#pragma once

struct PontoCalibracao {{ float nivel; int duty; }};

const PontoCalibracao CALIBRACAO[] = {{
{linhas}
}};
const int N_CALIBRACAO = {len(tabela)};
const int CALIBRACAO_SESSAO = {r.sessao_id or 0};
""",
        encoding="utf-8",
    )
    print(f"\nrelatorio: {pasta / nome}\ntabela do firmware: {cab}")
    print(f"duty 10 lx = {r.duty_pleno} ({r.duty_pleno / DUTY_MAX:.1%}) | "
          f"duty 5 lx = {r.duty_piso} ({r.duty_piso / DUTY_MAX:.1%})")
    print(f"dispersao entre repeticoes: pleno {rep['dispersao_relativa_pleno']:.2%}, "
          f"piso {rep['dispersao_relativa_piso']:.2%}  -> base da tolerancia do RF11")
    print(f"curva monotona: {'sim' if r.monotona else 'NAO - verifique a montagem'}")


def main(argv: list[str] | None = None) -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("modo", choices=["teto", "completa"])
    p.add_argument("--porta", default="COM3")
    p.add_argument("--ponto", default="BANCADA-01")
    p.add_argument("--comprimento-cm", type=float, default=None)
    p.add_argument("--series", type=int, default=3)
    p.add_argument("--pontos", type=int, default=33, help="niveis de duty na varredura")
    p.add_argument("--forcar", action="store_true", help="segue mesmo com teto fora do criterio")
    p.add_argument("--simulada", action="store_true", help="sem hardware (curva sintetica)")
    args = p.parse_args(argv)

    b = BancadaSimulada() if args.simulada else Bancada(args.porta)
    # Simulada: tudo numa transacao desfeita ao final - numero sintetico
    # nunca fica no banco.
    conn = psycopg.connect(config.DATABASE_URL, autocommit=not args.simulada)
    try:
        if args.modo == "teto":
            cmd_teto(b, classe_do_ponto(conn, args.ponto)[2])
            return
        r = cmd_completa(b, conn, args)
        if r.duty_pleno is not None:
            gravar_saidas(r, args.simulada)
    finally:
        if args.simulada:
            conn.rollback()
        conn.close()


if __name__ == "__main__":
    main(sys.argv[1:])
