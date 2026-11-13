import time
from datetime import datetime, timezone
from sqlalchemy import select
from app.database import SessionLocal
from app.models import OutboxEvent
from app.nosql import messages
from app.config import settings

def process_batch():
    processed_count = 0
    with SessionLocal() as db:
        # Lock evita que dois workers processem o mesmo evento ao mesmo tempo.
        events = db.scalars(select(OutboxEvent).where(OutboxEvent.processed.is_(False))
            .order_by(OutboxEvent.id).with_for_update(skip_locked=True).limit(100)).all()
        for event in events:
            try:
                doc = {"event_id": event.id, "event_type": event.event_type,
                       "ticket_id": event.aggregate_id, **event.payload}
                # event_id é chave idempotente: reprocessar não cria duplicata.
                messages.update_one({"event_id": event.id}, {"$setOnInsert": doc}, upsert=True)
                event.processed = True
                event.processed_at = datetime.now(timezone.utc)
                processed_count += 1
            except Exception:
                event.attempts += 1
        db.commit()
    return processed_count

if __name__ == "__main__":
    print("NEXORA Outbox Worker iniciado")
    while True:
        try:
            count = process_batch()
            if count:
                print(f"Eventos sincronizados: {count}")
        except Exception as exc:
            print(f"Falha no worker: {exc}")
        time.sleep(settings.outbox_poll_seconds)
