"""Rodada v68: Apendice A atualizado ao trabalho feito depois de 10/10/2026 (10/11/2026, decisao do autor).

a) periodo de uso ate 10/11/2026; b) Figura 13 na linha dos diagramas; c) Apendices E e F na linha da
arquitetura de referencia; d) linha nova para o termo aditivo (percentual em branco, os autores preenchem).

    python rev_v68.py pasta_v67   (depois: aceitar.py e zipar2.py)
"""
import sys
from pathlib import Path

import tc
from tc import Doc

tc.DATA = "2026-11-10T12:00:00Z"
d = Doc(str(Path(sys.argv[1]) / "word" / "document.xml"))

d.trocar("no período de 13/09/2026 a 10/10/2026", "a 10/10/2026", "a 10/11/2026")

q = d.tabela_com("Geração dos diagramas de casos de uso")
d.trocar(d.linha_com(q, "Geração dos diagramas").findall(tc.W + "tc")[2].find(tc.W + "p"),
         "Figuras 3, 4, 5 e 11", "Figuras 3, 4, 5, 11 e 13")

lin = d.linha_com(q, "Proposta de arquitetura de referência")
cel = lin.findall(tc.W + "tc")
d.trocar(cel[2].find(tc.W + "p"), "3.12.6.4 e Apêndice D", "3.12.6.4 e Apêndices D, E e F")
d.trocar(cel[3].find(tc.W + "p"), "Proposta de arquitetura de referência e estimativa de custo",
         "Proposta de arquitetura de referência, com os grupos de controle, da integração meteorológica e do "
         "particionamento das tabelas (este testado em banco descartável), e estimativa de custo")

d.nova_linha(q, "Proposta de arquitetura de referência",
             ["Claude Opus 5 e Claude Opus 5.5 (Anthropic)",
              "claude-opus-5 e claude-opus-5-5, pela ferramenta Claude Code",
              "5.3, 5.4 e 6.1",
              "Redação da proposta de termo aditivo do indicador de iluminância e das limitações e recomendações "
              "acrescentadas, a partir de recomendação do orientador; citações conferidas nos documentos "
              "contratuais",
              "____% — a preencher pelos autores"])

d.salvar()
print("ok")
