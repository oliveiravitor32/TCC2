"""Rodada v61: arquitetura de referencia corrigida para escala (grupo de controle, previsao por trecho,
dois estagios, comando em grupo, failsafe de campo, decisoes em serie temporal, celulas), Apendice D
coerente e limitacao nova em 5.3."""
import sys
import tc
from tc import Doc

tc.DATA = "2026-10-18T12:00:00Z"
d = Doc(sys.argv[1])

# ---------------------------------------------------------------- 3.12.6.4: exigencias (escala)
d.trocar("Quatro exigências distinguem a operação da demonstração.",
    "a ordem de grandeza estimada em 3.5.2 é de cerca de 170 publicações por segundo na entrada e de cerca de mil "
    "comandos por segundo na saída, em regime,",
    "a ordem de grandeza estimada em 3.5.2 é de cerca de 170 publicações por segundo na entrada, com a cobertura "
    "atual de cerca de 50 mil câmeras, e de cerca de 730 com câmera em todos os 218.768 trechos do cadastro; como "
    "cada trecho está associado, no recorte do Jardim Helena, a cerca de cinco postes, decidir poste a poste daria "
    "da ordem de 850 e de 3.700 decisões por segundo, respectivamente, e a renovação da validade, cerca de mil "
    "comandos por segundo, permanentemente,")

# ---------------------------------------------------------------- grupo de controle (novo paragrafo)
atend = d.achar("Atendidas essas exigências, a arquitetura de referência compõe-se")
d.novo_paragrafo(atend,
    "A unidade de decisão passa a ser o grupo de controle: o conjunto de pontos de luz associados exatamente aos "
    "mesmos trechos de via (3.5.2). Cada ponto pertence a um único grupo, e todos os pontos de um grupo recebem o "
    "mesmo nível, decidido pela mesma regra de cada ponto — o maior volume entre os trechos do grupo e ocorrência se "
    "qualquer deles a reportar. Como pontos com os mesmos trechos já recebem, poste a poste, exatamente a mesma "
    "decisão, o agrupamento não altera nenhum nível emitido: elimina apenas o cálculo repetido. A decisão de um "
    "grupo lê somente os seus trechos, e nunca o nível de outro grupo, de modo que o efeito de uma publicação não "
    "se propaga além dos pontos associados ao trecho publicado. No recorte do Jardim Helena, os 34 postes associados "
    "formam 17 grupos, de um a quatro postes. Onde a telegestão só admitir comando por circuito, o grupo pode ser o "
    "circuito, com perda de granularidade e de economia, o compromisso já registrado em 3.3.",
    depois=False)

# ---------------------------------------------------------------- lista
d.trocar("Entrada de eventos. Um portal",
    "e o registro retém os eventos enquanto a decisão estiver indisponível ou atrasada, sem perdê-los.",
    "e o registro retém os eventos enquanto a decisão estiver indisponível ou atrasada, sem perdê-los. Um segundo "
    "estágio, particionado pelo grupo de controle, recebe os avisos de reavaliação gerados por trecho, de modo que "
    "cada grupo tenha uma única réplica responsável e duas réplicas nunca decidam o mesmo grupo ao mesmo tempo. Os "
    "eventos são ordenados pela hora em que ocorreram, e não pela de chegada, e o que chega já vencido é descartado.")
d.trocar("Serviço de decisão replicado.",
    "e o número de réplicas acompanha a carga.",
    "e o número de réplicas acompanha o atraso da fila. Cada grupo é decidido uma vez por janela curta, que agrega "
    "as publicações de seus trechos no mesmo período; a ocorrência não espera a janela. Com cerca de dois postes por "
    "grupo, como no recorte, e uma decisão por grupo a cada 5 min, a cobertura total cai para a ordem de mil decisões "
    "por segundo.")
d.trocar("Previsão fora do caminho do comando.",
    "As réplicas carregam apenas versões aprovadas,",
    "A previsão em operação é calculada por trecho, uma vez a cada bloco de 15 min e em lote — da ordem de 250 "
    "previsões por segundo na cobertura total, em lugar de uma por decisão —, e guardada no armazenamento "
    "compartilhado; o nível previsto do grupo é o maior entre os de seus trechos, o que difere ligeiramente do "
    "protótipo, que prevê sobre a série do maior nível. As réplicas carregam apenas versões aprovadas,")
d.trocar("Adaptador de telegestão. Traduz o comando",
    "O MQTT permanece como meio de bancada.",
    "O comando é enviado por grupo, onde a telegestão o admitir, e só quando o nível muda, e não para renovar a "
    "validade de cada luminária: as redes de campo de telegestão, de baixa taxa, têm capacidade limitada de mensagens "
    "em direção ao ponto de luz. A proteção contra a perda da central passa, em campo, à agenda residente que o "
    "Caderno de Encargos já exige do controlador (3.5.2), com validade longa e sinal de vida enviado por grupo ou por "
    "concentrador, e não por luminária; sem a central, o ponto volta à agenda ou ao pleno. Depois de uma falha, a "
    "retomada é escalonada, com limite de taxa e prioridade para os pontos com ocorrência, e os pontos permanecem no "
    "pleno até receberem o novo nível. O MQTT permanece como meio de bancada.")
d.trocar("Dados em dois níveis.",
    "Eventos e telemetria, que crescem com o número de pontos e com o tempo, ficam em armazenamento orientado a "
    "série temporal,",
    "Eventos, decisões e telemetria, que crescem com o número de pontos e com o tempo, ficam em armazenamento "
    "orientado a série temporal,")
