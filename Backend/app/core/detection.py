from ultralytics import YOLO
from app.config import MODEL_PATH, CONF_THRESHOLD
from app.core.runtime_config import runtime_config

# Load models
person_model = YOLO("yolov8n.pt")              # COCO
custom_model = YOLO(MODEL_PATH)       # Your trained mode

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

    return detections