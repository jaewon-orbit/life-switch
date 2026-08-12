# Life Switch

> **Control physical switches in the real world, remotely.**

Life Switch is an experimental robotics project exploring how existing physical switches in our everyday lives can be controlled remotely using a small motorized device.

## Why I Started This

One summer, I turned on the air conditioner before leaving home.

After I went outside, I suddenly wondered:

> **"Did I actually turn it off?"**

That simple moment made me think about how many physical switches still exist around us.

Air conditioners, lights, heaters, appliances, and many other devices are designed to be operated by a person standing right in front of them.

So I started with a simple question:

> **What if I could control those physical switches from my phone, even when I'm away from home?**

Instead of replacing the existing appliance or modifying its internal electronics, Life Switch takes a different approach:

**Use a motor to physically interact with the existing switch.**

The motor acts as a robotic interface between the digital world and the physical world.

## Current Prototype

The first prototype uses:

- **ROBOTIS DYNAMIXEL XC430**
- **U2D2**
- **U2D2 Power Hub**
- **12V Power Supply**
- **Python**
- **Dynamixel SDK**
- **Linux**

The initial development is being done on a Linux laptop, with the goal of eventually controlling the motor through a web interface from a phone or browser.

## Goal

The goal is to build a small robotic device that allows users to remotely control existing physical switches from a phone or browser.

### Initial Prototype

> Use a ROBOTIS DYNAMIXEL motor to physically operate an existing switch.

### Long-Term Direction

The project is not limited to air conditioners.

The broader idea is to explore whether **physical interfaces in the real world can be made remotely controllable without replacing the devices themselves.**

Potential applications could include:

- Air conditioners
- Lights
- Heaters
- Household appliances
- Industrial switches
- Other manually operated physical controls

## Development Roadmap

### Phase 1 — Motor Control

- [ ] Set up Python environment
- [ ] Install Dynamixel SDK
- [ ] Connect U2D2
- [ ] Communicate with XC430
- [ ] Read motor state
- [ ] Control motor position
- [ ] Develop a physical switch mechanism

### Phase 2 — Remote Control

- [ ] Build a Python control server
- [ ] Create a simple web interface
- [ ] Control the motor from a browser
- [ ] Add basic safety controls

### Phase 3 — Mobile Access

- [ ] Mobile-friendly web interface
- [ ] Remote access
- [ ] Device status monitoring
- [ ] Explore PWA / dedicated mobile app

## Vision

Life Switch started with a simple problem:

> **"Did I turn off the air conditioner?"**

But the bigger question is:

> **Can we give existing physical interfaces a digital interface without replacing the devices themselves?**

This project is an exploration of that idea — connecting the digital world to the physical world, one switch at a time.
