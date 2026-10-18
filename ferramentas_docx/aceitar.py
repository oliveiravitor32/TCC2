"""Aceita todas as revisoes (w:ins/w:del) de um document.xml.

    python aceitar.py pasta/word/document.xml
"""
import sys

from lxml import etree

W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
arv = etree.parse(sys.argv[1])
raiz = arv.getroot()

# 1) linhas de tabela deletadas
for tr in list(raiz.iter(W + "tr")):
    trpr = tr.find(W + "trPr")
    if trpr is not None and trpr.find(W + "del") is not None:
        tr.getparent().remove(tr)
# 2) marcas de paragrafo deletadas: junta com o seguinte
for p in list(raiz.iter(W + "p")):
    rpr = p.find(f"{W}pPr/{W}rPr")
    if rpr is not None and rpr.find(W + "del") is not None:
        seg = p.getnext()
        if seg is not None and seg.tag == W + "p":
            pos = 1 if seg.find(W + "pPr") is not None else 0
            for filho in [c for c in p if c.tag != W + "pPr"][::-1]:
                seg.insert(pos, filho)
            p.getparent().remove(p)
        else:
            rpr.remove(rpr.find(W + "del"))
# 3) conteudo deletado some
for d in list(raiz.iter(W + "del")):
    d.getparent().remove(d)
# 4) insercoes viram texto normal; marcas em rPr/trPr somem
for i in list(raiz.iter(W + "ins")):
    pai = i.getparent()
    if pai.tag in (W + "rPr", W + "trPr"):
        pai.remove(i)
        continue
    pos = pai.index(i)
    for filho in list(i)[::-1]:
        pai.insert(pos, filho)
    pai.remove(i)
arv.write(sys.argv[1], xml_declaration=True, encoding="UTF-8", standalone=True)
print("aceito")
