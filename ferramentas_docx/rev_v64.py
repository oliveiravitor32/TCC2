"""Rodada v64: recomendacoes do orientador sobre a v60 (03/11/2026).

Termo aditivo do indicador (5.3, 5.4, 6.1); meteorologia com diagrama (5.3, 6.1, Apendice E, Figura 12);
piloto de validacao espacial (3.6, 6.1); token no painel (3.12.6.4, 5.3); particionamento (3.13.1, 6.1,
Apendice F).

    python rev_v64.py pasta_v63 figura_meteorologia.png particionamento.sql
"""
import copy
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

tc.DATA = "2026-11-03T12:00:00Z"
PASTA, FIG, SQL = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
d = Doc(str(PASTA / "word" / "document.xml"))


def clonar(mod, textos):
    """Copia do paragrafo `mod`, marcada como insercao; os w:t recebem `textos` na ordem
    (os que sobram ficam vazios). Mantem campos (SEQ) e formatacao."""
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


def depois(ref, novos):
    for n in novos:
        ref.addnext(n)
        ref = n
    return ref


# ======================================================== 1. Termo aditivo do indicador
d.trocar("O indicador contratual de nível mínimo de iluminância média (2.5) confronta",
         "A adoção em campo depende, portanto, de ajuste contratual ou regulatório sobre esse ponto, não tratado aqui.",
         "A adoção em campo depende, portanto, de ajuste contratual ou regulatório sobre esse ponto; uma proposta "
         "de redação figura em 5.4, sem implementação nem avaliação jurídica.")
p54 = d.achar("Para o município, a principal implicação é que a integração não depende de equipamento novo.")
d.novo_paragrafo(p54,
    "Para o indicador contratual, propõe-se, como ponto de partida a ser avaliado pelo poder concedente e pela "
    "agência reguladora dos serviços públicos municipais, a SP Regula, termo aditivo com a seguinte redação: "
    "“Para ponto de luz operado em regime de iluminação adaptativa, nos termos da subseção 6.10 da ABNT NBR 5101, "
    "a iluminância média aferida para o indicador de nível mínimo de iluminância média será confrontada com o "
    "mínimo da classe vigente no ponto no instante da medição, conforme registro do sistema de telegestão, desde "
    "que essa classe não seja inferior à classe mínima admitida para a via. Na falta de registro da classe "
    "vigente, prevalece o mínimo da classe da via.” A redação é dos autores e não substitui análise jurídica. Seu "
    "efeito é fazer do registro de cada decisão — nível pretendido, nível emitido e restrição aplicada (3.13) — a "
    "referência contra a qual se afere a instalação, registro que o protótipo já produz; e a falta dele recai "
    "sobre a concessionária, pelo lado da classe mais exigente.")

# ======================================================== 2. Meteorologia (Apendice E)
d.inserir("A recomendação da subseção 6.10 da ABNT NBR 5101 de não dimerizar sob nevoeiro",
          "pela separação entre as camadas adaptativa e fixa descrita em 3.7.",
          " O Apêndice E esboça essa integração, sem implementá-la.")
d.trocar("Incorporar dados meteorológicos como terceira restrição",
         "(5.3).", "(5.3), conforme o desenho conceitual do Apêndice E (Figura 12).")

# ======================================================== 3. Piloto de validacao espacial
d.inserir("A substituição da série é declarada e delimitada.",
          "o que converte a limitação em requisito documentado.",
          " Um piloto de validação com amostra de dados do município figura entre as recomendações de 6.1.")
d.novo_paragrafo(d.achar("Retreinar a camada de previsão sobre série municipal publicada"),
    "Conduzir piloto de validação espacial, caso a Prefeitura disponibilize amostra de 30 dias de contagem de "
    "pedestres em vias locais da capital: aplicar o modelo treinado em Zurique, sem retreino, a pontos paulistanos — "
    "a cidade inteira fora do treino —, com a série normalizada pela régua de cada ponto, e comparar o erro e a "
    "faixa de movimentação lida pelas regras com os da persistência e da média sazonal do próprio ponto. Trinta "
    "dias não bastam para treinar modelo local, porque a régua exige 28 dias de dado e um dos atributos é o nível "
    "de 7 dias antes; bastam para medir se a estrutura transferida de Zurique se mantém em São Paulo e, por "
    "reamostragem de dias, com que incerteza (3.6 e 5.3).")

