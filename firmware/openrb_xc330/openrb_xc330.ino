// Life Switch -- OpenRB-150 + XC330 first-motion test.
//
// Hardware:
//   OpenRB-150 DYNAMIXEL TTL port -> XC330-M288-T
//   OpenRB-150 USB-C -> PC (upload and Serial Monitor)
//
// Send MOVE over the OpenRB USB serial port to move a half-turn (2048 encoder
// counts, about 180 degrees) away from the current position, wait two seconds,
// and return. Disconnect the switch linkage before this test.

#include <Dynamixel2Arduino.h>

constexpr uint8_t DXL_ID = 1;
constexpr uint32_t DXL_BAUDRATE = 57600;
constexpr float DXL_PROTOCOL_VERSION = 2.0;
constexpr int32_t MIN_POSITION = 0;
constexpr int32_t MAX_POSITION = 4095;
constexpr int32_t TEST_OFFSET = 2048;

// OpenRB-150 uses Serial1 for its TTL DYNAMIXEL ports and manages direction
// automatically, so the direction-pin argument is -1.
Dynamixel2Arduino dxl(Serial1, -1);

using namespace ControlTableItem;

bool moveTo(int32_t goal_position) {
  Serial.print("Goal position: ");
  Serial.println(goal_position);

  if (!dxl.setGoalPosition(DXL_ID, goal_position, UNIT_RAW)) {
    Serial.println("ERROR: Could not set Goal Position.");
    return false;
  }

  const uint32_t timeout_at = millis() + 5000;
  while (millis() < timeout_at) {
    const int32_t position = static_cast<int32_t>(dxl.getPresentPosition(DXL_ID, UNIT_RAW));
    Serial.print("Present position: ");
    Serial.println(position);

    if (abs(goal_position - position) <= 10) {
      return true;
    }
    delay(100);
  }

  Serial.println("WARNING: Move timed out.");
  return false;
}

bool prepareMotor() {
  digitalWrite(BDPIN_DXL_PWR_EN, HIGH);  // Energize OpenRB DYNAMIXEL ports.
  // The XC330 must finish booting after the OpenRB power FET is enabled before
  // it can answer the first DYNAMIXEL ping. The old one-shot sketch naturally
  // provided this settling time during setup; the command server must do so
  // explicitly for every MOVE command.
  delay(600);

  if (!dxl.ping(DXL_ID)) {
    Serial.println("ERROR: XC330 ID 1 did not respond.");
    Serial.println("Check 5 V power, TTL cable, ID, baudrate, and DXL power LED.");
    digitalWrite(BDPIN_DXL_PWR_EN, LOW);
    return false;
  }

  // Configuration writes require torque off. Use normal position control for
  // this bring-up test; current-based control comes after communication works.
  dxl.torqueOff(DXL_ID);
  if (!dxl.setOperatingMode(DXL_ID, OP_POSITION)) {
    Serial.println("ERROR: Could not select Position Control Mode.");
    digitalWrite(BDPIN_DXL_PWR_EN, LOW);
    return false;
  }
  // 160 is twice the previous test speed (80), while retaining the same
  // 180-degree travel and return-trip behavior.
  dxl.writeControlTableItem(PROFILE_VELOCITY, DXL_ID, 160);
  dxl.torqueOn(DXL_ID);
  return true;
}

bool runReturnTrip() {
  if (!prepareMotor()) {
    return false;
  }

  const int32_t start = static_cast<int32_t>(dxl.getPresentPosition(DXL_ID, UNIT_RAW));
  const int32_t target = start <= (MAX_POSITION - TEST_OFFSET)
      ? start + TEST_OFFSET
      : start - TEST_OFFSET;

  Serial.print("Start position: ");
  Serial.println(start);
  const bool reached_target = moveTo(target);
  delay(2000);
  const bool returned_home = moveTo(start);

  dxl.torqueOff(DXL_ID);
  digitalWrite(BDPIN_DXL_PWR_EN, LOW);
  return reached_target && returned_home;
}

void setup() {
  Serial.begin(115200);
  delay(500);

  pinMode(BDPIN_DXL_PWR_EN, OUTPUT);
  digitalWrite(BDPIN_DXL_PWR_EN, LOW);

  dxl.begin(DXL_BAUDRATE);
  dxl.setPortProtocolVersion(DXL_PROTOCOL_VERSION);

  Serial.println("Life Switch OpenRB XC330 command server ready.");
  Serial.println("Commands: MOVE, STATUS");
}

void loop() {
  if (!Serial.available()) {
    return;
  }

  String command = Serial.readStringUntil('\n');
  command.trim();
  command.toUpperCase();

  if (command == "MOVE") {
    Serial.println("START");
    if (runReturnTrip()) {
      Serial.println("DONE");
    } else {
      Serial.println("ERROR: Move did not complete.");
    }
  } else if (command == "STATUS") {
    Serial.println("READY");
  } else if (command.length() > 0) {
    Serial.println("ERROR: Unknown command. Use MOVE or STATUS.");
  }
}
