"use client";

import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { AXIS, COLORS, GRID, TOOLTIP_STYLE } from "./theme";
import type { StepMetric } from "@/lib/types";

export function TokenUsageChart({ steps }: { steps: StepMetric[] }) {
  const data = steps.map((s) => ({
    step: s.step,
    input: s.input_tokens,
    output: s.output_tokens,
  }));

  return (
    <ResponsiveContainer width="100%" height={220}>
      <BarChart data={data} margin={{ top: 8, right: 16, bottom: 4, left: -8 }}>
        <CartesianGrid {...GRID} strokeDasharray="3 3" />
        <XAxis dataKey="step" {...AXIS} />
        <YAxis {...AXIS} />
        <Tooltip contentStyle={TOOLTIP_STYLE} cursor={{ fill: "#1a2130" }} />
        <Legend wrapperStyle={{ fontSize: 11 }} />
        <Bar dataKey="input" name="input tokens" fill={COLORS.input} radius={[3, 3, 0, 0]} />
        <Bar dataKey="output" name="output tokens" fill={COLORS.output} radius={[3, 3, 0, 0]} />
      </BarChart>
    </ResponsiveContainer>
  );
}
