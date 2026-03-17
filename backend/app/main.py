from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router
from app.core.config import Settings, get_settings
from app.services.llm_service import LLMService
from app.services.neo4j_service import Neo4jService
from app.services.orchestrator import ChatOrchestrator
from app.services.schema_service import SchemaService


def create_app(
    settings: Settings | None = None,
    *,
    neo4j_service: Neo4jService | None = None,
    llm_service: LLMService | None = None,
    schema_service: SchemaService | None = None,
    orchestrator: ChatOrchestrator | None = None,
) -> FastAPI:
    settings = settings or get_settings()
    neo4j_service = neo4j_service or Neo4jService(settings)
    llm_service = llm_service or LLMService(settings)
    schema_service = schema_service or SchemaService(
        neo4j_service,
        ttl_seconds=settings.schema_cache_ttl_seconds,
    )
    orchestrator = orchestrator or ChatOrchestrator(
        llm_service=llm_service,
        neo4j_service=neo4j_service,
        schema_service=schema_service,
    )

    @asynccontextmanager
    async def lifespan(app_instance: FastAPI):
        yield
        await app_instance.state.neo4j_service.close()

    app = FastAPI(title=settings.app_name, lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_methods=["*"],
        allow_headers=["*"],
        allow_credentials=False,
    )

    app.state.settings = settings
    app.state.neo4j_service = neo4j_service
    app.state.llm_service = llm_service
    app.state.schema_service = schema_service
    app.state.orchestrator = orchestrator
    app.include_router(router, prefix="/api")

    return app


app = create_app()
