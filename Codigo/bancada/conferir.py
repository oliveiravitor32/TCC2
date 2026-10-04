"""Confere se a bancada continua calibrada antes de usar (cerca de 1 min).

Pensado para o inicio de cada sessao e para a demonstracao: com o firmware
do no gravado (firmware/no/no.ino), ligue o USB e rode

    python -m bancada.conferir                 # porta COM3, ponto BANCADA-01
    python -m bancada.conferir --porta COM5
    python -m bancada.conferir --recalibrar    # se reprovar, recalibra sem perguntar
    python -m bancada.conferir --vm            # grava pela API da VM (ROTEIRO, secao 10)

Com o no ligado a VM, use --vm: a sessao aberta (com a residual de agora)
tem de estar no MESMO banco que recebe a telemetria, senao a VM continua
descontando a residual antiga. Exige CHAVE_API_VM (a CHAVE_API do .env da
VM; a chave publica do painel e recusada nesses endpoints).

O que faz, pela serial, com o no em modo manutencao:
  1. mede a residual com a fita apagada (3.4.3: descarta se > 5 % da classe);
  2. comanda o pleno, a classe intermediaria e o piso PELA TABELA GRAVADA NO
     NO e mede a iluminancia de cada um;
  3. compara com o esperado (nivel x valor da classe). O limite e a mesma
     tolerancia do diagnostico (decisao/diagnostico.py, 3.4.5): o maior entre
     K_SIGMA x a dispersao do ensaio de repetibilidade e 1,5 degrau do sensor
     sobre o piso. Nao e um numero novo;
  4. APROVADA: a sessao fica aberta no banco, com a residual medida agora, e
     a telemetria passa a ser descontada dela. REPROVADA: diz o que falhou e
     oferece recalibrar ali mesmo (bancada/calibrar.py completa), gravando a
     tabela nova no no sem recompilar, e confere de novo.
Ao terminar, o no sai da manutencao e volta sozinho ao servico (VM).

Sem banco (Docker parado), a conferencia roda igual e o resultado fica so em
bancada/resultados/conferencia_*.json; a recalibracao exige o banco.
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
from argparse import Namespace
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from bancada import destino as destinos
from bancada.calibrar import (
    RAIZ,
    RESIDUAL_MAX,
    Bancada,
    BancadaSimulada,
    cmd_completa,
    enviar_ao_no,
    gravar_saidas,
    medir_residual,
)
from bancada.destino import tolerancia_do_relatorio, ultimo_relatorio  # noqa: F401 (testes)

LEITURAS = 5  # leituras por nivel; a media entra na comparacao


@dataclass
class Nivel:
    nivel: float
    duty: int
    lux_esperado: float
    lux_liquido: float
    razao: float
    ok: bool


@dataclass
class Conferencia:
    ponto: str
    classe: str
    lux_classe: float
    lux_piso: float
    sessao_tabela_no: int | None
    tolerancia: float
    origem_tolerancia: str
    residual: float = 0.0
    residual_ok: bool = True
    niveis: list[Nivel] = field(default_factory=list)
    aprovada: bool = False
    motivo: str = ""
    sessao_id: int | None = None


# ---------------------------------------------------------------------------
# Conferencia
# ---------------------------------------------------------------------------
def niveis_a_conferir(lux_classe: float, lux_piso: float) -> list[float]:
    """Pleno, piso e o ponto medio: os degraus de classe da base v4 (P3, P4, P5)."""
    piso = lux_piso / lux_classe
    return [1.0, round((1.0 + piso) / 2, 4), round(piso, 4)]


def conferir(b, c: Conferencia) -> Conferencia:
    c.residual = round(medir_residual(b), 3)
    c.residual_ok = c.residual <= RESIDUAL_MAX * c.lux_classe
    print(f"residual {c.residual:.2f} lx "
          f"({'ok' if c.residual_ok else f'ACIMA de {RESIDUAL_MAX:.0%} da classe'})")
    if not c.residual_ok:
        c.motivo = "residual alta: escureca a bancada (anteparo) e repita (3.4.3)"
        return c

    print(f"tolerancia {c.tolerancia:.1%} ({c.origem_tolerancia})")
    for n in niveis_a_conferir(c.lux_classe, c.lux_piso):
        duty = b.nivel(n)
        liquido = statistics.fmean(b.medir(LEITURAS)) - c.residual
        esperado = n * c.lux_classe
        razao = liquido / esperado
        ok = abs(razao - 1.0) <= c.tolerancia
        c.niveis.append(Nivel(n, duty, round(esperado, 3), round(liquido, 3), round(razao, 4), ok))
        print(f"  nivel {n:.3f} (duty {duty:4d}): {liquido:6.2f} lx de {esperado:5.2f} lx "
              f"esperados ({razao - 1:+.1%})  {'ok' if ok else 'FORA'}")
    b.duty(0)

    c.aprovada = all(x.ok for x in c.niveis)
    if not c.aprovada:
        if c.niveis[0].lux_liquido < 0.1 * c.niveis[0].lux_esperado:
            c.motivo = ("a fita nao acende ou o sensor nao a ve: confira fonte de 12 V, "
                        "D4184 (TRIG no GPIO25, GND comum) e a posicao do sensor")
        else:
            c.motivo = "iluminancia fora da tolerancia: a bancada mudou; recalibre"
    return c


# ---------------------------------------------------------------------------
# Registro
# ---------------------------------------------------------------------------
def observacao(c: Conferencia) -> str:
    resumo = "; ".join(f"{x.nivel:.3f}:{x.razao - 1:+.1%}" for x in c.niveis)
    return (f"conferencia (bancada/conferir.py): {'APROVADA' if c.aprovada else 'REPROVADA'}; "
            f"tolerancia {c.tolerancia:.1%}; tabela do no = sessao {c.sessao_tabela_no}; {resumo}")


def gravar_json(c: Conferencia, simulada: bool) -> Path:
    pasta = RAIZ / "bancada" / "resultados"
    pasta.mkdir(parents=True, exist_ok=True)
    base = f"conferencia_{datetime.now():%Y%m%d_%H%M%S}"
    arq = pasta / f"{base}{'_SIMULADA' if simulada else ''}.json"
    n = 1
    while arq.exists():  # a reconferencia apos recalibrar nao sobrescreve a primeira
        n += 1
        arq = pasta / f"{base}_{n}{'_SIMULADA' if simulada else ''}.json"
    dados = {"gerado_em": datetime.now(timezone.utc).isoformat(), "simulada": simulada, **asdict(c)}
    arq.write_text(json.dumps(dados, indent=2, ensure_ascii=False), encoding="utf-8")
    return arq


# ---------------------------------------------------------------------------
def preparar(b, destino, ponto: str) -> Conferencia:
    classe, lux_classe, lux_piso = destino.classe(ponto)
    tol, origem = destino.tolerancia(ponto)
    return Conferencia(ponto, classe, lux_classe, lux_piso, b.sessao_no, tol, origem)


def rodada(b, destino, args) -> Conferencia:
    c = preparar(b, destino, args.ponto)
    conferir(b, c)
    # Aprovada: a sessao fica aberta (residual de agora) e as anteriores sao
    # encerradas; reprovada: encerrada na hora, so como registro.
    c.sessao_id = destino.conferencia(args.ponto, c.residual, c.aprovada, observacao(c))
    arq = gravar_json(c, args.simulada)
    print(f"\n{'APROVADA - pode usar' if c.aprovada else 'REPROVADA: ' + c.motivo}")
    print(f"registro: {arq}" + (f" | sessao {c.sessao_id} em {destino.nome}" if c.sessao_id else ""))
    return c


def perguntar(texto: str) -> bool:
    try:
        return input(texto).strip().lower() in ("s", "sim", "y")
    except EOFError:
        return False


def main(argv: list[str] | None = None) -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--porta", default="COM3")
    p.add_argument("--ponto", default="BANCADA-01")
    p.add_argument("--recalibrar", action="store_true", help="se reprovar, recalibra sem perguntar")
    p.add_argument("--comprimento-cm", type=float, default=None, help="so na recalibracao")
    p.add_argument("--simulada", action="store_true", help="sem hardware (curva sintetica)")
    p.add_argument("--vm", action="store_true",
                   help="grava pela API da VM, no banco da telemetria (CHAVE_API_VM)")
    args = p.parse_args(argv)

    if args.simulada:
        b = BancadaSimulada()
        # O no simulado comeca com a tabela da ultima calibracao real, que
        # nao casa com a curva sintetica: exercita o caminho da recalibracao.
        rel = ultimo_relatorio(args.ponto)
        if rel:
            b.enviar_tabela([tuple(x) for x in rel["tabela_firmware"]], rel["sessao_id"])
    else:
        b = Bancada(args.porta)
    if not getattr(b, "firmware_no", False):
        raise SystemExit("a conferencia usa o firmware do no (firmware/no/no.ino); grave-o na placa")
    destino = destinos.abrir(args.vm, args.simulada, obrigatorio=False)
    print(f"resultados vao para: {destino.nome}")
    try:
        c = rodada(b, destino, args)
        recalibravel = not c.aprovada and c.residual_ok and c.niveis and c.niveis[0].lux_liquido > 0
        if recalibravel and destino.grava and (
                args.recalibrar or perguntar("\nRecalibrar agora (alguns minutos)? [s/N] ")):
            r = cmd_completa(b, destino, Namespace(ponto=args.ponto, series=3, pontos=33,
                                                   forcar=False, comprimento_cm=args.comprimento_cm))
            if r.duty_pleno is not None:
                gravar_saidas(r, args.simulada)
                enviar_ao_no(b, r)
                print("\nconferindo de novo com a tabela nova...")
                c = rodada(b, destino, args)
        elif recalibravel:
            print("para recalibrar, suba o banco (docker compose up -d) ou use --vm e rode de novo")
    finally:
        destino.fechar()
        b.sair()
        print("no fora da manutencao: volta ao pleno e ao controle do servico")
    sys.exit(0 if c.aprovada else 1)


if __name__ == "__main__":
    main(sys.argv[1:])
