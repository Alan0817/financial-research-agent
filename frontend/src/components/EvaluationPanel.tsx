import { CheckCircle2, Gauge, Microscope } from "lucide-react";


const retrievers = [
  { name: "Dense", recall: "0.519", width: "52%" },
  { name: "BM25", recall: "0.593", width: "59%" },
  { name: "Hybrid", recall: "0.630", width: "63%" },
  { name: "Hybrid + cross-encoder", recall: "0.685", width: "69%" },
];


export function EvaluationPanel() {
  return (
    <div className="evaluation-layout">
      <div className="benchmark-panel">
        <div className="benchmark-panel__heading">
          <div>
            <p className="eyebrow">30-case retrieval benchmark</p>
            <h3>Evidence ranking, measured</h3>
          </div>
          <Gauge aria-hidden="true" size={24} />
        </div>
        <div className="benchmark-bars">
          {retrievers.map((retriever) => (
            <div className="benchmark-bar" key={retriever.name}>
              <div className="benchmark-bar__label">
                <span>{retriever.name}</span>
                <strong>Recall@10 {retriever.recall}</strong>
              </div>
              <span className="benchmark-bar__track">
                <span className="benchmark-bar__fill" style={{ width: retriever.width }} />
              </span>
            </div>
          ))}
        </div>
        <p className="benchmark-note">
          Retrieval metrics measure manually judged evidence ranking, not financial answer accuracy.
        </p>
      </div>

      <div className="evaluation-facts">
        <article>
          <CheckCircle2 aria-hidden="true" size={22} />
          <strong>177 automated tests</strong>
          <span>Deterministic coverage across agent, retrieval, API, and presentation boundaries.</span>
        </article>
        <article>
          <Microscope aria-hidden="true" size={22} />
          <strong>Trace-driven evaluation</strong>
          <span>Tool routing, provenance, limitations, and retrieval failure modes remain inspectable.</span>
        </article>
      </div>
    </div>
  );
}
