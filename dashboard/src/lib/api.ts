// Read-only client for the AnchorPrune v0.4 FastAPI service.
// The dashboard only GETs; it never mutates governed state.

import type {
  AuditResponse,
  GovernedState,
  HealthResponse,
  MetricsResponse,
  RunListResponse,
  RunSummary,
} from "./types";

export const API_BASE_URL =
  process.env.NEXT_PUBLIC_ANCHORPRUNE_API_URL ?? "http://127.0.0.1:8000";

async function getJSON<T>(path: string): Promise<T> {
  let res: Response;
  try {
    res = await fetch(`${API_BASE_URL}${path}`, { cache: "no-store" });
  } catch {
    throw new Error(
      `Could not reach the AnchorPrune API at ${API_BASE_URL}. Is \`anchorprune serve\` running?`,
    );
  }
  if (!res.ok) {
    throw new Error(`GET ${path} failed (${res.status} ${res.statusText})`);
  }
  return (await res.json()) as T;
}

export function getHealth(): Promise<HealthResponse> {
  return getJSON<HealthResponse>("/health");
}

export async function getRuns(): Promise<RunSummary[]> {
  const data = await getJSON<RunListResponse>("/runs");
  return data.runs;
}

export function getRun(runId: string): Promise<RunSummary> {
  return getJSON<RunSummary>(`/runs/${encodeURIComponent(runId)}`);
}

export function getRunState(runId: string): Promise<GovernedState> {
  return getJSON<GovernedState>(`/runs/${encodeURIComponent(runId)}/state`);
}

export function getRunAudit(runId: string): Promise<AuditResponse> {
  return getJSON<AuditResponse>(`/runs/${encodeURIComponent(runId)}/audit`);
}

export function getRunMetrics(runId: string): Promise<MetricsResponse> {
  return getJSON<MetricsResponse>(`/runs/${encodeURIComponent(runId)}/metrics`);
}
