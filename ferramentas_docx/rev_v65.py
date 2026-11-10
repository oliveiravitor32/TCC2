"""Rodada v65: figuras conferidas contra a arquitetura (09/11/2026).

Figura 5 regerada com a decisao por grupo de controle (sem marca na imagem); passos (3), (5) e (6) de
3.12.6.3 por grupo; Figura 10 nova = mapa do bairro (captura do painel, demonstracao); ER, foto posterior e
meteorologia passam a 11, 12 e 13 (remissoes e Quadro 19).

    python rev_v65.py pasta_v64 figura5.png mapa.png f6.jpg f7.jpg f8.jpg f9.jpg
"""
import copy
import shutil
import sys
from pathlib import Path

from lxml import etree
from PIL import Image

import tc
from tc import Doc, W, _marca

R = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}"
A = "{http://schemas.openxmlformats.org/drawingml/2006/main}"
WP = "{http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing}"
PIC = "{http://schemas.openxmlformats.org/drawingml/2006/picture}"
PR = "{http://schemas.openxmlformats.org/package/2006/relationships}"

tc.DATA = "2026-11-09T12:00:00Z"
PASTA, FIG5, MAPA = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
FIGS = [Path(x) for x in sys.argv[4:8]]  # capturas das Figuras 6 a 9
d = Doc(str(PASTA / "word" / "document.xml"))
txt = d.texto


def clonar(mod, textos):
    p = copy.deepcopy(mod)
    for b in p.findall(W + "bookmarkStart") + p.findall(W + "bookmarkEnd"):
        p.remove(b)
    for lr in p.iter(W + "lastRenderedPageBreak"):
        lr.getparent().remove(lr)
    ppr = p.find(W + "pPr")
    rpr = ppr.find(W + "rPr")
    if rpr is None:
        rpr = etree.SubElement(ppr, W + "rPr")
    rpr.append(_marca("ins"))
    ts = list(p.iter(W + "t"))
    for t, tx in zip(ts, textos + [""] * len(ts)):
        t.text = tx
        t.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
    for r in [r for r in p if r.tag == W + "r"]:
        ins = _marca("ins")
        r.addprevious(ins)
        ins.append(r)
    return p


def ajustar_altura(img_par, png, largura=None):
    w, h = Image.open(png).size
    for e in img_par.iter(WP + "extent", A + "ext"):
        cx = largura or int(e.get("cx"))
        e.set("cx", str(cx))
        e.set("cy", str(int(cx * h / w)))


pars = list(d.body)


def legenda(num, inicio):
    """Paragrafo da legenda (nao a entrada da lista de figuras): tem um w:t so com o numero."""
    return next(p for p in pars if p.tag == W + "p" and txt(p).startswith(f"Figura {num} – {inicio}")
                and any((t.text or "").strip() == num for t in p.iter(W + "t")))

# ------------------------------------------------ 1. renumerar legendas 10, 11, 12 -> 11, 12, 13 (campo SEQ)
for antigo, novo, inicio in [("12", "13", "Integração meteorológica"), ("11", "12", "Vista posterior"),
                             ("10", "11", "Diagrama entidade-relacionamento")]:
    cap = legenda(antigo, inicio)
    t = next(t for t in cap.iter(W + "t") if (t.text or "").strip() == antigo)
    t.text = novo

# remissoes no texto
d.trocar("A Figura 10 apresenta o modelo de dados", "A Figura 10", "A Figura 11")
d.trocar("A Figura 11 complementa as Figuras 1 e 2", "A Figura 11", "A Figura 12")
d.trocar("conforme o desenho conceitual do Apêndice E (Figura 12)", "(Figura 12)", "(Figura 13)")
d.trocar("A Figura 12 apresenta o desenho.", "A Figura 12", "A Figura 13")
d.trocar("com as entidades do Quadro 16 e o modelo da Figura 10", "Figura 10", "Figura 11")
d.trocar("Figuras 3, 4, 5 e 10", "Figuras 3, 4, 5 e 10", "Figuras 3, 4, 5 e 11")
d.trocar("Figuras 1, 2, 6, 7, 8, 9 e 11", "Figuras 1, 2, 6, 7, 8, 9 e 11", "Figuras 1, 2, 6, 7, 8, 9, 10 e 12")

