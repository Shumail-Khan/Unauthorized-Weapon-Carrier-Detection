import cv2
import os
import time

from datetime import datetime
from uuid import uuid4

from app.db.database import incidents_collection

from app.core.runtime_config import runtime_config
from app.core.state_manager import threat_memory
from app.core.processor import process_frame
from app.core.live_state import live_state

MEDIA_FOLDER = "media/incidents"
CROP_FOLDER = "media/crops"

# Ensure folders exist
os.makedirs(MEDIA_FOLDER, exist_ok=True)
os.makedirs(CROP_FOLDER, exist_ok=True)


def generate_frames():

    camera = cv2.VideoCapture(runtime_config["camera_index"])

    last_saved_time = 0

    while True:

        success, frame = camera.read()

        if not success:
            break

        # =========================
        # Detection Disabled
        # =========================
        if not runtime_config["detection_enabled"]:

            ret, buffer = cv2.imencode(".jpg", frame)

            yield (
                b"--frame\r\n"
                b"Content-Type: image/jpeg\r\n\r\n"
                + buffer.tobytes()
                + b"\r\n"
            )

            continue

        # =========================
        # Process Frame
        # =========================
        result = process_frame(frame)

        annotated_frame = result["frame"]
        detections = result["detections"]
        authorized = result["authorized"]
        threat = result["threat"]

        # =========================
        # Threat Memory
        # =========================
        unauthorized = not authorized

        threat_memory.update(unauthorized)

        if not threat_memory.is_active():
            threat = "LOW"

        # =========================
        # Live State Update
        # =========================
        live_state["authorized"] = authorized
        live_state["threat_level"] = threat
        live_state["detections"] = detections
        live_state["last_update"] = datetime.utcnow().isoformat()

        # =========================
        # Save Incident
        # =========================
        if not authorized and (time.time() - last_saved_time > 5):

            # Save annotated image
            filename = f"{uuid4()}.jpg"

            image_path = os.path.join(
                MEDIA_FOLDER,
                filename
            ).replace("\\", "/")

            cv2.imwrite(image_path, annotated_frame)

            # Save crops
            crop_paths = []

            for d in detections:

                if d["class"] not in ["Gun", "Weapon"]:
                    continue

                x1 = d["bbox"]["x1"]
                y1 = d["bbox"]["y1"]
                x2 = d["bbox"]["x2"]
                y2 = d["bbox"]["y2"]

                crop = frame[y1:y2, x1:x2]

                # Prevent empty crop save
                if crop.size == 0:
                    continue

                crop_filename = f"{uuid4()}.jpg"

                crop_path = os.path.join(
                    CROP_FOLDER,
                    crop_filename
                ).replace("\\", "/")

                cv2.imwrite(crop_path, crop)

                crop_paths.append(crop_path)

            # Store in DB
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

        # =========================
        # Encode & Stream
        # =========================
        ret, buffer = cv2.imencode(".jpg", annotated_frame)

        frame_bytes = buffer.tobytes()

        yield (
            b"--frame\r\n"
            b"Content-Type: image/jpeg\r\n\r\n"
            + frame_bytes
            + b"\r\n"
        )

        time.sleep(0.03)

    camera.release()