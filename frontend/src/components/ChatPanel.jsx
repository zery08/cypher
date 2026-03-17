import { countSelection, summarizeSelection } from "../state";


export default function ChatPanel({
  messages,
  input,
  onInputChange,
  onSend,
  isSending,
  error,
  currentSelection,
  attachedSelection,
  onAttachSelection,
  onClearAttachment,
}) {
  const currentSelectionCount = countSelection(currentSelection);
  const attachedCount = countSelection(attachedSelection);

  return (
    <section className="panel chat-panel">
      <div className="panel-header">
        <p className="eyebrow">Graph Copilot</p>
        <h2>채팅이 메인 인터페이스입니다</h2>
      </div>
      <div className="chat-feed">
        {messages.map((message) => (
          <article
            key={message.id}
            className={`chat-bubble ${message.role} ${message.isStreaming ? "pending" : ""}`}
          >
            <div className="bubble-label">{message.role === "user" ? "You" : "Assistant"}</div>
            <p>{message.content || (message.isStreaming ? "응답 생성 중..." : "")}</p>
            {message.selectionSnapshot && countSelection(message.selectionSnapshot) ? (
              <div className="selection-chip-row">
                <span className="pill pill-outline">
                  첨부됨: {summarizeSelection(message.selectionSnapshot)}
                </span>
              </div>
            ) : null}
            {message.queryTrace &&
            (message.queryTrace.used_neo4j ||
              message.queryTrace.cypher ||
              message.queryTrace.explanation ||
              message.queryTrace.warnings?.length) ? (
              <div className="query-card">
                <div className="query-card-header">
                  <strong>{message.queryTrace.used_neo4j ? "Neo4j 조회" : "실행 추적"}</strong>
                  {message.queryTrace.result_counts ? (
                    <span className="pill">
                      노드 {message.queryTrace.result_counts?.node_count || 0} / 엣지{" "}
                      {message.queryTrace.result_counts?.edge_count || 0}
                    </span>
                  ) : null}
                </div>
                {message.queryTrace.explanation ? (
                  <p className="muted">{message.queryTrace.explanation}</p>
                ) : null}
                {message.queryTrace.cypher ? (
                  <pre className="code-block compact">
                    <code>{message.queryTrace.cypher}</code>
                  </pre>
                ) : null}
                {message.queryTrace.warnings?.length ? (
                  <ul className="warning-list compact-list">
                    {message.queryTrace.warnings.map((warning) => (
                      <li key={warning}>{warning}</li>
                    ))}
                  </ul>
                ) : null}
              </div>
            ) : null}
          </article>
        ))}
        {isSending ? (
          <article className="chat-bubble assistant pending">
            <div className="bubble-label">Assistant</div>
            <p>질문을 분석하고 필요한 경우 Neo4j 조회를 준비하는 중입니다.</p>
          </article>
        ) : null}
      </div>
      <form className="composer" onSubmit={onSend}>
        <div className="composer-toolbar">
          <button
            type="button"
            className="secondary-button"
            onClick={onAttachSelection}
            disabled={!currentSelectionCount}
          >
            선택 항목 첨부
          </button>
          <span className="muted">
            현재 선택: {currentSelectionCount ? summarizeSelection(currentSelection) : "없음"}
          </span>
        </div>
        {attachedCount ? (
          <div className="attachment-banner">
            <span>다음 메시지에 첨부됨: {summarizeSelection(attachedSelection)}</span>
            <button type="button" className="ghost-button" onClick={onClearAttachment}>
              제거
            </button>
          </div>
        ) : null}
        <textarea
          value={input}
          onChange={(event) => onInputChange(event.target.value)}
          placeholder="예: A 회사와 관련된 사람 보여줘. 선택한 노드를 중심으로 다시 설명해줘."
          rows={5}
          disabled={isSending}
        />
        <div className="composer-footer">
          {error ? <p className="error-text">{error}</p> : <span className="muted">스트리밍 응답</span>}
          <button type="submit" className="primary-button" disabled={isSending || !input.trim()}>
            {isSending ? "질문 처리 중..." : "메시지 보내기"}
          </button>
        </div>
      </form>
    </section>
  );
}
