// Builds a grouped node/edge layout for the governed state graph.
// This is pure presentation: it arranges existing state objects and the edges
// the API already reports. It performs no governance and infers no linkage
// beyond what the state graph declares.

import type { Edge, Node } from "@xyflow/react";

import type { GovernedState } from "./types";

export type GraphNodeKind =
  | "system"
  | "domain"
  | "runtime"
  | "milestone"
  | "payload-active"
  | "payload-compressed"
  | "payload-quarantined"
  | "payload-evicted";

export interface GraphNodeData {
  label: string;
  sub: string;
  kind: GraphNodeKind;
  [key: string]: unknown;
}

export type GraphNode = Node<GraphNodeData>;

interface BuildOptions {
  includeEvicted?: boolean;
}

const COLUMN_X: Record<string, number> = {
  anchors: 0,
  milestones: 340,
  payload: 680,
};

const ROW_H = 96;

function payloadKind(state: string): GraphNodeKind {
  switch (state) {
    case "compressed":
      return "payload-compressed";
    case "quarantined":
      return "payload-quarantined";
    case "evicted":
      return "payload-evicted";
    default:
      return "payload-active";
  }
}

export function buildGraph(
  state: GovernedState,
  options: BuildOptions = {},
): { nodes: GraphNode[]; edges: Edge[] } {
  const nodes: GraphNode[] = [];
  const edges: Edge[] = [];
  const nodeIds = new Set<string>();

  // Column 1: anchors (system → domain → runtime), most authoritative on top.
  const order = { system: 0, domain: 1, runtime: 2 } as const;
  const anchors = [...state.anchors].sort(
    (a, b) => order[a.anchor_class] - order[b.anchor_class],
  );
  anchors.forEach((anchor, i) => {
    nodes.push({
      id: anchor.id,
      position: { x: COLUMN_X.anchors, y: i * ROW_H },
      data: {
        label: anchor.content,
        sub: `${anchor.anchor_class} · ${anchor.priority} · w=${anchor.weight.toFixed(2)}`,
        kind: anchor.anchor_class as GraphNodeKind,
      },
      type: "graphNode",
    });
    nodeIds.add(anchor.id);
  });

  // Column 2: milestones.
  state.milestones.forEach((m, i) => {
    nodes.push({
      id: m.id,
      position: { x: COLUMN_X.milestones, y: i * ROW_H },
      data: {
        label: m.finding,
        sub: `${m.stage} · retention=${m.confidence.toFixed(2)}`,
        kind: "milestone",
      },
      type: "graphNode",
    });
    nodeIds.add(m.id);
    m.linked_anchor_ids.forEach((aid) => {
      if (nodeIds.has(aid)) {
        edges.push({
          id: `e-${m.id}-${aid}`,
          source: m.id,
          target: aid,
          animated: false,
        });
      }
    });
  });

  // Column 3: payload blocks.
  const blocks = state.payload_blocks.filter(
    (b) => options.includeEvicted || b.pruning_state !== "evicted",
  );
  blocks.forEach((b, i) => {
    nodes.push({
      id: b.id,
      position: { x: COLUMN_X.payload, y: i * ROW_H },
      data: {
        label: b.content,
        sub: `${b.block_type} · ${b.pruning_state} · ${b.token_estimate} tok`,
        kind: payloadKind(b.pruning_state),
      },
      type: "graphNode",
    });
    nodeIds.add(b.id);
  });
  // Payload → anchor linkage (drawn after all nodes exist).
  blocks.forEach((b) => {
    b.linked_anchor_ids.forEach((aid) => {
      if (nodeIds.has(aid)) {
        edges.push({
          id: `e-${b.id}-${aid}`,
          source: b.id,
          target: aid,
          animated: false,
        });
      }
    });
  });
  // Milestone → source block linkage.
  state.milestones.forEach((m) => {
    m.linked_block_ids.forEach((bid) => {
      if (nodeIds.has(bid)) {
        edges.push({
          id: `e-${m.id}-${bid}`,
          source: m.id,
          target: bid,
          animated: false,
        });
      }
    });
  });

  // Conflict edges: only render where both endpoints resolve to real nodes.
  state.conflict_edges.forEach((c) => {
    if (nodeIds.has(c.source_ref) && nodeIds.has(c.target_ref)) {
      edges.push({
        id: c.id,
        source: c.source_ref,
        target: c.target_ref,
        label: c.critical ? "critical conflict" : "conflict",
        animated: c.critical,
        style: { stroke: "#fb7185" },
        labelStyle: { fill: "#fb7185", fontSize: 10 },
      });
    }
  });

  return { nodes, edges };
}
