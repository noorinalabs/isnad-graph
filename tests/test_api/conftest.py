"""API test fixtures."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def mock_neo4j() -> MagicMock:
    """Mock Neo4jClient for API tests."""
    client = MagicMock()
    client.execute_read.return_value = []
    client.execute_write.return_value = []
    return client


@pytest.fixture
def app(mock_neo4j: MagicMock) -> object:
    """FastAPI app with mocked Neo4j (lifespan disabled)."""
    from src.api.app import create_app

    app = create_app()
    app.state.neo4j = mock_neo4j
    return app


@pytest.fixture
def client(app: object) -> TestClient:
    """Test client."""
    return TestClient(app)  # type: ignore[arg-type]
