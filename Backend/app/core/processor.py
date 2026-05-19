import cv2
import os
import time

from uuid import uuid4
from datetime import datetime

from app.core.detection import detect_objects
from app.core.authorization import check_authorization
from app.core.annotation import draw_annotations
from app.core.threat_engine import classify_threat
from app.db.database import incidents_collection

MEDIA_FOLDER = "media/incidents"
CROP_FOLDER = "media/crops"


def process_frame(frame):

    detections = detect_objects(frame)

    authorized = check_authorization(detections)

    threat = classify_threat(detections)

    annotated_frame = draw_annotations(
        frame.copy(),
        detections,
        threat_level=threat,
        is_authorized=authorized
    )

    crop_paths = []

    if not authorized:

        filename = f"{uuid4()}.jpg"

        image_path = os.path.join(
            MEDIA_FOLDER,
            filename
        ).replace("\\", "/")

        cv2.imwrite(image_path, annotated_frame)

        for d in detections:

            if d["class"] in ["Gun", "Weapon"]:

                x1 = d["bbox"]["x1"]
                y1 = d["bbox"]["y1"]
                x2 = d["bbox"]["x2"]
                y2 = d["bbox"]["y2"]

                crop = frame[y1:y2, x1:x2]

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

    return {
        "frame": annotated_frame,
        "detections": detections,
        "authorized": authorized,
        "threat": threat
    }