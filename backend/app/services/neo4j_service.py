from typing import Any

import anyio
from neo4j import GraphDatabase

from app.core.config import Settings
from app.schemas import SchemaSnapshot


class Neo4jService:
    def __init__(self, settings: Settings):
        self.settings = settings
        self._driver = None

    @property
    def is_configured(self) -> bool:
        return self.settings.neo4j_configured

    def _get_driver(self):
        if not self.is_configured:
            raise RuntimeError("Neo4j is not configured.")
        if self._driver is None:
            self._driver = GraphDatabase.driver(
                self.settings.neo4j_uri,
                auth=(self.settings.neo4j_username, self.settings.neo4j_password),
            )
        return self._driver

    async def health_check(self) -> dict[str, Any]:
        if not self.is_configured:
            return {"configured": False, "reachable": False, "database": self.settings.neo4j_database}

        def _check():
            driver = self._get_driver()
            driver.verify_connectivity()
            return True

        try:
            reachable = await anyio.to_thread.run_sync(_check)
        except Exception as exc:  # pragma: no cover - depends on environment
            return {
                "configured": True,
                "reachable": False,
                "database": self.settings.neo4j_database,
                "error": str(exc),
            }

        return {"configured": True, "reachable": reachable, "database": self.settings.neo4j_database}

    async def run_query(self, cypher: str, parameters: dict[str, Any] | None = None) -> list[Any]:
        def _run():
            driver = self._get_driver()
            with driver.session(database=self.settings.neo4j_database or None) as session:
                result = session.run(cypher, parameters or {})
                return list(result)

        return await anyio.to_thread.run_sync(_run)

    async def get_schema_snapshot(self) -> SchemaSnapshot:
        def _fetch() -> SchemaSnapshot:
            driver = self._get_driver()
            with driver.session(database=self.settings.neo4j_database or None) as session:
                labels = session.run(
                    "CALL db.labels() YIELD label RETURN label ORDER BY label"
                ).value()
                relationship_types = session.run(
                    "CALL db.relationshipTypes() YIELD relationshipType "
                    "RETURN relationshipType ORDER BY relationshipType"
                ).value()
                property_keys = session.run(
                    "CALL db.propertyKeys() YIELD propertyKey RETURN propertyKey ORDER BY propertyKey"
                ).value()
                return SchemaSnapshot(
                    labels=[str(item) for item in labels],
                    relationship_types=[str(item) for item in relationship_types],
                    property_keys=[str(item) for item in property_keys],
                )

        return await anyio.to_thread.run_sync(_fetch)

    async def close(self) -> None:
        if self._driver is None:
            return

        await anyio.to_thread.run_sync(self._driver.close)
        self._driver = None
