"""Mede tempo de resposta de chamadas HTTP; API deve estar em execução."""
import time, statistics, urllib.request
URL = "http://localhost:8000/health"
SAMPLES = 100
latencies=[]
for _ in range(SAMPLES):
    start=time.perf_counter()
    with urllib.request.urlopen(URL) as response: response.read()
    latencies.append((time.perf_counter()-start)*1000)
ordered=sorted(latencies)
p95=ordered[int(0.95*(len(ordered)-1))]
print(f"Amostras: {SAMPLES}; média: {statistics.mean(latencies):.2f} ms; p95: {p95:.2f} ms; throughput aproximado: {1000/statistics.mean(latencies):.2f} req/s (sequencial)")
