export type EvidenceFamily = "quantitative" | "document" | "web";

export interface DemoCapabilities {
  showcase_available: boolean;
  live_mode_enabled: boolean;
  presentation_schema_version: string;
  evidence_families: EvidenceFamily[];
  showcase_scenario_count: number;
}

export interface ShowcaseScenario {
  scenario_id: string;
  title: string;
  short_description: string;
  category: string;
  example_question: string;
  expected_evidence_families: EvidenceFamily[];
  showcase_available: boolean;
  captured_at: string | null;
  snapshot_notice: string;
  tags: string[];
}

export interface DemoTraceEvent {
  event: "tool_requested" | "tool_completed" | "final_response" | string;
  round?: number;
  tool_name?: string;
  arguments?: Record<string, unknown>;
  status?: string;
  result_summary?: Record<string, unknown>;
}

export interface QuantitativeEvidence {
  tool_name?: string;
  result?: unknown;
  [key: string]: unknown;
}

export interface SecEvidence {
  rank?: number;
  score?: number;
  chunk_id?: string;
  document_id?: string;
  ticker?: string;
  company?: string;
  document_type?: string;
  filing_date?: string;
  period_end?: string;
  section?: string;
  section_title?: string;
  source?: string;
  source_url?: string;
  excerpt?: string;
}

export interface WebEvidence {
  rank?: number;
  title?: string;
  url?: string;
  snippet?: string;
  source?: string | null;
  published_at?: string | null;
}

export interface SecCitation {
  chunk_id?: string;
  document_id?: string;
  ticker?: string;
  company?: string;
  document_type?: string;
  filing_date?: string;
  section?: string;
  section_title?: string;
  source?: string;
  source_url?: string;
}

export interface WebSource {
  title?: string;
  url?: string;
  source?: string | null;
  published_at?: string | null;
}

export interface DemoLimitation {
  type?: string;
  code?: string;
  message?: string;
  value?: unknown;
  [key: string]: unknown;
}

export interface DemoPresentationResult {
  schema_version: string;
  mode: "showcase" | "live" | string;
  answer: string;
  tools_used: string[];
  evidence_families: EvidenceFamily[];
  trace: DemoTraceEvent[];
  quantitative_evidence: QuantitativeEvidence[];
  sec_evidence: SecEvidence[];
  web_evidence: WebEvidence[];
  sec_citations: SecCitation[];
  web_sources: WebSource[];
  limitations: DemoLimitation[];
  metadata: Record<string, unknown>;
}

export interface ScenarioListResponse {
  scenarios: ShowcaseScenario[];
}
