"""Corridas preliminares reproducibles para Avance 7."""
import csv
import statistics
from pathlib import Path
import sys
from time import perf_counter
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from src.algorithms.approximate import best_fit_decreasing, first_fit_decreasing
from src.algorithms.exact import bin_packing_exacto
from src.generator import generar_instancia
from src.validation import validate_solution

OUT = ROOT / "results" / "experiments"
OUT.mkdir(parents=True, exist_ok=True)
ALGORITHMS = {"FFD": first_fit_decreasing, "BFD": best_fit_decreasing, "Exacto": bin_packing_exacto}
rows = []
for n in (6, 8, 10, 12, 14, 16):
    for seed in (42, 43, 44):
        items = generar_instancia(n, 100, seed)
        outputs = {}
        for name, algorithm in ALGORITHMS.items():
            samples = []
            solution = None
            for _ in range(5):
                start = perf_counter()
                solution = algorithm(items, 100)
                samples.append(perf_counter() - start)
            valid, message = validate_solution(items, 100, solution)
            if not valid:
                raise RuntimeError(f"{name}: {message}")
            outputs[name] = solution
            rows.append({"n": n, "seed": seed, "capacity": 100, "algorithm": name,
                         "bins": len(solution), "waste": len(solution) * 100 - sum(items),
                         "utilization_pct": round(100 * sum(items) / (len(solution) * 100), 4) if solution else 100.0,
                         "median_runtime_s_5runs": f"{statistics.median(samples):.9f}",
                         "valid": valid})
        optimum = len(outputs["Exacto"])
        for row in rows[-3:]:
            row["gap_bins_vs_exact"] = row["bins"] - optimum

path = OUT / "resultados_avance7.csv"
with path.open("w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=list(rows[0]))
    writer.writeheader(); writer.writerows(rows)

# SVG de medianas sobre semillas (tiempo en ms, con eje log para apreciar todas las escalas).
summary = {}
for n in (6, 8, 10, 12, 14, 16):
    for name in ALGORITHMS:
        values = [float(r["median_runtime_s_5runs"]) * 1000 for r in rows if r["n"] == n and r["algorithm"] == name]
        summary[(n, name)] = statistics.median(values)
W, H = 900, 500
left, top, plotw, ploth = 90, 55, 740, 340
allv = [max(v, 0.00001) for v in summary.values()]
lo, hi = min(allv), max(allv)
import math
loglo, loghi = math.log10(lo), math.log10(hi)
def y(v): return top + ploth * (loghi - math.log10(max(v, 0.00001))) / max(loghi-loglo, 1e-9)
colors = {"FFD":"#2563eb", "BFD":"#059669", "Exacto":"#dc2626"}
svg = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">',
       '<rect width="100%" height="100%" fill="white"/>',
       '<text x="450" y="28" text-anchor="middle" font-family="Arial" font-size="20" font-weight="bold">Tiempo mediano por tamaño (escala logarítmica)</text>',
       f'<path d="M{left} {top}V{top+ploth}H{left+plotw}" fill="none" stroke="#374151"/>']
for n in (6, 8, 10, 12, 14, 16):
    x = left + (n-6)/10*plotw
    svg.append(f'<path d="M{x:.1f} {top+ploth}v6" stroke="#374151"/><text x="{x:.1f}" y="{top+ploth+24}" text-anchor="middle" font-family="Arial" font-size="13">{n}</text>')
for name, color in colors.items():
    points=[]
    for n in (6,8,10,12,14,16):
        x=left+(n-6)/10*plotw; yy=y(summary[(n,name)]); points.append(f'{x:.1f},{yy:.1f}')
        svg.append(f'<circle cx="{x:.1f}" cy="{yy:.1f}" r="4" fill="{color}"/>')
    svg.append(f'<polyline points="{" ".join(points)}" fill="none" stroke="{color}" stroke-width="2.5"/>')
svg.append(f'<text x="{left+plotw/2}" y="{H-30}" text-anchor="middle" font-family="Arial" font-size="14">Cantidad de archivos (n)</text>')
svg.append(f'<text transform="translate(25 {top+ploth/2}) rotate(-90)" text-anchor="middle" font-family="Arial" font-size="14">Tiempo mediano (ms, log)</text>')
for i,(name,color) in enumerate(colors.items()):
    xx=620+(i%2)*110; yy=470
    svg.append(f'<line x1="{xx}" y1="{yy}" x2="{xx+20}" y2="{yy}" stroke="{color}" stroke-width="3"/><text x="{xx+26}" y="{yy+5}" font-family="Arial" font-size="12">{name}</text>')
svg.append('</svg>')
(OUT / "tiempos_avance7.svg").write_text("\n".join(svg), encoding="utf-8")

print(f"CSV: {path} ({len(rows)} filas)")
print(f"SVG: {OUT / 'tiempos_avance7.svg'}")
print("Resumen n, gap promedio FFD/BFD, tiempo mediano (ms):")
for n in (6,8,10,12,14,16):
    group = [r for r in rows if r["n"] == n]
    print(n, *(round(statistics.mean(r["gap_bins_vs_exact"] for r in group if r["algorithm"] == a), 3) for a in ("FFD","BFD")),
          *(round(summary[(n,a)], 6) for a in ALGORITHMS))
