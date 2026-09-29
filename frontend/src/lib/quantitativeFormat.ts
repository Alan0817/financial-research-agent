import { isFiniteNumber } from "./quantitative";


export function formatPercentage(value: unknown, options: { signed?: boolean } = {}): string {
  if (!isFiniteNumber(value)) {
    return "Not available";
  }

  const prefix = options.signed && value > 0 ? "+" : "";
  return `${prefix}${(value * 100).toFixed(2)}%`;
}


export function formatTechnicalValue(value: unknown, decimals = 2): string {
  if (!isFiniteNumber(value)) {
    return "Not available";
  }

  return value.toFixed(decimals);
}


export function formatMarketPrice(value: unknown, symbol?: string): string {
  if (!isFiniteNumber(value)) {
    return "Not available";
  }

  if (symbol?.toUpperCase().endsWith("-USD")) {
    return new Intl.NumberFormat("en-US", {
      style: "currency",
      currency: "USD",
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    }).format(value);
  }

  return formatTechnicalValue(value, 2);
}


export function formatCompactNumber(value: unknown): string {
  if (!isFiniteNumber(value)) {
    return "Not available";
  }

  return new Intl.NumberFormat("en-US", {
    notation: "compact",
    maximumFractionDigits: 2,
  }).format(value);
}


export function formatDate(value: unknown): string {
  if (typeof value !== "string" || !value) {
    return "Not available";
  }

  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }

  return new Intl.DateTimeFormat("en", {
    dateStyle: "medium",
    timeZone: "UTC",
  }).format(date);
}


export function formatDateRange(start: unknown, end: unknown): string {
  if (typeof start !== "string" || typeof end !== "string") {
    return "Not available";
  }

  return `${formatDate(start)} to ${formatDate(end)}`;
}


export function formatProbabilityTarget(
  targetDefinition: unknown,
  fallbackDefinition: unknown,
): string {
  if (typeof targetDefinition === "string" && targetDefinition) {
    return targetDefinition.replace(/^Target = 1 when\s*/i, "P(").replace(/\.$/, ")");
  }

  if (typeof fallbackDefinition === "string" && fallbackDefinition) {
    return fallbackDefinition;
  }

  return "Probability of configured target";
}
