"""Shared test setup.

Every test run creates a fresh `<db>_test` database next to the dev database,
migrates it to the latest version, and drops it at the end. Dev data is never
touched.
"""

import time
from collections.abc import Iterator
from pathlib import Path

import jwt
import pytest
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import Engine, create_engine, text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session

from alembic import command
from app.config import settings
from app.db import get_session
from app.main import app

API_DIR = Path(__file__).resolve().parent.parent

DEV_URL = make_url(settings.database_url)
TEST_DB_NAME = f"{DEV_URL.database}_test"
TEST_URL = DEV_URL.set(database=TEST_DB_NAME)


@pytest.fixture(scope="session")
def alembic_cfg() -> Config:
    cfg = Config(str(API_DIR / "alembic.ini"))
    # alembic.ini is read by configparser, where "%" is special, so escape it.
    url = TEST_URL.render_as_string(hide_password=False).replace("%", "%%")
    cfg.set_main_option("sqlalchemy.url", url)
    return cfg


@pytest.fixture(scope="session")
def engine(alembic_cfg: Config) -> Iterator[Engine]:
    # Connect to the built-in "postgres" database to create/drop the test database.
    admin = create_engine(DEV_URL.set(database="postgres"), isolation_level="AUTOCOMMIT")
    with admin.connect() as conn:
        conn.execute(text(f'DROP DATABASE IF EXISTS "{TEST_DB_NAME}" WITH (FORCE)'))
        conn.execute(text(f'CREATE DATABASE "{TEST_DB_NAME}"'))

    command.upgrade(alembic_cfg, "head")
    test_engine = create_engine(TEST_URL)
    yield test_engine

    test_engine.dispose()
    with admin.connect() as conn:
        conn.execute(text(f'DROP DATABASE IF EXISTS "{TEST_DB_NAME}" WITH (FORCE)'))
    admin.dispose()


@pytest.fixture
def db(engine: Engine) -> Iterator[Session]:
    """A session whose changes are rolled back when the test ends."""
    connection = engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection, join_transaction_mode="create_savepoint")
    yield session
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def client(db: Session) -> Iterator[TestClient]:
    """HTTP client for the app, using the test session instead of the dev database."""
    app.dependency_overrides[get_session] = lambda: db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def make_token():
    def _make(
        sub: str = "sub-a",
        email: str = "a@example.com",
        *,
        aud: str = settings.jwt_audience,
        exp_in: int = 300,
        secret: str = settings.jwt_secret,
    ) -> str:
        now = int(time.time())
        payload = {"sub": sub, "email": email, "aud": aud, "iat": now, "exp": now + exp_in}
        return jwt.encode(payload, secret, algorithm="HS256")

    return _make


@pytest.fixture
def headers_for(make_token):
    def _headers(sub: str = "sub-a") -> dict[str, str]:
        token = make_token(sub=sub, email=f"{sub}@example.com")
        return {"Authorization": f"Bearer {token}"}

    return _headers
