from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from app.webhook import router as webhook_router
from app.scheduler.alerts import router as alerts_router

app = FastAPI(title="Kisan Alert", version="1.0.0")

app.include_router(webhook_router, prefix="/webhook")
app.include_router(alerts_router, prefix="/alerts")

@app.get("/")
async def health():
    return {"status": "ok", "service": "kisan-alert"}
