import type { EvidenceFamily } from "../types/api";


export const evidenceFamilyLabels: Record<EvidenceFamily, string> = {
  quantitative: "Quantitative",
  document: "SEC filing",
  web: "Current web",
};


export function isSafeExternalUrl(value: string | undefined): value is string {
  if (!value) {
    return false;
  }

  try {
    const url = new URL(value);
    return url.protocol === "https:" || url.protocol === "http:";
  } catch {
    return false;
  }
}


export function formatCapturedAt(value: string | null | undefined): string {
  if (!value) {
    return "Capture date not available";
  }

  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }

  return new Intl.DateTimeFormat("en", {
    dateStyle: "medium",
    timeStyle: "short",
    timeZone: "UTC",
  }).format(date);
}


export function formatValue(value: unknown): string {
  if (value === null || value === undefined || value === "") {
    return "Not available";
  }

  if (typeof value === "number") {
    return Number.isInteger(value) ? value.toString() : value.toFixed(4);
  }

  if (typeof value === "boolean") {
    return value ? "Yes" : "No";
  }

  if (typeof value === "string") {
    return value;
  }

  const serialized = JSON.stringify(value);
  return serialized.length > 180 ? `${serialized.slice(0, 177)}...` : serialized;
}


export function humanizeToolName(value: string): string {
  return value.replaceAll("_", " ");
}