# ======================================================== 4. Token no painel
d.inserir("Painel com acesso controlado.", "e toda alteração fica registrada.",
          " O provedor de identidade entrega ao painel um token de acesso de curta duração, no padrão JSON Web "
          "Token, e a entrada da interface confere, em cada publicação manual, o token e o perfil do usuário, e não "
          "uma chave compartilhada: um token vazado expira em minutos, e a entrada limita o número de publicações "
          "por usuário, o que contém publicações em massa. A plataforma de monitoramento mantém credencial própria, "
          "por sistema, e não por pessoa.")
d.inserir("Na demonstração, a chave com que o painel publica está embutida",
          "A chave é distinta da de integração e é revogada após a defesa.",
          " Na arquitetura de referência, a chave embutida dá lugar a token temporário por usuário (3.12.6.4).")

# ======================================================== 5. Particionamento (Apendice F)
d.inserir("Registre-se o que o modelo não resolve.",
          "O tratamento do crescimento em escala de parque figura entre as recomendações de 6.1.",
          " O Apêndice F apresenta o script de particionamento por data das duas entidades.")
d.trocar("Tratar o crescimento das entidades de evento urbano e de telemetria", "(3.13.1).",
         "(3.13.1 e Apêndice F).")

# ======================================================== 6. Lista de recomendacao do aditivo
d.novo_paragrafo(d.achar("Realizar a integração efetiva com a plataforma municipal e com o sistema de telegestão"),
    "Submeter ao poder concedente e à SP Regula a proposta de termo aditivo que define a classe contra a qual se "
    "afere um ponto de luz dimerizado, a partir da redação de 5.4 (2.5 e 5.3).")

# ======================================================== Apendices E e F
corpo = d.body
pars = list(corpo)
txt = d.texto
cab_d = next(p for p in pars if txt(p).startswith("APÊNDICE D"))
cap_fig = next(p for p in pars if txt(p).endswith("Vista posterior do nó de demonstração") and "Figura" in txt(p))
img_fig = cap_fig.getnext()
fonte_fig = img_fig.getnext()
corpo_mod = next(p for p in pars if txt(p).startswith("Este apêndice estima o custo mensal"))
ultimo = next(p for p in reversed(pars) if p.tag == W + "p" and txt(p).strip())

# imagem nova
media = PASTA / "word" / "media" / "figura_meteorologia.png"
Image.open(FIG).save(media)
rels_p = PASTA / "word" / "_rels" / "document.xml.rels"
rels = etree.parse(str(rels_p))
etree.SubElement(rels.getroot(), PR + "Relationship", Id="rIdMeteo64",
                 Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image",
                 Target="media/figura_meteorologia.png")
rels.write(str(rels_p), xml_declaration=True, encoding="UTF-8", standalone=True)
ct_p = PASTA / "[Content_Types].xml"
ct = etree.parse(str(ct_p))
CT = "{http://schemas.openxmlformats.org/package/2006/content-types}"
if not any(e.get("Extension", "").lower() == "png" for e in ct.getroot()):
    etree.SubElement(ct.getroot(), CT + "Default", Extension="png", ContentType="image/png")
    ct.write(str(ct_p), xml_declaration=True, encoding="UTF-8", standalone=True)

img = clonar(img_fig, [])
largura = 5760000  # 16 cm
w_px, h_px = Image.open(FIG).size
altura = int(largura * h_px / w_px)
for e in img.iter(WP + "extent", A + "ext"):
    e.set("cx", str(largura))
    e.set("cy", str(altura))
for e in img.iter(WP + "docPr", PIC + "cNvPr"):
    e.set("id", "6401")
    e.set("name", "Figura meteorologia")
next(img.iter(A + "blip")).set(R + "embed", "rIdMeteo64")

