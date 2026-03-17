import pytest

from app.schemas import (
    ChatTurnRequest,
    CurrentGraphContextDTO,
    QueryGenerationPlan,
    QueryResultSummary,
    SelectionContextDTO,
    SchemaSnapshot,
)
from app.services.orchestrator import ChatOrchestrator


class FakeLLMService:
    def __init__(self, plan, answer):
        self.plan = plan
        self.answer = answer

    async def plan_query(self, **kwargs):
        return self.plan

    async def answer_question(self, **kwargs):
        return self.answer


class FailingLLMService:
    async def plan_query(self, **kwargs):
        raise RuntimeError("401 invalid_api_key")

    async def answer_question(self, **kwargs):
        raise RuntimeError("should not reach")


class FakeSchemaService:
    async def get_schema_snapshot(self):
        return SchemaSnapshot(labels=["Person"], relationship_types=["WORKS_AT"], property_keys=["name"])


class FakeNeo4jService:
    def __init__(self, records=None, configured=True):
        self.records = records or []
        self.is_configured = configured

    async def run_query(self, cypher):
        return self.records


class FakeNode:
    def __init__(self, element_id, labels=None, properties=None):
        self.element_id = element_id
        self.labels = set(labels or [])
        self._properties = properties or {}

    def items(self):
        return self._properties.items()


def make_request():
    return ChatTurnRequest(
        message="A 회사와 관련된 사람 보여줘",
        history=[],
        selection_context=SelectionContextDTO(),
        current_graph_context=CurrentGraphContextDTO(has_graph=False),
    )


@pytest.mark.asyncio
async def test_orchestrator_returns_graph_when_query_is_used():
    plan = QueryGenerationPlan(
        needs_neo4j=True,
        reason="회사 관련 인물을 찾기 위해 조회가 필요합니다.",
        cypher="MATCH (p:Person) RETURN p LIMIT 5",
    )
    records = [{"person": FakeNode("n1", ["Person"], {"name": "Alice"})}]
    orchestrator = ChatOrchestrator(
        llm_service=FakeLLMService(plan, "Alice를 찾았습니다."),
        neo4j_service=FakeNeo4jService(records=records),
        schema_service=FakeSchemaService(),
    )

    response = await orchestrator.handle_turn(make_request())

    assert response.query_trace.used_neo4j is True
    assert response.graph is not None
    assert response.graph.summary == QueryResultSummary(
        node_count=1,
        edge_count=0,
        record_count=1,
        scalar_count=0,
    )


@pytest.mark.asyncio
async def test_orchestrator_blocks_unsafe_generated_query():
    plan = QueryGenerationPlan(
        needs_neo4j=True,
        reason="조회가 필요합니다.",
        cypher="CREATE (n:Bad) RETURN n",
    )
    orchestrator = ChatOrchestrator(
        llm_service=FakeLLMService(plan, "차단되었습니다."),
        neo4j_service=FakeNeo4jService(),
        schema_service=FakeSchemaService(),
    )

    response = await orchestrator.handle_turn(make_request())

    assert response.query_trace.used_neo4j is False
    assert response.graph is None
    assert response.query_trace.warnings


@pytest.mark.asyncio
async def test_orchestrator_returns_friendly_message_when_llm_plan_fails():
    orchestrator = ChatOrchestrator(
        llm_service=FailingLLMService(),
        neo4j_service=FakeNeo4jService(),
        schema_service=FakeSchemaService(),
    )

    response = await orchestrator.handle_turn(make_request())

    assert response.graph is None
    assert response.query_trace.used_neo4j is False
    assert "z.ai" in response.assistant_message
    assert any("invalid_api_key" in warning for warning in response.query_trace.warnings)
