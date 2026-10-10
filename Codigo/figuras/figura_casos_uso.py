"""Diagrama de casos de uso (3.12.5), a partir dos requisitos funcionais RF01-RF12 (Quadro 10).

    python Codigo/figuras/figura_casos_uso.py saida.png
"""
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Ellipse, FancyArrowPatch, Rectangle

F = "Arial"
fig, ax = plt.subplots(figsize=(12, 9.6), dpi=200)
ax.set_xlim(0, 15)
ax.set_ylim(0, 12)
ax.axis("off")


def ator(x, y, nome):
    ax.add_patch(plt.Circle((x, y + 0.62), 0.17, fill=False, lw=1.5))
    ax.plot([x, x], [y + 0.45, y - 0.05], color="black", lw=1.5)
    ax.plot([x - 0.3, x + 0.3], [y + 0.28, y + 0.28], color="black", lw=1.5)
    ax.plot([x, x - 0.25], [y - 0.05, y - 0.45], color="black", lw=1.5)
    ax.plot([x, x + 0.25], [y - 0.05, y - 0.45], color="black", lw=1.5)
    ax.text(x, y - 0.65, nome, ha="center", va="top", fontsize=9.5, fontname=F, fontweight="bold")
    return x, y + 0.15


def caso(x, y, texto, rf, w=3.5, h=0.82):
    ax.add_patch(Ellipse((x, y), w, h, fc="white", ec="black", lw=1.3))
    ax.text(x, y + 0.08, texto, ha="center", va="center", fontsize=8.8, fontname=F)
    ax.text(x, y - 0.24, rf, ha="center", va="center", fontsize=7.8, fontname=F, color="#444")
    return x, y, w / 2


def assoc(a, c):
    (ax_, ay), (cx, cy, r) = a, c
    lado = -1 if ax_ < cx else 1
    ax.plot([ax_ + (0.3 if lado < 0 else -0.3), cx + lado * r], [ay, cy], color="black", lw=1.0)


def inclui(c1, c2, texto="«include»"):
    (x1, y1, r1), (x2, y2, r2) = c1, c2
    ax.add_patch(FancyArrowPatch((x1, y1 - 0.41 if y2 < y1 else y1 + 0.41),
                                 (x2, y2 + 0.41 if y2 < y1 else y2 - 0.41),
                                 arrowstyle="-|>", mutation_scale=11, lw=0.9, ls=(0, (4, 3)), color="black"))
    ax.text((x1 + x2) / 2 + 0.08, (y1 + y2) / 2, texto, fontsize=7.5, fontname=F, style="italic",
            ha="left", va="center")


# fronteira do sistema
ax.add_patch(Rectangle((2.6, 0.4), 9.8, 11.2, fill=False, lw=1.6))
ax.text(7.5, 11.3, "Sistema de iluminação adaptativa", ha="center", fontsize=11, fontname=F, fontweight="bold")

# casos de uso
publicar = caso(5.0, 10.3, "Publicar volume ou ocorrência", "RF01")
decidir = caso(5.0, 8.5, "Decidir o nível de iluminação", "RF03")
prever = caso(9.9, 9.6, "Prever a demanda", "RF02")
verificar = caso(9.9, 8.2, "Verificar contra a norma", "RF04")
emitir = caso(9.9, 6.8, "Emitir o comando ao nó", "RF05")
registrar = caso(5.0, 6.7, "Registrar a cadeia da decisão", "RF07")
aplicar = caso(9.9, 5.3, "Aplicar o nível e medir a luz", "RF06")
diagnosticar = caso(9.9, 3.8, "Diagnosticar o ponto de luz", "RF11")
acompanhar = caso(5.0, 4.9, "Acompanhar e explicar no painel", "RF08")
energia = caso(5.0, 3.5, "Estimar o consumo de energia", "RF12")
parametros = caso(5.0, 2.1, "Alterar classe e parâmetros", "RF09")
cenarios = caso(9.9, 1.4, "Reproduzir a suíte de cenários", "RF10")

inclui(publicar, decidir, "«include»")
for c in (prever, verificar):
    (x1, y1, r1), (x2, y2, r2) = decidir, c
    ax.add_patch(FancyArrowPatch((x1 + r1, y1), (x2 - r2, y2), arrowstyle="-|>", mutation_scale=11,
                                 lw=0.9, ls=(0, (4, 3)), color="black"))
    ax.text((x1 + r1 + x2 - r2) / 2, (y1 + y2) / 2 + 0.16, "«include»", fontsize=7.5, fontname=F,
            style="italic", ha="center")
inclui(verificar, emitir)
inclui(decidir, registrar)

# atores
plataforma = ator(1.2, 9.9, "Plataforma de\nmonitoramento")
operador = ator(1.2, 4.3, "Operador\nmunicipal")
avaliador = ator(1.2, 0.95, "Avaliador")
no = ator(13.8, 5.6, "Nó de\niluminação")

assoc(plataforma, publicar)
for c in (acompanhar, energia, parametros):
    assoc(operador, c)
assoc(avaliador, cenarios)
for c in (emitir, aplicar, diagnosticar):
    assoc(no, c)

fig.savefig(sys.argv[1], bbox_inches="tight", pad_inches=0.1, facecolor="white")
