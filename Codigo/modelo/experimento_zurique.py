"""Previsao com dados de 15 min de Zurique (PROTOCOLO_ZURIQUE.md, DIVERGENCIAS 60).

    python -m modelo.experimento_zurique

Experimento separado: nao altera o modelo nem os tercis do sistema.
Saida: modelo/resultados/experimento_zurique.json
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import xgboost as xgb

AQUI = Path(__file__).resolve().parent
ARQ = AQUI / "dados" / "zurique_pedestres_15min.parquet"
SAIDA = AQUI / "resultados" / "experimento_zurique.json"

INICIO, FIM = "2016-01-01", "2020-01-01"
CORTE = pd.Timestamp("2019-01-01")
DIAS_MIN, COBERTURA_MIN = 730, 0.95
PERCENTIL_CHEIO = 0.99
RES = {
    "15min": {"freq": "15min", "por_hora": 4, "atrasos": (1, 2, 3, 4, 8, 96, 672),
              "medias": {"media_1h": 4, "media_3h": 12, "media_24h": 96}},
    "1h": {"freq": "h", "por_hora": 1, "atrasos": (1, 2, 3, 24, 168),
           "medias": {"media_3h": 3, "media_24h": 24}},
}


def carregar() -> pd.DataFrame:
    d = pd.read_parquet(ARQ, columns=["FK_STANDORT", "DATUM", "FUSS_IN", "FUSS_OUT"])
    d["ped"] = d[["FUSS_IN", "FUSS_OUT"]].sum(axis=1, min_count=1)
    d = d.dropna(subset=["ped"])
    d["ts"] = pd.to_datetime(d.DATUM)
    d = d[(d.ts >= INICIO) & (d.ts < FIM)]
    d = d.groupby(["FK_STANDORT", "ts"], as_index=False).ped.sum().astype({"ped": float})
    g = d.groupby("FK_STANDORT").ts.agg(["size", "min", "max"])
    cob = g["size"] / ((g["max"] - g["min"]).dt.total_seconds() / 900 + 1)
    ok = g.index[((g["max"] - g["min"]).dt.days >= DIAS_MIN) & (cob >= COBERTURA_MIN)]
    return d[d.FK_STANDORT.isin(ok)].rename(columns={"FK_STANDORT": "ponto"})


def montar(d: pd.DataFrame, cfg: dict) -> tuple[pd.DataFrame, list[str]]:
    n = cfg["por_hora"]
    # Grade completa por ponto; hora so vale com os 4 intervalos presentes.
    s = d.set_index("ts").groupby("ponto").ped.resample("15min").sum(min_count=1)
    if n == 1:
        s = s.reset_index(level=0).groupby("ponto").ped.resample("h").agg(
            lambda x: x.sum() if x.notna().sum() == 4 else np.nan)
    d = s.reset_index().sort_values(["ponto", "ts"])
    cheio = d[d.ts < CORTE].groupby("ponto").ped.quantile(PERCENTIL_CHEIO).rename("cheio")
    d = d.merge(cheio, on="ponto")
    d["nivel"] = (d.ped / d.cheio).clip(0, 1)

    g = d.groupby("ponto")["nivel"]
    for k in cfg["atrasos"]:
        d[f"atraso_{k}"] = g.shift(k)
    for nome, jan in cfg["medias"].items():
        d[nome] = g.shift(1).rolling(jan).mean().reset_index(level=0, drop=True)
    # Alvo: nivel medio dos proximos 60 minutos.
    d["alvo"] = sum(g.shift(-k) for k in range(1, n + 1)) / n
    # Persistencia: a ultima hora observada (inclui o intervalo corrente).
    d["persistencia"] = sum(g.shift(k) for k in range(0, n)) / n
    d["semana_anterior"] = d.groupby("ponto")["alvo"].shift(168 * n)

    d["hora"] = d.ts.dt.hour
    d["quarto"] = d.ts.dt.minute // 15
    frac = (d.hora * 4 + d.quarto) / 96
    d["dia_sen"], d["dia_cos"] = np.sin(2 * np.pi * frac), np.cos(2 * np.pi * frac)
    d["dia_semana"] = d.ts.dt.dayofweek
    d["fim_de_semana"] = (d.dia_semana >= 5).astype(int)
    colunas = [f"atraso_{k}" for k in cfg["atrasos"]] + list(cfg["medias"]) + [
        "hora", "quarto", "dia_sen", "dia_cos", "dia_semana", "fim_de_semana"]
    d = d.dropna(subset=colunas + ["alvo", "nivel", "persistencia", "semana_anterior"])
    return d, colunas


def faixa(v, f1, f2):
    return np.digitize(v, [f1, f2])


def medir(t: pd.DataFrame, previsores: list[str], f1: float, f2: float) -> dict:
    y = t.alvo.to_numpy()
    baixo = t.nivel.to_numpy() < f1
    real_sobe = y[baixo] >= f1
    saida = {"casos": int(len(t)), "casos_nivel_baixo": int(baixo.sum()),
             "fracao_que_sobe": round(float(real_sobe.mean()), 4) if baixo.any() else None}
    for nome in previsores:
        p = t[nome].to_numpy()
        e = p - y
        diz = p[baixo] >= f1
        vp = int((diz & real_sobe).sum())
        prec = vp / diz.sum() if diz.sum() else 0.0
        rev = vp / real_sobe.sum() if real_sobe.sum() else 0.0
        saida[nome] = {
            "mae": round(float(np.abs(e).mean()), 4),
            "rmse": round(float(np.sqrt((e ** 2).mean())), 4),
            "acerto_da_faixa": round(float((faixa(p, f1, f2) == faixa(y, f1, f2)).mean()), 4),
            "vai_subir": {"precisao": round(prec, 4), "revocacao": round(rev, 4),
                          "f1": round(2 * prec * rev / (prec + rev), 4) if prec + rev else 0.0},
        }
    return saida


def main() -> None:
    bruto = carregar()
    resultado = {"pontos": sorted(int(x) for x in bruto.ponto.unique()),
                 "janela": [INICIO, FIM], "corte_treino_teste": str(CORTE)}
    print(f"{len(resultado['pontos'])} pontos: {resultado['pontos']}")
    for nome, cfg in RES.items():
        d, colunas = montar(bruto, cfg)
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
        saz = treino.groupby(chave).alvo.mean().rename("media_sazonal")
        teste = teste.merge(saz, on=chave, how="left")
        teste["media_sazonal"] = teste.media_sazonal.fillna(teste.persistencia)
        previsores = ["xgboost", "persistencia", "media_sazonal", "semana_anterior"]
        noite = teste[(teste.hora >= 18) | (teste.hora < 6)]
        resultado[nome] = {
            "linhas_treino": int(len(treino)), "linhas_teste": int(len(teste)),
            "pontos_no_teste": int(teste.ponto.nunique()),
            "tercis": [round(f1, 4), round(f2, 4)], "arvores": int(modelo.best_iteration + 1),
            "noite": medir(noite, previsores, f1, f2),
            "todas_as_horas": medir(teste, previsores, f1, f2),
        }
        print(nome, json.dumps(resultado[nome]["noite"], indent=1))
    SAIDA.parent.mkdir(exist_ok=True)
    SAIDA.write_text(json.dumps(resultado, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
