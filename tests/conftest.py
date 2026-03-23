import os
import tempfile

import pytest
from fastapi.testclient import TestClient

from src.database import Database
from src.main import app, set_database


@pytest.fixture
def db():
    """Create a fresh in-memory database for each test."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        tmp_name = tmp.name
    database = Database(db_path=tmp_name)
    set_database(database)
    yield database
    os.unlink(tmp_name)


@pytest.fixture
def client(db):
    """Create a test client with a fresh database."""
    return TestClient(app)


@pytest.fixture
def sample_event():
    """Sample event payload."""
    return {
        "event_type": "order.created",
        "source": "shopify",
        "payload": {
            "order_id": "12345",
            "amount": 49.99,
            "currency": "USD",
        },
    }


@pytest.fixture
def sample_subscription():
    """Sample subscription payload."""
    return {
        "name": "Test Webhook",
        "endpoint_url": "https://example.com/webhook",
        "event_types": ["order.created"],
        "sources": ["shopify"],
        "retry_enabled": True,
        "max_retries": 3,
    }
