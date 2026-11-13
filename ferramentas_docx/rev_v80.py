"""v80 (13/11/2026, pedido do autor): pendencias opcionais do levantamento e conferencia das siglas.
- 2.1: "contado a partir de 2016" -> "de 2016 a 2026".
- 3.12.6.4: chave de demonstracao "revogada apos a apresentacao do trabalho" (era "apos a defesa").
- 5.3: a propria atenuacao pode piorar a imagem que alimenta a contagem (nao avaliado). C68.
- Lista de siglas: WGS84 escrito como no texto; NAT (Apendice D) acrescentada."""
import re
import sys
sys.path.insert(0, __file__.rsplit("\\", 1)[0].rsplit("/", 1)[0])
from rev_v71_abnt import reescrever, troca, RAIZ

T = [
    ("recorte temporal de dez anos, contado a partir de 2016.", "recorte temporal de dez anos, de 2016 a 2026."),
    ("é revogada após a defesa.", "é revogada após a apresentação do trabalho."),
    ("A previsão atua como segunda evidência, e o pior caso permanece dentro da faixa admitida pela norma (3.7).",
     "A previsão atua como segunda evidência, e o pior caso permanece dentro da faixa admitida pela norma (3.7). "
     "A própria atenuação pode contribuir para essa degradação, porque menos luz na via tende a piorar a imagem "
     "que alimenta a contagem; esse efeito não foi avaliado."),
    (">WGS 84<", ">WGS84<"),
]


def v80(nome, s):
    if nome != "word/document.xml":
        return None
    for a, b in T:
        s = troca(s, a, b)
    msk = [p for p in re.findall(r"<w:p[ >].*?</w:p>", s, re.S)
           if re.sub(r"<[^>]+>", "", p) == "MSKAmazon Managed Streaming for Apache Kafka"]
    assert len(msk) == 1
    nat = msk[0].replace(">MSK<", ">NAT<").replace(">Amazon Managed Streaming for Apache Kafka<", ">Network Address Translation<")
    return troca(s, msk[0], msk[0] + nat)


if __name__ == "__main__":
    base = RAIZ + "Transicao_pre-projeto-para-TCC-Completo_TCC_Iluminacao_SP_v"
    reescrever(base + "79.docx", base + "80.docx", v80)
    print("ok")
