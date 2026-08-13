#!/usr/bin/env python3
"""
Smart switch: move a configured motor to ON or OFF positions.

Usage:
  python scripts/switch_motor.py on
  python scripts/switch_motor.py off --motor B
  python scripts/switch_motor.py toggle
  python scripts/switch_motor.py status --motor A
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.motor_controller import MotorController
from src.motor_profiles import get_motor_profile


def print_status(motor: MotorController) -> None:
    position = motor.get_position()
    state = "ON" if motor.is_on() else "OFF"
    print(f"State: {state}")
    print(f"Position: {position}")
    print(f"ON target: {motor.on_position}  |  OFF target: {motor.off_position}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Control the life switch motor.")
    parser.add_argument(
        "command",
        choices=["on", "off", "toggle", "status"],
        help="Action to perform",
    )
    parser.add_argument(
        "--motor",
        help="Motor profile to use (A or B). Defaults to MOTOR env var, then A.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    try:
        profile = get_motor_profile(args.motor)
    except ValueError as exc:
        print(f"Error: {exc}")
        return 1

    print(
        f"Using motor {profile.name}: {profile.model} "
        f"(id={profile.motor_id}, baud={profile.baudrate})"
    )

    try:
        with MotorController(**profile.as_controller_kwargs()) as motor:
            if args.command == "on":
                motor.on()
            elif args.command == "off":
                motor.off()
            elif args.command == "toggle":
                new_state = motor.toggle()
                print(f"Toggled to {new_state.upper()}")
            elif args.command == "status":
                print_status(motor)
    except RuntimeError as exc:
        print(f"Error: {exc}")
        print(
            f"Tips: check {profile.power_supply} power, wiring, "
            "and close Dynamixel Wizard."
        )
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
