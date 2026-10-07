"""XGBoost contra regressao linear e Random Forest (PROTOCOLO_COMPARACAO_MODELOS.md).

    python -m modelo.comparar_modelos

Mesmos dados, particao e atributos de modelo/treinar.py; o XGBoost e o modelo
salvo que o sistema usa. Saida: modelo/resultados/comparacao_modelos.json.
"""

from __future__ import annotations

import json
import time
from datetime import datetime, timezone

import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression

from modelo.treinar import (
    FRACAO_TESTE, MODELO, RESULTADOS, carregar, erros, media_sazonal, montar_atributos,
    pontos_utilizaveis,
)

TERCIS = (0.1038, 0.4053)  # os do sistema (3.7)
LIMIAR_RELATIVO = 0.02


def faixa(x: np.ndarray) -> np.ndarray:
    return np.digitize(np.asarray(x), TERCIS)


def noite(ts: pd.Series) -> np.ndarray:
    h = ts.dt.hour.to_numpy()
    return (h >= 18) | (h < 6)


def para_linear(df: pd.DataFrame, colunas: list[str]) -> pd.DataFrame:
    x = df[colunas].copy()
    x = pd.get_dummies(x, columns=["hora", "dia_semana"], drop_first=True, dtype=float)
    return x


def main() -> None:
    bruto, meta = carregar()
    pontos = pontos_utilizaveis(bruto)
    d, _ = montar_atributos(bruto[bruto.location_id.isin(pontos)])
    colunas = [c for c in d.columns if c.startswith("atraso_")] + [
        "media_3h", "media_24h", "hora", "hora_sen", "hora_cos",
        "dia_semana", "fim_de_semana", "feriado",
    ]
    corte = d.ts.quantile(1 - FRACAO_TESTE)
    treino, teste = d[d.ts < corte], d[d.ts >= corte].reset_index(drop=True)
    print(f"{len(pontos)} pontos | treino {len(treino):,} | teste {len(teste):,} | corte {corte}")

    previsoes: dict[str, np.ndarray] = {}
    tempos: dict[str, dict] = {}

    m = xgb.XGBRegressor()
    m.load_model(MODELO)
    t0 = time.perf_counter()
    previsoes["xgboost"] = m.predict(teste[colunas]).clip(0, 1)
    tempos["xgboost"] = {"treino_s": None, "previsao_s": round(time.perf_counter() - t0, 2),
                         "obs": "modelo salvo; treino original nao cronometrado aqui"}

    xtr, xte = para_linear(treino, colunas), para_linear(teste, colunas)
    xte = xte.reindex(columns=xtr.columns, fill_value=0.0)
    lin = LinearRegression()
    t0 = time.perf_counter(); lin.fit(xtr, treino.alvo); t1 = time.perf_counter()
    previsoes["linear"] = lin.predict(xte).clip(0, 1)
    tempos["linear"] = {"treino_s": round(t1 - t0, 2), "previsao_s": round(time.perf_counter() - t1, 2)}
    print("linear ok")

    rf = RandomForestRegressor(n_estimators=200, min_samples_leaf=5, max_features=0.5,
                               max_samples=0.3, random_state=37, n_jobs=-1)
    t0 = time.perf_counter(); rf.fit(treino[colunas], treino.alvo); t1 = time.perf_counter()
    previsoes["random_forest"] = rf.predict(teste[colunas]).clip(0, 1)
    tempos["random_forest"] = {"treino_s": round(t1 - t0, 2), "previsao_s": round(time.perf_counter() - t1, 2)}
    print("random forest ok")

    # Treino do XGBoost cronometrado com os mesmos parametros (so para o tempo).
    corte_val = treino.ts.quantile(0.9)
    tr, val = treino[treino.ts < corte_val], treino[treino.ts >= corte_val]
    x2 = xgb.XGBRegressor(n_estimators=2000, learning_rate=0.05, max_depth=8, subsample=0.8,
                          colsample_bytree=0.8, min_child_weight=5, objective="reg:squarederror",
                          tree_method="hist", early_stopping_rounds=50, eval_metric="mae",
                          n_jobs=0, random_state=37)
    t0 = time.perf_counter(); x2.fit(tr[colunas], tr.alvo, eval_set=[(val[colunas], val.alvo)], verbose=False)
    tempos["xgboost"]["treino_s"] = round(time.perf_counter() - t0, 2)
    tempos["xgboost"]["obs"] = "treino refeito so para cronometrar; previsoes do modelo salvo"

    previsoes["persistencia"] = teste.nivel.to_numpy()
    previsoes["media_sazonal"] = media_sazonal(treino, teste)

    y = teste.alvo.to_numpy()
    n = noite(teste.ts)
    resultado = {}
    for nome, p in previsoes.items():
        resultado[nome] = {
            "todas": erros(y, p),
            "noite": erros(y[n], p[n]),
            "acerto_faixa_noite": float((faixa(p[n]) == faixa(y[n])).mean()),
        }

    por_ponto = {}
    for nome in ("linear", "random_forest", "persistencia", "media_sazonal"):
        melhor = 0
        for _pt, g in teste.groupby("location_id").groups.items():
            idx = np.asarray(g)
            mx = np.abs(previsoes["xgboost"][idx] - y[idx]).mean()
            mo = np.abs(previsoes[nome][idx] - y[idx]).mean()
            melhor += int(mx < mo)
        por_ponto[nome] = melhor

    leitura = {}
    mae_x = resultado["xgboost"]["todas"]["mae"]
    for nome in ("linear", "random_forest"):
        mae_o = resultado[nome]["todas"]["mae"]
        rel = (mae_o - mae_x) / mae_o  # >0: XGBoost menor
        maioria = por_ponto[nome] > len(pontos) / 2
        minoria = por_ponto[nome] < len(pontos) / 2
        if rel >= LIMIAR_RELATIVO and maioria:
            leitura[nome] = "XGBoost superior"
        elif rel <= -LIMIAR_RELATIVO and minoria:
            leitura[nome] = "XGBoost inferior"
        elif abs(rel) < LIMIAR_RELATIVO:
            leitura[nome] = "equivalentes em erro"
        else:
            leitura[nome] = "sem conclusao pela regra (MAE e pontos discordam)"
        leitura[nome] += f" (MAE {rel:+.1%} a favor do XGBoost; melhor em {por_ponto[nome]}/{len(pontos)} pontos)"

    for nome, r in resultado.items():
        print(f"  {nome:14s} MAE {r['todas']['mae']:.4f} RMSE {r['todas']['rmse']:.4f} | noite MAE "
              f"{r['noite']['mae']:.4f} faixa {r['acerto_faixa_noite']:.3f}")
    print("pontos em que o XGBoost tem MAE menor:", por_ponto)
    print("tempos:", tempos)
    for k, v in leitura.items():
        print(f"LEITURA {k}: {v}")

    saida = {"gerado_em": datetime.now(timezone.utc).isoformat(), "protocolo": "PROTOCOLO_COMPARACAO_MODELOS.md",
             "serie_sha256": meta["sha256"], "pontos": len(pontos), "linhas_treino": len(treino),
             "linhas_teste": len(teste), "corte": str(corte), "tercis": TERCIS, "metricas": resultado,
             "xgboost_melhor_por_ponto": por_ponto, "tempos": tempos, "leitura": leitura}
    (RESULTADOS / "comparacao_modelos.json").write_text(
        json.dumps(saida, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"registro: {RESULTADOS / 'comparacao_modelos.json'}")


if __name__ == "__main__":
    main()
