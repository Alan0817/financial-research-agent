import { LoaderCircle, Send } from "lucide-react";
import type { FormEventHandler } from "react";


export const LIVE_PROMPT_MAX_LENGTH = 4_000;

const EXAMPLE_PROMPTS = [
  "What does RSI measure and how is it commonly interpreted?",
  "Analyze NVDA market performance and risk from 2024-09-01 to 2024-12-01.",
  "What risks does MSTR disclose regarding custody of its Bitcoin holdings?",
  "What are the latest significant developments related to NVIDIA?",
  "Analyze BTC-USD from 2024-09-01 to 2024-12-01 using the available quantitative and ML capabilities.",
];


interface LiveResearchPanelProps {
  prompt: string;
  isSubmitting: boolean;
  error: string | null;
  onPromptChange: (prompt: string) => void;
  onSubmit: FormEventHandler<HTMLFormElement>;
}


export function LiveResearchPanel({
  prompt,
  isSubmitting,
  error,
  onPromptChange,
  onSubmit,
}: LiveResearchPanelProps) {
  const remainingCharacters = LIVE_PROMPT_MAX_LENGTH - prompt.length;
  const hasPrompt = Boolean(prompt.trim());

  return (
    <section className="live-research-panel" aria-labelledby="live-research-title">
      <div className="live-research-panel__heading">
        <div>
          <p className="eyebrow">Live mode</p>
          <h3 id="live-research-title">Run a local research request</h3>
        </div>
        <span className="live-mode-pill">LIVE RESEARCH</span>
      </div>
      <p className="live-research-panel__description">
        Submit one question to the server-owned Financial Research Agent. Provider, retrieval, and web-search settings remain outside the browser.
      </p>

      <form className="live-research-form" onSubmit={onSubmit}>
        <label htmlFor="live-research-prompt">Research question</label>
        <textarea
          id="live-research-prompt"
          maxLength={LIVE_PROMPT_MAX_LENGTH}
          onChange={(event) => onPromptChange(event.target.value)}
          placeholder="Ask a focused financial research question..."
          required
          rows={5}
          value={prompt}
        />
        <div className="live-research-form__footer">
          <span aria-live="polite">{remainingCharacters.toLocaleString()} characters remaining</span>
          <button className="button button--primary" disabled={!hasPrompt || isSubmitting} type="submit">
            {isSubmitting ? (
              <>
                <LoaderCircle aria-hidden="true" className="live-spinner" size={17} />
                Running research
              </>
            ) : (
              <>
                <Send aria-hidden="true" size={17} />
                Run research
              </>
            )}
          </button>
        </div>
      </form>

      <div className="live-example-prompts">
        <span>Try a local validation prompt</span>
        <div>
          {EXAMPLE_PROMPTS.map((example) => (
            <button
              disabled={isSubmitting}
              key={example}
              onClick={() => onPromptChange(example)}
              type="button"
            >
              {example}
            </button>
          ))}
        </div>
      </div>

      {error ? (
        <div className="live-research-error" role="alert">
          <strong>Live research could not complete.</strong>
          <span>{error}</span>
        </div>
      ) : null}
    </section>
  );
}
