# ESP32-S3 ↔ OpenRB-150 UART test

The test keeps the ESP32 PC console and the OpenRB link electrically separate.

## Exact wiring

| ESP32-S3-WROOM-1-N16R8 header pin | Signal | OpenRB-150 pin | Signal |
| --- | --- | --- | --- |
| GPIO17 | UART1 TX | D13 | Serial3 RX |
| GPIO18 | UART1 RX | D14 | Serial3 TX |
| GND | Ground | GND | Ground |

Both boards use 3.3 V logic. Do not connect a 5 V pin between them.

GPIO17/18 are exposed on the DevKitC-style N16R8 header and are assigned to
UART1 TX/RX. They are not boot strapping pins, USB D-/D+ (GPIO19/20), UART0
COM pins (GPIO43/44), or N16R8 OPI flash/PSRAM pins (GPIO26-32, GPIO33-37).
Arduino-ESP32 routes `HardwareSerial(1)` to this pair through the GPIO matrix.

## Test 3-2 — Cloudflare WebSocket PING/PONG

This sketch opens an outbound secure WebSocket connection to the FastAPI
endpoint at `/ws/esp32`. The server sends `PING`; the ESP32 replies with
`PONG`. For Test 3-3, it also forwards `ON`, `OFF`, `TOGGLE`, `STATUS`, and
`MOVE <position>` commands to the OpenRB over UART, then returns its replies.

1. Start FastAPI and the Quick Tunnel on the PC:

   ```bash
   python -m uvicorn src.server:app --host 127.0.0.1 --port 8000
   bash scripts/start_quick_tunnel.sh
   ```

2. In Arduino IDE's Library Manager, install **WebSockets** by Markus Sattler.
3. Copy `secrets.h.example` to `secrets.h`. Set `WIFI_SSID`,
   `WIFI_PASSWORD`, and `CLOUDFLARE_TUNNEL_HOST`. The host is the
   `…trycloudflare.com` portion printed by the tunnel command—do not include
   `https://` or `/ws/esp32`.
4. Upload this sketch to the ESP32 and open its Serial Monitor at 115200 baud.
   It should log `Cloudflare WebSocket connected`, followed by a `PING` and a
   `PONG` about every ten seconds.
5. From the phone or PC, open
   `https://YOUR-TUNNEL.trycloudflare.com/api/esp32/status`. A successful test
   returns `"connected": true` and a recent `"last_pong_at"` timestamp.
6. For Test 3-3, open `https://YOUR-TUNNEL.trycloudflare.com/xc330` from the
   phone over LTE. The existing UI calls FastAPI, which relays its command to
   the ESP32 and waits for the OpenRB reply before updating the UI.

Each Quick Tunnel restart gives you a new hostname, so update
`CLOUDFLARE_TUNNEL_HOST` and upload the ESP32 sketch again before reconnecting.

## ESP32 Arduino IDE settings

* **Board:** ESP32S3 Dev Module (or matching ESP32-S3 DevKitC-1)
* **USB CDC On Boot:** Disabled
* **Port:** `/dev/ttyACM0`
* **Serial Monitor:** 115200 baud
* **Flash Size:** 16 MB
* **PSRAM:** OPI PSRAM

Leave USB Mode and Upload Mode at the already-working USB-UART COM values;
they are unrelated to the board-to-board UART.

Upload `esp32_openrb_uart_test.ino`. With OpenRB disconnected, only the
banner and `ESP32 -> OpenRB: PINGING` appear every two seconds. With the
OpenRB sketch below loaded and wired, each send is followed by
`OpenRB -> ESP32: PONG`.

## Minimal OpenRB-150 sketch

`Serial3` is the board-to-board link; D13/D14 must not be connected to an
OpenRB PC console.

```cpp
#include <Arduino.h>

constexpr uint32_t UART_BAUDRATE = 115200;

void setup() {
  Serial.begin(115200);          // Separate OpenRB USB/PC console
  Serial3.begin(UART_BAUDRATE);  // D13 = RX, D14 = TX
}

void loop() {
  static char line[16];
  static size_t length = 0;

  while (Serial3.available() > 0) {
    const char c = static_cast<char>(Serial3.read());
    if (c == '\n') {
      line[length] = '\0';
      if (strcmp(line, "PINGING") == 0) Serial3.print("PONG\n");
      length = 0;
    } else if (c != '\r' && length < sizeof(line) - 1) {
      line[length++] = c;
    } else if (length == sizeof(line) - 1) {
      length = 0;
    }
  }
}
```
