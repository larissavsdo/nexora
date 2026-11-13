import json
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.models import Ticket, OutboxEvent
from app.repositories import get_customer, get_department, get_agent, get_ticket, add_ticket, add_outbox_event
from app.schemas import TicketCreate
from app.nosql import redis_client
from app.config import settings

VALID_PRIORITIES = {"low", "normal", "high", "urgent"}

def create_ticket(db: Session, data: TicketCreate):
    if data.priority not in VALID_PRIORITIES:
        raise HTTPException(422, "Prioridade inválida.")
    if not get_customer(db, data.customer_id):
        raise HTTPException(404, "Cliente não encontrado.")
    if not get_department(db, data.department_id):
        raise HTTPException(404, "Departamento não encontrado.")
    if data.agent_id and not get_agent(db, data.agent_id):
        raise HTTPException(404, "Atendente não encontrado.")
    try:
        ticket = Ticket(**data.model_dump())
        add_ticket(db, ticket)
        event = OutboxEvent(event_type="ticket.created", aggregate_id=ticket.id,
            payload={"ticket_id": ticket.id, "subject": ticket.subject,
                     "customer_id": ticket.customer_id, "status": ticket.status,
                     "created_at": datetime.now(timezone.utc).isoformat()})
        add_outbox_event(db, event)
        db.commit()
        db.refresh(ticket)
        return ticket
    except Exception:
        db.rollback()
        raise

def get_ticket_cached(db: Session, ticket_id: int):
    key = f"ticket:{ticket_id}"
    cached = redis_client.get(key)
    if cached:
        return json.loads(cached), "HIT"
    ticket = get_ticket(db, ticket_id)
    if not ticket:
        raise HTTPException(404, "Chamado não encontrado.")
    data = {"id": ticket.id, "subject": ticket.subject, "description": ticket.description,
            "status": ticket.status, "priority": ticket.priority,
            "customer_id": ticket.customer_id, "agent_id": ticket.agent_id,
            "department_id": ticket.department_id,
            "created_at": ticket.created_at.isoformat(), "updated_at": ticket.updated_at.isoformat()}
    redis_client.setex(key, settings.cache_ttl_seconds, json.dumps(data))
    return data, "MISS"

def update_ticket_status(db: Session, ticket_id: int, status: str):
    ticket = get_ticket(db, ticket_id)
    if not ticket:
        raise HTTPException(404, "Chamado não encontrado.")
    ticket.status = status
    ticket.updated_at = datetime.now(timezone.utc)
    add_outbox_event(db, OutboxEvent(event_type="ticket.status_updated", aggregate_id=ticket.id,
        payload={"ticket_id": ticket.id, "status": status, "updated_at": ticket.updated_at.isoformat()}))
    db.commit()
    db.refresh(ticket)
    redis_client.delete(f"ticket:{ticket_id}")
    return ticket

def add_message_event(db: Session, ticket_id: int, message: dict):
    if not get_ticket(db, ticket_id):
        raise HTTPException(404, "Chamado não encontrado.")
    payload = {"ticket_id": ticket_id, **message, "created_at": datetime.now(timezone.utc).isoformat()}
    db.add(OutboxEvent(event_type="message.created", aggregate_id=ticket_id, payload=payload))
    db.commit()
    redis_client.delete(f"ticket:{ticket_id}")
    return {"status": "accepted_for_sync", "ticket_id": ticket_id}
