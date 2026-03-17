from typing import Any, Literal

from pydantic import BaseModel, Field


class NodeDTO(BaseModel):
    id: str
    labels: list[str] = Field(default_factory=list)
    properties: dict[str, Any] = Field(default_factory=dict)


class EdgeDTO(BaseModel):
    id: str
    type: str
    source: str
    target: str
    properties: dict[str, Any] = Field(default_factory=dict)


class QueryResultSummary(BaseModel):
    node_count: int = 0
    edge_count: int = 0
    record_count: int = 0
    scalar_count: int = 0


class GraphPayload(BaseModel):
    nodes: list[NodeDTO] = Field(default_factory=list)
    edges: list[EdgeDTO] = Field(default_factory=list)
    summary: QueryResultSummary = Field(default_factory=QueryResultSummary)


class SelectionContextDTO(BaseModel):
    nodes: list[NodeDTO] = Field(default_factory=list)
    edges: list[EdgeDTO] = Field(default_factory=list)


class CurrentGraphContextDTO(BaseModel):
    has_graph: bool = False
    node_count: int = 0
    edge_count: int = 0


class ChatMessageDTO(BaseModel):
    role: Literal["user", "assistant", "system"]
    content: str


class ChatTurnRequest(BaseModel):
    message: str
    history: list[ChatMessageDTO] = Field(default_factory=list)
    selection_context: SelectionContextDTO = Field(default_factory=SelectionContextDTO)
    current_graph_context: CurrentGraphContextDTO | None = None


class QueryTraceDTO(BaseModel):
    used_neo4j: bool = False
    cypher: str | None = None
    explanation: str | None = None
    warnings: list[str] = Field(default_factory=list)
    result_counts: QueryResultSummary | None = None


class ChatTurnResponse(BaseModel):
    assistant_message: str
    query_trace: QueryTraceDTO
    graph: GraphPayload | None = None
    detail_summary: str | None = None


class HealthResponse(BaseModel):
    status: Literal["ok", "degraded"]
    app: dict[str, Any]
    neo4j: dict[str, Any]
    llm: dict[str, Any]


class QueryGenerationPlan(BaseModel):
    needs_neo4j: bool = False
    reason: str = ""
    cypher: str | None = None
    warnings: list[str] = Field(default_factory=list)


class SchemaSnapshot(BaseModel):
    labels: list[str] = Field(default_factory=list)
    relationship_types: list[str] = Field(default_factory=list)
    property_keys: list[str] = Field(default_factory=list)
