"""Benchmark HTTP sequencial do Cache-Aside; não modifica chamados."""
import argparse
import json
import math
import statistics
import time
import urllib.request
from pathlib import Path
from app.nosql import redis_client


def percentile(values, fraction):
    ordered = sorted(values)
    pos = (len(ordered) - 1) * fraction
    lo, hi = math.floor(pos), math.ceil(pos)
    return ordered[lo] + (ordered[hi] - ordered[lo]) * (pos - lo)

def request(url):
    started = time.perf_counter()
    with urllib.request.urlopen(url, timeout=15) as response:
        payload = json.load(response)
    return (time.perf_counter() - started) * 1000, payload.get('cache')

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--samples', type=int, default=20)
    parser.add_argument('--ticket-id', type=int, default=2)
    parser.add_argument('--url', default='http://localhost:8000')
    parser.add_argument('--output', default='results/benchmark_cache.json')
    args = parser.parse_args()
    if args.samples < 5:
        parser.error('Use --samples >= 5')
    url = args.url.rstrip('/') + f'/tickets/{args.ticket_id}'
    key = f'ticket:{args.ticket_id}'
    # Aquecimento de transporte/conexões antes das amostras.
    request(url)
    samples = {'MISS': [], 'HIT': []}
    for _ in range(args.samples):
        # Exclui apenas a chave de cache deste chamado; NÃO altera PostgreSQL/MongoDB.
        redis_client.delete(key)
        elapsed, state = request(url)
        if state != 'MISS':
            raise RuntimeError(f'Esperado MISS, recebido {state!r}. Verifique acesso concorrente ao chamado.')
        samples['MISS'].append(elapsed)
        elapsed, state = request(url)
        if state != 'HIT':
            raise RuntimeError(f'Esperado HIT, recebido {state!r}. Verifique TTL e Redis.')
        samples['HIT'].append(elapsed)
    summary = {name: {'amostras': len(v), 'media_ms': statistics.mean(v), 'mediana_ms': statistics.median(v), 'p95_ms': percentile(v, .95), 'min_ms': min(v), 'max_ms': max(v)} for name, v in samples.items()}
    summary['razao_mediana_miss_sobre_hit'] = summary['MISS']['mediana_ms'] / summary['HIT']['mediana_ms'] if summary['HIT']['mediana_ms'] else None
    result = {'metodologia': 'Requisições HTTP sequenciais; remove somente a chave Redis do ticket antes de cada MISS; HIT imediatamente após; tempo ponta a ponta medido no cliente; sem concorrência.', 'url': url, 'resumo': summary, 'amostras_ms': samples}
    target = Path(args.output)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding='utf-8')
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    print(f'Arquivo gerado: {target}')

if __name__ == '__main__':
    main()
