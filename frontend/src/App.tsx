import {
  ArrowDown,
  ArrowRight,
  Bot,
  ChartNoAxesCombined,
  ChevronRight,
  CircleAlert,
  Database,
  FileText,
  GitBranch,
  Github,
  Globe2,
  Layers3,
  SearchCheck,
  ShieldCheck,
} from "lucide-react";
import { type FormEvent, useEffect, useState } from "react";

import { ArchitectureDiagram } from "./components/ArchitectureDiagram";
import { EvaluationPanel } from "./components/EvaluationPanel";
import { EvidenceInspector } from "./components/EvidenceInspector";
import { ResearchResultViewer } from "./components/ResearchResultViewer";
import { LiveResearchPanel } from "./components/LiveResearchPanel";
import { ScenarioCards } from "./components/ScenarioCards";
import { SectionHeading } from "./components/SectionHeading";
import { StructuredLimitations } from "./components/StructuredLimitations";
import { ToolTimeline } from "./components/ToolTimeline";
import { createDemoDataSource, getDemoMode } from "./lib/demoDataSource";
import { DemoApiError } from "./lib/demoError";
import type {
  DemoCapabilities,
  DemoPresentationResult,
  ShowcaseScenario,
} from "./types/api";




type ResearchMode = "showcase" | "live";
const githubUrl = import.meta.env.VITE_GITHUB_URL?.trim() || "https://github.com/";
const demoMode = getDemoMode();
const dataSource = createDemoDataSource(demoMode);


