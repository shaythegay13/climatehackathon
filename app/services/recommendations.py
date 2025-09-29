from typing import List, Dict

# Simple rule-based recommendations based on alert metrics
RECOMMENDATIONS = {
    "pm25": [
        "Run a HEPA air purifier on high for 1-2 hours.",
        "Seal gaps around windows/doors; avoid indoor burning/cooking without ventilation.",
        "Check outdoor AQI; open windows only if outdoor air is better."
    ],
    "co2": [
        "Increase ventilation: open windows or run mechanical ventilation.",
        "Reduce room occupancy if possible.",
        "Check HVAC fresh air intake and filters."
    ],
    "tvoc": [
        "Increase ventilation and identify VOC sources (cleaners, paints, fragrances).",
        "Use low-VOC products; store chemicals properly.",
        "Run an air purifier with activated carbon if available."
    ],
    "humidity_low": [
        "Use a humidifier and target 40-50% RH.",
        "Add moisture sources (e.g., plants, bowls of water) temporarily.",
        "Avoid over-humidifying to prevent mold."
    ],
    "humidity_high": [
        "Run a dehumidifier and increase ventilation.",
        "Use exhaust fans during showering/cooking.",
        "Fix leaks and dry wet materials within 24-48 hours."
    ],
    "mold_risk": [
        "Reduce indoor humidity to 40-50% RH.",
        "Increase ventilation and dry damp areas quickly.",
        "Inspect for hidden moisture and clean visible mold safely."
    ],
}


def actions_for_alerts(alerts: List[Dict]) -> List[str]:
    actions: List[str] = []
    for a in alerts:
        metric = a.get("metric")
        if metric == "humidity":
            # choose low/high set based on value vs threshold
            if a.get("value", 0) < a.get("threshold", 0):
                actions.extend(RECOMMENDATIONS["humidity_low"])  # low humidity
            else:
                actions.extend(RECOMMENDATIONS["humidity_high"])  # high humidity
        else:
            actions.extend(RECOMMENDATIONS.get(metric, []))
    # de-duplicate keeping order
    seen = set()
    unique_actions = []
    for act in actions:
        if act not in seen:
            seen.add(act)
            unique_actions.append(act)
    return unique_actions
