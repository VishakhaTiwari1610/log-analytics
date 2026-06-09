from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pymongo import MongoClient
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv
import os

load_dotenv(".env")

app = FastAPI()
# CORS — allows your React dashboard to call this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

client = MongoClient(os.getenv("MONGODB_URI"))
db = client["jobfinder_analytics"]
logs_collection = db["logs"]

@app.get("/logs/summary")
@app.get("/logs/summary")
@app.get("/logs/summary")
def get_logs_summary():
    # Last 50 logs of ALL types
    recent_logs = list(
        logs_collection.find({}, {"_id": 0})
        .sort("timestamp", -1)
        .limit(50)
    )
    
    # Stats for last 5 minutes — only api_request events
    since = (datetime.now(timezone.utc) - timedelta(minutes=5)).isoformat()
    since = since.replace("+00:00", "Z")
    recent = list(logs_collection.find({
        "timestamp": {"$gte": since},
        "event": "api_request"
    }))
    
    total = len(recent)
    errors = len([l for l in recent if l.get("statusCode", 0) >= 400])
    success = total - errors
    
    avg_response_time = 0
    if recent:
        avg_response_time = round(
            sum(l.get("responseTime", 0) for l in recent) / total, 2
        )

    return {
        "logs": recent_logs,
        "stats": {
            "total_requests_5min": total,
            "errors_5min": errors,
            "success_5min": success,
            "avg_response_time_ms": avg_response_time,
            "error_rate": round((errors / total * 100), 2) if total > 0 else 0
        }
    }

@app.get("/alerts/recent")
def get_recent_alerts():
    """Runs detectors and returns current alert status"""
    import sys
    sys.path.append("consumer")
    from detector import run_all_detectors
    
    results = run_all_detectors()
    
    return {
        "checked_at": results["checked_at"],
        "alert_count": results["alert_count"],
        "alerts": results["alerts"],
        "all_detections": results["detections"]
    }

@app.get("/health")
def health():
    return {"status": "ok", "timestamp": datetime.now(timezone.utc).isoformat()}