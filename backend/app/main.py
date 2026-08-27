import logging
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.api.health import router as health_router
from app.ai.router import router as ai_router
from app.auth.router import router as auth_router
from app.assessments.router import router as assessments_router
from app.competencies.router import router as competencies_router
from app.core.config import Settings, get_settings
from app.core.database import close_database, initialize_database
from app.roles.router import router as roles_router
from app.skill_gaps.router import router as skill_gaps_router
from app.users.router import router as users_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


def create_app(settings: Settings | None = None) -> FastAPI:
    app_settings = settings or get_settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        client = None
        try:
            client, database = initialize_database(
                app_settings.mongodb_uri,
                app_settings.mongodb_database,
            )
            app.state.database_client = client
            app.state.database = database
            logger.info("MongoDB client initialized")
        except Exception:
            logger.exception("MongoDB client initialization failed")
            close_database(client)
            app.state.database_client = None
            app.state.database = None

        logger.info("Starting %s", app_settings.app_name)
        yield
        close_database(getattr(app.state, "database_client", None))
        logger.info("Application shutdown complete")

    application = FastAPI(
        title=app_settings.app_name,
        description="Competency framework foundation for ShikshaSetu",
        version="0.3.0",
        debug=app_settings.debug,
        lifespan=lifespan,
    )
    application.state.settings = app_settings
    application.include_router(health_router, prefix=app_settings.api_prefix)
    application.include_router(auth_router, prefix=app_settings.api_prefix)
    application.include_router(assessments_router, prefix=app_settings.api_prefix)
    application.include_router(competencies_router, prefix=app_settings.api_prefix)
    application.include_router(roles_router, prefix=app_settings.api_prefix)
    application.include_router(skill_gaps_router, prefix=app_settings.api_prefix)
    application.include_router(users_router, prefix=app_settings.api_prefix)
    application.include_router(ai_router, prefix=app_settings.api_prefix)

    @application.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.exception("Unhandled application error: %s", exc)
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error"},
        )

    return application


app = create_app()
