# Guia do Projeto Piloto — validação mínima antes de comprar tudo

Objetivo: gastar pouco, provar que a cadeia funciona ponta a ponta e só então escalar.

---

## Fase 0 — Compra mínima (1 nó apenas)

| # | Item | Para que serve | Necessário no piloto? |
|---|------|----------------|----------------------|
| 1 | ESP32 DevKit (38 pinos) | Cérebro: lê o sensor e envia pro Wi-Fi | **Sim** |
| 2 | Módulo INA219 (I2C) | Mede tensão e corrente, calcula potência | **Sim** |
| 3 | Fonte 12 V / 2 A com plug P4 | Alimenta a bancada | **Sim** |
| 4 | Adaptador P4 fêmea com borne | Liga a fonte à protoboard sem gambiarra | **Sim** |
| 5 | Protoboard 830 furos + jumpers | Montagem sem solda | **Sim** |
| 6 | Cabo micro-USB (dados, não só carga) | Grava o firmware no ESP32 | **Sim** |
| 7 | Cooler 12 V 40 mm | Carga com motor (liga/desliga, pico de partida) | **Sim** |
| 8 | Resistor 10 Ω / 10 W | Carga resistiva de valor conhecido — usada para calcular P = V²/R | **Sim** |
| 9 | Multímetro digital | Valor de referência para provar a exatidão (hipótese H1) | **Sim** |
| 10 | LED de potência 3 W + dissipador | Carga de iluminação | Não no piloto |
| 11 | ESP32 e INA219 extras (nós 2 e 3) | Múltiplos pontos de medição | Não no piloto |

**Custo do piloto: em torno de R$ 150 a R$ 250** (contra R$ 450–800 do sistema completo).

> Atenção ao cabo USB: muitos cabos de carregador não têm as vias de dados. Se o computador não reconhecer a placa, o cabo é o primeiro suspeito.

---

## Fase 1 — Montagem (1 tarde)

Ligação do INA219 ao ESP32:

```
INA219  ->  ESP32
VCC     ->  3V3
GND     ->  GND
SDA     ->  GPIO 21
SCL     ->  GPIO 22

INA219  ->  circuito medido
VIN+    ->  positivo da fonte 12 V
VIN-    ->  positivo da carga (cooler ou resistor)
GND da fonte -> GND da carga (terra comum com o ESP32)
```

O INA219 vai **em série** com a carga, no lado positivo. Ele mede a corrente que atravessa esse caminho.

---

## Fase 2 — Testes de validação, na ordem

**Teste 1 — o ESP32 enxerga o sensor?**
Rode um scanner I2C (código de 15 linhas, disponível nos exemplos da IDE). Se aparecer o endereço `0x40`, a ligação está correta. Se não aparecer nada: confira SDA/SCL e a alimentação em 3V3.

**Teste 2 — a medição bate com a realidade?**
Ligue o resistor de 10 Ω. Meça com o multímetro a tensão real sobre ele e a resistência real. Calcule P = V²/R. Compare com o valor que o INA219 reporta. Erro abaixo de 5% valida a hipótese H1 do trabalho — anote esses números, eles vão direto pro Quadro 12.

**Teste 3 — o dado chega na nuvem?**
Crie uma conta gratuita no HiveMQ Cloud, configure o ESP32 para publicar, e use um cliente MQTT no PC (MQTT Explorer) para ver as mensagens chegando. Só depois disso vale escrever backend.

**Teste 4 — o dado persiste?**
Suba um PostgreSQL gratuito (Supabase ou Neon) e um script Python que assina o tópico e grava. Neste ponto **a coleta começa e não para mais** — é o marco mais importante do cronograma.

**Teste 5 — resiliência.**
Desligue o roteador por 10 minutos com o sistema rodando. Veja o que acontece com a série. Isso é o caso de teste CT08 e revela se você precisa mesmo do buffer local.

---

## Fase 3 — Só depois disso

Com os cinco testes passando, aí sim: comprar os nós 2 e 3, escrever o dashboard, treinar os modelos.

O trabalho de IA pode acontecer **em paralelo e desde já**, usando a base pública da UCI — não depende de nenhum hardware.

---

## Ordem de prioridade se o tempo apertar

1. Um nó medindo e gravando na nuvem (sustenta H1 e H2)
2. Modelos rodando sobre a base pública (sustenta H3)
3. Dashboard (sustenta H4)
4. Nós 2 e 3 (enriquece, mas não é essencial)

Se só os itens 1 e 2 ficarem prontos, o trabalho ainda é defensável — basta ajustar a seção de limitações.
