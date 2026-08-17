// Minimal ESP32 USB serial output test.
// Open Serial Monitor at 115200 baud.

void setup() {
  Serial.begin(115200);
  delay(1000);
  Serial.println("===== SERIAL TEST =====");
}

void loop() {
  Serial.println("HELLO");
  delay(2000);
}
