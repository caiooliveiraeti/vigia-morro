#include <Arduino.h>
#include <DHT.h>

// ==== PINOS ====
#define PIN_DHT        2       // Sensor DHT22 para medir umidade

#define DHTTYPE DHT22
DHT dht(PIN_DHT, DHTTYPE);

float ler_umidade_solo() {
  float umidade = dht.readHumidity();
  return isnan(umidade) ? -1 : umidade; // Retorna -1 se a leitura falhar
}

float ler_temperatura_solo() {
  float temperatura = dht.readTemperature();
  return isnan(temperatura) ? -1 : temperatura; // Retorna -1 se a leitura falhar
}

void enviar_dados_serial(float umidade, float temperatura) {
  // Envia os dados dos sensores e o modo de decisão via Serial
  Serial.print("DATA:");
  Serial.print("MID="); Serial.print("550e8400-e29b-41d4-a716-446655440000"); Serial.print(",");
  Serial.print("CID="); Serial.print("CAIXA001"); Serial.print(",");
  Serial.print("H="); Serial.print(umidade, 2); Serial.print(",");
  Serial.print("T="); Serial.print(temperatura, 2); Serial.println();
}

void setup() {
  Serial.begin(115200);
  dht.begin();
}

void loop() {
  float umidade = ler_umidade_solo();
  float temperatura = ler_temperatura_solo();

  enviar_dados_serial(umidade, temperatura); // Envia os dados via Serial

  delay(1000); // Aguarda 2 segundos antes de repetir o loop
}