#include <Arduino.h>
// ==== PINOS ====
#define PIN_RELAY      26      // Relé para controlar a sirene de sirene

void setup_pinos() {
  // Configura os pinos como entrada ou saída
  pinMode(PIN_RELAY, OUTPUT);
}

void decidir_alerta_externa() {
  // Aguarda comandos via Serial para ativar ou desativar a sirene
  unsigned long t0 = millis();
  while (millis() - t0 < 50) { // Espera até 50 ms por um comando
    if (Serial.available()) {
      char cmd = Serial.read();
      if (cmd == '1' || cmd == '0') {
        executar_alerta_local(cmd == '1'); // Executa sirene com base no comando
      }
      break;
    }
  }
}

void executar_alerta_local(bool ligar) {
  // Liga ou desliga a sirene de sirene e registra no log
  if (ligar) {
    digitalWrite(PIN_RELAY, HIGH);
    Serial.println("LOG:[INFO] Alerta ATIVO.");
  } else {
    digitalWrite(PIN_RELAY, LOW);
    Serial.println("LOG:[INFO] Alerta DESLIGADO.");
  }
}

void setup() {
  // Configura o sistema e inicializa os sensores
  Serial.begin(115200);
  setup_pinos();
  digitalWrite(PIN_RELAY, LOW); // Garante que a sirene começa desligada
  Serial.println("LOG:Sistema de alerta iniciado!");
}

void loop() {
  
  decidir_alerta_externa();
  
  delay(500); // Aguarda 2 segundos antes de repetir o loop
}
