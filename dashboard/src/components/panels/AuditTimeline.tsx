"use client";

import { useState } from "react";

import { Badge, type BadgeTone } from "@/components/ui/Badge";
import { EmptyState } from "@/components/ui/EmptyState";
import { formatDate, titleCase } from "@/lib/format";
import type { AuditEvent } from "@/lib/types";

const EVENT_TONE: Record<string, BadgeTone> = {
  run_created: "neutral",
  payload_added: "neutral",
  anchor_proposed: "runtime",
  anchor_decision: "domain",
  conflict_detected: "danger",
  pruning_action: "warn",
  context_composed: "ok",
  step_completed: "milestone",
};

function reasonOf(payload: Record<string, unknown>): string {
  const keys = ["reason", "action", "op", "block_type", "content"];
  for (const k of keys) {
    if (typeof payload[k] === "string" && payload[k]) {
      return String(payload[k]);
    }
  }
  return "";
}

export function AuditTimeline({ events }: { events: AuditEvent[] }) {
  const [open, setOpen] = useState<number | null>(null);

  if (events.length === 0) {
    return <EmptyState title="No audit events recorded for this run." />;
  }

  return (
    <ol className="relative flex flex-col gap-1 border-l border-border pl-5">
      {events.map((e, i) => {
        const expanded = open === i;
        return (
          <li key={i} className="relative">
            <span className="absolute -left-[22px] top-2 h-2.5 w-2.5 rounded-full border border-border bg-panel2" />
            <button
              onClick={() => setOpen(expanded ? null : i)}
              className="flex w-full flex-wrap items-center gap-2 rounded-md px-2 py-1.5 text-left hover:bg-panel2/50"
            >
              <Badge tone={EVENT_TONE[e.event_type] ?? "neutral"}>
                {titleCase(e.event_type)}
              </Badge>
              <span className="text-xs text-muted">step {e.step_index}</span>
              <span className="truncate text-xs text-muted">
                {reasonOf(e.payload)}
              </span>
              <span className="ml-auto whitespace-nowrap text-[11px] text-muted">
                {formatDate(e.created_at)}
              </span>
            </button>
            {expanded ? (
              <pre className="mx-2 mb-2 overflow-x-auto rounded-lg bg-bg p-3 text-[11px] leading-relaxed text-muted">
                {JSON.stringify(e.payload, null, 2)}
              </pre>
            ) : null}
          </li>
        );
      })}
    </ol>
  );
}
