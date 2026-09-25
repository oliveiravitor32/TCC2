// Sketch de CALIBRACAO do no de bancada (TCC 3.4.2 a 3.4.4).
//
// Nao e o firmware de operacao: nao usa Wi-Fi nem MQTT. Fica esperando
// comandos pela serial (115200) enviados pelo script bancada/calibrar.py,
// que grava os resultados no banco (sessao_medicao e calibracao).
//
// Ligacoes (as mesmas do no):
//   BH1750  SDA = GPIO21, SCL = GPIO22, VCC = 3V3, endereco 0x23
//   D4184   TRIG/PWM = GPIO25, GND comum
//
// PWM de 5 kHz, 12 bits (0..4095), SEM correcao de gama: a calibracao mede
// a resposta real duty -> lux, e e ela que o firmware vai usar.
//
// Sensor em alta resolucao 2 com MTreg = 254 (maximo): 0,11 lx de
// resolucao, cerca de 440 ms por leitura (Quadro 4).
//
// Protocolo (uma linha por comando):
//   ?        -> "ID calibracao v1"
//   D <n>    -> aplica duty n (0..4095)         -> "OK D <n>"
//   M <k>    -> k leituras (1..50)              -> "L <lux>" x k, depois "FIM"
//   Qualquer erro                               -> "ERRO <motivo>"

#include <Wire.h>
#include <BH1750.h>

const int PINO_PWM = 25;
const int FREQ_PWM = 5000;
const int BITS_PWM = 12;
const int DUTY_MAX = 4095;

BH1750 sensor(0x23);
String linha;

void setup() {
  Serial.begin(115200);
  Wire.begin(21, 22);

  ledcAttach(PINO_PWM, FREQ_PWM, BITS_PWM);
  ledcWrite(PINO_PWM, 0);  // comeca apagado

  // Modo CONTINUO: o sensor mede sem parar e cada leitura pega a conversao
  // mais recente. Foi o que funcionou nesta placa; o modo "one time" exigia
  // reconfigurar a cada leitura e devolvia o registrador zerado.
  if (!sensor.begin(BH1750::CONTINUOUS_HIGH_RES_MODE_2)) {
    Serial.println("ERRO sensor BH1750 nao encontrado (confira SDA/SCL/VCC)");
  }
  sensor.setMTreg(BH1750_MTREG_MAX);  // 0,11 lx de resolucao

  // Autoteste: mostra que o sensor responde e quanto demora cada leitura.
  unsigned long t0 = millis();
  float teste = lerLux();
  Serial.printf("ID calibracao v2 | autoteste: %.2f lx em %lu ms\n", teste, millis() - t0);
}

float lerLux() {
  // measurementReady() NAO espera: so informa se ja deu o tempo. E preciso
  // chamar em laco - ler antes da conversao terminar devolve lixo.
  unsigned long limite = millis() + 2000;
  while (!sensor.measurementReady(false)) {
    if (millis() > limite) {
      Serial.println("ERRO conversao do sensor nao terminou");
      return -1;
    }
    delay(10);
  }
  return sensor.readLightLevel();
}

void tratar(String cmd) {
  cmd.trim();
  if (cmd == "?") {
    Serial.println("ID calibracao v1");
  } else if (cmd.startsWith("D ")) {
    long n = cmd.substring(2).toInt();
    if (n < 0 || n > DUTY_MAX) {
      Serial.println("ERRO duty fora de 0..4095");
      return;
    }
    ledcWrite(PINO_PWM, n);
    Serial.print("OK D ");
    Serial.println(n);
  } else if (cmd.startsWith("M ")) {
    long k = cmd.substring(2).toInt();
    if (k < 1 || k > 50) {
      Serial.println("ERRO k fora de 1..50");
      return;
    }
    for (long i = 0; i < k; i++) {
      float lux = lerLux();
      if (lux < 0) {
        Serial.println("ERRO leitura do sensor falhou");
        return;
      }
      Serial.print("L ");
      Serial.println(lux, 2);
    }
    Serial.println("FIM");
  } else if (cmd.length() > 0) {
    Serial.println("ERRO comando desconhecido");
  }
}

void loop() {
  while (Serial.available()) {
    char c = Serial.read();
    if (c == '\n') {
      tratar(linha);
      linha = "";
    } else if (c != '\r') {
      linha += c;
    }
  }
}
