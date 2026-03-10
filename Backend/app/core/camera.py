import cv2
import os
import time
from datetime import datetime
from uuid import uuid4

from app.core.annotation import draw_annotations
from app.core.authorization import check_authorization
from app.core.detection import detect_objects
from app.core.threat_engine import classify_threat
from app.db.database import incidents_collection

def generate_frames():
    camera = cv2.VideoCapture(0)
    while True:
        success, frame = camera.read()
        if not success:
            break

        detections = detect_objects(frame)
        authorized = check_authorization(detections)
        threat = classify_threat(detections)

        annotated_frame = draw_annotations(frame.copy(), detections)

        # If unauthorized → save evidence
        if not authorized:
            filename = f"{uuid4()}.jpg"
            image_path = os.path.join(MEDIA_FOLDER, filename)
            cv2.imwrite(image_path, annotated_frame)

            incident = {
                "timestamp": datetime.utcnow(),
                "detections": detections,
                "authorized": authorized,
                "threat_level": threat,
                "image_path": image_path
            }

            incidents_collection.insert_one(incident)

        # Encode frame
        ret, buffer = cv2.imencode(".jpg", annotated_frame)
        frame_bytes = buffer.tobytes()

        yield (
            b"--frame\r\n"
            b"Content-Type: image/jpeg\r\n\r\n" +
            frame_bytes +
            b"\r\n"
        )

        time.sleep(0.03)  # ~30 FPS