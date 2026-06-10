# Real-Time Log Analytics & Alerting System

A production-grade observability system that ingests application logs, 
detects anomalies in real-time, and delivers intelligent alerts — 
built on top of a MERN stack job portal application.

## Motivation

During my internship at E2E Networks, I manually validated cloud 
services and identified failures. I built this system to automate 
that detection process — turning reactive debugging into proactive 
monitoring.

## Live Demo

- **Dashboard**: https://log-dashboard-vishakhatiwari1610s-projects.vercel.app
- **API**: https://log-analytics-x0ij.onrender.com/docs

## Architecture
JobFinder Backend (Node.js)
│
▼
AWS SQS Queue
│
▼
Python Consumer ──────► MongoDB Atlas (log storage)
│
▼
Anomaly Detector (4 rules, runs every 60s)
│
▼
Slack Alerting (with deduplication + cooldown)
│
FastAPI REST API
│
▼
React Dashboard (Vercel)
## Features

- **Structured logging** — Winston-based JSON logging capturing every 
  API request and business event (login, job application, company registration)
- **Async log pipeline** — logs shipped to AWS SQS for decoupled, 
  fault-tolerant processing
- **Failure isolation** — application continues running if the analytics 
  pipeline goes down; local fallback file catches any dropped logs
- **4 anomaly detectors**:
  - Error spike — 10+ errors in 5 minutes
  - Failed login spike — 5+ failed logins in 2 minutes  
  - Slow response — any route averaging over 2000ms
  - Suspicious activity — same user triggering 20+ actions in 1 minute
- **Slack alerting** with 10-minute cooldown deduplication
- **React dashboard** showing live error rate chart, active alerts, 
  and real-time log feed with business event tracking

## Tech Stack

| Layer | Technology |
|---|---|
| Log source | Node.js + Winston |
| Message queue | AWS SQS (long polling) |
| Consumer | Python + boto3 |
| Storage | MongoDB Atlas |
| Detection | Python (rule-based) |
| Alerting | Slack Webhooks |
| API | FastAPI |
| Dashboard | React + Recharts |
| Deployment | Render (API) + Vercel (Dashboard) |

## Running Locally

**Prerequisites:** Node.js, Python 3.x, AWS account, MongoDB Atlas

**1. Backend (log source):**
```bash
cd job-finder-backend
npm install
npm run dev
```

**2. Python consumer:**
```bash
cd log-analytics
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt
python consumer/consumer.py
```

**3. FastAPI:**
```bash
uvicorn api:app --reload --port 8001
```

**4. Dashboard:**
```bash
cd log-dashboard
npm install
npm run dev
```

## Environment Variables

**Backend (.env):**
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
AWS_SQS_QUEUE_URL=
**log-analytics (.env):**
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
AWS_SQS_QUEUE_URL=
MONGODB_URI=
SLACK_WEBHOOK_URL=

## Key Design Decisions

**Why SQS over direct database writes?**
Decouples log generation from processing. If MongoDB is slow or down, 
the application is unaffected. Under heavy traffic, the queue absorbs 
bursts and the consumer processes at its own pace.

**Why rule-based detection over ML?**
Rule-based thresholds are explainable, debuggable, and don't require 
training data. For a v1 observability system, clear thresholds are 
more actionable than probabilistic anomaly scores.

**Why Slack over email/SMS?**
Slack webhooks provide instant team visibility with rich formatting. 
SNS would be better for multi-channel delivery in production, but 
Slack was the right tradeoff for speed and developer experience.