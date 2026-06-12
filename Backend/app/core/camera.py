import cv2
import os
import time

from datetime import datetime
from uuid import uuid4

from app.db.database import incidents_collection

from app.core.alert_service import send_email_alert
from app.core.runtime_config import runtime_config
from app.core.state_manager import threat_memory
from app.core.processor import process_frame
from app.core.live_state import live_state

MEDIA_FOLDER = "media/incidents"
CROP_FOLDER = "media/crops"

os.makedirs(MEDIA_FOLDER, exist_ok=True)
os.makedirs(CROP_FOLDER, exist_ok=True)

camera_instance = None


def get_camera():

    global camera_instance

    if camera_instance is None:

        camera_instance = cv2.VideoCapture(
            runtime_config["camera_index"],
            cv2.CAP_DSHOW
        )

        # Lower resolution = faster
        camera_instance.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        camera_instance.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

        # Lower internal buffer
        camera_instance.set(cv2.CAP_PROP_BUFFERSIZE, 1)

    return camera_instance


def remove_duplicate_persons(detections):

    persons = []
    others = []

    for d in detections:

        if d["class"] == "Person":
            persons.append(d)
        else:
            others.append(d)

    filtered = []

    for p in persons:

        px1 = p["bbox"]["x1"]
        py1 = p["bbox"]["y1"]
        px2 = p["bbox"]["x2"]
        py2 = p["bbox"]["y2"]

        keep = True

        for existing in filtered:

            ex1 = existing["bbox"]["x1"]
            ey1 = existing["bbox"]["y1"]
            ex2 = existing["bbox"]["x2"]
            ey2 = existing["bbox"]["y2"]

            # simple overlap check
            if (
                abs(px1 - ex1) < 40 and
                abs(py1 - ey1) < 40 and
                abs(px2 - ex2) < 40 and
                abs(py2 - ey2) < 40
            ):
                keep = False
                break

        if keep:
            filtered.append(p)

    return filtered + others


def generate_frames():

    camera = get_camera()

    last_email_time = 0
    last_saved_time = 0

    frame_skip = 2
    frame_count = 0

    latest_frame = None

    while True:

        success, frame = camera.read()

        if not success:
            break

        frame_count += 1

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
        # Skip Frames for Speed
        # =========================
        if frame_count % frame_skip != 0 and latest_frame is not None:

            yield (
                b"--frame\r\n"
                b"Content-Type: image/jpeg\r\n\r\n"
                + latest_frame
                + b"\r\n"
            )

            continue

        # =========================
        # Process Frame
        # =========================
        result = process_frame(frame)

        detections = remove_duplicate_persons(
            result["detections"]
        )

        annotated_frame = result["frame"]
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
        # Live State
        # =========================
        live_state["authorized"] = authorized
        live_state["threat_level"] = threat
        live_state["detections"] = detections
        live_state["last_update"] = datetime.utcnow().isoformat()

        # =========================
        # Save Incident
        # =========================
        if not authorized and (time.time() - last_saved_time > 5):

            filename = f"{uuid4()}.jpg"

            image_path = os.path.join(
                MEDIA_FOLDER,
                filename
            ).replace("\\", "/")

            cv2.imwrite(image_path, annotated_frame)

            crop_paths = []

            for d in detections:

                if d["class"] not in ["Gun", "Weapon"]:
                    continue

                x1 = d["bbox"]["x1"]
                y1 = d["bbox"]["y1"]
                x2 = d["bbox"]["x2"]
                y2 = d["bbox"]["y2"]

                crop = frame[y1:y2, x1:x2]

                if crop.size == 0:
                    continue

                crop_filename = f"{uuid4()}.jpg"

                crop_path = os.path.join(
                    CROP_FOLDER,
                    crop_filename
                ).replace("\\", "/")

                cv2.imwrite(crop_path, crop)

                crop_paths.append(crop_path)

            incident = {
                "timestamp": datetime.utcnow(),
                "detections": detections,
                "authorized": authorized,
                "threat_level": threat,
                "image_path": image_path,
                "crop_paths": crop_paths
            }

            incidents_collection.insert_one(incident)
            if time.time() - last_email_time > 30:
                send_email_alert(
                    threat_level=threat,
                    detections=detections
                )
                last_email_time = time.time()

            last_saved_time = time.time()

        # =========================
        # Encode & Stream
        # =========================
        ret, buffer = cv2.imencode(
            ".jpg",
            annotated_frame,
            [cv2.IMWRITE_JPEG_QUALITY, 70]
        )

        latest_frame = buffer.tobytes()

        yield (
            b"--frame\r\n"
            b"Content-Type: image/jpeg\r\n\r\n"
            + latest_frame
            + b"\r\n"
        )

        time.sleep(0.01)

    camera.release()
    global camera_instance
    camera_instance = None