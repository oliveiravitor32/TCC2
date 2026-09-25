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
# O BH1750 mede continuamente. Depois de trocar o duty, a proxima leitura e
# a de uma conversao que COMECOU ANTES da troca (luz antiga ou mistura das
# duas), e a seguinte ainda pode estar nesse caso com o registrador no maximo
# (conversao de ate ~660 ms). Duas leituras sao descartadas antes de medir.
# Achado do monitor de 10 min: a primeira leitura com a fita no maximo veio
# 0,00 lx, e o `teto` media 24,0 lx quando o valor real era 25,5 lx.
LEITURAS_DESCARTADAS = 2


# ---------------------------------------------------------------------------
# Acesso ao no
# ---------------------------------------------------------------------------
class Bancada:
    """Fala com o sketch de calibracao pela serial."""

    def __init__(self, porta: str) -> None:
        import serial  # pyserial

        try:
            self.s = serial.Serial(porta, 115200, timeout=5)
        except serial.SerialException as erro:
            raise SystemExit(
                f"nao consegui abrir {porta}: {erro}\n"
                "  - o Monitor Serial da Arduino IDE esta aberto? feche-o\n"
                "  - a porta esta certa? use --porta COMx"
            ) from None
        print(f"conectando em {porta}...")
        # Abrir a porta reinicia o ESP32: espera a identificacao.
        fim = time.monotonic() + 10
        while time.monotonic() < fim:
            l = self._linha(timeout_ok=True)
            if "ID calibracao" in l:
                # A propria linha traz o autoteste do sensor.
                print(f"no respondeu: {l}")
                if "0.00 lx" in l:
                    print("  ATENCAO: autoteste leu 0,00 lx com a fita apagada -"
                          " normal se a caixa estiver bem vedada")
                return
            self.s.write(b"?\n")
        raise SystemExit(
            f"o ESP32 em {porta} nao respondeu 'ID calibracao v1'.\n"
            "  Grave bancada/calibracao/calibracao.ino na placa.\n"
            "  (o sketch de diagnostico NAO serve para calibrar)"
        )

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
        self.medir(LEITURAS_DESCARTADAS)  # descarta as conversoes anteriores a troca

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
        # Reproduz o sensor real: apos trocar o duty, as primeiras leituras
        # ainda sao do nivel anterior.
        self._velhas: list[float] = []

    def _nivel(self, d: int) -> float:
        return self.teto * (d / DUTY_MAX) ** self.gama + self.residual

    def _aplicar(self, n: int) -> None:
        """Troca o duty SEM descartar leituras, como o sensor faria."""
        self._velhas = [self._nivel(self.d)] * LEITURAS_DESCARTADAS
        self.d = n

    def duty(self, n: int) -> None:
        self._aplicar(n)
        self.medir(LEITURAS_DESCARTADAS)

    def medir(self, k: int) -> list[float]:
        valores = []
        for _ in range(k):
            base = self._velhas.pop(0) if self._velhas else self._nivel(self.d)
            valores.append(round(max(0.0, base + self.rng.gauss(0, 0.05)), 2))
        return valores


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
    print("medindo a residual (luz apagada, ~5 s)...")
    b.duty(0)
    return statistics.fmean(b.medir(10))


def conectar_banco(simulada: bool) -> psycopg.Connection:
    """Falha rapido e explica: sem timeout, um banco parado trava o script."""
    print("conectando no banco...")
    try:
        return psycopg.connect(
            config.DATABASE_URL, autocommit=not simulada, connect_timeout=5
        )
    except psycopg.OperationalError as erro:
        raise SystemExit(
            f"nao consegui falar com o Postgres: {erro}\n"
            "  Abra o Docker Desktop e rode:  docker compose up -d"
        ) from None


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
    if teto < 1.0:
        print("\nPROBLEMA: o sensor le quase nada com a fita no MAXIMO.")
        print("  Nao e comprimento de fita - e a fita apagada ou o sensor sem ve-la:")
        print("  1. a fita acende? olhe dentro da caixa com o duty no maximo")
        print("  2. fonte de 12 V ligada? OUT+ / OUT- do D4184 na fita?")
        print("  3. GPIO25 no TRIG do modulo e GND comum?")
        print("  4. o sensor esta virado para a fita, sem difusor demais em cima dele?")
        return
    if residual > RESIDUAL_MAX * lux_classe:
        print(f"ATENCAO: residual acima de {RESIDUAL_MAX:.0%} da classe - melhore o anteparo (3.4.3)")
    if razao < TETO_MIN:
        print(f"FITA CURTA: aumente o segmento (alvo {TETO_MIN}x a {TETO_MAX}x)")
    elif razao > TETO_MAX:
        print(f"FITA LONGA: encurte o segmento (alvo {TETO_MIN}x a {TETO_MAX}x)")
    else:
        print("OK: comprimento dentro do criterio de 3.4.2")


JANELA_ESTAVEL_S = 60   # janela em que se julga a estabilidade
# Estavel = a MEDIA do ultimo minuto mudou menos que isto em relacao a media
# do minuto anterior. Olhar a amplitude (max - min) nao funciona: cada degrau
# do BH1750 vale ~0,11 lx, cerca de 0,44 % da leitura no teto, e a leitura
# oscila entre dois degraus vizinhos mesmo com a luz parada. A media filtra
# essa oscilacao; a deriva de aquecimento aparece nela.
LIMIAR_ESTAVEL = 0.001  # 0,1 % entre medias de minutos consecutivos


