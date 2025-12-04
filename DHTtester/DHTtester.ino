#include "BluetoothSerial.h"
#include "DHT.h"

#define DHTPIN 2
#define DHTTYPE DHT11

DHT dht(DHTPIN, DHTTYPE);

BluetoothSerial SerialBT;  // Bluetooth Serial

void setup() {
  Serial.begin(9600);
  SerialBT.begin("ESP32_DHT");  // Nombre del dispositivo Bluetooth
  
  dht.begin();
  Serial.println("Bluetooth listo. Conéctate desde la PC.");
}

void loop() {
  float h = dht.readHumidity();
  float t = dht.readTemperature();

  if (isnan(h) || isnan(t)) {
    Serial.println("Error leyendo DHT11");
    return;
  }

  // Enviar por Bluetooth en formato JSON
  String json = "{\"temperatura\": " + String(t) +
                ", \"humedad\": " + String(h) + "}";

  SerialBT.println(json);
  Serial.println("Enviado: " + json);

  delay(3000);  // Cada 3 segundos
}
