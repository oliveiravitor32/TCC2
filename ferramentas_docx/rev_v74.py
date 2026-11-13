"""v74: avaliacao critica (12/11/2026), itens 10 e 11 (decisao do autor).

Apendice G novo, no fim (para nao renumerar quadros e figuras): Quadro 22 com as sete regras
da base vigente (decisao/regras/v6-zurique.toml) e Figura 14 com uma noite real de Zurique
(Codigo/figuras/figura_noite_real.py). Remissoes em 3.7 e na analise de energia.
"""
import sys
from xml.sax.saxutils import escape
sys.path.insert(0, __file__.rsplit("\\", 1)[0].rsplit("/", 1)[0])
from rev_v71_abnt import reescrever, troca, RAIZ

IMG = RAIZ + "Docs/Figuras/figura_noite_real.png"
RID = "rId90"
CX, CY = 5760000, 3993600  # 16 cm, proporcao 1500 x 1040

PT = '<w:lang w:val="pt-BR"/>'
R10 = f'<w:sz w:val="20"/><w:szCs w:val="20"/>{PT}'


def par(t):
    return ('<w:p><w:pPr><w:spacing w:after="120" w:line="360" w:lineRule="auto"/><w:ind w:firstLine="709"/>'
            f'<w:jc w:val="both"/></w:pPr><w:r><w:rPr>{PT}</w:rPr><w:t xml:space="preserve">{escape(t)}</w:t></w:r></w:p>')


def legenda(rot, num, t, centro):
    r = lambda x: f'<w:r><w:rPr>{R10}</w:rPr>{x}</w:r>'
    pp = ('<w:keepNext/><w:spacing w:before="130" w:after="60"/><w:jc w:val="center"/>' if centro
          else '<w:keepNext/><w:spacing w:before="260" w:after="130"/>')
    return (f'<w:p><w:pPr>{pp}</w:pPr>' + r(f'<w:t xml:space="preserve">{rot} </w:t>')
            + r('<w:fldChar w:fldCharType="begin"/>') + r(f'<w:instrText xml:space="preserve"> SEQ {rot} \\* ARABIC </w:instrText>')
            + r('<w:fldChar w:fldCharType="separate"/>') + r(f'<w:t>{num}</w:t>') + r('<w:fldChar w:fldCharType="end"/>')
            + r(f'<w:t xml:space="preserve"> – {escape(t)}</w:t>') + '</w:p>')


def fonte(t, centro):
    jc = '<w:jc w:val="center"/>' if centro else ''
    sp = '<w:spacing w:after="280"/>' if centro else '<w:spacing w:before="130" w:after="260"/>'
    return f'<w:p><w:pPr>{sp}{jc}</w:pPr><w:r><w:rPr>{R10}</w:rPr><w:t>{escape(t)}</w:t></w:r></w:p>'


LARG = [850, 2950, 1450, 3821]
MAR = '<w:tcMar><w:top w:w="60" w:type="dxa"/><w:left w:w="80" w:type="dxa"/><w:bottom w:w="60" w:type="dxa"/><w:right w:w="80" w:type="dxa"/></w:tcMar>'


def linha(cels, cab=False):
    tr = '<w:tr>' + ('<w:trPr><w:cantSplit/><w:tblHeader/></w:trPr>' if cab else '<w:trPr><w:cantSplit/></w:trPr>')
    for w, c in zip(LARG, cels):
        shd = '<w:shd w:val="clear" w:color="auto" w:fill="EDEDED"/>' if cab else ''
        b = '<w:b/><w:bCs/>' if cab else ''
        tr += (f'<w:tc><w:tcPr><w:tcW w:w="{w}" w:type="dxa"/>{shd}{MAR}</w:tcPr><w:p><w:r><w:rPr>{b}{R10}</w:rPr>'
               f'<w:t xml:space="preserve">{escape(c)}</w:t></w:r></w:p></w:tc>')
    return tr + '</w:tr>'


