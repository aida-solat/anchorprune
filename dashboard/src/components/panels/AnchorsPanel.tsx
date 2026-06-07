"use client";

import { useState } from "react";

import { Badge, type BadgeTone } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { EmptyState } from "@/components/ui/EmptyState";
import { TCell, THead, TRow, Table } from "@/components/ui/Table";
import { formatDate } from "@/lib/format";
import type { Anchor, AnchorClass } from "@/lib/types";

const CLASS_TONE: Record<AnchorClass, BadgeTone> = {
  system: "system",
  domain: "domain",
  runtime: "runtime",
};

type ClassFilter = "all" | AnchorClass;

export function AnchorsPanel({ anchors }: { anchors: Anchor[] }) {
  const [cls, setCls] = useState<ClassFilter>("all");
  const [criticalOnly, setCriticalOnly] = useState(false);

  const filtered = anchors.filter((a) => {
    if (cls !== "all" && a.anchor_class !== cls) return false;
    if (criticalOnly && a.priority !== "critical") return false;
    return true;
  });

  const filters: ClassFilter[] = ["all", "system", "domain", "runtime"];

  return (
    <div className="flex flex-col gap-3">
      <div className="flex flex-wrap items-center gap-2">
        {filters.map((f) => (
          <Button
            key={f}
            variant={cls === f ? "primary" : "ghost"}
            onClick={() => setCls(f)}
          >
            {f}
          </Button>
        ))}
        <Button
          variant={criticalOnly ? "primary" : "ghost"}
          onClick={() => setCriticalOnly((v) => !v)}
        >
          Critical only
        </Button>
      </div>

      {filtered.length === 0 ? (
        <EmptyState title="No anchors match this filter." />
      ) : (
        <Table>
          <THead
            columns={[
              "Class",
              "Type",
              "Priority",
              "Weight",
              "Status",
              "Content",
              "Evidence",
              "Created",
            ]}
          />
          <tbody>
            {filtered.map((a) => (
              <TRow key={a.id}>
                <TCell>
                  <Badge tone={CLASS_TONE[a.anchor_class]}>
                    {a.anchor_class}
                  </Badge>
                </TCell>
                <TCell className="text-muted">{a.anchor_type}</TCell>
                <TCell>
                  <Badge tone={a.priority === "critical" ? "danger" : "neutral"}>
                    {a.priority}
                  </Badge>
                </TCell>
                <TCell className="tabular-nums text-muted">
                  {a.weight.toFixed(2)}
                </TCell>
                <TCell>
                  <Badge tone={a.status === "approved" ? "ok" : "warn"}>
                    {a.status}
                  </Badge>
                </TCell>
                <TCell className="max-w-md text-ink">{a.content}</TCell>
                <TCell className="tabular-nums text-muted">
                  {a.evidence_refs.length}
                </TCell>
                <TCell className="whitespace-nowrap text-xs text-muted">
                  {formatDate(a.created_at)}
                </TCell>
              </TRow>
            ))}
          </tbody>
        </Table>
      )}
    </div>
  );
}
