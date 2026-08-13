"""FastAPI web server for remote motor control."""

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

from src.motor_controller import MotorController
from src.motor_profiles import get_motor_profile

WEB_DIR = Path(__file__).resolve().parent.parent / "web"

motors: dict[str, MotorController | None] = {
    "A": None,
    "B": None,
}


def _require_motor(profile_name: str) -> MotorController:
    motor = motors.get(profile_name)
    if motor is None or not motor._connected:
        profile = get_motor_profile(profile_name)
        raise HTTPException(
            status_code=503,
            detail=(
                f"{profile.model} not connected. "
                f"Check U2D2, {profile.power_supply} power, and close Dynamixel Wizard."
            ),
        )
    return motor


def _status_response(m: MotorController, profile_name: str) -> dict:
    profile = get_motor_profile(profile_name)
    position = m.get_position()
    state = "on" if m.is_on() else "off"
    return {
        "state": state,
        "position": position,
        "on_target": m.on_position,
        "off_target": m.off_position,
        "motor": profile.name,
        "model": profile.model,
    }


def _connect_motor(profile_name: str) -> MotorController | None:
    profile = get_motor_profile(profile_name)
    print(
        f"Connecting motor {profile.name}: {profile.model} "
        f"(id={profile.motor_id}, baud={profile.baudrate})"
    )
    motor = MotorController(**profile.as_controller_kwargs())
    try:
        motor.connect()
    except RuntimeError as exc:
        print(f"Motor {profile.name} not connected at startup: {exc}")
        return None
    return motor


@asynccontextmanager
async def lifespan(app: FastAPI):
    global motors
    for profile_name in motors:
        motors[profile_name] = _connect_motor(profile_name)
    yield
    for profile_name, motor in motors.items():
        if motor is not None:
            motor.close()
            motors[profile_name] = None


app = FastAPI(title="Life Switch", version="0.1.0", lifespan=lifespan)


def _register_motor_routes(prefix: str, profile_name: str) -> None:
    @app.post(f"{prefix}/on")
    def api_on() -> dict:
        m = _require_motor(profile_name)
        position = m.on()
        return {"state": "on", "position": position}

    @app.post(f"{prefix}/off")
    def api_off() -> dict:
        m = _require_motor(profile_name)
        position = m.off()
        return {"state": "off", "position": position}

    @app.post(f"{prefix}/toggle")
    def api_toggle() -> dict:
        m = _require_motor(profile_name)
        state = m.toggle()
        return {"state": state, "position": m.get_position()}

    @app.get(f"{prefix}/status")
    def api_status() -> dict:
        m = _require_motor(profile_name)
        return _status_response(m, profile_name)


_register_motor_routes("/api", "A")
_register_motor_routes("/api/xc330", "B")


def _motor_connected(profile_name: str) -> bool:
    motor = motors.get(profile_name)
    return motor is not None and motor._connected


@app.get("/", response_model=None)
def root_page() -> RedirectResponse | FileResponse:
    """Send Cloudflare/root visitors to the UI for the connected motor."""
    if _motor_connected("B"):
        return RedirectResponse(url="/xc330", status_code=302)
    if _motor_connected("A"):
        return RedirectResponse(url="/xm430", status_code=302)
    return FileResponse(WEB_DIR / "landing.html")


@app.get("/xm430")
def xm430_page() -> FileResponse:
    return FileResponse(WEB_DIR / "index.html")


@app.get("/xc330")
def xc330_page() -> FileResponse:
    return FileResponse(WEB_DIR / "xc330_index.html")


app.mount("/", StaticFiles(directory=WEB_DIR, html=False), name="web")
