"""v79 (13/11/2026, pedido do autor): busca por texto com cara de IA.
- 3.5.2: "a via que qual luminaria ilumina" -> "a via que cada luminaria ilumina" (erro de digitacao).
- Apendice A: "recuperacao aumentada por geracao" (termo invertido e exagerado) retirado."""
import sys
sys.path.insert(0, __file__.rsplit("\\", 1)[0].rsplit("/", 1)[0])
from rev_v71_abnt import reescrever, troca, RAIZ

T = [
    ("observa a via que qual luminária ilumina", "observa a via que cada luminária ilumina"),
    ("instruções persistentes de projeto e recuperação aumentada por geração, com consulta a páginas web",
     "instruções persistentes de projeto e consulta a páginas web"),
]


def v79(nome, s):
    if nome != "word/document.xml":
        return None
    for a, b in T:
        s = troca(s, a, b)
    return s


if __name__ == "__main__":
    base = RAIZ + "Transicao_pre-projeto-para-TCC-Completo_TCC_Iluminacao_SP_v"
    reescrever(base + "78.docx", base + "79.docx", v79)
    print("ok")
