
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

This could potentially make many existing physical devices remotely controllable without requiring them to be replaced.

## The Idea

```text
Phone / Browser
       ↓
   Web Interface
       ↓
     Web API
       ↓
     Python
       ↓
      U2D2
       ↓
 DYNAMIXEL Motor
       ↓
 Physical Switch
       ↓
 Existing Device
