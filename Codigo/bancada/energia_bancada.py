"""Energia do no de bancada sobre uma trajetoria registrada (3.11, 5.5).

    python -m bancada.energia_bancada bancada/resultados/energia_bancada_ct18_descida.json

O JSON traz a telemetria baixada da VM (GET /telemetria) no intervalo da
descida ao piso do CT18. Integra, entre telemetrias consecutivas:
  - pelo ciclo de trabalho: P x duty x dt (3.11, bancada);
  - pela luz medida: P x duty_pleno x (lux / lux da classe) x dt, isto e,
    supondo potencia proporcional a luz entregue;
  - no pleno da classe: P x duty_pleno x dt.
P = 14,4 W/m x comprimento do segmento (Quadro 4).
"""

from __future__ import annotations

import json
import sys
from datetime import datetime


def _t(s: str) -> datetime:
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


def integrar(dados: dict, lux_classe: float = 10.0) -> dict:
    tel = sorted(dados["telemetria"], key=lambda t: t["recebido_em"])
    p, dpl = dados["potencia_segmento_w"], dados["duty_pleno"]
    e_duty = e_luz = e_pleno = horas = 0.0
    for a, b in zip(tel, tel[1:]):
        dt = (_t(b["recebido_em"]) - _t(a["recebido_em"])).total_seconds() / 3600
        e_duty += p * a["duty"] * dt
        e_luz += p * dpl * (a["lux_medido"] / lux_classe) * dt
        e_pleno += p * dpl * dt
        horas += dt
    return {"amostras": len(tel), "minutos": round(horas * 60, 2),
            "energia_duty_mwh": round(e_duty * 1000, 1), "energia_luz_mwh": round(e_luz * 1000, 1),
            "energia_pleno_mwh": round(e_pleno * 1000, 1),
            "duty_sobre_pleno": round(e_duty / e_pleno, 4),
            "divergencia_luz_duty": round(e_luz / e_duty - 1, 4)}


if __name__ == "__main__":
    with open(sys.argv[1], encoding="utf-8") as f:
        print(json.dumps(integrar(json.load(f)), indent=2))
