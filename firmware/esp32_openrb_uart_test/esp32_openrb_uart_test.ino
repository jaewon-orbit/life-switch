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
#include <time.h>

#include "secrets.h"

constexpr int OPENRB_TX_PIN = 17;
constexpr int OPENRB_RX_PIN = 18;
constexpr uint32_t BAUDRATE = 115200;

// The ESP32 always initiates this connection, so the home network needs no
// port forwarding.
constexpr char WEBSOCKET_HOST[] = "switch.jaewon-orbit.com";
constexpr uint16_t WEBSOCKET_PORT = 443;
constexpr char WEBSOCKET_PATH[] = "/ws/esp32";

const char *LETSENCRYPT_CHAIN =
"-----BEGIN CERTIFICATE-----\n" \
"MIIE2zCCAsOgAwIBAgIRAKICU/FfJpHAXcHOE7m8yk4wDQYJKoZIhvcNAQELBQAw\n" \
"LjELMAkGA1UEBhMCVVMxDTALBgNVBAoTBElTUkcxEDAOBgNVBAMTB1Jvb3QgWVIw\n" \
"HhcNMjUwOTAzMDAwMDAwWhcNMjgwOTAyMjM1OTU5WjAzMQswCQYDVQQGEwJVUzEW\n" \
"MBQGA1UEChMNTGV0J3MgRW5jcnlwdDEMMAoGA1UEAxMDWVIxMIIBIjANBgkqhkiG\n" \
"9w0BAQEFAAOCAQ8AMIIBCgKCAQEAoVi8X2xCYgMXvJxNPKp/oF13UMgmPABB07VC\n" \
"LNDtoXmt9luEZNJSBV10VyT1Pz6LD8Zq1d2gc43WNl1AdRrj4sEnazbOiz0nPpmG\n" \
"Bp2hui49oZtDIY6wdKeZAi5BbNU20CH6RSBBMLSQ9cXrH8dxdv4PAJ45ssGML68U\n" \
"SE3BsjC2a6cAN9L5CgXVIQi5tfNiTPoFZZ3S0OlXqLmmtdV95udWAb5b6e/F49Di\n" \
"CsH0Y00Ag72BVIb1hzynmKe+X0mERBTtsb3BwmpV9ipeBjMLoR/D9cHxHQCWoi5l\n" \
"TmXwY015J5rGelz1nZjJuxc2kioaX29XJBnhMkP531rSdG5uMwIDAQABo4HuMIHr\n" \
"MA4GA1UdDwEB/wQEAwIBhjATBgNVHSUEDDAKBggrBgEFBQcDATASBgNVHRMBAf8E\n" \
"CDAGAQH/AgEAMB0GA1UdDgQWBBQfLzW+RhSCzUCxrnksVXj699Ro+zAfBgNVHSME\n" \
"GDAWgBTe51tg0CJtQCh9Pw0B/qS1UrRRlDAyBggrBgEFBQcBAQQmMCQwIgYIKwYB\n" \
"BQUHMAKGFmh0dHA6Ly95ci5pLmxlbmNyLm9yZy8wEwYDVR0gBAwwCjAIBgZngQwB\n" \
"AgEwJwYDVR0fBCAwHjAcoBqgGIYWaHR0cDovL3lyLmMubGVuY3Iub3JnLzANBgkq\n" \
"hkiG9w0BAQsFAAOCAgEA0+zvMq3kHig1ddTmmm+RibTr9/RpX7k4buanMMRqbV/y\n" \
"IvP82zAHN3mvaw+cASuVsdpd0ikjhr4hnhJQLQOzOp2ccKrsdGOAgo0vddeISFAq\n" \
"EWEV4lmUM3vFF796up+bSgmJ1u6RupDCMxDgF8M3eLvGuj6L0lu3zkQ0KuQLnKxL\n" \
"tB0oQqn1Idg5CuuGpMvQzk29Pa3D/qHurc0EIM9SxukQuJqq63lxsYyRQFU8yMBO\n" \
"hq1w5LbfaWNRrz1uklOfI/pYkAb2E2MTZrAMQkBIE2S8Jt1F8gRc96o/xOsrgvSk\n" \
"a84AisX6xq1lz1Z7jGvrnXc4TMcjxZTjiTaihcYI1JIXZiLtEMSCa5l3cu8YWd6z\n" \
"dLRQlqRdclVjuQfNHawRJ6GWlkK0QJosivTKwdBw3KxEtzGo8yMHERbsy57gP1UX\n" \
"HOMcmZYQC0gtyR3SxfenIM/MxC3Ia2Ypab/kQ/CTnlIn2KQ5JUC6NYrGCbhFN9bp\n" \
"5lKJStEwCUnLpntcrXk5XVDCNv/5RyWpRThkGOV7GetKkQ0qAY8hCzWK6oqnAhDZ\n" \
"cjlYVdWfqOw3DIOX6EDNBgAqHarRVxyF9QZdOaXSyPJ0ueD2BYJEBgaCGQ8rAaU/\n" \
"Qc123V5LTXDZW4CcsPBDyhy4v+c8hClAyw/IkJlfBqxB9D+/wvIMHgECZ4ptP6o=\n" \
"-----END CERTIFICATE-----\n" \
"-----BEGIN CERTIFICATE-----\n" \
"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\n" \
"-----END CERTIFICATE-----\n";

