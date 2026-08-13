"""Motor connection profiles. Add or edit entries here when hardware changes."""

from dataclasses import dataclass
import os

DEFAULT_MOTOR = "A"


@dataclass(frozen=True)
class MotorProfile:
    name: str
    model: str
    device: str
    baudrate: int
    motor_id: int
    off_position: int
    on_position: int
    power_supply: str = "12V"

    def as_controller_kwargs(self) -> dict:
        return {
            "device": self.device,
            "baudrate": self.baudrate,
            "motor_id": self.motor_id,
            "off_position": self.off_position,
            "on_position": self.on_position,
        }


# Motor A: XM430-W210 (scan: id=2, baud=4000000, model=1030)
# Motor B: XC330-M288-T (scan: id=1, baud=57600, model=1240)
MOTORS: dict[str, MotorProfile] = {
    "A": MotorProfile(
        name="A",
        model="XM430-W210",
        device="/dev/ttyUSB0",
        baudrate=4000000,
        motor_id=2,
        off_position=400,
        on_position=3700,
    ),
    "B": MotorProfile(
        name="B",
        model="XC330-M288-T",
        device="/dev/ttyUSB0",
        baudrate=57600,
        motor_id=1,
        # XC330: 4095 units ≈ 360°, so 180° = 2048 units of travel.
        off_position=400,
        on_position=2448,
        power_supply="5V",
    ),
}


def get_motor_profile(name: str | None = None) -> MotorProfile:
    motor_name = (name or os.environ.get("MOTOR") or DEFAULT_MOTOR).upper()
    try:
        return MOTORS[motor_name]
    except KeyError as exc:
        valid = ", ".join(sorted(MOTORS))
        raise ValueError(f"Unknown motor {motor_name!r}. Choose one of: {valid}") from exc
