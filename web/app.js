const stateEl = document.getElementById("state");
const positionEl = document.getElementById("position");
const messageEl = document.getElementById("message");
const statusBox = document.getElementById("status-box");

function setMessage(text, isError = false) {
  messageEl.textContent = text;
  messageEl.className = isError ? "message error" : "message";
}

function updateStatus(data) {
  const label = data.state.toUpperCase();
  stateEl.textContent = label;
  stateEl.className = "state " + data.state;
  positionEl.textContent = "Position: " + data.position;
  statusBox.className = "status-box " + data.state;
}

async function callApi(path, method = "POST") {
  setMessage("Working...");
  try {
    const response = await fetch(path, { method });
    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.detail || "Request failed");
    }
    updateStatus(data);
    setMessage("OK");
  } catch (err) {
    setMessage(err.message, true);
  }
}

document.getElementById("btn-on").addEventListener("click", () => callApi("/api/on"));
document.getElementById("btn-off").addEventListener("click", () => callApi("/api/off"));
document.getElementById("btn-toggle").addEventListener("click", () => callApi("/api/toggle"));
document.getElementById("btn-status").addEventListener("click", () => callApi("/api/status", "GET"));

// Load status when page opens
callApi("/api/status", "GET");
