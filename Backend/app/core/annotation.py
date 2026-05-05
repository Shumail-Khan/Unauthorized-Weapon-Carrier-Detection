import cv2

def draw_annotations(frame, detections, threat_level=None, is_authorized=True):
    for d in detections:
        x1 = d["bbox"]["x1"]
        y1 = d["bbox"]["y1"]
        x2 = d["bbox"]["x2"]
        y2 = d["bbox"]["y2"]

        label = f'{d["class"]} {d["confidence"]:.2f}'

        color = (0, 0, 255) if d["class"] == "Gun" or d["class"] == "Weapon" else (0, 255, 0)

        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
        cv2.putText(frame, label, (x1, y1 - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

    if not is_authorized:
        # Add a prominent "UNAUTHORIZED" banner with the threat level at the top
        header_text = f"UNAUTHORIZED - THREAT: {threat_level}"
        cv2.putText(frame, header_text, (20, 50),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 255), 3)

    return frame