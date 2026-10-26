import csv
import json
import math
import time
from datetime import datetime
from pathlib import Path
from urllib.request import Request, urlopen

BASE = "http://localhost/api"
OUT = Path("tests/performance/results")
OUT.mkdir(parents=True, exist_ok=True)

records = []

def percentile(values, p):
    values = sorted(values)
    pos = (len(values) - 1) * p / 100
    lo = math.floor(pos)
    hi = math.ceil(pos)
    return round(
        values[lo] + (values[hi] - values[lo]) * (pos - lo), 2
    )

def get_catalog():
    start = time.perf_counter()

    with urlopen(
        BASE + "/products/cheapest",
        timeout=10
    ) as response:
        body = response.read()
        status = response.status
        trace = response.headers.get("x-request-trace", "")

    elapsed = (time.perf_counter() - start) * 1000

    return {
        "status": status,
        "ms": round(elapsed, 3),
        "trace": trace,
        "data": json.loads(body)
    }

print("===== CACHE EFFECT: 25 COMPARACIONES =====")

for i in range(1, 26):

    request = Request(
        BASE + "/cache/clear",
        data=b"",
        method="POST"
    )

    with urlopen(request, timeout=10) as response:
        cleared = json.loads(response.read())
        if response.status != 200:
            raise RuntimeError("Fallo la limpieza de cache")

    miss = get_catalog()
    hit = get_catalog()

    valid = (
        cleared.get("cacheKey") == "store:products:cheapest"
        and miss["status"] == 200
        and hit["status"] == 200
        and "cache miss" in miss["trace"].lower()
        and "cache hit" in hit["trace"].lower()
        and miss["data"] == hit["data"]
    )

    records.append({
        "iteration": i,
        "miss_ms": miss["ms"],
        "hit_ms": hit["ms"],
        "valid": valid,
        "miss_trace": miss["trace"],
        "hit_trace": hit["trace"]
    })

    print(
        f"Comparacion {i:02d}: "
        f"MISS={miss['ms']:.2f} ms | "
        f"HIT={hit['ms']:.2f} ms | "
        f"Datos iguales={valid}",
        flush=True
    )

    if not valid:
        print("ERROR: La traza o los datos no coinciden.")
        break

miss_values = [r["miss_ms"] for r in records if r["valid"]]
hit_values = [r["hit_ms"] for r in records if r["valid"]]

stamp = datetime.now().strftime("%Y%m%d_%H%M%S")

csv_file = OUT / f"cache_effect_{stamp}.csv"
json_file = OUT / f"cache_effect_{stamp}_summary.json"

with csv_file.open("w", newline="", encoding="utf-8") as file:
    writer = csv.DictWriter(
        file,
        fieldnames=list(records[0].keys())
    )
    writer.writeheader()
    writer.writerows(records)

summary = {
    "test": "cache_effect",
    "planned_comparisons": 25,
    "valid_comparisons": len(miss_values),
    "all_valid": len(miss_values) == 25,
    "miss_p50_ms": percentile(miss_values, 50) if miss_values else None,
    "miss_p95_ms": percentile(miss_values, 95) if miss_values else None,
    "hit_p50_ms": percentile(hit_values, 50) if hit_values else None,
    "hit_p95_ms": percentile(hit_values, 95) if hit_values else None
}

json_file.write_text(json.dumps(summary, indent=2), encoding="utf-8")

print("\n===== RESUMEN CACHE EFFECT =====")
for key, value in summary.items():
    print(f"{key}: {value}")

print("\n===== ARCHIVOS =====")
print(csv_file)
print(json_file)
print("===== PRUEBA FINALIZADA =====")
