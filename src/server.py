"""FastAPI web server for remote motor control."""

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles

from src.motor_controller import OFF_POSITION, ON_POSITION, MotorController

WEB_DIR = Path(__file__).resolve().parent.parent / "web"

motor: MotorController | None = None


def _require_motor() -> MotorController:
    if motor is None or not motor._connected:
        raise HTTPException(
            status_code=503,
            detail="Motor not connected. Check U2D2, 12V power, and close Dynamixel Wizard.",
        )
    return motor


def _status_response(m: MotorController) -> dict:
    position = m.get_position()
    state = "on" if m.is_on() else "off"
    return {
        "state": state,
        "position": position,
        "on_target": ON_POSITION,
        "off_target": OFF_POSITION,
    }


@asynccontextmanager
async def lifespan(app: FastAPI):
    global motor
    motor = MotorController()
    try:
        motor.connect()
    except RuntimeError as exc:
        print(f"Motor not connected at startup: {exc}")
        motor = None
    yield
    if motor is not None:
        motor.close()
        motor = None


app = FastAPI(title="Life Switch", version="0.1.0", lifespan=lifespan)


@app.post("/api/on")
def api_on() -> dict:
    m = _require_motor()
    position = m.on()
    return {"state": "on", "position": position}


@app.post("/api/off")
def api_off() -> dict:
    m = _require_motor()
    position = m.off()
    return {"state": "off", "position": position}


@app.post("/api/toggle")
def api_toggle() -> dict:
    m = _require_motor()
    state = m.toggle()
    return {"state": state, "position": m.get_position()}


@app.get("/api/status")
def api_status() -> dict:
    m = _require_motor()
    return _status_response(m)


app.mount("/", StaticFiles(directory=WEB_DIR, html=True), name="web")
