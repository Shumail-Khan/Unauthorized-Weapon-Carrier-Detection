from ultralytics import YOLO
from app.config import MODEL_PATH, CONF_THRESHOLD
from app.core.runtime_config import runtime_config

model = YOLO(MODEL_PATH)

def detect_objects(frame):
    results = model(frame, conf=runtime_config["conf_threshold"])

    detections = []

    for r in results:
        for box in r.boxes:
            cls_id = int(box.cls[0])
            conf = float(box.conf[0])
            class_name = model.names[cls_id]

            x1, y1, x2, y2 = box.xyxy[0].tolist()

            detections.append({
                "class": class_name,
                "confidence": conf,
                "bbox": {
                    "x1": int(x1),
                    "y1": int(y1),
                    "x2": int(x2),
                    "y2": int(y2)
                }
            })

    return detections