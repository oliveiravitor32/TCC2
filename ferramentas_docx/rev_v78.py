"""v78 (13/11/2026, pedido do autor): restos da avaliacao critica, folha de aprovacao, lista de siglas
e linha no Quadro 19.

- Tabela 1: "retomada ao amanhecer" -> "retomada no fim do periodo" (o cenario vai das 18 h as 2 h).
- 2.1: Gerhardt e Silveira (2009) e Wazlawick (2009) como referencia de metodo, fora do recorte.
- Folha de aprovacao depois da folha de rosto (modelo usado pelos colegas do curso).
- Lista de siglas depois da Lista de tabelas, antes do Sumario (NBR 14724). Siglas levantadas por
  varredura do texto inteiro da v77 (corpo e apendices; citacoes, titulos, nomes proprios,
  unidades, codigos de modelo e palavras-chave de SQL excluidos).
- Quadro 19: linha da lista de siglas e da folha de aprovacao (percentual em branco, para os autores).
- Numeracao: a secao do texto comeca com pgNumType start; somado o numero de paginas inseridas.
"""
import re
import sys
from xml.sax.saxutils import escape
sys.path.insert(0, __file__.rsplit("\\", 1)[0].rsplit("/", 1)[0])
from rev_v71_abnt import reescrever, troca, RAIZ

PAGINAS_NOVAS = int(sys.argv[1]) if len(sys.argv) > 1 else 0  # conferido no Word depois

SIGLAS = [
    ("6LoWPAN", "IPv6 over Low-Power Wireless Personal Area Networks"),
    ("ABCIP", "Associação Brasileira das Concessionárias de Iluminação Pública"),
    ("ABNT", "Associação Brasileira de Normas Técnicas"),
    ("ANSI", "American National Standards Institute"),
    ("ARM", "Advanced RISC Machines (arquitetura de processador)"),
    ("AWS", "Amazon Web Services"),
    ("CIE", "Commission Internationale de l'Éclairage"),
    ("CPF", "Cadastro de Pessoas Físicas"),
    ("CSS", "Cascading Style Sheets"),
    ("CT", "Caso de teste"),
    ("EBS", "Amazon Elastic Block Store"),
    ("EC2", "Amazon Elastic Compute Cloud"),
    ("EKS", "Amazon Elastic Kubernetes Service"),
    ("HTML", "HyperText Markup Language"),
    ("HTTP", "Hypertext Transfer Protocol"),
    ("I²C", "Inter-Integrated Circuit"),
    ("IEC", "International Electrotechnical Commission"),
    ("IoT", "Internet of Things (Internet das Coisas)"),
    ("ISO", "International Organization for Standardization"),
    ("JSON", "JavaScript Object Notation"),
    ("LED", "Light-Emitting Diode (diodo emissor de luz)"),
    ("LoRaWAN", "Long Range Wide Area Network"),
    ("MQTT", "Message Queuing Telemetry Transport"),
    ("MSK", "Amazon Managed Streaming for Apache Kafka"),
    ("NB-IoT", "Narrowband Internet of Things"),
    ("NBR", "Norma Brasileira"),
    ("OASIS", "Organization for the Advancement of Structured Information Standards"),
    ("RA", "Registro Acadêmico"),
    ("RDS", "Amazon Relational Database Service"),
    ("REST", "Representational State Transfer"),
    ("RF", "Requisito funcional"),
    ("RNF", "Requisito não funcional"),
    ("SES", "Secretaria Municipal de Serviços"),
    ("SHA", "Secure Hash Algorithm"),
    ("SMSO", "Secretaria Municipal de Serviços e Obras"),
    ("SMSU", "Secretaria Municipal de Segurança Urbana"),
    ("TLS", "Transport Layer Security"),
    ("UNIP", "Universidade Paulista"),
    ("USB", "Universal Serial Bus"),
    ("UUID", "Universally Unique Identifier"),
    ("vCPU", "Virtual Central Processing Unit (processador virtual)"),
    ("WGS 84", "World Geodetic System 1984"),
    ("XML", "Extensible Markup Language"),
]

