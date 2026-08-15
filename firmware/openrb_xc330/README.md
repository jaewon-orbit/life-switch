# OpenRB-150 XC330 first-motion test

This sketch validates the first standalone-control link for Life Switch:

`PC (USB-C) -> OpenRB-150 -> XC330-M288-T`

It is configured to match [`src/motor_profiles.py`](../../src/motor_profiles.py):
Protocol 2.0, motor ID `1`, and baudrate `57600`.

## Safety and wiring

1. Disconnect the motor horn from the physical switch for this first test.
2. With power off, connect the XC330's 3-pin TTL cable to any OpenRB DYNAMIXEL
   port. The XC330 is a 5 V TTL model; do not use a 12 V supply.
3. Connect OpenRB-150 to the PC with USB-C. USB may be sufficient for this
   small, unloaded test. For later loaded operation, use a regulated external
   5 V supply through the OpenRB terminal input, with its power-source jumper
   set according to the board manual.

## Arduino IDE setup

1. In **File > Preferences > Additional Boards Manager URLs**, add:

   `https://raw.githubusercontent.com/ROBOTIS-GIT/OpenRB-150/master/package_openrb_index.json`

2. In **Tools > Board > Boards Manager**, install both **Arduino SAMD** and
   **OpenRB**.
3. In **Tools > Manage Libraries**, install **DYNAMIXEL2Arduino**.
4. Select **Tools > Board > OpenRB-150**, select its USB port, open
   `openrb_xc330.ino`, and upload it. If upload fails, double-press the
   OpenRB reset button to enter its bootloader, then upload again.
5. Uploading only starts the command server; it does **not** move the motor.
   Close Serial Monitor if it is open, then run from the project root:

   ```bash
   python scripts/move_openrb_xc330.py --port /dev/ttyACM0
   ```

   The script sends `MOVE`. The board makes a faster half-turn (2048 counts,
   about 180 degrees), waits two seconds, returns, then disables torque and
   DYNAMIXEL power. `DONE` confirms the movement completed.

If it prints a ping error, confirm the OpenRB red **DXL** LED lights during the
test, then check cable seating, 5 V power, motor ID `1`, and baudrate `57600`.

## References

- [ROBOTIS OpenRB-150 manual](https://emanual.robotis.com/docs/en/parts/controller/openrb-150/)
- [DYNAMIXEL2Arduino OpenRB serial configuration](https://github.com/ROBOTIS-GIT/Dynamixel2Arduino)
