import cv2
import time
from pathlib import Path

import numpy as np
from datetime import datetime
from fastapi import APIRouter, UploadFile, File
from fastapi.responses import FileResponse, StreamingResponse, JSONResponse

from uuid import uuid4

from app.core.camera import generate_frames
from app.core.detection import detect_objects
from app.core.authorization import check_authorization
from app.core.threat_engine import classify_threat
from app.core.alert_service import send_email_alert
from app.core.annotation import draw_annotations
from app.core.runtime_config import runtime_config
from app.db.database import incidents_collection
from app.core.live_state import live_state

router = APIRouter()

BASE_DIR = Path(__file__).resolve().parents[2]
MEDIA_DIR = BASE_DIR / "media"
MEDIA_FOLDER = MEDIA_DIR / "incidents"
CROP_FOLDER = MEDIA_DIR / "crops"
VIDEO_FOLDER = MEDIA_DIR / "videos"
SETTINGS_HTML = BASE_DIR / "settings.html"
INCIDENTS_HTML = BASE_DIR / "incidents.html"

MEDIA_FOLDER.mkdir(parents=True, exist_ok=True)
CROP_FOLDER.mkdir(parents=True, exist_ok=True)
VIDEO_FOLDER.mkdir(parents=True, exist_ok=True)

@router.get("/incidents")
def get_incidents():
    incidents = list(incidents_collection.find().sort("timestamp", -1))
    for i in incidents:
        i["_id"] = str(i["_id"])
    return incidents

@router.get("/live-status")
def get_live_status():
    return live_state

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
    return FileResponse(str(SETTINGS_HTML))

@router.get("/incidents-view")
def incidents_page():
    return FileResponse(str(INCIDENTS_HTML))

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
        image_path = str(MEDIA_FOLDER / filename).replace("\\", "/")
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
                crop_path = str(CROP_FOLDER / crop_filename).replace("\\", "/")
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
    
@router.post("/analyze-video")
async def analyze_video(file: UploadFile = File(...)):

    input_path = str(VIDEO_FOLDER / f"input_{uuid4()}.mp4").replace("\\", "/")

    output_path = str(VIDEO_FOLDER / f"output_{uuid4()}.mp4").replace("\\", "/")

    with open(input_path, "wb") as buffer:
        buffer.write(await file.read())

    cap = cv2.VideoCapture(input_path)

    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS)

    fourcc = cv2.VideoWriter_fourcc(*"mp4v")

    out = cv2.VideoWriter(
        output_path,
        fourcc,
        fps,
        (width, height)
    )

    from app.core.processor import process_frame

    frame_count = 0

    while True:

        success, frame = cap.read()

        if not success:
            break

        result = process_frame(frame)

        annotated_frame = result["frame"]

        out.write(annotated_frame)

        frame_count += 1

    cap.release()
    out.release()

    return JSONResponse({
        "message": "Video processed successfully",
        "output_video": output_path,
        "frames_processed": frame_count
    })