REGRAS = [
    ("R1", "Ocorrência reportada = sim", "Classe da via", "Domínio: a ocorrência reportada justifica a elevação, independentemente da movimentação (Quadro 7)"),
    ("R2", "Observada = alta", "Classe da via", "Norma: a classe da via corresponde à atividade de pedestres para a qual foi selecionada (ABNT NBR 5101, 6.10.3)"),
    ("R3", "Prevista = alta", "Classe da via", "Literatura: antecipação da demanda (2.7; BELLONI et al., 2024)"),
    ("R4", "Ocorrência = não e observada = média", "Uma classe abaixo", "Norma: atividade menor admite classe inferior (ABNT NBR 5101, 6.10.2 e 6.10.3)"),
    ("R5", "Ocorrência = não, observada = baixa e prevista = baixa", "Classe mínima", "Norma: reduzir nos horários de baixa movimentação (ABNT NBR 5101, 6.3 e 6.10.3)"),
    ("R6", "Ocorrência = não, observada = baixa e prevista = média", "Uma classe abaixo", "Literatura: antecipação da demanda (2.7; BELLONI et al., 2024)"),
    ("R7", "Ocorrência = não, observada = baixa e faixa horária = início da noite", "Uma classe abaixo", "Domínio: faixa horária como evidência de apoio (Quadro 7)"),
]

BORDA = ''.join(f'<w:{b} w:val="single" w:sz="4" w:space="0" w:color="auto"/>' for b in ("top", "left", "bottom", "right", "insideH", "insideV"))
TABELA = (f'<w:tbl><w:tblPr><w:tblW w:w="9071" w:type="dxa"/><w:tblBorders>{BORDA}</w:tblBorders>'
          '<w:tblLayout w:type="fixed"/><w:tblCellMar><w:left w:w="10" w:type="dxa"/><w:right w:w="10" w:type="dxa"/></w:tblCellMar>'
          '<w:tblLook w:val="04A0" w:firstRow="1" w:lastRow="0" w:firstColumn="1" w:lastColumn="0" w:noHBand="0" w:noVBand="1"/></w:tblPr><w:tblGrid>'
          + ''.join(f'<w:gridCol w:w="{w}"/>' for w in LARG) + '</w:tblGrid>'
          + linha(["Regra", "Se", "Então", "Origem"], True) + ''.join(linha(r) for r in REGRAS) + '</w:tbl>')

IMAGEM = ('<w:p><w:pPr><w:keepNext/><w:spacing w:before="240"/><w:jc w:val="center"/></w:pPr><w:r><w:rPr><w:noProof/></w:rPr><w:drawing>'
          f'<wp:inline distT="0" distB="0" distL="0" distR="0"><wp:extent cx="{CX}" cy="{CY}"/><wp:effectExtent l="0" t="0" r="0" b="0"/>'
          '<wp:docPr id="6601" name="Figura noite real"/><wp:cNvGraphicFramePr><a:graphicFrameLocks xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" noChangeAspect="1"/></wp:cNvGraphicFramePr>'
          '<a:graphic xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"><a:graphicData uri="http://schemas.openxmlformats.org/drawingml/2006/picture">'
          '<pic:pic xmlns:pic="http://schemas.openxmlformats.org/drawingml/2006/picture"><pic:nvPicPr><pic:cNvPr id="6601" name="Figura noite real"/><pic:cNvPicPr/></pic:nvPicPr>'
          f'<pic:blipFill><a:blip r:embed="{RID}"/><a:stretch><a:fillRect/></a:stretch></pic:blipFill><pic:spPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="{CX}" cy="{CY}"/></a:xfrm>'
          '<a:prstGeom prst="rect"><a:avLst/></a:prstGeom></pic:spPr></pic:pic></a:graphicData></a:graphic></wp:inline></w:drawing></w:r></w:p>')

