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
#include <WiFi.h>
#include <WebSocketsClient.h>

#include "secrets.h"

constexpr int OPENRB_TX_PIN = 17;
constexpr int OPENRB_RX_PIN = 18;
constexpr uint32_t BAUDRATE = 115200;

// Test 3-2: set CLOUDFLARE_TUNNEL_HOST in secrets.h to the hostname printed
// by `bash scripts/start_quick_tunnel.sh` (without https:// or a path).
constexpr uint16_t CLOUDFLARE_HTTPS_PORT = 443;
constexpr char WEBSOCKET_PATH[] = "/ws/esp32";

// Test 2: send several motor toggles directly from the ESP32 after every boot.
constexpr bool TOGGLE_TEST_ON_BOOT = false;
constexpr uint8_t TOGGLE_TEST_COUNT = 3;
constexpr uint32_t TOGGLE_TEST_INTERVAL_MS = 1000;

HardwareSerial openrb(1);
WebSocketsClient cloudflare_websocket;

char pc_command[32];
size_t pc_command_length = 0;
char openrb_reply[64];
size_t openrb_reply_length = 0;

void connectWiFi() {
  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

  Serial.print("Connecting to Wi-Fi");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print('.');
  }

  Serial.println();
  Serial.print("Wi-Fi connected. ESP32 IP: ");
  Serial.println(WiFi.localIP());
}

void sendOpenrbCommand(const char *command);

void onWebSocketEvent(WStype_t type, uint8_t *payload, size_t length) {
  switch (type) {
    case WStype_DISCONNECTED:
      Serial.println("Cloudflare WebSocket disconnected");
      break;

    case WStype_CONNECTED:
      Serial.println("Cloudflare WebSocket connected");
      break;

    case WStype_TEXT: {
      String message;
      message.reserve(length);
      for (size_t index = 0; index < length; ++index) {
        message += static_cast<char>(payload[index]);
      }
      Serial.print("Cloudflare -> ESP32: ");
      Serial.println(message);

      if (message == "PING") {
        cloudflare_websocket.sendTXT("PONG");
        Serial.println("ESP32 -> Cloudflare: PONG");
      } else if (message == "ON" || message == "OFF" ||
                 message == "TOGGLE" || message == "STATUS" ||
                 message.startsWith("MOVE ")) {
        sendOpenrbCommand(message.c_str());
      } else {
        Serial.println("Ignoring unknown Cloudflare command");
      }
      break;
    }

    case WStype_ERROR:
      Serial.println("Cloudflare WebSocket error");
      break;

    default:
      break;
  }
}

void connectWebSocket() {
  cloudflare_websocket.beginSSL(CLOUDFLARE_TUNNEL_HOST,
                                CLOUDFLARE_HTTPS_PORT,
                                WEBSOCKET_PATH);
  cloudflare_websocket.onEvent(onWebSocketEvent);
  cloudflare_websocket.setReconnectInterval(5000);
}

void forwardPcCommand() {
  pc_command[pc_command_length] = '\0';
  if (pc_command_length > 0) {
    openrb.println(pc_command);
    Serial.print("ESP32 -> OpenRB: ");
    Serial.println(pc_command);
  }
  pc_command_length = 0;
}

void sendOpenrbCommand(const char *command) {
  openrb.println(command);
  Serial.print("ESP32 -> OpenRB: ");
  Serial.println(command);
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

    if (cloudflare_websocket.isConnected()) {
      String message = "OPENRB ";
      message += openrb_reply;
      cloudflare_websocket.sendTXT(message);
      Serial.print("ESP32 -> Cloudflare: ");
      Serial.println(message);
    }
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
  connectWiFi();
  connectWebSocket();
  openrb.begin(BAUDRATE, SERIAL_8N1, OPENRB_RX_PIN, OPENRB_TX_PIN);

  delay(1000);  // Give the OpenRB serial port time to finish starting.
  Serial.println("ESP32 OpenRB motor command bridge ready");
  Serial.println("Type ON, OFF, TOGGLE, STATUS, or MOVE 2048 and press Send.");

  if (TOGGLE_TEST_ON_BOOT) {
    Serial.println("Test 2: sending 3 automatic TOGGLE commands");
    for (uint8_t toggle_number = 1; toggle_number <= TOGGLE_TEST_COUNT;
         ++toggle_number) {
      Serial.print("Test 2 toggle ");
      Serial.print(toggle_number);
      Serial.print('/');
      Serial.println(TOGGLE_TEST_COUNT);
      sendOpenrbCommand("TOGGLE");

      if (toggle_number < TOGGLE_TEST_COUNT) {
        delay(TOGGLE_TEST_INTERVAL_MS);
      }
    }
  }
}

void loop() {
  cloudflare_websocket.loop();
  readPcCommands();
  readOpenrbReplies();
}
