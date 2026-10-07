"""Executor da suite de cenarios (TCC 3.9, RF10; resultados 5.2, 5.4 e 5.5).

    python -m cenarios.executar                    # toda a suite, modo antecipado
    python -m cenarios.executar --reativo          # sem previsao (H3)
    python -m cenarios.executar --degraus          # tabela em degraus (item 51)
    python -m cenarios.executar --cenario noite_tipica

RELOGIO VIRTUAL. O cenario roda em tempo simulado, com passo igual ao
periodo do ciclo. Uma rampa de cinco minutos continua tendo 60 passos e
continua limitada a 0,1 do pleno por minuto - o que muda e so quanto tempo
de parede a execucao consome. Isso torna a suite repetivel (RF10) e permite
cenarios de horas. A latencia fisica (RNF03) nao se mede aqui: ela e medida
na Etapa 5, com o no.

O que cada execucao produz:
  - RNF01/RNF02 (5.2): violacoes de piso e de taxa, contadas
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
from decisao.inferencia import carregar, em_degraus
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
    # Nivel normalizado de cada uma das 168 h anteriores (mais antiga
    # primeiro). Ausente = perfil sintetico. As noites reais de Melbourne
    # (avaliacao_ia/, DIVERGENCIAS 57) trazem o historico real.
    historico: list[float] | None = None

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
            historico=d.get("historico"),
        )

    def faixa(self, minuto: float) -> dict | None:
        for t in self.envelope:
            if t["de_min"] <= minuto < t["ate_min"]:
                return t
        return None


def carregar_suite(nome: str | None = None, pasta: Path = SUITE) -> list[Cenario]:
    arquivos = sorted(pasta.glob("*.json"))
    if nome:
        arquivos = [p for p in arquivos if p.stem == nome]
        if not arquivos:
            raise SystemExit(f"cenario {nome!r} nao encontrado em {pasta}")
    return [Cenario.de_arquivo(p) for p in arquivos]


# ---------------------------------------------------------------------------
# Execucao
# ---------------------------------------------------------------------------
def _inserir_volume(conn, quando: datetime, trecho_id: int, pessoas_media: float,
                    periodo_s: int = config.PERIODO_VOLUME_S, vigente_ate=None,
                    origem="cenario") -> None:
    """Volume do trecho: media de pessoas no periodo que termina em `quando`."""
    conn.execute(
        "INSERT INTO evento_urbano (ocorrido_em, tipo, pessoas_media, periodo_s, origem, trecho_id,"
        " vigente_ate) VALUES (%s, 'volume', %s, %s, %s, %s, %s)",
        (quando, round(pessoas_media, 2), periodo_s, origem, trecho_id, vigente_ate),
    )


def _inserir_ocorrencia(conn, quando: datetime, trecho_id: int, rotulo: str,
                        vigente_ate=None, origem="cenario") -> None:
    """Ocorrencia publicada na hora; 'encerrada' fecha a anterior."""
    conn.execute(
        "INSERT INTO evento_urbano (ocorrido_em, tipo, ocorrencia, origem, trecho_id, vigente_ate)"
        " VALUES (%s, 'ocorrencia', %s, %s, %s, %s)",
        (quando, rotulo, origem, trecho_id, vigente_ate),
    )


def trecho_principal(conn, ponto_id: int) -> int:
    """Trecho mais proximo do ponto: onde caem os eventos que o cenario nao
    localiza (DIVERGENCIAS 54). Os cenarios descrevem a via do ponto."""
    linha = conn.execute(
        "SELECT trecho_id FROM trecho_ponto WHERE ponto_de_luz_id = %s"
        " ORDER BY distancia_m, trecho_id LIMIT 1", (ponto_id,),
    ).fetchone()
    if linha is None:
        raise SystemExit("o ponto nao tem trecho associado: rode db/seed_cadastro.sql")
    return linha[0]


VOLUMES_POR_HORA = 3600 // config.PERIODO_VOLUME_S  # historico: um volume a cada 5 min


def _semear_historico(conn, inicio: datetime, execucao_id: int, trecho_id: int,
                      historico: list[float] | None = None) -> None:
    """Volumes nas 168 h anteriores ao cenario, pelo perfil sintetico.

    Um volume a cada 5 min, com a media de pessoas igual ao perfil daquela
    hora vezes a referencia inicial do trecho. Sao anteriores ao inicio da
    execucao (o estado da via so enxerga dali em diante) e so alimentam a
    previsao e a referencia (3.6).
    """
    ref = float(conn.execute(
        "SELECT referencia_pessoas FROM trecho_via WHERE id = %s", (trecho_id,)
    ).fetchone()[0])
    if historico is not None and len(historico) == 4 * HORAS_HISTORICO:
        # Historico real em blocos de 15 min (noites de Zurique, item 69).
        for k in range(4 * HORAS_HISTORICO, 0, -1):
            bloco = (inicio - timedelta(minutes=15 * k)).replace(second=0, microsecond=0)
            media = historico[4 * HORAS_HISTORICO - k] * ref
            for n in range(15 * 60 // config.PERIODO_VOLUME_S):
                _inserir_volume(conn, bloco + timedelta(seconds=config.PERIODO_VOLUME_S * n),
                                trecho_id, media, origem=f"cenario-historico:{execucao_id}")
        return
    if historico is not None and len(historico) != HORAS_HISTORICO:
        raise ValueError(f"historico deve ter {HORAS_HISTORICO} horas ou {4 * HORAS_HISTORICO} blocos de 15 min")
    for k in range(HORAS_HISTORICO, 0, -1):
        hora = (inicio - timedelta(hours=k)).replace(minute=0, second=0, microsecond=0)
        nivel = (historico[HORAS_HISTORICO - k] if historico is not None
                 else perfil_horario(hora.astimezone(config.FUSO)))
        media = nivel * ref
        for n in range(VOLUMES_POR_HORA):
            _inserir_volume(conn, hora + timedelta(seconds=config.PERIODO_VOLUME_S * n),
                            trecho_id, media, origem=f"cenario-historico:{execucao_id}")


class HistereseDescida:
    """Alternativa simples da avaliacao (DIVERGENCIAS 61): a tabela sobe de
    faixa no tercil, na hora, e so desce quando o volume cai `h` abaixo dele.
    Devolve o volume que a tabela deve ler (preso na fronteira enquanto a
    descida nao e confirmada)."""

    def __init__(self, f1: float, f2: float, h: float) -> None:
        self.f, self.h, self.faixa = (f1, f2), h, None

    def __call__(self, x: float) -> float:
        nova = 0 if x < self.f[0] else 1 if x < self.f[1] else 2
        if self.faixa is not None and nova < self.faixa:
            fronteira = self.f[self.faixa - 1]
            if x >= fronteira - self.h:
                return fronteira
        self.faixa = nova
        return x


def executar(conn, cenario: Cenario, *, reativo: bool, previsao: str | None,
             indice: int = 0, degraus: bool = False, serie: bool = False,
             histerese: float | None = None) -> dict:
    """Roda um cenario no relogio virtual.

    `indice` desloca o cenario em SEMANAS inteiras. Os cenarios declaram
    horarios do dia que se sobrepoem (a ocorrencia das 01h30 cairia dentro
    da madrugada ociosa, que vai das 01h as 03h), e uma condicao declarada em
    um contaminaria o outro. O deslocamento em semanas separa as janelas sem
    alterar a hora do dia nem o dia da semana - as duas coisas que entram na
    decisao (faixa horaria na inferencia, dia da semana no modelo).
    """
    base = carregar(config.REGRAS)
    if degraus:
        base = em_degraus(base)
    previsor = carregar_previsor(previsao)
    filtro = None
    if histerese is not None:
        f2 = (base.mov["alta"][0] + base.mov["alta"][1]) / 2
        filtro = HistereseDescida(fronteira_baixa(base), f2, histerese)
    ponto = ciclo.pontos(conn)[0]
    trecho = trecho_principal(conn, ponto.id)
    inicio = (cenario.inicio_local + timedelta(weeks=indice)).astimezone(timezone.utc)
    fim = inicio + timedelta(minutes=cenario.duracao_min)

    with conn.transaction():
        execucao_id = conn.execute(
            "INSERT INTO execucao_cenario (cenario, regime, modo_previsao, iniciada_em, observacao)"
            " VALUES (%s, 'adaptativo', %s, %s, %s) RETURNING id",
            (cenario.nome, "reativo" if reativo else "antecipado", inicio,
             f"relogio virtual, passo {config.PERIODO_S} s; previsao {previsor.rotulo}; regras {base.rotulo}; deslocamento de {indice} semana(s)"),
        ).fetchone()[0]
        _semear_historico(conn, inicio, execucao_id, trecho, cenario.historico)
        # Os cenarios declaram o volume como NIVEL normalizado (a escala das
        # fronteiras); aqui ele vira media de pessoas pela referencia que o
        # servico usa para o trecho no inicio da execucao.
        refs = ciclo.referencias(conn, inicio, ponto.id, ciclo.origens_da_execucao(execucao_id))

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
                vigente_ate = agora + timedelta(minutes=vig) if vig else None
                onde = e.get("trecho", trecho)
                if "ocorrencia" in e:
                    _inserir_ocorrencia(conn, agora, onde, e["ocorrencia"], vigente_ate,
                                        origem=f"cenario:{execucao_id}")
                else:
                    _inserir_volume(conn, agora, onde, e["nivel"] * refs[onde],
                                    e.get("periodo_s", config.PERIODO_VOLUME_S), vigente_ate,
                                    origem=f"cenario:{execucao_id}")
                i += 1
            d = ciclo.decidir(
                conn, base=base, previsor=previsor, ponto=ponto, agora=agora,
                versao_regras_id=versao_regras_id, versao_modelo_id=versao_modelo_id,
                execucao_id=execucao_id, reativo=reativo, desde=inicio,
                filtro_observada=filtro,
            )
            registro.append({
                "minuto": round(minuto, 3),
                "nivel_pretendido": float(d.nivel_pretendido),
                "nivel_emitido": float(d.nivel_emitido),
                "nivel_anterior": float(d.nivel_anterior) if d.nivel_anterior is not None else None,
                "restricao": d.restricao_aplicada,
                "observada": d.observada,
                "degrau": d.degrau,
                "sem_dado": d.estado.sem_dado,
                "ocorrencia": d.estado.ocorrencia,
                "criado_em": agora,
            })
            agora += timedelta(seconds=config.PERIODO_S)
        conn.execute("UPDATE execucao_cenario SET encerrada_em = %s WHERE id = %s", (fim, execucao_id))

    criterio = ciclo.criterio(conn, ponto.classe_codigo)
    r = avaliar(cenario, registro, execucao_id, criterio, previsor.rotulo, reativo, inicio, fim,
                fronteira_baixa=fronteira_baixa(base))
    if serie:
        r["serie"] = [{"minuto": x["minuto"], "emitido": x["nivel_emitido"],
                       "observada": x["observada"], "degrau": x["degrau"],
                       "ocorrencia": x["ocorrencia"], "sem_dado": x["sem_dado"]} for x in registro]
        r["inicio"] = inicio.isoformat()
    return r


def fronteira_baixa(base) -> float:
    """Tercil inferior da base (meio da rampa baixa/media)."""
    return (base.mov["baixa"][2] + base.mov["baixa"][3]) / 2


# ---------------------------------------------------------------------------
# Avaliacao
# ---------------------------------------------------------------------------
def avaliar(cenario, registro, execucao_id, criterio, modelo, reativo, inicio, fim,
            *, fronteira_baixa: float) -> dict:
    piso = float(criterio.piso)
    taxa_passo = float(criterio.taxa_max_decrescimo_min) * config.PERIODO_S / 60

    violacoes_piso = [r for r in registro if r["nivel_emitido"] < piso - 1e-9]
    violacoes_taxa = [
        b for a, b in zip(registro, registro[1:])
        if a["nivel_emitido"] - b["nivel_emitido"] > taxa_passo + 1e-9
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

    # H3 (2.10): janela de baixa demanda = ciclos com o volume observado
    # abaixo do tercil inferior (DIVERGENCIAS 56). Deriva do dado do cenario,
    # nao do envelope. "Em transicao" = ainda acima do piso, isto e, a janela
    # sendo gasta descendo em vez de no nivel que ela justificaria.
    margem = 0.02
    # Ciclos sob ocorrencia ou sem dado ficam de fora: neles o pleno e
    # imposto pela regra, e conta-los mediria a regra, nao a previsao.
    em_baixa = [r for r in registro
                if not r["sem_dado"] and not r["ocorrencia"]
                and r["observada"] is not None and r["observada"] < fronteira_baixa]
    em_transicao = [r for r in em_baixa if r["nivel_emitido"] > piso + margem]

    # Mudancas de nivel (item 51). A descida e limitada pela taxa; o que pode
    # ser brusco e a subida e o vai-e-volta. "Brusca" = subida de 0,1 do
    # pleno ou mais num unico passo.
    deltas = [b["nivel_emitido"] - a["nivel_emitido"] for a, b in zip(registro, registro[1:])]
    sinais = [1 if d > 1e-9 else -1 for d in deltas if abs(d) > 1e-9]
    mudancas = {
        "subidas_bruscas": sum(1 for d in deltas if d >= 0.1 - 1e-9),
        "maior_subida": round(max(deltas, default=0.0), 3),
        "variacao_total": round(sum(abs(d) for d in deltas), 3),
        "inversoes_de_sentido": sum(1 for a, b in zip(sinais, sinais[1:]) if a != b),
    }

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
                fuso=config.FUSO,
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
        },
        "restricoes_aplicadas": {
            r: sum(1 for x in registro if x["restricao"] == r)
            for r in ("nenhuma", "piso", "taxa")
        },
        "envelope": {
            "ciclos_avaliados": avaliados,
            "dentro": dentro,
            "aderencia": round(dentro / avaliados, 4) if avaliados else None,
            "ciclos_sem_envelope": sem_envelope,
            "discordancias": fora[:20],
        },
        "h3": {
            "janela": "volume observado abaixo do tercil inferior, sem ocorrencia",
            "ciclos_em_janela_baixa": len(em_baixa),
            "ciclos_em_transicao": len(em_transicao),
            "fracao_em_transicao": round(len(em_transicao) / len(em_baixa), 4) if em_baixa else None,
            "minutos_ate_o_piso": round(
                min((r["minuto"] for r in em_baixa if r["nivel_emitido"] <= piso + margem),
                    default=-1), 2),
        },
        "mudancas": mudancas,
        "energia": energia,
    }


def main() -> None:
    p = argparse.ArgumentParser(description="Suite de cenarios (3.9, RF10)")
    p.add_argument("--cenario", default=None, help="roda so este cenario")
    p.add_argument("--reativo", action="store_true", help="sem previsao (H3)")
    p.add_argument("--degraus", action="store_true",
                   help="mesma base como tabela em degraus, sem logica nebulosa (item 51)")
    p.add_argument("--previsao", choices=["persistencia", "xgboost", "media-sazonal"], default=None)
    p.add_argument("--histerese", type=float, default=None,
                   help="com --degraus: so desce de faixa com o volume H abaixo do tercil (item 61)")
    p.add_argument("--saida", default=None, help="arquivo do relatorio")
    p.add_argument("--pasta", default=None,
                   help="pasta de cenarios (padrao: suite/); ex.: avaliacao_ia/melbourne")
    p.add_argument("--serie", action="store_true",
                   help="inclui no relatorio o nivel emitido de cada ciclo (avaliacao das IAs)")
    args = p.parse_args()

    pasta = AQUI / args.pasta if args.pasta else SUITE
    cenarios = carregar_suite(args.cenario, pasta)
    relatorios = []
    with psycopg.connect(config.DATABASE_URL, connect_timeout=5) as conn:
        for i, c in enumerate(cenarios):
            r = executar(conn, c, reativo=args.reativo, previsao=args.previsao, indice=i,
                         degraus=args.degraus, serie=args.serie,
                         histerese=args.histerese)
            relatorios.append(r)
            v = r["violacoes"]
            print(f"{c.nome:34s} decisoes={r['decisoes']:4d} "
                  f"violacoes(piso/taxa)={v['piso']}/{v['taxa']} "
                  f"aderencia={r['envelope']['aderencia']} "
                  f"energia={r['energia']['REF-40W']['adaptativo_wh']:.1f} Wh "
                  f"({r['energia']['REF-40W']['razao_adaptativo_pleno']:.0%} do pleno)")

    total = {
        "gerado_em": datetime.now(timezone.utc).isoformat(),
        "modo_previsao": "reativo" if args.reativo else "antecipado",
        "passo_s": config.PERIODO_S,
        "base_regras": (em_degraus if args.degraus else (lambda b: b))(carregar(config.REGRAS)).rotulo,
        "cenarios": len(relatorios),
        "decisoes": sum(r["decisoes"] for r in relatorios),
        "violacoes_totais": {
            k: sum(r["violacoes"][k] for r in relatorios) for k in ("piso", "taxa")
        },
        "relatorios": relatorios,
    }
    RESULTADOS.mkdir(exist_ok=True)
    prefixo = args.pasta.replace("/", "_") if args.pasta else "suite"
    nome = args.saida or (f"{prefixo}_{'reativo' if args.reativo else 'antecipado'}"
                          f"{'_degraus' if args.degraus else ''}"
                          f"{'_histerese' if args.histerese is not None else ''}"
                          f"{'_' + args.previsao.replace('-', '_') if args.previsao else ''}.json")
    (RESULTADOS / nome).write_text(
        json.dumps(total, indent=2, ensure_ascii=False, default=str), encoding="utf-8"
    )
    print(f"\n{total['decisoes']} decisoes | violacoes: {total['violacoes_totais']}")
    print(f"relatorio: {RESULTADOS / nome}")


if __name__ == "__main__":
    main()
