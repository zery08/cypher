import { describe, expect, it } from "vitest";

import {
  buildSelectionFromGraph,
  countSelection,
  createMessage,
  initialState,
  reducer,
} from "./state";


describe("state reducer", () => {
  it("updates the active assistant message while streaming", () => {
    const stateAfterSend = reducer(initialState, {
      type: "SEND_STARTED",
      userMessage: createMessage("user", "테스트"),
      assistantMessage: createMessage("assistant", "", { isStreaming: true }),
    });
    const assistantMessage = stateAfterSend.messages.at(-1);

    const stateAfterDelta = reducer(stateAfterSend, {
      type: "STREAM_APPEND_DELTA",
      assistantMessageId: assistantMessage.id,
      content: "응답",
    });

    expect(stateAfterDelta.messages.at(-1).content).toBe("응답");
  });

  it("attaches latest query trace and graph during a streamed Neo4j-backed response", () => {
    const stateAfterSend = reducer(initialState, {
      type: "SEND_STARTED",
      userMessage: createMessage("user", "테스트"),
      assistantMessage: createMessage("assistant", "", { isStreaming: true }),
    });
    const assistantMessage = stateAfterSend.messages.at(-1);
    const graph = {
      nodes: [{ id: "n1", labels: ["Person"], properties: { name: "Alice" } }],
      edges: [],
      summary: { node_count: 1, edge_count: 0 },
    };

    const queryTrace = { used_neo4j: true, cypher: "MATCH (n) RETURN n", warnings: [] };
    const stateAfterTrace = reducer(stateAfterSend, {
      type: "STREAM_QUERY_TRACE",
      assistantMessageId: assistantMessage.id,
      queryTrace,
    });
    const nextState = reducer(stateAfterTrace, {
      type: "STREAM_GRAPH",
      graph,
    });

    expect(nextState.graph).toEqual(graph);
    expect(nextState.latestQueryTrace.cypher).toBe("MATCH (n) RETURN n");
  });

  it("builds a selection snapshot from current graph ids", () => {
    const graph = {
      nodes: [{ id: "n1", labels: ["Person"], properties: { name: "Alice" } }],
      edges: [{ id: "e1", type: "KNOWS", source: "n1", target: "n2", properties: {} }],
    };

    const selection = buildSelectionFromGraph(graph, ["n1"], ["e1"]);

    expect(countSelection(selection)).toBe(2);
    expect(selection.nodes[0].id).toBe("n1");
    expect(selection.edges[0].id).toBe("e1");
  });
});
