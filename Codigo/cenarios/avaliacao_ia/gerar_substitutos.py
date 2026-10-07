"""Cenarios de ruido na fronteira do teste 2 (PROTOCOLO_SUBSTITUTOS.md, DIVERGENCIAS 59).

    python -m cenarios.avaliacao_ia.gerar_substitutos
"""

from __future__ import annotations

import json
import random
from pathlib import Path

AQUI = Path(__file__).resolve().parent
DUR_MIN = 180
PASSO_MIN = 5
DESVIO = 0.03
SEMENTES = (591, 592, 593)
def _fronteiras():
    import tomllib
    from decisao import config

    a, b = tomllib.loads(config.REGRAS.read_text(encoding="utf-8"))["movimentacao"]["fronteiras"]
    return [("baixa", a, "2026-09-23T01:00:00"), ("alta", b, "2026-09-22T19:00:00")]


FRONTEIRAS = _fronteiras()


def main() -> None:
    destino = AQUI / "ruido"
    destino.mkdir(exist_ok=True)
    for velho in destino.glob("*.json"):
        velho.unlink()
    for rotulo, centro, inicio in FRONTEIRAS:
        for s in SEMENTES:
            rng = random.Random(s)
            eventos = [{"em_min": m, "nivel": round(min(1.0, max(0.0, rng.gauss(centro, DESVIO))), 4)}
                       for m in range(0, DUR_MIN, PASSO_MIN)]
            nome = f"ruido_fronteira_{rotulo}_{s}"
            cen = {
                "nome": nome,
                "descricao": f"Volume oscilando em torno do tercil {rotulo} ({centro}).",
                "origem": f"normal({centro}; {DESVIO}), semente {s} (DIVERGENCIAS 59).",
                "inicio_local": inicio,
                "duracao_min": DUR_MIN,
                "eventos": eventos,
                "envelope": [{"de_min": 0, "ate_min": DUR_MIN, "min": 0.5, "max": 1.0,
                              "nota": "comparacao Mamdani x tabela; aderencia nao avaliada"}],
            }
            (destino / f"{nome}.json").write_text(
                json.dumps(cen, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
            print(nome)


if __name__ == "__main__":
    main()
