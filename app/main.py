from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from app.config import settings
from app.database import Base, engine
from app import models
from app.routers import router
from app.nosql import mongo_client, redis_client

app = FastAPI(title=settings.app_name,
    description="Plataforma omnichannel de gerenciamento de atendimentos e relacionamento com clientes.",
    version="1.0.0")
app.include_router(router)

@app.on_event("startup")
def startup():
    Base.metadata.create_all(bind=engine)
    mongo_client.admin.command("ping")
    redis_client.ping()

@app.get("/")
def home():
    return {"sistema": "NEXORA", "mensagem": "Bem-vindo ao NEXORA!", "status": "online"}

# Interface SaaS de demonstração. A API REST permanece disponível em /docs.
STATIC_DIR = Path(__file__).resolve().parent / "static"
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

@app.get("/app", include_in_schema=False)
def web_app():
    return FileResponse(STATIC_DIR / "index.html")
