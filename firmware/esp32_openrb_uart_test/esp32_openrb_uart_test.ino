#include <Arduino.h>

// ESP32-S3-WROOM-1-N16R8 DevKitC-style board: GPIO17/GPIO18 are exposed
// UART1 TX/RX header pins. UART0 GPIO43/GPIO44 stays dedicated to the
// USB-UART COM debug console.
constexpr int OPENRB_TX_PIN = 17;
constexpr int OPENRB_RX_PIN = 18;
constexpr uint32_t OPENRB_BAUDRATE = 115200;
constexpr uint32_t PING_INTERVAL_MS = 2000;

HardwareSerial openrb(1);
char reply_buffer[64];
size_t reply_length = 0;
uint32_t next_ping_at = 0;

void printReplyLine() {
  reply_buffer[reply_length] = '\0';
  char *reply = reply_buffer;
  while (*reply == ' ' || *reply == '\t') ++reply;
  char *end = reply + strlen(reply);
  while (end > reply && (end[-1] == ' ' || end[-1] == '\t' ||
                         end[-1] == '\r' || end[-1] == '\n')) {
    *--end = '\0';
  }
  if (*reply != '\0') {
    Serial.print("OpenRB -> ESP32: ");
    Serial.println(reply);
  }
  reply_length = 0;
}

void readOpenRB() {
  while (openrb.available() > 0) {
    const char received = static_cast<char>(openrb.read());
    if (received == '\n') {
      printReplyLine();
    } else if (reply_length < sizeof(reply_buffer) - 1) {
      reply_buffer[reply_length++] = received;
    } else {
      reply_length = 0;  // Discard an overlong line.
    }
  }
}

void setup() {
  // Keep USB CDC On Boot Disabled. Serial uses UART0 through /dev/ttyACM0.
  Serial.begin(115200);
  openrb.begin(OPENRB_BAUDRATE, SERIAL_8N1, OPENRB_RX_PIN, OPENRB_TX_PIN);

  delay(300);
  Serial.println("================================");
  Serial.println("ESP32 <-> OpenRB UART TEST");
  Serial.println("================================");
  Serial.println("ESP32 UART initialized.");
  Serial.println("OpenRB UART initialized.");
}

void loop() {
  readOpenRB();

  const uint32_t now = millis();
  if (static_cast<int32_t>(now - next_ping_at) >= 0) {
    openrb.print("PINGING\n");
    Serial.println("ESP32 -> OpenRB: PINGING");
    next_ping_at = now + PING_INTERVAL_MS;
  }
}
