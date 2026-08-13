# Life Switch

# Goal

Control physical switches in the real world, remotely.

Control physical switches from a phone or web browser. The first prototype uses a DYNAMIXEL motor to physically operate the switch.
<br>
<br>
# Why?
During a summer heat wave, I wanted to turn on the air conditioner before getting home.
Another time, I left home and suddenly wondered, "Did I turn off the air conditioner?"
<br>
<br>
These made me think about how many devices still require physical interaction.
<br>
<br>
Life Switch is an experimental project that uses a small motor to physically control existing switches remotely.

## NOW NOW NOW 
## Latest Updates

## 1. Remote Control over LTE

Successfully controlled the motor remotely from a mobile browser over LTE using Cloudflare Tunnel.

## 2. Motor Change: XM430 → XC330

Changed the motor from XM430 to XC330-M288T-T, which is smaller and more suitable for the physical switch prototype.

The motor control code was also refactored to use motor profiles instead of motor-specific rotation values. This allows different motors to be tested without changing the core control logic.

## 3. UI Revamp

Redesigned the browser UI to make the remote switch control simpler and more intuitive.

| Before | After |
|:---:|:---:|
| <img src="./docs/images/ui-before.jpg" width="400"> | <img src="./docs/images/ui-revamp.jpg" width="400"> |

## 4. Next? Standalone Control

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



## Prototype

* ROBOTIS DYNAMIXEL XC430
* U2D2
* U2D2 Power Hub
* 12V Power Supply
* Python
* Dynamixel SDK
* Linux

The first prototype is being developed on a Linux laptop.

## Goal

Control existing physical switches from a phone/browser without modifying the device itself.

The first prototype focuses on using a DYNAMIXEL motor to physically operate a switch.

## Roadmap

### Phase 1 — Motor Control

* Set up Python environment
* Install Dynamixel SDK
* Connect U2D2
* Communicate with XC430
* Read motor state
* Control motor position
* Build a physical switch mechanism

### Phase 2 — Remote Control

* Build a Python control server
* Create a web interface
* Control the motor from a browser
* Add basic safety controls

### Phase 3 — Mobile

* Mobile-friendly interface
* Remote access
* Device status
* Explore PWA / mobile app

## Vision

Explore how existing physical interfaces can be controlled remotely.