// Test 2: send several motor toggles directly from the ESP32 after every boot.
constexpr bool TOGGLE_TEST_ON_BOOT = false;
constexpr uint8_t TOGGLE_TEST_COUNT = 3;
constexpr uint32_t TOGGLE_TEST_INTERVAL_MS = 1000;

HardwareSerial openrb(1);
WebSocketsClient vps_websocket;

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

void syncTime() {
  configTime(0, 0, "pool.ntp.org", "time.nist.gov");
  Serial.print("Synchronizing NTP time");

  time_t now = time(nullptr);
  while (now < 100000) {
    delay(500);
    Serial.print('.');
    now = time(nullptr);
  }

  Serial.println("\nNTP time synchronized");
}

void sendOpenrbCommand(const char *command);

void onWebSocketEvent(WStype_t type, uint8_t *payload, size_t length) {
  switch (type) {
    case WStype_DISCONNECTED:
      Serial.println("VPS WebSocket disconnected; remote commands are unavailable");
      break;

    case WStype_CONNECTED:
      Serial.println("VPS WebSocket connected");
      break;

    case WStype_TEXT: {
      String message;
      message.reserve(length);
      for (size_t index = 0; index < length; ++index) {
        message += static_cast<char>(payload[index]);
      }
      Serial.print("VPS -> ESP32: ");
      Serial.println(message);

      if (message == "PING") {
        vps_websocket.sendTXT("PONG");
        Serial.println("ESP32 -> VPS: PONG");
      } else if (message == "ON" || message == "OFF" ||
                 message == "TOGGLE" || message == "STATUS" ||
                 message.startsWith("MOVE ")) {
        sendOpenrbCommand(message.c_str());
      } else {
        Serial.println("Ignoring unknown VPS command");
      }
      break;
    }

    case WStype_ERROR:
      Serial.printf("[WS] Error: %.*s\n",
                    static_cast<int>(length),
                    payload ? reinterpret_cast<char *>(payload) : "(no detail)");
      break;

    default:
      break;
  }
}

void connectWebSocket() {
  vps_websocket.beginSslWithCA(WEBSOCKET_HOST,
                               WEBSOCKET_PORT,
                               WEBSOCKET_PATH,
                               LETSENCRYPT_CHAIN);
  vps_websocket.onEvent(onWebSocketEvent);
  vps_websocket.setReconnectInterval(5000);
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

    if (vps_websocket.isConnected()) {
      String message = "OPENRB ";
      message += openrb_reply;
      vps_websocket.sendTXT(message);
      Serial.print("ESP32 -> VPS: ");
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
  syncTime();
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
  vps_websocket.loop();
  readPcCommands();
  readOpenrbReplies();
}
