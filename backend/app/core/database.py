import logging
import time

from pymongo import MongoClient
from pymongo.database import Database

from app.core.framework_indexes import ensure_framework_indexes
from app.learning_activities.repository import create_learning_activity_indexes

logger = logging.getLogger(__name__)


def initialize_database(uri: str, database_name: str) -> tuple[MongoClient, Database]:
    """
    Initialize MongoDB client with retry logic to handle Atlas cold-start latency.
    Atlas free-tier clusters can take 10–30 s to wake from paused state.
    """
    # Use generous timeouts; Atlas SRV DNS + TLS handshake can be slow on first connect
    client = MongoClient(
        uri,
        serverSelectionTimeoutMS=30000,
        connectTimeoutMS=20000,
        socketTimeoutMS=30000,
    )
    database = client[database_name]

    # Retry ping up to 3 times to tolerate Atlas cold starts
    last_error: Exception | None = None
    for attempt in range(1, 4):
        try:
            client.admin.command("ping")
            logger.info("MongoDB ping succeeded (attempt %d)", attempt)
            break
        except Exception as exc:
            last_error = exc
            if attempt < 3:
                logger.warning(
                    "MongoDB ping attempt %d failed, retrying in 5 s: %s", attempt, exc
                )
                time.sleep(5)
            else:
                raise

    ensure_framework_indexes(database)
    create_learning_activity_indexes(database)
    return client, database


def close_database(client: MongoClient | None) -> None:
    if client is not None:
        client.close()
