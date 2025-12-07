#include "DHT.h"

#define DHTPIN 2
#define DHTTYPE DHT11

DHT dht(DHTPIN, DHTTYPE);

void setup() {
  Serial.begin(9600);  // USB serial
  dht.begin();
  Serial.println("Serial listo. Conéctate desde Python.");
}

void loop() {
  float h = dht.readHumidity();
  float t = dht.readTemperature();

  if (isnan(h) || isnan(t)) {
    Serial.println("Error leyendo DHT11");
    return;
  }

  String json = "{\"temperatura\": " + String(t) +
                ", \"humedad\": " + String(h) + "}";

  Serial.println(json);  // ← USB

  delay(3000);
}
