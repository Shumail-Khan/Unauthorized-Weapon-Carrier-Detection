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
    
    return {
        "frame": annotated_frame,
        "detections": detections,
        "authorized": authorized,
        "threat": threat
    }