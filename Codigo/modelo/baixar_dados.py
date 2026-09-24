"""Baixa a serie horaria de pedestres de Melbourne (TCC 3.6).

    python -m modelo.baixar_dados

A serie e publicada em janela movel de 24 meses, entao o recorte precisa ser
DATADO: o script grava, ao lado do arquivo, a data de extracao, a contagem de
registros e o hash do conteudo (modelo/dados/extracao.json). E esse recorte,
e nao "a serie de Melbourne" em geral, que sustenta o resultado 5.1.

Origem: CITY OF MELBOURNE. Pedestrian Counting System (counts per hour).
Licenca aberta. Conjunto: pedestrian-counting-system-monthly-counts-per-hour.

Nenhum dado pessoal: sao contagens agregadas por sensor e por hora (RNF08).
"""

from __future__ import annotations

import hashlib
import json
import sys
from datetime import date, datetime, timezone
from pathlib import Path

import urllib.request

BASE = "https://data.melbourne.vic.gov.au/api/explore/v2.1/catalog/datasets"
CONJUNTO = "pedestrian-counting-system-monthly-counts-per-hour"
PASTA = Path(__file__).resolve().parent / "dados"
CSV = PASTA / "melbourne_pedestres.csv"
META = PASTA / "extracao.json"

COLUNAS = "sensing_date,hourday,sensor_name,location_id,pedestriancount"


def total_registros() -> int:
    url = f"{BASE}/{CONJUNTO}/records?limit=1"
    with urllib.request.urlopen(url, timeout=60) as r:
        return json.load(r)["total_count"]


def baixar() -> None:
    PASTA.mkdir(parents=True, exist_ok=True)
    total = total_registros()
    print(f"conjunto com {total:,} registros; baixando CSV (alguns minutos)...")

    url = f"{BASE}/{CONJUNTO}/exports/csv?select={COLUNAS}&delimiter=,"
    sha = hashlib.sha256()
    baixado = 0
    with urllib.request.urlopen(url, timeout=900) as r, CSV.open("wb") as f:
        while pedaco := r.read(1 << 20):
            f.write(pedaco)
            sha.update(pedaco)
            baixado += len(pedaco)
            print(f"\r  {baixado / 1e6:,.1f} MB", end="", flush=True)
    print()

    linhas = sum(1 for _ in CSV.open(encoding="utf-8", errors="replace")) - 1
    META.write_text(
        json.dumps(
            {
                "conjunto": CONJUNTO,
                "fonte": f"{BASE}/{CONJUNTO}",
                "extraido_em": date.today().isoformat(),
                "baixado_em": datetime.now(timezone.utc).isoformat(),
                "registros_declarados": total,
                "linhas_no_csv": linhas,
                "bytes": baixado,
                "sha256": sha.hexdigest(),
                "colunas": COLUNAS.split(","),
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"ok: {CSV} ({linhas:,} linhas)\nmetadados: {META}")


if __name__ == "__main__":
    try:
        baixar()
    except Exception as erro:  # rede, timeout, mudanca na API
        raise SystemExit(f"falha ao baixar: {type(erro).__name__}: {erro}") from None
