const API_BASE = "/api/xc330";

const stateEl = document.getElementById("state");
const positionEl = document.getElementById("position");
const messageEl = document.getElementById("message");
const statusBox = document.getElementById("status-box");
const toggleSwitch = document.getElementById("toggle-switch");

let isLoading = false;


function setMessage(text = "", isError = false) {
  messageEl.textContent = text;
  messageEl.className = "message";

  if (text) {
    messageEl.classList.add("visible");
  }

  if (isError) {
    messageEl.classList.add("error");
  }
}


function switchStatusMessage(data) {
  const isOn = String(data.state).toLowerCase() === "on";
  return isOn ? "Switch is now ON" : "Switch is now OFF";
}


function updateStatus(data) {
  const state = String(data.state).toLowerCase();
  const isOn = state === "on";

  stateEl.textContent = isOn ? "ON" : "OFF";
  stateEl.className = `state ${isOn ? "on" : "off"}`;
  statusBox.className = `switch-card ${isOn ? "on" : "off"}`;
  toggleSwitch.checked = isOn;
  positionEl.textContent = `Position ${data.position ?? "—"}`;
}


async function callApi(path, method = "POST") {
  if (isLoading) {
    return;
  }

  isLoading = true;
  statusBox.classList.add("loading");
  setMessage("Working...");

  try {
    const response = await fetch(path, {
      method,
      headers: {
        Accept: "application/json",
      },
    });

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.detail || "Request failed");
    }

    updateStatus(data);
    setMessage(switchStatusMessage(data));
  } catch (error) {
    console.error(error);

    setMessage(
      error.message || "Unable to control XC330.",
      true
    );

    try {
      await loadStatus({ showWorking: false });
    } catch {
      // Keep original error.
    }
  } finally {
    isLoading = false;
    statusBox.classList.remove("loading");
  }
}


async function loadStatus({ showWorking = true } = {}) {
  if (showWorking) {
    setMessage("Working...");
  }

  const response = await fetch(`${API_BASE}/status`, {
    method: "GET",
    headers: {
      Accept: "application/json",
    },
  });

  const data = await response.json();

  if (!response.ok) {
    throw new Error(
      data.detail ||
      "XC330-M288-T not connected. Check U2D2, 5V power, and close Dynamixel Wizard."
    );
  }

  updateStatus(data);

  if (showWorking) {
    setMessage(switchStatusMessage(data));
  }
}


toggleSwitch.addEventListener("change", () => {
  callApi(`${API_BASE}/toggle`);
});


loadStatus().catch((error) => {
  console.error(error);

  setMessage(
    error.message ||
    "XC330-M288-T not connected. Check U2D2, 5V power, and close Dynamixel Wizard.",
    true
  );
});
