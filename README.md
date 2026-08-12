# Life Switch

Goal: Control physical switches in the real world, remotely.<br>
<br>
<br>

During a summer heat wave, I wanted to turn on the air conditioner before getting home.

Another time, I left home and suddenly wondered, "Did I turn off the air conditioner?"
<br>
<br>
<br>
These made me think about how many devices still require physical interaction.<br><br>
Life Switch is an experimental project that uses a small motor to physically control existing switches remotely.

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

Control existing physical switches from a phone or browser without modifying the device itself.

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
