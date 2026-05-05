def check_authorization(detections):
    weapon_detected = False
    uniform_detected = False

    for d in detections:
        if d["class"] == "Gun" or d["class"] == "Weapon":
            weapon_detected = True
        if d["class"] == "Uniform":
            uniform_detected = True

    if weapon_detected and not uniform_detected:
        return False  # Unauthorized

    return True