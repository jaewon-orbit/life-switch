#!/usr/bin/env python3
"""Request the OpenRB-150 firmware to run the XC330 return-trip motion.

The OpenRB sketch owns the DYNAMIXEL bus. This script sends it a USB serial
``MOVE`` command; it does not talk to the XC330 directly like move_motor.py
does through a U2D2.

Run:
    python scripts/move_openrb_xc330.py --port /dev/ttyACM0
"""

import argparse
import sys
import time

import serial


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the configured XC330 return-trip through OpenRB-150."
    )
    parser.add_argument("--port", required=True, help="OpenRB USB serial port")
    parser.add_argument("--baudrate", type=int, default=115200)
    parser.add_argument(
        "--timeout",
        type=float,
        default=20.0,
        help="Seconds to wait for the motion result (default: 20)",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    try:
        with serial.Serial(args.port, args.baudrate, timeout=0.25) as port:
            # USB serial connection can reset an Arduino-compatible board.
            # The firmware is idle after reset, so wait for it to be ready.
            time.sleep(1.5)
            port.reset_input_buffer()
            port.write(b"MOVE\n")
            port.flush()

            deadline = time.monotonic() + args.timeout
            while time.monotonic() < deadline:
                line = port.readline().decode("utf-8", errors="replace").strip()
                if not line:
                    continue
                print(line)
                if line == "DONE":
                    return 0
                if line.startswith("ERROR:"):
                    return 1
    except serial.SerialException as exc:
        print(f"Could not open OpenRB serial port {args.port}: {exc}", file=sys.stderr)
        return 1

    print("Timed out waiting for OpenRB motion result.", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
