import {
  BarChart3,
  BrainCircuit,
  ExternalLink,
  FileText,
  Globe2,
  Layers3,
  ShieldCheck,
} from "lucide-react";

import { formatValue, isSafeExternalUrl } from "../lib/format";
import {
  formatCompactNumber,
  formatDate,
  formatDateRange,
  formatMarketPrice,
  formatPercentage,
  formatTechnicalValue,
} from "../lib/quantitativeFormat";
import {
  getAnalyzeMarketResult,
  getRecordValue,
  getStringValue,
  isFiniteNumber,
  isRecord,
} from "../lib/quantitative";
import type {
  DemoPresentationResult,
  QuantitativeEvidence,
  SecEvidence,
  WebEvidence,
} from "../types/api";


interface EvidenceInspectorProps {
  result: DemoPresentationResult;
}

interface MetricEntry {
  label: string;
  value: string;
}

interface MetricGroupProps {
  title: string;
  entries: MetricEntry[];
  icon?: "model";
}


function MetricGroup({ title, entries, icon }: MetricGroupProps) {
  if (entries.length === 0) {
    return null;
  }

  return (
    <section className="quantitative-metric-group">
      <div className="quantitative-metric-group__heading">
        {icon === "model" ? <BrainCircuit aria-hidden="true" size={17} /> : null}
        <h5>{title}</h5>
      </div>
      <dl className="metric-grid">
        {entries.map((entry) => (
          <div key={entry.label}>
            <dt>{entry.label}</dt>
            <dd>{entry.value}</dd>
          </div>
        ))}
      </dl>
    </section>
  );
}


function AnalyzeMarketEvidence({ evidence }: { evidence: QuantitativeEvidence }) {
  const result = getAnalyzeMarketResult(evidence);
  if (!result) {
    return <GenericQuantitativeEvidence evidence={evidence} />;
  }

  const market = getRecordValue(result, "market");
  const latestOhlcv = getRecordValue(market, "latest_ohlcv");
  const period = getRecordValue(result, "period");
  const requestedPeriod = getRecordValue(period, "requested");
  const availablePeriod = getRecordValue(period, "available");
  const technicalAnalysis = getRecordValue(result, "technical_analysis");
  const indicators = getRecordValue(technicalAnalysis, "indicators");
  const risk = getRecordValue(result, "risk");
  const assumptions = getRecordValue(risk, "assumptions");
  const lstm = getRecordValue(result, "lstm_prediction");
  const symbol = getStringValue(result, "symbol");
  const maximumDrawdown = risk?.maximum_drawdown ?? risk?.maxium_drawdown;

  const marketEntries = compactEntries([
    entry("Symbol", symbol),
    dateRangeEntry("Requested period", requestedPeriod),
    dateRangeEntry("Available period", availablePeriod),
    entry("Observations", market?.observations),
    numberEntry("Latest close", latestOhlcv?.Close, (value) => formatMarketPrice(value, symbol)),
    numberEntry("Volume", latestOhlcv?.Volume, formatCompactNumber),
    numberEntry("Period return", market?.period_return, (value) => formatPercentage(value, { signed: true })),
  ]);

  const technicalEntries = compactEntries([
    dateEntry("Indicator timestamp", technicalAnalysis?.timestamp),
    numberEntry("RSI", indicators?.RSI, (value) => formatTechnicalValue(value, 2)),
    numberEntry("MACD", indicators?.MACD, (value) => formatTechnicalValue(value, 2)),
    numberEntry("MACD signal", indicators?.MACD_Signal, (value) => formatTechnicalValue(value, 2)),
    numberEntry("MA-7", indicators?.MA_7, (value) => formatMarketPrice(value, symbol)),
    numberEntry("MA-30", indicators?.MA_30, (value) => formatMarketPrice(value, symbol)),
    numberEntry("Volatility", indicators?.Volatility, formatPercentage),
  ]);

  const riskEntries = compactEntries([
    entry("Observations", risk?.observations),
    entry("Annualization factor", risk?.annualization_factor),
    numberEntry("Annualized volatility", risk?.annualized_volatility, formatPercentage),
    numberEntry("Sharpe ratio", risk?.sharpe_ratio, (value) => formatTechnicalValue(value, 2)),
    numberEntry("Maximum drawdown", maximumDrawdown, formatPercentage),
    numberEntry("Cumulative return", risk?.cumulative_return, (value) => formatPercentage(value, { signed: true })),
    entry("Observation frequency", assumptions?.observation_frequency),
    numberEntry("Risk-free rate", assumptions?.risk_free_rate, formatPercentage),
    entry("Sharpe annualization", assumptions?.sharpe_annualization),
  ]);

  const modelEntries = lstm
    ? compactEntries([
        entry("Status", lstm.status),
        dateEntry("Model timestamp", lstm.timestamp),
        numberEntry("Probability of configured target", lstm.probability_up, formatPercentage),
        entry("Prediction label", lstm.prediction),
        entry("Raw threshold label", lstm.raw_signal),
        entry("Target definition", lstm.target_definition),
        entry("Probability definition", lstm.probability_up_definition),
        entry("Raw signal definition", lstm.raw_signal_definition),
        booleanEntry("Raw signal is exposure", lstm.raw_signal_is_exposure, "No — not an exposure"),
      ])
    : [];

  return (
    <article className="quantitative-card">
      <span className="evidence-kicker">{evidence.tool_name?.replaceAll("_", " ") ?? "Tool result"}</span>
      <div className="quantitative-schema-groups">
        <MetricGroup entries={marketEntries} title="Market" />
        <MetricGroup entries={technicalEntries} title="Technical analysis" />
        <MetricGroup entries={riskEntries} title="Risk" />
        <MetricGroup entries={modelEntries} icon="model" title="ML prediction" />
      </div>
    </article>
  );
}


