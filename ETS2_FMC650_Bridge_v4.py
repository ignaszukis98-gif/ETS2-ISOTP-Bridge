import requests
import json
import time
import os

# =========================
# CONFIG
# =========================

API_URL = "http://localhost:25555/api/ets2/telemetry"
INTERVAL = 1.0

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
            trailer = ets.get("trailer", {})

            # === BASIC INFO ===
            make = truck.get("make", "")
            model = truck.get("model", "")

            # === CORE DATA ===
            speed = abs(truck.get("speed", 0))
            rpm = truck.get("engineRpm", 0)
            fuel = truck.get("fuel", 0)
            fuel_capacity = truck.get("fuelCapacity", 1)

            throttle = truck.get("userThrottle", 0)
            brake = truck.get("userBrake", 0)
            clutch = truck.get("userClutch", 0)

            coolant = truck.get("waterTemperature", 0)
            oil = truck.get("oilTemperature", 0)

            cruise = truck.get("cruiseControlOn", False)

            # PTO from trailer
            pto = int(trailer.get("attached", False))

            # === DERIVED VALUES ===

            # Fuel %
            fuel_percent = int((fuel / fuel_capacity) * 100) if fuel_capacity > 0 else 0

            # Engine load (approximation from throttle)
            engine_load = int(throttle * 100)

            # Torque (approximation)
            torque = int(throttle * 100)

            # Service distance (fake but usable)
            service_distance = int(truck.get("odometer", 0))

            # === LOAD FILE ===
            sim = load_sim()

            # === INFO ===
            sim["info"]["make"] = make
            sim["info"]["model"] = model

            # =========================
            # WRITE SIGNALS
            # =========================

            # --- Brake ---
            sim["broadcast"]["signals"]["_x18F001FF"]["brake_pedal_position"]["value"] = int(brake * 100)

            # --- Temperatures ---
            sim["broadcast"]["signals"]["_x18FEEE18"]["engine_coolant_temperature"]["value"] = int(coolant)
            sim["broadcast"]["signals"]["_x18FEEE18"]["engine_oil_temperature"]["value"] = int(oil)

            # --- Driving state ---
            sim["broadcast"]["signals"]["_x18FEF1FF"]["speed"]["value"] = int(speed)
            sim["broadcast"]["signals"]["_x18FEF1FF"]["clutch"]["value"] = int(clutch > 0)
            sim["broadcast"]["signals"]["_x18FEF1FF"]["cruise_control"]["value"] = int(cruise)
            sim["broadcast"]["signals"]["_x18FEF1FF"]["brake"]["value"] = int(brake > 0)
            sim["broadcast"]["signals"]["_x18FEF1FF"]["PTO"]["value"] = pto

            # --- Engine ---
            sim["broadcast"]["signals"]["_x18F00418"]["rpm"]["value"] = int(rpm)
            sim["broadcast"]["signals"]["_x18F00418"]["torque"]["value"] = torque

            # --- Fuel ---
            sim["broadcast"]["signals"]["_x18FEFC18"]["fuel_level_1"]["value"] = fuel_percent
            sim["broadcast"]["signals"]["_x18FEFC18"]["fuel_level_2"]["value"] = fuel_percent

            # --- Service ---
            sim["broadcast"]["signals"]["_x18FEC018"]["service_distance"]["value"] = service_distance

            # --- Accelerator + load ---
            sim["broadcast"]["signals"]["_x18F00318"]["accelerator_pedal"]["value"] = int(throttle * 100)
            sim["broadcast"]["signals"]["_x18F00318"]["engine_load_at_current_speed"]["value"] = engine_load

            # === SAVE ===
            write_safe(sim)

            print(
                f"{make} {model} | "
                f"speed={speed:.1f} "
                f"rpm={int(rpm)} "
                f"fuel={fuel_percent}% "
                f"load={engine_load}% "
                f"PTO={pto}"
            )

        except Exception as e:
            print("Error:", e)

        time.sleep(INTERVAL)


if __name__ == "__main__":
    main()