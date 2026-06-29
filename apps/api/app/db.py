"""Camada de banco — SQLAlchemy 2.0 + PostGIS.

O engine é criado de forma preguiçosa (lazy) para que a API suba mesmo sem banco
disponível (o endpoint de simulação é stateless). Os endpoints de CRUD exigem banco.
"""

from __future__ import annotations

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from .config import settings

_engine = None
_SessionLocal: sessionmaker[Session] | None = None


class Base(DeclarativeBase):
    pass


def get_engine():
    global _engine, _SessionLocal
    if _engine is None:
        _engine = create_engine(settings.database_url, pool_pre_ping=True, future=True)
        _SessionLocal = sessionmaker(bind=_engine, autoflush=False, expire_on_commit=False)
    return _engine


def get_session() -> Generator[Session, None, None]:
    if _SessionLocal is None:
        get_engine()
    assert _SessionLocal is not None
    session = _SessionLocal()
    try:
        yield session
    finally:
        session.close()
