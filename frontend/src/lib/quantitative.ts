import type { QuantitativeEvidence } from "../types/api";

export type AnalyzeMarketResult = Record<string, unknown>;


export interface KeyFinding {
  label: string;
  value: string;
  detail?: string;
  kind: "market" | "technical" | "model";
}


export function getAnalyzeMarketResult(
  evidence: QuantitativeEvidence,
): AnalyzeMarketResult | null {
  if (evidence.tool_name !== "analyze_market" || !isRecord(evidence.result)) {
    return null;
  }

  return evidence.result as AnalyzeMarketResult;
}


export function getAnalyzeMarketEvidence(
  evidence: QuantitativeEvidence[],
): AnalyzeMarketResult | null {
  for (const item of evidence) {
    const result = getAnalyzeMarketResult(item);
    if (result) {
      return result;
    }
  }

  return null;
}


export function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}


export function isFiniteNumber(value: unknown): value is number {
  return typeof value === "number" && Number.isFinite(value);
}


export function getRecordValue(
  record: Record<string, unknown> | undefined,
  key: string,
): Record<string, unknown> | undefined {
  if (!record) {
    return undefined;
  }

  const value = record[key];
  return isRecord(value) ? value : undefined;
}


export function getStringValue(
  record: Record<string, unknown> | undefined,
  key: string,
): string | undefined {
  const value = record?.[key];
  return typeof value === "string" ? value : undefined;
}
