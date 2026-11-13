"""v75 (12/11/2026, decisao do autor): Quadro 19 com a linha do Apendice G (100 %, revisado pelo autor)
e alineas das duas restricoes de 3.7 reiniciadas em a) (continuavam a lista de objetivos: j), k))."""
import re
import sys
sys.path.insert(0, __file__.rsplit("\\", 1)[0].rsplit("/", 1)[0])
from rev_v71_abnt import reescrever, troca, RAIZ

NOVA_LISTA = 90


def v75(nome, s):
    if nome == "word/document.xml":
        # alineas de 3.7
        for ini in ("Piso de iluminância: o nível emitido", "Taxa de variação: a transição entre"):
            p = [m for m in re.findall(r"<w:p[ >].*?</w:p>", s, re.S) if re.sub(r"<[^>]+>", "", m).startswith(ini)]
            assert len(p) == 1 and '<w:numId w:val="3"/>' in p[0], ini
            s = s.replace(p[0], p[0].replace('<w:numId w:val="3"/>', f'<w:numId w:val="{NOVA_LISTA}"/>'))
        # Quadro 19: copia a ultima linha (figuras) e troca os textos
        ult = "Marcações numeradas sobre fotografias feitas pelos autores"
        tb = next(t for t in re.findall(r"<w:tbl>.*?</w:tbl>", s, re.S) if ult in t)
        linhas = re.findall(r"<w:tr[ >].*?</w:tr>", tb, re.S)
        base = linhas[-1]
        cel = re.findall(r"<w:tc>.*?</w:tc>", base, re.S)
        novos = ["Apêndice G (Quadro 22 e Figura 14)",
                 "Montagem do quadro da base de regras a partir do arquivo da base vigente e geração, por script Python, do gráfico de uma noite real a partir de resultados já gravados",
                 "100% — regras, origem de cada uma, escolha da noite e leitura do gráfico revisadas pelos autores"]
        nova = base
        for c, t in zip(cel[2:], novos):
            # mantem o primeiro run (formatacao) e troca todo o texto da celula
            p = re.search(r"<w:p[ >].*?</w:p>", c, re.S).group(0)
            run = re.search(r"<w:r[ >].*?</w:r>", p, re.S).group(0)
            rpr = re.search(r"<w:rPr>.*?</w:rPr>", run, re.S)
            novo_p = re.sub(r"<w:r[ >].*</w:r>", f'<w:r>{rpr.group(0) if rpr else ""}<w:t xml:space="preserve">{t}</w:t></w:r>', p, flags=re.S)
            nova = nova.replace(c, c.replace(p, novo_p))
        s = troca(s, tb, tb.replace(base, base + nova))
        return s
    if nome == "word/numbering.xml":
        assert f'w:numId="{NOVA_LISTA}"' not in s
        num = (f'<w:num w:numId="{NOVA_LISTA}"><w:abstractNumId w:val="2"/>'
               '<w:lvlOverride w:ilvl="0"><w:startOverride w:val="1"/></w:lvlOverride></w:num>')
        i = s.rindex("</w:num>") + len("</w:num>")
        return s[:i] + num + s[i:]
    return None


if __name__ == "__main__":
    base = RAIZ + "Transicao_pre-projeto-para-TCC-Completo_TCC_Iluminacao_SP_v"
    reescrever(base + "74.docx", base + "75.docx", v75)
    print("ok")
