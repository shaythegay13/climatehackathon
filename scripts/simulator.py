import os
import time
import random
import requests
from datetime import datetime, timezone
from dotenv import load_dotenv

load_dotenv()

BASE_URL = os.getenv("SIMULATOR_BASE_URL", "http://localhost:8000")
ENDPOINT = f"{BASE_URL}/api/v1/sensor-ingest"
ZIPS = os.getenv("SIMULATOR_ZIPCODES", "10001,11201").split(",")
BOROUGH = os.getenv("SIMULATOR_BOROUGH", "Manhattan")
INTERVAL = int(os.getenv("SIMULATOR_INTERVAL_SECONDS", "5"))


def generate_payload(zipcode: str, borough: str):
    return {
        "zipcode": zipcode,
        "borough": borough,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "pm25": round(random.uniform(2, 120), 1),
        "co2": random.randint(400, 2000),
        "tvoc": round(random.uniform(10, 600), 1),
        "humidity": round(random.uniform(20, 75), 1),
        "temperature": round(random.uniform(16, 30), 1),
        "mold_risk": round(random.uniform(0, 1), 2),
    }


def main():
    print(f"Simulator posting to {ENDPOINT} every {INTERVAL}s; zipcodes={ZIPS}")
    try:
        while True:
            for z in ZIPS:
                payload = generate_payload(z.strip(), BOROUGH)
                try:
                    resp = requests.post(ENDPOINT, json=payload, timeout=5)
                    if resp.ok:
                        data = resp.json()
                        print(f"[{datetime.now().isoformat()}] {z}: created reading {data.get('reading_id')} with {data.get('alerts_created')} alerts")
                    else:
                        print(f"Error {resp.status_code}: {resp.text}")
                except requests.RequestException as e:
                    print(f"Request failed: {e}")
            time.sleep(INTERVAL)
    except KeyboardInterrupt:
        print("\nSimulator stopped.")


if __name__ == "__main__":
    main()
