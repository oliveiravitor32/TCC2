"""Diagrama de sequencia do percurso de uma decisao (secao 4.6.3)."""
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

FONTE = "Arial"
ATORES = ["Plataforma de\nmonitoramento\n(emulada)", "Interface de\ndados urbanos\n(REST)", "Banco de\ndados",
          "Serviço de\ndecisão", "Intermediário\nMQTT", "Nó de\niluminação", "Painel"]
X = [0.6 + 1.75 * i for i in range(len(ATORES))]
P, I, B, S, M, N, PA = X

fig, ax = plt.subplots(figsize=(12, 12.0), dpi=200)
ax.set_xlim(-0.4, X[-1] + 1.0)
TOPO, BASE = 0.0, -16.9
ax.set_ylim(BASE - 1.0, TOPO + 1.5)
ax.axis("off")

for x, nome in zip(X, ATORES):
    ax.add_patch(Rectangle((x - 0.72, TOPO + 0.15), 1.44, 1.15, fill=True, fc="#f2f2f2", ec="black", lw=1.4))
    ax.text(x, TOPO + 0.72, nome, ha="center", va="center", fontsize=9.5, fontname=FONTE, fontweight="bold")
    ax.plot([x, x], [TOPO + 0.15, BASE], color="black", lw=0.9, ls=(0, (4, 3)))


def seta(y, a, b, texto, tracejada=False):
    ax.annotate("", xy=(b, y), xytext=(a, y),
                arrowprops=dict(arrowstyle="-|>", color="black", lw=1.3, ls="--" if tracejada else "-"))
    ax.text((a + b) / 2, y + 0.13, texto, ha="center", va="bottom", fontsize=8.6, fontname=FONTE,
            bbox=dict(fc="white", ec="none", pad=0.6))


def proprio(y, x, texto):
    ax.add_patch(Rectangle((x - 0.09, y - 0.55), 0.18, 0.7, fc="white", ec="black", lw=1.2))
    ax.text(x + 0.2, y - 0.2, texto, ha="left", va="center", fontsize=8.6, fontname=FONTE,
            bbox=dict(fc="white", ec="none", pad=0.6))


def numero(y, n):
    ax.text(-0.35, y, str(n), ha="center", va="center", fontsize=9, fontname=FONTE, fontweight="bold",
            bbox=dict(boxstyle="circle,pad=0.25", fc="white", ec="black", lw=1.0))


y = -0.9
numero(y, 1); seta(y, P, I, "POST /eventos\nvolume ou ocorrência do trecho")
y -= 1.25
numero(y, 2); seta(y, I, B, "valida e grava\no evento")
y -= 1.05
seta(y, B, S, "notifica o evento", tracejada=True)
y -= 1.25
numero(y, 3); seta(y, S, B, "lê o estado da via, a classe\ndo ponto e o histórico")
y -= 1.25
numero(y, 4); proprio(y + 0.2, S, "previsão → inferência\nnebulosa → verificação\nnormativa (piso)")
y -= 1.45
numero(y, 5); seta(y, S, B, "grava a decisão: nível pretendido,\nnível emitido, restrição e ativações")
y -= 1.45
numero(y, 6); seta(y, S, M, "se o alvo mudou ou vai vencer:\n{decisao_id, nivel, validade_s,\npiso, taxa_min}")
y -= 1.05
seta(y, M, N, "entrega o comando")
y -= 1.25
numero(y, 7); proprio(y + 0.2, N, "rampa até o alvo (taxa);\nnível → ciclo de trabalho\n(calibração); mede\na iluminância")
y -= 1.45
numero(y, 8); seta(y, N, M, "telemetria {decisao_id, duty, lux,\nnivel, nivel_antes, lux_antes}")
y -= 1.05
seta(y, M, S, "entrega a telemetria")
y -= 1.25
numero(y, 9); seta(y, S, B, "grava a telemetria e\natualiza o diagnóstico")
y -= 1.3
numero(y, 10); seta(y, PA, I, "GET /decisoes, /telemetria,\n/eventos/{id}/explicacao")
y -= 1.05
seta(y, I, B, "consulta")
ax.text((X[0] + X[-1]) / 2, BASE - 0.6,
        "Sem evento novo, o serviço só decide de novo quando o comando está para vencer (varredura a cada minuto);\na rampa de descida corre no nó, e o vencimento da validade leva o nó ao pleno.",
        ha="center", va="center", fontsize=9, fontname=FONTE, style="italic")

fig.savefig(sys.argv[1], bbox_inches="tight", pad_inches=0.12, facecolor="white")
print(fig.get_size_inches())
