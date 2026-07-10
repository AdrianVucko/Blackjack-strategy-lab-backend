"""API test fixtures: isolate the database to a temp file before app import."""

from __future__ import annotations

import os
import tempfile
from collections.abc import Iterator

import pytest

_db_fd, _db_path = tempfile.mkstemp(suffix=".db")
os.close(_db_fd)
os.environ["DATABASE_URL"] = f"sqlite:///{_db_path}"


@pytest.fixture(scope="session")
def client() -> Iterator[object]:
    from fastapi.testclient import TestClient

    from blackjack.main import app

    with TestClient(app) as test_client:
        yield test_client

    os.unlink(_db_path)
