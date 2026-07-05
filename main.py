from dotenv import load_dotenv
load_dotenv()

from pathlib import Path
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from app.webhook import router as webhook_router
from app.scheduler.alerts import router as alerts_router

app = FastAPI(title="Kisan Alert", version="1.0.0")

app.include_router(webhook_router, prefix="/webhook")
app.include_router(alerts_router, prefix="/alerts")

LANDING_PAGE = (Path(__file__).parent / "app" / "static" / "index.html").read_text()

@app.get("/", response_class=HTMLResponse)
async def landing_page():
    return LANDING_PAGE

@app.get("/health")
async def health():
    return {"status": "ok", "service": "kisan-alert"}
