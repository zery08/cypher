from collections.abc import Iterable, Mapping
from typing import Any

from app.schemas import EdgeDTO, GraphPayload, NodeDTO, QueryResultSummary


def serialize_value(value: Any) -> Any:
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    if isinstance(value, Mapping):
        return {str(key): serialize_value(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [serialize_value(item) for item in value]
    return str(value)


def is_node(value: Any) -> bool:
    return hasattr(value, "element_id") and hasattr(value, "labels")


def is_relationship(value: Any) -> bool:
    return (
        hasattr(value, "element_id")
        and hasattr(value, "type")
        and (hasattr(value, "start_node") or hasattr(value, "start_node_element_id"))
    )


def is_path(value: Any) -> bool:
    return hasattr(value, "nodes") and hasattr(value, "relationships")


def normalize_records(records: Iterable[Any]) -> GraphPayload:
    nodes: dict[str, NodeDTO] = {}
    edges: dict[str, EdgeDTO] = {}
    scalar_count = 0
    record_count = 0

    for record in records:
        record_count += 1
        values = record.values() if hasattr(record, "values") else record
        for value in values:
            scalar_count += _extract_entities(value, nodes, edges)

    return GraphPayload(
        nodes=list(nodes.values()),
        edges=list(edges.values()),
        summary=QueryResultSummary(
            node_count=len(nodes),
            edge_count=len(edges),
            record_count=record_count,
            scalar_count=scalar_count,
        ),
    )


def _extract_entities(value: Any, nodes: dict[str, NodeDTO], edges: dict[str, EdgeDTO]) -> int:
    if is_node(value):
        _add_node(value, nodes)
        return 0

    if is_relationship(value):
        _add_relationship(value, nodes, edges)
        return 0

    if is_path(value):
        for node in getattr(value, "nodes", []):
            _add_node(node, nodes)
        for relationship in getattr(value, "relationships", []):
            _add_relationship(relationship, nodes, edges)
        return 0

    if isinstance(value, Mapping):
        return sum(_extract_entities(item, nodes, edges) for item in value.values())

    if isinstance(value, (list, tuple, set)):
        return sum(_extract_entities(item, nodes, edges) for item in value)

    return 1


def _add_node(node: Any, nodes: dict[str, NodeDTO]) -> None:
    node_id = str(getattr(node, "element_id"))
    if node_id in nodes:
        return

    labels = list(getattr(node, "labels", []))
    properties = serialize_value(dict(node.items())) if hasattr(node, "items") else {}
    nodes[node_id] = NodeDTO(id=node_id, labels=labels, properties=properties)


def _add_relationship(relationship: Any, nodes: dict[str, NodeDTO], edges: dict[str, EdgeDTO]) -> None:
    edge_id = str(getattr(relationship, "element_id"))
    if edge_id in edges:
        return

    start_node = getattr(relationship, "start_node", None)
    end_node = getattr(relationship, "end_node", None)
    if start_node is not None:
        _add_node(start_node, nodes)
    if end_node is not None:
        _add_node(end_node, nodes)

    source = getattr(relationship, "start_node_element_id", None) or getattr(start_node, "element_id", "")
    target = getattr(relationship, "end_node_element_id", None) or getattr(end_node, "element_id", "")
    properties = serialize_value(dict(relationship.items())) if hasattr(relationship, "items") else {}

    edges[edge_id] = EdgeDTO(
        id=edge_id,
        type=str(getattr(relationship, "type", "")),
        source=str(source),
        target=str(target),
        properties=properties,
    )
