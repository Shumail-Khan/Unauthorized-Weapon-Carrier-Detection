from ultralytics import YOLO
from app.config import MODEL_PATH, CONF_THRESHOLD
from app.core.runtime_config import runtime_config

# Load models
person_model = YOLO("yolov8n.pt")              # COCO
custom_model = YOLO(MODEL_PATH)       # Your trained mode

def boxes_overlap(boxA, boxB, threshold=0.5):

    xA = max(boxA["x1"], boxB["x1"])
    yA = max(boxA["y1"], boxB["y1"])
    xB = min(boxA["x2"], boxB["x2"])
    yB = min(boxA["y2"], boxB["y2"])

    inter = max(0, xB - xA) * max(0, yB - yA)

    if inter <= 0:
        return False

    areaA = (
        (boxA["x2"] - boxA["x1"]) *
        (boxA["y2"] - boxA["y1"])
    )

    areaB = (
        (boxB["x2"] - boxB["x1"]) *
        (boxB["y2"] - boxB["y1"])
    )

    iou = inter / float(areaA + areaB - inter)

    return iou > threshold

def detect_objects(frame):

    detections = []

    # =========================
    # 1️⃣ PERSON DETECTION (COCO)
    # =========================
    person_results = person_model(frame, conf=0.4)

    for r in person_results:
        for box in r.boxes:
            cls_id = int(box.cls[0])
            class_name = person_model.names[cls_id]

            if class_name != "person":
                continue

            x1, y1, x2, y2 = box.xyxy[0].tolist()

            detections.append({
                "class": "Person",
                "confidence": float(box.conf[0]),
                "bbox": {
                    "x1": int(x1),
                    "y1": int(y1),
                    "x2": int(x2),
                    "y2": int(y2)
                },
                "source": "COCO"
            })

    # =========================
    # 2️⃣ CUSTOM MODEL (Weapon + Uniform)
    # =========================
    custom_results = custom_model(
        frame,
        conf=runtime_config["conf_threshold"]
    )

    for r in custom_results:
        for box in r.boxes:

            cls_id = int(box.cls[0])
            class_name = custom_model.names[cls_id]

            x1, y1, x2, y2 = box.xyxy[0].tolist()

            detections.append({
                "class": class_name,
                "confidence": float(box.conf[0]),
                "bbox": {
                    "x1": int(x1),
                    "y1": int(y1),
                    "x2": int(x2),
                    "y2": int(y2)
                },
                "source": "CUSTOM"
            })

    filtered = []

    for d in detections:

        duplicate = False

        for f in filtered:

            same_class = d["class"] == f["class"]

            overlap = boxes_overlap(
                d["bbox"],
                f["bbox"]
            )

            if same_class and overlap:
                duplicate = True
                break

        if not duplicate:
            filtered.append(d)

    return filtered