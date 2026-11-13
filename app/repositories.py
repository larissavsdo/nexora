"""Camada de acesso aos dados relacionais (Repository Pattern)."""
from sqlalchemy import select, desc
from sqlalchemy.orm import Session
from app.models import Ticket, Customer, Agent, Department, OutboxEvent


def get_customer(db: Session, customer_id: int):
    return db.get(Customer, customer_id)


def get_department(db: Session, department_id: int):
    return db.get(Department, department_id)


def get_agent(db: Session, agent_id: int):
    return db.get(Agent, agent_id)


def get_ticket(db: Session, ticket_id: int):
    return db.get(Ticket, ticket_id)


def add_ticket(db: Session, ticket: Ticket):
    db.add(ticket)
    db.flush()
    return ticket


def add_outbox_event(db: Session, event: OutboxEvent):
    db.add(event)


def list_tickets(db: Session, limit: int = 50, offset: int = 0, status: str | None = None):
    query = select(Ticket).order_by(desc(Ticket.created_at)).offset(offset).limit(limit)
    if status:
        query = query.where(Ticket.status == status)
    return db.scalars(query).all()
