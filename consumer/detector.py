from datetime import datetime, timezone, timedelta
from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv("../.env")

client = MongoClient(os.getenv("MONGODB_URI"))
db = client["jobfinder_analytics"]
logs = db["logs"]

def get_recent_logs(minutes):
    """Get logs from the last N minutes"""
    since = datetime.now(timezone.utc) - timedelta(minutes=minutes)
    return list(logs.find({
        "timestamp": {"$gte": since.isoformat()}
    }))

def detect_error_spike():
    """Rule 1: More than 10 errors in last 5 minutes"""
    recent = get_recent_logs(5)
    errors = [l for l in recent if l.get("statusCode", 0) >= 400]
    
    if len(errors) > 10:
        return {
            "alert": True,
            "type": "error_spike",
            "count": len(errors),
            "threshold": 10,
            "window_minutes": 5,
            "message": f"{len(errors)} errors detected in the last 5 minutes"
        }
    return {"alert": False, "type": "error_spike", "count": len(errors)}

def detect_failed_login_spike():
    """Rule 2: More than 5 failed logins in last 2 minutes"""
    since = datetime.now(timezone.utc) - timedelta(minutes=2)
    recent = list(logs.find({
        "timestamp": {"$gte": since.isoformat()},
        "route": "/api/v1/user/login",
        "statusCode": {"$in": [400, 401]}
    }))
    
    if len(recent) > 5:
        return {
            "alert": True,
            "type": "failed_login_spike",
            "count": len(recent),
            "threshold": 5,
            "window_minutes": 2,
            "message": f"{len(recent)} failed login attempts in the last 2 minutes"
        }
    return {"alert": False, "type": "failed_login_spike", "count": len(recent)}

def detect_slow_responses():
    """Rule 3: Any route averaging over 2000ms in last 5 minutes"""
    recent = get_recent_logs(5)
    
    # Group by route
    route_times = {}
    for log in recent:
        route = log.get("route", "unknown")
        rt = log.get("responseTime", 0)
        if route not in route_times:
            route_times[route] = []
        route_times[route].append(rt)
    
    slow_routes = []
    for route, times in route_times.items():
        avg = sum(times) / len(times)
        if avg > 2000:
            slow_routes.append({
                "route": route,
                "avg_response_time": round(avg, 2),
                "sample_count": len(times)
            })
    
    if slow_routes:
        return {
            "alert": True,
            "type": "slow_response",
            "slow_routes": slow_routes,
            "message": f"{len(slow_routes)} route(s) averaging over 2000ms"
        }
    return {"alert": False, "type": "slow_response"}

def run_all_detectors():
    """Run all detectors and return results"""
    results = {
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "detections": [
            detect_error_spike(),
            detect_failed_login_spike(),
            detect_slow_responses()
        ]
    }
    
    alerts = [d for d in results["detections"] if d.get("alert")]
    results["alert_count"] = len(alerts)
    results["alerts"] = alerts
    
    return results

if __name__ == "__main__":
    results = run_all_detectors()
    print(f"\nChecked at: {results['checked_at']}")
    print(f"Active alerts: {results['alert_count']}")
    
    for detection in results["detections"]:
        status = "ALERT" if detection.get("alert") else "OK"
        print(f"  [{status}] {detection['type']}: count={detection.get('count', 'N/A')}")
    
    if results["alerts"]:
        print("\nAlert details:")
        for alert in results["alerts"]:
            print(f"  -> {alert.get('message')}")