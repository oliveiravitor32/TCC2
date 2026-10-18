"""Gerador de volumes da visao de bairro (DIVERGENCIAS 76).

Publica, a cada 5 min, UM pacote no POST /eventos com o volume de cada trecho
do recorte, como a plataforma faria (Quadro 18). Os numeros sao INVENTADOS,
so para a demonstracao: uma "noite" que comeca movimentada e esvazia aos
poucos, comprimida em --ciclo-min minutos e repetida, com alguns trechos
sempre mais cheios e uma pequena variacao com semente fixa. origem =
"gerador-demo", para ficar claro na auditoria. Nunca e fonte de resultado.

Por padrao NAO publica nos trechos do no real (BANCADA-01), para nao mexer na
demonstracao da bancada; --incluir-bancada desliga essa protecao.

    API_URL=https://... CHAVE_API=... python -m simulador.gerador_volumes [--ciclo-min 60]
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import random
import time
import urllib.request
from datetime import datetime, timezone

from cadastro.recorte import RECORTE

TRECHOS_BANCADA = {20159, 21198, 22661}
PESSOAS_INICIO = 3.0   # pessoas na area no comeco da noite, no trecho medio
PERIODO_S = 300

log = logging.getLogger("gerador")


def trechos() -> list[int]:
    rec = json.loads(RECORTE.read_text(encoding="utf-8"))
    return sorted(f["properties"]["cd_identificador"] for f in rec["trechos"]["geojson"]["features"])


def pacote(ids: list[int], fracao_da_noite: float, pesos: dict[int, float], rnd: random.Random,
           agora: datetime) -> list[dict]:
    """Volume de cada trecho: perfil que esvazia (1 - f)^2, peso do trecho e ruido."""
    base = PESSOAS_INICIO * (1 - fracao_da_noite) ** 2
    itens = []
    for t in ids:
        media = max(0.0, base * pesos[t] + rnd.gauss(0, 0.1))
        itens.append({"ocorrido_em": agora.isoformat(), "tipo": "volume",
                      "pessoas_media": round(media, 2), "periodo_s": PERIODO_S,
                      "trecho": t, "origem": "gerador-demo"})
    return itens


def publicar(url: str, chave: str, itens: list[dict]) -> dict:
    req = urllib.request.Request(url.rstrip("/") + "/eventos", data=json.dumps(itens).encode(),
                                 headers={"Content-Type": "application/json", "X-Chave-Api": chave},
                                 method="POST")
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read())


def main() -> None:
    p = argparse.ArgumentParser(description="volumes inventados para a visao de bairro")
    p.add_argument("--ciclo-min", type=float, default=60, help="duracao de uma 'noite' simulada")
    p.add_argument("--intervalo-s", type=float, default=PERIODO_S)
    p.add_argument("--incluir-bancada", action="store_true")
    p.add_argument("--semente", type=int, default=42)
    p.add_argument("--uma-vez", action="store_true")
    a = p.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    url = os.environ.get("API_URL", "http://localhost:8000")
    chave = os.environ.get("CHAVE_API", "")
    ids = [t for t in trechos() if a.incluir_bancada or t not in TRECHOS_BANCADA]
    rnd = random.Random(a.semente)
    pesos = {t: rnd.uniform(0.5, 1.6) for t in ids}  # alguns trechos sempre mais cheios
    inicio = time.monotonic()
    while True:
        f = ((time.monotonic() - inicio) / 60 % a.ciclo_min) / a.ciclo_min
        try:
            r = publicar(url, chave, pacote(ids, f, pesos, rnd, datetime.now(timezone.utc)))
            log.info("noite %.0f%%: %s aceitos, %s recusados", f * 100, len(r["aceitos"]),
                     len(r["recusados"]))
        except Exception as erro:  # demonstracao: segue tentando
            log.warning("publicacao falhou: %s", erro)
        if a.uma_vez:
            return
        time.sleep(a.intervalo_s)


if __name__ == "__main__":
    main()
