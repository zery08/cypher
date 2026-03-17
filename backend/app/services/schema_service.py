import time

from app.schemas import SchemaSnapshot
from app.services.neo4j_service import Neo4jService


class SchemaService:
    def __init__(self, neo4j_service: Neo4jService, ttl_seconds: int = 60):
        self.neo4j_service = neo4j_service
        self.ttl_seconds = ttl_seconds
        self._cached_schema: SchemaSnapshot | None = None
        self._cached_at = 0.0

    async def get_schema_snapshot(self) -> SchemaSnapshot:
        now = time.monotonic()
        if self._cached_schema and now - self._cached_at < self.ttl_seconds:
            return self._cached_schema

        schema = await self.neo4j_service.get_schema_snapshot()
        self._cached_schema = schema
        self._cached_at = now
        return schema
