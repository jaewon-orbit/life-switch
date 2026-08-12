#!/usr/bin/env python3
"""
Smart switch: move XM430 to ON or OFF positions.

Usage:
  python scripts/switch_motor.py on
  python scripts/switch_motor.py off
  python scripts/switch_motor.py toggle
  python scripts/switch_motor.py status
"""

import sys
from pathlib import Path

# Allow imports from src/
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.motor_controller import MotorController, OFF_POSITION, ON_POSITION


def print_status(motor: MotorController) -> None:
    position = motor.get_position()
    state = "ON" if motor.is_on() else "OFF"
    print(f"State: {state}")
    print(f"Position: {position}")
    print(f"ON target: {ON_POSITION}  |  OFF target: {OFF_POSITION}")


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: python scripts/switch_motor.py [on|off|toggle|status]")
        return 1

    command = sys.argv[1].lower()
    valid = {"on", "off", "toggle", "status"}
    if command not in valid:
        print(f"Unknown command: {command}")
        print("Usage: python scripts/switch_motor.py [on|off|toggle|status]")
        return 1

    try:
        with MotorController() as motor:
            if command == "on":
                motor.on()
            elif command == "off":
                motor.off()
            elif command == "toggle":
                new_state = motor.toggle()
                print(f"Toggled to {new_state.upper()}")
            elif command == "status":
                print_status(motor)
    except RuntimeError as exc:
        print(f"Error: {exc}")
        print("Tips: check 12V power, wiring, and close Dynamixel Wizard.")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
