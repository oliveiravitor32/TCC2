"""Rodada v67: bloco 2 do REVISAR (10/11/2026).

C39: conta da classe P conferida na NBR 5101:2024 (Tabela 6, p. 13) e escrita na 3.8;
C42 (b): Quadro 3 sem os prazos de 2019 (decisao do autor).

    python rev_v67.py pasta_v66   (depois: aceitar.py e zipar2.py)
"""
import sys
from pathlib import Path

import tc
from tc import Doc

tc.DATA = "2026-11-10T12:00:00Z"
d = Doc(str(Path(sys.argv[1]) / "word" / "document.xml"))

d.trocar("Certificação compulsória instituída em 2017, com prazos de adequação a partir de 2019, e consolidada em 2022",
         "Certificação compulsória instituída em 2017, com prazos de adequação a partir de 2019, e consolidada em 2022",
         "Certificação compulsória instituída em 2017 e consolidada em 2022")

d.trocar("A soma dos fatores de ponderação conduz, pela equação normativa de seleção, à classe P3.",
         "A soma dos fatores de ponderação conduz, pela equação normativa de seleção, à classe P3.",
         "Pela tabela de parâmetros da classe P da norma, os valores de ponderação são 1 para a velocidade baixa, "
         "0 para o volume moderado, 1 para pedestres e tráfego motorizado, 0,5 para veículos estacionados presentes "
         "e 0 para a luminância de ambiente moderada; a soma é 2,5, e a equação normativa de seleção, 6 menos a "
         "soma, dá 3,5, que, não sendo inteiro, se arredonda para o inteiro inferior: classe P3 (ASSOCIAÇÃO "
         "BRASILEIRA DE NORMAS TÉCNICAS, 2024, Tabela 6).")

d.salvar()
print("ok")
