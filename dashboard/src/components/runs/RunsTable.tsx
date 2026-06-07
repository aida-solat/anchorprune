"use client";

import Link from "next/link";

import { RunStatusBadge } from "@/components/runs/RunStatusBadge";
import { Badge } from "@/components/ui/Badge";
import { TCell, THead, TRow, Table } from "@/components/ui/Table";
import { formatRelative } from "@/lib/format";
import type { RunSummary } from "@/lib/types";

export function RunsTable({ runs }: { runs: RunSummary[] }) {
  return (
    <Table>
      <THead
        columns={["Run", "Goal", "Domain", "Status", "Created", "Updated", ""]}
      />
      <tbody>
        {runs.map((run) => (
          <TRow key={run.run_id} className="hover:bg-panel2/40">
            <TCell className="font-mono text-xs text-muted">{run.run_id}</TCell>
            <TCell className="max-w-sm text-ink">{run.goal}</TCell>
            <TCell>
              <Badge>{run.domain}</Badge>
            </TCell>
            <TCell>
              <RunStatusBadge status={run.status} />
            </TCell>
            <TCell className="whitespace-nowrap text-xs text-muted">
              {formatRelative(run.created_at)}
            </TCell>
            <TCell className="whitespace-nowrap text-xs text-muted">
              {formatRelative(run.updated_at)}
            </TCell>
            <TCell>
              <Link
                href={`/runs/${encodeURIComponent(run.run_id)}`}
                className="text-sm text-accent hover:underline"
              >
                Open →
              </Link>
            </TCell>
          </TRow>
        ))}
      </tbody>
    </Table>
  );
}
