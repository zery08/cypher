function formatValue(value) {
  return JSON.stringify(value, null, 2);
}


export default function DetailPanel({ graph, focusItem, selectedNodeIds, selectedEdgeIds }) {
  const detail = getDetail(graph, focusItem, selectedNodeIds, selectedEdgeIds);

  return (
    <section className="panel detail-panel">
      <div className="panel-header">
        <p className="eyebrow">Selection Detail</p>
        <h2>선택된 데이터</h2>
      </div>
      {!detail ? (
        <p className="muted">그래프에서 노드 또는 엣지를 선택하면 상세 데이터가 여기에 표시됩니다.</p>
      ) : detail.type === "summary" ? (
        <div className="selection-summary">
          <p>{detail.description}</p>
          <div className="selection-columns">
            <div>
              <h3>Nodes</h3>
              <ul>
                {detail.nodes.map((node) => (
                  <li key={node.id}>{node.properties.name || node.labels[0] || node.id}</li>
                ))}
              </ul>
            </div>
            <div>
              <h3>Edges</h3>
              <ul>
                {detail.edges.map((edge) => (
                  <li key={edge.id}>{edge.type}</li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      ) : (
        <div className="detail-card">
          <div className="detail-badges">
            <span className="pill">{detail.type === "node" ? "Node" : "Edge"}</span>
            <span className="pill pill-outline">{detail.item.id}</span>
          </div>
          {detail.type === "node" ? (
            <div className="detail-meta">
              <p className="muted">{detail.item.labels.join(", ") || "No labels"}</p>
            </div>
          ) : (
            <div className="detail-meta">
              <p className="muted">
                {detail.item.source} → {detail.item.target}
              </p>
            </div>
          )}
          <pre className="code-block compact">
            <code>{formatValue(detail.item.properties)}</code>
          </pre>
        </div>
      )}
    </section>
  );
}


function getDetail(graph, focusItem, selectedNodeIds, selectedEdgeIds) {
  if (!graph) {
    return null;
  }

  if (focusItem?.kind === "node") {
    const node = graph.nodes.find((item) => item.id === focusItem.id);
    if (node) {
      return { type: "node", item: node };
    }
  }

  if (focusItem?.kind === "edge") {
    const edge = graph.edges.find((item) => item.id === focusItem.id);
    if (edge) {
      return { type: "edge", item: edge };
    }
  }

  const selectedNodes = graph.nodes.filter((item) => selectedNodeIds.includes(item.id));
  const selectedEdges = graph.edges.filter((item) => selectedEdgeIds.includes(item.id));
  const total = selectedNodes.length + selectedEdges.length;

  if (total === 1 && selectedNodes.length === 1) {
    return { type: "node", item: selectedNodes[0] };
  }
  if (total === 1 && selectedEdges.length === 1) {
    return { type: "edge", item: selectedEdges[0] };
  }
  if (total > 1) {
    return {
      type: "summary",
      description: `노드 ${selectedNodes.length}개와 엣지 ${selectedEdges.length}개가 선택되어 있습니다.`,
      nodes: selectedNodes,
      edges: selectedEdges,
    };
  }

  return null;
}
