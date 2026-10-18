"""Rodada v62: grupos de controle implementados, visao de bairro, logs, Quadros 13, 16 e 17,
Figura 10 (ER com grupo_controle) e numero de testes.

    python rev_v62.py pasta_v61 figura_er.png
"""
import sys
from pathlib import Path

from lxml import etree
from PIL import Image

import tc
from tc import Doc, W

tc.DATA = "2026-10-18T22:00:00Z"
PASTA = Path(sys.argv[1])
ER = Path(sys.argv[2])
d = Doc(str(PASTA / "word" / "document.xml"))
R = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}"
WP = "{http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing}"
A = "{http://schemas.openxmlformats.org/drawingml/2006/main}"

# ---------------------------------------------------------------- 3.12.6.1: logs
d.inserir("Ao nó cabe assinar o tópico de comando",
          "as consultas permanecem abertas, porque o painel apenas lê.",
          " A interface e o serviço de decisão registram em log cada publicação aceita ou recusada, as "
          "tentativas sem chave válida, os erros e cada comando emitido, com um identificador de requisição "
          "e o identificador da decisão, que permitem seguir um evento até o comando e a telemetria; o log "
          "não contém chave de acesso nem dado pessoal (RNF08), e o seu tamanho é limitado na máquina virtual.")

# ---------------------------------------------------------------- 3.12.6.3: visao de bairro
tit = d.achar("3.12.6.4 Arquitetura de referência para operação em escala", unico=False)[-1]
corpo = d.achar("As Figuras 8 e 9 completam a visão de monitoramento.")
d.novo_paragrafo(tit,
    "Para a demonstração, o painel oferece também uma visão de bairro: o mapa do recorte do Jardim Helena "
    "(3.5.2) com os 35 postes do cadastro, coloridos pelo nível decidido e pela saúde do ponto, e os trechos de "
    "via coloridos pelo volume vigente ou pela ocorrência aberta. A ocorrência pode ser publicada para vários "
    "trechos de uma vez, sempre como evento da interface, e nunca como comando, de modo que toda decisão continua "
    "a passar pela verificação normativa. Só o nó de bancada é físico; o ponto simulado e os outros 33 postes, "
    "marcados como simulados no banco, respondem por programa, com luz sintética, e não compõem nenhum resultado "
    "do Capítulo 4.", depois=False, modelo=corpo)

# ---------------------------------------------------------------- 3.12.6.4: grupo implementado
d.trocar("A unidade de decisão passa a ser o grupo de controle",
         "o compromisso já registrado em 3.3.",
         "o compromisso já registrado em 3.3. O protótipo já decide assim: o serviço avalia o estado da via, a "
         "previsão e a inferência uma vez por grupo e registra a decisão de cada ponto, ligada ao grupo; um teste "
         "automatizado confere que o resultado é idêntico ao da decisão ponto a ponto, e a suíte de cenários, "
         "executada de novo, produziu os mesmos níveis.")

# ---------------------------------------------------------------- Quadro 13: painel
d.trocar("Exibir o dado recebido, o nível pretendido",
         "na demonstração, publicar volumes e ocorrências de trecho em nome da plataforma emulada",
         "na demonstração, publicar volumes e ocorrências de trecho em nome da plataforma emulada e mostrar o "
         "mapa do bairro")

# ---------------------------------------------------------------- Quadro 16
d.trocar("Identificador; placa do cadastro municipal; coordenadas geográficas e planas",
         "estado operacional; potência plena do segmento",
         "estado operacional; potência plena do segmento; indicador de nó simulado; grupo de controle")
d.trocar("Representa a luminária. Na avaliação, dois registros",
         "cada um representando um poste real do cadastro; o modelo é o do parque",
         "cada um representando um poste real do cadastro; o modelo é o do parque. Na visão de bairro de "
         "3.12.6.3, outros 33 postes do recorte, marcados como simulados, que não entram em resultado")
