import requests
import json
import time
import os

# =========================
# CONFIG
# =========================

API_URL = "http://localhost:25555/api/ets2/telemetry"
INTERVAL = 1.0

# Auto-resolve path to FMS.json (no hardcoded path)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SIM_FILE = os.path.join(
    BASE_DIR,
    "can-isotp-simulator-main",
    "config_samples",
    "FMS.json"
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


# =========================
# MAIN LOOP
# =========================

def main():
    while True:
        try:
            ets = fetch_telemetry()
            truck = ets.get("truck", {})

            # === ETS2 DATA ===
            make = truck.get("make", "")
            model = truck.get("model", "")

            speed = truck.get("speed", 0)
            brake = truck.get("userBrake", 0)
            throttle = truck.get("userThrottle", 0)
            clutch = truck.get("userClutch", 0)

            coolant = truck.get("waterTemperature", 0)
            oil = truck.get("oilTemperature", 0)

            cruise = truck.get("cruiseControlOn", False)

            # Trailer → PTO mapping
            pto = int(ets.get("trailer", {}).get("attached", False))

            # === LOAD FILE ===
            sim = load_sim()

            # === UPDATE INFO ===
            sim["info"]["make"] = make
            sim["info"]["model"] = model

            # === WRITE SIGNALS ===

            # Brake pedal (0–100%)
            sim["broadcast"]["signals"]["_x18F001FF"]["brake_pedal_position"]["value"] = int(brake * 100)

            # Temperatures
            sim["broadcast"]["signals"]["_x18FEEE18"]["engine_coolant_temperature"]["value"] = int(coolant)
            sim["broadcast"]["signals"]["_x18FEEE18"]["engine_oil_temperature"]["value"] = int(oil)

            # === NEW BLOCK (_x18FEF1FF) ===

            # Speed
            sim["broadcast"]["signals"]["_x18FEF1FF"]["speed"]["value"] = int(speed)

            # Clutch (0–1 → 0/1)
            sim["broadcast"]["signals"]["_x18FEF1FF"]["clutch"]["value"] = int(clutch > 0)

            # Cruise control (bool → 0/1)
            sim["broadcast"]["signals"]["_x18FEF1FF"]["cruise_control"]["value"] = int(cruise)

            # Brake (bool)
            sim["broadcast"]["signals"]["_x18FEF1FF"]["brake"]["value"] = int(brake > 0)

            # PTO
            sim["broadcast"]["signals"]["_x18FEF1FF"]["PTO"]["value"] = pto

            # === SAVE ===
            write_safe(sim)

            print(
                f"{make} {model} | "
                f"speed={speed:.1f} km/h "
                f"brake%={int(brake*100)} "
                f"brakeBool={int(brake>0)} "
                f"coolant={int(coolant)} "
                f"oil={int(oil)} "
                f"PTO={pto}"
            )

        except Exception as e:
            print("Error:", e)

        time.sleep(INTERVAL)


if __name__ == "__main__":
    main()