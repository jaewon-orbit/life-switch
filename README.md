# Life Switch

An embedded system for controlling an existing lamp switch from a phone.

[![Life Switch demo](https://img.youtube.com/vi/OXimIOwr_dM/0.jpg)](https://www.youtube.com/watch?v=OXimIOwr_dM)

## Why I Built It

I wanted to turn off my lamp from bed, or from outside the house if I had forgotten it. The goal was to keep the original switch and wiring, attach a motor to operate it, and make it accessible from a mobile browser.

The first version required a PC connected to the motor. Keeping a PC running just to switch a lamp felt unnecessary, so I moved the device-side connection to an ESP32 and OpenRB-150.

## System

```text
Phone browser (GitHub Pages)
           ↕ WSS
     VPS / FastAPI relay
           ↕ WSS
       ESP32 (Wi-Fi)
           ↕ UART
        OpenRB-150
           ↕
     DYNAMIXEL XC330
           ↓
   Original lamp switch
```

| Component | Role |
| --- | --- |
| DYNAMIXEL XC330-M288-T | Moves a printed horn against the switch |
| OpenRB-150 | Controls the motor and reads its position |
| ESP32 | Connects the device to Wi-Fi and forwards commands over UART |
| FastAPI relay on a VPS | Connects the browser and ESP32 over WebSocket |
| Browser interface | Sends commands and displays position-derived switch state |
| Autodesk Fusion | Used to design the printed horn |

## What I Built and Changed

- Connected the browser, Python backend, Wi-Fi module, motor controller, and physical switch.
- Replaced the initial PC connection with ESP32-based remote control.
- Switched from an XM430 to a smaller XC330 and separated motor settings into profiles.
- Designed and mounted a printed horn for the lamp's rocker switch.
- Used current-based position control to limit torque during movement.
- Updated the interface from motor position feedback instead of assuming the last displayed state was correct.

## Design Decisions

**Outbound connection through a relay.** The ESP32 connects to the VPS from behind the home router. The browser uses the same relay, so the setup does not need router port forwarding.

**Position updates when needed.** The XC330 browser interface requests `STATUS` when its WebSocket opens, including after a page refresh or browser reconnection. A toggle command returns motor position feedback, which also updates the display. These events replace continuous position polling over the network. Connection heartbeats are separate from motor-position requests.

**Position as a state estimate.** The interface maps the motor position to the configured ON and OFF endpoints, around 1350 and 1900. This addressed mismatches between the actual motor position and the displayed state.

The main lesson was to choose components and communication patterns that fit the task, and change them as the practical requirements became clearer.

## Demonstrated Operation and Scope

The demo shows remote operation of my IKEA TÅGARP lamp. The project progressed from PC-connected motor control to a standalone ESP32/OpenRB setup, with remote access tested over LTE.

The mechanism and position endpoints are fitted to this particular switch. The displayed state is inferred from motor position; it does not independently measure whether the lamp is illuminated. The repository records the implementation and demos, without a measured reliability or latency benchmark.

## Setup

- Follow the [OpenRB motor setup](firmware/openrb_xc330/README.md) and [ESP32 wiring and relay setup](firmware/esp32_openrb_uart_test/README.md).
- Copy `firmware/esp32_openrb_uart_test/secrets.h.example` to `secrets.h` in the same directory and enter the Wi-Fi settings locally.
- Keep local credentials out of version control.

## Usage

Open the GitHub Pages site and tap the toggle. That's it — it works the same over LTE or outside the house, thanks to the VPS relay.

<details>
<summary>Legacy: local dev testing via Cloudflare Quick Tunnel</summary>

Used early on to test the browser UI from a phone before the VPS relay existed. Not needed for normal use anymore.

```bash
python -m uvicorn src.server:app --host 127.0.0.1 --port 8000
bash scripts/start_quick_tunnel.sh
```

`cloudflared` prints a random `https://…trycloudflare.com` URL, valid only while the tunnel is running.

</details>

<br>

<details>
<summary>Hardware assembly</summary>

1. Right now, Life Switch remotely controls the physical switch of my IKEA TÅGARP floor lamp.

<div align="center">
<img src="./docs/images/lamp.jpg" width="80" alt="TÅGARP floor lamp">
</div>
<br>
2. And this is the lamp's inline rocker switch.

<div align="center">
<img src="./docs/images/rocker_switch_1.jpg" width="120" alt="Lamp's inline rocker switch">
<img src="./docs/images/rocker_switch_2.jpg" width="75" alt="Lamp's inline rocker switch">
</div>
<br>
3. Removed the stock plain horn from the XC330's output disc, and mounted ROBOTIS official XC330 horn (HNX330-N102), onto the output shaft with its center screw.<br>
<a href="https://github.com/jaewon-orbit/life-switch/raw/refs/heads/main/docs/models/XL_XC_330_HORN.stp.zip">📦 Download XC330 Horn (HNX330-N102) STP file</a>
<div align="center">
<img src="./docs/images/hnx330_n102.jpg" width="160" alt="HNX330-N102 horn mounted on the XC330 output shaft">
</div>
<br> 
4. Designed a teardrop-shaped horn in Autodesk Fusion, and mounted it onto the HNX330-N102 with M2×6mm screws.<br>
<a href="https://github.com/jaewon-orbit/life-switch/raw/refs/heads/main/docs/models/teardrop_horn.stp.zip">📦 Download Teardrop-Shaped Horn STP file</a>
<div align="center">
<img src="./docs/images/tear_drop_3d_model_1.png" width="295" alt="Teardrop-shaped design in Autodesk Fusion">
<img src="./docs/images/tear_drop_3d_model_2.png" width="200" alt="Teardrop-shaped design in Autodesk Fusion">
<a href="https://www.youtube.com/watch?v=8kB1C54fzu8"><img src="https://img.youtube.com/vi/8kB1C54fzu8/0.jpg" width="140" alt="Horn print, assembly, and test video"></a>
</div>
<br> 
5. Attached the motor + horn next to the lamp's inline rocker switch with cable ties, using the horn to physically toggle it.
<div align="center">
<img src="./docs/images/motor_horn_attached.jpg" width="160" alt="Motor and horn attached next to the rocker switch">
</div>
<br> 
6. Put the ESP32 and OpenRB-150 in a small basket, and cable-tied the basket to the lamp's pole.
<div align="center">
<img src="./docs/images/esp32_openrb_basket.jpg" width="140" alt="ESP32 and OpenRB-150 inside the small basket">
<img src="./docs/images/lamp_full_setup.jpg" width="200" alt="Floor lamp with the basket tied to the pole">
</div>

<br>

</details>

<details>
<summary>Build history and photos</summary>

- **Remote control over LTE** — controlled the motor from a mobile browser over LTE via Cloudflare Tunnel.

  <img src="./docs/images/motor_move_LTE.png" width="140" alt="Motor controlled remotely over LTE">

- **Motor: XM430 → XC330** — switched to a smaller motor; refactored control code to use motor profiles instead of hardcoded values.
- **UI revamp** — simplified the UI to show only what the user actually needs.

  | Before | After |
  |:---:|:---:|
  | <img src="./docs/images/ui-before.jpg" width="140"> | <img src="./docs/images/ui-revamp.jpg" width="140"> |

- **Standalone control** — connected ESP32 + OpenRB-150 to control the motor without a PC.

  <img src="./docs/images/esp32_openrb_motor.jpg" width="300" alt="ESP32 and OpenRB motor control setup">

- **VPS WebSocket relay** — deployed a VPS to relay WebSocket traffic between GitHub Pages and ESP32, avoiding port forwarding.
- **Current-based position control** — switched from position control to current-based position control to protect the motor and the 3D-printed horn.
- **Status sync on refresh** — the browser now requests the real motor position (`STATUS`) whenever the WebSocket connects or a toggle is pressed, instead of relying on a stored default.
- **UI, round 2** — after adding current-based position control and status sync, simplified the browser UI for clearer switch control.
  | Before | After |
  |:---:|:---:|
  | <img src="./docs/images/ui-v2-before.jpg" width="400"> | <img src="./docs/images/ui-v2-after.jpg" width="400"> |

<br>

</details>
