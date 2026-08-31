from pymongo import MongoClient
from pymongo.database import Database

from app.core.framework_indexes import ensure_framework_indexes
from app.learning_activities.repository import create_learning_activity_indexes


def initialize_database(uri: str, database_name: str) -> tuple[MongoClient, Database]:
    client = MongoClient(uri, serverSelectionTimeoutMS=2000)
    database = client[database_name]
    ensure_framework_indexes(database)
    create_learning_activity_indexes(database)
    return client, database


def close_database(client: MongoClient | None) -> None:
    if client is not None:
        client.close()
