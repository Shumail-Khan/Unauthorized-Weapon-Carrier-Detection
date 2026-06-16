def classify_threat(detections):

    persons = [
        d for d in detections
        if d["class"] == "Person"
    ]

    weapons = [
        d for d in detections
        if d["class"] in ["Gun", "Weapon"]
    ]

    if len(weapons) >= 1 and len(persons) <= 1:
        return "LOW"

    if len(weapons) >= 1 and len(persons) <= 3 and len(persons) > 1:
        return "MEDIUM"

    if len(weapons) >= 1 and len(persons) > 3:
        return "HIGH"

    return "LOW"