d.trocar("execução de cenário; entradas da inferência, grau de ativação de cada regra e degrau de classe",
         "grau de ativação de cada regra e degrau de classe",
         "grau de ativação de cada regra e degrau de classe; grupo de controle")
q16 = d.tabela_com("Núcleo do registro de auditoria. Separar o nível pretendido")
d.nova_linha(q16, "Associa trechos a pontos de luz, na relação de muitos para muitos",
             ["grupo_controle", "Chave; classe de iluminação; trechos; instante do cálculo",
              "Grupo de controle (3.12.6.4): pontos associados aos mesmos trechos e da mesma classe, que recebem a "
              "mesma decisão, calculada uma vez"])

# ---------------------------------------------------------------- Quadro 17
d.trocar("estado operacional em {operante, falha, manutenção, sem comunicação}",
         "potência plena do segmento, positiva",
         "potência plena do segmento, positiva; indicador de simulado, falso por padrão; grupo, chave "
         "estrangeira")
d.trocar("régua aprendida, positiva, e instante do cálculo",
         "régua aprendida, positiva, e instante do cálculo",
         "régua aprendida, positiva, e instante do cálculo; linha em WGS84, só para o mapa do painel")
d.trocar("entradas da inferência e ativações das regras, em JSON",
         "entradas da inferência e ativações das regras, em JSON",
         "entradas da inferência e ativações das regras, em JSON; grupo, chave estrangeira opcional")
q17 = d.tabela_com("Pontos de luz afetados por uma leitura e trechos que cada ponto enxerga")
d.nova_linha(q17, "Pontos de luz afetados por uma leitura e trechos que cada ponto enxerga",
             ["grupo_controle", "Identificador; chave única, formada pela classe e pelos trechos ordenados; "
              "classe, chave estrangeira; trechos, vetor; instante do cálculo",
              "Recalculado quando o cadastro muda, nunca durante a operação; cada ponto em um único grupo"])

# ---------------------------------------------------------------- 3.12.9: testes
d.trocar("Os casos automatizados, CT01 a CT14, foram satisfeitos",
         "na execução de 10 de outubro de 2026, com os 262 testes automatizados aprovados.",
         "na execução de 18 de outubro de 2026, com os 281 testes automatizados aprovados.")

# ---------------------------------------------------------------- 5.3: logs na VM
d.trocar("A implantação adotada — uma única máquina virtual da camada gratuita",
         "as cópias de segurança são manuais,",
         "as cópias de segurança são manuais, os logs ficam só nos contêineres, sem centralização,")

d.salvar()

# ---------------------------------------------------------------- Figura 10 (sem marca de revisao)
arv = etree.parse(str(PASTA / "word" / "document.xml"))
corpo_xml = arv.getroot().find(W + "body")
legenda = [p for p in corpo_xml.iter(W + "p")
           if "Diagrama entidade-relacionamento do banco de dados" in "".join(t.text or "" for t in p.iter(W + "t"))][-1]
img = legenda.getnext()
blip = next(img.iter(A + "blip"))
rid = blip.get(R + "embed")
rels = etree.parse(str(PASTA / "word" / "_rels" / "document.xml.rels"))
alvo = next(r.get("Target") for r in rels.getroot() if r.get("Id") == rid)
destino = PASTA / "word" / alvo
Image.open(ER).convert("RGB").save(destino) if destino.suffix.lower() in (".jpg", ".jpeg") else \
    Image.open(ER).save(destino)
w, h = Image.open(ER).size
ext = next(img.iter(WP + "extent"))
cx = int(ext.get("cx"))
cy = int(cx * h / w)
for e in list(img.iter(WP + "extent")) + list(img.iter(A + "ext")):
    e.set("cx", str(cx))
    e.set("cy", str(cy))
arv.write(str(PASTA / "word" / "document.xml"), xml_declaration=True, encoding="UTF-8", standalone=True)
print("ok", alvo)
