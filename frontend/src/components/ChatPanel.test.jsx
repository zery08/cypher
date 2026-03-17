import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import ChatPanel from "./ChatPanel";


describe("ChatPanel", () => {
  it("renders Neo4j query trace inside assistant messages", () => {
    render(
      <ChatPanel
        messages={[
          {
            id: "a1",
            role: "assistant",
            content: "조회 결과입니다.",
            queryTrace: {
              used_neo4j: true,
              cypher: "MATCH (n) RETURN n",
              explanation: "그래프 조회",
              warnings: [],
              result_counts: { node_count: 3, edge_count: 2 },
            },
          },
        ]}
        input=""
        onInputChange={() => {}}
        onSend={(event) => event.preventDefault()}
        isSending={false}
        error={null}
        currentSelection={{ nodes: [], edges: [] }}
        attachedSelection={null}
        onAttachSelection={() => {}}
        onClearAttachment={() => {}}
      />,
    );

    expect(screen.getByText("Neo4j 조회")).toBeInTheDocument();
    expect(screen.getByText("MATCH (n) RETURN n")).toBeInTheDocument();
  });

  it("renders warning-only execution traces when z.ai planning fails", () => {
    render(
      <ChatPanel
        messages={[
          {
            id: "a2",
            role: "assistant",
            content: "z.ai 호출 실패",
            queryTrace: {
              used_neo4j: false,
              cypher: null,
              explanation: "z.ai query planning failed.",
              warnings: ["429 rate_limit_exceeded"],
            },
          },
        ]}
        input=""
        onInputChange={() => {}}
        onSend={(event) => event.preventDefault()}
        isSending={false}
        error={null}
        currentSelection={{ nodes: [], edges: [] }}
        attachedSelection={null}
        onAttachSelection={() => {}}
        onClearAttachment={() => {}}
      />,
    );

    expect(screen.getByText("실행 추적")).toBeInTheDocument();
    expect(screen.getByText("429 rate_limit_exceeded")).toBeInTheDocument();
  });

  it("calls attach handler when the attach button is pressed", () => {
    const onAttachSelection = vi.fn();
    render(
      <ChatPanel
        messages={[]}
        input=""
        onInputChange={() => {}}
        onSend={(event) => event.preventDefault()}
        isSending={false}
        error={null}
        currentSelection={{ nodes: [{ id: "n1" }], edges: [] }}
        attachedSelection={null}
        onAttachSelection={onAttachSelection}
        onClearAttachment={() => {}}
      />,
    );

    fireEvent.click(screen.getByRole("button", { name: "선택 항목 첨부" }));
    expect(onAttachSelection).toHaveBeenCalledTimes(1);
  });
});
