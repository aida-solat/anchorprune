"use client";

import { Badge } from "@/components/ui/Badge";
import { Card } from "@/components/ui/Card";
import { EmptyState } from "@/components/ui/EmptyState";
import { pct } from "@/lib/format";
import type { Milestone } from "@/lib/types";

export function MilestonesPanel({ milestones }: { milestones: Milestone[] }) {
  if (milestones.length === 0) {
    return (
      <EmptyState
        title="No milestones retained yet."
        hint="Milestones are compact reasoning checkpoints AnchorPrune keeps across steps — evidence that it retains decision state, not just shortened text."
      />
    );
  }

  return (
    <div className="flex flex-col gap-3">
      <p className="text-xs text-muted">
        Retention confidence is a governance heuristic for how strongly a
        milestone should be kept across steps — not the model&apos;s confidence
        in the final decision.
      </p>
      <div className="grid gap-3 md:grid-cols-2">
        {milestones.map((m) => (
          <Card key={m.id} className="flex flex-col gap-2 border-milestone/30">
            <div className="flex items-center justify-between">
              <Badge tone="milestone">{m.stage}</Badge>
              <span className="text-xs text-muted">
                retention confidence {pct(m.confidence)}
              </span>
            </div>
            <p className="text-sm text-ink">{m.finding}</p>
            <div className="mt-auto flex flex-wrap gap-3 text-xs text-muted">
              <span>{m.linked_anchor_ids.length} anchors</span>
              <span>{m.linked_block_ids.length} source blocks</span>
              <span>{m.evidence_refs.length} evidence</span>
              <span>step {m.step_index}</span>
            </div>
          </Card>
        ))}
      </div>
    </div>
  );
}
