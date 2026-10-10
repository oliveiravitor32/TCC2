"""Figura 1 - arquitetura do sistema (4.6), conforme a implantacao vigente."""
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Rectangle

F = "Arial"
fig, ax = plt.subplots(figsize=(6.6, 7.6), dpi=300)
ax.set_xlim(0, 12); ax.set_ylim(0, 14.2); ax.axis("off")


def caixa(x, y, w, h, titulo, sub):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0,rounding_size=0.15",
                                fc="white", ec="black", lw=1.4))
    ax.text(x + w / 2, y + h * 0.66, titulo, ha="center", va="center", fontsize=8.6, fontname=F, fontweight="bold")
    ax.text(x + w / 2, y + h * 0.27, sub, ha="center", va="center", fontsize=7.0, fontname=F, color="#222")


def seta(x1, y1, x2, y2, txt="", dx=0.15, ha="left", tracejada=False):
    ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle="-|>", color="black", lw=1.2, ls="--" if tracejada else "-"))
    if txt:
        ax.text((x1 + x2) / 2 + dx, (y1 + y2) / 2, txt, ha=ha, va="center", fontsize=7.2, fontname=F)


# nuvem
ax.add_patch(Rectangle((0.3, 4.55), 11.4, 9.4, fc="#f5f5f5", ec="#444", lw=1.3, ls=(0, (5, 3))))
ax.text(0.55, 13.6, "NUVEM — máquina virtual com contêineres", fontsize=8.6, fontname=F, fontweight="bold", color="#333")
W, X0 = 6.1, 0.65
caixa(X0, 11.75, W, 1.35, "Interface de dados urbanos", "REST / HTTP — emula a plataforma municipal")
caixa(X0, 9.45, W, 1.35, "Serviço de decisão", "previsão + inferência nebulosa (Mamdani)")
caixa(X0, 7.15, W, 1.35, "Camada de verificação normativa", "piso da classe (ABNT NBR 5101)")
caixa(X0, 5.0, W, 1.15, "Intermediário de mensagens MQTT", "TLS, credencial e tópico por nó")
caixa(7.55, 9.45, 3.2, 1.35, "Banco de dados", "PostgreSQL em contêiner")
seta(X0 + W / 2, 11.75, X0 + W / 2, 10.8, "estado da via")
seta(X0 + W / 2, 9.45, X0 + W / 2, 8.5, "nível pretendido")
seta(X0 + W / 2, 7.15, X0 + W / 2, 6.15, "nível-alvo, validade,\npiso e taxa")
# registro de auditoria
xa = X0 + W + 0.25
for yy in (12.42, 10.12, 7.82, 5.57):
    ax.plot([X0 + W, xa], [yy, yy], color="black", lw=1.1, ls=(0, (3, 2)))
ax.plot([xa, xa], [5.57, 12.42], color="black", lw=1.1, ls=(0, (3, 2)))
seta(xa, 10.12, 7.55, 10.12, tracejada=True)
ax.text(9.15, 11.15, "registro de auditoria", ha="center", fontsize=7.2, fontname=F, style="italic")

# painel fora da VM
ax.add_patch(Rectangle((7.4, 0.3), 4.3, 2.75, fc="white", ec="#444", lw=1.3, ls=(0, (5, 3))))
ax.text(7.6, 2.75, "HOSPEDAGEM DE FRONT END", fontsize=7.0, fontname=F, fontweight="bold", color="#333")
caixa(7.65, 0.55, 3.2, 1.75, "Painel web", "consulta a REST; publica\nem nome da plataforma")
ax.plot([10.85, 11.25, 11.25, 7.2], [1.45, 1.45, 12.9, 12.9], color="black", lw=1.1)
ax.annotate("", xy=(X0 + W, 12.9), xytext=(7.2, 12.9), arrowprops=dict(arrowstyle="-|>", color="black", lw=1.1))
ax.annotate("", xy=(10.85, 1.45), xytext=(11.25, 1.45), arrowprops=dict(arrowstyle="-|>", color="black", lw=1.1))
ax.text(11.35, 7.5, "REST", fontsize=7.2, fontname=F, rotation=90, va="center")

# ambiente fisico
ax.add_patch(Rectangle((0.3, 0.3), 6.85, 2.75, fc="white", ec="#444", lw=1.3))
ax.text(0.5, 2.75, "AMBIENTE FÍSICO — bancada", fontsize=7.6, fontname=F, fontweight="bold", color="#333")
ax.add_patch(FancyBboxPatch((0.55, 0.5), 6.35, 1.95, boxstyle="round,pad=0,rounding_size=0.15",
                            fc="white", ec="black", lw=1.4))
ax.text(3.72, 2.08, "Nó de iluminação — ESP32", ha="center", fontsize=8.6, fontname=F, fontweight="bold")
ax.text(3.72, 1.45, "rampa até o alvo, sem exceder a taxa nem descer do piso;\nvencida a validade, nível pleno",
        ha="center", va="center", fontsize=6.2, fontname=F)
ax.text(3.72, 0.78, "PWM → módulo MOSFET → fita de LED  •  BH1750 → iluminância",
        ha="center", va="center", fontsize=6.2, fontname=F)
seta(5.3, 5.0, 5.3, 2.45, "comando\n(tópico assinado)", dx=-0.15, ha="right")
seta(6.3, 2.45, 6.3, 5.0, "telemetria\n(tópico publicado)", dx=0.12)

fig.savefig(sys.argv[1], bbox_inches="tight", pad_inches=0.08, facecolor="white")
