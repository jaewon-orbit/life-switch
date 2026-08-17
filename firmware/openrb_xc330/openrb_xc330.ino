// OpenRB-150 <-> ESP32 UART wiring test.
// OpenRB USB-C: Serial Monitor at 115200 baud
// ESP32 link: Serial3 at 115200 baud (OpenRB D13/RX, D14/TX)

constexpr uint32_t UART_BAUDRATE = 115200;

void setup() {
  Serial.begin(UART_BAUDRATE);
  Serial3.begin(UART_BAUDRATE);

  delay(500);

  Serial.println("OpenRB UART TEST READY");
}

void loop() {
  if (Serial3.available()) {
    String msg = Serial3.readStringUntil('\n');

    Serial.print("RECEIVED: [");
    Serial.print(msg);
    Serial.println("]");

    Serial3.println("PONG");
  }
}
