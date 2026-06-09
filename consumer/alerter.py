import requests
import json
import os
from datetime import datetime, timezone
from dotenv import load_dotenv

load_dotenv("../.env")

SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL")

# Deduplication store — tracks last alert time per alert type
# Stored in memory — resets if consumer restarts
last_alert_times = {}
COOLDOWN_MINUTES = 10

def should_send_alert(alert_type):
    """Returns True if enough time has passed since last alert of this type"""
    if alert_type not in last_alert_times:
        return True
    
    last_sent = last_alert_times[alert_type]
    minutes_since = (datetime.now(timezone.utc) - last_sent).total_seconds() / 60
    return minutes_since >= COOLDOWN_MINUTES

def send_slack_alert(alert):
    """Send a formatted alert to Slack"""
    alert_type = alert.get("type")
    
    if not should_send_alert(alert_type):
        print(f"[COOLDOWN] Skipping {alert_type} — sent recently")
        return False

    # Format message based on alert type
    if alert_type == "error_spike":
        emoji = "🔴"
        title = "Error Spike Detected"
        detail = f"{alert.get('count')} errors in last {alert.get('window_minutes')} minutes (threshold: {alert.get('threshold')})"
    
    elif alert_type == "failed_login_spike":
        emoji = "⚠️"
        title = "Failed Login Spike"
        detail = f"{alert.get('count')} failed logins in last {alert.get('window_minutes')} minutes (threshold: {alert.get('threshold')})"
    
    elif alert_type == "slow_response":
        emoji = "🐢"
        title = "Slow Response Detected"
        slow_routes = alert.get("slow_routes", [])
        detail = "\n".join([
            f"• {r['route']}: {r['avg_response_time']}ms avg ({r['sample_count']} requests)"
            for r in slow_routes
        ])
    
    else:
        emoji = "❓"
        title = "Unknown Alert"
        detail = str(alert)

    message = {
        "blocks": [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"{emoji} JobFinder Alert: {title}"
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": detail
                }
            },
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": f"Detected at: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}"
                    }
                ]
            }
        ]
    }

    try:
        response = requests.post(
            SLACK_WEBHOOK_URL,
            data=json.dumps(message),
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            last_alert_times[alert_type] = datetime.now(timezone.utc)
            print(f"[ALERT SENT] {alert_type} -> Slack")
            return True
        else:
            print(f"[SLACK ERROR] Status {response.status_code}: {response.text}")
            return False
            
    except Exception as e:
        print(f"[SLACK ERROR] {e}")
        return False

def process_alerts(detection_results):
    """Process all alerts from detection results"""
    alerts = detection_results.get("alerts", [])
    
    if not alerts:
        print(f"[{datetime.now(timezone.utc).strftime('%H:%M:%S')}] No alerts")
        return
    
    print(f"[{datetime.now(timezone.utc).strftime('%H:%M:%S')}] {len(alerts)} alert(s) found")
    for alert in alerts:
        send_slack_alert(alert)