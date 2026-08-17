/*
 * ESP32 -> OpenRB-150 command bridge for the XC330 switch motor.
 *
 * Wire the ESP32-S3 to the OpenRB:
 *   GPIO17 (ESP32 TX) -> D13 (OpenRB Serial3 RX)
 *   GPIO18 (ESP32 RX) -> D14 (OpenRB Serial3 TX)
 *   GND               -> GND
 *
 * Upload firmware/openrb_xc330/openrb_xc330.ino to the OpenRB first.
 * Then upload this sketch to the ESP32. In the ESP32 Serial Monitor (115200
 * baud, Newline), type ON, OFF, TOGGLE, STATUS, or MOVE 2048.
 */

#include <Arduino.h>

constexpr int OPENRB_TX_PIN = 17;
constexpr int OPENRB_RX_PIN = 18;
constexpr uint32_t BAUDRATE = 115200;

HardwareSerial openrb(1);

char pc_command[32];
size_t pc_command_length = 0;
char openrb_reply[64];
size_t openrb_reply_length = 0;

void forwardPcCommand() {
  pc_command[pc_command_length] = '\0';
  if (pc_command_length > 0) {
    openrb.println(pc_command);
    Serial.print("ESP32 -> OpenRB: ");
    Serial.println(pc_command);
  }
  pc_command_length = 0;
}

void readPcCommands() {
  while (Serial.available() > 0) {
    const char received = static_cast<char>(Serial.read());
    if (received == '\n') {
      forwardPcCommand();
    } else if (received != '\r' && pc_command_length < sizeof(pc_command) - 1) {
      pc_command[pc_command_length++] = received;
    } else if (pc_command_length == sizeof(pc_command) - 1) {
      pc_command_length = 0;
      Serial.println("ERROR: command is too long");
    }
  }
}

void printOpenrbReply() {
  openrb_reply[openrb_reply_length] = '\0';
  if (openrb_reply_length > 0) {
    Serial.print("OpenRB -> ESP32: ");
    Serial.println(openrb_reply);
  }
  openrb_reply_length = 0;
}

void readOpenrbReplies() {
  while (openrb.available() > 0) {
    const char received = static_cast<char>(openrb.read());
    if (received == '\n') {
      printOpenrbReply();
    } else if (received != '\r' && openrb_reply_length < sizeof(openrb_reply) - 1) {
      openrb_reply[openrb_reply_length++] = received;
    } else if (openrb_reply_length == sizeof(openrb_reply) - 1) {
      openrb_reply_length = 0;
      Serial.println("ERROR: OpenRB reply is too long");
    }
  }
}

void setup() {
  Serial.begin(BAUDRATE);
  openrb.begin(BAUDRATE, SERIAL_8N1, OPENRB_RX_PIN, OPENRB_TX_PIN);

  delay(300);
  Serial.println("ESP32 OpenRB motor command bridge ready");
  Serial.println("Type ON, OFF, TOGGLE, STATUS, or MOVE 2048 and press Send.");
}

void loop() {
  readPcCommands();
  readOpenrbReplies();
}
