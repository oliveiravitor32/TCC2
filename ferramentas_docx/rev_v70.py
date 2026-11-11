"""Rodada v70: C23 (11/11/2026, decisao do autor): limitacao da 5.3 diz que o no unico e o fisico.

    python rev_v70.py pasta_v69   (depois: aceitar.py e zipar2.py)
"""
import sys
from pathlib import Path

import tc
from tc import Doc

tc.DATA = "2026-11-11T12:00:00Z"
d = Doc(str(Path(sys.argv[1]) / "word" / "document.xml"))
T = "O protótipo é um nó único, em escala reduzida"
d.trocar(T, "O protótipo é um nó único", "O protótipo físico é um nó único")
d.inserir("O protótipo físico é um nó único, em escala reduzida", "geometria fotométrica de uma luminária viária real",
          "; os demais pontos de luz do sistema são simulados por programa")
d.salvar()
print("ok")
