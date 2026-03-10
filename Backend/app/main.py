from fastapi import FastAPI
from app.api.routes import router
from fastapi.staticfiles import StaticFiles


app = FastAPI(title="WDUP Backend API")
app.mount("/media", StaticFiles(directory="media"), name="media")

app.include_router(router)

@app.get("/")
def root():
    print("WDUP Backend is running.")
    return {"message": "WDUP Backend Running"}