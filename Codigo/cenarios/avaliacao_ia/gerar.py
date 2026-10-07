"""Gera os cenarios da avaliacao das IAs (DIVERGENCIAS 57).

    python -m cenarios.avaliacao_ia.gerar

Tudo aqui foi fixado ANTES de qualquer execucao (semente, sorteio, janelas,
metricas em PROTOCOLO.md). Os resultados sao reportados como vierem.

1. melbourne/  - 8 noites REAIS da serie de Melbourne, do periodo de TESTE do
   modelo (a partir do corte treino/teste): o modelo nunca viu essas horas no
   treino. 4 sensores sorteados (2 do grupo mais movimentado a noite, 2 do
   menos), cada um com uma noite de dia util e uma de fim de semana. O
   historico de 168 h e o real, e o volume da noite e o real, publicado a
   cada 5 min com o valor da hora corrente (a serie e horaria). Normalizacao
   igual a do treino: contagem / percentil 99 do sensor, limitada a 1. O
   relogio da noite e o de Sao Paulo, com a mesma hora do dia e o mesmo dia
   da semana (a faixa horaria e os atributos de calendario acompanham).

2. camera/ - dois pares de cenarios sinteticos (historico = perfil sintetico
   da suite): em cada par, o CONTROLE publica o movimento real, e a FALHA
   publica volume quase zero durante 2 h (camera obstruida, chuva), com o
   mesmo movimento real. Um par no inicio da noite (o historico diz
   "movimento"), outro na madrugada (o historico diz "calmo"). A mesma
   entrada da FALHA e a de uma rua realmente vazia: o que a previsao protege
   num caso, gasta no outro - as duas leituras sao reportadas.
"""

from __future__ import annotations

import json
import random
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd

from cenarios.executar import HORAS_HISTORICO, perfil_horario

AQUI = Path(__file__).resolve().parent
CSV = AQUI.parent.parent / "modelo" / "dados" / "melbourne_pedestres.csv"
METRICAS = AQUI.parent.parent / "modelo" / "resultados" / "metricas.json"

SEMENTE = 57
COBERTURA_MIN = 0.98          # como no treino (modelo/treinar.py)
HORAS_MIN = 17_000
PERCENTIL_CHEIO = 0.99
NOITE_H = 12                  # 18h -> 06h
PASSO_MIN = 5
NOITES = "zurique"            # pasta das noites reais (item 69; antes, "melbourne")
ENVELOPE_LIVRE = [{"de_min": 0, "ate_min": NOITE_H * 60, "min": 0.5, "max": 1.0,
                   "nota": "dado real: sem envelope a priori; a aderencia nao e avaliada"}]


def _serie() -> tuple[pd.DataFrame, pd.Timestamp]:
    d = pd.read_csv(CSV, usecols=["sensing_date", "hourday", "location_id", "pedestriancount"])
    d["ts"] = pd.to_datetime(d.sensing_date) + pd.to_timedelta(d.hourday, unit="h")
    g = d.groupby("location_id").ts.agg(["size", "min", "max"])
    possiveis = (g["max"] - g["min"]).dt.total_seconds() // 3600 + 1
    ok = g.index[(g["size"] / possiveis >= COBERTURA_MIN) & (g["size"] >= HORAS_MIN)]
    d = d[d.location_id.isin(ok)].copy()
    cheio = d.groupby("location_id").pedestriancount.transform(lambda s: s.quantile(PERCENTIL_CHEIO))
    d["nivel"] = (d.pedestriancount / cheio).clip(0, 1)
    corte = pd.Timestamp(json.loads(METRICAS.read_text(encoding="utf-8"))["corte_treino_teste"])
    return d[["location_id", "ts", "nivel"]], corte


def _noite(grade: pd.Series, inicio: pd.Timestamp) -> tuple[list[float], list[float]] | None:
    """168 h de historico + 12 h de noite, sem buraco; None se faltar hora."""
    horas = pd.date_range(inicio - pd.Timedelta(hours=HORAS_HISTORICO),
                          inicio + pd.Timedelta(hours=NOITE_H - 1), freq="h")
    v = grade.reindex(horas)
    if v.isna().any():
        return None
    v = [round(float(x), 4) for x in v]
    return v[:HORAS_HISTORICO], v[HORAS_HISTORICO:]


