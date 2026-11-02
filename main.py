from datetime import datetime, timezone
from fastapi import FastAPI

app = FastAPI(
    title="Pocket Option AI Analyzer",
    version="0.1.0",
    description="Read-only market analysis API. No trade execution."
)

@app.get("/")
def home():
    return {
        "project": "Pocket Option AI Analyzer",
        "status": "running",
        "mode": "read-only"
    }

@app.get("/health")
def health():
    return {
        "status": "ok",
        "time_utc": datetime.now(timezone.utc).isoformat()
    }

@app.get("/api/status")
def api_status():
    return {
        "connected": False,
        "live_data": False,
        "credentials_configured": False,
        "message": "Market-data adapter is not configured yet.",
        "read_only": True
    }
