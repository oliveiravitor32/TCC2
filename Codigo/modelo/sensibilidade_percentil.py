"""Sensibilidade da regua ao percentil (PROTOCOLO_SENSIBILIDADE_P99.md, item 72).

    python -m modelo.sensibilidade_percentil

Teste a posteriori: mede se trocar o percentil 99 por 95, 99,5 ou 99,9 muda a
faixa de movimento que as regras leem. Saida:
modelo/resultados/sensibilidade_percentil.json.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone

import numpy as np
import pandas as pd

from modelo.treinar_zurique import AQUI, CORTE, preparar

PERCENTIS = (0.95, 0.99, 0.995, 0.999)
REF = 0.99
BLOCOS_28D, MINIMO = 2688, 672
SAIDA = AQUI / "resultados" / "sensibilidade_percentil.json"


def noturno(ts: pd.Series) -> pd.Series:
    return (ts.dt.hour >= 18) | (ts.dt.hour < 6)


def main() -> None:
    d, _ = preparar()
    d = d[["ponto", "ts", "ped"]].dropna(subset=["ped"]).reset_index(drop=True)
    treino, teste = d[d.ts < CORTE], d[d.ts >= CORTE].copy()
    noite = noturno(teste.ts).to_numpy()

    # 1 e 2: regua do treino, tercis recalculados, faixa do teste.
    faixa, tercis, saturacao = {}, {}, {}
    for p in PERCENTIS:
        cheio = treino.groupby("ponto").ped.quantile(p)
        nt = (treino.ped / treino.ponto.map(cheio)).clip(0, 1)
        t = [float(nt.quantile(q)) for q in (1 / 3, 2 / 3)]
        nv = (teste.ped / teste.ponto.map(cheio)).clip(0, 1).to_numpy()
        tercis[p], faixa[p] = t, np.digitize(nv, t)
        saturacao[p] = float((nv >= 1).mean())

    # 3 e 4: regua de 28 dias como o servico a calcula (rotina diaria, item 71).
    variacao, faixa_op = {}, {}
    teste["dia"] = teste.ts.dt.normalize()
    for p in PERCENTIS:
        reguas, var = [], []
        for pt, sub in d.groupby("ponto"):
            s = sub.set_index("ts").ped
            r = s.rolling("28D", closed="left", min_periods=MINIMO).quantile(p)
            diaria = r[r.index.normalize() == r.index].loc[lambda x: x.index >= CORTE]
            diaria = diaria[diaria > 0]
            var.append((diaria.pct_change().abs()).dropna())
            reguas.append(pd.DataFrame({"ponto": pt, "dia": diaria.index, "regua": diaria.to_numpy()}))
        v = pd.concat(var)
        variacao[p] = {"mediana": float(v.median()), "p95": float(v.quantile(0.95)),
                       "dias_ponto": int(len(v))}
        rg = pd.concat(reguas)
        m = teste.merge(rg, on=["ponto", "dia"], how="left")
        nv = (m.ped / m.regua).clip(0, 1).to_numpy()
        f = np.where(np.isnan(nv), -1, np.digitize(np.nan_to_num(nv), tercis[p]))
        faixa_op[p] = f

    validos_op = (faixa_op[REF] >= 0) & noite
    res = {"gerado_em": datetime.now(timezone.utc).isoformat(),
           "protocolo": "modelo/PROTOCOLO_SENSIBILIDADE_P99.md",
           "blocos_teste": int(len(teste)), "blocos_teste_noite": int(noite.sum()),
           "por_percentil": {}}
    for p in PERCENTIS:
        ok_op = validos_op & (faixa_op[p] >= 0)
        res["por_percentil"][str(p)] = {
            "blocos_acima_em_28_dias": round(BLOCOS_28D * (1 - p), 1),
            "tercis": [round(x, 4) for x in tercis[p]],
            "concordancia_faixa_treino": round(float((faixa[p] == faixa[REF]).mean()), 4),
            "concordancia_faixa_treino_noite": round(float((faixa[p] == faixa[REF])[noite].mean()), 4),
            "saturacao_teste": round(saturacao[p], 4),
            "variacao_diaria_regua": {k: round(x, 4) if isinstance(x, float) else x
                                      for k, x in variacao[p].items()},
            "concordancia_faixa_operacao_noite": round(float((faixa_op[p] == faixa_op[REF])[ok_op].mean()), 4),
        }
    pp = res["por_percentil"]
    menor = min(pp[str(p)][k] for p in (0.95, 0.995)
                for k in ("concordancia_faixa_treino_noite", "concordancia_faixa_operacao_noite"))
    res["leitura"] = {"menor_concordancia_noturna_p95_p995": menor,
                      "regra": ">= 0,90 -> pouco sensivel",
                      "conclusao": "pouco sensivel" if menor >= 0.90 else "sensivel"}
    SAIDA.write_text(json.dumps(res, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(res, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
