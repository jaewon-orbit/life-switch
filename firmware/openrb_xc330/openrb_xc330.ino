/*
 * ESP32 -> OpenRB-150 -> XC330-M288-T motor controller.
 *
 * ESP32 wiring (ESP32-S3 DevKitC):
 *   GPIO17 (TX) -> OpenRB D13 (Serial3 RX)
 *   GPIO18 (RX) -> OpenRB D14 (Serial3 TX)
 *   GND        -> OpenRB GND
 *
 * Send one newline-terminated command from the ESP32:
 *   PING             -> PONG
 *   ON               -> move to ON_POSITION
 *   OFF              -> move to OFF_POSITION
 *   TOGGLE           -> move to the opposite position
 *   MOVE <0-4095>    -> move to an explicit position
 *   STATUS           -> STATUS <current-position>
 *
 * The motor torque is released after each completed move, so it makes one
 * movement and then stops without continuously holding force. Replies are
 * sent back to the ESP32 on Serial3. The USB Serial port is only used for
 * optional debugging. Install the DYNAMIXEL2Arduino library and select the
 * OpenRB-150 board before uploading.
 */

#include <Arduino.h>
#include <Dynamixel2Arduino.h>

constexpr uint32_t DEBUG_BAUDRATE = 115200;
constexpr uint32_t ESP32_BAUDRATE = 115200;
constexpr uint32_t DXL_BAUDRATE = 57600;

constexpr uint8_t DXL_ID = 1;  // XC330-M288-T motor ID
constexpr int32_t OFF_POSITION = 400;
constexpr int32_t ON_POSITION = 2448;  // 400 + 2048: approximately 180 degrees
constexpr int32_t POSITION_MIN = 0;
constexpr int32_t POSITION_MAX = 4095;
constexpr int32_t POSITION_TOLERANCE = 20;
constexpr uint32_t MOVE_TIMEOUT_MS = 10000;

constexpr int DXL_DIR_PIN = -1;

HardwareSerial &dxl_serial = Serial1;
Dynamixel2Arduino dxl(dxl_serial, DXL_DIR_PIN);

char command_buffer[32];
size_t command_length = 0;
char usb_command_buffer[32];
size_t usb_command_length = 0;

void reply(const char *message) {
  Serial3.println(message);
  Serial.print("ESP32 reply: ");
  Serial.println(message);
}

void replyPosition(const char *prefix, int32_t position) {
  char message[48];
  snprintf(message, sizeof(message), "%s %ld", prefix,
           static_cast<long>(position));
  reply(message);
}

bool readPosition(int32_t &position) {
  const float value = dxl.getPresentPosition(DXL_ID);

  if (dxl.getLastLibErrCode() != 0) {
    reply("ERROR READ_POSITION");
    return false;
  }

  position = static_cast<int32_t>(value);
  return true;
}

bool moveTo(int32_t goal) {
  if (goal < POSITION_MIN || goal > POSITION_MAX) {
    reply("ERROR INVALID_POSITION");
    return false;
  }

  dxl.torqueOn(DXL_ID);
  if (!dxl.setGoalPosition(DXL_ID, goal)) {
    reply("ERROR SET_GOAL");
    return false;
  }

  const uint32_t started_at = millis();
  int32_t position = 0;
  while (millis() - started_at < MOVE_TIMEOUT_MS) {
    if (!readPosition(position)) return false;
    if (abs(goal - position) <= POSITION_TOLERANCE) {
      dxl.torqueOff(DXL_ID);
      replyPosition("DONE", position);
      return true;
    }
    delay(25);
  }

  dxl.torqueOff(DXL_ID);
  reply("ERROR MOVE_TIMEOUT");
  return false;
}

void handleCommand(char *command) {
  while (*command == ' ' || *command == '\t') ++command;
  for (char *p = command; *p != '\0'; ++p) *p = toupper(*p);

  if (strcmp(command, "PING") == 0) {
    reply("PONG");
  } else if (strcmp(command, "ON") == 0) {
    moveTo(ON_POSITION);
  } else if (strcmp(command, "OFF") == 0) {
    moveTo(OFF_POSITION);
  } else if (strcmp(command, "STATUS") == 0) {
    int32_t position = 0;
    if (readPosition(position)) replyPosition("STATUS", position);
  } else if (strcmp(command, "TOGGLE") == 0) {
    int32_t position = 0;
    if (!readPosition(position)) return;
    moveTo(abs(position - ON_POSITION) < abs(position - OFF_POSITION)
               ? OFF_POSITION
               : ON_POSITION);
  } else if (strncmp(command, "MOVE ", 5) == 0) {
    char *end = nullptr;
    const long goal = strtol(command + 5, &end, 10);
    while (*end == ' ' || *end == '\t') ++end;
    if (end == command + 5 || *end != '\0') {
      reply("ERROR INVALID_COMMAND");
      return;
    }
    moveTo(static_cast<int32_t>(goal));
  } else {
    reply("ERROR UNKNOWN_COMMAND");
  }
}

void readCommands(Stream &input, char *buffer, size_t &length) {
  while (input.available() > 0) {
    const char received = static_cast<char>(input.read());
    if (received == '\n') {
      buffer[length] = '\0';
      handleCommand(buffer);
      length = 0;
    } else if (received != '\r' && length < sizeof(command_buffer) - 1) {
      buffer[length++] = received;
    } else if (length == sizeof(command_buffer) - 1) {
      length = 0;
      reply("ERROR COMMAND_TOO_LONG");
    }
  }
}

void setup() {
  Serial.begin(DEBUG_BAUDRATE);
  Serial3.begin(ESP32_BAUDRATE);  // OpenRB D13 (RX), D14 (TX)

  dxl.begin(DXL_BAUDRATE);
  dxl.setPortProtocolVersion(2.0);

  if (!dxl.ping(DXL_ID)) {
    Serial.println("ERROR: XC330 not found");
    Serial3.println("ERROR MOTOR_NOT_FOUND");
    return;
  }

  delay(300);
  Serial.println("OpenRB XC330 ESP32 controller ready");
  reply("READY");
}

void loop() {
  // Type the same commands in the Arduino IDE Serial Monitor, or send them
  // from the ESP32 over Serial3.
  readCommands(Serial, usb_command_buffer, usb_command_length);
  readCommands(Serial3, command_buffer, command_length);
}
