export default function QueryTracePanel({ queryTrace }) {
  if (!queryTrace) {
    return (
      <section className="panel trace-panel panel-soft">
        <div className="panel-header">
          <p className="eyebrow">Latest Neo4j Query</p>
          <h2>아직 조회가 없습니다</h2>
        </div>
        <p className="muted">
          오른쪽 채팅에서 그래프 데이터가 필요한 질문을 보내면, 생성된 Cypher와 실행 요약이 여기에
          표시됩니다.
        </p>
      </section>
    );
  }

  return (
    <section className="panel trace-panel">
      <div className="panel-header">
        <p className="eyebrow">Latest Neo4j Query</p>
        <h2>{queryTrace.explanation || "최근 조회 추적"}</h2>
      </div>
      <div className="trace-meta">
        <span className="pill">{queryTrace.used_neo4j ? "실행됨" : "실행 안 됨"}</span>
        {queryTrace.result_counts ? (
          <span className="pill pill-outline">
            노드 {queryTrace.result_counts.node_count} / 엣지 {queryTrace.result_counts.edge_count}
          </span>
        ) : null}
      </div>
      {queryTrace.cypher ? (
        <pre className="code-block">
          <code>{queryTrace.cypher}</code>
        </pre>
      ) : (
        <p className="muted">이번 턴에서는 Cypher가 실행되지 않았습니다.</p>
      )}
      {queryTrace.warnings?.length ? (
        <ul className="warning-list">
          {queryTrace.warnings.map((warning) => (
            <li key={warning}>{warning}</li>
          ))}
        </ul>
      ) : null}
    </section>
  );
}
