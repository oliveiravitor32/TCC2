"""Rodada v66: decisoes dos autores na folha de defesa (blocos 3 e 4, 10/11/2026).

C22: 5.3 sem "cada ponto de luz e decidido isoladamente" (decisao por grupo desde a v62);
C24/C33: citacoes conferidas nos PDFs oficiais (Anexo V p. 20-22; item 5 do Caderno na telegestao);
C5: 5.3 com a resolucao horaria como primeiro motivo, pela Tabela 4 (Zurique, 15 min x 1 h).

    python rev_v66.py pasta_v65   (depois: aceitar.py e zipar2.py)
"""
import sys
from pathlib import Path

import tc
from tc import Doc

tc.DATA = "2026-11-10T12:00:00Z"
d = Doc(str(Path(sys.argv[1]) / "word" / "document.xml"))

d.substituir_paragrafo(
    "Cada ponto de luz é decidido isoladamente",
    "Cada grupo de controle é decidido a partir dos seus próprios trechos: não se contempla o controle "
    "coordenado entre grupos, em que o nível de um ponto considera o dos vizinhos.")

d.trocar("(SÃO PAULO, 2015, Anexo V, p. 20-21)", "p. 20-21", "p. 20-22")
d.trocar("(SÃO PAULO, 2015, itens 7.1.1, 7.1.2 e 7.2.1)", "itens 7.1.1", "itens 5, 7.1.1")

d.substituir_paragrafo(
    "Com a série horária de Melbourne, o modelo de previsão não se mostrou insubstituível",
    "Com a série horária de Melbourne, o modelo de previsão não se mostrou insubstituível no sistema: a média "
    "sazonal do próprio ponto o igualava. A principal razão medida é a resolução da série: com os mesmos dados de "
    "Zurique, a vantagem do modelo sobre a melhor referência simples aparece em 15 min e desaparece quando a série "
    "é somada por hora (4.6, Tabela 4); uma previsão horária muda pouco entre as publicações de volume, que chegam a "
    "cada 5 min. A troca para a série de 15 min de Zurique foi decidida depois do resultado de Melbourne, com o "
    "apoio desse experimento de protocolo prévio (3.6), e é declarada como tal. Contribuem ainda a leitura da "
    "previsão em três faixas pelas regras, a elevação imediata da luz e a regularidade do movimento noturno. Por "
    "fim, o modelo foi treinado para reduzir o erro médio, e não para acertar a faixa que as regras leem; essa "
    "razão é hipótese, não investigada.")

d.salvar()
print("ok")
