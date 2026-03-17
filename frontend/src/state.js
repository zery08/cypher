let fallbackId = 0;


function createId() {
  if (typeof crypto !== "undefined" && typeof crypto.randomUUID === "function") {
    return crypto.randomUUID();
  }
  fallbackId += 1;
  return `message-${fallbackId}`;
}


export function createMessage(role, content, extras = {}) {
  return {
    id: createId(),
    role,
    content,
    ...extras,
  };
}


export const initialState = {
  messages: [
    createMessage(
      "assistant",
      "질문을 보내면 필요할 때만 Neo4j를 조회하고, 최근 조회 결과를 왼쪽 그래프에 보여줍니다.",
    ),
  ],
  input: "",
  isSending: false,
  error: null,
  graph: null,
  latestQueryTrace: null,
  selectedNodeIds: [],
  selectedEdgeIds: [],
  focusItem: null,
  attachedSelection: null,
};


export function reducer(state, action) {
  switch (action.type) {
    case "SET_INPUT":
      return { ...state, input: action.value };
    case "TOGGLE_NODE_SELECTION":
      return {
        ...state,
        selectedNodeIds: toggleId(state.selectedNodeIds, action.id),
        focusItem: { kind: "node", id: action.id },
      };
    case "TOGGLE_EDGE_SELECTION":
      return {
        ...state,
        selectedEdgeIds: toggleId(state.selectedEdgeIds, action.id),
        focusItem: { kind: "edge", id: action.id },
      };
    case "SET_FOCUS":
      return { ...state, focusItem: action.value };
    case "ATTACH_SELECTION":
      return { ...state, attachedSelection: action.selection };
    case "CLEAR_ATTACHED_SELECTION":
      return { ...state, attachedSelection: null };
    case "SEND_STARTED":
      return {
        ...state,
        isSending: true,
        error: null,
        input: "",
        messages: [...state.messages, action.userMessage, action.assistantMessage],
      };
    case "STREAM_APPEND_DELTA":
      return {
        ...state,
        messages: state.messages.map((message) =>
          message.id === action.assistantMessageId
            ? {
                ...message,
                content: `${message.content}${action.content}`,
              }
            : message,
        ),
      };
    case "STREAM_QUERY_TRACE":
      return {
        ...state,
        latestQueryTrace: action.queryTrace,
        messages: state.messages.map((message) =>
          message.id === action.assistantMessageId
            ? {
                ...message,
                queryTrace: action.queryTrace,
              }
            : message,
        ),
      };
    case "STREAM_GRAPH":
      return {
        ...state,
        graph: action.graph,
        selectedNodeIds: [],
        selectedEdgeIds: [],
        focusItem: null,
      };
    case "SEND_FINISHED":
      return {
        ...state,
        isSending: false,
        error: null,
        attachedSelection: null,
        messages: state.messages.map((message) =>
          message.id === action.assistantMessageId
            ? {
                ...message,
                isStreaming: false,
              }
            : message,
        ),
      };
    case "SEND_FAILED":
      return {
        ...state,
        isSending: false,
        error: action.error,
        messages: state.messages.map((message) =>
          message.id === action.assistantMessageId
            ? {
                ...message,
                isStreaming: false,
              }
            : message,
        ),
      };
    default:
      return state;
  }
}


function toggleId(items, id) {
  return items.includes(id) ? items.filter((item) => item !== id) : [...items, id];
}


export function buildSelectionFromGraph(graph, selectedNodeIds, selectedEdgeIds) {
  if (!graph) {
    return { nodes: [], edges: [] };
  }

  return {
    nodes: graph.nodes.filter((node) => selectedNodeIds.includes(node.id)),
    edges: graph.edges.filter((edge) => selectedEdgeIds.includes(edge.id)),
  };
}


export function buildGraphContext(graph) {
  if (!graph) {
    return {
      has_graph: false,
      node_count: 0,
      edge_count: 0,
    };
  }

  return {
    has_graph: true,
    node_count: graph.nodes.length,
    edge_count: graph.edges.length,
  };
}


export function countSelection(selection) {
  if (!selection) {
    return 0;
  }
  return selection.nodes.length + selection.edges.length;
}


export function summarizeSelection(selection) {
  if (!selection || countSelection(selection) === 0) {
    return "선택 항목 없음";
  }

  return `노드 ${selection.nodes.length}개, 엣지 ${selection.edges.length}개`;
}
