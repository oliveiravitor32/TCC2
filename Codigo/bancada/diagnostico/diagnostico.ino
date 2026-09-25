// Diagnostico rapido da bancada: acha o BH1750, dimeriza a fita e imprime
// duty + lux continuamente. NAO e o firmware nem a calibracao - e so para
// descobrir por que o sensor nao esta lendo.
//
// Monitor Serial em 115200.
//
// Ligacoes esperadas: SDA=21, SCL=22, VCC=3V3, GND comum; PWM=25.

#include <Wire.h>
#include <BH1750.h>

const int PINO_PWM = 25;
const int DUTY_MAX = 4095;

BH1750 sensor;
uint8_t enderecoAchado = 0;
int duty = 0;
int passo = 64;

// Pares (SDA, SCL) testados: o esperado, o invertido e outros comuns.
const int PARES[][2] = {{21, 22}, {22, 21}, {4, 5}, {32, 33}, {33, 32}, {19, 18}};
const int N_PARES = sizeof(PARES) / sizeof(PARES[0]);
int sdaUsado = 21, sclUsado = 22;

// Varre o barramento nos pinos atuais e mostra tudo o que responder.
uint8_t varrer(int sda, int scl, bool detalhar) {
  Wire.end();
  Wire.begin(sda, scl);
  delay(50);
  uint8_t achado = 0;
  for (uint8_t a = 1; a < 127; a++) {
    Wire.beginTransmission(a);
    if (Wire.endTransmission() == 0) {
      if (detalhar) Serial.printf("  SDA=%d SCL=%d -> dispositivo em 0x%02X", sda, scl, a);
      if (a == 0x23 || a == 0x5C) {
        if (detalhar) Serial.print("  <- BH1750");
        achado = a;
      }
      if (detalhar) Serial.println();
    }
  }
  return achado;
}

uint8_t procurarSensor() {
  Serial.println("\n--- varredura I2C (varios pares de pinos) ---");
  for (int i = 0; i < N_PARES; i++) {
    uint8_t achado = varrer(PARES[i][0], PARES[i][1], true);
    if (achado) {
      sdaUsado = PARES[i][0];
      sclUsado = PARES[i][1];
      Serial.printf("ACHOU: BH1750 em 0x%02X com SDA=%d, SCL=%d\n", achado, sdaUsado, sclUsado);
      Serial.println("-------------------------------------------\n");
      return achado;
    }
  }
  Serial.println("NADA respondeu em nenhum par de pinos.");
  Serial.println("Nao e pino trocado. Verifique, nesta ordem:");
  Serial.println("  1. VCC do sensor no 3V3 do ESP32 (nao 5V, nao VIN)");
  Serial.println("  2. GND do sensor no GND do ESP32");
  Serial.println("  3. fios/emendas abertos (teste ligando direto, sem extensao)");
  Serial.println("  4. soldas do GY-302");
  Serial.println("-------------------------------------------\n");
  // Volta ao barramento padrao para as proximas tentativas.
  Wire.end();
  Wire.begin(21, 22);
  return 0;
}

void setup() {
  Serial.begin(115200);
  delay(300);

  ledcAttach(PINO_PWM, 5000, 12);
  ledcWrite(PINO_PWM, 0);

  enderecoAchado = procurarSensor();
  if (enderecoAchado) {
    if (sensor.begin(BH1750::CONTINUOUS_HIGH_RES_MODE_2, enderecoAchado)) {
      sensor.setMTreg(BH1750_MTREG_MAX);  // 0,11 lx, ~440 ms por leitura
      Serial.println("sensor iniciado. duty / lux:");
    } else {
      Serial.println("ERRO: sensor achado no barramento mas nao iniciou.");
      enderecoAchado = 0;
    }
  }
}

void loop() {
  // Sobe e desce o brilho para ver a lux acompanhar.
  duty += passo;
  if (duty >= DUTY_MAX) { duty = DUTY_MAX; passo = -passo; }
  if (duty <= 0)        { duty = 0;        passo = -passo; }
  ledcWrite(PINO_PWM, duty);

  if (!enderecoAchado) {
    Serial.printf("duty %4d (%3d%%) | sensor ausente - a fita deve estar variando\n",
                  duty, duty * 100 / DUTY_MAX);
    // Sem sensor, tenta de novo de vez em quando (mau contato intermitente).
    static int tentativas = 0;
    if (++tentativas % 20 == 0) {
      enderecoAchado = procurarSensor();
      if (enderecoAchado) {
        sensor.begin(BH1750::CONTINUOUS_HIGH_RES_MODE_2, enderecoAchado);
        sensor.setMTreg(BH1750_MTREG_MAX);
      }
    }
    delay(500);
    return;
  }

  while (!sensor.measurementReady(false)) {
    delay(10);
  }
  float lux = sensor.readLightLevel();
  Serial.printf("duty %4d (%3d%%) | lux %8.2f%s\n",
                duty, duty * 100 / DUTY_MAX, lux,
                lux < 0 ? "   <- LEITURA INVALIDA" : "");
  delay(100);
}
