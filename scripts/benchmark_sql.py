"""Compara plano/tempo com índice ausente e presente. Execute em base de teste."""
from sqlalchemy import text
from app.database import engine

QUERY = "EXPLAIN (ANALYZE, BUFFERS) SELECT id, subject, status FROM tickets WHERE customer_id = 250 ORDER BY created_at DESC LIMIT 30"
with engine.begin() as conn:
    print("\n=== SEM ÍNDICE customer_id ===")
    conn.execute(text("DROP INDEX IF EXISTS ix_tickets_customer_id"))
    for row in conn.execute(text(QUERY)):
        print(row[0])
    print("\n=== COM ÍNDICE customer_id ===")
    conn.execute(text("CREATE INDEX ix_tickets_customer_id ON tickets(customer_id)"))
    for row in conn.execute(text(QUERY)):
        print(row[0])
print("Compare Execution Time e tipo de scan. Resultados dependem da máquina e dos dados.")
