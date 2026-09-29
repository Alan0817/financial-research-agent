import { Check, CircleDotDashed, Wrench } from "lucide-react";

import { formatValue, humanizeToolName } from "../lib/format";
import type { DemoTraceEvent } from "../types/api";


interface ToolTimelineProps {
  trace: DemoTraceEvent[];
}


function TracePayload({ value }: { value: Record<string, unknown> }) {
  const entries = Object.entries(value);

  if (entries.length === 0) {
    return null;
  }

  return (
    <dl className="trace-payload">
      {entries.map(([key, entryValue]) => (
        <div key={key}>
          <dt>{key.replaceAll("_", " ")}</dt>
          <dd>{formatValue(entryValue)}</dd>
        </div>
      ))}
    </dl>
  );
}


export function ToolTimeline({ trace }: ToolTimelineProps) {
  if (trace.length === 0) {
    return null;
  }

  return (
    <section className="tool-timeline" aria-labelledby="timeline-title">
      <div className="subsection-heading">
        <div>
          <p className="eyebrow">Observable execution</p>
          <h3 id="timeline-title">Tool execution timeline</h3>
        </div>
        <p>Provider-neutral trace events; this is not hidden reasoning.</p>
      </div>
      <ol>
        {trace.map((event, index) => {
          const isFinal = event.event === "final_response";
          const isComplete = event.event === "tool_completed";
          const title = isFinal
            ? "Final synthesis returned"
            : event.tool_name
              ? humanizeToolName(event.tool_name)
              : event.event.replaceAll("_", " ");

          return (
            <li key={`${event.event}-${event.tool_name ?? "final"}-${index}`}>
              <span className={`timeline-icon ${isComplete || isFinal ? "timeline-icon--complete" : ""}`}>
                {isFinal || isComplete ? (
                  <Check aria-hidden="true" size={15} />
                ) : (
                  <Wrench aria-hidden="true" size={15} />
                )}
              </span>
              <article>
                <div className="timeline-item__header">
                  <div>
                    <span className="timeline-event">{event.event.replaceAll("_", " ")}</span>
                    <h4>{title}</h4>
                  </div>
                  {event.round ? <span className="round-label">Round {event.round}</span> : null}
                </div>
                {event.status ? <span className="status-label">{event.status}</span> : null}
                {event.arguments ? <TracePayload value={event.arguments} /> : null}
                {event.result_summary ? <TracePayload value={event.result_summary} /> : null}
              </article>
            </li>
          );
        })}
      </ol>
      <div className="timeline-caption">
        <CircleDotDashed aria-hidden="true" size={16} />
        Only sanitized requests, tool completions, and safe result summaries are shown.
      </div>
    </section>
  );
}
