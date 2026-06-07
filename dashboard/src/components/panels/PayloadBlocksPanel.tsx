"use client";

import { useState } from "react";

import { Badge, type BadgeTone } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { EmptyState } from "@/components/ui/EmptyState";
import { TCell, THead, TRow, Table } from "@/components/ui/Table";
import { truncate } from "@/lib/format";
import type { PayloadBlock, PruningState } from "@/lib/types";

const STATE_TONE: Record<PruningState, BadgeTone> = {
  active: "ok",
  compressed: "neutral",
  quarantined: "danger",
  evicted: "warn",
};

type Filter = "all" | PruningState | "adversarial" | "noise" | "obsolete";

function flag(block: PayloadBlock, key: string): boolean {
  return Boolean(
    block.metadata && (block.metadata as Record<string, unknown>)[key],
  );
}

export function PayloadBlocksPanel({ blocks }: { blocks: PayloadBlock[] }) {
  const [filter, setFilter] = useState<Filter>("all");

  const filtered = blocks.filter((b) => {
    switch (filter) {
      case "all":
        return true;
      case "adversarial":
      case "noise":
      case "obsolete":
        return filter === "obsolete"
          ? b.obsolete || flag(b, "obsolete")
          : flag(b, filter);
      default:
        return b.pruning_state === filter;
    }
  });

  const filters: Filter[] = [
    "all",
    "active",
    "compressed",
    "quarantined",
    "evicted",
    "adversarial",
    "noise",
    "obsolete",
  ];

  return (
    <div className="flex flex-col gap-3">
      <p className="text-xs leading-relaxed text-muted">
        Payload blocks are retained for inspection, but only{" "}
        <span className="text-ink">active</span> and{" "}
        <span className="text-ink">compressed</span> governed state can
        influence future context. <span className="text-ink">Quarantined</span>{" "}
        and <span className="text-ink">evicted</span> blocks are excluded from
        the composed decision context.
      </p>
      <div className="flex flex-wrap items-center gap-2">
        {filters.map((f) => (
          <Button
            key={f}
            variant={filter === f ? "primary" : "ghost"}
            onClick={() => setFilter(f)}
          >
            {f}
          </Button>
        ))}
      </div>

      {filtered.length === 0 ? (
        <EmptyState title="No payload blocks match this filter." />
      ) : (
        <Table>
          <THead
            columns={[
              "Type",
              "State",
              "Utility",
              "Tokens",
              "Anchors",
              "Content",
            ]}
          />
          <tbody>
            {filtered.map((b) => (
              <TRow key={b.id}>
                <TCell className="whitespace-nowrap text-muted">
                  {b.block_type}
                </TCell>
                <TCell>
                  <Badge tone={STATE_TONE[b.pruning_state]}>
                    {b.pruning_state}
                  </Badge>
                </TCell>
                <TCell className="tabular-nums text-muted">
                  {b.utility_score.toFixed(2)}
                </TCell>
                <TCell className="tabular-nums text-muted">
                  {b.token_estimate}
                </TCell>
                <TCell className="tabular-nums text-muted">
                  {b.linked_anchor_ids.length}
                </TCell>
                <TCell className="max-w-md text-ink">
                  {truncate(b.content, 160)}
                </TCell>
              </TRow>
            ))}
          </tbody>
        </Table>
      )}
    </div>
  );
}
