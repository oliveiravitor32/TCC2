"""Executor da suite de cenarios (TCC 3.9, RF10; resultados 5.2, 5.4 e 5.5).

    python -m cenarios.executar                    # toda a suite, modo antecipado
    python -m cenarios.executar --reativo          # sem previsao (H3)
    python -m cenarios.executar --cenario noite_tipica

RELOGIO VIRTUAL. O cenario roda em tempo simulado, com passo igual ao
periodo do ciclo. Uma rampa de cinco minutos continua tendo 60 passos e
continua limitada a 0,1 do pleno por minuto - o que muda e so quanto tempo
de parede a execucao consome. Isso torna a suite repetivel (RF10) e permite
cenarios de horas. A latencia fisica (RNF03) nao se mede aqui: ela e medida
na Etapa 5, com o no.

O que cada execucao produz:
  - RNF01/RNF02 (5.2): violacoes de piso, de taxa e de meteorologia, contadas
    sobre o registro de decisoes. O esperado e zero;
  - 5.4: aderencia ao envelope esperado de cada trecho;
  - 5.5: energia do regime adaptativo e das duas linhas de base de 3.11;
  - H3: fracao da janela de baixa demanda consumida em transicao.

O historico que antecede o cenario e SINTETICO e existe para que a camada de
previsao tenha o que consumir; esta declarado no relatorio.
"""

from __future__ import annotations

import argparse
import json
import math
from dataclasses import dataclass
from datetime import datetime, time, timedelta, timezone
from decimal import Decimal
from pathlib import Path

import psycopg

from decisao import ciclo, config
from decisao.energia import (
    energia_decisoes,
    energia_pleno_constante,
    trajetoria_horario_fixo,
)
from decisao.inferencia import carregar
from decisao.previsao import carregar_previsor

AQUI = Path(__file__).resolve().parent
SUITE = AQUI / "suite"
RESULTADOS = AQUI / "resultados"

# Linha de base 2 (3.11): programacao agendada, sem dado urbano.
HORA_INICIO_ATENUACAO = time(0, 0)
HORA_FIM_ATENUACAO = time(5, 0)
# Luminaria de referencia do Quadro 9 usada no relatorio (a razao entre
# regimes independe da potencia; os dois extremos sao reportados).
POTENCIAS_REFERENCIA = {"REF-40W": 40.0, "REF-440W": 440.0}
HORAS_HISTORICO = 168


# ---------------------------------------------------------------------------
# Historico sintetico
# ---------------------------------------------------------------------------
def perfil_horario(momento: datetime) -> float:
    """Nivel tipico de movimentacao normalizada, por hora e dia da semana.

    Curva sintetica com dois picos (manha e fim de tarde) e vale de
    madrugada, achatada no fim de semana. Nao e dado de Melbourne: serve
    para dar ao modelo um passado plausivel antes do cenario comecar.
    """
    h = momento.hour + momento.minute / 60
    manha = math.exp(-((h - 8.5) ** 2) / 4)
    tarde = math.exp(-((h - 17.5) ** 2) / 6)
    base = 0.08 + 0.55 * manha + 0.75 * tarde
    if momento.weekday() >= 5:
        base = 0.06 + 0.55 * base
    return round(min(max(base, 0.0), 1.0), 3)


# ---------------------------------------------------------------------------
# Cenario
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class Cenario:
    nome: str
    descricao: str
    origem: str
    inicio_local: datetime
    duracao_min: float
    eventos: list[dict]
    envelope: list[dict]
    adversarial: bool = False

    @staticmethod
    def de_arquivo(p: Path) -> "Cenario":
        d = json.loads(p.read_text(encoding="utf-8"))
        return Cenario(
            nome=d.get("nome", p.stem),
            descricao=d["descricao"],
            origem=d.get("origem", ""),
            inicio_local=datetime.fromisoformat(d["inicio_local"]).replace(tzinfo=config.FUSO),
            duracao_min=float(d["duracao_min"]),
            eventos=d["eventos"],
            envelope=d["envelope"],
            adversarial=bool(d.get("adversarial", False)),
        )

    def faixa(self, minuto: float) -> dict | None:
        for t in self.envelope:
            if t["de_min"] <= minuto < t["ate_min"]:
                return t
        return None


