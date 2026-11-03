"""Rodada v63: divisao do trabalho por area de responsabilidade em 3.12.2 (pedido do autor).

    python rev_v63.py pasta_v62
"""
import sys
from pathlib import Path

import tc
from tc import Doc

tc.DATA = "2026-11-02T23:00:00Z"
d = Doc(str(Path(sys.argv[1]) / "word" / "document.xml"))
d.trocar("A divisão do trabalho acompanhou essa organização",
         "Vitor Oliveira dos Santos ficou responsável pelo desenvolvimento do software e pela montagem do nó de "
         "bancada, e Bruno Bonavigo Dacal e Lucas de Araujo Vergara, pela documentação e pelo apoio à pesquisa.",
         "a equipe dividiu-se por área de responsabilidade. Vitor Oliveira dos Santos respondeu pela borda e pela "
         "infraestrutura: montagem do nó de bancada, firmware, comunicação segura, implantação em nuvem e banco de "
         "dados. Lucas de Araujo Vergara respondeu pelo módulo de inteligência: fundamentação da previsão e da "
         "inferência nebulosa, análise das métricas e dos resultados e sua documentação. Bruno Bonavigo Dacal "
         "respondeu pelos requisitos e pela operação: levantamento normativo e dos dados urbanos, validação do "
         "painel e dos alertas e documentação da operação.")
d.salvar()
