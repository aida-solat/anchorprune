"use client";

import { ContextGrowthChart } from "@/components/charts/ContextGrowthChart";
import { PruningActionsChart } from "@/components/charts/PruningActionsChart";
import { StateObjectCountChart } from "@/components/charts/StateObjectCountChart";
import { TokenUsageChart } from "@/components/charts/TokenUsageChart";
import { Card } from "@/components/ui/Card";
import { EmptyState } from "@/components/ui/EmptyState";
import { num } from "@/lib/format";
import type { MetricsResponse, PayloadBlock } from "@/lib/types";

function ChartCard({
  title,
  subtitle,
  children,
}: {
  title: string;
  subtitle?: string;
  children: React.ReactNode;
}) {
  return (
    <Card className="flex flex-col gap-2">
      <div>
        <h3 className="text-sm font-medium text-ink">{title}</h3>
        {subtitle ? <p className="text-xs text-muted">{subtitle}</p> : null}
      </div>
      {children}
    </Card>
  );
}

export function MetricsPanel({
  metrics,
  blocks,
}: {
  metrics: MetricsResponse | null;
  blocks: PayloadBlock[];
}) {
  const steps = metrics?.steps ?? [];

  return (
    <div className="flex flex-col gap-4">
      {metrics ? (
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          <SummaryStat label="Steps" value={num(metrics.summary.total_steps)} />
          <SummaryStat
            label="Input tokens"
            value={num(metrics.summary.total_input_tokens)}
          />
          <SummaryStat
            label="Output tokens"
            value={num(metrics.summary.total_output_tokens)}
          />
          <SummaryStat
            label="Max context"
            value={num(metrics.summary.max_context_size)}
          />
        </div>
      ) : null}

      {steps.length === 0 ? (
        <EmptyState
          title="No step metrics yet."
          hint="Run at least one step (POST /runs/{id}/steps) to populate metrics."
        />
      ) : (
        <div className="grid gap-3 lg:grid-cols-2">
          <ChartCard
            title="Context growth"
            subtitle="Composed input tokens per step"
          >
            <ContextGrowthChart steps={steps} />
          </ChartCard>
          <ChartCard title="Token usage" subtitle="Input vs output per step">
            <TokenUsageChart steps={steps} />
          </ChartCard>
          <ChartCard
            title="State object counts"
            subtitle="Anchors, payload, quarantined over steps"
          >
            <StateObjectCountChart steps={steps} />
          </ChartCard>
          <ChartCard
            title="Payload by state"
            subtitle="Final-snapshot pruning breakdown"
          >
            <PruningActionsChart blocks={blocks} />
          </ChartCard>
        </div>
      )}
    </div>
  );
}

function SummaryStat({ label, value }: { label: string; value: string }) {
  return (
    <Card className="flex flex-col gap-1">
      <span className="text-xs uppercase tracking-wide text-muted">{label}</span>
      <span className="text-xl font-semibold tabular-nums text-ink">{value}</span>
    </Card>
  );
}
