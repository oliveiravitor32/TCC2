# Roteiro de respostas para a banca (v74)

Baseado na avaliação crítica de 11/11/2026 (seção 8, "perguntas difíceis"). Cada resposta usa só o que o texto já diz; a seção entre parênteses é onde está no TCC. Ler em voz alta, de memória, sem slide.

**Regra geral:** admitir o limite primeiro, depois dizer o que foi demonstrado. Nunca discutir com o examinador sobre um número: mostrar onde ele está no texto.

---

## 1. Qual é, em uma frase, a contribuição do trabalho?

> Uma arquitetura que liga a plataforma de monitoramento à telegestão, com uma camada de verificação normativa separada da inteligência, de modo que nenhuma decisão chega à luminária sem respeitar o piso e a taxa da NBR 5101. Não é um algoritmo novo: nenhum componente isolado é inédito (2.9); o que a revisão não localizou foi o arranjo.

## 2. Se uma tabela faz o mesmo que a lógica nebulosa, por que manter a lógica nebulosa?

> Não escondemos isso: a tabela em degraus igualou a inferência nebulosa em energia, e a tabela com histerese teve menos mudanças perceptíveis (4.6). A inferência fica no sistema por dois motivos: o objetivo era avaliá-la, e foi avaliada contra um substituto simples, com critério fixado antes; e ela registra o grau de ativação de cada regra, o que ajuda a explicar a decisão no painel. Se fôssemos implantar hoje, a tabela com histerese seria uma escolha defensável, e a camada de verificação continuaria igual, porque ela não depende de qual decide.

## 3. Se a previsão piorou a métrica de H3, por que ela continua no sistema?

> H3 foi rejeitada e está escrito assim (5.1): com previsão, 27,9 % da janela em transição contra 23,3 % sem ela. Mas a previsão mostrou outra utilidade: é uma segunda evidência quando a contagem falha no início da noite, e aí ela segura a luz (4.6). Com a série de 15 min de Zurique, o XGBoost superou a melhor referência simples (3.6, 4.6). Então ela fica como proteção contra contagem errada, não como antecipação.

## 4. Como vocês sabem que a camada de verificação funciona, se ela nunca corrigiu o piso nos cenários?

> Nos cenários integrados, a inferência não pede menos que o piso por construção, então ali a camada não tinha o que corrigir: a rampa, sim, atuou em 541 passos (4.2). A prova da camada não é a suíte; é o CT05, que joga cem mil combinações aleatórias de nível pedido, incluindo valores abaixo do piso, e não teve violação (3.12.9). E o ensaio físico mostrou a rampa e o failsafe no nó real.

## 5. "667.200 passos sem violação" não é um número inflado? São 324 decisões.

> São passos de 5 s do nó, não decisões, e a Tabela 1 diz isso. O serviço decidiu 324 vezes na suíte. O número mostra que o nível aplicado ficou dentro da norma em cada instante, inclusive durante as rampas. A evidência mais forte do piso é o CT05.

## 6. Por que Zurique? O que garante que vale para o Jardim Helena?

> Nada garante, e está nas limitações (5.3). Não existe série pública de pedestres de São Paulo. O que se transfere é a forma do ciclo diário, normalizada por ponto, e não a quantidade de pessoas. A recomendação é um piloto com 30 dias de dados de São Paulo antes de qualquer uso (6.1).

## 7. A série de Zurique conta passagens, e a interface de vocês pede ocupação.

> É verdade, e está declarado em 5.3. As séries públicas disponíveis contam passagens. Como cada ponto é normalizado pelo próprio percentil 99, o sistema usa a forma da curva, não a grandeza. Com a plataforma real, o modelo seria retreinado com a ocupação que ela publicar.

## 8. O que exatamente a bancada prova sobre uma luminária de rua?

> Prova o caminho completo e o comportamento de controle: evento → decisão → comando por MQTT com TLS → nó → luz medida → telemetria, com latência de 1,03 s a 1,47 s; a rampa de 10 para 5 lux em cerca de 5 min; o failsafe voltando ao pleno sem comando; e a detecção de falha. Não prova fotometria de via, potência real de luminária nem economia em escala: isso está excluído por escrito (1.3, 5.3).

