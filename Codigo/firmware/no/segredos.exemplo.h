// MODELO de configuracao do no. Copie este arquivo para "segredos.h" (na
// mesma pasta) e preencha. O segredos.h NAO vai para o git: ele tem a senha
// do Wi-Fi e a credencial do no no broker (RNF06).
#pragma once

// ---- Wi-Fi --------------------------------------------------------------
#define WIFI_SSID  "nome-da-sua-rede"
#define WIFI_SENHA "senha-da-sua-rede"

// ---- Broker MQTT --------------------------------------------------------
// Desenvolvimento: o Mosquitto do docker compose, no seu PC. Use o IP do PC
// na rede local (no Windows: comando `ipconfig`, "Endereco IPv4"), nunca
// "localhost" - para o ESP32, localhost e ele mesmo.
#define MQTT_URI "mqtt://192.168.0.10:1883"

// Na VM (passo 10), com TLS:
//   #define MQTT_URI "mqtts://seu-dominio:8883"
// e cole o certificado da CA em MQTT_CA_PEM abaixo.

// Credencial propria do no (RNF06). Vazio = broker sem senha (so local).
#define MQTT_USUARIO ""
#define MQTT_SENHA   ""

// Certificado da CA em formato PEM, para mqtts://. nullptr = sem TLS.
static const char *MQTT_CA_PEM = nullptr;

// ---- Identidade do ponto de luz -------------------------------------------
// Tem de ser igual ao `codigo` da tabela ponto_de_luz.
#define PONTO "BANCADA-01"
