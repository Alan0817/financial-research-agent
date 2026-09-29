import { ArrowDown, Database, FileText, Globe2, Scale, SearchCheck } from "lucide-react";


export function ArchitectureDiagram() {
  return (
    <div className="architecture-diagram" aria-label="Financial Research Agent architecture">
      <div className="architecture-provider-row">
        <span>OpenAI</span>
        <span>Gemini</span>
      </div>
      <div className="architecture-node architecture-node--client">User question</div>
      <ArrowDown aria-hidden="true" className="architecture-arrow" size={20} />
      <div className="architecture-node architecture-node--agent">FinancialAnalysisAgent</div>
      <div className="architecture-connector-label">provider-neutral LLMClient</div>
      <ArrowDown aria-hidden="true" className="architecture-arrow" size={20} />
      <div className="architecture-node architecture-node--registry">ToolRegistry</div>
      <div className="architecture-tools-row">
        <div className="architecture-tool architecture-tool--quantitative">
          <Scale aria-hidden="true" size={20} />
          <strong>Quantitative</strong>
          <span>Market · technical · risk · BTC ML</span>
        </div>
        <div className="architecture-tool architecture-tool--document">
          <FileText aria-hidden="true" size={20} />
          <strong>SEC filings</strong>
          <span>Chunked evidence · provenance</span>
        </div>
        <div className="architecture-tool architecture-tool--web">
          <Globe2 aria-hidden="true" size={20} />
          <strong>Current web</strong>
          <span>Search result sources · URLs</span>
        </div>
      </div>
      <div className="architecture-retrieval-row">
        <SearchCheck aria-hidden="true" size={19} />
        <span>Hybrid retrieval</span>
        <span className="architecture-divider">Dense + BM25</span>
        <ArrowDown aria-hidden="true" size={16} />
        <span>RRF</span>
        <ArrowDown aria-hidden="true" size={16} />
        <span>Optional cross-encoder</span>
        <Database aria-hidden="true" size={18} />
      </div>
    </div>
  );
}