PT = '<w:lang w:val="pt-BR"/>'
QUEBRA = f'<w:p><w:r><w:rPr>{PT}</w:rPr><w:br w:type="page"/></w:r></w:p>'
VAZIO = '<w:p/>'


def p(texto, jc=None, bold=False, ind=None, spacing=None, keep=False):
    pp = ""
    if keep:
        pp += "<w:keepNext/>"
    if spacing:
        pp += spacing
    if ind:
        pp += f'<w:ind w:left="{ind}"/>'
    if jc:
        pp += f'<w:jc w:val="{jc}"/>'
    b = "<w:b/><w:bCs/>" if bold else ""
    return f'<w:p><w:pPr>{pp}</w:pPr><w:r><w:rPr>{b}{PT}</w:rPr><w:t xml:space="preserve">{escape(texto)}</w:t></w:r></w:p>'


AUTORES = ["BRUNO BONAVIGO DACAL", "LUCAS DE ARAUJO VERGARA", "VITOR OLIVEIRA DOS SANTOS"]
TITULO = ("CONTROLE INTELIGENTE DA ILUMINAÇÃO PÚBLICA A PARTIR DE DADOS URBANOS JÁ EXISTENTES: "
          "PROPOSTA DE INTEGRAÇÃO ENTRE PLATAFORMA DE MONITORAMENTO E TELEGESTÃO NO MUNICÍPIO DE SÃO PAULO")
NATUREZA = ("Trabalho de Conclusão de Curso apresentado ao curso de Bacharelado em Ciência da Computação da "
            "Universidade Paulista – UNIP, como requisito parcial para a obtenção do título de Bacharel em "
            "Ciência da Computação.")
LINHA = "_______________________________________________"


def assinatura(nome):
    return (VAZIO + VAZIO + p(LINHA, "center") + p(nome, "center") + p("Universidade Paulista – UNIP", "center"))


FOLHA = (QUEBRA + "".join(p(a, "center") for a in AUTORES) + VAZIO * 4
         + p(TITULO, "center", bold=True, spacing='<w:spacing w:line="360" w:lineRule="auto"/>') + VAZIO * 2
         + f'<w:p><w:pPr><w:ind w:left="4536"/><w:jc w:val="both"/></w:pPr><w:r><w:rPr>{PT}</w:rPr><w:t>{escape(NATUREZA)}</w:t></w:r></w:p>'
         + VAZIO * 2 + p("Aprovado em: ____/____/________") + VAZIO * 2
         + p("BANCA EXAMINADORA", "center", bold=True)
         + assinatura("Prof. Marco Gomes – Orientador")
         + assinatura("Prof(a). ___________________________________")
         + assinatura("Prof(a). ___________________________________"))

ITEM = ('<w:p><w:pPr><w:tabs><w:tab w:val="left" w:pos="1701"/></w:tabs><w:spacing w:after="60" w:line="360" w:lineRule="auto"/>'
        '<w:ind w:left="1701" w:hanging="1701"/></w:pPr><w:r><w:rPr>{pt}</w:rPr><w:t xml:space="preserve">{s}</w:t></w:r>'
        '<w:r><w:rPr>{pt}</w:rPr><w:tab/><w:t xml:space="preserve">{e}</w:t></w:r></w:p>')
LISTA = (f'<w:p><w:pPr><w:pageBreakBefore/><w:spacing w:after="480"/><w:jc w:val="center"/></w:pPr><w:r><w:rPr><w:b/><w:bCs/>{PT}</w:rPr><w:t>LISTA DE SIGLAS</w:t></w:r></w:p>'
         + "".join(ITEM.format(pt=PT, s=escape(s), e=escape(e)) for s, e in SIGLAS))