E = [
    clonar(cab_d, ["APÊNDICE E — INTEGRAÇÃO METEOROLÓGICA PROPOSTA PARA A CAMADA DE VERIFICAÇÃO"]),
    clonar(corpo_mod, [
        "Este apêndice esboça, como proposta dos autores, não implementada nem ensaiada, como a recomendação da "
        "subseção 6.10 da ABNT NBR 5101 de não dimerizar sob nevoeiro, neblina ou chuva poderia ser incorporada "
        "como terceira restrição da camada de verificação (5.3 e 6.1). A Figura 12 apresenta o desenho."]),
    clonar(cap_fig, ["Figura ", "12", " – Integração meteorológica proposta para a camada de verificação"]),
    img,
    clonar(fonte_fig, ["Fonte: Elaborado pelos autores (2026)."]),
    clonar(corpo_mod, [
        "A fonte é a prevista no termo de referência da plataforma de monitoramento: dados de estações climáticas "
        "e do Instituto Nacional de Meteorologia (SÃO PAULO, 2022, Anexo XI). Um adaptador próprio, fora do serviço "
        "de decisão, obtém esses dados por consulta periódica ou por notificação, conforme o que a fonte oferecer — "
        "a forma de acesso não foi verificada —, e os traduz para uma condição adversa por área, com início e "
        "validade, gravada em tabela. A norma não fixa os critérios que caracterizam nevoeiro, neblina ou chuva "
        "intensa; eles teriam de ser definidos com o órgão meteorológico."]),
    clonar(corpo_mod, [
        "A camada de verificação lê a tabela a cada decisão. Com condição adversa vigente no trecho do ponto de "
        "luz, o nível emitido passa a ser o da classe da via: a elevação é imediata, como já admitido em 3.7, e, ao "
        "fim da condição, a descida obedece à taxa de decréscimo. A restrição aplicada é gravada na decisão, como "
        "as demais, e a inferência não é alterada, pela separação entre as camadas adaptativa e fixa (3.7). Se a "
        "fonte deixar de responder, o operador é alertado e valem as duas restrições atuais; a alternativa — "
        "suspender a atenuação enquanto a fonte estiver indisponível — é mais conservadora e gasta mais energia, e "
        "a escolha entre as duas cabe ao município."]),
]

F = [
    clonar(cab_d, ["APÊNDICE F — PARTICIONAMENTO POR DATA DO BANCO DE DADOS"]),
    clonar(corpo_mod, [
        "Este apêndice apresenta o particionamento por data das entidades de evento urbano e de telemetria, que "
        "crescem com o número de pontos e com o tempo (3.13.1 e 6.1). O protótipo não o usa. O script, no "
        "repositório do trabalho (Codigo/db/escala/particionamento.sql), cria versões das duas tabelas "
        "particionadas por mês, ligadas às demais tabelas do protótipo, e foi testado pelos autores em banco "
        "descartável, em PostgreSQL 16, em 3 de novembro de 2026: cada evento foi gravado na partição do seu mês, "
        "a consulta de um dia leu só a partição correspondente, o evento fora das faixas criadas foi para a "
        "partição padrão, e a retirada de um mês foi operação de catálogo, sem apagamento linha a linha."]),
    clonar(corpo_mod, [
        "O particionamento muda o modelo em um ponto. No PostgreSQL, toda chave primária ou única de tabela "
        "particionada contém a coluna de partição: a chave do evento passa a incluir o instante em que ocorreu, e "
        "a associação entre decisão e evento passa a levar esse instante; na telemetria, a unicidade por decisão "
        "passa a incluir o instante da medição, e a relação de um para no máximo um com a decisão (3.13.2) fica a "
        "cargo do serviço. Com a extensão TimescaleDB, citada em 3.12.6.4, a criação das partições e a retenção "
        "são automáticas; essa alternativa está indicada no script, mas não foi testada. O trecho principal do "
        "script é reproduzido a seguir."]),
]

