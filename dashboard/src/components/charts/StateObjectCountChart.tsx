"use client";

import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { AXIS, COLORS, GRID, TOOLTIP_STYLE } from "./theme";
import type { StepMetric } from "@/lib/types";

export function StateObjectCountChart({ steps }: { steps: StepMetric[] }) {
  const data = steps.map((s) => ({
    step: s.step,
    anchors: s.anchors,
    payload: s.payload_blocks,
    quarantined: s.quarantined,
  }));

  return (
    <ResponsiveContainer width="100%" height={220}>
      <LineChart data={data} margin={{ top: 8, right: 16, bottom: 4, left: -8 }}>
        <CartesianGrid {...GRID} strokeDasharray="3 3" />
        <XAxis dataKey="step" {...AXIS} />
        <YAxis {...AXIS} allowDecimals={false} />
        <Tooltip contentStyle={TOOLTIP_STYLE} />
        <Legend wrapperStyle={{ fontSize: 11 }} />
        <Line type="monotone" dataKey="anchors" stroke={COLORS.anchors} strokeWidth={2} dot={{ r: 2 }} />
        <Line type="monotone" dataKey="payload" stroke={COLORS.payload} strokeWidth={2} dot={{ r: 2 }} />
        <Line type="monotone" dataKey="quarantined" stroke={COLORS.quarantined} strokeWidth={2} dot={{ r: 2 }} />
      </LineChart>
    </ResponsiveContainer>
  );
}
