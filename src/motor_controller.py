"""Control an XM430 motor over U2D2 using the Dynamixel SDK."""

import time

from dynamixel_sdk import *  # noqa: F403

# Connection settings (from scan_motor.py)
DEVICENAME = "/dev/ttyUSB0"
BAUDRATE = 4000000
PROTOCOL_VERSION = 2.0
DXL_ID = 2

# Switch positions (0–4095). Tune these for your physical ON/OFF stops.
OFF_POSITION = 400
ON_POSITION = 3700

# XM430 control table (Protocol 2.0)
ADDR_TORQUE_ENABLE = 64
ADDR_GOAL_POSITION = 116
ADDR_PRESENT_POSITION = 132
TORQUE_ENABLE = 1
TORQUE_DISABLE = 0
MOVING_THRESHOLD = 20


class MotorController:
    def __init__(
        self,
        device: str = DEVICENAME,
        baudrate: int = BAUDRATE,
        motor_id: int = DXL_ID,
        off_position: int = OFF_POSITION,
        on_position: int = ON_POSITION,
    ) -> None:
        self.device = device
        self.baudrate = baudrate
        self.motor_id = motor_id
        self.off_position = off_position
        self.on_position = on_position
        self.port_handler = PortHandler(device)
        self.packet_handler = PacketHandler(PROTOCOL_VERSION)
        self._connected = False

    def connect(self) -> None:
        if not self.port_handler.openPort():
            raise RuntimeError(f"Failed to open port: {self.device}")

        if not self.port_handler.setBaudRate(self.baudrate):
            self.port_handler.closePort()
            raise RuntimeError(f"Failed to set baud rate: {self.baudrate}")

        model_number, result, error = self.packet_handler.ping(
            self.port_handler, self.motor_id
        )
        if result != COMM_SUCCESS:
            self.port_handler.closePort()
            raise RuntimeError(
                f"Ping failed: {self.packet_handler.getTxRxResult(result)}"
            )
        if error:
            self.port_handler.closePort()
            raise RuntimeError(
                f"Ping error: {self.packet_handler.getRxPacketError(error)}"
            )

        self._connected = True
        print(f"Connected: {self.device} @ {self.baudrate}, id={self.motor_id}, model={model_number}")

    def close(self) -> None:
        if not self._connected:
            return
        self.disable_torque()
        self.port_handler.closePort()
        self._connected = False

    def __enter__(self) -> "MotorController":
        self.connect()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()

    def enable_torque(self) -> None:
        self._check_comm(
            *self.packet_handler.write1ByteTxRx(
                self.port_handler, self.motor_id, ADDR_TORQUE_ENABLE, TORQUE_ENABLE
            ),
            "enable torque",
        )

    def disable_torque(self) -> None:
        if not self._connected:
            return
        self.packet_handler.write1ByteTxRx(
            self.port_handler, self.motor_id, ADDR_TORQUE_ENABLE, TORQUE_DISABLE
        )

    def get_position(self) -> int:
        position, result, error = self.packet_handler.read4ByteTxRx(
            self.port_handler, self.motor_id, ADDR_PRESENT_POSITION
        )
        self._check_comm(result, error, "read position")
        return position

    def move_to(self, goal: int, wait: bool = True) -> int:
        self.enable_torque()
        self._check_comm(
            *self.packet_handler.write4ByteTxRx(
                self.port_handler, self.motor_id, ADDR_GOAL_POSITION, goal
            ),
            "write goal position",
        )

        if not wait:
            return goal

        while True:
            position = self.get_position()
            if abs(goal - position) <= MOVING_THRESHOLD:
                return position
            time.sleep(0.05)

    def on(self) -> int:
        print(f"Switch ON -> position {self.on_position}")
        final = self.move_to(self.on_position)
        print(f"Reached position {final}")
        return final

    def off(self) -> int:
        print(f"Switch OFF -> position {self.off_position}")
        final = self.move_to(self.off_position)
        print(f"Reached position {final}")
        return final

    def is_on(self) -> bool:
        position = self.get_position()
        return abs(position - self.on_position) < abs(position - self.off_position)

    def toggle(self) -> str:
        if self.is_on():
            self.off()
            return "off"
        self.on()
        return "on"

    def _check_comm(self, result: int, error: int, action: str) -> None:
        if result != COMM_SUCCESS:
            raise RuntimeError(
                f"Failed to {action}: {self.packet_handler.getTxRxResult(result)}"
            )
        if error:
            raise RuntimeError(
                f"Failed to {action}: {self.packet_handler.getRxPacketError(error)}"
            )
