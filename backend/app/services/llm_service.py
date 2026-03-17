import json
import re
from collections.abc import AsyncIterator
from typing import Any

from openai import AsyncOpenAI

from app.core.config import Settings
from app.schemas import (
    ChatMessageDTO,
    CurrentGraphContextDTO,
    GraphPayload,
    QueryGenerationPlan,
    QueryTraceDTO,
    SchemaSnapshot,
    SelectionContextDTO,
)


class LLMService:
    def __init__(self, settings: Settings):
        self.settings = settings
        self._client = None

    @property
    def is_configured(self) -> bool:
        return self.settings.llm_configured

    def _get_client(self) -> AsyncOpenAI:
        if not self.is_configured:
            raise RuntimeError("LLM is not configured.")
        if self._client is None:
            self._client = AsyncOpenAI(
                base_url=self.settings.llm_base_url,
                api_key=self.settings.llm_api_key,
                timeout=20.0,
                max_retries=0,
            )
        return self._client

    async def plan_query(
        self,
        message: str,
        history: list[ChatMessageDTO],
        selection: SelectionContextDTO,
        graph_context: CurrentGraphContextDTO | None,
        schema: SchemaSnapshot | None,
    ) -> QueryGenerationPlan:
        if not self.is_configured:
            return QueryGenerationPlan(
                needs_neo4j=False,
                reason="LLM configuration is missing.",
                warnings=["OpenAI-compatible LLM configuration is missing."],
            )

        prompt_messages = [
            {
                "role": "system",
                "content": (
                    "You decide whether the user's latest chat message requires querying Neo4j. "
                    "Return strict JSON with keys needs_neo4j (boolean), reason (string), "
                    "cypher (string or null), warnings (array of strings). "
                    "If a query is needed, generate exactly one read-only Cypher statement, "
                    "use only the provided schema when possible, always include RETURN, and "
                    "never use write or admin operations."
                ),
            },
            {
                "role": "user",
                "content": json.dumps(
                    {
                        "message": message,
                        "history": [item.model_dump() for item in history[-8:]],
                        "selection_context": selection.model_dump(),
                        "current_graph_context": graph_context.model_dump() if graph_context else None,
                        "schema": schema.model_dump() if schema else None,
                    },
                    ensure_ascii=False,
                ),
            },
        ]
        parsed = await self._complete_json(prompt_messages, temperature=0.1)
        return QueryGenerationPlan.model_validate(parsed)

    async def answer_question(
        self,
        message: str,
        history: list[ChatMessageDTO],
        selection: SelectionContextDTO,
        query_trace: QueryTraceDTO,
        graph: GraphPayload | None,
    ) -> str:
        if not self.is_configured:
            return (
                "OpenAI-compatible LLM configuration is missing. "
                "Set LLM_BASE_URL, LLM_API_KEY, and LLM_MODEL."
            )

        prompt_messages = self._build_answer_prompt_messages(
            message=message,
            history=history,
            selection=selection,
            query_trace=query_trace,
            graph=graph,
        )
        return await self._complete(prompt_messages, temperature=0.3)

    async def answer_question_stream(
        self,
        message: str,
        history: list[ChatMessageDTO],
        selection: SelectionContextDTO,
        query_trace: QueryTraceDTO,
        graph: GraphPayload | None,
    ) -> AsyncIterator[str]:
        if not self.is_configured:
            yield (
                "OpenAI-compatible LLM configuration is missing. "
                "Set LLM_BASE_URL, LLM_API_KEY, and LLM_MODEL."
            )
            return

        prompt_messages = self._build_answer_prompt_messages(
            message=message,
            history=history,
            selection=selection,
            query_trace=query_trace,
            graph=graph,
        )

        client = self._get_client()
        stream = await client.chat.completions.create(
            model=self.settings.llm_model,
            messages=prompt_messages,
            temperature=0.3,
            stream=True,
        )

        async for chunk in stream:
            if not chunk.choices:
                continue
            content = _coerce_text(chunk.choices[0].delta.content)
            if content:
                yield content

    async def _complete(self, messages: list[dict[str, Any]], temperature: float) -> str:
        client = self._get_client()
        response = await client.chat.completions.create(
            model=self.settings.llm_model,
            messages=messages,
            temperature=temperature,
        )
        content = response.choices[0].message.content or ""
        return content.strip()

    async def _complete_json(self, messages: list[dict[str, Any]], temperature: float) -> dict[str, Any]:
        client = self._get_client()
        try:
            response = await client.chat.completions.create(
                model=self.settings.llm_model,
                messages=messages,
                temperature=temperature,
                response_format={"type": "json_object"},
            )
            content = response.choices[0].message.content or "{}"
            return _extract_json_object(content)
        except Exception:
            raw_content = await self._complete(messages, temperature=temperature)
            return _extract_json_object(raw_content)

    def _build_answer_prompt_messages(
        self,
        message: str,
        history: list[ChatMessageDTO],
        selection: SelectionContextDTO,
        query_trace: QueryTraceDTO,
        graph: GraphPayload | None,
    ) -> list[dict[str, Any]]:
        return [
            {
                "role": "system",
                "content": (
                    "You are a graph analyst. Answer in Korean. Use the Neo4j query trace and graph "
                    "result when available. If no database query was used, answer from the conversation "
                    "and attached graph selection only. If important data is missing, say so plainly."
                ),
            },
            {
                "role": "user",
                "content": json.dumps(
                    {
                        "message": message,
                        "history": [item.model_dump() for item in history[-8:]],
                        "selection_context": selection.model_dump(),
                        "query_trace": query_trace.model_dump(),
                        "graph_preview": _summarize_graph_payload(graph),
                    },
                    ensure_ascii=False,
                ),
            },
        ]


def _extract_json_object(text: str) -> dict[str, Any]:
    stripped = text.strip()
    if stripped.startswith("```"):
        stripped = re.sub(r"^```(?:json)?\s*|\s*```$", "", stripped, flags=re.DOTALL)

    try:
        return json.loads(stripped)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", stripped, flags=re.DOTALL)
        if not match:
            raise
        return json.loads(match.group(0))


def _coerce_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        parts = []
        for item in value:
            if isinstance(item, str):
                parts.append(item)
                continue
            if isinstance(item, dict):
                text = item.get("text")
                if isinstance(text, str):
                    parts.append(text)
                continue
            text = getattr(item, "text", None)
            if isinstance(text, str):
                parts.append(text)
        return "".join(parts)
    return str(value)


def _summarize_graph_payload(graph: GraphPayload | None) -> dict[str, Any] | None:
    if graph is None:
        return None

    return {
        "summary": graph.summary.model_dump(),
        "nodes": [node.model_dump() for node in graph.nodes[:12]],
        "edges": [edge.model_dump() for edge in graph.edges[:20]],
    }
