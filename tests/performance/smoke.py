import csv
import json
import math
import time
from datetime import datetime
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from urllib.request import urlopen

URL = "http://localhost/api/products/cheapest"
DURATION = 20
RESULTS = Path("tests/performance/results")
RESULTS.mkdir(parents=True, exist_ok=True)

def percentile(values, p):
    if not values:
        return None
    values = sorted(values)
    pos = (len(values) - 1) * p / 100
    lo, hi = math.floor(pos), math.ceil(pos)
    return values[lo] + (values[hi] - values[lo]) * (pos - lo)

def worker(number, deadline):
    records = []
    while time.monotonic() < deadline:
        start = time.perf_counter()
        status = 0
        error = ""
        try:
            with urlopen(URL, timeout=5) as response:
                status = response.status
                response.read()
        except Exception as exc:
            error = str(exc)[:150]

        ms = (time.perf_counter() - start) * 1000
        records.append({
            "timestamp": datetime.now().isoformat(timespec="milliseconds"),
            "users": number,
            "status": status,
            "latency_ms": round(ms, 3),
            "error": error
        })
        time.sleep(0.15)
    return records

all_records = []
summaries = []

for users in [1, 5]:
    print(f"\n===== SMOKE TEST: {users} USUARIO(S) =====", flush=True)

    started = time.monotonic()
    deadline = started + DURATION

    with ThreadPoolExecutor(max_workers=users) as executor:
        jobs = [executor.submit(worker, users, deadline)
                for _ in range(users)]
        records = [r for job in jobs for r in job.result()]

    elapsed = time.monotonic() - started
    latencies = [r["latency_ms"] for r in records]
    errors = sum(r["status"] != 200 for r in records)

    summary = {
        "test": "smoke",
        "users": users,
        "duration_s": round(elapsed, 2),
        "requests": len(records),
        "errors": errors,
        "error_rate_pct": round(errors * 100 / len(records), 3) if records else 100,
        "throughput_rps": round(len(records) / elapsed, 2),
        "p50_ms": round(percentile(latencies, 50), 2) if latencies else None,
        "p95_ms": round(percentile(latencies, 95), 2) if latencies else None,
        "p99_ms": round(percentile(latencies, 99), 2) if latencies else None
    }

    summaries.append(summary)
    all_records.extend(records)

    for key, value in summary.items():
        print(f"{key}: {value}")

stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
csv_path = RESULTS / f"smoke_{stamp}.csv"
json_path = RESULTS / f"smoke_{stamp}_summary.json"

with csv_path.open("w", newline="", encoding="utf-8") as file:
    writer = csv.DictWriter(file, fieldnames=[
        "timestamp", "users", "status", "latency_ms", "error"
    ])
    writer.writeheader()
    writer.writerows(all_records)

json_path.write_text(
    json.dumps(summaries, indent=2),
    encoding="utf-8"
)

print("\n===== RESULTADOS GUARDADOS =====")
print(csv_path)
print(json_path)
print("===== SMOKE TEST FINALIZADO =====")
