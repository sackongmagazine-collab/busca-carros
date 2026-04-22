import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.database import create_tables
from app.routers import auth, search, alerts, subscriptions, dealers, admin


@asynccontextmanager
async def lifespan(app: FastAPI):
    await create_tables()
    yield


app = FastAPI(
    title="Busca Carros API",
    description="O principal buscador inteligente de carros do Brasil.",
    version="2.0.0",
    lifespan=lifespan,
)

# Em produção aceita qualquer subdomínio *.vercel.app + domínio próprio
_extra_origins = [o.strip() for o in os.getenv("ALLOWED_ORIGINS", "").split(",") if o.strip()]
ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://localhost:3000",
    "https://buscacarros.com.br",
    "https://www.buscacarros.com.br",
] + _extra_origins

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

for router in [auth.router, search.router, alerts.router, subscriptions.router, dealers.router, admin.router]:
    app.include_router(router, prefix="/api")


@app.get("/health")
async def health():
    return {"status": "ok", "version": "2.0.0"}
