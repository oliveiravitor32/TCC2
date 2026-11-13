"""v76 (12/11/2026): descricao da Figura 14 ajustada ao grafico (C65 b), conferida contra a serie gravada
(cenarios/resultados/avaliacao_ia_zurique_antecipado.json, ponto 1358, dia util):
0,75 das 18h31 as 22h29; 0,64-0,75 de 22h30 a 0h; 0,5 de 0h02, repique 0,58 de 0h15 a 0h29, 0,5 de 0h30 a 4h59;
0,56 de 5h00 a 5h14 e 0,75 de 5h15 em diante. Volume abaixo do tercil inferior a partir das 22h15."""
import sys
sys.path.insert(0, __file__.rsplit("\\", 1)[0].rsplit("/", 1)[0])
from rev_v71_abnt import reescrever, troca, RAIZ

A = ("Até a meia-noite, com o volume entre os dois tercis, o regime adaptativo ficou, após a descida inicial, uma classe abaixo da via; "
     "das 0 h às 5 h, com o volume abaixo do tercil inferior, os dois regimes ficaram no piso; "
     "depois das 5 h, o horário fixo voltou ao pleno e o adaptativo, ")  # segue "a uma classe abaixo." em outro run
B = ("Das 18 h 30 às 22 h 30, com o volume entre os dois tercis até as 22 h 15, o regime adaptativo ficou uma classe abaixo da via; "
     "entre 22 h 30 e 0 h 30, com o volume em torno do tercil inferior, alternou entre essa classe e níveis intermediários e tocou o piso logo após a meia-noite; "
     "da 0 h 30 às 5 h, com o volume abaixo do tercil inferior, os dois regimes ficaram no piso; "
     "às 5 h, o horário fixo voltou ao pleno, e o adaptativo, depois de um degrau intermediário, chegou às 5 h 15 ")


def v76(nome, s):
    return troca(s, A, B) if nome == "word/document.xml" else None


if __name__ == "__main__":
    base = RAIZ + "Transicao_pre-projeto-para-TCC-Completo_TCC_Iluminacao_SP_v"
    reescrever(base + "75.docx", base + "76.docx", v76)
    print("ok")
