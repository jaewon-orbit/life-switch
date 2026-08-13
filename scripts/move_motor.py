#!/usr/bin/env python3
"""
Move a configured Dynamixel motor once via U2D2 (Protocol 2.0).

Before running:
  1. Power ON (12V for XM430, 5V for XC330)
  2. U2D2 plugged into USB (usually /dev/ttyUSB0)
  3. Close Dynamixel Wizard if it is open (only one app can use the port)

Run:
  python scripts/move_motor.py
  python scripts/move_motor.py --motor B
"""

import argparse
import sys
import time
from pathlib import Path

from dynamixel_sdk import *  # noqa: F403

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.motor_profiles import get_motor_profile

PROTOCOL_VERSION = 2.0

TORQUE_ENABLE = 1
TORQUE_DISABLE = 0
DXL_MINIMUM_POSITION_VALUE = 0
DXL_MAXIMUM_POSITION_VALUE = 4095


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Demo move for a configured motor.")
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

    device = profile.device
    baudrate = profile.baudrate
    dxl_id = profile.motor_id
    addr_torque_enable = profile.addr_torque_enable
    addr_goal_position = profile.addr_goal_position
    addr_present_position = profile.addr_present_position
    moving_threshold = profile.moving_threshold

    print(
        f"Using motor {profile.name}: {profile.model} "
        f"(id={dxl_id}, baud={baudrate})"
    )

    port_handler = PortHandler(device)
    packet_handler = PacketHandler(PROTOCOL_VERSION)

    if not port_handler.openPort():
        print(f"Failed to open port: {device}")
        return 1

    if not port_handler.setBaudRate(baudrate):
        print(f"Failed to set baud rate: {baudrate}")
        port_handler.closePort()
        return 1

    print(f"Port open: {device} @ {baudrate} baud, motor ID {dxl_id}")

    model_number, result, error = packet_handler.ping(port_handler, dxl_id)
    if result != COMM_SUCCESS:
        print(f"Ping failed: {packet_handler.getTxRxResult(result)}")
        print("Tips: check power, wiring, motor ID, and run scan_motor.py")
        port_handler.closePort()
        return 1
    if error:
        print(f"Ping error: {packet_handler.getRxPacketError(error)}")
        port_handler.closePort()
        return 1

    print(f"Motor found. Model number: {model_number}")

    result, error = packet_handler.write1ByteTxRx(
        port_handler, dxl_id, addr_torque_enable, TORQUE_ENABLE
    )
    if result != COMM_SUCCESS or error:
        print("Failed to enable torque")
        port_handler.closePort()
        return 1

    present_position, result, error = packet_handler.read4ByteTxRx(
        port_handler, dxl_id, addr_present_position
    )
    if result != COMM_SUCCESS or error:
        print("Failed to read present position")
        disable_torque(packet_handler, port_handler, dxl_id, addr_torque_enable)
        port_handler.closePort()
        return 1

    print(f"Current position: {present_position}")

    if present_position > (DXL_MINIMUM_POSITION_VALUE + DXL_MAXIMUM_POSITION_VALUE) / 2:
        goal = DXL_MINIMUM_POSITION_VALUE + 400
    else:
        goal = DXL_MAXIMUM_POSITION_VALUE - 400

    print(f"Moving to goal position: {goal}")
    result, error = packet_handler.write4ByteTxRx(
        port_handler, dxl_id, addr_goal_position, goal
    )
    if result != COMM_SUCCESS or error:
        print("Failed to write goal position")
        disable_torque(packet_handler, port_handler, dxl_id, addr_torque_enable)
        port_handler.closePort()
        return 1

    while True:
        present_position, result, error = packet_handler.read4ByteTxRx(
            port_handler, dxl_id, addr_present_position
        )
        if result != COMM_SUCCESS or error:
            break
        if abs(goal - present_position) <= moving_threshold:
            break
        time.sleep(0.05)

    print(f"Done. Final position: {present_position}")

    disable_torque(packet_handler, port_handler, dxl_id, addr_torque_enable)
    port_handler.closePort()
    return 0


def disable_torque(
    packet_handler, port_handler, dxl_id: int, addr_torque_enable: int
) -> None:
    packet_handler.write1ByteTxRx(
        port_handler, dxl_id, addr_torque_enable, TORQUE_DISABLE
    )


if __name__ == "__main__":
    sys.exit(main())
