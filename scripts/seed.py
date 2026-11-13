"""Popula a base com clientes, agentes e no mínimo 100 mil chamados."""
import random
from datetime import datetime, timedelta, timezone
from faker import Faker
from sqlalchemy import select, func
from app.database import SessionLocal
from app.models import Customer, Agent, Department, Ticket

fake = Faker("pt_BR")
TOTAL_TICKETS = 100_000
BATCH_SIZE = 5_000

def main():
    random.seed(42)
    with SessionLocal() as db:
        departments = db.scalars(select(Department)).all()
        if not departments:
            departments = [Department(name=n) for n in ["Comercial", "Suporte", "Financeiro", "Implantação", "Relacionamento"]]
            db.add_all(departments); db.commit()
            departments = db.scalars(select(Department)).all()
        if db.scalar(select(func.count(Customer.id))) == 0:
            customers = [Customer(name=fake.name(), email=f"cliente{i}@exemplo.test") for i in range(1,1001)]
            db.add_all(customers); db.commit()
        
        if db.scalar(select(func.count(Agent.id))) == 0:
            nomes_colaboradores = [
                "Larissa Oliveira",
                "Rodrigo Machado",
                "Maria Eduarda Matos",
                "Dr. Jario Jose",
                "Edivania Oliveira",
                "Igor Pereira",
                "Mateus Marques",
                "Regina Santos",
                "Wilma Maria",
                "Carlos Miguel",
                "Brendo Rocha",
                "Pedro Levy",
                "Lilian Santana",
                "Allana Duarte",
                "Anne Silva",
                "Thiago Brandao",
                "Roberta Santos",
                "Pedro Gustavo",
                "Marcelo Araújo",
                "Andreia Oliveira",
                "Lucy Matos",
                "Thalita Lima",
                "Paulo Victor",
                "Edna Vasconcelos",
                "Luiz Fernando",
                "Witalo Santos",
                "Felipe Carvalho",
                "Carolina Dantas",
                "Fernanda Cardoso",
                "Junior Silva",
            ]

            agents = [
                Agent(
                    name=nome,
                    email=f"agente{i}@nexora.test",
                    department_id=random.choice(departments).id
                )
                for i, nome in enumerate(nomes_colaboradores, start=1)
            ]

            db.add_all(agents)
            db.commit()

        customers = db.scalars(select(Customer)).all()
        agents = db.scalars(select(Agent)).all()
        existing = db.scalar(select(func.count(Ticket.id))) or 0
        remaining = max(0, TOTAL_TICKETS-existing)
        print(f"Chamados existentes: {existing}; serão criados: {remaining}")
        statuses = ["open", "in_progress", "waiting", "resolved", "closed"]
        priorities = ["low", "normal", "high", "urgent"]
        for start in range(0, remaining, BATCH_SIZE):
            batch=[]
            for _ in range(min(BATCH_SIZE, remaining-start)):
                created = datetime.now(timezone.utc)-timedelta(days=random.randint(0,730), hours=random.randint(0,23))
                batch.append(Ticket(subject=fake.sentence(nb_words=6)[:220], description=fake.text(max_nb_chars=180),
                    status=random.choice(statuses), priority=random.choice(priorities),
                    customer_id=random.choice(customers).id, agent_id=random.choice(agents).id,
                    department_id=random.choice(departments).id, created_at=created, updated_at=created))
            db.add_all(batch); db.commit()
            print(f"Progresso: {min(start+BATCH_SIZE, remaining)}/{remaining}")
    print("Carga finalizada. Confira com SELECT COUNT(*) FROM tickets;")

if __name__ == "__main__": main()
