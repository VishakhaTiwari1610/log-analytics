import boto3
import pymongo
import json
import time
import schedule
from dotenv import load_dotenv
import os
from detector import run_all_detectors
from alerter import process_alerts

load_dotenv("../.env")

sqs = boto3.client(
    "sqs",
    region_name="ap-southeast-2",
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY")
)

mongo_client = pymongo.MongoClient(os.getenv("MONGODB_URI"))
db = mongo_client["jobfinder_analytics"]
logs_collection = db["logs"]

logs_collection.create_index("timestamp")
logs_collection.create_index("statusCode")
logs_collection.create_index("event")

QUEUE_URL = os.getenv("AWS_SQS_QUEUE_URL")

def process_message(message):
    try:
        log_entry = json.loads(message["Body"])
        logs_collection.insert_one(log_entry)
        print(f"Stored: {log_entry.get('event')} - {log_entry.get('route')}")
        return True
    except Exception as e:
        print(f"Failed to process message: {e}")
        return False

def poll_queue():
    try:
        response = sqs.receive_message(
            QueueUrl=QUEUE_URL,
            MaxNumberOfMessages=10,
            WaitTimeSeconds=20
        )
        messages = response.get("Messages", [])
        
        if not messages:
            return
            
        for message in messages:
            success = process_message(message)
            if success:
                sqs.delete_message(
                    QueueUrl=QUEUE_URL,
                    ReceiptHandle=message["ReceiptHandle"]
                )
    except Exception as e:
        print(f"Polling error: {e}")

def run_detection():
    results = run_all_detectors()
    process_alerts(results)

# Schedule detection every 60 seconds
schedule.every(60).seconds.do(run_detection)

print("Consumer started. Polling SQS + running detection every 60s...")

# Run detection once immediately on startup
run_detection()

while True:
    poll_queue()
    schedule.run_pending()
    time.sleep(1)

    # {"event":"api_request","method":"GET","route":"/api/v1/jobs/get","statusCode":401,"responseTime":1,"userId":null,"ip":"::1","timestamp":"2026-06-08T15:45:10.626Z"}