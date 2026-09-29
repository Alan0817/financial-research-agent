import { BrainCircuit, Gauge, TrendingUp } from "lucide-react";

import {
  formatMarketPrice,
  formatPercentage,
  formatProbabilityTarget,
  formatTechnicalValue,
} from "../lib/quantitativeFormat";
import {
  getAnalyzeMarketEvidence,
  getRecordValue,
  getStringValue,
  isFiniteNumber,
  type KeyFinding,
} from "../lib/quantitative";
import type { QuantitativeEvidence } from "../types/api";


interface KeyFindingsProps {
  evidence: QuantitativeEvidence[];
}


export function KeyFindings({ evidence }: KeyFindingsProps) {
  const findings = extractKeyFindings(evidence);

  if (findings.length === 0) {
    return null;
  }

  return (
    <section className="key-findings" aria-labelledby="key-findings-title">
      <div className="key-findings__heading">
        <div>
          <p className="eyebrow">Research summary</p>
          <h4 id="key-findings-title">Key findings</h4>
        </div>
        <span>Derived from structured tool evidence</span>
      </div>
      <div className="key-findings__grid">
        {findings.map((finding) => (
          <article className={`key-finding key-finding--${finding.kind}`} key={finding.label}>
            <FindingIcon kind={finding.kind} />
            <span className="key-finding__label">{finding.label}</span>
            <strong>{finding.value}</strong>
            {finding.detail ? <span className="key-finding__detail">{finding.detail}</span> : null}
          </article>
        ))}
      </div>
    </section>
  );
}


function FindingIcon({ kind }: { kind: KeyFinding["kind"] }) {
  if (kind === "model") {
    return <BrainCircuit aria-hidden="true" size={19} />;
  }

  if (kind === "technical") {
    return <Gauge aria-hidden="true" size={19} />;
  }

  return <TrendingUp aria-hidden="true" size={19} />;
}


function extractKeyFindings(evidence: QuantitativeEvidence[]): KeyFinding[] {
  const result = getAnalyzeMarketEvidence(evidence);
  if (!result) {
    return [];
  }

  const market = getRecordValue(result, "market");
  const latestOhlcv = getRecordValue(market, "latest_ohlcv");
  const technicalAnalysis = getRecordValue(result, "technical_analysis");
  const indicators = getRecordValue(technicalAnalysis, "indicators");
  const lstm = getRecordValue(result, "lstm_prediction");
  const symbol = getStringValue(result, "symbol");
  const latestClose = latestOhlcv?.Close;
  const periodReturn = market?.period_return;
  const rsi = indicators?.RSI;
  const volatility = indicators?.Volatility;
  const probabilityUp = lstm?.probability_up;
  const findings: KeyFinding[] = [];

  if (isFiniteNumber(latestClose)) {
    findings.push({
      label: symbol ? `Latest ${symbol} close` : "Latest close",
      value: formatMarketPrice(latestClose, symbol),
      kind: "market",
    });
  }

  if (isFiniteNumber(periodReturn)) {
    findings.push({
      label: "Captured-period return",
      value: formatPercentage(periodReturn, { signed: true }),
      kind: "market",
    });
  }

  if (isFiniteNumber(rsi)) {
    findings.push({
      label: "RSI",
      value: formatTechnicalValue(rsi, 2),
      kind: "technical",
    });
  }

  if (isFiniteNumber(volatility)) {
    findings.push({
      label: "Technical volatility",
      value: formatPercentage(volatility),
      kind: "technical",
    });
  }

  if (lstm?.status === "available" && isFiniteNumber(probabilityUp)) {
    findings.push({
      label: symbol?.toUpperCase() === "BTC-USD" ? "BTC-specific LSTM" : "LSTM prediction",
      value: formatPercentage(probabilityUp),
      detail: `${formatProbabilityTarget(lstm.target_definition, lstm.probability_up_definition)} · Raw label is not an exposure`,
      kind: "model",
    });
  }

  return findings.slice(0, 5);
}
