# ⚡ DevPulse

> Real-time system monitor with live WebSocket streaming. Beautiful dark dashboard showing CPU, RAM, disk, network and processes — updating every 1.5 seconds.

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.12-blue?logo=python&logoColor=white" />
  <img src="https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi&logoColor=white" />
  <img src="https://img.shields.io/badge/WebSockets-live-brightgreen?logo=socket.io&logoColor=white" />
  <img src="https://img.shields.io/badge/Docker-ready-2496ED?logo=docker&logoColor=white" />
  <img src="https://img.shields.io/badge/psutil-6.0-orange" />
  <img src="https://img.shields.io/badge/License-MIT-purple" />
</p>

---

## ✨ What it monitors

| Metric | Details |
|---|---|
| **CPU** | Global %, per-core bars, frequency, temperature |
| **Memory** | RAM used/free/total + swap |
| **Disk** | Per-partition usage with color-coded bars |
| **Network** | Real-time upload/download speed + totals |
| **Processes** | Top 8 by CPU with inline sparkbars |
| **System** | OS, hostname, architecture, uptime |

All metrics update live via WebSocket every **1.5 seconds** with animated sparkline history charts.

---

## 🚀 Quick Start

### Docker (one command)

```bash
git clone https://github.com/tu-usuario/devpulse.git
cd devpulse
docker compose up -d
```

Open **http://localhost:8080** → live dashboard immediately.

```bash
docker compose logs -f    # follow logs
docker compose down       # stop
```

### Python local (macOS / Linux)

```bash
chmod +x start.sh && ./start.sh
```

### Manual

```bash
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --host 127.0.0.1 --port 8080
```

---

## 🏗️ Architecture

```
devpulse/
├── main.py              # FastAPI + WebSocket broadcaster + psutil metrics
├── static/
│   └── index.html       # Full dashboard: HTML + CSS + Canvas charts (no deps)
├── Dockerfile           # Multi-stage build (~90MB final image)
├── docker-compose.yml   # pid:host for real system metrics
├── requirements.txt
└── start.sh
```

**Key technical decisions:**

- **WebSocket push model** — server pushes every 1.5s, no client polling
- **Canvas-based sparklines** — no chart library, pure Canvas 2D API
- **Ring gauges** — drawn with `arc()` and glow shadows
- **Zero frontend dependencies** — no npm, no webpack, no React
- **psutil** — cross-platform system stats (Linux, macOS, Windows)
- **Multi-stage Docker** — builder stage installs deps, runtime stage is clean

---

## 📡 API

| Endpoint | Type | Description |
|---|---|---|
| `GET /` | HTTP | Dashboard UI |
| `GET /api/snapshot` | HTTP | One-shot JSON metrics |
| `WS /ws` | WebSocket | Live metrics stream (1.5s interval) |
| `GET /docs` | HTTP | Auto-generated Swagger UI |

### Snapshot response shape

```json
{
  "ts": "2024-01-15T10:30:00Z",
  "system": { "os": "Linux", "hostname": "myhost", "uptime": "02:30:00" },
  "cpu": { "percent": 23.4, "per_core": [12, 45, 8, 31], "freq_mhz": 3600 },
  "memory": { "total": 17179869184, "used": 8053063680, "percent": 46.9 },
  "disk": [{ "mountpoint": "/", "used": 42949672960, "percent": 61.0 }],
  "network": { "recv_speed": 125440, "send_speed": 8192 },
  "processes": [{ "name": "python3", "pid": 1234, "cpu": 12.5, "mem": 2.1 }]
}
```

---

## 🐳 Docker details

The compose file uses `pid: host` so the container can see **real host processes** instead of only its own. Volumes mount `/proc` and `/sys` read-only for accurate CPU/network metrics.

Resource limits keep the monitor from impacting what it measures:
- CPU: max 0.25 cores
- RAM: max 128MB

---

## 🛠️ Extending

Some ideas to take it further:
- **Alerts** — WebSocket push notification when CPU/RAM exceeds threshold
- **History** — persist metrics to SQLite and add a 24h graph view  
- **Auth** — add Basic Auth or JWT to expose it on a public server
- **Multi-host** — add an agent mode and aggregate multiple machines
- **Prometheus endpoint** — export `/metrics` for Grafana integration

---

## 📄 License

MIT © 2024
