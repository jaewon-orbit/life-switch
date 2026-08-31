// Set window.LIFE_SWITCH_WS_URL before this script to override the endpoint.
const WS_URL = window.LIFE_SWITCH_WS_URL || "wss://switch.jaewon-orbit.com/ws/client";
const RECONNECT_DELAY_MS = 3000;

const stateEl = document.getElementById("state");
const positionEl = document.getElementById("position");
const messageEl = document.getElementById("message");
const statusBox = document.getElementById("status-box");
const toggleSwitch = document.getElementById("toggle-switch");
const connectionEl = document.getElementById("connection-status");

let isLoading = false;
let socket = null;
let reconnectTimer = null;
let esp32Connected = false;

function setMessage(text = "", isError = false) {
  messageEl.textContent = text;
  messageEl.className = "message";
  if (text) messageEl.classList.add("visible");
  if (isError) messageEl.classList.add("error");
}

function updateConnectionStatus(browserConnected, isError = false) {
  connectionEl.textContent = `Browser: ${browserConnected ? "connected to VPS" : "reconnecting to VPS"} · ESP32: ${esp32Connected ? "connected to VPS" : "not connected"}`;
  connectionEl.className = isError ? "connection-status error" : "connection-status";
}

function switchStatusMessage(data) {
  return String(data.state).toLowerCase() === "on" ? "Switch is now ON" : "Switch is now OFF";
}

function updateStatus(data) {
  const isOn = String(data.state).toLowerCase() === "on";
  stateEl.textContent = isOn ? "ON" : "OFF";
  stateEl.className = `state ${isOn ? "on" : "off"}`;
  statusBox.className = `switch-card ${isOn ? "on" : "off"}`;
  toggleSwitch.checked = isOn;
  positionEl.textContent = `Position ${data.position ?? "—"}`;
}

function finishCommand() {
  isLoading = false;
  statusBox.classList.remove("loading");
}

function sendCommand(command) {
  if (isLoading) return;
  if (!socket || socket.readyState !== WebSocket.OPEN) {
    setMessage("Browser is not connected to the VPS yet.", true);
    return;
  }
  isLoading = true;
  statusBox.classList.add("loading");
  setMessage("Sending motor command to VPS...");
  socket.send(JSON.stringify({ type: "command", command }));
}

function connect() {
  clearTimeout(reconnectTimer);
  updateConnectionStatus(false);
  socket = new WebSocket(WS_URL);
  socket.addEventListener("open", () => updateConnectionStatus(true));
  socket.addEventListener("message", ({ data }) => {
    let event;
    try {
      event = JSON.parse(data);
    } catch {
      setMessage("Received an invalid response from the VPS.", true);
      finishCommand();
      return;
    }
    if (event.type === "connection") {
      esp32Connected = Boolean(event.esp32_connected);
      updateConnectionStatus(true);
    } else if (event.type === "esp32") {
      esp32Connected = Boolean(event.connected);
      updateConnectionStatus(true);
      if (!esp32Connected) setMessage("ESP32 disconnected from the VPS.", true);
    } else if (event.type === "command") {
      setMessage(`Motor command ${event.command} sent to ESP32...`);
    } else if (event.type === "status") {
      updateStatus(event);
      setMessage(switchStatusMessage(event));
      finishCommand();
    } else if (event.type === "error") {
      setMessage(event.message || "Unable to control XC330.", true);
      finishCommand();
    }
  });
  socket.addEventListener("close", () => {
    esp32Connected = false;
    updateConnectionStatus(false, true);
    finishCommand();
    reconnectTimer = setTimeout(connect, RECONNECT_DELAY_MS);
  });
  socket.addEventListener("error", () => socket.close());
}

toggleSwitch.addEventListener("change", () => sendCommand("TOGGLE"));
connect();
