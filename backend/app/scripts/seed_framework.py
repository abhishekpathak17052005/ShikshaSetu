from datetime import UTC, datetime

from pymongo import MongoClient, UpdateOne
from pymongo.database import Database

from app.competencies.models import Domain, FrameworkStatus, SourceType
from app.core.config import get_settings
from app.core.database import close_database, initialize_database
from app.core.framework_indexes import ensure_framework_indexes

LEVEL_DEFINITIONS = {
    "1": "Awareness of the competency and its basic concepts.",
    "2": "Can apply basic concepts with guidance.",
    "3": "Can perform common tasks independently.",
    "4": "Can handle complex tasks and support others.",
    "5": "Can lead, design, and provide expert guidance.",
}

COMPETENCIES = (
    (Domain.STATISTICAL, "Survey Design"),
    (Domain.STATISTICAL, "Sampling"),
    (Domain.STATISTICAL, "National Accounts"),
    (Domain.STATISTICAL, "Price Statistics"),
    (Domain.STATISTICAL, "Labour Statistics"),
    (Domain.STATISTICAL, "Agricultural Statistics"),
    (Domain.STATISTICAL, "Industrial Statistics"),
    (Domain.STATISTICAL, "SDG Indicators"),
    (Domain.STATISTICAL, "Metadata Standards"),
    (Domain.STATISTICAL, "Data Quality Frameworks"),
    (Domain.TECHNICAL, "Python"),
    (Domain.TECHNICAL, "R"),
    (Domain.TECHNICAL, "SQL"),
    (Domain.TECHNICAL, "Stata"),
    (Domain.TECHNICAL, "SPSS"),
    (Domain.TECHNICAL, "SAS"),
    (Domain.TECHNICAL, "GIS"),
    (Domain.TECHNICAL, "Data Visualization"),
    (Domain.TECHNICAL, "AI/ML"),
    (Domain.TECHNICAL, "Cloud Computing"),
    (Domain.TECHNICAL, "APIs"),
    (Domain.TECHNICAL, "Open Data"),
    (Domain.DIGITAL_GOVERNANCE, "Cybersecurity"),
    (Domain.DIGITAL_GOVERNANCE, "Data Privacy"),
    (Domain.DIGITAL_GOVERNANCE, "Digital Signatures"),
    (Domain.DIGITAL_GOVERNANCE, "Government Cloud"),
    (Domain.DIGITAL_GOVERNANCE, "Digital Public Infrastructure"),
    (Domain.BEHAVIOURAL_MANAGERIAL, "Leadership"),
    (Domain.BEHAVIOURAL_MANAGERIAL, "Communication"),
    (Domain.BEHAVIOURAL_MANAGERIAL, "Project Management"),
    (Domain.BEHAVIOURAL_MANAGERIAL, "Ethics"),
    (Domain.BEHAVIOURAL_MANAGERIAL, "Decision Making"),
    (Domain.BEHAVIOURAL_MANAGERIAL, "Change Management"),
)

ROLE_REQUIREMENTS = {
    "STAT_SAMPLING": (4, 1),
    "STAT_SURVEY_DESIGN": (4, 1),
    "STAT_DATA_QUALITY_FRAMEWORKS": (4, 1),
    "TECH_PYTHON": (3, 2),
    "TECH_SQL": (3, 2),
    "TECH_DATA_VISUALIZATION": (3, 2),
    "TECH_GIS": (2, 3),
    "TECH_AI_ML": (2, 3),
}


def competency_code(domain: Domain, name: str) -> str:
    prefix = {
        Domain.STATISTICAL: "STAT",
        Domain.TECHNICAL: "TECH",
        Domain.DIGITAL_GOVERNANCE: "GOV",
        Domain.BEHAVIOURAL_MANAGERIAL: "BEH",
    }[domain]
    normalized = "_".join("".join(character if character.isalnum() else "_" for character in name.upper()).split("_"))
    return f"{prefix}_{normalized}"


def seed_framework(database: Database) -> dict[str, int]:
    ensure_framework_indexes(database)
    timestamp = datetime.now(UTC)
    competency_ids: dict[str, object] = {}

    for domain, name in COMPETENCIES:
        code = competency_code(domain, name)
        document = {
            "code": code,
            "name": name,
            "domain": domain.value,
            "description": f"Prototype competency covering {name}.",
            "level_definitions": LEVEL_DEFINITIONS,
            "status": "active",
            "framework_status": FrameworkStatus.PROTOTYPE.value,
            "source_type": SourceType.PROTOTYPE.value,
            "source_reference": "ShikshaSetu Phase 2 prototype taxonomy",
            "updated_at": timestamp,
        }
        result = database.competencies.update_one(
            {"code": code},
            {"$set": document, "$setOnInsert": {"created_at": timestamp}},
            upsert=True,
        )
        item = database.competencies.find_one({"code": code}, {"_id": 1})
        competency_ids[code] = item["_id"]

    role_document = {
        "role_code": "STATISTICAL_OFFICER",
        "role_name": "Statistical Officer",
        "description": "Prototype role for demonstrating competency requirements.",
        "status": "active",
        "framework_status": FrameworkStatus.PROTOTYPE.value,
        "source_type": SourceType.PROTOTYPE.value,
        "source_reference": "ShikshaSetu Phase 2 prototype role framework",
        "updated_at": timestamp,
    }
    database.roles.update_one(
        {"role_code": role_document["role_code"]},
        {"$set": role_document, "$setOnInsert": {"created_at": timestamp}},
        upsert=True,
    )
    role = database.roles.find_one({"role_code": "STATISTICAL_OFFICER"}, {"_id": 1})

    operations = []
    for code, (required_level, priority) in ROLE_REQUIREMENTS.items():
        operations.append(
            UpdateOne(
                {"role_id": role["_id"], "competency_id": competency_ids[code]},
                {
                    "$set": {
                        "required_level": required_level,
                        "priority": priority,
                        "importance": 1.0 if priority == 1 else 0.75 if priority == 2 else 0.5,
                        "framework_status": FrameworkStatus.PROTOTYPE.value,
                        "updated_at": timestamp,
                    },
                    "$setOnInsert": {"created_at": timestamp},
                },
                upsert=True,
            )
        )
    if operations:
        database.role_requirements.bulk_write(operations)

    return {
        "competencies": database.competencies.count_documents({}),
        "domains": len({domain for domain, _ in COMPETENCIES}),
        "roles": database.roles.count_documents({}),
        "role_requirements": database.role_requirements.count_documents({"role_id": role["_id"]}),
    }


def main() -> None:
    settings = get_settings()
    client: MongoClient | None = None
    try:
        client, database = initialize_database(settings.mongodb_uri, settings.mongodb_database)
        print(seed_framework(database))
    finally:
        close_database(client)


if __name__ == "__main__":
    main()
