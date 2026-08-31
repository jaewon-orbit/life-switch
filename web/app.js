// Set window.LIFE_SWITCH_WS_URL before this script to override the endpoint.
const WS_URL = window.LIFE_SWITCH_WS_URL || "wss://switch.jaewon-orbit.com/ws/client";
const RECONNECT_DELAY_MS = 3000;
const stateEl = document.getElementById("state");
const positionEl = document.getElementById("position");
const messageEl = document.getElementById("message");
const statusBox = document.getElementById("status-box");
const connectionEl = document.getElementById("connection-status");
let socket;
let esp32Connected = false;
let reconnectTimer;

function setMessage(text, isError = false) {
  messageEl.textContent = text;
  messageEl.className = isError ? "message error" : "message";
}
function updateConnection(browserConnected, isError = false) {
  connectionEl.textContent = `Browser: ${browserConnected ? "connected to VPS" : "reconnecting to VPS"} · ESP32: ${esp32Connected ? "connected to VPS" : "not connected"}`;
  connectionEl.className = isError ? "connection-status error" : "connection-status";
}
function updateStatus(data) {
  const state = String(data.state).toLowerCase();
  stateEl.textContent = state.toUpperCase();
  stateEl.className = "state " + state;
  positionEl.textContent = "Position: " + data.position;
  statusBox.className = "status-box " + state;
}
function sendCommand(command) {
  if (!socket || socket.readyState !== WebSocket.OPEN) {
    setMessage("Browser is not connected to the VPS yet.", true);
    return;
  }
  setMessage("Sending motor command to VPS...");
  socket.send(JSON.stringify({ type: "command", command }));
}
function connect() {
  clearTimeout(reconnectTimer);
  updateConnection(false);
  socket = new WebSocket(WS_URL);
  socket.onopen = () => updateConnection(true);
  socket.onmessage = ({ data }) => {
    try {
      const event = JSON.parse(data);
      if (event.type === "connection") {
        esp32Connected = Boolean(event.esp32_connected);
        updateConnection(true);
      } else if (event.type === "esp32") {
        esp32Connected = Boolean(event.connected);
        updateConnection(true);
      } else if (event.type === "command") {
        setMessage(`Motor command ${event.command} sent to ESP32...`);
      } else if (event.type === "status") {
        updateStatus(event);
        setMessage("OK");
      } else if (event.type === "error") {
        setMessage(event.message || "Request failed", true);
      }
    } catch {
      setMessage("Received an invalid response from the VPS.", true);
    }
  };
  socket.onclose = () => {
    esp32Connected = false;
    updateConnection(false, true);
    reconnectTimer = setTimeout(connect, RECONNECT_DELAY_MS);
  };
  socket.onerror = () => socket.close();
}
document.getElementById("btn-on").addEventListener("click", () => sendCommand("ON"));
document.getElementById("btn-off").addEventListener("click", () => sendCommand("OFF"));
document.getElementById("btn-toggle").addEventListener("click", () => sendCommand("TOGGLE"));
document.getElementById("btn-status").addEventListener("click", () => sendCommand("STATUS"));
connect();
