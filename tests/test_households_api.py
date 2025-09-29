import os
import uuid
from fastapi.testclient import TestClient

# Ensure tests use a separate SQLite DB file
os.environ["DATABASE_URL"] = "sqlite:///./test_air_quality.db"

from app.main import app  # noqa: E402  (import after env var set)

client = TestClient(app)


def test_create_household_and_get():
    payload = {
        "zipcode": "10001",
        "housing_type": "apartment",
        "address": f"{uuid.uuid4()} Example St",
        "risk_score": 10.5,
    }
    r = client.post("/api/v1/households", json=payload)
    assert r.status_code == 200, r.text
    data = r.json()
    hid = data["household_id"]

    r2 = client.get(f"/api/v1/households/{hid}")
    assert r2.status_code == 200, r2.text
    data2 = r2.json()
    assert data2["zipcode"] == payload["zipcode"]
    assert data2["housing_type"] == payload["housing_type"]


def test_add_reading_and_alerts_to_household():
    # Create household
    r = client.post(
        "/api/v1/households",
        json={"zipcode": "10001", "housing_type": "apartment"},
    )
    assert r.status_code == 200, r.text
    hid = r.json()["household_id"]

    # Add a reading via household endpoints
    reading_payload = {
        "household_id": hid,
        "device_id": "dev-001",
        "pm25": 15.0,
        "co2": 900,
        "voc": 120.0,
        "humidity": 45.0,
        "mold_flag": False,
    }
    r2 = client.post(f"/api/v1/households/{hid}/readings", json=reading_payload)
    assert r2.status_code == 200, r2.text
    reading = r2.json()
    assert reading["household_id"] == hid

    # Create an alert for household
    alert_payload = {
        "household_id": hid,
        "event_type": "pm25_high",
        "alert_message": "PM2.5 exceeds threshold",
        "reading_id": reading["reading_id"],
    }
    r3 = client.post(f"/api/v1/households/{hid}/alerts", json=alert_payload)
    assert r3.status_code == 200, r3.text

    # Fetch alerts
    r4 = client.get(f"/api/v1/households/{hid}/alerts?hours_back=24")
    assert r4.status_code == 200, r4.text
    alerts = r4.json()
    assert isinstance(alerts, list)
    assert any(a["event_type"] == "pm25_high" for a in alerts)


def test_health_context_upsert_and_get():
    upsert_payload = {
        "zipcode": "10001",
        "asthma_rate": 18.3,
        "er_visit_rate": 22.7,
        "ej_index": 0.63,
    }
    r = client.put("/api/v1/health-context", json=upsert_payload)
    assert r.status_code == 200, r.text

    r2 = client.get("/api/v1/health-context/10001")
    assert r2.status_code == 200, r2.text
    ctx = r2.json()
    assert ctx["zipcode"] == "10001"
    assert ctx["asthma_rate"] == 18.3
