"use client";

import { RunsTable } from "@/components/runs/RunsTable";
import { Button } from "@/components/ui/Button";
import { EmptyState } from "@/components/ui/EmptyState";
import { getRuns } from "@/lib/api";
import { useResource } from "@/lib/useResource";

export default function RunsPage() {
  const { data, error, loading, reload } = useResource(getRuns, []);

  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold text-ink">Runs</h1>
          <p className="text-sm text-muted">
            Persisted runs from the AnchorPrune service.
          </p>
        </div>
        <Button variant="ghost" onClick={reload}>
          Refresh
        </Button>
      </div>

      {loading ? (
        <p className="text-sm text-muted">Loading runs…</p>
      ) : error ? (
        <EmptyState
          title="Could not load runs"
          hint={error}
        />
      ) : !data || data.length === 0 ? (
        <EmptyState
          title="No runs yet"
          hint="Create one via the API or CLI: `anchorprune run --input examples/supplier/scenario.json`, then refresh."
        />
      ) : (
        <RunsTable runs={data} />
      )}
    </div>
  );
}
