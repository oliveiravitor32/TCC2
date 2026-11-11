"""Rodada v69: leitura guiada (10/11/2026), itens 8, 12 e 18.

8: 3.5.2 camera -> trecho como requisito da integracao, e limitacao na 5.3;
12: Figura 11 declara que omite as tabelas de apoio; 18: lacuna explicita no Resumo e no Abstract; 5: 3.1 pela classificacao de Gerhardt e Silveira (2009).

    python rev_v69.py pasta_v68   (depois: aceitar.py e zipar2.py)
"""
import sys
from pathlib import Path

import tc
from tc import Doc

tc.DATA = "2026-11-10T12:00:00Z"
d = Doc(str(Path(sys.argv[1]) / "word" / "document.xml"))

d.trocar("A outra ligação, entre cada câmera e os trechos que ela observa",
         "cabe à plataforma, que conhece a posição e o campo de visão de cada câmera: é ela que publica o volume já "
         "referido ao código do trecho (Quadro 18). Este trabalho não constrói nem verifica essa associação.",
         "cabe à plataforma, que precisaria associar cada câmera aos trechos que ela cobre e publicar o volume já "
         "referido ao código do trecho; essa associação é exigida na especificação de integração (Quadro 18) e não "
         "foi construída nem verificada neste trabalho.")

d.trocar("A associação entre cada câmera e os trechos que ela observa é atribuída à plataforma",
         "A associação entre cada câmera e os trechos que ela observa é atribuída à plataforma",
         "Não se verificou se a plataforma municipal dispõe hoje dessa associação. A associação entre cada câmera e "
         "os trechos que ela observa é atribuída à plataforma")

d.trocar("arranjo não localizado na revisão bibliográfica:", "arranjo não localizado na revisão bibliográfica",
         "arranjo, da plataforma de monitoramento à telegestão com verificação normativa, não localizado na "
         "revisão bibliográfica")
d.trocar("arrangement not found in the literature review:", "an arrangement not found in the literature review",
         "an arrangement, from the monitoring platform to the remote management system with normative "
         "verification, not found in the literature review")

d.trocar("A Figura 11 apresenta o modelo de dados em nível de relacionamento",
         "e uma entidade que aquele quadro não discrimina.",
         "e uma entidade que aquele quadro não discrimina. A figura mostra as entidades do caminho da decisão; as "
         "de apoio à avaliação (versão do modelo de previsão, execução de cenário, sessão de medição, calibração, "
         "alerta de diagnóstico e luminária de referência) constam dos Quadros 16 e 17.")

d.substituir_paragrafo(
    "Quanto à natureza, a pesquisa é aplicada",
    "Quanto à natureza, a pesquisa é aplicada, por destinar-se à solução de problema concreto de infraestrutura "
    "urbana. Quanto à abordagem, é quantitativa: opera sobre grandezas mensuráveis — nível decidido, iluminância "
    "entregue, latência do percurso e proporção de decisões conformes. Quanto aos objetivos, é exploratória na "
    "caracterização da infraestrutura e das variáveis, e explicativa na avaliação, em que as hipóteses são testadas "
    "por experimento. Quanto aos procedimentos, combina pesquisa bibliográfica, pesquisa documental sobre fontes "
    "oficiais e dados abertos municipais, desenvolvimento de protótipo e pesquisa experimental em laboratório, na "
    "bancada (GERHARDT; SILVEIRA, 2009, p. 35-39).")

d.novo_paragrafo(d.achar("GALIČ, Maša; GELLERT"),
                 "GERHARDT, Tatiana Engel; SILVEIRA, Denise Tolfo (org.). Métodos de pesquisa. Porto Alegre: "
                 "Editora da UFRGS, 2009. Disponível em: http://hdl.handle.net/10183/52806. Acesso em: 10 nov. 2026.")

d.salvar()
print("ok")
