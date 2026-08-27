from bson import ObjectId
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import create_app


class FakeCollection:
    def __init__(self, documents: list[dict]) -> None:
        self.documents = documents

    def find(self, query: dict, projection: dict | None = None):
        matches = [item for item in self.documents if all(item.get(key) == value for key, value in query.items())]
        return FakeCursor(matches)

    def find_one(self, query: dict):
        for item in self.documents:
            if all(item.get(key) == value for key, value in query.items()):
                return item
        return None


class FakeCursor(list):
    def sort(self, key: str, direction: int):
        return FakeCursor(sorted(self, key=lambda item: item[key], reverse=direction < 0))


class FakeDatabase:
    def __init__(self) -> None:
        role_id = ObjectId()
        competency_id = ObjectId()
        now = __import__("datetime").datetime.now(__import__("datetime").UTC)
        self.competencies = FakeCollection([{
            "_id": competency_id,
            "code": "TECH_SQL",
            "name": "SQL",
            "domain": "TECHNICAL",
            "description": "Prototype competency.",
            "level_definitions": {str(level): f"Level {level}" for level in range(1, 6)},
            "status": "active",
            "framework_status": "prototype",
            "source_type": "PROTOTYPE",
            "source_reference": None,
            "created_at": now,
            "updated_at": now,
        }])
        self.roles = FakeCollection([{
            "_id": role_id,
            "role_code": "STATISTICAL_OFFICER",
            "role_name": "Statistical Officer",
            "description": "Prototype role.",
            "status": "active",
            "framework_status": "prototype",
            "source_type": "PROTOTYPE",
            "source_reference": None,
            "created_at": now,
            "updated_at": now,
        }])
        self.role_requirements = FakeCollection([{
            "role_id": role_id,
            "competency_id": competency_id,
            "required_level": 4,
            "priority": 1,
            "importance": 1.0,
            "framework_status": "prototype",
            "created_at": now,
            "updated_at": now,
        }])

    def command(self, name: str) -> dict[str, int]:
        return {"ok": 1}


def test_framework_read_apis_return_public_ids() -> None:
    application = create_app(Settings(mongodb_uri="mongodb://test", mongodb_database="test"))
    application.state.database = FakeDatabase()
    client = TestClient(application)

    competencies = client.get("/api/v1/competencies")
    roles = client.get("/api/v1/roles")
    requirements = client.get(f"/api/v1/roles/{application.state.database.roles.documents[0]['_id']}/requirements")

    assert competencies.status_code == 200
    assert competencies.json()[0]["code"] == "TECH_SQL"
    assert "_id" not in competencies.json()[0]
    assert roles.json()[0]["role_code"] == "STATISTICAL_OFFICER"
    assert requirements.json()[0]["required_level"] == 4
    client.close()
