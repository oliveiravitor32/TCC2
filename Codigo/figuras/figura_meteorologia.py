"""Diagrama conceitual da terceira restricao da camada de verificacao: condicao meteorologica adversa
(Apendice E; proposta, nao implementada).

    python Codigo/figuras/figura_meteorologia.py saida.png
"""
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

F = "Arial"
fig, ax = plt.subplots(figsize=(12, 7.4), dpi=200)
ax.set_xlim(0, 15)
ax.set_ylim(0, 9.2)
ax.axis("off")


def caixa(x, y, w, h, titulo, linhas, tracejada=False, cinza=False):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.12",
                                fc="#eeeeee" if cinza else "white", ec="black", lw=1.3,
                                ls="--" if tracejada else "-"))
    ax.text(x + w / 2, y + h - 0.28, titulo, ha="center", va="top", fontsize=10, fontname=F, fontweight="bold")
    ax.text(x + w / 2, y + h - 0.72, "\n".join(linhas), ha="center", va="top", fontsize=8.6, fontname=F,
            linespacing=1.45)


def seta(x1, y1, x2, y2, rotulo=None, dx=0.0, dy=0.18, tracejada=False):
    ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle="-|>", mutation_scale=14, lw=1.2,
                                 color="black", ls="--" if tracejada else "-"))
    if rotulo:
        ax.text((x1 + x2) / 2 + dx, (y1 + y2) / 2 + dy, rotulo, ha="center", va="bottom", fontsize=8.2,
                fontname=F, style="italic")


# Fila de cima: fonte meteorologica (nova, tracejada)
caixa(0.3, 6.3, 3.6, 2.5, "Fonte meteorológica",
      ["INMET: estações e avisos", "meteorológicos", "estações do município", "(termo de referência,", "Anexo XI)"],
      tracejada=True)
caixa(5.2, 6.3, 4.2, 2.5, "Adaptador meteorológico",
      ["consulta periódica ou notificação,", "conforme o que a fonte oferecer", "traduz para: área, condição", "(nevoeiro, neblina, chuva intensa),",
       "início e validade"], tracejada=True)
caixa(10.7, 6.3, 4.0, 2.5, "Condição adversa vigente",
      ["tabela por área (trechos afetados)", "vence sozinha ao fim da validade", "fonte muda ou indisponível:",
       "alerta ao operador; valem", "as restrições 1 e 2"], tracejada=True)
seta(3.9, 7.55, 5.2, 7.55)
seta(9.4, 7.55, 10.7, 7.55, "grava")

# Fila de baixo: caminho atual da decisao
caixa(0.3, 1.2, 3.6, 2.6, "Inferência nebulosa",
      ["volume, previsão,", "ocorrência, faixa horária,", "classe da via", "", "→ nível pretendido"], cinza=True)
caixa(5.2, 0.6, 5.5, 3.9, "Camada de verificação normativa",
      ["1  piso: nível ≥ classe mínima", "2  taxa: decréscimo ≤ 0,1 do pleno/min",
       "3  (proposta) condição adversa no trecho", "    (subseção 6.10 da NBR 5101):",
       "    sobe até a classe da via, na hora;", "    ao fim, desce dentro da taxa",
       "grava a restrição aplicada"], cinza=True)
caixa(12.0, 1.2, 2.7, 2.6, "Nó / telegestão",
      ["comando com", "nível emitido", "e validade"], cinza=True)
seta(3.9, 2.5, 5.2, 2.5, "pretendido", dy=0.12)
seta(10.7, 2.5, 12.0, 2.5, "emitido", dy=0.12)
seta(12.7, 6.3, 8.6, 4.5, tracejada=True)
ax.text(11.3, 5.0, "lida a cada decisão", fontsize=8.2, fontname=F, style="italic")

ax.text(0.3, 0.1, "Tracejado: componentes propostos, não implementados. Cinza: caminho já implementado (3.7). "
        "A inferência não muda.", fontsize=8.2, fontname=F, color="#333")

plt.savefig(sys.argv[1], bbox_inches="tight", facecolor="white")
