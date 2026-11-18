# Roteiro de respostas para a banca (v81)

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

## 17. A economia de 37,6 % vem de oito noites de outra cidade, sem margem de erro. Dá para confiar?

> Como número exato, não; como direção, sim. São oito noites reais de quatro pontos de Zurique, e não calculamos intervalo de confiança para a energia; só o acerto de faixa da previsão tem intervalo (4.6). O que dá confiança é que as três avaliações independentes apontam para o mesmo lado: 24,3 % na suíte de cenários, 37,6 % nas noites reais e 24,1 % na bancada (5.4). E nunca afirmamos economia anual, de parque ou em reais (1.3, 3.11).

## 18. Por que há resultados dentro do Capítulo 3, que é a metodologia?

> A estrutura segue o roteiro do orientador, que pôs a engenharia de software e o banco de dados dentro da metodologia (3.12 e 3.13). O que aparece no Capítulo 3 é a preparação do instrumento — a calibração do nó, o recorte do Jardim Helena, o exemplo de uma decisão —, que precisa existir antes de medir. Os resultados que respondem às hipóteses estão todos no Capítulo 4 e são discutidos no Capítulo 5.

## 19. A revisão é narrativa, sem bases nem termos de busca. Como afirmam que há uma lacuna?

> A revisão é declarada como narrativa (2.1), e por isso a lacuna está escrita com cuidado: "não localizado", e não "não existe" (2.9). Não dizemos que nenhum componente é novo; dizemos que não encontramos o arranjo — monitoramento urbano ligado à telegestão com uma camada de verificação normativa separada. Se alguém mostrar um trabalho com esse arranjo, ele entra como correlato; a contribuição prática do protótipo continua.

## 20. A classe P3 foi definida sem medir a rua. Ela vale para o Jardim Helena?

> A classe sai da conta da própria NBR 5101 (Tabela 6), feita na 3.8, mas os parâmetros de entrada — tipo de via, fluxo de pedestres e demais fatores — foram adotados por nós para uma via local, sem levantamento de campo. Isso não afeta o mecanismo: a classe é um registro no banco (RF09), e se a prefeitura atribuir outra, muda um dado, não o código, e o piso e a taxa passam a seguir a classe nova.

## 21. A conclusão é curta para um trabalho deste tamanho.

> Ela segue o roteiro do orientador: fecha sem informação nova. A retomada do objetivo geral, de cada objetivo específico e de cada hipótese está na abertura do Capítulo 6, e a discussão está no Capítulo 5. As recomendações ficam separadas em 6.1.

## 22. São 36 limitações. Isso não esconde as que importam?

> Preferimos declarar tudo a deixar algo de fora. Para não diluir, a abertura da 5.3 diz o peso de cada grupo: o invariante de segurança não depende de nenhuma delas; a aderência ao envelope depende de critérios nossos; a energia, da luminária de referência; a previsão, de série de outra cidade; e a bancada vale para a escala reduzida. As que mais condicionam a conclusão são três: dados de outra cidade, nó único em bancada e integração não testada com a plataforma e a telegestão reais.

## 23. A arquitetura de escala, o custo na AWS e a meteorologia não foram implantados. Por que estão no trabalho?

> Estão rotuladas como proposta, não como resultado (3.12.6.4 e Apêndices D, E e F), e vieram das recomendações do orientador. Uma parte foi, sim, implementada no protótipo: a decisão por grupo de controle, conferida por teste e pela suíte. O custo é estimativa com preço público da AWS, não orçamento. O objetivo é mostrar que o caminho do protótipo à escala existe e quanto custaria, não afirmar que ele funciona.

## 24. As citações estão em maiúsculas, como "(SÃO PAULO, 2018a)". Isso não é da norma antiga?

> Usamos o sistema autor-data com a entrada em maiúsculas dentro dos parênteses, por decisão nossa, de forma uniforme em todo o texto. Se a UNIP exigir a forma da NBR 10520:2023, só com inicial maiúscula, é uma troca de formatação que não altera nenhuma fonte nem nenhum argumento.

---

## Preparação individual (fazer antes da banca)

Cada tarefa abaixo serve para que cada autor consiga defender sozinho a sua parte. Marque o quadrado quando estiver pronto.