# ------------------------------------------------ 2. passos da Figura 5 por grupo de controle
d.trocar("(3) Leitura do estado.", "Para cada ponto de luz associado ao trecho (3.5.2), o serviço lê os "
         "volumes vigentes dos trechos do ponto,",
         "Para cada grupo de controle associado ao trecho — os pontos de luz ligados exatamente aos mesmos "
         "trechos (3.5.2 e 3.12.6.4) —, o serviço lê os volumes vigentes dos trechos do grupo,")
d.inserir("(4) Decisão.", "produz o nível-alvo emitido.",
          " O cálculo é feito uma vez por grupo, e todos os pontos do grupo recebem o mesmo nível.")
d.trocar("(5) Registro.", "A decisão é gravada", "A decisão de cada ponto do grupo é gravada")
d.trocar("(6) Comando.", "no tópico do ponto de luz,", "no tópico de cada ponto de luz do grupo,")

# imagem da Figura 5 (sem marca de revisao: o arquivo e trocado, como nas Figuras 4, 5 e 10 da v38)
rels_p = PASTA / "word" / "_rels" / "document.xml.rels"
rels = etree.parse(str(rels_p))
alvo_rel = {e.get("Id"): e.get("Target") for e in rels.getroot()}
cap5 = legenda("5", "Sequência")
img5 = cap5.getnext()
rid5 = next(img5.iter(A + "blip")).get(R + "embed")
shutil.copyfile(FIG5, PASTA / "word" / alvo_rel[rid5])
ajustar_altura(img5, FIG5)

# ------------------------------------------------ 3. Figura 10 nova: mapa do bairro
pb = d.achar("Para a demonstração, o painel oferece também uma visão de bairro")
d.inserir(pb, "e não compõem nenhum resultado do Capítulo 4.",
          " A Figura 10 mostra essa visão em 9 de novembro de 2026, no estado de demonstração: o nó de bancada "
          "aparece sem comunicação porque estava desligado, e os alertas de outros postes simulados foram "
          "provocados para exibir as funções de diagnóstico (3.4.5); o poste das Figuras 6 a 9 não tem alerta.")

# ------------------------------------------------ 3b. Figuras 6 a 9 recapturadas (mesmo poste, mesmo instante)
for num, inicio, arq in [("6", "Painel", FIGS[0]), ("7", "Painel", FIGS[1]), ("8", "Painel", FIGS[2]),
                         ("9", "Painel", FIGS[3])]:
    cap = legenda(num, inicio)
    imgp = cap.getnext()
    rid = next(imgp.iter(A + "blip")).get(R + "embed")
    destino = PASTA / "word" / alvo_rel[rid]
    Image.open(arq).convert("RGB").save(destino, format="JPEG", quality=90)
    ajustar_altura(imgp, arq)

d.substituir_paragrafo(
    "As Figuras 6 e 7 mostram o passo (10) no painel de acompanhamento",
    "As Figuras 6 a 9 mostram o passo (10) no painel de acompanhamento, capturadas em 9 de novembro de 2026, "
    "às 22 h 53 min, para um mesmo ponto de luz e um mesmo instante: o poste de placa IP0598561, na Rua Várzea da "
    "Palma, um dos postes simulados da visão de bairro descrita adiante. O nó de bancada estava desligado na data "
    "da captura. Os volumes são publicados por um gerador de demonstração e a luz é sintética; as figuras ilustram "
    "o painel e não compõem nenhum resultado do Capítulo 4. Na visão de monitoramento (Figura 6), os cartões "
    "percorrem a cadeia da decisão mais recente — volume nulo, nível pretendido de 0,521 pela inferência, emitido "
    "sem correção, acima do piso de 0,500, e luz entregue de 5,77 lx contra 5,21 lx esperados, com o estado do nó "
    "antes do comando —, e o gráfico traz as últimas 24 horas: o nível pretendido, o nível esperado no nó pela "
    "rampa, as medições antes e logo após cada comando e o piso da classe. O ponto fica no pleno enquanto há "
    "movimento, oscila entre 0,75 e 1,0 quando o volume varia e, com a via vazia, desce em degraus e em rampa até "
    "perto do piso, sem ultrapassá-lo; as medições acompanham o nível esperado. Na visão de decisões explicadas "
    "(Figura 7), a publicação de volume nulo no trecho do ponto abre a explicação regra a regra para cada poste "
    "ligado a esse trecho: no ponto da Figura 6, as regras R5, com grau 1,0, e R7, com grau 0,06, levaram ao degrau "
    "1,92 e ao nível de 0,521; no poste vizinho de placa IP0598560, ligado também a um trecho da Rua Ascenso "
    "Fernandes com movimento alto, o maior volume entre os trechos prevaleceu, e as regras R2 e R3 mantiveram o "
    "pleno (3.5.2).")