function App() {
  const [capabilities, setCapabilities] = useState<DemoCapabilities | null>(null);
  const [scenarios, setScenarios] = useState<ShowcaseScenario[]>([]);
  const [selectedScenarioId, setSelectedScenarioId] = useState<string | null>(null);
  const [selectedResult, setSelectedResult] = useState<DemoPresentationResult | null>(null);
  const [catalogError, setCatalogError] = useState<string | null>(null);
  const [resultError, setResultError] = useState<string | null>(null);
  const [isLoadingCatalog, setIsLoadingCatalog] = useState(true);
  const [isLoadingResult, setIsLoadingResult] = useState(false);

  const [activeMode, setActiveMode] = useState<ResearchMode>("showcase");
  const [livePrompt, setLivePrompt] = useState("");
  const [submittedLivePrompt, setSubmittedLivePrompt] = useState("");
  const [liveResult, setLiveResult] = useState<DemoPresentationResult | null>(null);
  const [liveError, setLiveError] = useState<string | null>(null);
  const [isSubmittingLiveResearch, setIsSubmittingLiveResearch] = useState(false);
  useEffect(() => {
    let active = true;

    async function loadCatalog() {
      try {
        const [nextCapabilities, response] = await Promise.all([
          dataSource.getCapabilities(),
          dataSource.getShowcaseScenarios(),
        ]);

        if (!active) {
          return;
        }

        setCapabilities(nextCapabilities);
        setScenarios(response.scenarios.filter((scenario) => scenario.showcase_available));
        setSelectedScenarioId(response.scenarios.find((scenario) => scenario.showcase_available)?.scenario_id ?? null);
        if (!nextCapabilities.live_mode_enabled) {
          setActiveMode("showcase");
        }
      } catch (error) {
        if (active) {
          setCatalogError(toUserMessage(error));
        }
      } finally {
        if (active) {
          setIsLoadingCatalog(false);
        }
      }
    }

    void loadCatalog();

    return () => {
      active = false;
    };
  }, []);

  useEffect(() => {
    if (!selectedScenarioId) {
      setSelectedResult(null);
      return;
    }

    const scenarioId = selectedScenarioId;
    let active = true;
    setIsLoadingResult(true);
    setResultError(null);

    async function loadResult() {
      try {
        const result = await dataSource.getShowcaseScenario(scenarioId);
        if (active) {
          setSelectedResult(result);
        }
      } catch (error) {
        if (active) {
          setSelectedResult(null);
          setResultError(toUserMessage(error));
        }
      } finally {
        if (active) {
          setIsLoadingResult(false);
        }
      }
    }

    void loadResult();

    return () => {
      active = false;
    };
  }, [selectedScenarioId]);

  const selectedScenario = scenarios.find((scenario) => scenario.scenario_id === selectedScenarioId) ?? null;

  async function handleLiveResearch(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    const prompt = livePrompt.trim();
    if (!prompt || isSubmittingLiveResearch) {
      return;
    }

    setIsSubmittingLiveResearch(true);
    setLiveError(null);
    setLiveResult(null);

    try {
      const result = await dataSource.runLiveResearch(prompt);
      setSubmittedLivePrompt(prompt);
      setLiveResult(result);
    } catch (error) {
      setLiveError(toUserMessage(error, "Live research could not complete."));
    } finally {
      setIsSubmittingLiveResearch(false);
    }
  }

  return (
    <main>
      <header className="site-header">
        <a className="wordmark" href="#top" aria-label="Financial Research Agent home">
          FRA<span>/</span>
        </a>
        <nav aria-label="Primary navigation">
          <a href="#showcase">Showcase</a>
          <a href="#architecture">Architecture</a>
          <a href="#evaluation">Evaluation</a>
        </nav>
        <a className="github-link" href={githubUrl} rel="noreferrer" target="_blank">
          <Github aria-hidden="true" size={17} />
          GitHub
        </a>
      </header>

      <section className="hero" id="top">
        <div className="hero-copy">
          <p className="eyebrow">Tool-using research system</p>
          <h1>Financial Research Agent</h1>
          <p className="hero-description">
            Evidence-grounded financial research with deterministic quantitative analysis, SEC filing retrieval,
            and current web evidence.
          </p>
          <div className="hero-actions">
            <a className="button button--primary" href="#showcase">
              Explore demo <ArrowDown aria-hidden="true" size={18} />
            </a>
            <a className="button button--secondary" href="#architecture">
              View architecture <GitBranch aria-hidden="true" size={18} />
            </a>
          </div>
          <div className="credibility-row" aria-label="Project technical capabilities">
            <span>OpenAI + Gemini</span>
            <span>Hybrid RAG</span>
            <span>177 automated tests</span>
          </div>
        </div>
        <div className="hero-system-card" aria-label="Evidence-routing overview">
          <div className="system-card__header">
            <span>Research execution</span>
            <span className="system-status">Inspectable</span>
          </div>
          <div className="system-node system-node--agent">
            <Bot aria-hidden="true" size={20} />
            <div>
              <strong>LLM orchestration</strong>
              <span>Routes questions to owned tools</span>
            </div>
          </div>
          <div className="system-branches">
            <div>
              <ChartNoAxesCombined aria-hidden="true" size={18} />
              <span>Quantitative</span>
            </div>
            <div>
              <FileText aria-hidden="true" size={18} />
              <span>SEC filings</span>
            </div>
            <div>
              <Globe2 aria-hidden="true" size={18} />
              <span>Current web</span>
            </div>
          </div>
          <p>Tools provide the evidence. The model orchestrates and synthesizes it.</p>
        </div>
      </section>

      <section className="content-section evidence-systems" aria-labelledby="evidence-systems-title">
        <SectionHeading
          eyebrow="Evidence architecture"
          title="Three distinct evidence systems"
          id="evidence-systems-title"
          description="The LLM does not invent numerical analysis or filing claims. It selects bounded application-owned tools and synthesizes their returned evidence."
        />
        <div className="evidence-system-grid">
          <article>
            <span className="evidence-system-icon evidence-system-icon--quantitative">
              <ChartNoAxesCombined aria-hidden="true" size={22} />
            </span>
            <h3>Quantitative</h3>
            <p>Market data, technical analysis, risk metrics, and a bounded BTC-USD-only ML capability.</p>
          </article>
          <article>
            <span className="evidence-system-icon evidence-system-icon--document">
              <FileText aria-hidden="true" size={22} />
            </span>
            <h3>SEC filings</h3>
            <p>Section-aware retrieval with filing metadata, source provenance, and hybrid dense plus BM25 ranking.</p>
          </article>
          <article>
            <span className="evidence-system-icon evidence-system-icon--web">
              <Globe2 aria-hidden="true" size={22} />
            </span>
            <h3>Current web</h3>
            <p>Source URL and snippet evidence for recent information, deliberately separate from formal filing disclosures.</p>
          </article>
        </div>
      </section>

      <section className="content-section showcase-section" id="showcase" aria-labelledby="showcase-title">
        <SectionHeading
          eyebrow="Interactive showcase"
          title="Review observable research artifacts"
          id="showcase-title"
          description="Choose a reviewed snapshot to inspect the result, its evidence, and its sanitized tool execution. These examples are not live market or web information."
        />

        {capabilities && !capabilities.live_mode_enabled ? (
          <div className="mode-notice" role="status">
            <ShieldCheck aria-hidden="true" size={18} />
            <span>Public demo uses reviewed showcase snapshots. Live research is intentionally disabled.</span>
          </div>
        ) : null}

        {capabilities?.live_mode_enabled ? (
          <div className="research-mode-switch" aria-label="Research mode">
            <button
              aria-pressed={activeMode === "showcase"}
              className={activeMode === "showcase" ? "research-mode-switch__button research-mode-switch__button--active" : "research-mode-switch__button"}
              onClick={() => setActiveMode("showcase")}
              type="button"
            >
              Reviewed Showcase
            </button>
            <button
              aria-pressed={activeMode === "live"}
              className={activeMode === "live" ? "research-mode-switch__button research-mode-switch__button--active" : "research-mode-switch__button"}
              onClick={() => setActiveMode("live")}
              type="button"
            >
              Live Research
            </button>
          </div>
        ) : null}

        {activeMode === "showcase" ? (
          <div>
            {isLoadingCatalog ? <div className="loading-state">Loading reviewed showcase scenarios…</div> : null}
            {catalogError ? <ShowcaseUnavailable message={catalogError} /> : null}
            {!isLoadingCatalog && !catalogError ? (
              <ScenarioCards
                onSelect={setSelectedScenarioId}
                scenarios={scenarios}
                selectedScenarioId={selectedScenarioId}
              />
            ) : null}

            <div className="showcase-detail" aria-live="polite">
              {isLoadingResult ? <div className="loading-state">Loading selected evidence snapshot…</div> : null}
              {resultError ? <ShowcaseUnavailable message={resultError} /> : null}
              {selectedScenario && selectedResult ? (
                <ResearchArtifacts result={selectedResult} scenario={selectedScenario} />
              ) : null}
            </div>
          </div>
        ) : (
          <div>
            <LiveResearchPanel
              error={liveError}
              isSubmitting={isSubmittingLiveResearch}
              onPromptChange={setLivePrompt}
              onSubmit={handleLiveResearch}
              prompt={livePrompt}
            />
            <div className="showcase-detail" aria-live="polite">
              {isSubmittingLiveResearch ? <div className="loading-state">Running live research request…</div> : null}
              {liveResult ? <ResearchArtifacts prompt={submittedLivePrompt} result={liveResult} /> : null}
            </div>
          </div>
        )}
      </section>

      <section className="content-section architecture-section" id="architecture" aria-labelledby="architecture-title">
        <SectionHeading
          eyebrow="System design"
          title="A thin orchestration layer over deterministic evidence"
          id="architecture-title"
          description="Provider adapters translate tool requests, while ToolRegistry remains the execution and validation boundary. Structured traces retain requests, completions, evidence, and limitations without leaking provider SDK objects into the agent layer."
        />
        <ArchitectureDiagram />
      </section>

      <section className="content-section evaluation-section" id="evaluation" aria-labelledby="evaluation-title">
        <SectionHeading
          eyebrow="Evaluation"
          title="Measured system behavior, not a generic confidence claim"
          id="evaluation-title"
          description="Evaluation covers retrieval ranking, tool routing, evidence provenance, capability boundaries, and structured limitations. It does not independently prove every generated sentence is factually correct."
        />
        <EvaluationPanel />
      </section>

      <section className="content-section decisions-section" aria-labelledby="decisions-title">
        <SectionHeading
          eyebrow="Engineering decisions"
          title="Bounded by design"
          id="decisions-title"
        />
        <div className="decisions-grid">
          <article>
            <Bot aria-hidden="true" size={22} />
            <h3>Provider-neutral tool calling</h3>
            <p>OpenAI and Gemini adapters share one application-level tool and trace contract.</p>
          </article>
          <article>
            <Layers3 aria-hidden="true" size={22} />
            <h3>Evidence-source separation</h3>
            <p>Market calculations, SEC filings, and current web sources are intentionally not conflated.</p>
          </article>
          <article>
            <SearchCheck aria-hidden="true" size={22} />
            <h3>Retrieval as an experiment</h3>
            <p>Dense, lexical, hybrid, and reranked retrieval were compared against manually judged evidence.</p>
          </article>
          <article>
            <CircleAlert aria-hidden="true" size={22} />
            <h3>Graceful boundaries</h3>
            <p>Tool results preserve no-results, unavailable, and model-applicability limitations as structured data.</p>
          </article>
        </div>
      </section>

      <section className="content-section failure-section" aria-labelledby="failure-title">
        <SectionHeading
          eyebrow="Failure analysis"
          title="A retrieval failure was treated as an engineering signal"
          id="failure-title"
          description="A live MSTR custody query returned no results despite relevant filing evidence. Trace inspection located a metadata contract mismatch before ranking: the human filter “Risk Factors” did not match the canonical “PART I ITEM 1A” section identifier."
        />
        <div className="failure-flow">
          <span>no_results</span>
          <ChevronRight aria-hidden="true" size={18} />
          <span>trace inspection</span>
          <ChevronRight aria-hidden="true" size={18} />
          <span>section filter mismatch</span>
          <ChevronRight aria-hidden="true" size={18} />
          <span>generic contract correction</span>
          <ChevronRight aria-hidden="true" size={18} />
          <span>regression validation</span>
        </div>
        <p className="failure-footnote">
          Filing-date inference can still be overly restrictive when an LLM adds dates the user did not request. The retrieval layer returns a truthful structured no-results limitation rather than fabricating evidence.
        </p>
      </section>

      <section className="content-section limitations-section" aria-labelledby="limitations-title">
        <SectionHeading eyebrow="Limitations" title="Research tooling with explicit constraints" id="limitations-title" />
        <ul className="limitations-list">
          <li>This is a research and portfolio demonstration, not investment advice or a production trading system.</li>
          <li>Showcase examples are reviewed historical snapshots; current web evidence requires configured live services.</li>
          <li>The SEC evaluation corpus is intentionally small and covers NVDA, AAPL, and MSTR filings.</li>
          <li>The LSTM is experimental, applies only to BTC-USD, and does not predict equities such as MSTR or NVDA.</li>
        </ul>
      </section>

      <footer>
        <span>Financial Research Agent</span>
        <span>React · TypeScript · FastAPI · deterministic tools · provenance</span>
        <a href={githubUrl} rel="noreferrer" target="_blank">
          GitHub <ArrowRight aria-hidden="true" size={15} />
        </a>
      </footer>
    </main>
  );
}


interface ResearchArtifactsProps {
  result: DemoPresentationResult;
  scenario?: ShowcaseScenario;
  prompt?: string;
}


function ResearchArtifacts({ result, scenario, prompt }: ResearchArtifactsProps) {
  return (
    <>
      <ResearchResultViewer prompt={prompt} result={result} scenario={scenario} />
      <EvidenceInspector result={result} />
      <ToolTimeline trace={result.trace} />
      <StructuredLimitations limitations={result.limitations} />
    </>
  );
}


function ShowcaseUnavailable({ message }: { message: string }) {
  const heading = demoMode === "static" ? "Showcase data unavailable" : "Showcase API unavailable";

  return (
    <div className="api-error" role="alert">
      <CircleAlert aria-hidden="true" size={20} />
      <div>
        <strong>{heading}</strong>
        <p>{message}</p>
      </div>
    </div>
  );
}


function toUserMessage(error: unknown, fallback = "The demo API could not load this resource."): string {
  if (error instanceof DemoApiError) {
    return error.message;
  }

  return fallback;
}


export default App;
