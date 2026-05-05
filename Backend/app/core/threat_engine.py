def classify_threat(detections):
    threat_score = 0

    for d in detections:
        if d["class"] == "Gun" or d["class"] == "Weapon":
            if d["confidence"] > 0.7:
                threat_score += 3
            else:
                threat_score += 1

    if threat_score >= 5:
        return "CRITICAL"
    elif threat_score >= 3:
        return "HIGH"
    elif threat_score >= 1:
        return "MEDIUM"
    else:
        return "LOW"