d.substituir_paragrafo(
    "As Figuras 8 e 9 completam a visão de monitoramento.",
    "As Figuras 8 e 9 completam a visão de monitoramento do mesmo ponto. O cartão de consumo (Figura 8) projeta, "
    "para a luminária de referência de 40 W (Quadro 9), a potência derivada da iluminância medida contra a do "
    "fluxo pleno, com a ressalva, exibida no próprio painel, de que se trata de estimativa e não de medição "
    "elétrica (3.11); na janela de 30 min da captura, o ponto consumiu 11,25 Wh, 56,2 % dos 20,00 Wh do pleno, "
    "com divergência de 7,7 % para a estimativa pelo comando. O registro de decisões (Figura 9) lista, para cada "
    "decisão, os níveis pretendido e emitido, a correção aplicada e a iluminância da telemetria correspondente: "
    "com a via vazia, as decisões a cada 7 min, uma por publicação, baixaram o nível de 0,616 a 0,521, sem "
    "correção. Ao lado, o diagnóstico do ponto, sem alerta aberto, e as publicações recebidas do trecho.")

cap9 = legenda("9", "Painel")
img9 = cap9.getnext()
fonte9 = img9.getnext()

media = PASTA / "word" / "media" / "painel_mapa_bairro.png"
shutil.copyfile(MAPA, media)
etree.SubElement(rels.getroot(), PR + "Relationship", Id="rIdMapa65",
                 Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image",
                 Target="media/painel_mapa_bairro.png")
rels.write(str(rels_p), xml_declaration=True, encoding="UTF-8", standalone=True)
ct_p = PASTA / "[Content_Types].xml"
ct = etree.parse(str(ct_p))
CT = "{http://schemas.openxmlformats.org/package/2006/content-types}"
if not any(e.get("Extension", "").lower() == "png" for e in ct.getroot()):
    etree.SubElement(ct.getroot(), CT + "Default", Extension="png", ContentType="image/png")
    ct.write(str(ct_p), xml_declaration=True, encoding="UTF-8", standalone=True)

img = clonar(img9, [])
ajustar_altura(img, MAPA)
for e in img.iter(WP + "docPr", PIC + "cNvPr"):
    e.set("id", "6501")
    e.set("name", "Figura mapa do bairro")
next(img.iter(A + "blip")).set(R + "embed", "rIdMapa65")

ts9 = [t.text for t in cap9.iter(W + "t")]
num_i = next(i for i, x in enumerate(ts9) if (x or "").strip() == "9")
textos_cap = [""] * len(ts9)
textos_cap[0] = "Figura "
textos_cap[num_i] = "10"
textos_cap[num_i + 1] = " – Painel de acompanhamento: mapa do bairro (demonstração, postes simulados)"
novos = [clonar(cap9, textos_cap), img,
         clonar(fonte9, ["Fonte: Elaborado pelos autores (2026), sobre mapa do OpenStreetMap."])]
ref = pb
for n in novos:
    ref.addnext(n)
    ref = n

d.salvar()
print("ok")
