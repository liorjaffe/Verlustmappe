import time
import random
import requests

API_URL = "http://localhost:8000/api/telemetry"

def generate_fc_data(fc_id):
    return {
        "device_id": fc_id,
        "telemetry": {
            "stack_voltage": round(random.uniform(40.0, 48.0), 2),
            "stack_current": round(random.uniform(10.0, 80.0), 2),
            "stack_power": round(random.uniform(400.0, 3800.0), 1),
            "h2_pressure": round(random.uniform(0.4, 0.6), 3),
            "stack_temp": round(random.uniform(55.0, 65.0), 1),
            "air_flow": round(random.uniform(100.0, 300.0), 1),
            "cell_1": round(random.uniform(0.65, 0.78), 3),
            "cell_2": round(random.uniform(0.65, 0.78), 3),
            "cell_3": round(random.uniform(0.65, 0.78), 3),
            "cell_4": round(random.uniform(0.65, 0.78), 3),
        }
    }

def generate_load_data():
    return {
        "device_id": "power_load",
        "telemetry": {
            "actual_voltage": round(random.uniform(47.8, 48.2), 2),
            "actual_current": round(random.uniform(5.0, 50.0), 2),
            "active_power": round(random.uniform(200.0, 2400.0), 1),
            "temperature": round(random.uniform(30.0, 42.0), 1),
        }
    }

def generate_battery_data():
    return {
        "device_id": "gtem_battery",
        "telemetry": {
            "voltage": round(random.uniform(45.0, 52.0), 2),
            "current": round(random.uniform(-30.0, 30.0), 2),
            "power": round(random.uniform(-1500.0, 1500.0), 1),
            "temperature": round(random.uniform(25.0, 35.0), 1),
        }
    }

def main():
    print("Starte Daten-Simulation fuer alle Geraete... (Strg+C zum Beenden)")
    while True:
        try:
            requests.post(API_URL, json=generate_fc_data("fc1_can"))
            requests.post(API_URL, json=generate_fc_data("fc2_can"))
            requests.post(API_URL, json=generate_load_data())
            requests.post(API_URL, json=generate_battery_data())
            print(" Telemetriedaten gesendet.")
        except Exception as e:
            print(f" Fehler beim Senden: {e}")
        time.sleep(1)

if __name__ == "__main__":
    main()
