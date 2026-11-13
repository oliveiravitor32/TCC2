"""v77 (13/11/2026): restos da avaliacao critica (itens 2 e 21).
Quadro 13 sem "e durante a defesa"; 1.3 "compativel com a infraestrutura ja contratada" (igual ao Resumo)."""
import sys
sys.path.insert(0, __file__.rsplit("\\", 1)[0].rsplit("/", 1)[0])
from rev_v71_abnt import reescrever, troca, RAIZ

T = [
    ("se torna observável durante a execução e durante a defesa", "se torna observável durante a execução"),
    ("é tecnicamente realizável sobre a infraestrutura já contratada pelo município, sem aquisição de equipamento,",
     "é compatível com a infraestrutura já contratada pelo município, sem aquisição de equipamento,"),
]


def v77(nome, s):
    if nome != "word/document.xml":
        return None
    for a, b in T:
        s = troca(s, a, b)
    return s


if __name__ == "__main__":
    base = RAIZ + "Transicao_pre-projeto-para-TCC-Completo_TCC_Iluminacao_SP_v"
    reescrever(base + "76.docx", base + "77.docx", v77)
    print("ok")
