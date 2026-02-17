"""
DevPulse — Real-time System Monitor
Backend: FastAPI + WebSockets + psutil
"""

import asyncio
import json
import os
import platform
import time
from datetime import datetime
from typing import Set

import psutil
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

app = FastAPI(title="DevPulse", version="1.0.0")
app.mount("/static", StaticFiles(directory="static"), name="static")

# ─── Connection Manager ───────────────────────────────────────────────────────

class ConnectionManager:
    def __init__(self):
        self.active: Set[WebSocket] = set()

    async def connect(self, ws: WebSocket):
        await ws.accept()
        self.active.add(ws)

    def disconnect(self, ws: WebSocket):
        self.active.discard(ws)

    async def broadcast(self, data: dict):
        dead = set()
        for ws in self.active:
            try:
                await ws.send_json(data)
            except Exception:
                dead.add(ws)
        self.active -= dead

manager = ConnectionManager()

# ─── Metrics ──────────────────────────────────────────────────────────────────

# Track previous net counters to calculate speed
_prev_net = psutil.net_io_counters()
_prev_net_time = time.time()

def get_metrics() -> dict:
    global _prev_net, _prev_net_time

    # CPU
    cpu_percent   = psutil.cpu_percent(interval=None)
    cpu_freq      = psutil.cpu_freq()
    cpu_count     = psutil.cpu_count(logical=True)
    cpu_count_phys= psutil.cpu_count(logical=False)
    try:
        cpu_temps = psutil.sensors_temperatures()
        temp = next(
            (t.current for group in cpu_temps.values() for t in group if t.current),
            None
        )
    except Exception:
        temp = None

    per_cpu = psutil.cpu_percent(percpu=True, interval=None)

    # Memory
    mem = psutil.virtual_memory()
    swap = psutil.swap_memory()

    # Disk
    disks = []
    for part in psutil.disk_partitions(all=False):
        try:
            usage = psutil.disk_usage(part.mountpoint)
            disks.append({
                "device":     part.device,
                "mountpoint": part.mountpoint,
                "fstype":     part.fstype,
                "total":      usage.total,
                "used":       usage.used,
                "free":       usage.free,
                "percent":    usage.percent,
            })
        except PermissionError:
            continue

    # Network speed
    now_net  = psutil.net_io_counters()
    now_time = time.time()
    elapsed  = now_time - _prev_net_time or 1

    net_recv_speed = (now_net.bytes_recv - _prev_net.bytes_recv) / elapsed
    net_sent_speed = (now_net.bytes_sent - _prev_net.bytes_sent) / elapsed

    _prev_net      = now_net
    _prev_net_time = now_time

    # Top processes (by CPU)
    procs = []
    for p in sorted(
        psutil.process_iter(["pid", "name", "cpu_percent", "memory_percent", "status"]),
        key=lambda x: x.info.get("cpu_percent") or 0,
        reverse=True
    )[:8]:
        procs.append({
            "pid":    p.info["pid"],
            "name":   p.info["name"],
            "cpu":    round(p.info.get("cpu_percent") or 0, 1),
            "mem":    round(p.info.get("memory_percent") or 0, 1),
            "status": p.info.get("status", ""),
        })

    # System info (static-ish)
    boot_time = psutil.boot_time()
    uptime_s  = int(time.time() - boot_time)
    h, rem    = divmod(uptime_s, 3600)
    m, s      = divmod(rem, 60)

    return {
        "ts": datetime.utcnow().isoformat() + "Z",
        "system": {
            "os":       platform.system(),
            "release":  platform.release(),
            "machine":  platform.machine(),
            "hostname": platform.node(),
            "uptime":   f"{h:02d}:{m:02d}:{s:02d}",
            "uptime_s": uptime_s,
        },
        "cpu": {
            "percent":    cpu_percent,
            "per_core":   per_cpu,
            "count":      cpu_count,
            "count_phys": cpu_count_phys,
            "freq_mhz":   round(cpu_freq.current, 0) if cpu_freq else None,
            "freq_max":   round(cpu_freq.max, 0) if cpu_freq else None,
            "temp_c":     round(temp, 1) if temp else None,
        },
        "memory": {
            "total":   mem.total,
            "used":    mem.used,
            "free":    mem.available,
            "percent": mem.percent,
            "swap_used":    swap.used,
            "swap_total":   swap.total,
            "swap_percent": swap.percent,
        },
        "disk": disks,
        "network": {
            "bytes_sent":  now_net.bytes_sent,
            "bytes_recv":  now_net.bytes_recv,
            "packets_sent":now_net.packets_sent,
            "packets_recv":now_net.packets_recv,
            "send_speed":  net_sent_speed,
            "recv_speed":  net_recv_speed,
        },
        "processes": procs,
    }

# ─── Routes ───────────────────────────────────────────────────────────────────

@app.get("/")
def root():
    return FileResponse("static/index.html")

@app.get("/api/snapshot")
def snapshot():
    """One-shot metrics for initial load."""
    return get_metrics()

@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await manager.connect(ws)
    # Prime CPU percent (first call always 0)
    psutil.cpu_percent(interval=None)
    psutil.cpu_percent(percpu=True, interval=None)
    await asyncio.sleep(0.5)
    try:
        while True:
            data = get_metrics()
            await ws.send_json(data)
            await asyncio.sleep(1.5)
    except WebSocketDisconnect:
        manager.disconnect(ws)
    except Exception:
        manager.disconnect(ws)

if __name__ == "__main__":
    import uvicorn
    print("\n⚡ DevPulse starting on http://localhost:8080\n")
    uvicorn.run("main:app", host="0.0.0.0", port=8080, reload=False)
