#!/usr/bin/env python3
"""
Scan common baud rates and motor IDs to find your XM430.

Run:
  python scripts/scan_motor.py
"""

from dynamixel_sdk import *  # noqa: F403

DEVICENAME = "/dev/ttyUSB0"
PROTOCOL_VERSION = 2.0
BAUDRATES = [57600, 1000000, 115200, 2000000, 3000000, 4000000]
IDS = list(range(0, 16))


def main() -> None:
    port_handler = PortHandler(DEVICENAME)
    packet_handler = PacketHandler(PROTOCOL_VERSION)

    try:
        opened = port_handler.openPort()
    except Exception as exc:
        print(f"Cannot open {DEVICENAME}: {exc}")
        print("Close Dynamixel Wizard (or any other app using the U2D2), then try again.")
        return

    if not opened:
        print(f"Cannot open {DEVICENAME}")
        return

    print(f"Scanning {DEVICENAME} ...")
    found = False

    for baud in BAUDRATES:
        if not port_handler.setBaudRate(baud):
            continue

        for dxl_id in IDS:
            model_number, result, error = packet_handler.ping(port_handler, dxl_id)
            if result == COMM_SUCCESS and not error:
                print(f"FOUND  id={dxl_id}  baud={baud}  model={model_number}")
                found = True

    port_handler.closePort()

    if not found:
        print("No motor found.")
        print("Check: 12V power, cables, U2D2 USB, and close Dynamixel Wizard.")


if __name__ == "__main__":
    main()
