"""Aderencia ao envelope dos tres regimes (3.11): adaptativo, fluxo pleno
constante e atenuacao por horario fixo, sobre a suite de cenarios.

    python -m cenarios.aderencia_regimes

Le cenarios/resultados/suite_antecipado.json (gerado com --serie) e grava
cenarios/resultados/suite_aderencia_regimes.json. A aderencia e a fracao dos
ciclos em que o nivel do regime fica dentro do envelope esperado do cenario.
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta

import psycopg

from cenarios.executar import HORA_FIM_ATENUACAO, HORA_INICIO_ATENUACAO, RESULTADOS, carregar_suite
from decisao import ciclo, config
from decisao.energia import trajetoria_horario_fixo

EPS = 1e-9


def main() -> None:
    with psycopg.connect(config.DATABASE_URL, connect_timeout=5) as conn:
        piso = float(ciclo.criterio(conn, "P3").piso)
    d = json.loads((RESULTADOS / "suite_antecipado.json").read_text(encoding="utf-8"))
    rel = {r["cenario"]: r for r in d["relatorios"]}
    total = {"adaptativo": 0, "pleno_constante": 0, "horario_fixo": 0, "ciclos": 0}
    por = {}
    for c in carregar_suite(None):
        r = rel[c.nome]
        if "serie" not in r:
            raise SystemExit("suite sem serie: rode o executor com --serie")
        inicio = datetime.fromisoformat(r["inicio"])
        fixo = trajetoria_horario_fixo(
            inicio, inicio + timedelta(seconds=config.PERIODO_S * len(r["serie"])), piso,
            hora_inicio_atenuacao=HORA_INICIO_ATENUACAO, hora_fim_atenuacao=HORA_FIM_ATENUACAO,
            passo_s=config.PERIODO_S, fuso=config.FUSO,
        )
        n = {"adaptativo": 0, "pleno_constante": 0, "horario_fixo": 0, "ciclos": 0}
        for x, (_, _, nf) in zip(r["serie"], fixo):
            f = c.faixa(x["minuto"])
            if f is None:
                continue
            n["ciclos"] += 1
            for nome, nivel in (("adaptativo", x["emitido"]), ("pleno_constante", 1.0), ("horario_fixo", nf)):
                n[nome] += f["min"] - EPS <= nivel <= f["max"] + EPS
        por[c.nome] = {k: round(n[k] / n["ciclos"], 4) for k in ("adaptativo", "pleno_constante", "horario_fixo")}
        por[c.nome]["ciclos"] = n["ciclos"]
        for k in total:
            total[k] += n[k]
    saida = {"suite": {k: round(total[k] / total["ciclos"], 4) for k in ("adaptativo", "pleno_constante", "horario_fixo")},
             "ciclos": total["ciclos"], "por_cenario": por}
    (RESULTADOS / "suite_aderencia_regimes.json").write_text(
        json.dumps(saida, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(saida, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
