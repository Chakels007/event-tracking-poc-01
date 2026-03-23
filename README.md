# Event Tracking Pipeline — Apache Kafka + Flink POC

A minimal real-time event streaming pipeline built with Node.js, Apache Flink, and Kafka. Proves the end-to-end plumbing works before adding business logic.

```
Node.js Producer → Kafka [raw-messages] → Flink → Kafka [processed-messages]
```

---

## What This Does

- **Node.js** generates one message per second and publishes it to Kafka
- **Kafka** buffers messages between producer and processor
- **Flink** reads each message, adds `"processed": true` and `"processed_by": "flink"`, and writes to a second Kafka topic
- Everything is wired together with **Docker Compose** — one command boots the full stack

---

## Stack

| Component | Technology | Version |
|-----------|-----------|---------|
| Event Producer | Node.js + kafkajs | Node 20 |
| Message Broker | Apache Kafka | 7.6.0 (Confluent) |
| Stream Processor | Apache Flink (PyFlink) | 1.18 |
| Orchestration | Docker Compose | v2 |

---

## Project Structure

```
event-tracking-poc-01/
├── docker-compose.yml        # defines all 6 services
├── producer/
│   ├── index.js              # Node.js producer — sends 1 msg/sec
│   ├── package.json          # kafkajs dependency
│   └── Dockerfile
└── flink/
    ├── job.py                # PyFlink pipeline — read → enrich → write
    └── Dockerfile
```

---

## Prerequisites

- **Docker Desktop** installed and running (whale icon in taskbar)
- **4 GB RAM** available to Docker
- Ports **8081** (Flink UI) and **9092** (Kafka) free on your machine

---

## Quick Start

```bash
# 1. Clone / navigate to the project
cd event-tracking-poc-01

# 2. Boot the full stack
docker compose up --build
```

First run takes **3–5 minutes** to pull base images. After that, under 30 seconds.

---

## Confirm It's Working

Once running, you should see this in the terminal:

```
producer-1  | [SENT] #1 → Hello from message #1
producer-1  | [SENT] #2 → Hello from message #2

flink-job-1 | FLINK OUT> {"id": 1, "text": "Hello from message #1", "timestamp": "...", "processed": true, "processed_by": "flink"}
flink-job-1 | FLINK OUT> {"id": 2, "text": "Hello from message #2", "timestamp": "...", "processed": true, "processed_by": "flink"}
```

Open the Flink Web UI at **http://localhost:8081** to see the cluster status.

---

## Stop the Pipeline

```bash
Ctrl + C

docker compose down
```

---

## How the Enrichment Works

The `enrich()` function in `flink/job.py` is the extension point for all business logic:

```python
def enrich(raw: str) -> str:
    msg = json.loads(raw)
    msg["processed"] = True         # added by Flink
    msg["processed_by"] = "flink"   # added by Flink
    return json.dumps(msg)
```

Replace the body of this function with anything — filtering, aggregation, fraud scoring, alerting — the pipeline infrastructure stays the same.

---

## Services

| Service | Purpose | Port |
|---------|---------|------|
| zookeeper | Kafka coordinator | internal |
| kafka | Message broker | 9092 |
| jobmanager | Flink master + Web UI | 8081 |
| taskmanager | Flink worker (2 task slots) | internal |
| flink-job | Submits the Python job | internal |
| producer | Node.js event generator | internal |

---

## Troubleshooting

**`kafka connection refused` on startup**
Normal — the producer starts before Kafka is fully ready. It retries automatically. Wait 20–30 seconds.

**Port 8081 already in use**
Change `"8081:8081"` to `"8082:8081"` in `docker-compose.yml` and open `http://localhost:8082` instead.

**Flink UI shows 0 running jobs but console shows messages flowing**
This is expected in the current setup. Flink runs in embedded MiniCluster mode (inside the flink-job container), which is separate from the JobManager UI. The pipeline is working correctly — the UI shows the cluster, not the embedded job.

---

## What's Next

This POC is intentionally empty in the middle. Possible next steps:

- **Filter** — only forward messages matching a condition
- **Aggregate** — count events per user per minute using Flink windows
- **Route** — send different event types to different Kafka topics
- **Score** — run an ML model on each event and attach a result
- **Alert** — trigger a notification when a threshold is crossed

---

## Known Issues Fixed During Setup

| Issue | Fix |
|-------|-----|
| `flink:1.18-python3` image not found on Docker Hub | Switched to `flink:1.18` and installed Python 3 via apt-get |
| `python: command not found` inside Flink container | Added `ln -s /usr/bin/python3 /usr/bin/python` to Dockerfile |
| Files extracted flat with no subfolders | Created `producer/` and `flink/` folders manually and moved files in |
