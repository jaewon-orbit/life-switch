"""FastAPI web server for remote motor control and ESP32 connectivity tests."""

import asyncio
import os
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

from src.motor_controller import MotorController
from src.motor_profiles import get_motor_profile

WEB_DIR = Path(__file__).resolve().parent.parent / "web"

motors: dict[str, MotorController | None] = {
    "A": None,
    "B": None,
}

# Test 3-2: one ESP32 connects outward to this endpoint through Cloudflare.
# This is deliberately separate from motor-control commands; it only confirms
# a PING/PONG WebSocket round trip.
esp32_socket: WebSocket | None = None
esp32_last_pong_at: str | None = None
esp32_last_message: str | None = None
esp32_command_lock = asyncio.Lock()
esp32_command_reply: asyncio.Future[str] | None = None
client_sockets: set[WebSocket] = set()

# GitHub Pages is the production browser origin. Local origins make it possible
# to develop the static files without weakening production origin checks.
ALLOWED_BROWSER_ORIGINS = {
    origin.strip()
    for origin in os.environ.get(
        "LIFE_SWITCH_ALLOWED_ORIGINS",
        "https://jaewon-orbit.github.io,http://localhost:8000,http://127.0.0.1:8000",
    ).split(",")
    if origin.strip()
}


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


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
    except Exception as exc:
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
app.add_middleware(
    CORSMiddleware,
    allow_origins=sorted(ALLOWED_BROWSER_ORIGINS),
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


async def _broadcast_to_clients(message: dict) -> None:
    """Send a state/event message to every connected browser."""
    disconnected: list[WebSocket] = []
    for client in tuple(client_sockets):
        try:
            await client.send_json(message)
        except (RuntimeError, WebSocketDisconnect):
            disconnected.append(client)
    for client in disconnected:
        client_sockets.discard(client)


async def _send_client_event(websocket: WebSocket, event: str, **data: object) -> None:
    await websocket.send_json({"type": event, **data})


def _browser_origin_allowed(websocket: WebSocket) -> bool:
    """Only browsers from configured origins may control the relay."""
    return websocket.headers.get("origin") in ALLOWED_BROWSER_ORIGINS


@app.get("/api/esp32/status")
def esp32_status() -> dict:
    """Report the Test 3-2 WebSocket connection state."""
    return {
        "connected": esp32_socket is not None,
        "last_pong_at": esp32_last_pong_at,
        "last_message": esp32_last_message,
    }


@app.websocket("/ws/esp32")
async def esp32_websocket(websocket: WebSocket) -> None:
    """Continuously verify the ESP32's Cloudflare WebSocket connection."""
    global esp32_command_reply, esp32_last_message, esp32_last_pong_at, esp32_socket

    await websocket.accept()
    esp32_socket = websocket
    print("ESP32 WebSocket connected")
    await _broadcast_to_clients({"type": "esp32", "connected": True})

    async def send_pings() -> None:
        while True:
            await websocket.send_text("PING")
            await asyncio.sleep(10)

    ping_task = asyncio.create_task(send_pings())

    try:
        while True:
            message = await asyncio.wait_for(websocket.receive_text(), timeout=30)
            esp32_last_message = message

            if message == "PONG":
                esp32_last_pong_at = _utc_now()
                print(f"ESP32 WebSocket PONG at {esp32_last_pong_at}")
            else:
                print(f"ESP32 WebSocket message: {message}")

                # ESP32 forwards an OpenRB reply in this form. A single
                # command at a time is allowed, so its reply can be paired
                # safely with the HTTP request that sent the command.
                if message.startswith("OPENRB ") and esp32_command_reply:
                    if not esp32_command_reply.done():
                        esp32_command_reply.set_result(message.removeprefix("OPENRB "))
    except asyncio.TimeoutError:
        print("ESP32 WebSocket timed out waiting for PONG")
        await websocket.close(code=1011, reason="PONG timeout")
    except WebSocketDisconnect:
        print("ESP32 WebSocket disconnected")
    finally:
        ping_task.cancel()
        try:
            await ping_task
        except asyncio.CancelledError:
            pass
        if esp32_socket is websocket:
            esp32_socket = None
            await _broadcast_to_clients({"type": "esp32", "connected": False})


@app.websocket("/ws/client")
async def client_websocket(websocket: WebSocket) -> None:
    """Receive browser commands and relay them over the ESP32's outbound socket.

    Messages are JSON: ``{"type": "command", "command": "ON"}``.
    The endpoint deliberately accepts only the four public switch commands.
    """
    if not _browser_origin_allowed(websocket):
        await websocket.close(code=1008, reason="Origin is not allowed")
        return

    await websocket.accept()
    client_sockets.add(websocket)
    await _send_client_event(
        websocket,
        "connection",
        browser_connected=True,
        esp32_connected=esp32_socket is not None,
    )

    try:
        while True:
            payload = await websocket.receive_json()
            if not isinstance(payload, dict) or payload.get("type") != "command":
                await _send_client_event(websocket, "error", message="Expected a command message.")
                continue

            command = str(payload.get("command", "")).upper().strip()
            if command not in {"ON", "OFF", "TOGGLE", "STATUS"}:
                await _send_client_event(websocket, "error", message="Unsupported command.")
                continue

            if esp32_socket is None:
                await _send_client_event(
                    websocket, "error", message="ESP32 is not connected to the VPS."
                )
                continue

            await _send_client_event(websocket, "command", command=command, status="sent")
            try:
                reply = await _send_esp32_command(command)
                position = _xc330_position_from_reply(reply)
                status = _xc330_status_from_position(position)
            except HTTPException as exc:
                await _send_client_event(websocket, "error", message=str(exc.detail))
                continue

            await _broadcast_to_clients(
                {"type": "status", "command": command, "reply": reply, **status}
            )
    except WebSocketDisconnect:
        pass
    finally:
        client_sockets.discard(websocket)


async def _send_esp32_command(command: str, timeout: float = 15.0) -> str:
    """Send one XC330 command through ESP32 and await its OpenRB reply."""
    global esp32_command_reply

    async with esp32_command_lock:
        if esp32_socket is None:
            raise HTTPException(
                status_code=503,
                detail="ESP32 WebSocket is not connected.",
            )

        reply_future = asyncio.get_running_loop().create_future()
        esp32_command_reply = reply_future
        try:
            await esp32_socket.send_text(command)
            return await asyncio.wait_for(reply_future, timeout=timeout)
        except asyncio.TimeoutError as exc:
            raise HTTPException(
                status_code=504,
                detail=f"Timed out waiting for OpenRB reply to {command}.",
            ) from exc
        finally:
            if esp32_command_reply is reply_future:
                esp32_command_reply = None


def _xc330_position_from_reply(reply: str) -> int:
    """Read the numeric position from OpenRB's DONE or STATUS reply."""
    parts = reply.split()
    if len(parts) == 2 and parts[0] in {"DONE", "STATUS"}:
        try:
            return int(parts[1])
        except ValueError:
            pass
    raise HTTPException(status_code=502, detail=f"OpenRB error: {reply}")


def _xc330_status_from_position(position: int) -> dict:
    profile = get_motor_profile("B")
    state = (
        "on"
        if abs(position - profile.on_position) < abs(position - profile.off_position)
        else "off"
    )
    return {
        "state": state,
        "position": position,
        "on_target": profile.on_position,
        "off_target": profile.off_position,
        "motor": profile.name,
        "model": profile.model,
    }


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


@app.post("/api/xc330/on")
async def api_xc330_on() -> dict:
    position = _xc330_position_from_reply(await _send_esp32_command("ON"))
    return {"state": "on", "position": position}


@app.post("/api/xc330/off")
async def api_xc330_off() -> dict:
    position = _xc330_position_from_reply(await _send_esp32_command("OFF"))
    return {"state": "off", "position": position}


@app.post("/api/xc330/toggle")
async def api_xc330_toggle() -> dict:
    position = _xc330_position_from_reply(await _send_esp32_command("TOGGLE"))
    return _xc330_status_from_position(position)


@app.get("/api/xc330/status")
async def api_xc330_status() -> dict:
    position = _xc330_position_from_reply(await _send_esp32_command("STATUS"))
    return _xc330_status_from_position(position)


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
