"use client";

import {
  Background,
  Controls,
  Handle,
  type NodeProps,
  Position,
  ReactFlow,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import { useMemo } from "react";

import { EmptyState } from "@/components/ui/EmptyState";
import { truncate } from "@/lib/format";
import { buildGraph, type GraphNodeKind } from "@/lib/graph";
import type { GovernedState } from "@/lib/types";

const KIND_STYLE: Record<
  GraphNodeKind,
  { border: string; tag: string; label: string }
> = {
  system: { border: "#f87171", tag: "#f87171", label: "System anchor" },
  domain: { border: "#fbbf24", tag: "#fbbf24", label: "Domain anchor" },
  runtime: { border: "#60a5fa", tag: "#60a5fa", label: "Runtime anchor" },
  milestone: { border: "#34d399", tag: "#34d399", label: "Milestone" },
  "payload-active": {
    border: "#3b82f6",
    tag: "#60a5fa",
    label: "Payload (active)",
  },
  "payload-compressed": {
    border: "#4b5568",
    tag: "#8a97ad",
    label: "Payload (compressed)",
  },
  "payload-quarantined": {
    border: "#fb7185",
    tag: "#fb7185",
    label: "Payload (quarantined)",
  },
  "payload-evicted": {
    border: "#6b7280",
    tag: "#6b7280",
    label: "Payload (evicted)",
  },
};

function GraphNode({ data }: NodeProps) {
  const kind = data.kind as GraphNodeKind;
  const style = KIND_STYLE[kind];
  return (
    <div
      className="w-56 rounded-lg border bg-panel px-3 py-2 text-left shadow"
      style={{ borderColor: style.border }}
    >
      <Handle type="target" position={Position.Left} style={{ opacity: 0 }} />
      <span
        className="text-[10px] font-semibold uppercase tracking-wide"
        style={{ color: style.tag }}
      >
        {String(data.sub)}
      </span>
      <p
        className="mt-0.5 text-xs leading-snug text-ink"
        title={String(data.label)}
      >
        {truncate(String(data.label), 90)}
      </p>
      <Handle type="source" position={Position.Right} style={{ opacity: 0 }} />
    </div>
  );
}

const LEGEND: GraphNodeKind[] = [
  "system",
  "domain",
  "runtime",
  "milestone",
  "payload-active",
  "payload-quarantined",
];

export function StateGraph({ state }: { state: GovernedState }) {
  const nodeTypes = useMemo(() => ({ graphNode: GraphNode }), []);
  const { nodes, edges } = useMemo(() => buildGraph(state), [state]);

  if (nodes.length === 0) {
    return <EmptyState title="No state objects to graph yet." />;
  }

  return (
    <div className="flex flex-col gap-3">
      <div className="flex flex-wrap gap-3">
        {LEGEND.map((k) => (
          <span
            key={k}
            className="flex items-center gap-1.5 text-xs text-muted"
          >
            <span
              className="h-2.5 w-2.5 rounded-sm"
              style={{ backgroundColor: KIND_STYLE[k].tag }}
            />
            {KIND_STYLE[k].label}
          </span>
        ))}
      </div>
      <div className="h-[560px] rounded-xl border border-border bg-bg">
        <ReactFlow
          nodes={nodes}
          edges={edges}
          nodeTypes={nodeTypes}
          fitView
          fitViewOptions={{ padding: 0.3 }}
          minZoom={0.2}
          proOptions={{ hideAttribution: false }}
          nodesDraggable
          nodesConnectable={false}
          elementsSelectable
        >
          <Background color="#252e40" gap={20} />
          <Controls showInteractive={false} />
        </ReactFlow>
      </div>
      <p className="text-xs text-muted">
        Columns: anchors → milestones → payload blocks. Edges show anchor,
        evidence, and conflict linkage the state graph declares. Evicted blocks
        are hidden by default.
      </p>
    </div>
  );
}
