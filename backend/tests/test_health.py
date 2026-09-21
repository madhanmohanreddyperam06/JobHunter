from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_api_health():
    """
    Test GET /api/health returns HTTP 200 with status: healthy.
    """
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "job-command-center-api"


def test_database_health():
    """
    Test GET /api/health/database verifies live MySQL connection.
    """
    response = client.get("/api/health/database")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["database"] == "connected"
