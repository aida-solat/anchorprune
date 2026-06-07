"use client";

import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { AXIS, COLORS, GRID, TOOLTIP_STYLE } from "./theme";
import type { StepMetric } from "@/lib/types";

export function ContextGrowthChart({ steps }: { steps: StepMetric[] }) {
  const data = steps.map((s) => ({
    step: s.step,
    context: s.input_tokens,
  }));

  return (
    <ResponsiveContainer width="100%" height={220}>
      <LineChart data={data} margin={{ top: 8, right: 16, bottom: 4, left: -8 }}>
        <CartesianGrid {...GRID} strokeDasharray="3 3" />
        <XAxis dataKey="step" {...AXIS} />
        <YAxis {...AXIS} />
        <Tooltip contentStyle={TOOLTIP_STYLE} />
        <Line
          type="monotone"
          dataKey="context"
          name="context tokens"
          stroke={COLORS.input}
          strokeWidth={2}
          dot={{ r: 3 }}
        />
      </LineChart>
    </ResponsiveContainer>
  );
}
