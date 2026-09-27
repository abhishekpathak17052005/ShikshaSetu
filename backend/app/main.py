import logging
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.health import router as health_router
from app.auth.router import router as auth_router
from app.ai.router import router as learning_materials_router
from app.assessments.router import router as assessments_router
from app.capability_assessments.router import router as capability_assessments_router
from app.competencies.router import router as competencies_router
from app.core.config import Settings, get_settings
from app.core.database import close_database, initialize_database
from app.learning_activities.router import router as learning_activities_router
from app.learning_resources.router import router as recommendations_router
from app.quizzes.router import router as quizzes_router
from app.roles.router import router as roles_router
from app.skill_gaps.router import router as skill_gaps_router
from app.admin.router import router as admin_router
from app.trainer.router import router as trainer_router
from app.users.router import router as users_router
from app.igot.router import router as igot_router
from app.assistant.router import router as assistant_router
from app.adaptive_assessments.router import router as adaptive_assessments_router
from app.talent.router import router as talent_router
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from app.core.limiter import limiter

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

            try:
                from app.talent.repository import ensure_talent_indexes
                ensure_talent_indexes(database)
            except Exception:
                logger.exception("Talent index creation failed (non-fatal)")

            # Build in-memory embedding indexes — LAZY background task,
            # does NOT block application ready state.
            # If the corpus grows large this will run in the background only.
            try:
                from app.rag.embedding_index import EmbeddingIndexManager
                import threading

                def _lazy_rag_init(db):
                    try:
                        indexed = EmbeddingIndexManager.get_instance().load_all_ready_materials(db)
                        logger.info("RAG embedding index: loaded %d material(s) (background)", indexed)
                    except Exception:
                        logger.exception("RAG embedding index background load failed (non-fatal)")

                t = threading.Thread(target=_lazy_rag_init, args=(database,), daemon=True, name="rag-index-loader")
                t.start()
                logger.info("RAG embedding index: lazy background load started")
            except Exception:
                logger.exception("RAG embedding index startup init failed (non-fatal)")

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
        version="0.3.1",
        debug=app_settings.debug,
        lifespan=lifespan,
    )
    is_production = app_settings.app_env.lower() in ("production", "prod")
    cors_kwargs = {
        "allow_origins": app_settings.cors_allowed_origins,
        "allow_credentials": True,
        "allow_methods": ["*"],
        "allow_headers": ["*"],
    }
    if not is_production:
        cors_kwargs["allow_origin_regex"] = r"https://.*\.vercel\.app|https://.*\.onrender\.com"

    application.add_middleware(
        CORSMiddleware,
        **cors_kwargs,
    )
    application.add_middleware(SlowAPIMiddleware)

    @application.middleware("http")
    async def add_security_headers(request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        return response

    application.state.settings = app_settings
    application.state.limiter = limiter

    @application.exception_handler(RateLimitExceeded)
    async def rate_limit_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
        return JSONResponse(
            status_code=429,
            content={"detail": "Too many requests. Please slow down and try again later."},
            headers={"Retry-After": "60"},
        )

    @application.get("/", include_in_schema=False)
    @application.head("/", include_in_schema=False)
    async def root_health_check():
        return {"status": "ok", "app": app_settings.app_name}

    application.include_router(health_router, prefix=app_settings.api_prefix)
    application.include_router(auth_router, prefix=app_settings.api_prefix)
    application.include_router(learning_materials_router, prefix=app_settings.api_prefix)
    application.include_router(capability_assessments_router)
    application.include_router(assessments_router, prefix=app_settings.api_prefix)
    application.include_router(competencies_router, prefix=app_settings.api_prefix)
    application.include_router(learning_activities_router, prefix=app_settings.api_prefix)
    application.include_router(roles_router, prefix=app_settings.api_prefix)
    application.include_router(recommendations_router, prefix=app_settings.api_prefix)
    application.include_router(quizzes_router, prefix=app_settings.api_prefix)
    application.include_router(skill_gaps_router, prefix=app_settings.api_prefix)
    application.include_router(trainer_router, prefix=app_settings.api_prefix)
    application.include_router(admin_router, prefix=app_settings.api_prefix)
    application.include_router(users_router, prefix=app_settings.api_prefix)
    application.include_router(igot_router, prefix=app_settings.api_prefix)
    application.include_router(assistant_router, prefix=app_settings.api_prefix)
    application.include_router(adaptive_assessments_router, prefix=app_settings.api_prefix)
    application.include_router(talent_router, prefix=app_settings.api_prefix)

    @application.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.exception("Unhandled application error: %s", exc)
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error"},
        )

    return application


app = create_app()