def carregar_suite(nome: str | None = None) -> list[Cenario]:
    arquivos = sorted(SUITE.glob("*.json"))
    if nome:
        arquivos = [p for p in arquivos if p.stem == nome]
        if not arquivos:
            raise SystemExit(f"cenario {nome!r} nao encontrado em {SUITE}")
    return [Cenario.de_arquivo(p) for p in arquivos]


# ---------------------------------------------------------------------------
# Execucao
# ---------------------------------------------------------------------------
def _inserir_evento(conn, quando: datetime, tipo: str, valor=None, rotulo=None,
                    vigente_ate=None, origem="cenario") -> None:
    conn.execute(
        "INSERT INTO evento_urbano (ocorrido_em, tipo, valor, rotulo, origem, vigente_ate)"
        " VALUES (%s, %s, %s, %s, %s, %s)",
        (quando, tipo, valor, rotulo, origem, vigente_ate),
    )


def _semear_historico(conn, inicio: datetime) -> None:
    """Uma leitura por hora nas 168 h anteriores ao cenario (perfil sintetico)."""
    for k in range(HORAS_HISTORICO, 0, -1):
        quando = (inicio - timedelta(hours=k)).replace(minute=0, second=0, microsecond=0)
        _inserir_evento(conn, quando, "movimentacao", valor=perfil_horario(quando.astimezone(config.FUSO)),
                        vigente_ate=quando + timedelta(hours=1), origem="cenario-historico")


def executar(conn, cenario: Cenario, *, reativo: bool, previsao: str | None,
             indice: int = 0) -> dict:
    """Roda um cenario no relogio virtual.

    `indice` desloca o cenario em SEMANAS inteiras. Os cenarios declaram
    horarios do dia que se sobrepoem (a chuva as 02h cairia dentro da
    madrugada ociosa, que vai das 01h as 03h), e uma condicao declarada em um
    contaminaria o outro. O deslocamento em semanas separa as janelas sem
    alterar a hora do dia nem o dia da semana - as duas coisas que entram na
    decisao (faixa horaria na inferencia, dia da semana no modelo).
    """
    base = carregar(config.REGRAS)
    previsor = carregar_previsor(previsao)
    ponto = ciclo.pontos(conn)[0]
    inicio = (cenario.inicio_local + timedelta(weeks=indice)).astimezone(timezone.utc)
    fim = inicio + timedelta(minutes=cenario.duracao_min)

    with conn.transaction():
        execucao_id = conn.execute(
            "INSERT INTO execucao_cenario (cenario, regime, modo_previsao, iniciada_em, observacao)"
            " VALUES (%s, 'adaptativo', %s, %s, %s) RETURNING id",
            (cenario.nome, "reativo" if reativo else "antecipado", inicio,
             f"relogio virtual, passo {config.PERIODO_S} s; previsao {previsor.rotulo}; deslocamento de {indice} semana(s)"),
        ).fetchone()[0]
        _semear_historico(conn, inicio)

        pendentes = sorted(cenario.eventos, key=lambda e: e["em_min"])
        registro: list[dict] = []
        versao_regras_id = ciclo.registrar_versao_regras(conn, base)
        versao_modelo_id = ciclo.id_modelo(conn, previsor.rotulo)
        agora, i = inicio, 0
        while agora < fim:
            minuto = (agora - inicio).total_seconds() / 60
            while i < len(pendentes) and pendentes[i]["em_min"] <= minuto:
                e = pendentes[i]
                vig = e.get("vigente_min")
                _inserir_evento(
                    conn, agora, e["tipo"], e.get("valor"), e.get("rotulo"),
                    agora + timedelta(minutes=vig) if vig else None,
                )
                i += 1
            d = ciclo.decidir(
                conn, base=base, previsor=previsor, ponto=ponto, agora=agora,
                versao_regras_id=versao_regras_id, versao_modelo_id=versao_modelo_id,
                execucao_id=execucao_id, reativo=reativo, desde=inicio,
            )
            registro.append({
                "minuto": round(minuto, 3),
                "nivel_pretendido": float(d.nivel_pretendido),
                "nivel_emitido": float(d.nivel_emitido),
                "nivel_anterior": float(d.nivel_anterior) if d.nivel_anterior is not None else None,
                "restricao": d.restricao_aplicada,
                "observada": d.estado.observada,
                "meteorologia_adversa": d.estado.meteorologia_adversa,
                "ocorrencia": d.estado.ocorrencia,
                "criado_em": agora,
            })
            agora += timedelta(seconds=config.PERIODO_S)
        conn.execute("UPDATE execucao_cenario SET encerrada_em = %s WHERE id = %s", (fim, execucao_id))

    criterio = ciclo.criterio(conn, ponto.classe_codigo)
    # Fronteira "baixa/media" da base vigente: e ela que define o que conta
    # como janela de baixa demanda (2.10), e nao o julgamento dos autores.
    fronteira_baixa = (base.mov["baixa"][2] + base.mov["baixa"][3]) / 2
    return avaliar(cenario, registro, execucao_id, criterio, previsor.rotulo, reativo,
                   inicio, fim, fronteira_baixa)


