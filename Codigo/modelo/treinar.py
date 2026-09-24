"""Treina e avalia a camada de previsao (TCC 3.6, Etapa 3, resultado 5.1).

    python -m modelo.treinar [--registrar]

Tarefa: regressao sobre dado tabular. Prever o nivel de movimentacao da
PROXIMA janela horaria a partir das janelas anteriores e de atributos de
calendario. Modelo: reforco de gradiente (XGBoost, CHEN; GUESTRIN, 2016),
escolhido em 2.7 por ser a familia que supera aprendizado profundo em dado
tabular (GRINSZTAJN; OYALLON; VAROQUAUX, 2022).

Protocolo (3.6):
  - particao CRONOLOGICA (o periodo final e o teste): sem vazamento;
  - metricas MAE e RMSE;
  - comparacao obrigatoria com duas referencias ingenuas: persistencia e
    media sazonal (mesma hora, mesmo dia da semana). Se o modelo nao superar
    as referencias, o resultado e reportado assim mesmo.

Normalizacao por ponto de medicao: as contagens absolutas de Melbourne nao
sao transponiveis a uma via paulistana (3.6). O que se transfere e a
ESTRUTURA. Cada ponto e normalizado pela propria distribuicao, e e nesse
espaco normalizado que o modelo trabalha e que os tercis das particoes
nebulosas sao calculados (3.7).

Saidas: modelo/resultados/metricas.json, modelo/modelo_previsao.json e,
com --registrar, a linha correspondente em versao_modelo_previsao.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import xgboost as xgb

AQUI = Path(__file__).resolve().parent
CSV = AQUI / "dados" / "melbourne_pedestres.csv"
META = AQUI / "dados" / "extracao.json"
RESULTADOS = AQUI / "resultados"
MODELO = AQUI / "modelo_previsao.json"

# Pontos com serie utilizavel: sem eles, os atrasos ficam cheios de buraco.
COBERTURA_MIN = 0.98
HORAS_MIN = 17_000
# Normalizacao robusta: o percentil 99 e o "cheio" do ponto. O maximo
# absoluto seria um evento isolado (um jogo, uma passeata) e achataria o
# resto da distribuicao.
PERCENTIL_CHEIO = 0.99
FRACAO_TESTE = 0.2
ATRASOS = (1, 2, 3, 24, 168)  # 1-3 h, mesmo horario de ontem, da semana passada
ROTULO = "xgboost-v1"


# ---------------------------------------------------------------------------
# Calendario (feriados de Victoria, onde a serie e medida)
# ---------------------------------------------------------------------------
def _pascoa(ano: int) -> date:
    """Domingo de Pascoa (algoritmo gregoriano anonimo)."""
    a, b, c = ano % 19, ano // 100, ano % 100
    d, e = b // 4, b % 4
    f, g = (b + 8) // 25, (b - (b + 8) // 25 + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i, k = c // 4, c % 4
    l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l) // 451
    mes = (h + l - 7 * m + 114) // 31
    dia = ((h + l - 7 * m + 114) % 31) + 1
    return date(ano, mes, dia)


def _enesima_segunda(ano: int, mes: int, n: int) -> date:
    d = date(ano, mes, 1)
    d += timedelta(days=(0 - d.weekday()) % 7)
    return d + timedelta(weeks=n - 1)


def feriados(anos: list[int]) -> set[date]:
    """Feriados publicos de Victoria. A sexta da Grande Final da AFL varia
    de ano para ano e nao e incluida - fica declarado como aproximacao."""
    f: set[date] = set()
    for ano in anos:
        pascoa = _pascoa(ano)
        f |= {
            date(ano, 1, 1),                       # Ano-Novo
            date(ano, 1, 26),                      # Dia da Australia
            _enesima_segunda(ano, 3, 2),           # Dia do Trabalho (Victoria)
            pascoa - timedelta(days=2),            # Sexta-Feira Santa
            pascoa - timedelta(days=1),            # Sabado de Pascoa
            pascoa,                                # Domingo de Pascoa
            pascoa + timedelta(days=1),            # Segunda de Pascoa
            date(ano, 4, 25),                      # ANZAC
            _enesima_segunda(ano, 6, 2),           # Aniversario do Rei
            date(ano, 11, 1) + timedelta(days=(1 - date(ano, 11, 1).weekday()) % 7),  # Melbourne Cup
            date(ano, 12, 25),                     # Natal
            date(ano, 12, 26),                     # Boxing Day
        }
    return f


# ---------------------------------------------------------------------------
# Preparacao
# ---------------------------------------------------------------------------
def carregar() -> tuple[pd.DataFrame, dict]:
    if not CSV.exists():
        raise SystemExit("serie ausente: rode  python -m modelo.baixar_dados")
    meta = json.loads(META.read_text(encoding="utf-8"))
    d = pd.read_csv(CSV, usecols=["sensing_date", "hourday", "location_id", "pedestriancount"])
    d["ts"] = pd.to_datetime(d.sensing_date) + pd.to_timedelta(d.hourday, unit="h")
    return d[["location_id", "ts", "pedestriancount"]], meta


def pontos_utilizaveis(d: pd.DataFrame) -> list[int]:
    g = d.groupby("location_id").ts.agg(["size", "min", "max"])
    possiveis = ((g["max"] - g["min"]).dt.total_seconds() // 3600 + 1)
    ok = (g["size"] / possiveis >= COBERTURA_MIN) & (g["size"] >= HORAS_MIN)
    return sorted(g.index[ok])


def montar_atributos(d: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series]:
    """Serie normalizada por ponto + atrasos + calendario."""
    d = d.sort_values(["location_id", "ts"]).copy()
    cheio = d.groupby("location_id").pedestriancount.transform(
        lambda s: s.quantile(PERCENTIL_CHEIO)
    )
    # 0 = ponto vazio, 1 = movimentacao "cheia" do proprio ponto.
    d["nivel"] = (d.pedestriancount / cheio).clip(0, 1)

    # Grade horaria completa por ponto: hora faltante vira NaN e as linhas
    # cujo atraso caia num buraco sao descartadas (nao se inventa dado).
    d = (
        d.set_index("ts")
        .groupby("location_id")["nivel"]
        .resample("h")
        .mean()
        .reset_index()
        .sort_values(["location_id", "ts"])
    )

    g = d.groupby("location_id")["nivel"]
    for k in ATRASOS:
        d[f"atraso_{k}h"] = g.shift(k)
    d["media_3h"] = g.shift(1).rolling(3).mean().reset_index(level=0, drop=True)
    d["media_24h"] = g.shift(1).rolling(24).mean().reset_index(level=0, drop=True)

    d["hora"] = d.ts.dt.hour
    d["dia_semana"] = d.ts.dt.dayofweek
    d["fim_de_semana"] = (d.dia_semana >= 5).astype(int)
    fer = feriados(sorted(d.ts.dt.year.unique()))
    d["feriado"] = d.ts.dt.date.isin(fer).astype(int)
    # Hora como angulo: 23h e 0h sao vizinhas.
    d["hora_sen"] = np.sin(2 * np.pi * d.hora / 24)
    d["hora_cos"] = np.cos(2 * np.pi * d.hora / 24)

    # Alvo: nivel da PROXIMA janela.
    d["alvo"] = g.shift(-1)

    colunas = [f"atraso_{k}h" for k in ATRASOS] + [
        "media_3h", "media_24h", "hora", "hora_sen", "hora_cos",
        "dia_semana", "fim_de_semana", "feriado",
    ]
    d = d.dropna(subset=colunas + ["alvo", "nivel"])
    return d, d["alvo"]


# ---------------------------------------------------------------------------
# Avaliacao
# ---------------------------------------------------------------------------
def erros(y: np.ndarray, p: np.ndarray) -> dict:
    e = np.asarray(p) - np.asarray(y)
    return {"mae": float(np.abs(e).mean()), "rmse": float(np.sqrt((e**2).mean()))}


def media_sazonal(treino: pd.DataFrame, teste: pd.DataFrame) -> np.ndarray:
    """Media historica daquela hora naquele dia da semana, por ponto.

    Calculada SO no treino (evita vazamento). Onde a combinacao nao existe
    no treino, cai para a media do ponto.
    """
    chave = ["location_id", "dia_semana", "hora"]
    m = treino.groupby(chave).alvo.mean().rename("sazonal")
    por_ponto = treino.groupby("location_id").alvo.mean().rename("ponto")
    j = teste.merge(m, on=chave, how="left").merge(por_ponto, on="location_id", how="left")
    return j.sazonal.fillna(j.ponto).to_numpy()


def treinar(registrar: bool) -> dict:
    bruto, meta = carregar()
    pontos = pontos_utilizaveis(bruto)
    print(f"serie extraida em {meta['extraido_em']}; {len(pontos)} pontos utilizaveis")
    d, _ = montar_atributos(bruto[bruto.location_id.isin(pontos)])

    colunas = [c for c in d.columns if c.startswith("atraso_")] + [
        "media_3h", "media_24h", "hora", "hora_sen", "hora_cos",
        "dia_semana", "fim_de_semana", "feriado",
    ]
    corte = d.ts.quantile(1 - FRACAO_TESTE)
    treino, teste = d[d.ts < corte], d[d.ts >= corte]
    # Ultimos 10 % do treino como validacao, para a parada antecipada.
    corte_val = treino.ts.quantile(0.9)
    tr, val = treino[treino.ts < corte_val], treino[treino.ts >= corte_val]
    print(f"treino ate {corte:%Y-%m-%d} ({len(treino):,} linhas) | teste {len(teste):,} linhas")

    modelo = xgb.XGBRegressor(
        n_estimators=2000,
        learning_rate=0.05,
        max_depth=8,
        subsample=0.8,
        colsample_bytree=0.8,
        min_child_weight=5,
        objective="reg:squarederror",
        tree_method="hist",
        early_stopping_rounds=50,
        eval_metric="mae",
        n_jobs=0,
        random_state=37,
    )
    modelo.fit(tr[colunas], tr.alvo, eval_set=[(val[colunas], val.alvo)], verbose=False)

    prev = modelo.predict(teste[colunas]).clip(0, 1)
    resultado = {
        "xgboost": erros(teste.alvo, prev),
        "persistencia": erros(teste.alvo, teste.nivel),  # projeta o valor corrente
        "media_sazonal": erros(teste.alvo, media_sazonal(treino, teste)),
    }
    for nome, m in resultado.items():
        print(f"  {nome:14s} MAE {m['mae']:.4f}  RMSE {m['rmse']:.4f}")
    melhor = min(resultado, key=lambda k: resultado[k]["mae"])
    print(f"  -> menor MAE: {melhor}")

    # Tercis da distribuicao normalizada: fronteiras das particoes nebulosas
    # baixa/media/alta (3.7), derivadas do dado e nao arbitradas.
    tercis = [round(float(d.nivel.quantile(q)), 4) for q in (1 / 3, 2 / 3)]
    print(f"  tercis do nivel normalizado: {tercis}")

    MODELO.parent.mkdir(exist_ok=True)
    modelo.save_model(MODELO)
    relatorio = {
        "rotulo": ROTULO,
        "gerado_em": datetime.now(timezone.utc).isoformat(),
        "serie_extraida_em": meta["extraido_em"],
        "serie_sha256": meta["sha256"],
        "pontos": len(pontos),
        "linhas_treino": len(treino),
        "linhas_teste": len(teste),
        "corte_treino_teste": str(corte),
        "percentil_cheio": PERCENTIL_CHEIO,
        "atrasos_h": list(ATRASOS),
        "atributos": colunas,
        "melhor_iteracao": int(modelo.best_iteration),
        "metricas": resultado,
        "menor_mae": melhor,
        "tercis_nivel": tercis,
        "modelo_sha256": hashlib.sha256(MODELO.read_bytes()).hexdigest(),
    }
    RESULTADOS.mkdir(exist_ok=True)
    (RESULTADOS / "metricas.json").write_text(
        json.dumps(relatorio, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(f"\nmodelo: {MODELO}\nmetricas: {RESULTADOS / 'metricas.json'}")

    if registrar:
        import psycopg

        from decisao import config

        with psycopg.connect(config.DATABASE_URL, autocommit=True, connect_timeout=5) as conn:
            conn.execute(
                """
                INSERT INTO versao_modelo_previsao
                    (rotulo, algoritmo, serie_extraida_em, treinado_em, mae, rmse, hash_modelo)
                VALUES (%s, 'xgboost', %s, now(), %s, %s, %s)
                ON CONFLICT (rotulo) DO UPDATE SET
                    serie_extraida_em = EXCLUDED.serie_extraida_em,
                    treinado_em = EXCLUDED.treinado_em,
                    mae = EXCLUDED.mae, rmse = EXCLUDED.rmse,
                    hash_modelo = EXCLUDED.hash_modelo
                """,
                (ROTULO, meta["extraido_em"], resultado["xgboost"]["mae"],
                 resultado["xgboost"]["rmse"], relatorio["modelo_sha256"]),
            )
        print(f"registrado em versao_modelo_previsao como {ROTULO!r}")
    return relatorio


if __name__ == "__main__":
    p = argparse.ArgumentParser(description="Treino da camada de previsao (3.6)")
    p.add_argument("--registrar", action="store_true", help="grava a versao no banco")
    treinar(p.parse_args().registrar)