T = [
    ("retomada ao amanhecer", "retomada no fim do período"),
    ("nenhuma afirmação sobre o estado da arte da técnica depende de literatura anterior ao recorte.",
     "nenhuma afirmação sobre o estado da arte da técnica depende de literatura anterior ao recorte. Pela mesma razão, "
     "as obras de metodologia de Gerhardt e Silveira (2009) e de Wazlawick (2009) comparecem apenas como referência de "
     "método, na classificação da pesquisa (3.1), e não sustentam afirmação sobre o estado da arte."),
]


def linha_quadro19(s):
    ult = "Montagem do quadro da base de regras"
    tb = next(t for t in re.findall(r"<w:tbl>.*?</w:tbl>", s, re.S) if ult in t)
    base = re.findall(r"<w:tr[ >].*?</w:tr>", tb, re.S)[-1]
    cel = re.findall(r"<w:tc>.*?</w:tc>", base, re.S)
    novos = ["Lista de siglas e folha de aprovação",
             "Levantamento das siglas por varredura do texto completo e redação do significado de cada uma; "
             "folha de aprovação no modelo adotado no curso",
             ""]
    nova = base
    for c, t in zip(cel[2:], novos):
        par = re.search(r"<w:p[ >].*?</w:p>", c, re.S).group(0)
        rpr = re.search(r"<w:rPr>.*?</w:rPr>", re.search(r"<w:r[ >].*?</w:r>", par, re.S).group(0), re.S)
        novo_p = re.sub(r"<w:r[ >].*</w:r>", f'<w:r>{rpr.group(0) if rpr else ""}<w:t xml:space="preserve">{escape(t)}</w:t></w:r>', par, flags=re.S)
        nova = nova.replace(c, c.replace(par, novo_p))
    return troca(s, tb, tb.replace(base, base + nova))


def v78(nome, s):
    if nome != "word/document.xml":
        return None
    for a, b in T:
        s = troca(s, a, b)
    s = linha_quadro19(s)
    corpo = s.index("<w:body>")
    itens = list(re.finditer(r"<w:p[ >].*?</w:p>|<w:tbl>.*?</w:tbl>", s[corpo:], re.S))
    txt = lambda m: re.sub(r"<[^>]+>", "", m.group(0))
    # fim da folha de rosto: o "2026" logo antes da quebra que abre o RESUMO
    i_res = next(k for k, m in enumerate(itens) if txt(m) == "RESUMO")
    fim_rosto = itens[i_res - 2]
    assert txt(fim_rosto) == "2026" and "w:br" in itens[i_res - 1].group(0)
    i_sum = next(k for k, m in enumerate(itens) if txt(m) == "SUMÁRIO")
    sumario = itens[i_sum]
    # os paragrafos vazios entre a Lista de tabelas e o SUMARIO so empurravam a pagina: saem, e o
    # SUMARIO passa a ter quebra antes (pageBreakBefore)
    k = i_sum - 1
    while txt(itens[k]).strip() == "" and "fldChar" not in itens[k].group(0):
        k -= 1
    ini_vazios, fim_sum = corpo + itens[k].end(), corpo + sumario.end()
    sum_xml = sumario.group(0).replace("<w:pPr>", "<w:pPr><w:pageBreakBefore/>", 1)
    s = s[:ini_vazios] + LISTA + sum_xml + s[fim_sum:]
    pos_rosto = corpo + fim_rosto.end()
    s = s[:pos_rosto] + FOLHA + s[pos_rosto:]
    if PAGINAS_NOVAS:
        s = troca(s, '<w:pgNumType w:start="9"/>', f'<w:pgNumType w:start="{9 + PAGINAS_NOVAS}"/>')
    return s


if __name__ == "__main__":
    base = RAIZ + "Transicao_pre-projeto-para-TCC-Completo_TCC_Iluminacao_SP_v"
    reescrever(base + "77.docx", base + "78.docx", v78)
    print("ok")
