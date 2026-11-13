"""v72: avaliacao critica (12/11/2026), itens 1, 2 e 26 (decisao do autor).

Resumo/Abstract: "sem deixar a via abaixo do nivel exigido" -> nunca 2 lux abaixo (deficit medio 0,8 lux,
Tabela 3); "integracao e viavel" -> compativel com os contratos, viabilidade em campo condicionada;
frase truncada do Resumo/Abstract; "testado pelos em banco" (Apendice F).
"""
import sys
sys.path.insert(0, __file__.rsplit("\\", 1)[0].rsplit("/", 1)[0])
from rev_v71_abnt import reescrever, troca, RAIZ

T = [
    ("a camada que as liga, arranjo, da plataforma de monitoramento à telegestão com verificação normativa, não localizado na revisão bibliográfica:",
     "a camada que as liga, da plataforma de monitoramento à telegestão, com verificação normativa, arranjo não localizado na revisão bibliográfica:"),
    ("sem deixar a via abaixo do nível exigido, o que a programação horária não assegurou.",
     "sem nunca deixar a via 2 lux ou mais abaixo do nível pedido (déficit médio de 0,8 lux), o que a programação horária não assegurou."),
    ("Conclui-se que a integração é viável com a infraestrutura já contratada, desde que a plataforma publique os dados na interface especificada.",
     "Conclui-se que a integração é compatível com o que os contratos vigentes já exigem; a viabilidade em campo depende de a plataforma publicar os dados na interface especificada e de a telegestão aceitar os comandos."),
    ("the layer that connects them, an arrangement, from the monitoring platform to the remote management system with normative verification, not found in the literature review:",
     "the layer that connects them, from the monitoring platform to the remote management system, with normative verification, an arrangement not found in the literature review:"),
    ("without leaving the street below the required level, which the fixed schedule did not ensure.",
     "without ever leaving the street 2 lux or more below the requested level (mean deficit of 0.8 lux), which the fixed schedule did not ensure."),
    ("The integration is feasible with the infrastructure already under contract, provided that the monitoring platform publishes its data through the specified interface.",
     "The integration is compatible with what the current contracts already require; its feasibility in the field depends on the monitoring platform publishing its data through the specified interface and on the remote management system accepting the commands."),
    ("testado pelos em banco descartável", "testado pelos autores em banco descartável"),
]


def v72(nome, s):
    if nome != "word/document.xml":
        return None
    for a, b in T:
        s = troca(s, a, b)
    return s


if __name__ == "__main__":
    base = RAIZ + "Transicao_pre-projeto-para-TCC-Completo_TCC_Iluminacao_SP_v"
    reescrever(base + "71.docx", base + "72.docx", v72)
    print("ok")
