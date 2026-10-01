"""Conferencias POSTERIORES ao protocolo de Zurique (DIVERGENCIAS 60).

    python -m modelo.conferencia_zurique

Nao fazem parte do criterio fixado: servem para verificar se o ganho medido
se sustenta. Mesmos dados, particao, modelo e semente do experimento.
  1. resultado por ponto (em quantos o XGBoost supera a melhor referencia);
  2. duas referencias simples mais espertas, sem treino:
       semana_corrigida = semana anterior + (ultima hora de hoje - ultima hora
                          de sete dias atras), limitada a [0, 1];
       mistura          = media entre a semana anterior e a ultima hora;
  3. intervalo de 95 % da diferenca de acerto da faixa, reamostrando DIAS
     (2000 reamostragens, semente 60).
Saida: modelo/resultados/conferencia_zurique.json
"""

from __future__ import annotations

import json

import numpy as np
import xgboost as xgb

from modelo.experimento_zurique import CORTE, RES, SAIDA, carregar, faixa, medir, montar

SIMPLES = ["persistencia", "media_sazonal", "semana_anterior", "semana_corrigida", "mistura"]


def main() -> None:
    bruto = carregar()
    resultado = {}
    for nome, cfg in RES.items():
        n = cfg["por_hora"]
        d, colunas = montar(bruto, cfg)
        d["pers_semana"] = d.groupby("ponto")["persistencia"].shift(168 * n)
        d = d.dropna(subset=["pers_semana"])
        d["semana_corrigida"] = (d.semana_anterior + d.persistencia - d.pers_semana).clip(0, 1)
        d["mistura"] = (d.semana_anterior + d.persistencia) / 2
        treino, teste = d[d.ts < CORTE], d[d.ts >= CORTE].copy()
        corte_val = treino.ts.quantile(0.9)
        tr, val = treino[treino.ts < corte_val], treino[treino.ts >= corte_val]
        f1, f2 = (float(treino.nivel.quantile(q)) for q in (1 / 3, 2 / 3))
        modelo = xgb.XGBRegressor(
            n_estimators=2000, learning_rate=0.05, max_depth=8, subsample=0.8,
            colsample_bytree=0.8, min_child_weight=5, objective="reg:squarederror",
            tree_method="hist", early_stopping_rounds=50, eval_metric="mae",
            n_jobs=0, random_state=37,
        )
        modelo.fit(tr[colunas], tr.alvo, eval_set=[(val[colunas], val.alvo)], verbose=False)
        teste["xgboost"] = modelo.predict(teste[colunas]).clip(0, 1)
        chave = ["ponto", "dia_semana", "hora", "quarto"]
        teste = teste.merge(treino.groupby(chave).alvo.mean().rename("media_sazonal"), on=chave, how="left")
        teste["media_sazonal"] = teste.media_sazonal.fillna(teste.persistencia)
        noite = teste[(teste.hora >= 18) | (teste.hora < 6)].copy()

        geral = medir(noite, ["xgboost"] + SIMPLES, f1, f2)

        por_ponto = {}
        ganha_faixa = ganha_f1 = 0
        for ponto, t in noite.groupby("ponto"):
            m = medir(t, ["xgboost"] + SIMPLES, f1, f2)
            melhor_faixa = max(m[s]["acerto_da_faixa"] for s in SIMPLES)
            melhor_f1 = max(m[s]["vai_subir"]["f1"] for s in SIMPLES)
            por_ponto[int(ponto)] = {
                "casos": m["casos"], "fracao_que_sobe": m["fracao_que_sobe"],
                "faixa_xgboost": m["xgboost"]["acerto_da_faixa"], "faixa_melhor_simples": melhor_faixa,
                "f1_xgboost": m["xgboost"]["vai_subir"]["f1"], "f1_melhor_simples": melhor_f1,
            }
            ganha_faixa += m["xgboost"]["acerto_da_faixa"] > melhor_faixa
            ganha_f1 += m["xgboost"]["vai_subir"]["f1"] > melhor_f1

        # Intervalo da diferenca de acerto da faixa, reamostrando dias inteiros.
        real = faixa(noite.alvo.to_numpy(), f1, f2)
        dia = noite.ts.dt.normalize()
        codigos, _ = np.unique(dia.to_numpy(), return_inverse=True), None
        idx = np.unique(dia.to_numpy(), return_inverse=True)[1]
        ndias = idx.max() + 1
        cont = np.bincount(idx, minlength=ndias).astype(float)
        ok_x = np.bincount(idx, weights=faixa(noite.xgboost.to_numpy(), f1, f2) == real, minlength=ndias)
        rng = np.random.default_rng(60)
        intervalos = {}
        for s in SIMPLES:
            ok_s = np.bincount(idx, weights=faixa(noite[s].to_numpy(), f1, f2) == real, minlength=ndias)
            dif = []
            for _ in range(2000):
                a = rng.integers(0, ndias, ndias)
                dif.append((ok_x[a].sum() - ok_s[a].sum()) / cont[a].sum())
            intervalos[s] = [round(float(np.percentile(dif, q)) * 100, 2) for q in (2.5, 97.5)]

        resultado[nome] = {"noite": geral, "pontos": len(por_ponto),
                           "pontos_em_que_xgboost_ganha_na_faixa": int(ganha_faixa),
                           "pontos_em_que_xgboost_ganha_no_f1": int(ganha_f1),
                           "por_ponto": por_ponto,
                           "ic95_diferenca_faixa_pp": intervalos}
        print(nome, json.dumps({k: v for k, v in resultado[nome].items() if k != "noite"}, indent=1))
        for p in ["xgboost"] + SIMPLES:
            v = geral[p]
            print(f"  {p:17s} mae {v['mae']:.4f} faixa {v['acerto_da_faixa']:.4f} f1 {v['vai_subir']['f1']:.3f}")
    (SAIDA.parent / "conferencia_zurique.json").write_text(
        json.dumps(resultado, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
