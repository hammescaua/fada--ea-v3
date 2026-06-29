"""Aplicação FastAPI — API do Gêmeo Digital da soja.

O endpoint de simulação é stateless (funciona sem banco). Os endpoints de CRUD de
fazendas/talhões exigem PostGIS. A app sobe normalmente mesmo sem banco disponível.
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .routers import farms, learning, sensors, simulation

app = FastAPI(
    title="FADA EA v3 — Gêmeo Digital da Soja",
    description="Motor agronômico determinístico + simulação de safra (Noroeste do RS).",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(simulation.router, prefix="/api")
app.include_router(farms.router, prefix="/api")
app.include_router(learning.router, prefix="/api")
app.include_router(sensors.router, prefix="/api")


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok", "service": "fada-api", "version": "0.1.0"}
