from fastapi.testclient import TestClient
from pymongo.errors import PyMongoError

from app.core.config import Settings
from app.main import create_app


class ReachableDatabase:
    def command(self, name: str) -> dict[str, int]:
        assert name == "ping"
        return {"ok": 1}


class UnreachableDatabase:
    def command(self, name: str) -> None:
        raise PyMongoError("database is unavailable")


def make_client(database: object) -> TestClient:
    application = create_app(Settings(mongodb_uri="mongodb://test", mongodb_database="test"))
    client = TestClient(application)
    application.state.database = database
    return client


def test_health_returns_service_and_database_status() -> None:
    client = make_client(ReachableDatabase())

    response = client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "ShikshaSetu Backend",
        "database": "connected",
    }
    client.close()


def test_health_reports_database_failure() -> None:
    client = make_client(UnreachableDatabase())

    response = client.get("/api/v1/health")

    assert response.status_code == 503
    assert response.json() == {"detail": "Database is unavailable"}
    client.close()