### - [ ] 1. Vitor: verificação, failsafe e painel ao vivo

- **Verificação** (`Codigo/decisao/verificacao.py`): é o "segurança" do sistema. Antes de qualquer comando ir para o poste, confere duas regras da norma:
  - **piso:** a luz nunca fica abaixo do mínimo da classe (ex.: 5 lux na P5);
  - **taxa:** a luz só desce devagar, no máximo 10 % do pleno por minuto; subir pode ser na hora.
- **Failsafe** (firmware, `Codigo/firmware/no/no.ino`): se o poste ficar sem receber comando válido por um tempo, volta sozinho para a luz máxima. Se a internet ou o servidor cair, a rua nunca fica escura.
- **Painel ao vivo:** abrir o painel, escolher uma decisão e mostrar a explicação: quais regras dispararam, o nível pedido e o nível enviado.
- **Treino:** explicar em voz alta, sem olhar o código, o que cada um desses dois arquivos faz.

### - [ ] 2. Lucas: regras, tercis, XGBoost e H3

- **As 7 regras** (Quadro 22, Apêndice G): saber dizer cada uma em uma frase, do tipo "se há ocorrência, luz da classe da via" e "se o movimento é baixo e a previsão também, classe mínima".
- **Tercis:** os dois números que separam movimento "baixo", "médio" e "alto". Saem de dividir os dados de Zurique em três partes iguais. Dizer que foi escolha nossa, porque a norma não dá esses números.
- **XGBoost:**
  - **atributos:** prevê o movimento olhando o passado (1, 2, 3, 24 e 168 horas antes, médias recentes, hora, dia da semana e feriado);
  - **partição cronológica:** treina com os anos antigos e testa com o ano seguinte, nunca embaralhado, porque na vida real só se conhece o passado.
- **H3:** a ideia era que a previsão encurtaria o tempo em transição. Foi rejeitada: 27,9 % com previsão contra 23,3 % sem. Dizer com tranquilidade: resultado negativo relatado com honestidade conta a favor.

### - [ ] 3. Bruno: requisitos, interface, contrato e termo aditivo

- **Requisitos:** Quadro 10, funcionais = o que o sistema faz (RF01 a RF12); Quadro 11, não funcionais = como ele deve se comportar, como segurança, tempo de resposta e privacidade (RNF01 a RNF09).
- **Interface de integração** (Quadro 18): o que a Smart Sampa teria de enviar, em dois tipos de mensagem: o **volume** de pessoas a cada 5 min por trecho e a **ocorrência** (segurança ou trânsito).
- **Contrato e Caderno de Encargos:** mostram que a telegestão e a dimerização já são exigidas da concessionária. Por isso o trabalho não precisa comprar equipamento.
- **Termo aditivo** (5.4): hoje o contrato mede a luz como se o poste estivesse sempre no máximo; propomos que, em modo adaptativo, ela seja comparada com a classe registrada naquele momento, nunca abaixo da mínima da norma, e que, sem registro, valha a classe da via.

### - [ ] 4. Caso ao vivo da camada de verificação corrigindo um pedido

É a resposta mais forte para "como sabem que a segurança funciona?". Duas formas:

- **Rodar o teste do CT05** na pasta `Codigo`: joga cem mil pedidos aleatórios, inclusive abaixo do piso, e mostra que nenhum passa:

  ```bash
  python -m pytest tests/test_verificacao.py -v
  ```

- **Mostrar no painel uma decisão com "restrição aplicada: piso"**, isto é, uma em que o sistema pediu menos que o mínimo e a camada corrigiu.

Ensaiar antes, para não depender da sorte na hora.

### - [ ] 5. Slide com três colunas

Separa com clareza o que foi provado e de que jeito, e antecipa o ataque "o que vocês realmente provaram?".

| Demonstrado em bancada | Simulado | Só documentado (contrato) |
|---|---|---|
| Nó real com ESP32, fita de LED e sensor | 33 postes do bairro | A Smart Sampa publicar volume |
| MQTT com TLS, rampa, failsafe e latência de 1 a 1,5 s | Cenários e noites de Zurique | A telegestão aceitar o comando |
| Diagnóstico de falha | Energia da luminária de 40 W | Dimerização de 0 a 10 V nas luminárias |
