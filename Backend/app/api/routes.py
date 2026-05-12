import os
import cv2
import time

import numpy as np
from datetime import datetime
from fastapi import APIRouter, UploadFile, File
from fastapi.responses import FileResponse, StreamingResponse

from uuid import uuid4

from app.core.camera import generate_frames
from app.core.detection import detect_objects
from app.core.authorization import check_authorization
from app.core.threat_engine import classify_threat
from app.core.alert_service import send_email_alert
from app.core.annotation import draw_annotations
from app.core.runtime_config import runtime_config
from app.db.database import incidents_collection

router = APIRouter()

MEDIA_FOLDER = "media/incidents"
CROP_FOLDER = "media/crops"

@router.get("/incidents")
def get_incidents():
    incidents = list(incidents_collection.find().sort("timestamp", -1))
    for i in incidents:
        i["_id"] = str(i["_id"])
    return incidents

@router.get("/settings")
def get_settings():
    return runtime_config


@router.post("/settings")
async def update_settings(settings: dict):

    if "detection_enabled" in settings:
        runtime_config["detection_enabled"] = settings["detection_enabled"]

    if "conf_threshold" in settings:
        runtime_config["conf_threshold"] = float(settings["conf_threshold"])

    if "camera_index" in settings:
        runtime_config["camera_index"] = int(settings["camera_index"])

    return {
        "message": "Settings updated",
        "current": runtime_config
    }

@router.get("/settings-view")
def settings_page():
    return FileResponse("settings.html")

@router.get("/incidents-view")
def incidents_page():
    return FileResponse("incidents.html")

@router.get("/video-feed")
def video_feed():
    return StreamingResponse(
        generate_frames(),
        media_type="multipart/x-mixed-replace; boundary=frame"
    )

@router.post("/analyze-image") 
async def analyze_image(file: UploadFile = File(...)):
    if not runtime_config["detection_enabled"]:
        return {
            "message": "Detection is disabled"
        }
    
    contents = await file.read()
    nparr = np.frombuffer(contents, np.uint8)
    frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    detections = detect_objects(frame)
    authorized = check_authorization(detections)
    threat = classify_threat(detections)

    image_path = None
    crop_paths = []

    if not authorized:
        # 1️⃣ Draw annotations
        annotated_frame = draw_annotations(
            frame.copy(), 
            detections, 
            threat_level=threat, 
            is_authorized=authorized
        )

        # 2️⃣ Save full annotated frame
        filename = f"{uuid4()}.jpg"
        image_path = os.path.join(MEDIA_FOLDER, filename)
        image_path = image_path.replace("\\", "/")
        cv2.imwrite(image_path, annotated_frame)

        # 3️⃣ Save cropped weapon images
        for d in detections:
            if d["class"] in ["Gun", "Weapon"]:
                x1 = d["bbox"]["x1"]
                y1 = d["bbox"]["y1"]
                x2 = d["bbox"]["x2"]
                y2 = d["bbox"]["y2"]

                crop = frame[y1:y2, x1:x2]

                crop_filename = f"{uuid4()}.jpg"
                crop_path = os.path.join(CROP_FOLDER, crop_filename)
                crop_path = crop_path.replace("\\", "/")
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
        send_email_alert(threat)

    return {
        "authorized": authorized,
        "threat_level": threat,
        "detections": detections,
        "image_saved": image_path
    }