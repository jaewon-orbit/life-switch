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

## VPS WebSocket relay

This sketch opens a persistent outbound WebSocket connection to the FastAPI
endpoint at `/ws/esp32`. The server sends `PING`; the ESP32 replies with
`PONG`. It reconnects every five seconds after a lost connection. Browser
commands (`ON`, `OFF`, `TOGGLE`, and `STATUS`) are forwarded to the OpenRB over
UART, and replies are returned to the VPS. No inbound home-network connection
or port forwarding is required.

1. For a development test, start FastAPI on the VPS:

   ```bash
   python -m uvicorn src.server:app --host 0.0.0.0 --port 8000
   ```

2. In Arduino IDE's Library Manager, install **WebSockets** by Markus Sattler.
3. Copy `secrets.h.example` to `secrets.h`. Set `WIFI_SSID` and
   `WIFI_PASSWORD`. For the initial non-TLS VPS test, keep `VPS_HOST` as the
   VPS IP, `VPS_PORT` as `8000`, and `VPS_USE_TLS` as `0`. Do not commit this
   file. For production, set the DNS hostname, port `443`, and `VPS_USE_TLS`
   to `1`.
4. Upload this sketch to the ESP32 and open its Serial Monitor at 115200 baud.
   It should log `VPS WebSocket connected`, followed by a `PING` and a
   `PONG` about every ten seconds.
5. Visit `http://167.99.79.3:8000/api/esp32/status` to confirm a successful
   connection. It returns `"connected": true` and a recent `"last_pong_at"`.
6. Open the browser UI configured for the VPS. It uses `/ws/client`, which
   relays its command to the ESP32 and waits for the OpenRB reply before
   updating the UI.

If the ESP32 loses its VPS connection, it accepts no more remote commands. An
already-started move is bounded by the OpenRB's 10-second move timeout and it
releases motor torque when it completes or times out.

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
