import requests
import json
import time
import os
from datetime import datetime

# =========================
# CONFIG
# =========================

API_URL = "http://localhost:25555/api/ets2/telemetry"
INTERVAL = 1.0

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

SIM_FILE = os.path.join(
    BASE_DIR,
    "can-isotp-simulator",
    "config_samples",
    "FMS.json"
)

# Log file setup
LOG_DIR = os.path.join(BASE_DIR, "logs")
os.makedirs(LOG_DIR, exist_ok=True)

LOG_FILE = os.path.join(
    LOG_DIR,
    f"log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
)


# =========================
# HELPERS
# =========================

def fetch_telemetry():
    return requests.post(API_URL, timeout=1).json()


def load_sim():
    with open(SIM_FILE, "r") as f:
        return json.load(f)


def write_safe(data):
    tmp = SIM_FILE + ".tmp"
    with open(tmp, "w") as f:
        json.dump(data, f, indent=4)
    os.replace(tmp, SIM_FILE)


def log(message):
    timestamp = datetime.now().strftime("%H:%M:%S")
    line = f"[{timestamp}] {message}"

    print(line)

    with open(LOG_FILE, "a") as f:
        f.write(line + "\n")


# =========================
# MAIN LOOP
# =========================

def main():
    log("=== Bridge Started ===")

    while True:
        try:
            ets = fetch_telemetry()

            truck = ets.get("truck", {})
            trailer = ets.get("trailer", {})

            # === DATA ===
            make = truck.get("make", "")
            model = truck.get("model", "")

            raw_speed = truck.get("speed", 0)
            speed = abs(raw_speed)  # FIX negative values

            rpm = truck.get("engineRpm", 0)
            fuel = truck.get("fuel", 0)
            fuel_capacity = truck.get("fuelCapacity", 1)

            throttle = truck.get("userThrottle", 0)
            brake = truck.get("userBrake", 0)
            clutch = truck.get("userClutch", 0)

            coolant = truck.get("waterTemperature", 0)
            oil = truck.get("oilTemperature", 0)

            cruise = truck.get("cruiseControlOn", False)
            pto = int(trailer.get("attached", False))

            # === DERIVED ===
            fuel_percent = int((fuel / fuel_capacity) * 100) if fuel_capacity > 0 else 0
            engine_load = int(throttle * 100)
            torque = int(throttle * 100)
            service_distance = int(truck.get("odometer", 0))

            # === LOAD ===
            sim = load_sim()

            # === INFO ===
            sim["info"]["make"] = make
            sim["info"]["model"] = model

            # === WRITE ===
            sim["broadcast"]["signals"]["_x18F001FF"]["brake_pedal_position"]["value"] = int(brake * 100)

            sim["broadcast"]["signals"]["_x18FEEE18"]["engine_coolant_temperature"]["value"] = int(coolant)
            sim["broadcast"]["signals"]["_x18FEEE18"]["engine_oil_temperature"]["value"] = int(oil)

            sim["broadcast"]["signals"]["_x18FEF1FF"]["speed"]["value"] = int(speed)
            sim["broadcast"]["signals"]["_x18FEF1FF"]["clutch"]["value"] = int(clutch > 0)
            sim["broadcast"]["signals"]["_x18FEF1FF"]["cruise_control"]["value"] = int(cruise)
            sim["broadcast"]["signals"]["_x18FEF1FF"]["brake"]["value"] = int(brake > 0)
            sim["broadcast"]["signals"]["_x18FEF1FF"]["PTO"]["value"] = pto

            sim["broadcast"]["signals"]["_x18F00418"]["rpm"]["value"] = int(rpm)
            sim["broadcast"]["signals"]["_x18F00418"]["torque"]["value"] = torque

            sim["broadcast"]["signals"]["_x18FEFC18"]["fuel_level_1"]["value"] = fuel_percent
            sim["broadcast"]["signals"]["_x18FEFC18"]["fuel_level_2"]["value"] = fuel_percent

            sim["broadcast"]["signals"]["_x18FEC018"]["service_distance"]["value"] = service_distance

            sim["broadcast"]["signals"]["_x18F00318"]["accelerator_pedal"]["value"] = int(throttle * 100)
            sim["broadcast"]["signals"]["_x18F00318"]["engine_load_at_current_speed"]["value"] = engine_load

            # === SAVE ===
            write_safe(sim)

            # === LOG EVERYTHING ===
            log(
                f"{make} {model} | "
                f"speed={speed:.1f} | "
                f"rpm={int(rpm)} | "
                f"fuel={fuel_percent}% | "
                f"throttle={int(throttle*100)}% | "
                f"brake={int(brake*100)}% | "
                f"clutch={int(clutch*100)}% | "
                f"coolant={int(coolant)} | "
                f"oil={int(oil)} | "
                f"cruise={int(cruise)} | "
                f"PTO={pto}"
            )

        except Exception as e:
            log(f"ERROR: {e}")

        time.sleep(INTERVAL)


if __name__ == "__main__":
    main()