d.trocar("Dados em dois níveis.",
    "As consultas do painel são atendidas por réplica de leitura, sem concorrer com a decisão.",
    "Da decisão, grava-se completa a que muda o nível ou gera comando, com as entradas e o grau de cada regra, e da "
    "que mantém o alvo, um resumo; esta continua reconstituível pelos eventos e pela versão da base de regras "
    "(RNF04). Na cobertura total, decidir e gravar tudo poste a poste produziria centenas de gigabytes por dia. Os "
    "dados recentes ficam em armazenamento quente, e os antigos, em arquivo de menor custo. As consultas do painel "
    "são atendidas por réplica de leitura, sem concorrer com a decisão.")
d.trocar("Operação. Os serviços são executados em Kubernetes",
    "decisão de contratação que não altera a arquitetura.",
    "decisão de contratação que não altera a arquitetura. As cópias de segurança são replicadas em outra região, "
    "com tempo de recuperação e perda máxima de dados declarados em contrato.")

# ---------------------------------------------------------------- celulas
dois = d.achar("Dois traços da arquitetura de referência decorrem")
d.novo_paragrafo(dois,
    "Para além de um município, a arquitetura organiza-se em células. Cada município, ou região metropolitana, opera "
    "a sua cópia completa — entrada, decisão, dados e adaptador para a central da sua concessionária —, e só a base "
    "de regras, a tabela de classes da norma e os modelos de previsão vêm de um registro comum e versionado. Não há "
    "sistema central único: o país, com cerca de 22 milhões de pontos de luz (ABCIP, 2024a), cerca de 33 vezes o "
    "parque paulistano, somaria da ordem de dezenas de milhares de decisões por segundo, repartidas entre células "
    "das quais a maior é a de São Paulo, e a falha de uma célula leva apenas os seus pontos à agenda ou ao pleno. Os "
    "valores desta subseção são ordem de grandeza, calculada, e não resultado de teste de carga.",
    depois=False)
d.trocar("Dois traços da arquitetura de referência decorrem",
    "cerca de US$ 3 mil por mês para a infraestrutura de produção,",
    "cerca de US$ 3 mil por mês para a infraestrutura de produção de São Paulo,")

# ---------------------------------------------------------------- 5.3
vm = d.achar("A implantação adotada — uma única máquina virtual da camada gratuita")
d.novo_paragrafo(vm,
    "A arquitetura de referência de 3.12.6.4 apoia-se em capacidades da telegestão que o contrato exige, mas cuja "
    "implantação não é pública: o comando por grupo, a agenda residente no controlador e a capacidade de mensagens "
    "da central e da rede de campo da concessionária. Nenhuma foi avaliada. A proteção de campo proposta — agenda "
    "residente com sinal de vida por grupo — difere da validade por comando ensaiada na bancada (RNF07) e não foi "
    "ensaiada. Onde o grupo for o circuito, e não o conjunto de trechos, todos os pontos do circuito ficam no nível "
    "do mais exigente, com perda de economia não quantificada.")

# ---------------------------------------------------------------- Apendice D
d.trocar("Este apêndice estima o custo mensal",
    "para a ordem de grandeza estimada em 3.5.2 — cerca de 170 publicações e mil comandos por segundo —,",
    "para a ordem de grandeza de 3.5.2 e 3.12.6.4 — cerca de 170 publicações por segundo com a cobertura atual de "
    "câmeras, até cerca de 730 com a cobertura total, e decisão por grupo de controle —,")
d.trocar("Banco principal (PostgreSQL)", "Banco principal (PostgreSQL)",
    "Banco principal (PostgreSQL): cadastro, classes e versões")
d.trocar("Eventos e telemetria (TimescaleDB)", "Eventos e telemetria (TimescaleDB)",
    "Eventos, decisões e telemetria (TimescaleDB)")
d.trocar("A estimativa resulta em cerca de US$ 3 mil por mês",
    "Cada componente tem ao menos duas instâncias, em zonas de disponibilidade distintas, porque a disponibilidade é "
    "exigência da arquitetura, e não opção;",
    "Os componentes com estado ou processamento próprio têm ao menos duas instâncias, em zonas de disponibilidade "
    "distintas, porque a disponibilidade é exigência da arquitetura, e não opção; o balanceador e o plano de controle "
    "do orquestrador são serviços gerenciados, redundantes por construção;")
d.trocar("A estimativa resulta em cerca de US$ 3 mil por mês",
    "o espaço de 1.000 GB por máquina supõe cerca de mil telemetrias por segundo com retenção da ordem de um mês.",
    "o espaço de 1.000 GB por máquina supõe cerca de mil telemetrias por segundo e as decisões que mudam o nível, "
    "comprimidas, com retenção quente da ordem de um mês. Os 12 núcleos das máquinas do cluster bastam porque a "
    "decisão é por grupo e a previsão, por trecho em lote (3.12.6.4): decidir poste a poste, com previsão a cada "
    "decisão, exigiria na cobertura total da ordem de duas a três vezes mais processamento e armazenamento de "
    "decisões que este quadro não comporta.")

d.trocar("Dados em dois níveis.", "Cadastro, classes de iluminação, versões e decisões ficam",
         "Cadastro, classes de iluminação e versões ficam")
d.trocar("Dois traços da arquitetura de referência decorrem",
         "o controlador mantém o último comando até o vencimento da validade e então volta ao pleno,",
         "o ponto mantém o último comando até o vencimento da validade e então volta ao pleno, na bancada, ou à "
         "agenda residente, em campo,")
d.trocar("Quatro exigências distinguem a operação da demonstração.",
         "porque o controlador volta ao pleno no vencimento da validade do comando (RNF07),",
         "porque o ponto volta ao pleno no vencimento da validade do comando (RNF07), ou, em campo, à agenda "
         "residente do controlador,")
d.salvar()
print("ok")
