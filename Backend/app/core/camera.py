import cv2
import os
import time
from datetime import datetime
from uuid import uuid4

from app.core.annotation import draw_annotations
from app.core.authorization import check_authorization
from app.core.detection import detect_objects
from app.db.database import incidents_collection
from app.core.runtime_config import runtime_config
from app.core.state_manager import threat_memory
from app.core.threat_engine import classify_threat

MEDIA_FOLDER = "media/incidents"
CROP_FOLDER = "media/crops"

def generate_frames():
    camera = cv2.VideoCapture(runtime_config["camera_index"])

    last_saved_time = 0  # ✅ cooldown

    while True:
        success, frame = camera.read()
        if not success:
            break

        if not runtime_config["detection_enabled"]:
            # just stream raw frame
            ret, buffer = cv2.imencode(".jpg", frame)
            yield (
                b"--frame\r\n"
                b"Content-Type: image/jpeg\r\n\r\n" +
                buffer.tobytes() +
                b"\r\n"
            )
            continue
        
        detections = detect_objects(frame)
        authorized = check_authorization(detections)
        unauthorized = not authorized
        threat_memory.update(unauthorized)
        
        if threat_memory.is_active():
            threat = classify_threat(detections)
        else:
            threat = "LOW"

        annotated_frame = draw_annotations(
            frame.copy(), 
            detections, 
            threat_level=threat, 
            is_authorized=authorized
        )

        # ✅ Save only every 5 seconds
        if not authorized and (time.time() - last_saved_time > 5):

            # 1️⃣ Save annotated frame
            filename = f"{uuid4()}.jpg"
            image_path = os.path.join(MEDIA_FOLDER, filename)
            cv2.imwrite(image_path, annotated_frame)

            # 2️⃣ Save crops
            crop_paths = []

            for d in detections:
                if d["class"] == "Gun" or d["class"] == "Weapon":
                    x1 = d["bbox"]["x1"]
                    y1 = d["bbox"]["y1"]
                    x2 = d["bbox"]["x2"]
                    y2 = d["bbox"]["y2"]

                    crop = frame[y1:y2, x1:x2]

                    crop_filename = f"{uuid4()}.jpg"
                    crop_path = os.path.join(CROP_FOLDER, crop_filename)
                    cv2.imwrite(crop_path, crop)

                    crop_paths.append(crop_path)

            # 3️⃣ Store in DB
            incident = {
                "timestamp": datetime.utcnow(),
                "detections": detections,
                "authorized": authorized,
                "threat_level": threat,
                "image_path": image_path,
                "crop_paths": crop_paths
            }

            incidents_collection.insert_one(incident)

            last_saved_time = time.time()

        # Encode frame for streaming
        ret, buffer = cv2.imencode(".jpg", annotated_frame)
        frame_bytes = buffer.tobytes()

        yield (
            b"--frame\r\n"
            b"Content-Type: image/jpeg\r\n\r\n" +
            frame_bytes +
            b"\r\n"
        )

        time.sleep(0.03)

    camera.release()