def cmd_monitor(b, duty: int, limite_s: float | None = None) -> None:
    """Fixa o duty e acompanha a lux ate Ctrl+C (ou ate `limite_s`).

    Mostra a deriva desde o inicio e diz quando a leitura estabiliza - o que
    serve para saber quanto tempo a bancada precisa aquecer antes da
    calibracao (3.4.4). Grava tudo em bancada/resultados/aquecimento_*.csv.
    """
    pasta = RAIZ / "bancada" / "resultados"
    pasta.mkdir(parents=True, exist_ok=True)
    arquivo = pasta / f"aquecimento_{datetime.now():%Y%m%d_%H%M%S}.csv"

    b.duty(duty)
    print(f"duty fixo em {duty} ({duty / DUTY_MAX:.0%}). Ctrl+C para parar.")
    print(f"gravando em {arquivo}\n")
    print(f"{'tempo':>7s}  {'lux':>7s}  {'desde o inicio':>15s}  {'min':>6s}  {'max':>6s}  estado")

    inicio = time.monotonic()
    leituras: list[tuple[float, float]] = []  # (segundos, lux)
    estavel_desde: float | None = None
    try:
        with arquivo.open("w", encoding="utf-8") as csv:
            csv.write("segundos,lux\n")
            while limite_s is None or time.monotonic() - inicio < limite_s:
                lux = statistics.fmean(b.medir(1))
                t = time.monotonic() - inicio
                leituras.append((t, lux))
                csv.write(f"{t:.1f},{lux:.2f}\n")
                csv.flush()

                primeira = leituras[0][1]
                valores = [v for _, v in leituras]
                deriva = (lux - primeira) / primeira if primeira else 0.0

                # Estavel = a media do ultimo minuto quase nao mudou em relacao
                # a do minuto anterior (ver LIMIAR_ESTAVEL).
                if t < 2 * JANELA_ESTAVEL_S:
                    estado = "aquecendo..."
                else:
                    atual = [v for s, v in leituras if s >= t - JANELA_ESTAVEL_S]
                    anterior = [v for s, v in leituras
                                if t - 2 * JANELA_ESTAVEL_S <= s < t - JANELA_ESTAVEL_S]
                    m_atual, m_anterior = statistics.fmean(atual), statistics.fmean(anterior)
                    variacao = (m_atual - m_anterior) / m_anterior if m_anterior else 0.0
                    if abs(variacao) <= LIMIAR_ESTAVEL:
                        estavel_desde = estavel_desde if estavel_desde is not None else t
                        estado = f"ESTAVEL (media {variacao:+.2%} no ultimo minuto)"
                    else:
                        estavel_desde = None
                        estado = f"variando: media {variacao:+.2%} no ultimo minuto"

                print(f"{t:6.0f}s  {lux:7.2f}  {lux - primeira:+8.2f} ({deriva:+.1%})"
                      f"  {min(valores):6.2f}  {max(valores):6.2f}  {estado}")
    except KeyboardInterrupt:
        pass
    finally:
        b.duty(0)

    if len(leituras) > 1:
        valores = [v for _, v in leituras]
        total = leituras[-1][0]
        print(f"\nfita apagada. {len(leituras)} leituras em {total:.0f} s.")
        relativa = (valores[-1] - valores[0]) / valores[0] if valores[0] else 0.0
        print(f"  inicio {valores[0]:.2f} lx -> fim {valores[-1]:.2f} lx "
              f"(deriva {valores[-1] - valores[0]:+.2f} lx, {relativa:+.1%})")
        print(f"  minimo {min(valores):.2f} | maximo {max(valores):.2f} | "
              f"desvio padrao {statistics.pstdev(valores):.3f} lx")
        if estavel_desde is not None:
            print(f"  estabilizou por volta de {estavel_desde - 2 * JANELA_ESTAVEL_S:.0f} s: "
                  "aqueca a bancada pelo menos isso antes de calibrar.")
        else:
            print("  nao chegou a estabilizar: deixe mais tempo ligada.")
        print(f"  dados: {arquivo}")


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
    p.add_argument("modo", choices=["teto", "completa", "monitor"])
    p.add_argument("--duty", type=int, default=DUTY_MAX, help="modo monitor: duty fixo 0..4095")
    p.add_argument("--minutos", type=float, default=None,
                   help="modo monitor: para sozinho depois deste tempo")
    p.add_argument("--porta", default="COM3")
    p.add_argument("--ponto", default="BANCADA-01")
    p.add_argument("--comprimento-cm", type=float, default=None)
    p.add_argument("--series", type=int, default=3)
    p.add_argument("--pontos", type=int, default=33, help="niveis de duty na varredura")
    p.add_argument("--forcar", action="store_true", help="segue mesmo com teto fora do criterio")
    p.add_argument("--simulada", action="store_true", help="sem hardware (curva sintetica)")
    args = p.parse_args(argv)

    b = BancadaSimulada() if args.simulada else Bancada(args.porta)
    if args.modo == "monitor":  # nao precisa de banco
        cmd_monitor(b, max(0, min(args.duty, DUTY_MAX)),
                    args.minutos * 60 if args.minutos else None)
        return
    # Simulada: tudo numa transacao desfeita ao final - numero sintetico
    # nunca fica no banco.
    conn = conectar_banco(args.simulada)
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