APENDICE = (
    '<w:p><w:pPr><w:pStyle w:val="Heading1"/><w:pageBreakBefore/><w:spacing w:before="480" w:after="280" w:line="360" w:lineRule="auto"/>'
    f'<w:jc w:val="center"/></w:pPr><w:r><w:rPr>{PT}</w:rPr><w:t>APÊNDICE G — BASE DE REGRAS E TRAJETÓRIA DE UMA NOITE REAL</w:t></w:r></w:p>'
    + par("Este apêndice reúne em quadro a base de regras descrita em 3.7 e mostra em figura uma das noites reais da avaliação de 4.6. "
          "No Quadro 22, as movimentações observada e prevista são classificadas em baixa, média e alta por conjuntos trapezoidais com "
          "fronteiras nos tercis do nível normalizado por trecho (3.7); as regras são ligadas por E, e a saída é o degrau de classe, "
          "convertido em fração do pleno pelas classes lidas do banco (Quadro 8).")
    + legenda("Quadro", 22, "Base de regras vigente da inferência nebulosa", False)
    + TABELA
    + fonte("Fonte: Elaborado pelos autores (2026), base v6-zurique do repositório do trabalho.", False)
    + par("A Figura 14 mostra a noite do ponto 1358 de Zurique, do grupo mais movimentado, num dia útil (30 de julho de 2019), das 18 h às 6 h, "
          "no modo em operação, com a previsão e a inferência nebulosa. Na parte superior está o volume observado, normalizado, com os tercis "
          "que separam as faixas de movimentação; na inferior, o nível emitido pelo regime adaptativo, o do horário fixo, calculado pela mesma "
          "função da avaliação, o fluxo pleno e o piso da classe mínima. Até a meia-noite, com o volume entre os dois tercis, o regime adaptativo "
          "ficou, após a descida inicial, uma classe abaixo da via; das 0 h às 5 h, com o volume abaixo do tercil inferior, os dois regimes "
          "ficaram no piso; depois das 5 h, o horário fixo voltou ao pleno e o adaptativo, a uma classe abaixo. Nessa noite, o regime "
          "adaptativo consumiu 64,3 % do fluxo pleno e 81,1 % do horário fixo.")
    + legenda("Figura", 14, "Noite real de Zurique com os três regimes", True)
    + IMAGEM
    + fonte("Fonte: Elaborado pelos autores (2026) a partir dos resultados da avaliação de 4.6.", True)
)


def v74(nome, s):
    if nome == "word/document.xml":
        s = troca(s, "o que permite explicá-la regra a regra.",
                  "o que permite explicá-la regra a regra. O Quadro 22, no Apêndice G, reúne as sete regras com a origem de cada uma.")
        s = troca(s, "o regime adaptativo consome 62,4 % do fluxo pleno e 78,6 % do horário fixo.",
                  "o regime adaptativo consome 62,4 % do fluxo pleno e 78,6 % do horário fixo; a Figura 14, no Apêndice G, mostra uma dessas noites.")
        i = s.rindex("<w:sectPr")
        return s[:i] + APENDICE + s[i:]
    if nome == "word/_rels/document.xml.rels":
        assert RID not in s
        return s.replace("</Relationships>", f'<Relationship Id="{RID}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="media/noite_real.png"/></Relationships>')
    return None


if __name__ == "__main__":
    import zipfile
    base = RAIZ + "Transicao_pre-projeto-para-TCC-Completo_TCC_Iluminacao_SP_v"
    reescrever(base + "73.docx", base + "74.docx", v74)
    # reescrever so edita *.xml: a relacao da imagem (.rels) e a imagem entram aqui
    tmp = base + "74.tmp"
    zin = zipfile.ZipFile(base + "74.docx")
    with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as z:
        for i in zin.infolist():
            d = zin.read(i.filename)
            if i.filename == "word/_rels/document.xml.rels":
                d = v74(i.filename, d.decode("utf-8")).encode("utf-8")
            z.writestr(i, d)
        z.write(IMG, "word/media/noite_real.png")
    zin.close()
    import os
    os.replace(tmp, base + "74.docx")
    print("ok")