## 9. O Resumo dizia que a via não ficou abaixo do exigido, mas a Tabela 3 mostra minutos abaixo.

> Corrigimos: o adaptativo nunca ficou 2 lux ou mais abaixo do nível pedido; ficou abaixo por margem pequena, com déficit médio de 0,8 lux. O horário fixo, nas noites reais, ficou 85 minutos 2 lux ou mais abaixo.

## 10. O envelope e as regras foram escritos por vocês. O que H1 testa?

> Coerência interna, e o texto declara isso (3.9). O resultado que não depende de nós é o invariante normativo: zero violação de piso e de taxa, verificado contra a norma.

## 11. Uma pessoa sozinha às 3 h fica na classe mínima. Isso é seguro?

> A classe mínima, P5, é classe de pedestres, com iluminância vertical para reconhecimento facial (Quadro 8). Uma versão anterior levava ao pleno com qualquer pessoa e foi abandonada por ir além da norma (3.7). E qualquer ocorrência reportada volta à classe da via na hora (R1).

## 12. Ao baixar a luz, a câmera conta pior. O sistema não se engana sozinho?

> Não foi avaliado; é uma limitação que reconhecemos. O pior caso fica no piso da norma, nunca abaixo, e a previsão funciona como segunda evidência contra contagem errada.

## 13. Metade das 50 mil câmeras é privada. Elas contam pessoas?

> Não sabemos: a cobertura não foi levantada (5.3). Por isso o sistema é conservador: trecho sem dado fica no pleno.

## 14. A concessionária seria multada pelo indicador se dimerizasse. Então hoje é inviável?

> Hoje, sem ajuste contratual, sim. O indicador de iluminância não prevê ponto dimerizado. O trabalho identifica isso e propõe a redação de um termo aditivo (5.4). Por isso concluímos "compatível com os contratos", e não "viável".

## 15. O sistema foi feito com IA em poucas semanas. O que é de vocês?

> O problema, os requisitos, a arquitetura, os critérios de avaliação, a montagem física, a conferência dos resultados e a interpretação. O Apêndice A declara o uso da ferramenta linha a linha. Cada um responde pela sua área (3.12.2):
> - **Vitor:** nó, firmware, comunicação segura, nuvem e banco.
> - **Lucas:** módulo de inteligência (previsão, inferência, avaliação).
> - **Bruno:** requisitos e operação.

## 16. O sistema quase nunca fica no pleno à noite? A economia vem de baixar a luz com gente na rua?

> Sim, e é esperado. As fronteiras de movimentação são os tercis calculados com o dia inteiro (3.7), então à noite a rua raramente chega a "alto": nas oito noites de Zurique, o pleno ocupou de 0 % a 15 % do tempo, e a diferença para o horário fixo veio quase toda do começo da noite, porque de madrugada os dois ficam no piso. Isso está dentro da norma: com movimento médio ela admite uma classe abaixo (R4), e essa classe ainda é de pedestres. Qualquer ocorrência leva à classe da via na hora (R1). Os tercis são critério nosso, declarado como limitação (5.3); fixar essas fronteiras com dados reais de São Paulo cabe no piloto proposto em 6.1.

---

## Preparação individual (fazer antes da banca)

- [ ] **Vitor:** explicar de memória `decisao/verificacao.py` (piso e taxa) e o failsafe no firmware; mostrar ao vivo o painel com a decisão explicada.
- [ ] **Lucas:** explicar as 7 regras (Quadro 22), os tercis, o XGBoost (atributos e por que partição cronológica) e o resultado de H3.
- [ ] **Bruno:** explicar os requisitos (Quadros 10 e 11), a interface de integração (Quadro 18), o contrato, o Caderno de Encargos e o termo aditivo.
- [ ] Ter pronto um caso ao vivo: pedido abaixo do piso sendo corrigido pela camada de verificação (rodar o teste do CT05 ou mostrar a decisão com a restrição aplicada).
- [ ] Um slide com três colunas: demonstrado em bancada, simulado, e apenas documentado em contrato.
