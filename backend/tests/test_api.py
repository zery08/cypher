from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import create_app
from app.schemas import ChatTurnResponse, QueryTraceDTO


class FakeOrchestrator:
    async def handle_turn(self, payload):
        return ChatTurnResponse(
            assistant_message="응답입니다.",
            query_trace=QueryTraceDTO(used_neo4j=False, explanation="일반 답변"),
            graph=None,
            detail_summary=None,
        )

    async def stream_turn(self, payload):
        yield {
            "type": "query_trace",
            "query_trace": QueryTraceDTO(
                used_neo4j=False,
                explanation="일반 답변",
            ).model_dump(),
        }
        yield {"type": "delta", "content": "응"}
        yield {"type": "delta", "content": "답"}
        yield {"type": "done", "detail_summary": None}


class FakeNeo4jService:
    async def health_check(self):
        return {"configured": True, "reachable": True, "database": "neo4j"}

    async def close(self):
        return None


class FakeLLMService:
    is_configured = True


def test_chat_turn_route_returns_structured_response():
    app = create_app(
        settings=Settings(llm_api_key="test-key"),
        neo4j_service=FakeNeo4jService(),
        llm_service=FakeLLMService(),
        orchestrator=FakeOrchestrator(),
    )
    client = TestClient(app)

    response = client.post(
        "/api/chat/turn",
        json={
            "message": "안녕",
            "history": [],
            "selection_context": {"nodes": [], "edges": []},
            "current_graph_context": {"has_graph": False, "node_count": 0, "edge_count": 0},
        },
    )

    assert response.status_code == 200
    assert response.json()["assistant_message"] == "응답입니다."


def test_health_route_reports_ok_status():
    app = create_app(
        settings=Settings(llm_api_key="test-key"),
        neo4j_service=FakeNeo4jService(),
        llm_service=FakeLLMService(),
        orchestrator=FakeOrchestrator(),
    )
    client = TestClient(app)

    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_chat_stream_route_returns_sse_payload():
    app = create_app(
        settings=Settings(llm_api_key="test-key"),
        neo4j_service=FakeNeo4jService(),
        llm_service=FakeLLMService(),
        orchestrator=FakeOrchestrator(),
    )
    client = TestClient(app)

    response = client.post(
        "/api/chat/stream",
        json={
            "message": "안녕",
            "history": [],
            "selection_context": {"nodes": [], "edges": []},
            "current_graph_context": {"has_graph": False, "node_count": 0, "edge_count": 0},
        },
    )

    assert response.status_code == 200
    assert "text/event-stream" in response.headers["content-type"]
    assert '"type": "delta"' in response.text
    assert '"content": "응"' in response.text