# ---------------------------------------------------------------------------
# Avaliacao
# ---------------------------------------------------------------------------
def avaliar(cenario, registro, execucao_id, criterio, modelo, reativo, inicio, fim,
            fronteira_baixa: float) -> dict:
    piso = float(criterio.piso)
    taxa_passo = float(criterio.taxa_max_decrescimo_min) * config.PERIODO_S / 60

    violacoes_piso = [r for r in registro if r["nivel_emitido"] < piso - 1e-9]
    violacoes_taxa = [
        b for a, b in zip(registro, registro[1:])
        if a["nivel_emitido"] - b["nivel_emitido"] > taxa_passo + 1e-9
    ]
    violacoes_meteo = [
        r for r in registro if r["meteorologia_adversa"] and r["nivel_emitido"] < 1.0 - 1e-9
    ]

    dentro, fora, sem_envelope = 0, [], 0
    for r in registro:
        faixa = cenario.faixa(r["minuto"])
        if faixa is None:
            sem_envelope += 1
            continue
        if faixa["min"] - 1e-9 <= r["nivel_emitido"] <= faixa["max"] + 1e-9:
            dentro += 1
        else:
            fora.append({"minuto": r["minuto"], "nivel": r["nivel_emitido"],
                         "esperado": [faixa["min"], faixa["max"]]})

    # H3 (2.10): janela de baixa demanda = ciclos em que a movimentacao
    # observada fica abaixo da fronteira "baixa/media" da base de regras.
    # Deriva do dado do cenario, nao do envelope. "Em transicao" = ainda
    # acima do piso, isto e, a janela sendo gasta descendo em vez de no
    # nivel que ela justificaria.
    margem = 0.02
    # Ciclos sob chuva ou ocorrencia ficam de fora: neles o pleno e imposto
    # pela norma ou pela regra de dominio, e contar esses ciclos mediria a
    # verificacao, nao o efeito da previsao.
    em_baixa = [r for r in registro
                if r["observada"] is not None and r["observada"] < fronteira_baixa
                and not r["meteorologia_adversa"] and not r["ocorrencia"]]
    em_transicao = [r for r in em_baixa if r["nivel_emitido"] > piso + margem]

    decisoes = [(r["criado_em"], r["nivel_anterior"], r["nivel_emitido"]) for r in registro]
    energia = {}
    for nome, potencia in POTENCIAS_REFERENCIA.items():
        adaptativo = energia_decisoes(decisoes, potencia, fim=fim)
        pleno = energia_pleno_constante(potencia, cenario.duracao_min)
        fixo = energia_decisoes(
            trajetoria_horario_fixo(
                inicio, fim, piso,
                hora_inicio_atenuacao=HORA_INICIO_ATENUACAO,
                hora_fim_atenuacao=HORA_FIM_ATENUACAO,
                passo_s=config.PERIODO_S,
            ),
            potencia, fim=fim,
        )
        energia[nome] = {
            "adaptativo_wh": round(adaptativo, 3),
            "pleno_constante_wh": round(pleno, 3),
            "horario_fixo_wh": round(fixo, 3),
            "razao_adaptativo_pleno": round(adaptativo / pleno, 4) if pleno else None,
            "razao_adaptativo_fixo": round(adaptativo / fixo, 4) if fixo else None,
        }

    avaliados = dentro + len(fora)
    return {
        "cenario": cenario.nome,
        "descricao": cenario.descricao,
        "adversarial": cenario.adversarial,
        "execucao_id": execucao_id,
        "modo_previsao": "reativo" if reativo else "antecipado",
        "modelo": modelo,
        "decisoes": len(registro),
        "violacoes": {
            "piso": len(violacoes_piso),
            "taxa": len(violacoes_taxa),
            "meteorologia": len(violacoes_meteo),
        },
        "restricoes_aplicadas": {
            r: sum(1 for x in registro if x["restricao"] == r)
            for r in ("nenhuma", "piso", "taxa", "meteorologia")
        },
        "envelope": {
            "ciclos_avaliados": avaliados,
            "dentro": dentro,
            "aderencia": round(dentro / avaliados, 4) if avaliados else None,
            "ciclos_sem_envelope": sem_envelope,
            "discordancias": fora[:20],
        },
        "h3": {
            "fronteira_baixa": round(fronteira_baixa, 4),
            "ciclos_em_janela_baixa": len(em_baixa),
            "ciclos_em_transicao": len(em_transicao),
            "fracao_em_transicao": round(len(em_transicao) / len(em_baixa), 4) if em_baixa else None,
            "minutos_ate_o_piso": round(
                min((r["minuto"] for r in em_baixa if r["nivel_emitido"] <= piso + margem),
                    default=-1), 2),
        },
        "energia": energia,
    }


