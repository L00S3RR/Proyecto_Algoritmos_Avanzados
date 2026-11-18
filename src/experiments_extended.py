"""Experimentos reproducibles con varias distribuciones y entorno registrado."""
import csv
import platform
import random
import statistics
import sys
from pathlib import Path
from time import perf_counter

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.algorithms.approximate import first_fit_decreasing, best_fit_decreasing
from src.algorithms.exact import bin_packing_exacto
from src.validation import validate_solution

CAPACITY = 100
SIZES = (6, 10, 14, 18)
SEEDS = (42, 43, 44)
REPETITIONS = 3
EXACT_TIMEOUT = 0.5
ALGORITHMS = {"FFD": first_fit_decreasing, "BFD": best_fit_decreasing, "Exacto": bin_packing_exacto}


def make_instance(n, seed, distribution):
    rng = random.Random(seed)
    bounds = {"uniforme": (10, 90), "concentrada": (40, 60), "cercana_capacidad": (70, 95)}
    low, high = bounds[distribution]
    return [rng.randint(low, high) for _ in range(n)]


def run():
    rows = []
    for distribution in ("uniforme", "concentrada", "cercana_capacidad"):
        for n in SIZES:
            for seed in SEEDS:
                items = make_instance(n, seed, distribution)
                current = []
                for name, algorithm in ALGORITHMS.items():
                    samples = []
                    solution = None
                    status = "ok"
                    for _ in range(REPETITIONS):
                        start = perf_counter()
                        try:
                            solution = algorithm(items, CAPACITY, timeout_s=EXACT_TIMEOUT) if name == "Exacto" else algorithm(items, CAPACITY)
                        except TimeoutError:
                            status = "timeout"
                            break
                        samples.append(perf_counter() - start)
                    if status == "ok":
                        valid, message = validate_solution(items, CAPACITY, solution)
                        if not valid:
                            raise RuntimeError(f"{name}: {message}")
                    bins = len(solution) if status == "ok" else ""
                    current.append({"distribution": distribution, "n": n, "seed": seed,
                                    "capacity": CAPACITY, "items": ";".join(map(str, items)),
                                    "algorithm": name, "status": status, "bins": bins,
                                    "median_runtime_s": f"{statistics.median(samples):.9f}" if samples else "",
                                    "gap_bins_vs_exact": "", "repetitions": len(samples),
                                    "exact_timeout_s": EXACT_TIMEOUT,
                                    "python": platform.python_version(), "os": platform.platform()})
                exact = current[-1]
                if exact["status"] == "ok":
                    for row in current:
                        row["gap_bins_vs_exact"] = row["bins"] - exact["bins"]
                rows.extend(current)
    output = ROOT / "results" / "experiments" / "resultados_ampliados.csv"
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print(f"{output}: {len(rows)} filas, {sum(row['status'] == 'timeout' for row in rows)} timeout(s)")
    return rows


if __name__ == "__main__":
    run()