def melbourne(destino: Path) -> list[dict]:
    d, corte = _serie()
    teste = d[d.ts >= corte]
    noturno = teste[(teste.ts.dt.hour >= 18) | (teste.ts.dt.hour < 6)]
    media = noturno.groupby("location_id").nivel.mean().sort_values()
    metade = len(media) // 2
    calmos, movimentados = list(media.index[:metade]), list(media.index[metade:])
    rng = random.Random(SEMENTE)
    sensores = [("movimentado", s) for s in rng.sample(movimentados, 2)] + \
               [("calmo", s) for s in rng.sample(calmos, 2)]

    gerados = []
    for grupo, sensor in sensores:
        grade = d[d.location_id == sensor].set_index("ts").nivel.sort_index()
        grade = grade[~grade.index.duplicated()]
        dias = pd.date_range(corte.normalize() + pd.Timedelta(days=8), teste.ts.max().normalize()
                             - pd.Timedelta(days=1), freq="D")
        for tipo, filtro in (("dia_util", lambda x: x.weekday() < 4),   # seg-qui a noite
                             ("fim_de_semana", lambda x: x.weekday() == 5)):  # sabado a noite
            candidatos = [x for x in dias if filtro(x)]
            rng.shuffle(candidatos)
            for dia in candidatos:
                inicio = dia + pd.Timedelta(hours=18)
                noite = _noite(grade, inicio)
                if noite is not None:
                    break
            else:
                raise SystemExit(f"sem noite completa para o sensor {sensor} ({tipo})")
            historico, horas = noite
            nome = f"melbourne_{grupo}_{sensor}_{tipo}"
            cen = {
                "nome": nome,
                "descricao": (f"Noite real do sensor {sensor} de Melbourne ({grupo}, {tipo}), "
                              f"{inicio:%Y-%m-%d} 18h-06h, no periodo de teste do modelo."),
                "origem": (f"Serie de Melbourne extraida em 2026-09-23; sorteio com semente {SEMENTE} "
                           "(DIVERGENCIAS 57). Volume = valor da hora corrente a cada 5 min."),
                "inicio_local": f"{inicio:%Y-%m-%dT%H:%M:%S}",
                "duracao_min": NOITE_H * 60,
                "historico": historico,
                "eventos": [{"em_min": m, "nivel": horas[m // 60]}
                            for m in range(0, NOITE_H * 60, PASSO_MIN)],
                "envelope": ENVELOPE_LIVRE,
            }
            (destino / f"{nome}.json").write_text(
                json.dumps(cen, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
            gerados.append({"cenario": nome, "sensor": int(sensor), "grupo": grupo, "tipo": tipo,
                            "inicio": str(inicio), "media_noite": round(sum(horas) / len(horas), 4)})
    return gerados


def _serie_zurique():
    """Serie de Zurique com a preparacao do modelo principal (item 69)."""
    from modelo.treinar_zurique import CORTE, preparar

    d, _ = preparar()
    return d[["ponto", "ts", "nivel"]], CORTE


def zurique(destino: Path) -> list[dict]:
    """Parte 1 do PROTOCOLO.md com noites de Zurique (PROTOCOLO_MODELO_ZURIQUE.md,
    Parte C): mesma semente, mesma regra de sorteio, teste = 2019, historico de
    672 blocos de 15 min e volume de 5 min = valor do bloco corrente."""
    d, corte = _serie_zurique()
    teste = d[d.ts >= corte]
    noturno = teste[(teste.ts.dt.hour >= 18) | (teste.ts.dt.hour < 6)]
    media = noturno.groupby("ponto").nivel.mean().sort_values()
    metade = len(media) // 2
    calmos, movimentados = list(media.index[:metade]), list(media.index[metade:])
    rng = random.Random(SEMENTE)
    sensores = [("movimentado", s) for s in rng.sample(movimentados, 2)] + \
               [("calmo", s) for s in rng.sample(calmos, 2)]

    gerados = []
    for grupo, sensor in sensores:
        grade = d[d.ponto == sensor].set_index("ts").nivel.sort_index()
        dias = pd.date_range(corte.normalize() + pd.Timedelta(days=8), teste.ts.max().normalize()
                             - pd.Timedelta(days=1), freq="D")
        for tipo, filtro in (("dia_util", lambda x: x.weekday() < 4),
                             ("fim_de_semana", lambda x: x.weekday() == 5)):
            candidatos = [x for x in dias if filtro(x)]
            rng.shuffle(candidatos)
            for dia in candidatos:
                inicio = dia + pd.Timedelta(hours=18)
                blocos = pd.date_range(inicio - pd.Timedelta(hours=HORAS_HISTORICO),
                                       inicio + pd.Timedelta(hours=NOITE_H) - pd.Timedelta(minutes=15),
                                       freq="15min")
                v = grade.reindex(blocos)
                if not v.isna().any():
                    break
            else:
                raise SystemExit(f"sem noite completa para o ponto {sensor} ({tipo})")
            v = [round(float(x), 4) for x in v]
            historico, noite = v[:4 * HORAS_HISTORICO], v[4 * HORAS_HISTORICO:]
            nome = f"zurique_{grupo}_{sensor}_{tipo}"
            cen = {
                "nome": nome,
                "descricao": (f"Noite real do ponto {sensor} de Zurique ({grupo}, {tipo}), "
                              f"{inicio:%Y-%m-%d} 18h-06h, no periodo de teste do modelo (2019)."),
                "origem": (f"Open Data Zurich, 15 min, preparada como no modelo principal; sorteio com "
                           f"semente {SEMENTE} (DIVERGENCIAS 57 e 69). Volume = valor do bloco de 15 min "
                           "corrente a cada 5 min."),
                "inicio_local": f"{inicio:%Y-%m-%dT%H:%M:%S}",
                "duracao_min": NOITE_H * 60,
                "historico": historico,
                "eventos": [{"em_min": m, "nivel": noite[m // 15]}
                            for m in range(0, NOITE_H * 60, PASSO_MIN)],
                "envelope": ENVELOPE_LIVRE,
            }
            (destino / f"{nome}.json").write_text(
                json.dumps(cen, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
            gerados.append({"cenario": nome, "sensor": int(sensor), "grupo": grupo, "tipo": tipo,
                            "inicio": str(inicio), "media_noite": round(sum(noite) / len(noite), 4)})
    return gerados


def camera(destino: Path) -> list[dict]:
    """Pares controle x falha. O nivel real segue o perfil sintetico da suite."""
    pares = [
        # nome, inicio (terca), duracao, falha (de, ate) em minutos
        ("inicio_da_noite", datetime(2026, 9, 22, 18, 0), 240, (30, 150)),
        ("madrugada", datetime(2026, 9, 23, 1, 0), 240, (30, 150)),
    ]
    gerados = []
    for rotulo, inicio, dur, (de, ate) in pares:
        real = [perfil_horario(inicio + timedelta(minutes=m)) for m in range(0, dur, PASSO_MIN)]
        for caso in ("controle", "falha"):
            eventos = []
            for i, m in enumerate(range(0, dur, PASSO_MIN)):
                falhou = caso == "falha" and de <= m < ate
                eventos.append({"em_min": m, "nivel": 0.0 if falhou else real[i],
                                "nivel_real": real[i]})
            nome = f"camera_{rotulo}_{caso}"
            cen = {
                "nome": nome,
                "descricao": (f"{'Camera contando zero' if caso == 'falha' else 'Camera correta'} "
                              f"entre os minutos {de} e {ate}; movimento real pelo perfil da suite "
                              f"({rotulo.replace('_', ' ')})."),
                "origem": "Avaliacao da previsao como segunda evidencia (DIVERGENCIAS 57).",
                "inicio_local": f"{inicio:%Y-%m-%dT%H:%M:%S}",
                "duracao_min": dur,
                "falha_min": [de, ate],
                "eventos": eventos,
                "envelope": [{"de_min": 0, "ate_min": dur, "min": 0.5, "max": 1.0,
                              "nota": "comparacao controle x falha; aderencia nao avaliada"}],
            }
            (destino / f"{nome}.json").write_text(
                json.dumps(cen, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
            gerados.append({"cenario": nome, "falha_min": [de, ate]})
    return gerados


def main() -> None:
    # Desde o item 69, as noites reais sao de Zurique; as de Melbourne ficam
    # no historico do repositorio (gerar com melbourne()).
    for pasta in (NOITES, "camera"):
        (AQUI / pasta).mkdir(exist_ok=True)
        for velho in (AQUI / pasta).glob("*.json"):
            velho.unlink()
    resumo = {"semente": SEMENTE, NOITES: zurique(AQUI / NOITES),
              "camera": camera(AQUI / "camera")}
    (AQUI / "sorteio.json").write_text(json.dumps(resumo, indent=2, ensure_ascii=False) + "\n",
                                       encoding="utf-8")
    print(json.dumps(resumo, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
