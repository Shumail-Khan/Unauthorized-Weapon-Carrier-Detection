from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.api.routes import router

app = FastAPI(title="WDUP Backend API")

BASE_DIR = Path(__file__).resolve().parent.parent
MEDIA_DIR = BASE_DIR / "media"
INCIDENTS_DIR = MEDIA_DIR / "incidents"
CROPS_DIR = MEDIA_DIR / "crops"
VIDEO_HTML_PATH = BASE_DIR / "video.html"
STATIC_DIR = BASE_DIR / "static"

INCIDENTS_DIR.mkdir(parents=True, exist_ok=True)
CROPS_DIR.mkdir(parents=True, exist_ok=True)
STATIC_DIR.mkdir(parents=True, exist_ok=True)

app.mount("/media", StaticFiles(directory=str(MEDIA_DIR)), name="media")
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

app.include_router(router)

@app.get("/")
def index():
    return FileResponse(str(VIDEO_HTML_PATH))
