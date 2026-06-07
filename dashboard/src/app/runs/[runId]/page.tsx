"use client";

import dynamic from "next/dynamic";
import Link from "next/link";
import { useState } from "react";

import { RunStatusBadge } from "@/components/runs/RunStatusBadge";
import { AnchorsPanel } from "@/components/panels/AnchorsPanel";
import { AuditTimeline } from "@/components/panels/AuditTimeline";
import { MetricsPanel } from "@/components/panels/MetricsPanel";
import { MilestonesPanel } from "@/components/panels/MilestonesPanel";
import { PayloadBlocksPanel } from "@/components/panels/PayloadBlocksPanel";
import { QuarantinePanel } from "@/components/panels/QuarantinePanel";
import { StatCard } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { TabPanel, Tabs, type TabDef } from "@/components/ui/Tabs";
import { getRun, getRunAudit, getRunMetrics, getRunState } from "@/lib/api";
import { num } from "@/lib/format";
import { useResource } from "@/lib/useResource";

// React Flow measures the DOM, so render it client-only.
const StateGraph = dynamic(
  () => import("@/components/state/StateGraph").then((m) => m.StateGraph),
  { ssr: false, loading: () => <p className="text-sm text-muted">Loading graph…</p> },
);

export default function RunDetailPage({
  params,
}: {
  params: { runId: string };
}) {
  const runId = decodeURIComponent(params.runId);
  const [tab, setTab] = useState("graph");

  const run = useResource(() => getRun(runId), [runId]);
  const state = useResource(() => getRunState(runId), [runId]);
  const audit = useResource(() => getRunAudit(runId), [runId]);
  const metrics = useResource(() => getRunMetrics(runId), [runId]);

  const reloadAll = () => {
    run.reload();
    state.reload();
    audit.reload();
    metrics.reload();
  };

  const s = state.data;
  const liveBlocks = s?.payload_blocks.filter((b) => b.pruning_state !== "evicted") ?? [];
  const quarantinedCount =
    s?.payload_blocks.filter((b) => b.pruning_state === "quarantined" || b.quarantined)
      .length ?? 0;

  const tabs: TabDef[] = [
    { id: "graph", label: "Graph" },
    { id: "anchors", label: "Anchors", count: s?.anchors.length },
    { id: "payloads", label: "Payloads", count: s?.payload_blocks.length },
    { id: "quarantine", label: "Quarantine", count: quarantinedCount },
    { id: "milestones", label: "Milestones", count: s?.milestones.length },
    { id: "audit", label: "Audit", count: audit.data?.events.length },
    { id: "metrics", label: "Metrics", count: metrics.data?.summary.total_steps },
  ];

  return (
    <div className="flex flex-col gap-5">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="flex flex-col gap-1">
          <Link href="/runs" className="text-xs text-muted hover:text-ink">
            ← Runs
          </Link>
          <h1 className="text-xl font-semibold text-ink">
            {run.data?.goal ?? runId}
          </h1>
          <div className="flex flex-wrap items-center gap-2 text-xs text-muted">
            <span className="font-mono">{runId}</span>
            {run.data ? (
              <>
                <span>· {run.data.domain}</span>
                <RunStatusBadge status={run.data.status} />
              </>
            ) : null}
          </div>
        </div>
        <Button variant="ghost" onClick={reloadAll}>
          Refresh
        </Button>
      </div>

      {state.error ? (
        <p className="rounded-lg border border-danger/40 bg-danger/10 px-3 py-2 text-sm text-danger">
          {state.error}
        </p>
      ) : null}

      <div className="grid gap-3 sm:grid-cols-3 lg:grid-cols-6">
        <StatCard label="Anchors" value={num(s?.anchors.length ?? 0)} />
        <StatCard label="Payload (live)" value={num(liveBlocks.length)} />
        <StatCard
          label="Quarantined"
          value={num(quarantinedCount)}
          tone={quarantinedCount > 0 ? "danger" : "default"}
        />
        <StatCard label="Milestones" value={num(s?.milestones.length ?? 0)} tone="ok" />
        <StatCard
          label="Input tokens"
          value={num(metrics.data?.summary.total_input_tokens ?? 0)}
        />
        <StatCard
          label="Max context"
          value={num(metrics.data?.summary.max_context_size ?? 0)}
        />
      </div>

      <Tabs tabs={tabs} active={tab} onChange={setTab} />

      {state.loading ? (
        <p className="text-sm text-muted">Loading governed state…</p>
      ) : (
        <>
          <TabPanel when="graph" active={tab}>
            {s ? <StateGraph state={s} /> : null}
          </TabPanel>
          <TabPanel when="anchors" active={tab}>
            {s ? <AnchorsPanel anchors={s.anchors} /> : null}
          </TabPanel>
          <TabPanel when="payloads" active={tab}>
            {s ? <PayloadBlocksPanel blocks={s.payload_blocks} /> : null}
          </TabPanel>
          <TabPanel when="quarantine" active={tab}>
            {s ? (
              <QuarantinePanel blocks={s.payload_blocks} conflicts={s.conflict_edges} />
            ) : null}
          </TabPanel>
          <TabPanel when="milestones" active={tab}>
            {s ? <MilestonesPanel milestones={s.milestones} /> : null}
          </TabPanel>
          <TabPanel when="audit" active={tab}>
            <AuditTimeline events={audit.data?.events ?? []} />
          </TabPanel>
          <TabPanel when="metrics" active={tab}>
            <MetricsPanel metrics={metrics.data} blocks={s?.payload_blocks ?? []} />
          </TabPanel>
        </>
      )}
    </div>
  );
}
