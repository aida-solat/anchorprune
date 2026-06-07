// Shared chart styling for the dark dashboard shell.

export const AXIS = { stroke: "#8a97ad", fontSize: 11 } as const;
export const GRID = { stroke: "#252e40" } as const;

export const TOOLTIP_STYLE = {
  background: "#121722",
  border: "1px solid #252e40",
  borderRadius: 8,
  color: "#e6edf6",
  fontSize: 12,
} as const;

export const COLORS = {
  input: "#5b8cff",
  output: "#34d399",
  anchors: "#fbbf24",
  payload: "#60a5fa",
  quarantined: "#fb7185",
  active: "#34d399",
  compressed: "#8a97ad",
  evicted: "#fbbf24",
} as const;
