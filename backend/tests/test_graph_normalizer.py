from app.services.graph_normalizer import normalize_records


class FakeNode:
    def __init__(self, element_id, labels=None, properties=None):
        self.element_id = element_id
        self.labels = set(labels or [])
        self._properties = properties or {}

    def items(self):
        return self._properties.items()


class FakeRelationship:
    def __init__(self, element_id, rel_type, start_node, end_node, properties=None):
        self.element_id = element_id
        self.type = rel_type
        self.start_node = start_node
        self.end_node = end_node
        self._properties = properties or {}

    def items(self):
        return self._properties.items()


def test_normalize_records_extracts_nodes_and_edges():
    alice = FakeNode("n1", ["Person"], {"name": "Alice"})
    acme = FakeNode("n2", ["Company"], {"name": "Acme"})
    works_at = FakeRelationship("r1", "WORKS_AT", alice, acme, {"since": 2022})
    records = [{"person": alice, "company": acme, "relationship": works_at}]

    graph = normalize_records(records)

    assert graph.summary.node_count == 2
    assert graph.summary.edge_count == 1
    assert {node.id for node in graph.nodes} == {"n1", "n2"}
    assert graph.edges[0].source == "n1"
    assert graph.edges[0].target == "n2"
