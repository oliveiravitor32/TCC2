"""Modelo principal de previsao em 15 min, serie de Zurique (PROTOCOLO_MODELO_ZURIQUE.md).

    python -m modelo.treinar_zurique [--registrar]

Parte A do protocolo: preparacao com checklist contado, feriados do cantao,
p99 e tercis so no treino, XGBoost com os hiperparametros de treinar.py,
comparacoes e leitura. Saidas: modelo/modelo_previsao_zurique.json e
modelo/resultados/metricas_zurique.json.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import time
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression

from modelo.treinar import _pascoa

AQUI = Path(__file__).resolve().parent
ARQ = AQUI / "dados" / "zurique_pedestres_15min.parquet"
META = AQUI / "dados" / "zurique_extracao.json"
MODELO = AQUI / "modelo_previsao_zurique.json"
SAIDA = AQUI / "resultados" / "metricas_zurique.json"
ROTULO = "xgboost-zurique-15min-v1"

INICIO, FIM = "2016-01-01", "2020-01-01"
CORTE = pd.Timestamp("2019-01-01")
DIAS_MIN, COBERTURA_MIN = 730, 0.95
PERCENTIL_CHEIO = 0.99
ATRASOS = (1, 2, 3, 4, 8, 96, 672)
MEDIAS = {"media_1h": 4, "media_3h": 12, "media_24h": 96}
POR_HORA = 4
TRAVADO_INTERVALOS = 32  # 8 h
LIMIAR_RELATIVO = 0.02
COLUNAS = [f"atraso_{k}" for k in ATRASOS] + list(MEDIAS) + [
    "hora", "quarto", "dia_sen", "dia_cos", "dia_semana", "fim_de_semana", "feriado"]


def feriados_zurique(anos) -> set[date]:
    f: set[date] = set()
    for a in anos:
        p = _pascoa(a)
        f |= {date(a, 1, 1), date(a, 1, 2), p - timedelta(days=2), p + timedelta(days=1),
              date(a, 5, 1), p + timedelta(days=39), p + timedelta(days=50),
              date(a, 8, 1), date(a, 12, 25), date(a, 12, 26)}
    return f


# ---------------------------------------------------------------------------
# Preparacao (checklist do protocolo)
# ---------------------------------------------------------------------------
def preparar() -> tuple[pd.DataFrame, dict]:
    ck: dict = {}
    d = pd.read_parquet(ARQ, columns=["FK_STANDORT", "DATUM", "FUSS_IN", "FUSS_OUT"])
    d["ts"] = pd.to_datetime(d.DATUM)
    d = d[(d.ts >= INICIO) & (d.ts < FIM)].rename(columns={"FK_STANDORT": "ponto"})

    # 1. integridade
    d["ped"] = d[["FUSS_IN", "FUSS_OUT"]].sum(axis=1, min_count=1)
    ck["registros_na_janela"] = int(len(d))
    ck["nulos_descartados"] = int(d.ped.isna().sum())
    d = d.dropna(subset=["ped"])
    ck["negativos_descartados"] = int((d.ped < 0).sum())
    d = d[d.ped >= 0]
    rep = d.duplicated(["ponto", "ts"], keep=False)
    ck["linhas_em_carimbo_repetido"] = int(rep.sum())
    ck["datas_com_carimbo_repetido"] = sorted({str(x) for x in d[rep].ts.dt.date})
    # 2. horario de verao: carimbos repetidos combinados pela MEDIA
    d = d.groupby(["ponto", "ts"], as_index=False).ped.mean()

    # selecao de pontos (a mesma do item 60)
    g = d.groupby("ponto").ts.agg(["size", "min", "max"])
    cob = g["size"] / ((g["max"] - g["min"]).dt.total_seconds() / 900 + 1)
    ok = g.index[((g["max"] - g["min"]).dt.days >= DIAS_MIN) & (cob >= COBERTURA_MIN)]
    d = d[d.ponto.isin(ok)]
    ck["pontos"] = [int(x) for x in ok]

    # 3. grade completa (ausente fica NaN)
    d = (d.astype({"ped": float}).set_index("ts").groupby("ponto").ped.resample("15min").mean()
         .reset_index().sort_values(["ponto", "ts"]))
    ck["intervalos_na_grade"] = int(len(d))
    ck["intervalos_ausentes"] = int(d.ped.isna().sum())

    # 4. sensor travado: zero por >= 8 h com algum intervalo entre 8h e 20h
    travados = 0
    marca = np.zeros(len(d), dtype=bool)
    for _, idx in d.groupby("ponto").groups.items():
        sub = d.loc[idx]
        z = (sub.ped.astype(float) == 0).to_numpy(dtype=bool)  # ausente nao e zero
        dia = ((sub.ts.dt.hour >= 8) & (sub.ts.dt.hour < 20)).to_numpy()
        pos = np.flatnonzero(np.diff(np.concatenate([[0], z.astype(int), [0]])))
        for ini, fim in zip(pos[::2], pos[1::2]):
            if fim - ini >= TRAVADO_INTERVALOS and dia[ini:fim].any():
                travados += 1
                marca[d.index.get_indexer(sub.index[ini:fim])] = True
    ck["sequencias_de_sensor_travado"] = travados
    ck["intervalos_marcados_travados"] = int(marca.sum())
    d.loc[marca, "ped"] = np.nan

    # 5. outliers: p99 so no treino, nivel limitado a 1
    cheio = d[d.ts < CORTE].groupby("ponto").ped.quantile(PERCENTIL_CHEIO).rename("cheio")
    d = d.merge(cheio, on="ponto")
    ck["intervalos_acima_p99"] = int((d.ped > d.cheio).sum())
    ck["intervalos_acima_2x_p99"] = int((d.ped > 2 * d.cheio).sum())
    d["nivel"] = (d.ped / d.cheio).clip(0, 1)

    # 6. realocacao: mediana mensal fora de 0,5 a 2 x a mediana do ponto (so reporta)
    m = d.assign(mes=d.ts.dt.to_period("M")).groupby(["ponto", "mes"]).nivel.median()
    ref = m.groupby("ponto").median()
    fora = []
    for (pt, mes), v in m.items():
        r = ref[pt]
        if r > 0 and not (0.5 * r <= v <= 2 * r):
            fora.append(f"{pt}:{mes} ({v / r:.2f}x)")
    ck["meses_suspeitos_de_realocacao"] = fora
    return d.sort_values(["ponto", "ts"]).reset_index(drop=True), ck


def atributos(d: pd.DataFrame) -> pd.DataFrame:
    g = d.groupby("ponto")["nivel"]
    for k in ATRASOS:
        d[f"atraso_{k}"] = g.shift(k)
    for nome, jan in MEDIAS.items():
        d[nome] = g.shift(1).rolling(jan).mean().reset_index(level=0, drop=True)
    d["alvo"] = sum(g.shift(-k) for k in range(1, POR_HORA + 1)) / POR_HORA
    d["persistencia"] = sum(g.shift(k) for k in range(0, POR_HORA)) / POR_HORA
    d["semana_anterior"] = d.groupby("ponto")["alvo"].shift(672)
    d["hora"] = d.ts.dt.hour
    d["quarto"] = d.ts.dt.minute // 15
    frac = (d.hora * 4 + d.quarto) / 96
    d["dia_sen"], d["dia_cos"] = np.sin(2 * np.pi * frac), np.cos(2 * np.pi * frac)
    d["dia_semana"] = d.ts.dt.dayofweek
    d["fim_de_semana"] = (d.dia_semana >= 5).astype(int)
    fer = feriados_zurique(sorted(d.ts.dt.year.unique()))
    d["feriado"] = d.ts.dt.date.isin(fer).astype(int)
    return d.dropna(subset=COLUNAS + ["alvo", "nivel", "persistencia", "semana_anterior"])


# ---------------------------------------------------------------------------
def faixa(v, t):
    return np.digitize(np.asarray(v), t)


def metricas(y, p, n, baixo, t) -> dict:
    e = p - y
    sobe = y[n & baixo] >= t[0]
    diz = p[n & baixo] >= t[0]
    vp = int((diz & sobe).sum())
    prec = vp / diz.sum() if diz.sum() else 0.0
    rev = vp / sobe.sum() if sobe.sum() else 0.0
    return {"mae": float(np.abs(e).mean()), "rmse": float(np.sqrt((e ** 2).mean())),
            "mae_noite": float(np.abs(e[n]).mean()),
            "acerto_faixa_noite": float((faixa(p[n], t) == faixa(y[n], t)).mean()),
            "f1_vai_subir_noite": 2 * prec * rev / (prec + rev) if prec + rev else 0.0}


def main(registrar: bool) -> None:
    meta = json.loads(META.read_text(encoding="utf-8"))
    d, ck = preparar()
    print("checklist:", {k: v for k, v in ck.items() if not isinstance(v, list)})
    print("datas repetidas:", ck["datas_com_carimbo_repetido"], "| meses suspeitos:", len(ck["meses_suspeitos_de_realocacao"]))
    d = atributos(d)
    treino, teste = d[d.ts < CORTE], d[d.ts >= CORTE].reset_index(drop=True)
    tercis = [round(float(treino.nivel.quantile(q)), 4) for q in (1 / 3, 2 / 3)]
    print(f"treino {len(treino):,} | teste {len(teste):,} | tercis (so treino) {tercis}")

    corte_val = treino.ts.quantile(0.9)
    tr, val = treino[treino.ts < corte_val], treino[treino.ts >= corte_val]
    modelo = xgb.XGBRegressor(n_estimators=2000, learning_rate=0.05, max_depth=8, subsample=0.8,
                              colsample_bytree=0.8, min_child_weight=5, objective="reg:squarederror",
                              tree_method="hist", early_stopping_rounds=50, eval_metric="mae",
                              n_jobs=0, random_state=37)
    t0 = time.perf_counter()
    modelo.fit(tr[COLUNAS], tr.alvo, eval_set=[(val[COLUNAS], val.alvo)], verbose=False)
    tempos = {"xgboost_treino_s": round(time.perf_counter() - t0, 1)}
    modelo.save_model(MODELO)

    prev = {"xgboost": modelo.predict(teste[COLUNAS]).clip(0, 1),
            "persistencia": teste.persistencia.to_numpy(),
            "semana_anterior": teste.semana_anterior.to_numpy()}
    ch = ["ponto", "dia_semana", "hora", "quarto"]
    saz = treino.groupby(ch).alvo.mean().rename("s")
    prev["media_sazonal"] = teste.merge(saz, on=ch, how="left").s.fillna(treino.alvo.mean()).to_numpy()

    xl = pd.get_dummies(treino[COLUNAS], columns=["hora", "dia_semana"], dtype=float)
    xlt = pd.get_dummies(teste[COLUNAS], columns=["hora", "dia_semana"], dtype=float).reindex(columns=xl.columns, fill_value=0.0)
    prev["linear"] = LinearRegression().fit(xl, treino.alvo).predict(xlt).clip(0, 1)
    rf = RandomForestRegressor(n_estimators=200, min_samples_leaf=5, max_features=0.5,
                               max_samples=0.3, random_state=37, n_jobs=-1)
    t0 = time.perf_counter(); rf.fit(treino[COLUNAS], treino.alvo); tempos["rf_treino_s"] = round(time.perf_counter() - t0, 1)
    prev["random_forest"] = rf.predict(teste[COLUNAS]).clip(0, 1)

    y = teste.alvo.to_numpy()
    h = teste.ts.dt.hour.to_numpy()
    n = (h >= 18) | (h < 6)
    baixo = teste.nivel.to_numpy() < tercis[0]
    res = {k: metricas(y, v, n, baixo, tercis) for k, v in prev.items()}

    por_ponto = {}
    for k in ("linear", "random_forest", "media_sazonal", "persistencia", "semana_anterior"):
        por_ponto[k] = int(sum(
            np.abs(prev["xgboost"][i] - y[i]).mean() < np.abs(prev[k][i] - y[i]).mean()
            for i in (np.asarray(ix) for ix in teste.groupby("ponto").groups.values())))
    npt = teste.ponto.nunique()

    leitura = {}
    for k in ("linear", "random_forest"):
        rel = (res[k]["mae"] - res["xgboost"]["mae"]) / res[k]["mae"]
        if rel >= LIMIAR_RELATIVO and por_ponto[k] > npt / 2:
            leitura[k] = "XGBoost superior"
        elif rel <= -LIMIAR_RELATIVO and por_ponto[k] < npt / 2:
            leitura[k] = "XGBoost inferior"
        elif abs(rel) < LIMIAR_RELATIVO:
            leitura[k] = "equivalentes em erro"
        else:
            leitura[k] = "sem conclusao pela regra"
        leitura[k] += f" (MAE {rel:+.1%}; melhor em {por_ponto[k]}/{npt} pontos)"
    simples = ("persistencia", "media_sazonal", "semana_anterior")
    melhor = max(simples, key=lambda k: res[k]["acerto_faixa_noite"])
    df = res["xgboost"]["acerto_faixa_noite"] - res[melhor]["acerto_faixa_noite"]
    melhor_f1 = max(res[k]["f1_vai_subir_noite"] for k in simples)
    dfs = res["xgboost"]["f1_vai_subir_noite"] - melhor_f1
    leitura["referencias_simples"] = (
        ("NAO substituivel" if df >= 0.02 and dfs >= 0.02 else "substituivel")
        + f" (faixa {df * 100:+.1f} pp sobre {melhor}; F1 {dfs:+.3f} sobre a melhor)")

    for k, v in res.items():
        print(f"  {k:15s} MAE {v['mae']:.4f} noite {v['mae_noite']:.4f} faixa {v['acerto_faixa_noite']:.3f} F1 {v['f1_vai_subir_noite']:.3f}")
    print("por ponto:", por_ponto, "| tempos:", tempos)
    for k, v in leitura.items():
        print("LEITURA", k, ":", v)

    rel = {"rotulo": ROTULO, "protocolo": "PROTOCOLO_MODELO_ZURIQUE.md",
           "gerado_em": datetime.now(timezone.utc).isoformat(), "serie_sha256": meta["sha256"],
           "checklist": ck, "linhas_treino": len(treino), "linhas_teste": len(teste),
           "melhor_iteracao": int(modelo.best_iteration), "tercis_nivel": tercis,
           "atributos": COLUNAS, "metricas": res, "xgboost_melhor_por_ponto": por_ponto,
           "pontos_no_teste": int(npt), "tempos": tempos, "leitura": leitura,
           "modelo_sha256": hashlib.sha256(MODELO.read_bytes()).hexdigest()}
    SAIDA.write_text(json.dumps(rel, indent=2, ensure_ascii=False), encoding="utf-8")
    print("registro:", SAIDA)

    if registrar:
        import psycopg

        from decisao import config
        with psycopg.connect(config.DATABASE_URL, autocommit=True, connect_timeout=5) as conn:
            conn.execute(
                """INSERT INTO versao_modelo_previsao
                       (rotulo, algoritmo, serie_extraida_em, treinado_em, mae, rmse, hash_modelo)
                   VALUES (%s, 'xgboost', %s, now(), %s, %s, %s)
                   ON CONFLICT (rotulo) DO UPDATE SET treinado_em = EXCLUDED.treinado_em,
                       mae = EXCLUDED.mae, rmse = EXCLUDED.rmse, hash_modelo = EXCLUDED.hash_modelo""",
                (ROTULO, meta["baixado_em"][:10], res["xgboost"]["mae"], res["xgboost"]["rmse"],
                 rel["modelo_sha256"]))
        print("registrado como", ROTULO)


if __name__ == "__main__":
    a = argparse.ArgumentParser()
    a.add_argument("--registrar", action="store_true")
    main(a.parse_args().registrar)
