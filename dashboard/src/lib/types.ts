// Types mirror the AnchorPrune v0.4 FastAPI response shapes exactly.
// The dashboard is read-only: these describe what the API returns, nothing more.

export type AnchorClass = "system" | "domain" | "runtime";
export type AnchorPriority = "critical" | "high" | "medium" | "low";
export type AnchorStatus = "approved" | "quarantined" | "expired";
export type PruningState = "active" | "compressed" | "quarantined" | "evicted";

export interface Anchor {
  id: string;
  content: string;
  anchor_class: AnchorClass;
  anchor_type: string;
  priority: AnchorPriority;
  source: string;
  weight: number;
  status: AnchorStatus;
  evidence_refs: string[];
  created_at: string;
  expires?: string | null;
  reason?: string | null;
  metadata?: Record<string, unknown>;
}

export interface PayloadBlock {
  id: string;
  block_type: string;
  content: string;
  linked_anchor_ids: string[];
  evidence_refs: string[];
  utility_score: number;
  pruning_state: PruningState;
  quarantined: boolean;
  compressed: boolean;
  evicted: boolean;
  decision_impact: number;
  obsolete: boolean;
  conflict_severity: number;
  created_at: string;
  step_index: number;
  token_estimate: number;
  metadata?: Record<string, unknown>;
}

export interface Milestone {
  id: string;
  stage: string;
  finding: string;
  confidence: number;
  linked_anchor_ids: string[];
  linked_block_ids: string[];
  evidence_refs: string[];
  created_at: string;
  step_index: number;
  metadata?: Record<string, unknown>;
}

export type ConflictKind = "system_anchor" | "domain_anchor" | "payload";

export interface ConflictEdge {
  id: string;
  source_ref: string;
  target_ref: string;
  kind: ConflictKind;
  severity: number;
  critical: boolean;
  reason?: string | null;
}

// ---- API envelope shapes --------------------------------------------------

export interface HealthResponse {
  status: string;
  version: string;
}

export interface RunSummary {
  run_id: string;
  goal: string;
  domain: string;
  status: string;
  config_name?: string | null;
  metadata?: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}

export interface RunListResponse {
  runs: RunSummary[];
  count: number;
}

export interface GovernedState {
  run_id: string;
  goal: string;
  domain: string;
  step_index: number;
  anchors: Anchor[];
  payload_blocks: PayloadBlock[];
  milestones: Milestone[];
  conflict_edges: ConflictEdge[];
  payload_block_count: number;
}

export interface AuditEvent {
  event_type: string;
  step_index: number;
  payload: Record<string, unknown>;
  created_at: string;
}

export interface AuditResponse {
  run_id: string;
  events: AuditEvent[];
}

export interface StepMetric {
  step: number;
  input_tokens: number;
  output_tokens: number;
  anchors: number;
  payload_blocks: number;
  quarantined: number;
}

export interface MetricsSummary {
  total_steps: number;
  total_input_tokens: number;
  total_output_tokens: number;
  max_context_size: number;
}

export interface MetricsResponse {
  run_id: string;
  steps: StepMetric[];
  summary: MetricsSummary;
}