function GenericQuantitativeEvidence({ evidence }: { evidence: QuantitativeEvidence }) {
  const source = evidence.result ?? evidence;
  const entries = flattenGenericEntries(source);

  if (entries.length === 0) {
    return <p className="empty-evidence">This reviewed tool result did not expose compact metrics.</p>;
  }

  return (
    <article className="quantitative-card">
      <span className="evidence-kicker">{evidence.tool_name?.replaceAll("_", " ") ?? "Tool result"}</span>
      <MetricGroup entries={entries} title="Structured result" />
    </article>
  );
}


function flattenGenericEntries(value: unknown, prefix = "", depth = 0): MetricEntry[] {
  if (depth >= 6 || !isRecord(value)) {
    return prefix ? [{ label: prefix, value: formatValue(value) }] : [];
  }

  return Object.entries(value).flatMap(([key, nestedValue]) => {
    const label = prefix ? `${prefix} · ${key.replaceAll("_", " ")}` : key.replaceAll("_", " ");
    return flattenGenericEntries(nestedValue, label, depth + 1);
  });
}


function entry(label: string, value: unknown): MetricEntry | null {
  if (value === null || value === undefined || value === "") {
    return null;
  }

  return { label, value: formatValue(value) };
}


function numberEntry(
  label: string,
  value: unknown,
  formatter: (value: number) => string,
): MetricEntry | null {
  if (!isFiniteNumber(value)) {
    return null;
  }

  return { label, value: formatter(value) };
}


function dateEntry(label: string, value: unknown): MetricEntry | null {
  if (typeof value !== "string" || !value) {
    return null;
  }

  return { label, value: formatDate(value) };
}


function dateRangeEntry(label: string, value: Record<string, unknown> | undefined): MetricEntry | null {
  const start = value?.start;
  const end = value?.end;
  if (typeof start !== "string" || typeof end !== "string") {
    return null;
  }

  return { label, value: formatDateRange(start, end) };
}


function booleanEntry(
  label: string,
  value: unknown,
  falseLabel: string,
): MetricEntry | null {
  if (typeof value !== "boolean") {
    return null;
  }

  return { label, value: value ? "Yes" : falseLabel };
}


function compactEntries(entries: Array<MetricEntry | null>): MetricEntry[] {
  return entries.filter((entry): entry is MetricEntry => entry !== null);
}


