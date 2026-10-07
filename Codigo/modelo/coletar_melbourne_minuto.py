"""Coleta continua da contagem de pedestres POR MINUTO de Melbourne.

O conjunto "Pedestrian Counting System - Past Hour (counts per minute)" so
guarda as ultimas ~11 horas (conferido em 06/10/2026, apesar do nome). Para
formar uma serie de semanas, este script baixa o conjunto inteiro e acrescenta
ao arquivo do dia so as linhas novas. Rodado a cada hora pelo cron da VM,
uma coleta perdida nao perde dado (a janela da API cobre ~11 coletas).

    python3 modelo/coletar_melbourne_minuto.py [pasta]

So biblioteca padrao (roda no python3 do Ubuntu da VM, fora dos conteineres).
Saida: <pasta>/AAAA-MM-DD.csv (data UTC de sensing_datetime) e coletas.log.
Cada linha guarda tambem coletado_em, para documentar a extracao (3.6).
Nao toca no banco nem no servico de decisao.
"""

from __future__ import annotations

import csv
import io
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

URL = ("https://data.melbourne.vic.gov.au/api/explore/v2.1/catalog/datasets/"
       "pedestrian-counting-system-past-hour-counts-per-minute/exports/csv?delimiter=%2C")
CAMPOS = ["location_id", "sensing_datetime", "direction_1", "direction_2",
          "total_of_directions", "coletado_em"]


def chaves_existentes(arq: Path) -> set[tuple[str, str]]:
    if not arq.exists():
        return set()
    with arq.open(encoding="utf-8", newline="") as f:
        return {(l["location_id"], l["sensing_datetime"]) for l in csv.DictReader(f)}


def coletar(pasta: Path) -> tuple[int, int]:
    pasta.mkdir(parents=True, exist_ok=True)
    agora = datetime.now(timezone.utc).isoformat(timespec="seconds")
    with urllib.request.urlopen(URL, timeout=120) as resp:
        texto = resp.read().decode("utf-8-sig")
    linhas = list(csv.DictReader(io.StringIO(texto)))

    por_dia: dict[str, list[dict]] = {}
    for l in linhas:
        por_dia.setdefault(l["sensing_datetime"][:10], []).append(l)

    novas = 0
    for dia, ls in sorted(por_dia.items()):
        arq = pasta / f"{dia}.csv"
        vistas = chaves_existentes(arq)
        incluir = [l for l in ls if (l["location_id"], l["sensing_datetime"]) not in vistas]
        if not incluir:
            continue
        novo = not arq.exists()
        with arq.open("a", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=CAMPOS, extrasaction="ignore")
            if novo:
                w.writeheader()
            for l in sorted(incluir, key=lambda x: (x["sensing_datetime"], int(x["location_id"]))):
                w.writerow({**l, "coletado_em": agora})
        novas += len(incluir)

    with (pasta / "coletas.log").open("a", encoding="utf-8") as f:
        f.write(f"{agora} baixadas={len(linhas)} novas={novas}\n")
    return len(linhas), novas


if __name__ == "__main__":
    pasta = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parent / "dados" / "melbourne_minuto"
    try:
        baixadas, novas = coletar(pasta)
        print(f"baixadas {baixadas}, novas {novas}")
    except Exception as erro:  # o cron nao mostra o erro: fica no log
        pasta.mkdir(parents=True, exist_ok=True)
        with (pasta / "coletas.log").open("a", encoding="utf-8") as f:
            f.write(f"{datetime.now(timezone.utc).isoformat(timespec='seconds')} ERRO {erro!r}\n")
        raise
