import { AlertTriangle } from "lucide-react";

import { formatValue } from "../lib/format";
import type { DemoLimitation } from "../types/api";


interface StructuredLimitationsProps {
  limitations: DemoLimitation[];
}


export function StructuredLimitations({ limitations }: StructuredLimitationsProps) {
  if (limitations.length === 0) {
    return null;
  }

  return (
    <section className="limitations-panel" aria-labelledby="limitations-title">
      <div className="limitations-panel__heading">
        <AlertTriangle aria-hidden="true" size={18} />
        <h3 id="limitations-title">Structured limitations</h3>
      </div>
      <ul>
        {limitations.map((limitation, index) => (
          <li key={`${limitation.type ?? limitation.code ?? "limitation"}-${index}`}>
            <strong>{limitation.type ?? limitation.code ?? "Limitation"}:</strong>{" "}
            {limitation.message ?? formatValue(limitation.value ?? "A bounded capability limitation was recorded.")}
          </li>
        ))}
      </ul>
    </section>
  );
}
