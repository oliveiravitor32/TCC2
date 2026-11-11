"""v71 (ABNT) do TCC e ajustes ABNT do Entregavel 2 v2, direto no XML.

TCC:  Tabelas 1-4 abertas nas laterais; Titulo 3 sem negrito; Titulo 4 em italico.
Ent2: REFERENCIAS centralizado; citacoes autor-data; Tabelas 1-3 abertas nas
      laterais; numero de pagina conta a partir da folha de rosto (PAGE - 1).
"""
import re
import sys
import zipfile

RAIZ = "C:/Users/vitor/Documents/GitHub/TCC2/"


def reescrever(orig, dest, mudar):
    zin = zipfile.ZipFile(orig)
    itens = [(i, zin.read(i.filename)) for i in zin.infolist()]
    zin.close()
    out = zipfile.ZipFile(dest, "w", zipfile.ZIP_DEFLATED)
    for i, d in itens:
        novo = mudar(i.filename, d.decode("utf-8")) if i.filename.endswith(".xml") else None
        out.writestr(i, novo.encode("utf-8") if novo is not None else d)
    out.close()


def abrir_laterais(doc):
    """Bordas left/right = nil nas tabelas cuja legenda (paragrafo anterior) comeca com 'Tabela'."""
    partes = re.split(r"(<w:tbl>.*?</w:tbl>)", doc, flags=re.S)
    n, ultimo = 0, ""
    for k, pt in enumerate(partes):
        if pt.startswith("<w:tbl>"):
            if ultimo.startswith("Tabela"):
                partes[k] = re.sub(r'<w:(left|right|start|end) w:val="[^"]*"[^/]*/>',
                                   lambda m: f'<w:{m.group(1)} w:val="nil"/>', pt)
                n += 1
        else:
            ps = [re.sub(r"<[^>]+>", "", p).strip() for p in re.findall(r"<w:p[ >].*?</w:p>", pt, re.S)]
            ps = [p for p in ps if p]
            if ps:
                ultimo = ps[-1]
    print("tabelas abertas:", n)
    return "".join(partes)


def troca(s, a, b, n=1):
    assert s.count(a) == n, (s.count(a), a[:60])
    return s.replace(a, b)


def tcc(nome, s):
    if nome == "word/document.xml":
        return abrir_laterais(s)
    if nome == "word/styles.xml":
        s = troca(s, '<w:outlineLvl w:val="2"/></w:pPr><w:rPr><w:b/><w:bCs/></w:rPr>',
                  '<w:outlineLvl w:val="2"/></w:pPr><w:rPr><w:b w:val="0"/><w:bCs w:val="0"/></w:rPr>')
        s = troca(s, '<w:outlineLvl w:val="3"/></w:pPr><w:rPr><w:b/><w:bCs/></w:rPr>',
                  '<w:outlineLvl w:val="3"/></w:pPr><w:rPr><w:b w:val="0"/><w:bCs w:val="0"/><w:i/><w:iCs/></w:rPr>')
        return s
    return None


CIT = [
    ("cadastro público GeoSampa", "cadastro público GeoSampa (SÃO PAULO, 2026)"),
    ("classes P3 a P5 da ABNT NBR 5101", "classes P3 a P5 da ABNT NBR 5101 (ASSOCIAÇÃO BRASILEIRA DE NORMAS TÉCNICAS, 2024)"),
    ("definidos pelo Caderno de Encargos da concessão", "definidos pelo Caderno de Encargos da concessão (SÃO PAULO, 2015)"),
    ("portal de dados abertos da Stadt Zürich, licença CC0", "portal de dados abertos da Stadt Zürich, licença CC0; STADT ZÜRICH, 2026"),
    ("(City of Melbourne Open Data)", "(CITY OF MELBOURNE, 2026)"),
    ("(XGBoost, Chen e Guestrin, 2016)", "XGBoost (CHEN; GUESTRIN, 2016)"),
]


def ent(nome, s):
    if nome == "word/document.xml":
        for a, b in CIT:
            s = troca(s, a, b)
        # "arvores de decisao XGBoost (...)": virgula antes do nome
        s = troca(s, "árvores de decisão XGBoost (CHEN", "árvores de decisão, XGBoost (CHEN")
        # REFERENCIAS (o titulo, nao a entrada do sumario): centralizar
        m = [p for p in re.findall(r"<w:p[ >].*?</w:p>", s, re.S)
             if re.sub(r"<[^>]+>", "", p).strip() == "REFERÊNCIAS" and "Heading1" in p]
        assert len(m) == 1
        p = m[0]
        q = re.sub(r'<w:jc w:val="\w+"/>', "", p)
        q = q.replace('<w:pStyle w:val="Heading1"/>', '<w:pStyle w:val="Heading1"/><w:jc w:val="center"/>', 1)
        s = s.replace(p, q)
        return abrir_laterais(s)
    if nome.startswith("word/header"):
        # PAGE -> = PAGE - 1 (a capa nao conta; a contagem comeca na folha de rosto)
        if "<w:instrText>PAGE</w:instrText>" in s:
            rp = '<w:rPr><w:sz w:val="20"/><w:szCs w:val="20"/></w:rPr>'
            antigo = re.search(r'<w:r><w:rPr><w:sz w:val="20"/><w:szCs w:val="20"/></w:rPr><w:fldChar w:fldCharType="begin"/></w:r>.*?<w:fldChar w:fldCharType="end"/></w:r>', s, re.S).group(0)
            fc = lambda t: f'<w:r>{rp}<w:fldChar w:fldCharType="{t}"/></w:r>'
            it = lambda t: f'<w:r>{rp}<w:instrText xml:space="preserve">{t}</w:instrText></w:r>'
            novo = (fc("begin") + it(" = ") + fc("begin") + it(" PAGE ") + fc("separate")
                    + f'<w:r>{rp}<w:t>2</w:t></w:r>' + fc("end") + it(" - 1 ") + fc("separate")
                    + f'<w:r>{rp}<w:t>1</w:t></w:r>' + fc("end"))
            return s.replace(antigo, novo)
    return None


if __name__ == "__main__":
    base = RAIZ + "Transicao_pre-projeto-para-TCC-Completo_TCC_Iluminacao_SP_v"
    reescrever(base + "70.docx", base + "71.docx", tcc)
    e = RAIZ + "Docs/Entregavel2/Entregavel2_Guia_do_Usuario_e_Manual_de_Operacao_v2.docx"
    tmp = e + ".tmp"
    reescrever(e, tmp, ent)
    import os
    os.replace(tmp, e)
    print("ok")
