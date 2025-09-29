from datetime import datetime
from typing import List, Dict, Any, Optional

# Thresholds for alerts
THRESHOLDS = {
    "pm25": {"limit": 35.0, "severity": "warning", "unit": "μg/m³", "message": "PM2.5 above healthy levels"},
    "co2": {"limit": 1200.0, "severity": "warning", "unit": "ppm", "message": "CO2 too high; ventilation recommended"},
    "tvoc": {"limit": 200.0, "severity": "warning", "unit": "ppb", "message": "VOC levels elevated"},
    "humidity_low": {"limit": 30.0, "severity": "info", "unit": "%", "message": "Humidity too low"},
    "humidity_high": {"limit": 60.0, "severity": "info", "unit": "%", "message": "Humidity too high"},
    "mold_risk": {"limit": 0.6, "severity": "warning", "unit": "index", "message": "Mold risk elevated"},
}

METRIC_KEYS = ["pm25", "co2", "tvoc", "humidity", "temperature", "mold_risk"]


def evaluate_reading(payload: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Given a sensor reading payload (already validated), return a list of alert dicts
    describing any triggered conditions. The dict structure matches DB fields except IDs.
    """
    alerts: List[Dict[str, Any]] = []

    # PM2.5
    pm25 = payload.get("pm25")
    if pm25 is not None and pm25 > THRESHOLDS["pm25"]["limit"]:
        alerts.append({
            "metric": "pm25",
            "threshold": THRESHOLDS["pm25"]["limit"],
            "value": float(pm25),
            "severity": THRESHOLDS["pm25"]["severity"],
            "message": THRESHOLDS["pm25"]["message"],
        })

    # CO2
    co2 = payload.get("co2")
    if co2 is not None and co2 > THRESHOLDS["co2"]["limit"]:
        alerts.append({
            "metric": "co2",
            "threshold": THRESHOLDS["co2"]["limit"],
            "value": float(co2),
            "severity": THRESHOLDS["co2"]["severity"],
            "message": THRESHOLDS["co2"]["message"],
        })

    # TVOC
    tvoc = payload.get("tvoc")
    if tvoc is not None and tvoc > THRESHOLDS["tvoc"]["limit"]:
        alerts.append({
            "metric": "tvoc",
            "threshold": THRESHOLDS["tvoc"]["limit"],
            "value": float(tvoc),
            "severity": THRESHOLDS["tvoc"]["severity"],
            "message": THRESHOLDS["tvoc"]["message"],
        })

    # Humidity (both low and high)
    humidity = payload.get("humidity")
    if humidity is not None:
        if humidity < THRESHOLDS["humidity_low"]["limit"]:
            alerts.append({
                "metric": "humidity",
                "threshold": THRESHOLDS["humidity_low"]["limit"],
                "value": float(humidity),
                "severity": THRESHOLDS["humidity_low"]["severity"],
                "message": THRESHOLDS["humidity_low"]["message"],
            })
        if humidity > THRESHOLDS["humidity_high"]["limit"]:
            alerts.append({
                "metric": "humidity",
                "threshold": THRESHOLDS["humidity_high"]["limit"],
                "value": float(humidity),
                "severity": THRESHOLDS["humidity_high"]["severity"],
                "message": THRESHOLDS["humidity_high"]["message"],
            })

    # Mold risk
    mold_risk = payload.get("mold_risk")
    if mold_risk is not None and mold_risk >= THRESHOLDS["mold_risk"]["limit"]:
        alerts.append({
            "metric": "mold_risk",
            "threshold": THRESHOLDS["mold_risk"]["limit"],
            "value": float(mold_risk),
            "severity": THRESHOLDS["mold_risk"]["severity"],
            "message": THRESHOLDS["mold_risk"]["message"],
        })

    return alerts
