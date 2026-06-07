"use client";

import { Badge } from "@/components/ui/Badge";
import { Card } from "@/components/ui/Card";
import { EmptyState } from "@/components/ui/EmptyState";
import { formatDate } from "@/lib/format";
import type { ConflictEdge, PayloadBlock } from "@/lib/types";

export function QuarantinePanel({
  blocks,
  conflicts,
}: {
  blocks: PayloadBlock[];
  conflicts: ConflictEdge[];
}) {
  const quarantined = blocks.filter(
    (b) => b.pruning_state === "quarantined" || b.quarantined,
  );

  if (quarantined.length === 0 && conflicts.length === 0) {
    return (
      <EmptyState
        title="No quarantined payloads in this run."
        hint="When a payload tries to override a system anchor or contradicts a critical constraint, the Anchor Governor quarantines it here — kept for audit, but never composed into the decision context."
      />
    );
  }

  return (
    <div className="flex flex-col gap-4">
      <p className="text-sm text-muted">
        Quarantined state is retained for audit but{" "}
        <span className="text-ink">never reaches the model&apos;s decision context</span>.
        This is where the governance story is visible.
      </p>

      {conflicts.length > 0 ? (
        <div className="flex flex-col gap-2">
          <h3 className="text-xs uppercase tracking-wide text-muted">
            Conflict edges
          </h3>
          {conflicts.map((c) => (
            <ConflictCard key={c.id} conflict={c} />
          ))}
        </div>
      ) : null}

      {quarantined.length > 0 ? (
        <div className="flex flex-col gap-2">
          <h3 className="text-xs uppercase tracking-wide text-muted">
            Quarantined payload blocks
          </h3>
          {quarantined.map((b) => (
            <Card key={b.id} className="border-danger/30">
              <div className="mb-1 flex items-center gap-2">
                <Badge tone="danger">quarantined</Badge>
                <Badge>{b.block_type}</Badge>
                <span className="text-xs text-muted">
                  conflict severity {b.conflict_severity.toFixed(2)}
                </span>
              </div>
              <p className="text-sm text-ink">{b.content}</p>
              <p className="mt-2 text-xs text-muted">
                Downstream action blocked: this block is excluded from the
                composed context. Added {formatDate(b.created_at)}.
              </p>
            </Card>
          ))}
        </div>
      ) : null}
    </div>
  );
}

function ConflictCard({ conflict }: { conflict: ConflictEdge }) {
  return (
    <Card className="border-danger/30">
      <div className="mb-1 flex flex-wrap items-center gap-2">
        <Badge tone={conflict.critical ? "danger" : "warn"}>
          {conflict.critical ? "critical hard gate" : "conflict"}
        </Badge>
        <Badge>{conflict.kind}</Badge>
        <span className="text-xs text-muted">
          severity {conflict.severity.toFixed(2)}
        </span>
      </div>
      <p className="text-sm text-ink">{conflict.source_ref}</p>
      <p className="mt-1 text-xs text-muted">
        Conflicts with <span className="text-ink">{conflict.target_ref}</span>
        {conflict.reason ? ` · ${conflict.reason}` : ""}
      </p>
    </Card>
  );
}
