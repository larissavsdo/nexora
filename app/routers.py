from fastapi import APIRouter, Depends, Header
from sqlalchemy.orm import Session
from app.database import get_db
from app.repositories import list_tickets as repository_list_tickets
from app.schemas import TicketCreate, TicketOut, TicketStatusUpdate, MessageCreate
from app.services import create_ticket, get_ticket_cached, update_ticket_status, add_message_event
from app.nosql import messages
from datetime import datetime, timezone

router = APIRouter()

@router.get("/health")
def health():
    return {"system": "NEXORA", "status": "online"}

@router.post("/tickets", response_model=TicketOut, status_code=201)
def post_ticket(data: TicketCreate, db: Session = Depends(get_db)):
    return create_ticket(db, data)

@router.get("/tickets")
def list_tickets(limit: int = 50, offset: int = 0, status: str | None = None, db: Session = Depends(get_db)):
    limit = max(1, min(limit, 200))
    rows = repository_list_tickets(db, limit=limit, offset=offset, status=status)
    return [TicketOut.model_validate(row).model_dump(mode="json") for row in rows]

@router.get("/tickets/{ticket_id}")
def get_ticket(ticket_id: int, x_cache: str | None = Header(default=None), db: Session = Depends(get_db)):
    data, cache_status = get_ticket_cached(db, ticket_id)
    return {**data, "cache": cache_status}

@router.patch("/tickets/{ticket_id}/status", response_model=TicketOut)
def patch_ticket(ticket_id: int, data: TicketStatusUpdate, db: Session = Depends(get_db)):
    return update_ticket_status(db, ticket_id, data.status)

@router.post("/tickets/{ticket_id}/messages", status_code=202)
def post_message(ticket_id: int, data: MessageCreate, db: Session = Depends(get_db)):
    return add_message_event(db, ticket_id, data.model_dump())

@router.get("/tickets/{ticket_id}/messages")
def list_messages(ticket_id: int):
    docs = messages.find({"ticket_id": ticket_id}, {"_id": 0}).sort("created_at", -1).limit(100)
    return list(docs)

# Endpoints de leitura para a interface web. Não alteram as rotas existentes.
from sqlalchemy import select, func
from app.models import Customer, Department, Agent, Ticket

@router.get('/ui/metadata')
def ui_metadata(db: Session = Depends(get_db)):
    return {
        'customers': [{'id': x.id, 'name': x.name} for x in db.scalars(select(Customer).order_by(Customer.name).limit(2000))],
        'departments': [{'id': x.id, 'name': x.name} for x in db.scalars(select(Department).order_by(Department.name))],
        'agents': [{'id': x.id, 'name': x.name, 'department_id': x.department_id} for x in db.scalars(select(Agent).order_by(Agent.name))],
    }

@router.get('/ui/stats')
def ui_stats(db: Session = Depends(get_db)):
    statuses = dict(db.execute(select(Ticket.status, func.count(Ticket.id)).group_by(Ticket.status)).all())
    return {
        'total': sum(statuses.values()),
        'open': statuses.get('open', 0),
        'in_progress': statuses.get('in_progress', 0),
        'waiting': statuses.get('waiting', 0),
        'resolved': statuses.get('resolved', 0),
        'closed': statuses.get('closed', 0),
        'customers': db.scalar(select(func.count(Customer.id))) or 0,
        'agents': db.scalar(select(func.count(Agent.id))) or 0,
    }
