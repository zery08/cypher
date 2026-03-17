import { useEffect, useRef } from "react";
import CytoscapeComponent from "react-cytoscapejs";


const stylesheet = [
  {
    selector: "node",
    style: {
      width: 42,
      height: 42,
      "background-color": "#ff7b54",
      color: "#261316",
      label: "data(label)",
      "font-size": 10,
      "text-valign": "center",
      "text-halign": "center",
      "font-weight": 700,
      "text-wrap": "wrap",
      "text-max-width": 80,
      "border-width": 2,
      "border-color": "#fff4dc",
    },
  },
  {
    selector: "edge",
    style: {
      width: 2,
      "line-color": "#e9b872",
      "target-arrow-color": "#e9b872",
      "target-arrow-shape": "triangle",
      "curve-style": "bezier",
      label: "data(label)",
      "font-size": 9,
      color: "#7e6454",
      "text-background-opacity": 1,
      "text-background-color": "#fff4dc",
      "text-background-padding": 2,
    },
  },
  {
    selector: ".selected",
    style: {
      "background-color": "#00a6a6",
      "line-color": "#00a6a6",
      "target-arrow-color": "#00a6a6",
      "border-color": "#d7fffb",
      width: 4,
    },
  },
  {
    selector: ".focused",
    style: {
      "border-width": 4,
      "border-color": "#261316",
      width: 5,
    },
  },
];


export default function GraphView({
  graph,
  selectedNodeIds,
  selectedEdgeIds,
  focusItem,
  onToggleNode,
  onToggleEdge,
  onFocus,
}) {
  const cyRef = useRef(null);

  useEffect(() => {
    const cy = cyRef.current;
    if (!cy) {
      return undefined;
    }

    const handleNodeTap = (event) => {
      const node = event.target;
      onToggleNode(node.id());
    };
    const handleEdgeTap = (event) => {
      const edge = event.target;
      onToggleEdge(edge.id());
    };
    const handleBackgroundTap = (event) => {
      if (event.target === cy) {
        onFocus(null);
      }
    };

    cy.on("tap", "node", handleNodeTap);
    cy.on("tap", "edge", handleEdgeTap);
    cy.on("tap", handleBackgroundTap);

    return () => {
      cy.off("tap", "node", handleNodeTap);
      cy.off("tap", "edge", handleEdgeTap);
      cy.off("tap", handleBackgroundTap);
    };
  }, [onFocus, onToggleEdge, onToggleNode]);

  if (!graph || (!graph.nodes.length && !graph.edges.length)) {
    return (
      <section className="panel graph-panel panel-soft">
        <div className="panel-header">
          <p className="eyebrow">Latest Graph</p>
          <h2>결과 그래프가 없습니다</h2>
        </div>
        <p className="muted">
          오른쪽 채팅에서 Neo4j 조회가 필요한 질문을 보내면 여기에 최신 노드와 엣지가 표시됩니다.
        </p>
      </section>
    );
  }

  const elements = [
    ...graph.nodes.map((node) => ({
      data: {
        id: node.id,
        label: node.properties.name || node.labels[0] || node.id,
      },
      classes: buildClasses(selectedNodeIds.includes(node.id), focusItem, "node", node.id),
    })),
    ...graph.edges.map((edge) => ({
      data: {
        id: edge.id,
        label: edge.type,
        source: edge.source,
        target: edge.target,
      },
      classes: buildClasses(selectedEdgeIds.includes(edge.id), focusItem, "edge", edge.id),
    })),
  ];

  return (
    <section className="panel graph-panel">
      <div className="panel-header">
        <p className="eyebrow">Latest Graph</p>
        <h2>최신 Neo4j 결과</h2>
      </div>
      <div className="graph-meta">
        <span className="pill pill-outline">노드 {graph.nodes.length}</span>
        <span className="pill pill-outline">엣지 {graph.edges.length}</span>
      </div>
      <div className="graph-canvas">
        <CytoscapeComponent
          elements={elements}
          style={{ width: "100%", height: "100%" }}
          stylesheet={stylesheet}
          layout={{ name: "cose", animate: false, padding: 28, fit: true }}
          cy={(cy) => {
            cyRef.current = cy;
          }}
        />
      </div>
    </section>
  );
}


function buildClasses(isSelected, focusItem, kind, id) {
  const classes = [];
  if (isSelected) {
    classes.push("selected");
  }
  if (focusItem && focusItem.kind === kind && focusItem.id === id) {
    classes.push("focused");
  }
  return classes.join(" ");
}
