"""v73: avaliacao critica (12/11/2026), itens 5, 12, 16, 18, 19 e 21 (decisoes do autor).

16 sem "sessenta emissores por metro" (segmento medido de 6 cm; opcao b do autor); 18 coluna da
Tabela 1 = passos; 19 reconciliacao 36/35/34 postes; 21 sem plateia/defesa; 12 nivel do horario
fixo em 3.11 (decisao/energia.py: desce ao piso sob a taxa, volta ao pleno); 5 passagens x ocupacao em 5.3.
"""
import sys
sys.path.insert(0, __file__.rsplit("\\", 1)[0].rsplit("/", 1)[0])
from rev_v71_abnt import reescrever, troca, RAIZ

T = [
    # 16
    ("Tipo 5050, sessenta emissores por metro, 14,4 W/m,", "Tipo 5050, 14,4 W/m,"),
    ("sessenta emissores por metro, 14,4 W/m —", "14,4 W/m —"),
    # 18
    ("o envelope esperado, o número de decisões", "o envelope esperado, o número de passos de 5 s"),
    ("Decisões e aderência (adaptativo; fluxo pleno; horário fixo)", "Passos de 5 s e aderência (adaptativo; fluxo pleno; horário fixo)"),
    # 19
    ("com 16 trechos e 36 postes.", "com 16 trechos e 36 postes. Os 36 registros correspondem a 35 postes, porque uma placa aparece duplicada no cadastro; desses, 34 ficam a até 25 m de algum trecho e entram na associação."),
    # 21
    ("de modo que a plateia da defesa acompanhe", "de modo que o observador acompanhe"),
    ("O sistema reproduz o fluxo completo a ser demonstrado na defesa:", "O sistema reproduz o fluxo completo a ser demonstrado:"),
    ("delimita a cena observada pela plateia", "delimita a cena observada"),
    ("O que a plateia observa não é apenas", "O que o observador vê não é apenas"),
    ("É a interface de apresentação do sistema e o que a plateia observa durante a defesa.", "É a interface de apresentação do sistema e o que o observador acompanha durante a demonstração."),
    # 12
    ("das 0 h às 5 h, janela escolhida pelos autores, que corresponde",
     "das 0 h às 5 h, janela escolhida pelos autores, em que o nível desce à classe mínima de dimerização (0,5 do pleno) sob a mesma taxa de um décimo por minuto e volta ao pleno às 5 h, e que corresponde"),
    # 5
    ("sem atributo de feriado, e os limiares do critério de leitura são dos autores.",
     "sem atributo de feriado, e os limiares do critério de leitura são dos autores. As séries de Melbourne e de Zurique vêm de contadores automáticos, que registram passagens, e não da ocupação média que a interface especifica (3.5.2); o que se transfere ao sistema é a forma do ciclo diário, normalizada por ponto, e não a grandeza."),
]


def v73(nome, s):
    if nome != "word/document.xml":
        return None
    for a, b in T:
        s = troca(s, a, b)
    return s


if __name__ == "__main__":
    base = RAIZ + "Transicao_pre-projeto-para-TCC-Completo_TCC_Iluminacao_SP_v"
    reescrever(base + "72.docx", base + "73.docx", v73)
    print("ok")
