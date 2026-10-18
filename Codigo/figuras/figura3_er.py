"""Figura 3 - diagrama entidade-relacionamento (v26), no estilo da original."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

W_BOX, HDR, ROW, PAD = 350, 60, 42, 16
LW = 2.2
FONTE = "Arial"

ENT = {
    "classe_iluminacao": [("PK", "codigo_classe"), ("", "iluminancia_minima"), ("", "ilum_min_dimerizada"),
                          ("FK", "classe_minima_admitida"), ("", "taxa_max_decrescimo")],
    "ponto_de_luz": [("PK", "id_ponto"), ("", "codigo"), ("", "placa"), ("", "latitude / longitude"),
                     ("", "utm_e / utm_n"), ("", "logradouro"), ("FK", "codigo_classe"), ("", "estado_operacional"),
                     ("", "simulado"), ("FK", "id_grupo")],
    "trecho_ponto": [("PK,FK", "id_trecho"), ("PK,FK", "id_ponto"), ("", "distancia_m"), ("", "criterio")],
    "versao_base_regras": [("PK", "id_versao"), ("", "rotulo"), ("", "data_vigencia"), ("", "qtd_regras"),
                           ("", "resumo_alteracoes"), ("", "hash_arquivo")],
    "decisao": [("PK", "id_decisao"), ("", "carimbo_tempo"), ("FK", "id_ponto"), ("", "nivel_pretendido"),
                ("", "nivel_emitido"), ("", "restricao_aplicada"), ("FK", "id_versao"), ("", "entrada (JSON)"),
                ("", "ativacoes (JSON)"), ("", "validade_s"), ("FK", "id_grupo")],
    "telemetria": [("PK", "id_telemetria"), ("", "carimbo_tempo"), ("FK", "id_decisao"), ("FK", "id_ponto"),
                   ("", "ciclo_trabalho"), ("", "iluminancia_medida"), ("", "nivel_aplicado"),
                   ("", "nivel_antes"), ("", "iluminancia_antes")],
    "evento_urbano": [("PK", "id_evento"), ("", "carimbo_tempo"), ("", "tipo"), ("", "pessoas_media"), ("", "periodo_s"), ("", "ocorrencia"),
                      ("FK", "id_trecho"), ("", "origem"), ("", "vigente_ate")],
    "decisao_evento": [("PK,FK", "id_decisao"), ("PK,FK", "id_evento")],
    "grupo_controle": [("PK", "id_grupo"), ("", "chave"), ("FK", "codigo_classe"), ("", "trechos"),
                       ("", "calculado_em")],
    "trecho_via": [("PK", "id_trecho"), ("", "codlog"), ("", "tipo / nome_logradouro"),
                   ("", "numero_inicial / final"), ("", "geometria"), ("", "referencia_pessoas"), ("", "referencia_aprendida"), ("", "referencia_calculada_em")],
}

COL = [25, 485, 945, 1405]
POS = {  # (x, y do topo)
    "classe_iluminacao": (COL[0], 25),
    "ponto_de_luz": (COL[0], 470),
    "trecho_ponto": (COL[0], 1100),
    "versao_base_regras": (COL[1], 25),
    "decisao": (COL[1], 470),
    "telemetria": (COL[1], 1130),
    "evento_urbano": (COL[2], 25),
    "decisao_evento": (COL[2], 1100),
    "grupo_controle": (COL[3], 500),
    "trecho_via": (COL[3], 25),
}


def altura(n):
    return HDR + PAD + n * ROW + PAD // 2


def caixa(nome):
    x, y = POS[nome]
    return x, y, W_BOX, altura(len(ENT[nome]))


LARG = COL[3] + W_BOX + 25
ALT = 1660
fig = plt.figure(figsize=(LARG / 100, ALT / 100), dpi=100)
ax = fig.add_axes([0, 0, 1, 1])
ax.set_xlim(0, LARG)
ax.set_ylim(ALT, 0)
ax.axis("off")

for nome, attrs in ENT.items():
    x, y, w, h = caixa(nome)
    ax.add_patch(Rectangle((x, y), w, HDR, facecolor="#e4e4e4", edgecolor="black", lw=LW))
    ax.add_patch(Rectangle((x, y), w, h, facecolor="none", edgecolor="black", lw=LW))
    ax.text(x + w / 2, y + HDR / 2, nome, ha="center", va="center", fontsize=15, fontweight="bold", family=FONTE)
    for i, (chave, attr) in enumerate(attrs):
        yy = y + HDR + PAD + ROW * i + ROW / 2 - 4
        if chave:
            ax.text(x + 17, yy, chave, ha="left", va="center", fontsize=11.5, color="#444", fontweight="bold", family=FONTE)
        ax.text(x + 100, yy, attr, ha="left", va="center", fontsize=13, family=FONTE,
                fontweight="bold" if "PK" in chave else "normal")


def linha(pts, rotulos):
    xs, ys = zip(*pts)
    ax.plot(xs, ys, color="black", lw=LW, solid_capstyle="butt")
    for (tx, ty, t) in rotulos:
        ax.text(tx, ty, t, ha="center", va="center", fontsize=14, fontweight="bold", family=FONTE)


def base(n):
    x, y, w, h = caixa(n)
    return x + w / 2, y + h


def topo(n):
    x, y, w, h = caixa(n)
    return x + w / 2, y


# classe 1:N ponto
(x1, y1), (x2, y2) = base("classe_iluminacao"), topo("ponto_de_luz")
linha([(x1, y1), (x2, y2)], [(x1 + 25, y1 + 35, "1"), (x1 + 25, y2 - 35, "N")])
# versao 1:N decisao
(x1, y1), (x2, y2) = base("versao_base_regras"), topo("decisao")
linha([(x1, y1), (x2, y2)], [(x1 + 25, y1 + 35, "1"), (x1 + 25, y2 - 35, "N")])
# ponto 1:N trecho_ponto
(x1, y1), (x2, y2) = base("ponto_de_luz"), topo("trecho_ponto")
linha([(x1, y1), (x2, y2)], [(x1 + 25, y1 + 35, "1"), (x1 + 25, y2 - 35, "N")])
# decisao 1:1 telemetria
(x1, y1), (x2, y2) = base("decisao"), topo("telemetria")
linha([(x1, y1), (x2, y2)], [(x1 + 25, y1 + 35, "1"), (x1 + 25, y2 - 35, "0..1")])
# evento 1:N decisao_evento
(x1, y1), (x2, y2) = base("evento_urbano"), topo("decisao_evento")
linha([(x1, y1), (x2, y2)], [(x1 + 25, y1 + 35, "1"), (x1 + 25, y2 - 35, "N")])

# ponto 1:N decisao (horizontal)
px, py, pw, ph = caixa("ponto_de_luz")
dx, dy, dw, dh = caixa("decisao")
yh = py + 150
linha([(px + pw, yh), (dx, yh)], [(px + pw + 30, yh - 22, "1"), (dx - 30, yh - 22, "N")])
# ponto 1:N telemetria (cotovelo pelo corredor entre as colunas)
tx, ty, tw, th = caixa("telemetria")
xc = (px + pw + dx) / 2
y_sai = py + ph - 60
y_ent = ty + th / 2
linha([(px + pw, y_sai), (xc, y_sai), (xc, y_ent), (tx, y_ent)],
      [(px + pw + 18, y_sai - 22, "1"), (tx - 22, y_ent - 22, "N")])
# decisao 1:N decisao_evento
ex, ey, ew, eh = caixa("decisao_evento")
xc2 = (dx + dw + ex) / 2
y_sai = dy + dh - 60
y_ent = ey + eh / 2
linha([(dx + dw, y_sai), (xc2, y_sai), (xc2, y_ent), (ex, y_ent)],
      [(dx + dw + 18, y_sai - 22, "1"), (ex - 22, y_ent - 22, "N")])
# trecho_via 1:N evento_urbano (horizontal)
vx, vy, vw, vh = caixa("trecho_via")
ux, uy, uw, uh = caixa("evento_urbano")
yh = vy + 150
linha([(vx, yh), (ux + uw, yh)], [(vx - 30, yh - 22, "1"), (ux + uw + 30, yh - 22, "N")])
# trecho_via 1:N trecho_ponto (pelo corredor de baixo)
kx, ky, kw, kh = caixa("trecho_ponto")
y_fundo = ALT - 30
xv = vx + vw + 14
y_v = vy + vh - 40
linha([(kx + kw / 2, ky + kh), (kx + kw / 2, y_fundo), (xv, y_fundo), (xv, y_v), (vx + vw, y_v)],
      [(kx + kw / 2 + 25, ky + kh + 30, "N"), (vx + vw - 18, y_v - 22, "1")])

# grupo_controle 1:N decisao (horizontal) e 1:N ponto_de_luz (pelos corredores)
gx, gy, gw, gh = caixa("grupo_controle")
yh = gy + 200
linha([(dx + dw, yh), (gx, yh)], [(dx + dw + 30, yh - 22, "N"), (gx - 30, yh - 22, "1")])
xc0 = (px + pw + dx) / 2
xc1 = (dx + dw + 945) / 2
y0 = py + 60
y_topo = dy - 12
y_ent = gy + 62
linha([(px + pw, y0), (xc0, y0), (xc0, y_topo), (xc1, y_topo), (xc1, y_ent), (gx, y_ent)],
      [(px + pw + 18, y0 - 22, "N"), (gx - 22, y_ent - 22, "1")])

import sys
fig.savefig(sys.argv[1], dpi=100, facecolor="white")
print("ok", LARG, ALT)