def main() -> None:
    p = argparse.ArgumentParser(description="Suite de cenarios (3.9, RF10)")
    p.add_argument("--cenario", default=None, help="roda so este cenario")
    p.add_argument("--reativo", action="store_true", help="sem previsao (H3)")
    p.add_argument("--previsao", choices=["persistencia", "xgboost"], default=None)
    p.add_argument("--saida", default=None, help="arquivo do relatorio")
    args = p.parse_args()

    cenarios = carregar_suite(args.cenario)
    relatorios = []
    with psycopg.connect(config.DATABASE_URL, connect_timeout=5) as conn:
        for i, c in enumerate(cenarios):
            r = executar(conn, c, reativo=args.reativo, previsao=args.previsao, indice=i)
            relatorios.append(r)
            v = r["violacoes"]
            print(f"{c.nome:34s} decisoes={r['decisoes']:4d} "
                  f"violacoes(piso/taxa/meteo)={v['piso']}/{v['taxa']}/{v['meteorologia']} "
                  f"aderencia={r['envelope']['aderencia']} "
                  f"energia={r['energia']['REF-40W']['adaptativo_wh']:.1f} Wh "
                  f"({r['energia']['REF-40W']['razao_adaptativo_pleno']:.0%} do pleno)")

    total = {
        "gerado_em": datetime.now(timezone.utc).isoformat(),
        "modo_previsao": "reativo" if args.reativo else "antecipado",
        "passo_s": config.PERIODO_S,
        "base_regras": carregar(config.REGRAS).rotulo,
        "cenarios": len(relatorios),
        "decisoes": sum(r["decisoes"] for r in relatorios),
        "violacoes_totais": {
            k: sum(r["violacoes"][k] for r in relatorios) for k in ("piso", "taxa", "meteorologia")
        },
        "relatorios": relatorios,
    }
    RESULTADOS.mkdir(exist_ok=True)
    nome = args.saida or f"suite_{'reativo' if args.reativo else 'antecipado'}.json"
    (RESULTADOS / nome).write_text(
        json.dumps(total, indent=2, ensure_ascii=False, default=str), encoding="utf-8"
    )
    print(f"\n{total['decisoes']} decisoes | violacoes: {total['violacoes_totais']}")
    print(f"relatorio: {RESULTADOS / nome}")


if __name__ == "__main__":
    main()