# codigo: um paragrafo por linha, fonte monoespacada
CODIGO = """CREATE TABLE escala.evento_urbano (
    id            BIGINT GENERATED ALWAYS AS IDENTITY,
    ocorrido_em   TIMESTAMPTZ NOT NULL,
    tipo          TEXT NOT NULL CHECK (tipo IN ('volume','ocorrencia')),
    pessoas_media NUMERIC(8,2), periodo_s INTEGER, ocorrencia TEXT,
    origem        TEXT NOT NULL,
    trecho_id     BIGINT NOT NULL REFERENCES public.trecho_via (id),
    vigente_ate   TIMESTAMPTZ,
    -- (demais colunas e restrições como em schema.sql)
    PRIMARY KEY (id, ocorrido_em)
) PARTITION BY RANGE (ocorrido_em);
CREATE INDEX ON escala.evento_urbano (trecho_id, ocorrido_em DESC);

CREATE TABLE escala.telemetria (
    id              BIGINT GENERATED ALWAYS AS IDENTITY,
    decisao_id      UUID NOT NULL REFERENCES public.decisao (id),
    ponto_de_luz_id BIGINT NOT NULL REFERENCES public.ponto_de_luz (id),
    medido_em       TIMESTAMPTZ NOT NULL,
    duty NUMERIC(5,4) NOT NULL, lux_medido NUMERIC(8,2) NOT NULL,
    -- (demais colunas como em schema.sql)
    PRIMARY KEY (id, medido_em),
    UNIQUE (decisao_id, medido_em)
) PARTITION BY RANGE (medido_em);

CREATE TABLE escala.decisao_evento (
    decisao_id         UUID NOT NULL REFERENCES public.decisao (id),
    evento_id          BIGINT NOT NULL,
    evento_ocorrido_em TIMESTAMPTZ NOT NULL,
    PRIMARY KEY (decisao_id, evento_id),
    FOREIGN KEY (evento_id, evento_ocorrido_em)
        REFERENCES escala.evento_urbano (id, ocorrido_em));

-- uma partição por mês, criada adiante (rodar todo mês)
CREATE TABLE escala.evento_urbano_2026_11
    PARTITION OF escala.evento_urbano
    FOR VALUES FROM ('2026-11-01') TO ('2026-12-01');
CREATE TABLE escala.evento_urbano_padrao
    PARTITION OF escala.evento_urbano DEFAULT;

-- retenção: retirar um mês inteiro, depois de exportá-lo
ALTER TABLE escala.evento_urbano
    DETACH PARTITION escala.evento_urbano_2026_09;
DROP TABLE escala.evento_urbano_2026_09;"""


def linha_codigo(texto):
    p = etree.Element(W + "p")
    ppr = etree.SubElement(p, W + "pPr")
    etree.SubElement(ppr, W + "keepLines")
    etree.SubElement(ppr, W + "spacing", {W + "before": "0", W + "after": "0", W + "line": "240",
                                          W + "lineRule": "auto"})
    etree.SubElement(ppr, W + "ind", {W + "firstLine": "0", W + "left": "0"})
    etree.SubElement(ppr, W + "jc", {W + "val": "left"})
    etree.SubElement(ppr, W + "rPr").append(_marca("ins"))
    ins = etree.SubElement(p, W + "ins")
    for k, v in _marca("ins").attrib.items():
        ins.set(k, v)
    r = etree.SubElement(ins, W + "r")
    rpr = etree.SubElement(r, W + "rPr")
    etree.SubElement(rpr, W + "rFonts", {W + "ascii": "Courier New", W + "hAnsi": "Courier New",
                                         W + "cs": "Courier New"})
    etree.SubElement(rpr, W + "sz", {W + "val": "17"})
    etree.SubElement(rpr, W + "szCs", {W + "val": "17"})
    etree.SubElement(rpr, W + "lang", {W + "val": "pt-BR"})
    t = etree.SubElement(r, W + "t")
    t.text = texto if texto else " "
    t.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
    return p


F += [linha_codigo(l) for l in CODIGO.split("\n")]
F.append(clonar(fonte_fig, ["Fonte: Elaborado pelos autores (2026)."]))

depois(ultimo, E + F)
d.salvar()
print("ok")
