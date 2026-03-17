from collections.abc import AsyncIterator
from typing import Any

from app.schemas import (
    ChatTurnRequest,
    ChatTurnResponse,
    GraphPayload,
    QueryTraceDTO,
    SchemaSnapshot,
)
from app.services.graph_normalizer import normalize_records
from app.services.llm_service import LLMService
from app.services.neo4j_service import Neo4jService
from app.services.query_guard import QueryValidationError, validate_read_only_cypher
from app.services.schema_service import SchemaService


class ChatOrchestrator:
    def __init__(
        self,
        llm_service: LLMService,
        neo4j_service: Neo4jService,
        schema_service: SchemaService,
    ):
        self.llm_service = llm_service
        self.neo4j_service = neo4j_service
        self.schema_service = schema_service

    async def handle_turn(self, payload: ChatTurnRequest) -> ChatTurnResponse:
        query_trace, graph_payload, detail_summary, early_message = await self._prepare_turn(payload)
        if early_message is not None:
            return ChatTurnResponse(
                assistant_message=early_message,
                query_trace=query_trace,
                graph=graph_payload,
                detail_summary=detail_summary,
            )

        try:
            assistant_message = await self.llm_service.answer_question(
                message=payload.message,
                history=payload.history,
                selection=payload.selection_context,
                query_trace=query_trace,
                graph=graph_payload,
            )
        except Exception as exc:
            warnings = [*query_trace.warnings, f"z.ai answer generation failed: {exc}"]
            assistant_message = (
                "Neo4j 조회 또는 컨텍스트 준비는 되었지만 최종 z.ai GLM 응답 생성이 실패했습니다. "
                "API 키, 모델명, 사용량 한도 또는 z.ai 계정 권한을 확인해 주세요."
            )
            query_trace = QueryTraceDTO(
                used_neo4j=query_trace.used_neo4j,
                cypher=query_trace.cypher,
                explanation=query_trace.explanation,
                warnings=warnings,
                result_counts=query_trace.result_counts,
            )

        return ChatTurnResponse(
            assistant_message=assistant_message,
            query_trace=query_trace,
            graph=graph_payload,
            detail_summary=detail_summary,
        )

    async def stream_turn(self, payload: ChatTurnRequest) -> AsyncIterator[dict[str, Any]]:
        query_trace, graph_payload, detail_summary, early_message = await self._prepare_turn(payload)

        yield {
            "type": "query_trace",
            "query_trace": query_trace.model_dump(),
        }

        if graph_payload is not None:
            yield {
                "type": "graph",
                "graph": graph_payload.model_dump(),
                "detail_summary": detail_summary,
            }

        if early_message is not None:
            yield {"type": "delta", "content": early_message}
            yield {"type": "done", "detail_summary": detail_summary}
            return

        try:
            async for chunk in self.llm_service.answer_question_stream(
                message=payload.message,
                history=payload.history,
                selection=payload.selection_context,
                query_trace=query_trace,
                graph=graph_payload,
            ):
                yield {"type": "delta", "content": chunk}
        except Exception as exc:
            warnings = [*query_trace.warnings, f"z.ai answer generation failed: {exc}"]
            query_trace = QueryTraceDTO(
                used_neo4j=query_trace.used_neo4j,
                cypher=query_trace.cypher,
                explanation=query_trace.explanation,
                warnings=warnings,
                result_counts=query_trace.result_counts,
            )
            yield {
                "type": "query_trace",
                "query_trace": query_trace.model_dump(),
            }
            yield {
                "type": "delta",
                "content": (
                    "Neo4j 조회 또는 컨텍스트 준비는 되었지만 최종 z.ai GLM 응답 생성이 실패했습니다. "
                    "API 키, 모델명, 사용량 한도 또는 z.ai 계정 권한을 확인해 주세요."
                ),
            }

        yield {"type": "done", "detail_summary": detail_summary}

    async def _prepare_turn(
        self,
        payload: ChatTurnRequest,
    ) -> tuple[QueryTraceDTO, GraphPayload | None, str | None, str | None]:
        schema, schema_warning = await self._load_schema()
        try:
            plan = await self.llm_service.plan_query(
                message=payload.message,
                history=payload.history,
                selection=payload.selection_context,
                graph_context=payload.current_graph_context,
                schema=schema,
            )
        except Exception as exc:
            warning = f"z.ai query-planning failed: {exc}"
            query_trace = QueryTraceDTO(
                used_neo4j=False,
                explanation="z.ai query planning failed.",
                warnings=[warning] + ([schema_warning] if schema_warning else []),
            )
            return (
                query_trace,
                None,
                None,
                "채팅 요청을 처리하는 중 z.ai GLM 호출이 실패했습니다. "
                "API 키, 모델명, 사용량 한도 또는 계정 권한 상태를 확인해 주세요.",
            )

        warnings = list(plan.warnings)
        if schema_warning:
            warnings.append(schema_warning)

        graph_payload: GraphPayload | None = None
        query_trace = QueryTraceDTO(
            used_neo4j=False,
            cypher=plan.cypher,
            explanation=plan.reason,
            warnings=warnings,
        )

        if plan.needs_neo4j:
            graph_payload, execution_warning = await self._run_query(plan.cypher)
            if execution_warning:
                warnings.append(execution_warning)
            if graph_payload:
                query_trace = QueryTraceDTO(
                    used_neo4j=True,
                    cypher=plan.cypher,
                    explanation=plan.reason,
                    warnings=warnings,
                    result_counts=graph_payload.summary,
                )
            else:
                query_trace = QueryTraceDTO(
                    used_neo4j=False,
                    cypher=plan.cypher,
                    explanation=plan.reason,
                    warnings=warnings,
                )

        return query_trace, graph_payload, _build_detail_summary(graph_payload), None

    async def _load_schema(self) -> tuple[SchemaSnapshot | None, str | None]:
        if not self.neo4j_service.is_configured:
            return None, "Neo4j configuration is missing."

        try:
            schema = await self.schema_service.get_schema_snapshot()
        except Exception as exc:
            return None, f"Failed to load Neo4j schema: {exc}"

        return schema, None

    async def _run_query(self, cypher: str | None) -> tuple[GraphPayload | None, str | None]:
        if not self.neo4j_service.is_configured:
            return None, "Neo4j configuration is missing."
        if not cypher:
            return None, "A database query was required but the LLM did not generate Cypher."

        try:
            safe_cypher = validate_read_only_cypher(cypher)
        except QueryValidationError as exc:
            return None, str(exc)

        try:
            records = await self.neo4j_service.run_query(safe_cypher)
        except Exception as exc:
            return None, f"Neo4j query failed: {exc}"

        return normalize_records(records), None


def _build_detail_summary(graph_payload: GraphPayload | None) -> str | None:
    if graph_payload is None:
        return None

    summary = graph_payload.summary
    return (
        f"Rendered {summary.node_count} nodes and {summary.edge_count} edges "
        f"from {summary.record_count} Neo4j records."
    )
