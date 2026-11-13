"""v81 (13/11/2026, pedido do autor): Apendice C chamado no texto (3.4) e termino do uso de IA em 13/11/2026
(Apendice A: periodo e data). O mesmo ajuste de data no Entregavel 2 v2."""
import sys
sys.path.insert(0, __file__.rsplit("\\", 1)[0].rsplit("/", 1)[0])
from rev_v71_abnt import reescrever, troca, RAIZ

T = [
    ("e a Figura 1 mostra o nó montado.", "e a Figura 1 mostra o nó montado; a vista posterior está no Apêndice C."),
    ]


def dia13(s, ancora, pulos):
    """O Word quebrou "12/11/2026" em varios runs: troca o run "2" do dia por "3"."""
    import re
    assert s.count(ancora) == 1, ancora
    i = s.index(ancora) + len(ancora)
    ts = list(re.finditer(r"(<w:t[^>]*>)([^<]*)(</w:t>)", s[i:]))
    m = ts[pulos]
    assert m.group(2) == "2", m.group(2)
    a, b = i + m.start(2), i + m.end(2)
    return s[:a] + "3" + s[b:]
T_E2 = [("de 13/09/2026 a 12/11/2026,", "de 13/09/2026 a 13/11/2026,")]


def aplica(tabela):
    def f(nome, s):
        if nome != "word/document.xml":
            return None
        for a, b in tabela:
            s = troca(s, a, b)
        if tabela is T:
            s = dia13(s, "13/09/2026 a ", 0)
            s = dia13(s, "Data: ", 1)
        return s
    return f


if __name__ == "__main__":
    base = RAIZ + "Transicao_pre-projeto-para-TCC-Completo_TCC_Iluminacao_SP_v"
    reescrever(base + "80.docx", base + "81.docx", aplica(T))
    e2 = RAIZ + "Docs/Entregavel2/Entregavel2_Guia_do_Usuario_e_Manual_de_Operacao_v2.docx"
    tmp = e2 + ".tmp"
    reescrever(e2, tmp, aplica(T_E2))
    import os
    os.replace(tmp, e2)
    print("ok")
