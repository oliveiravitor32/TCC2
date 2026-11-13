"""Figura do Apendice G: uma noite real de Zurique com os tres regimes.

    python -m figuras.figura_noite_real saida.png

So le resultado ja gravado (cenarios/resultados/avaliacao_ia_zurique_antecipado.json,
modo em operacao: XGBoost + inferencia nebulosa, base v6-zurique) e calcula o horario
fixo pela mesma funcao da avaliacao (decisao.energia.trajetoria_horario_fixo).
"""
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from datetime import time
from zoneinfo import ZoneInfo

from decisao.energia import trajetoria_horario_fixo

# os mesmos de cenarios/executar.py e decisao/config.py (importa-los exige o psycopg)
HORA_INICIO_ATENUACAO, HORA_FIM_ATENUACAO = time(0, 0), time(5, 0)
FUSO = ZoneInfo("America/Sao_Paulo")

NOITE = "zurique_movimentado_1358_dia_util"
PISO = 0.5
TERCIS = (0.0693, 0.2946)

raiz = Path(__file__).resolve().parents[1]
d = json.load(open(raiz / "cenarios/resultados/avaliacao_ia_zurique_antecipado.json", encoding="utf-8"))
r = next(x for x in d["relatorios"] if x["cenario"] == NOITE)
s = r["serie"]
h = [x["minuto"] / 60 for x in s]
inicio = datetime.fromisoformat(r["inicio"])
fixo = trajetoria_horario_fixo(inicio, inicio + timedelta(hours=12), PISO,
                               hora_inicio_atenuacao=HORA_INICIO_ATENUACAO,
                               hora_fim_atenuacao=HORA_FIM_ATENUACAO, passo_s=5.0, fuso=FUSO)
hf = [(t - inicio).total_seconds() / 3600 for t, _, _ in fixo]

plt.rcParams.update({"font.family": "Arial", "font.size": 9})
f, (a1, a2) = plt.subplots(2, 1, figsize=(7.5, 5.2), sharex=True, gridspec_kw={"height_ratios": [1, 1.4]})
a1.plot(h, [x["observada"] for x in s], color="#555", lw=1)
for t in TERCIS:
    a1.axhline(t, color="#999", lw=0.7, ls=":")
a1.text(12.05, TERCIS[0], "tercil inferior", va="center", fontsize=7)
a1.text(12.05, TERCIS[1], "tercil superior", va="center", fontsize=7)
a1.set_ylabel("Volume observado\n(normalizado)")
a1.set_ylim(0, 1)

a2.plot(h, [1.0] * len(h), color="#999", lw=1.2, ls="--", label="Fluxo pleno constante")
a2.plot(hf, [n for _, _, n in fixo], color="#d97706", lw=1.4, label="Horário fixo (0 h às 5 h)")
a2.plot(h, [x["emitido"] for x in s], color="#1d4ed8", lw=1.6, label="Adaptativo (em operação)")
a2.axhline(PISO, color="#b91c1c", lw=0.9, label="Piso (P5)")
a2.set_ylabel("Nível (fração do pleno)")
a2.set_ylim(0.3, 1.05)
a2.legend(loc="lower left", fontsize=7.5, ncol=2, frameon=False)
a2.set_xticks(range(0, 13, 2))
a2.set_xticklabels([f"{(18 + k) % 24} h" for k in range(0, 13, 2)])
a2.set_xlabel("Hora local")
for a in (a1, a2):
    a.spines[["top", "right"]].set_visible(False)
plt.tight_layout()
plt.savefig(sys.argv[1], dpi=200, facecolor="white")
e = r["energia"]["REF-40W"]
print(NOITE, r["descricao"], e["razao_adaptativo_pleno"], e["razao_adaptativo_fixo"])
