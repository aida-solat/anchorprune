"use client";

import {
  Cell,
  Legend,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
} from "recharts";

import { TOOLTIP_STYLE } from "./theme";
import { EmptyState } from "@/components/ui/EmptyState";
import type { PayloadBlock, PruningState } from "@/lib/types";

const STATE_COLOR: Record<PruningState, string> = {
  active: "#34d399",
  compressed: "#8a97ad",
  quarantined: "#fb7185",
  evicted: "#fbbf24",
};

// Derived from the final-state payload distribution. The read-only API exposes
// pruning state per block (not a per-step action log), so this is the snapshot
// breakdown of where blocks ended up.
export function PruningActionsChart({ blocks }: { blocks: PayloadBlock[] }) {
  const counts: Record<PruningState, number> = {
    active: 0,
    compressed: 0,
    quarantined: 0,
    evicted: 0,
  };
  blocks.forEach((b) => {
    counts[b.pruning_state] += 1;
  });
  const data = (Object.keys(counts) as PruningState[])
    .map((state) => ({ name: state, value: counts[state] }))
    .filter((d) => d.value > 0);

  if (data.length === 0) {
    return <EmptyState title="No payload blocks to break down yet." />;
  }

  return (
    <ResponsiveContainer width="100%" height={220}>
      <PieChart>
        <Pie
          data={data}
          dataKey="value"
          nameKey="name"
          innerRadius={45}
          outerRadius={80}
          paddingAngle={2}
        >
          {data.map((d) => (
            <Cell key={d.name} fill={STATE_COLOR[d.name as PruningState]} />
          ))}
        </Pie>
        <Tooltip contentStyle={TOOLTIP_STYLE} />
        <Legend wrapperStyle={{ fontSize: 11 }} />
      </PieChart>
    </ResponsiveContainer>
  );
}
