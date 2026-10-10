"""Fotos do no de bancada com marcacoes numeradas e legenda (Docs/Fotos -> Docs/Fotos/marcadas).

    python Codigo/figuras/fotos_marcadas.py

A numeracao e a mesma nas tres fotos. Cada marca: (numero, ponto do objeto, posicao do circulo).
"""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

RAIZ = Path(__file__).resolve().parents[2] / "Docs" / "Fotos"
SAIDA = RAIZ / "marcadas"

NOMES = {
    1: "ESP32 (controlador do nó)",
    2: "Protoboard",
    3: "Módulo MOSFET D4184 (aciona a fita)",
    4: "Sensor de luz BH1750",
    5: "Fita de LED de 12 V (atrás do difusor)",
    6: "Fonte de 12 V da fita",
    7: "Fonte USB do ESP32",
    8: "Caixa de polipropileno",
    9: "Cabo de alimentação da fita",
    10: "Papel difusor da luz da fita",
}

FOTOS = {
    "Hardware_Visao_panoramica.jpeg": [
        (1, (1225, 1040), (1420, 1200)),
        (2, (1290, 880), (1450, 800)),
        (3, (770, 975), (880, 860)),
        (5, (400, 420), (190, 330)),
        (10, (360, 455), (170, 520)),
        (6, (640, 1190), (420, 1330)),
        (7, (820, 1150), (930, 1330)),
        (8, (700, 700), (520, 560)),
    ],
    "Hardware_Visao_panoramica_de_tras_da_caixa.jpeg": [
        (1, (1105, 285), (1230, 150)),
        (3, (1070, 555), (1230, 470)),
        (4, (740, 230), (600, 300)),
        (9, (325, 1010), (180, 1120)),
        (6, (1440, 880), (1260, 1010)),
        (7, (1440, 650), (1260, 650)),
        (8, (500, 600), (330, 480)),
    ],
    "Hardware_Visao_de_cima_da_caixa.jpeg": [
        (4, (160, 780), (330, 760)),
        (5, (1320, 800), (1130, 700)),
        (10, (1290, 960), (1120, 1010)),
        (6, (640, 125), (800, 70)),
        (8, (760, 870), (760, 1050)),
    ],
}


def fonte(tam, negrito=False):
    for nome in (("arialbd.ttf",) if negrito else ("arial.ttf",)):
        try:
            return ImageFont.truetype(nome, tam)
        except OSError:
            pass
    return ImageFont.load_default()


def marcar(arquivo, marcas):
    img = Image.open(RAIZ / arquivo).convert("RGB")
    w, h = img.size
    usados = sorted({n for n, _, _ in marcas})
    linhas = (len(usados) + 1) // 2
    alt_leg = 30 + linhas * 46
    tela = Image.new("RGB", (w, h + alt_leg), "white")
    tela.paste(img, (0, 0))
    d = ImageDraw.Draw(tela)
    r, fnum = 30, fonte(34, True)
    for n, (px, py), (cx, cy) in marcas:
        for cor, larg in (("white", 9), ("black", 4)):
            d.line([(px, py), (cx, cy)], fill=cor, width=larg)
        d.ellipse([px - 9, py - 9, px + 9, py + 9], fill="black", outline="white", width=3)
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill="white", outline="black", width=4)
        d.text((cx, cy), str(n), fill="black", font=fnum, anchor="mm")
    fleg, fnl = fonte(30), fonte(30, True)
    for i, n in enumerate(usados):
        x = 40 + (i % 2) * (w // 2)
        y = h + 22 + (i // 2) * 46
        d.text((x, y), f"{n}", fill="black", font=fnl)
        d.text((x + 58, y), NOMES[n], fill="black", font=fleg)
    SAIDA.mkdir(exist_ok=True)
    destino = SAIDA / arquivo.replace(".jpeg", "_marcada.jpg")
    tela.save(destino, quality=92)
    print(destino)


for arq, marcas in FOTOS.items():
    marcar(arq, marcas)
