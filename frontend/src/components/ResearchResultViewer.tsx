import { CheckCircle2, FileClock, Radio, Wrench } from "lucide-react";

import { EvidenceBadge } from "./EvidenceBadge";
import { KeyFindings } from "./KeyFindings";
import { MarkdownContent } from "./MarkdownContent";
import { formatCapturedAt, humanizeToolName } from "../lib/format";
import type { DemoPresentationResult, ShowcaseScenario } from "../types/api";


interface ResearchResultViewerProps {
  result: DemoPresentationResult;
  scenario?: ShowcaseScenario;
  prompt?: string;
}


export function ResearchResultViewer({ result, scenario, prompt }: ResearchResultViewerProps) {
  const isLive = result.mode === "live";
  const title = scenario?.title ?? "Live research";
  const question = scenario?.example_question ?? prompt ?? "Submitted research question";

  return (
    <article className="research-result" aria-labelledby="result-title">
      <div className="result-header">
        <div>
          <p className="eyebrow">{isLive ? "Live research result" : "Reviewed research result"}</p>
          <h3 id="result-title">{title}</h3>
        </div>
        {isLive ? (
          <span className="live-result-pill">
            <Radio aria-hidden="true" size={15} />
            LIVE RESEARCH
          </span>
        ) : (
          <span className="snapshot-pill">
            <FileClock aria-hidden="true" size={15} />
            Showcase snapshot
          </span>
        )}
      </div>

      <div className="question-block">
        <span className="question-label">{isLive ? "Submitted question" : "Example question"}</span>
        <p>{question}</p>
      </div>

      <div className="answer-panel">
        <div className="answer-panel__label">
          <CheckCircle2 aria-hidden="true" size={18} />
          Research answer
        </div>
        <MarkdownContent content={result.answer} />
      </div>

      <KeyFindings evidence={result.quantitative_evidence} />

      {!isLive ? (
        <div className="snapshot-notice snapshot-notice--compact" role="note">
          <FileClock aria-hidden="true" size={16} />
          <div>
            <strong>Reviewed showcase snapshot</strong>
            <span>
              Captured {formatCapturedAt(scenario?.captured_at)} · Historical example · Not live data
            </span>
          </div>
        </div>
      ) : null}

      <div className="result-summary-grid result-summary-grid--compact">
        <div>
          <span className="metric-label">Evidence</span>
          <div className="badge-row">
            {result.evidence_families.length > 0 ? (
              result.evidence_families.map((family) => <EvidenceBadge family={family} key={family} />)
            ) : (
              <span className="muted-label">Conceptual response</span>
            )}
          </div>
        </div>
        <div>
          <span className="metric-label">Tools</span>
          <div className="tool-chip-list">
            {result.tools_used.length > 0 ? (
              result.tools_used.map((toolName) => (
                <span className="tool-chip" key={toolName}>
                  <Wrench aria-hidden="true" size={14} />
                  {humanizeToolName(toolName)}
                </span>
              ))
            ) : (
              <span className="muted-label">No tools called</span>
            )}
          </div>
        </div>
      </div>
    </article>
  );
}
