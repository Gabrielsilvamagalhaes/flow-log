"""Fixtures compartilhadas por toda a suite de testes do flowlog.

Este arquivo e importado pelo pytest antes de qualquer modulo de teste, o que
garante que o engine de producao seja substituido pelo engine de teste antes de
qualquer import do pacote `flowlog`.
"""

from __future__ import annotations

import sys
from collections.abc import Iterator
from datetime import datetime, timedelta
from typing import Any, Callable
from unittest.mock import AsyncMock

import pytest
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

# ---------------------------------------------------------------------------
# Engine de teste
# ---------------------------------------------------------------------------
# `job_service` faz `from flowlog.server.database.connection import engine`, ou
# seja, congela a referencia no momento do import. Por isso a troca precisa
# acontecer aqui no topo do conftest (executado antes dos modulos de teste) e
# nao dentro de uma fixture.
from flowlog.server.database import connection as db_connection  # noqa: E402

# StaticPool + check_same_thread=False: mantem o mesmo banco em memoria entre
# conexoes e threads (o TestClient do FastAPI roda em outra thread).
test_engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
    echo=False,
)

db_connection.engine = test_engine

# Import dos models depois da troca do engine: registra as tabelas no metadata.
from flowlog.server.database.models.job_logs import JobLog  # noqa: E402
from flowlog.server.database.models.jobs import Job  # noqa: E402
from flowlog.shared.enums.job_enums import Environment, JobStatus, Jobtypes  # noqa: E402
from flowlog.shared.enums.log_enums import LogLevel  # noqa: E402


@pytest.fixture(autouse=True)
def _rebind_module_level_engines(monkeypatch: pytest.MonkeyPatch) -> None:
    """Reaponta qualquer modulo que ja tenha importado o engine de producao.

    Protege contra ordem de import inesperada (ex.: um modulo do flowlog
    importado por um plugin antes deste conftest).
    """
    for name, module in list(sys.modules.items()):
        if not name.startswith("flowlog"):
            continue
        if getattr(module, "engine", None) not in (None, test_engine):
            monkeypatch.setattr(module, "engine", test_engine, raising=False)


@pytest.fixture(autouse=True)
def _fresh_database() -> Iterator[None]:
    """Cria o schema antes de cada teste e derruba depois: zero vazamento de estado."""
    SQLModel.metadata.create_all(test_engine)
    yield
    SQLModel.metadata.drop_all(test_engine)


@pytest.fixture
def session() -> Iterator[Session]:
    """Sessao direta no banco de teste, para arrange/assert em testes de service."""
    with Session(test_engine) as session:
        yield session


@pytest.fixture
def client() -> Iterator[Any]:
    """TestClient da API completa (rotas + exception handlers)."""
    from fastapi.testclient import TestClient

    from flowlog.server.server import server

    with TestClient(server) as client:
        yield client


# ---------------------------------------------------------------------------
# Factories
# ---------------------------------------------------------------------------
@pytest.fixture
def make_job(session: Session) -> Callable[..., Job]:
    """Cria e persiste um Job. Sobrescreva qualquer campo via kwargs."""

    def _make_job(**overrides: Any) -> Job:
        defaults: dict[str, Any] = {
            "client_identifier": "cliente-teste",
            "job_type": Jobtypes.ETL,
            "environment": Environment.DEVELOPMENT,
            "status": JobStatus.RUNNING,
            "started_at": datetime(2026, 1, 1, 12, 0, 0),
            "ended_at": None,
            "summary": None,
        }
        job = Job(**{**defaults, **overrides})

        session.add(job)
        session.commit()
        session.refresh(job)
        return job

    return _make_job


@pytest.fixture
def make_job_log(session: Session, make_job: Callable[..., Job]) -> Callable[..., JobLog]:
    """Cria e persiste um JobLog. Sem `job_id` nos kwargs, cria um Job novo."""

    def _make_job_log(**overrides: Any) -> JobLog:
        job_id = overrides.pop("job_id", None)
        if job_id is None:
            job_id = make_job().id

        defaults: dict[str, Any] = {
            "message": "mensagem de log de teste",
            "level": LogLevel.INFO,
            "timestamp": datetime(2026, 1, 1, 12, 0, 0),
            "stack_trace": None,
            "error_code": None,
            "metadata_info": None,
        }
        job_log = JobLog(job_id=job_id, **{**defaults, **overrides})

        session.add(job_log)
        session.commit()
        session.refresh(job_log)
        return job_log

    return _make_job_log


@pytest.fixture
def finished_job(make_job: Callable[..., Job]) -> Job:
    """Job ja finalizado: usado nos casos que devem retornar 400."""
    return make_job(
        status=JobStatus.SUCCESS,
        ended_at=datetime(2026, 1, 1, 12, 0, 0) + timedelta(minutes=5),
        summary="job concluido",
    )


# ---------------------------------------------------------------------------
# Redis / BullMQ
# ---------------------------------------------------------------------------
@pytest.fixture
def fake_redis(monkeypatch: pytest.MonkeyPatch) -> AsyncMock:
    """Substitui o singleton do RedisClient por um AsyncMock.

    Evita dependencia de um Redis real nos testes unitarios. `monkeypatch`
    restaura `RedisClient._client` ao final de cada teste.
    """
    from flowlog.bullmq.client import RedisClient

    redis = AsyncMock()
    redis.ping.return_value = True

    monkeypatch.setattr(RedisClient, "_client", redis)
    return redis
