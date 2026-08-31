# 💡 Life Switch

Control physical switch in the real world, remotely.
<br>
<br>
# Why Life Switch?
During a summer heat wave, I wanted to turn on the air conditioner before getting home. <br>
Another time, I left home and suddenly wondered, "Did I turn off the air conditioner?"
<br><br>
There's many devices still require physical interaction.
<br>
Long story short, I need it.
Hope it’s easy to make.
<br>
<br>
# now now now Latest Updates

### 1. Remote Control over LTE

Successfully controlled the motor remotely from a mobile browser over LTE using Cloudflare Tunnel.

<img src="./docs/images/motor_move_LTE.png" width="200" alt="Motor controlled remotely over LTE">

### 2. Motor Change: XM430 → XC330

Changed the motor from XM430 to XC330-M288T-T, which is smaller and more suitable for the physical switch prototype.

The motor control code was also refactored to use motor profiles instead of motor-specific rotation values. This allows different motors to be tested without changing the core control logic.

### 3. UI Revamp

Redesigned the browser UI to make the remote switch control simpler and more intuitive.

| Before | After |
|:---:|:---:|
| <img src="./docs/images/ui-before.jpg" width="200"> | <img src="./docs/images/ui-revamp.jpg" width="200"> |

### 4. Next? Standalone Control

The next goal is to control the switch independently from a PC.

ESP32 + OpenRB-150 will be used to connect the motor to the internet and enable remote control from a mobile device.

Planned architecture:

Mobile Browser
→ Internet / LTE
→ ESP32
→ OpenRB-150
→ XC330
→ Physical Switch

WebSocket is being considered for bidirectional communication, with a custom domain potentially used for the remote connection.

Also, I will gonna use current-based control instead of position control to improve safety.

### 5. OpenRB-150 XC330 control (current test setup)

OpenRB-150 now controls the XC330-M288-T directly. The firmware in
[`firmware/openrb_xc330/`](./firmware/openrb_xc330/) receives commands over its
USB connection and runs a 180° return trip at the configured speed; it turns
torque and DYNAMIXEL power off when finished.


run this scripts to move the motor with OpenRB
(my port is (/dev/ttyACM0))

```bash
python scripts/move_openrb_xc330.py --port /dev/ttyACM0
```

this sends `MOVE` to the OpenRB. Existing
[`scripts/move_motor.py`](./scripts/move_motor.py) remains the separate U2D2
motor-control script.

### 6. ESP32 Control

Successfully controlled the robot with ESP32, using OpenRB as the motor control interface.
Starting from the ground up is always the key to solving complex problems.

<img src="./docs/images/esp32_openrb_motor.jpg" width="400" alt="ESP32 and OpenRB motor control setup">

<br>
<br>

## VPS WebSocket relay

The standalone architecture is now:

`GitHub Pages browser → /ws/client on VPS → existing outbound ESP32 /ws/esp32 → UART → OpenRB-150 → XC330`

The ESP32 is always the connecting side and reconnects automatically; do not
configure home-network port forwarding. Browser and ESP32 connection state are
shown separately in the web UI. The existing HTTP API routes remain available
for local troubleshooting, but GitHub Pages uses the WebSocket relay.

For initial development, the web scripts use
`ws://167.99.79.3:8000/ws/client`. Change the public `WS_URL` setting in
`web/app.js` and `web/xc330_app.js` to
`wss://YOUR_VPS_DOMAIN/ws/client` before publishing the HTTPS GitHub Pages
site; an HTTPS page cannot open an insecure `ws://` connection.

### VPS deployment

The service and Nginx templates in [`deploy/`](./deploy/) use `/opt/life-switch`
and a dedicated `life-switch` system user. They proxy both ordinary HTTP and
WebSocket upgrade requests, so Nginx can later terminate HTTPS/WSS. See the
deployment commands in the project handoff for the exact first-install steps.

## Test 3-1 — FastAPI through a Cloudflare Quick Tunnel

Use this temporary setup to access the existing XC330 web UI from a phone on
LTE. It does not need a custom domain or a Cloudflare account.

In the first terminal, start the existing FastAPI server:

```bash
python -m uvicorn src.server:app --host 127.0.0.1 --port 8000
```

In a second terminal, create the Quick Tunnel:

```bash
bash scripts/start_quick_tunnel.sh
```

`cloudflared` prints an `https://…trycloudflare.com` URL. Open that exact URL
on the phone while Wi-Fi is turned off. The root URL redirects to `/xc330`
when the XC330 is connected; otherwise open `https://…trycloudflare.com/xc330`.

The Quick Tunnel URL is random and stops working as soon as `cloudflared` is
stopped. Treat it like a temporary public remote-control link: share it only
with people you trust. The FastAPI server stays bound to `127.0.0.1`, so only
the Cloudflare tunnel exposes it externally.

# Roadmap

### Phase 1 — Motor Control

* Developing in Linux (done)
* Set up Python environment (done)
* Explore DYNAMIXEL Wizard 2.0 and DYNAMIXEL SDK (done)
* Explore U2D2 (USB to DYNAMIXEL, connecting a PC to a DYNAMIXEL motor) (done)
* Control the motor with Python scripts (done)
* Support different motors using motor profiles (done)
* Switch from XM430 to XC330-M288T-T (done)
* Use current-based control instead of position control for improved safety

### Phase 2 — Remote Control

* Create a web interface for PC and mobile (done)
* Control the motor from a browser using FastAPI (done)
* Access and control the motor remotely over LTE using Cloudflare Tunnel (done)
* Revamp the UI to make switch control simpler and more intuitive (done)

### Phase 3 — Standalone Control
Control the switch independently from a PC

* Use ESP32 + OpenRB-150 to control the XC330
* Connect the switch to the internet through ESP32
* Control the switch remotely from a mobile device
* Explore WebSocket for bidirectional communication
* Using a custom domain for the remote connection
