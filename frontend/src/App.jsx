import { useReducer } from "react";

import ChatPanel from "./components/ChatPanel";
import DetailPanel from "./components/DetailPanel";
import GraphView from "./components/GraphView";
import QueryTracePanel from "./components/QueryTracePanel";
import { streamChatTurn } from "./lib/api";
import {
  buildGraphContext,
  buildSelectionFromGraph,
  createMessage,
  initialState,
  reducer,
} from "./state";


export default function App() {
  const [state, dispatch] = useReducer(reducer, initialState);
  const currentSelection = buildSelectionFromGraph(
    state.graph,
    state.selectedNodeIds,
    state.selectedEdgeIds,
  );

  async function handleSend(event) {
    event.preventDefault();
    const message = state.input.trim();
    if (!message || state.isSending) {
      return;
    }

    const attachedSelection = state.attachedSelection || { nodes: [], edges: [] };
    const userMessage = createMessage("user", message, {
      selectionSnapshot: attachedSelection,
    });
    const assistantMessage = createMessage("assistant", "", {
      isStreaming: true,
      queryTrace: null,
    });

    dispatch({ type: "SEND_STARTED", userMessage, assistantMessage });

    try {
      await streamChatTurn(
        {
        message,
        history: state.messages.map((item) => ({
          role: item.role,
          content: item.content,
        })),
        selection_context: attachedSelection,
        current_graph_context: buildGraphContext(state.graph),
        },
        {
          onEvent(event) {
            if (event.type === "query_trace") {
              dispatch({
                type: "STREAM_QUERY_TRACE",
                assistantMessageId: assistantMessage.id,
                queryTrace: event.query_trace,
              });
              return;
            }

            if (event.type === "graph") {
              dispatch({
                type: "STREAM_GRAPH",
                graph: event.graph,
              });
              return;
            }

            if (event.type === "delta") {
              dispatch({
                type: "STREAM_APPEND_DELTA",
                assistantMessageId: assistantMessage.id,
                content: event.content,
              });
            }
          },
        },
      );

      dispatch({
        type: "SEND_FINISHED",
        assistantMessageId: assistantMessage.id,
      });
    } catch (error) {
      dispatch({
        type: "SEND_FAILED",
        error: error.message,
        assistantMessageId: assistantMessage.id,
      });
    }
  }

  function handleAttachSelection() {
    dispatch({
      type: "ATTACH_SELECTION",
      selection: currentSelection,
    });
  }

  return (
    <div className="app-shell">
      <header className="hero">
        <div>
          <p className="eyebrow">Neo4j + LLM</p>
          <h1>Graph Chat Workspace</h1>
        </div>
        <p className="hero-copy">
          채팅이 Neo4j 조회를 유도하고, 최신 결과 그래프가 왼쪽에 시각적으로 유지됩니다.
        </p>
      </header>
      <main className="layout">
        <section className="left-column">
          <QueryTracePanel queryTrace={state.latestQueryTrace} />
          <GraphView
            graph={state.graph}
            selectedNodeIds={state.selectedNodeIds}
            selectedEdgeIds={state.selectedEdgeIds}
            focusItem={state.focusItem}
            onToggleNode={(id) => dispatch({ type: "TOGGLE_NODE_SELECTION", id })}
            onToggleEdge={(id) => dispatch({ type: "TOGGLE_EDGE_SELECTION", id })}
            onFocus={(value) => dispatch({ type: "SET_FOCUS", value })}
          />
          <DetailPanel
            graph={state.graph}
            focusItem={state.focusItem}
            selectedNodeIds={state.selectedNodeIds}
            selectedEdgeIds={state.selectedEdgeIds}
          />
        </section>
        <ChatPanel
          messages={state.messages}
          input={state.input}
          onInputChange={(value) => dispatch({ type: "SET_INPUT", value })}
          onSend={handleSend}
          isSending={state.isSending}
          error={state.error}
          currentSelection={currentSelection}
          attachedSelection={state.attachedSelection}
          onAttachSelection={handleAttachSelection}
          onClearAttachment={() => dispatch({ type: "CLEAR_ATTACHED_SELECTION" })}
        />
      </main>
    </div>
  );
}
