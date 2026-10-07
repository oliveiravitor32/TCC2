"""Noites reais de Zurique em 15 min (PROTOCOLO_SUAVIDADE.md, DIVERGENCIAS 61).

    python -m cenarios.avaliacao_ia.gerar_suavidade
"""

from __future__ import annotations

import json
import random
from pathlib import Path

import pandas as pd

from cenarios.executar import HORAS_HISTORICO
from modelo.treinar_zurique import CORTE, preparar

AQUI = Path(__file__).resolve().parent
SEMENTE = 61
NOITE_H = 12
PASSO_MIN = 5


def main() -> None:
    destino = AQUI / "suavidade"
    destino.mkdir(exist_ok=True)
    for velho in destino.glob("*.json"):
        velho.unlink()
    # Item 69: a mesma preparacao do modelo principal (horario de verao,
    # sensor travado, p99 so no treino) e historico em blocos de 15 min.
    d, _ = preparar()
    teste = d[d.ts >= CORTE]
    noturno = teste[(teste.ts.dt.hour >= 18) | (teste.ts.dt.hour < 6)]
    media = noturno.groupby("ponto").nivel.mean().sort_values()
    metade = len(media) // 2
    calmos, movimentados = list(media.index[:metade]), list(media.index[metade:])
    rng = random.Random(SEMENTE)
    pontos = [("movimentado", p) for p in rng.sample(movimentados, 2)] + \
             [("calmo", p) for p in rng.sample(calmos, 2)]

    gerados = []
    for grupo, ponto in pontos:
        grade = d[d.ponto == ponto].set_index("ts").nivel.sort_index()
        dias = pd.date_range(CORTE + pd.Timedelta(days=8), teste.ts.max().normalize() - pd.Timedelta(days=1),
                             freq="D")
        for tipo, filtro in (("dia_util", lambda x: x.weekday() < 4), ("fim_de_semana", lambda x: x.weekday() == 5)):
            candidatos = [x for x in dias if filtro(x)]
            rng.shuffle(candidatos)
            for dia in candidatos:
                inicio = dia + pd.Timedelta(hours=18)
                quartos = pd.date_range(inicio - pd.Timedelta(hours=HORAS_HISTORICO),
                                        inicio + pd.Timedelta(hours=NOITE_H) - pd.Timedelta(minutes=15),
                                        freq="15min")
                v = grade.reindex(quartos)
                if not v.isna().any():
                    break
            else:
                raise SystemExit(f"sem noite completa para o ponto {ponto} ({tipo})")
            hist = v[v.index < inicio]
            noite = v[v.index >= inicio]
            nome = f"zurique_{grupo}_{ponto}_{tipo}"
            cen = {
                "nome": nome,
                "descricao": (f"Noite real do ponto {ponto} de Zurique ({grupo}, {tipo}), "
                              f"{inicio:%Y-%m-%d} 18h-06h, em valores de 15 min."),
                "origem": (f"Open Data Zürich, 15 min; sorteio com semente {SEMENTE} (DIVERGENCIAS 61). "
                           "Volume de 5 min = valor do intervalo de 15 min corrente."),
                "inicio_local": f"{inicio:%Y-%m-%dT%H:%M:%S}",
                "duracao_min": NOITE_H * 60,
                "historico": [round(float(x), 4) for x in hist],
                "eventos": [{"em_min": m, "nivel": round(float(noite.iloc[m // 15]), 4)}
                            for m in range(0, NOITE_H * 60, PASSO_MIN)],
                "envelope": [{"de_min": 0, "ate_min": NOITE_H * 60, "min": 0.5, "max": 1.0,
                              "nota": "dado real: sem envelope a priori; a aderencia nao e avaliada"}],
            }
            (destino / f"{nome}.json").write_text(json.dumps(cen, indent=2, ensure_ascii=False) + "\n",
                                                  encoding="utf-8")
            gerados.append({"cenario": nome, "ponto": int(ponto), "grupo": grupo, "tipo": tipo,
                            "inicio": str(inicio), "media_noite": round(float(noite.mean()), 4)})
    (AQUI / "sorteio_suavidade.json").write_text(
        json.dumps({"semente": SEMENTE, "noites": gerados}, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(gerados, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
