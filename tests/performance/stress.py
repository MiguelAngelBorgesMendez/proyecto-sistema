import csv
import json
import math
import time
from pathlib import Path
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
from urllib.request import urlopen

URL = "http://localhost/api/products/cheapest"
LEVELS = [5, 10, 20, 30]
DURATION = 25
PAUSE = 0.10

OUT = Path("tests/performance/results")
OUT.mkdir(parents=True, exist_ok=True)
STAMP = datetime.now().strftime("%Y%m%d_%H%M%S")

records = []
summaries = []

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

def worker(worker_id, users, deadline):
    local = []

    while time.monotonic() < deadline:
        start = time.perf_counter()
        status = 0
        error = ""

        try:
            with urlopen(URL, timeout=3) as response:
                status = response.status
                response.read()
        except Exception as exc:
            error = str(exc)[:150]

        latency = (time.perf_counter() - start) * 1000

        local.append({
            "timestamp": datetime.now().isoformat(),
            "users": users,
            "worker": worker_id,
            "status": status,
            "latency_ms": round(latency, 3),
            "error": error
        })

        time.sleep(PAUSE)

    return local

for users in LEVELS:
    print(f"\n===== STRESS: {users} USUARIOS =====", flush=True)

    started = time.monotonic()
    deadline = started + DURATION

    with ThreadPoolExecutor(max_workers=users) as executor:
        jobs = [
            executor.submit(worker, i + 1, users, deadline)
            for i in range(users)
        ]
        stage = [r for job in jobs for r in job.result()]

    elapsed = time.monotonic() - started
    records.extend(stage)

    latencies = [r["latency_ms"] for r in stage]
    errors = sum(r["status"] != 200 for r in stage)
    total = len(stage)

    summary = {
        "users": users,
        "duration_s": round(elapsed, 2),
        "requests": total,
        "errors": errors,
        "error_rate_pct": round(100 * errors / total, 3) if total else 100,
        "throughput_rps": round(total / elapsed, 2),
        "p50_ms": percentile(latencies, 50),
        "p95_ms": percentile(latencies, 95),
        "p99_ms": percentile(latencies, 99)
    }

    summaries.append(summary)

    for key, value in summary.items():
        print(f"{key}: {value}", flush=True)

    if summary["error_rate_pct"] > 1:
        print("LIMITE DE ERRORES SUPERADO. Deteniendo prueba.")
        break

    if summary["p95_ms"] is None or summary["p95_ms"] > 500:
        print("LIMITE DE LATENCIA SUPERADO. Deteniendo prueba.")
        break

    print("Nivel completado.", flush=True)
    time.sleep(5)

csv_path = OUT / f"stress_{STAMP}.csv"
json_path = OUT / f"stress_{STAMP}_summary.json"

with csv_path.open("w", newline="", encoding="utf-8") as file:
    writer = csv.DictWriter(
        file,
        fieldnames=[
            "timestamp", "users", "worker",
            "status", "latency_ms", "error"
        ]
    )
    writer.writeheader()
    writer.writerows(records)

json_path.write_text(
    json.dumps(summaries, indent=2),
    encoding="utf-8"
)

print("\n===== RESULTADOS GUARDADOS =====")
print(csv_path)
print(json_path)
print("===== STRESS TEST FINALIZADO =====")
