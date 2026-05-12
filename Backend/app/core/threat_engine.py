def classify_threat(detections):

    persons = [d for d in detections if d["class"] == "Person"]
    weapons = [d for d in detections if d["class"] in ["Gun", "Weapon"]]

    if not weapons:
        return "LOW"

    count = len(persons)

    if count <= 1:
        return "LOW"
    elif count <= 5:
        return "MEDIUM"
    else:
        return "HIGH"