import logging
import threading
import time
from typing import TYPE_CHECKING

import certifi
from fastapi import HTTPException, status
from pymongo import MongoClient
from pymongo.database import Database

if TYPE_CHECKING:
    from fastapi import Request

from app.core.framework_indexes import ensure_framework_indexes
from app.learning_activities.repository import create_learning_activity_indexes

logger = logging.getLogger(__name__)

_reconnect_lock = threading.Lock()


def initialize_database(uri: str, database_name: str, settings=None) -> tuple[MongoClient, Database]:
    """
    Initialize MongoDB client with connection pooling and optimized settings.
    Connection pool reduces latency for concurrent requests.
    """
    from app.core.config import get_settings
    
    if settings is None:
        settings = get_settings()
    
    # Resilient timeout calculation for remote Atlas clusters
    server_timeout = max(getattr(settings, "mongodb_server_selection_timeout_ms", 15000), 15000)

    # Optimized connection settings with resilient pooling
    client = MongoClient(
        uri,
        tlsCAFile=certifi.where(),
        # Connection pool settings for better concurrency
        maxPoolSize=getattr(settings, "mongodb_max_pool_size", 50),
        minPoolSize=getattr(settings, "mongodb_min_pool_size", 5),
        maxIdleTimeMS=getattr(settings, "mongodb_max_idle_time_ms", 30000),
        # Resilient timeout settings for Atlas cloud connections
        serverSelectionTimeoutMS=server_timeout,
        connectTimeoutMS=15000,
        socketTimeoutMS=30000,
        # Performance & stability optimizations
        retryWrites=True,
        retryReads=True,
        readPreference='primaryPreferred',
    )
    database = client[database_name]

    # Verify connectivity via ping with retry
    last_err = None
    for attempt in range(1, 3):
        try:
            client.admin.command("ping")
            logger.info(
                "MongoDB connected with pool (attempt %d, serverTimeout=%dms)",
                attempt,
                server_timeout,
            )
            last_err = None
            break
        except Exception as exc:
            last_err = exc
            logger.warning("MongoDB ping attempt %d failed: %s", attempt, exc)
            time.sleep(0.5)

    if last_err is not None:
        logger.error("MongoDB connection failed after retries: %s", last_err)
        raise last_err

    # Background-safe index creation
    try:
        ensure_framework_indexes(database)
        create_learning_activity_indexes(database)
    except Exception as exc:
        logger.warning("Framework index creation notice: %s", exc)
    
    # Initialize RAG retrieval indexes (non-fatal)
    try:
        from app.ai.retrieval_indexes import ensure_retrieval_indexes, ensure_learning_material_indexes
        ensure_retrieval_indexes(database)
        ensure_learning_material_indexes(database)
    except Exception as exc:
        logger.warning("Retrieval indexes initialization notice: %s", exc)
    
    return client, database


def close_database(client: MongoClient | None) -> None:
    if client is not None:
        try:
            client.close()
        except Exception:
            pass


def get_or_reconnect_database(app) -> Database:
    """
    Safely retrieves the database instance from app state.
    If the connection was dropped or startup experienced a temporary network issue,
    this automatically re-establishes the connection on-demand so the server
    never gets stuck in a permanent 503 state.
    """
    db = getattr(app.state, "database", None)
    if db is not None:
        try:
            db.client.admin.command("ping")
            return db
        except Exception:
            logger.warning("MongoDB connection was dropped or timed out, triggering auto-reconnect...")
            try:
                db.client.close()
            except Exception:
                pass
            app.state.database = None
            app.state.database_client = None

    with _reconnect_lock:
        # Check again under lock
        db = getattr(app.state, "database", None)
        if db is not None:
            return db

        from app.core.config import get_settings
        settings = getattr(app.state, "settings", None) or get_settings()

        logger.info("Database instance is None in app.state — attempting auto-reconnect...")
        try:
            client, database = initialize_database(
                settings.mongodb_uri,
                settings.mongodb_database,
                settings,
            )
            app.state.database_client = client
            app.state.database = database
            logger.info("Successfully reconnected to MongoDB on demand")
            return database
        except Exception as exc:
            logger.error("On-demand database reconnection failed: %s", exc)
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Database is currently unavailable. Please verify network connectivity.",
            )


def get_database(request: "Request") -> Database:
    """FastAPI dependency to get database from app state with automatic reconnection"""
    return get_or_reconnect_database(request.app)
