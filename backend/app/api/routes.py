import json

from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse

from app.schemas import ChatTurnRequest, ChatTurnResponse, HealthResponse

router = APIRouter()


@router.post("/chat/turn", response_model=ChatTurnResponse)
async def chat_turn(payload: ChatTurnRequest, request: Request) -> ChatTurnResponse:
    return await request.app.state.orchestrator.handle_turn(payload)


@router.post("/chat/stream")
async def chat_stream(payload: ChatTurnRequest, request: Request) -> StreamingResponse:
    async def event_stream():
        async for event in request.app.state.orchestrator.stream_turn(payload):
            if await request.is_disconnected():
                break
            yield _encode_sse(event)

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.get("/health", response_model=HealthResponse)
async def health(request: Request) -> HealthResponse:
    settings = request.app.state.settings
    neo4j_health = await request.app.state.neo4j_service.health_check()
    llm_health = {
        "configured": request.app.state.llm_service.is_configured,
        "model": settings.llm_model,
        "base_url": settings.llm_base_url,
    }
    status = "ok" if neo4j_health.get("reachable") and llm_health["configured"] else "degraded"
    return HealthResponse(
        status=status,
        app={"name": settings.app_name},
        neo4j=neo4j_health,
        llm=llm_health,
    )


def _encode_sse(payload: dict) -> str:
    return f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"
