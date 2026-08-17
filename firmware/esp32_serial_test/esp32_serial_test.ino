void setup() {
  Serial.begin(115200);
  delay(1000);

  Serial.println("===== ESP32 TEST =====");
  Serial.println("ESP32 IS ALIVE");
}

void loop() {
  Serial.println("RUNNING");
  delay(1000);
}