function SecEvidenceCard({ evidence }: { evidence: SecEvidence }) {
  return (
    <article className="evidence-card evidence-card--sec">
      <div className="evidence-card__header">
        <div>
          <span className="evidence-kicker">SEC filing evidence</span>
          <h4>
            {evidence.ticker ?? "Issuer"} {evidence.document_type ?? "Filing"}
          </h4>
        </div>
        {evidence.rank ? <span className="rank-label">Rank {evidence.rank}</span> : null}
      </div>
      <dl className="provenance-grid">
        <div>
          <dt>Filed</dt>
          <dd>{evidence.filing_date ?? "Not available"}</dd>
        </div>
        <div>
          <dt>Section</dt>
          <dd>{evidence.section_title ?? evidence.section ?? "Not available"}</dd>
        </div>
        {evidence.chunk_id ? (
          <div>
            <dt>Evidence ID</dt>
            <dd className="mono-value">{evidence.chunk_id}</dd>
          </div>
        ) : null}
      </dl>
      {evidence.excerpt ? <p className="evidence-excerpt">{evidence.excerpt}</p> : null}
      {isSafeExternalUrl(evidence.source_url) ? (
        <a className="source-link" href={evidence.source_url} rel="noreferrer" target="_blank">
          Read official filing <ExternalLink aria-hidden="true" size={15} />
        </a>
      ) : null}
    </article>
  );
}


function WebEvidenceCard({ evidence }: { evidence: WebEvidence }) {
  return (
    <article className="evidence-card evidence-card--web">
      <div className="evidence-card__header">
        <div>
          <span className="evidence-kicker">Web search evidence</span>
          <h4>{evidence.title ?? "Source result"}</h4>
        </div>
        {evidence.rank ? <span className="rank-label">Rank {evidence.rank}</span> : null}
      </div>
      <p className="source-meta">
        {evidence.source ?? "Source not specified"}
        {evidence.published_at ? ` · ${evidence.published_at}` : ""}
      </p>
      {evidence.snippet ? <p className="evidence-excerpt">{evidence.snippet}</p> : null}
      {isSafeExternalUrl(evidence.url) ? (
        <a className="source-link" href={evidence.url} rel="noreferrer" target="_blank">
          Open source <ExternalLink aria-hidden="true" size={15} />
        </a>
      ) : null}
    </article>
  );
}


export function EvidenceInspector({ result }: EvidenceInspectorProps) {
  const hasEvidence =
    result.quantitative_evidence.length > 0 ||
    result.sec_evidence.length > 0 ||
    result.web_evidence.length > 0;

  if (!hasEvidence) {
    return null;
  }

  return (
    <section className="evidence-inspector" aria-labelledby="evidence-inspector-title">
      <div className="subsection-heading">
        <div>
          <p className="eyebrow">Inspectable artifacts</p>
          <h3 id="evidence-inspector-title">Evidence inspector</h3>
        </div>
        <p>Structured tool outputs retain their source-specific provenance.</p>
      </div>

      {result.quantitative_evidence.length > 0 ? (
        <div className="evidence-group">
          <div className="evidence-group__heading">
            <BarChart3 aria-hidden="true" size={19} />
            <h4>Quantitative evidence</h4>
          </div>
          <div className="quantitative-list">
            {result.quantitative_evidence.map((evidence, index) => (
              <AnalyzeMarketEvidence evidence={evidence} key={`${evidence.tool_name ?? "metrics"}-${index}`} />
            ))}
          </div>
        </div>
      ) : null}

      {result.sec_evidence.length > 0 ? (
        <div className="evidence-group">
          <div className="evidence-group__heading">
            <FileText aria-hidden="true" size={19} />
            <h4>SEC filing evidence</h4>
          </div>
          <div className="evidence-list">
            {result.sec_evidence.map((evidence, index) => (
              <SecEvidenceCard evidence={evidence} key={evidence.chunk_id ?? index} />
            ))}
          </div>
        </div>
      ) : null}

      {result.web_evidence.length > 0 ? (
        <div className="evidence-group">
          <div className="evidence-group__heading">
            <Globe2 aria-hidden="true" size={19} />
            <h4>Web source evidence</h4>
          </div>
          <div className="evidence-list">
            {result.web_evidence.map((evidence, index) => (
              <WebEvidenceCard evidence={evidence} key={evidence.url ?? index} />
            ))}
          </div>
        </div>
      ) : null}

      {result.sec_citations.length > 0 || result.web_sources.length > 0 ? (
        <div className="provenance-note">
          <Layers3 aria-hidden="true" size={17} />
          <span>
            Evidence and citation metadata are preserved separately from the generated synthesis.
          </span>
        </div>
      ) : null}

      {result.quantitative_evidence.length > 0 ? (
        <div className="quantitative-boundary-note">
          <ShieldCheck aria-hidden="true" size={17} />
          <span>Model labels are structured evidence, not investment recommendations or exposure instructions.</span>
        </div>
      ) : null}
    </section>
  );
}
