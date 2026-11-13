"""Benchmark repetido e não destrutivo do PostgreSQL (executar dentro do container api)."""
import argparse
import json
import math
import statistics
import time
from pathlib import Path
from sqlalchemy import text
from app.database import engine

QUERY = "SELECT id, subject, status, created_at FROM tickets WHERE status = 'open' ORDER BY created_at DESC LIMIT 20"
SETTINGS_OFF = ("SET LOCAL enable_indexscan = off", "SET LOCAL enable_bitmapscan = off", "SET LOCAL enable_indexonlyscan = off")

def percentile(values, fraction):
    ordered = sorted(values)
    position = (len(ordered) - 1) * fraction
    low = math.floor(position)
    high = math.ceil(position)
    return ordered[low] + (ordered[high] - ordered[low]) * (position - low)

def measure(conn, indexed):
    # Transação isolada para que SET LOCAL nunca afete outras consultas.
    with conn.begin():
        if not indexed:
            for statement in SETTINGS_OFF:
                conn.execute(text(statement))
        started = time.perf_counter()
        rows = conn.execute(text(QUERY)).all()
        elapsed_ms = (time.perf_counter() - started) * 1000
    assert len(rows) == 20, f"Esperados 20 registros, recebidos {len(rows)}"
    return elapsed_ms

def plan(conn, indexed):
    with conn.begin():
        if not indexed:
            for statement in SETTINGS_OFF:
                conn.execute(text(statement))
        return [row[0] for row in conn.execute(text("EXPLAIN (ANALYZE, BUFFERS) " + QUERY))]

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--samples', type=int, default=20)
    parser.add_argument('--warmup', type=int, default=3)
    parser.add_argument('--output', default='results/benchmark_sql.json')
    args = parser.parse_args()
    if args.samples < 5 or args.warmup < 0:
        parser.error('Use --samples >= 5 e --warmup >= 0')
    samples = {'com_indice': [], 'sem_indice': []}
    with engine.connect() as conn:
        with conn.begin():
            count = conn.scalar(text('SELECT COUNT(*) FROM tickets'))
        if count < 100000:
            raise RuntimeError(f'Base com {count} chamados; esperado pelo menos 100000')
        for i in range(args.warmup):
            measure(conn, True)
            measure(conn, False)
        # Alternar a ordem reduz viés por aquecimento e carga do sistema.
        for i in range(args.samples):
            order = (True, False) if i % 2 == 0 else (False, True)
            for indexed in order:
                samples['com_indice' if indexed else 'sem_indice'].append(measure(conn, indexed))
        plans = {'com_indice': plan(conn, True), 'sem_indice': plan(conn, False)}
    summary = {name: {'amostras': len(values), 'media_ms': statistics.mean(values), 'mediana_ms': statistics.median(values), 'p95_ms': percentile(values, .95), 'min_ms': min(values), 'max_ms': max(values)} for name, values in samples.items()}
    summary['razao_mediana_sem_sobre_com'] = summary['sem_indice']['mediana_ms'] / summary['com_indice']['mediana_ms'] if summary['com_indice']['mediana_ms'] else None
    result = {'metodologia': 'Consultas sequenciais em uma conexão; transação com SET LOCAL para desativar índices, sem remover índices; tempo medido no cliente SQLAlchemy.', 'total_tickets': count, 'consulta': QUERY, 'resumo': summary, 'amostras_ms': samples, 'planos': plans}
    target = Path(args.output)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding='utf-8')
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    print(f'Arquivo gerado: {target}')

if __name__ == '__main__':
    main()
