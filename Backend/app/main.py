from fastapi import FastAPI
from app.api.routes import router
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

app = FastAPI(title="WDUP Backend API")
app.mount("/media", StaticFiles(directory="media"), name="media")

app.include_router(router)

@app.get("/")
def index():
    return FileResponse("video.html")