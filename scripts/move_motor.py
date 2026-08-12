#!/usr/bin/env python3
"""
Move an XM430 motor once via U2D2 (Protocol 2.0).

Before running:
  1. 12V power ON (Power Hub + XM430)
  2. U2D2 plugged into USB (usually /dev/ttyUSB0)
  3. Close Dynamixel Wizard if it is open (only one app can use the port)

Run:
  python scripts/move_motor.py
"""

import sys
import time

from dynamixel_sdk import *  # noqa: F403

# ----- Change these if needed -----
DEVICENAME = "/dev/ttyUSB0"
BAUDRATE = 4000000        # found by scan_motor.py
PROTOCOL_VERSION = 2.0
DXL_ID = 2
# ----------------------------------

# XM430 control table (Protocol 2.0)
ADDR_TORQUE_ENABLE = 64
ADDR_GOAL_POSITION = 116
ADDR_PRESENT_POSITION = 132
TORQUE_ENABLE = 1
TORQUE_DISABLE = 0
DXL_MINIMUM_POSITION_VALUE = 0
DXL_MAXIMUM_POSITION_VALUE = 4095
DXL_MOVING_STATUS_THRESHOLD = 20


def main() -> int:
    port_handler = PortHandler(DEVICENAME)
    packet_handler = PacketHandler(PROTOCOL_VERSION)

    if not port_handler.openPort():
        print(f"Failed to open port: {DEVICENAME}")
        return 1

    if not port_handler.setBaudRate(BAUDRATE):
        print(f"Failed to set baud rate: {BAUDRATE}")
        port_handler.closePort()
        return 1

    print(f"Port open: {DEVICENAME} @ {BAUDRATE} baud, motor ID {DXL_ID}")

    # Ping first — quick check that the motor responds
    model_number, result, error = packet_handler.ping(port_handler, DXL_ID)
    if result != COMM_SUCCESS:
        print(f"Ping failed: {packet_handler.getTxRxResult(result)}")
        print("Tips: check power, wiring, motor ID, and try BAUDRATE = 1000000")
        port_handler.closePort()
        return 1
    if error:
        print(f"Ping error: {packet_handler.getRxPacketError(error)}")
        port_handler.closePort()
        return 1

    print(f"Motor found. Model number: {model_number}")

    # Enable torque
    result, error = packet_handler.write1ByteTxRx(
        port_handler, DXL_ID, ADDR_TORQUE_ENABLE, TORQUE_ENABLE
    )
    if result != COMM_SUCCESS or error:
        print("Failed to enable torque")
        port_handler.closePort()
        return 1

    # Read current position
    present_position, result, error = packet_handler.read4ByteTxRx(
        port_handler, DXL_ID, ADDR_PRESENT_POSITION
    )
    if result != COMM_SUCCESS or error:
        print("Failed to read present position")
        disable_torque(packet_handler, port_handler)
        port_handler.closePort()
        return 1

    print(f"Current position: {present_position}")

    # Move to opposite end of range (small safe demo motion)
    if present_position > (DXL_MINIMUM_POSITION_VALUE + DXL_MAXIMUM_POSITION_VALUE) / 2:
        goal = DXL_MINIMUM_POSITION_VALUE + 400
    else:
        goal = DXL_MAXIMUM_POSITION_VALUE - 400

    print(f"Moving to goal position: {goal}")
    result, error = packet_handler.write4ByteTxRx(
        port_handler, DXL_ID, ADDR_GOAL_POSITION, goal
    )
    if result != COMM_SUCCESS or error:
        print("Failed to write goal position")
        disable_torque(packet_handler, port_handler)
        port_handler.closePort()
        return 1

    # Wait until the motor stops moving
    while True:
        present_position, result, error = packet_handler.read4ByteTxRx(
            port_handler, DXL_ID, ADDR_PRESENT_POSITION
        )
        if result != COMM_SUCCESS or error:
            break
        if abs(goal - present_position) <= DXL_MOVING_STATUS_THRESHOLD:
            break
        time.sleep(0.05)

    print(f"Done. Final position: {present_position}")

    disable_torque(packet_handler, port_handler)
    port_handler.closePort()
    return 0


def disable_torque(packet_handler, port_handler) -> None:
    packet_handler.write1ByteTxRx(
        port_handler, DXL_ID, ADDR_TORQUE_ENABLE, TORQUE_DISABLE
    )


if __name__ == "__main__":
    sys.exit(main())
