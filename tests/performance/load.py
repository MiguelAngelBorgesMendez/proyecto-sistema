import csv
import json
import math
import subprocess
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path
from urllib.request import urlopen

URL = "http://localhost/api/products/cheapest"
USERS = 10
DURATION = 600
PAUSE = 0.25

OUT = Path("tests/performance/results")
OUT.mkdir(parents=True, exist_ok=True)
STAMP = datetime.now().strftime("%Y%m%d_%H%M%S")

STOP = threading.Event()
records = []

CONTAINERS = [
    "distributed-three-tier-galera-proxy-1",
    "distributed-three-tier-app1-1",
    "distributed-three-tier-app2-1",
    "distributed-three-tier-app3-1",
    "distributed-three-tier-redis-1",
    "distributed-three-tier-galera1-1",
]

def percentile(values, p):
    if not values:
        return None
    values = sorted(values)
    pos = (len(values) - 1) * p / 100
    lo = math.floor(pos)
    hi = math.ceil(pos)
    return round(
        values[lo] + (values[hi] - values[lo]) * (pos - lo), 2
    )

def worker(worker_id, deadline):
    local = []
    consecutive_errors = 0

    while time.monotonic() < deadline and not STOP.is_set():
        start = time.perf_counter()
        status = 0
        error = ""

        try:
            with urlopen(URL, timeout=5) as response:
                status = response.status
                response.read()
        except Exception as exc:
            error = str(exc)[:200]

        latency = round((time.perf_counter() - start) * 1000, 3)

        local.append({
            "timestamp": datetime.now().isoformat(),
            "worker": worker_id,
            "status": status,
            "latency_ms": latency,
            "error": error
        })

        if status != 200:
            consecutive_errors += 1
        else:
            consecutive_errors = 0

        if consecutive_errors >= 5:
            print(
                f"ALERTA: 5 errores consecutivos en usuario {worker_id}",
                flush=True
            )
            STOP.set()
            break

        STOP.wait(PAUSE)

    return local

def monitor_resources():
    path = OUT / f"load_{STAMP}_docker_stats.txt"

    with path.open("w", encoding="utf-8") as file:
        while not STOP.is_set():
            now = datetime.now().isoformat(timespec="seconds")

            try:
                result = subprocess.run(
                    [
                        "docker", "stats", "--no-stream",
                        "--format",
                        "{{.Name}} | CPU {{.CPUPerc}} | RAM {{.MemUsage}}",
                        *CONTAINERS
                    ],
                    capture_output=True,
                    text=True,
                    timeout=35
                )

                file.write(f"\n===== {now} =====\n")
                file.write(result.stdout)
                if result.returncode:
                    file.write(result.stderr)
                file.flush()

                print(f"[Recursos] Muestra registrada: {now}", flush=True)

            except Exception as exc:
                file.write(f"\n{now}: {exc}\n")
                file.flush()

            if STOP.wait(120):
                break

print("===== LOAD TEST: 10 USUARIOS / 10 MINUTOS =====", flush=True)

start = time.monotonic()
deadline = start + DURATION

monitor = threading.Thread(target=monitor_resources, daemon=True)
monitor.start()

with ThreadPoolExecutor(max_workers=USERS) as executor:
    futures = [
        executor.submit(worker, i + 1, deadline)
        for i in range(USERS)
    ]
    for future in futures:
        records.extend(future.result())

elapsed = time.monotonic() - start
STOP.set()
monitor.join(timeout=40)

latencies = [r["latency_ms"] for r in records]
errors = sum(r["status"] != 200 for r in records)
total = len(records)

summary = {
    "test": "load",
    "users": USERS,
    "planned_duration_s": DURATION,
    "actual_duration_s": round(elapsed, 2),
    "requests": total,
    "errors": errors,
    "error_rate_pct": round(100 * errors / total, 3) if total else 100,
    "throughput_rps": round(total / elapsed, 2),
    "p50_ms": percentile(latencies, 50),
    "p95_ms": percentile(latencies, 95),
    "p99_ms": percentile(latencies, 99),
    "completed_duration": elapsed >= DURATION,
}

for key, value in summary.items():
    print(f"{key}: {value}")

csv_file = OUT / f"load_{STAMP}.csv"
json_file = OUT / f"load_{STAMP}_summary.json"

with csv_file.open("w", newline="", encoding="utf-8") as file:
    writer = csv.DictWriter(
        file,
        fieldnames=[
            "timestamp", "worker", "status", "latency_ms", "error"
        ]
    )
    writer.writeheader()
    writer.writerows(records)

json_file.write_text(
    json.dumps(summary, indent=2),
    encoding="utf-8"
)

print("\n===== EVIDENCIAS GUARDADAS =====")
print(csv_file)
print(json_file)
print(OUT / f"load_{STAMP}_docker_stats.txt")
print("===== LOAD TEST FINALIZADO =====")
