import { type RefObject } from "react";
import { ArrowRight, Clock, Info, Star, Zap } from "lucide-react";
import { AGENT_CSS_VAR, AGENT_DEFS, RECENT_RESEARCH, type RecentResearch } from "../data/demo";
import { Segmented, type Depth, type ReportStyle } from "./TopBar";

export default function Composer({
  query,
  setQuery,
  onRun,
  onRunLive,
  inputRef,
  onSelectRecent,
  depth,
  setDepth,
  style,
  setStyle,
}: {
  query: string;
  setQuery: (q: string) => void;
  onRun: () => void;
  onRunLive: () => void;
  inputRef: RefObject<HTMLInputElement | null>;
  onSelectRecent: (entry: RecentResearch) => void;
  depth: Depth;
  setDepth: (d: Depth) => void;
  style: ReportStyle;
  setStyle: (s: ReportStyle) => void;
}) {
  const examples = RECENT_RESEARCH.slice(0, 3);

  return (
    <div className="mx-auto w-full max-w-[680px] px-4 pb-10 pt-[9vh] sm:px-6">
      <p className="mb-2 flex items-center gap-2 text-[0.68rem] font-extrabold uppercase tracking-[0.16em] text-muted2">
        <span className="h-1.5 w-1.5 rounded-full bg-emerald" />
        New research
      </p>
      <h2 className="font-display text-[1.7rem] font-bold leading-[1.15] tracking-[-0.01em] sm:text-[2rem]">
        What do you want to <span className="text-emeraldink">research</span>?
      </h2>
      <p className="mt-2 text-[0.88rem] leading-relaxed text-muted">
        The crew searches the live web, cross-checks every claim and writes a fully cited report.
      </p>

      {/* query input */}
      <form
        className="mt-5"
        onSubmit={(e) => {
          e.preventDefault();
          onRun();
        }}
      >
        <div className="flex items-center gap-2 rounded-2xl border border-muted/25 bg-panel p-1.5 shadow-[0_18px_50px_rgba(0,0,0,0.35)] transition focus-within:border-emerald/60">
          <label htmlFor="composer-input" className="sr-only">
            Research question
          </label>
          <input
            id="composer-input"
            ref={inputRef}
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Ask a research question…"
            data-testid="composer-input"
            className="h-11 min-w-0 flex-1 bg-transparent px-3 text-[0.95rem] text-ink outline-none placeholder:text-muted2"
          />
          <button
            type="submit"
            data-testid="composer-run-button"
            className="flex h-11 shrink-0 items-center gap-1.5 rounded-xl bg-emerald px-4 text-[0.88rem] font-bold text-[#06231A] shadow-[0_8px_20px_rgba(0,217,122,0.25)] transition hover:bg-emeraldsoft"
          >
            Run <ArrowRight size={16} strokeWidth={2.5} />
          </button>
        </div>
      </form>

      {/* live research */}
      <div className="mt-3 flex flex-wrap items-center gap-2">
        <button
          type="button"
          onClick={onRunLive}
          data-testid="composer-run-live-button"
          className="flex h-10 items-center gap-2 rounded-xl border border-emerald/60 bg-emerald/[0.12] px-4 text-[0.85rem] font-bold text-emeraldink transition hover:bg-emerald/[0.22]"
        >
          <Zap size={15} strokeWidth={2.5} /> Run live research
        </button>
        <span className="text-[0.75rem] text-muted2">Live research uses Gemini + Tavily — needs keys in Vercel.</span>
      </div>

      {/* depth + style (shown here below lg; top bar carries them on desktop) */}
      <div className="mt-3 flex flex-wrap items-center gap-4 lg:hidden">
        <Segmented label="Depth" options={["Quick", "Standard", "Deep"] as const} value={depth} onChange={setDepth} />
        <Segmented
          label="Style"
          options={["Executive Brief", "Detailed Report", "Technical Analysis"] as const}
          value={style}
          onChange={setStyle}
          shortLabels={{ "Executive Brief": "Brief", "Detailed Report": "Detailed", "Technical Analysis": "Technical" }}
        />
      </div>

      {/* example questions */}
      <div className="mt-4">
        <div className="mb-2 text-[0.68rem] font-extrabold uppercase tracking-[0.14em] text-muted2">Try one</div>
        <div className="flex flex-col gap-2">
          {examples.map((ex) => (
            <button
              key={ex.title}
              type="button"
              onClick={() => setQuery(ex.question)}
              data-testid={`example-chip-${ex.title}`}
              className="rounded-xl border border-muted/[0.18] bg-panel/60 px-3.5 py-2.5 text-left text-[0.85rem] font-medium text-ink transition hover:border-emerald/60 hover:bg-panel"
            >
              {ex.question}
            </button>
          ))}
        </div>
      </div>

      {/* how the crew works — one line, factual */}
      <p className="mt-5 flex flex-wrap items-center gap-x-3 gap-y-1 text-[0.75rem] text-muted">
        {AGENT_DEFS.map((a) => (
          <span key={a.id} className="inline-flex items-center gap-1.5">
            <span className="h-2 w-2 rounded-full" style={{ background: AGENT_CSS_VAR[a.id] }} />
            <b style={{ color: AGENT_CSS_VAR[a.id] }}>{a.name}</b> {a.role.toLowerCase()}
          </span>
        ))}
      </p>

      {/* recent research */}
      <div className="mt-7">
        <div className="mb-1.5 text-[0.68rem] font-extrabold uppercase tracking-[0.14em] text-muted2">
          Recent research
        </div>
        <ul className="divide-y divide-muted/[0.10] rounded-2xl border border-muted/[0.14] bg-panel/50">
          {RECENT_RESEARCH.map((entry) => (
            <li key={entry.title}>
              <button
                type="button"
                onClick={() => onSelectRecent(entry)}
                className="flex w-full items-center gap-3 px-4 py-3 text-left transition hover:bg-ink/[0.04]"
              >
                <span className="min-w-0 flex-1">
                  <span className="flex items-center gap-1.5 truncate text-[0.88rem] font-semibold">
                    {entry.title}
                    {entry.saved && <Star size={12} className="shrink-0 fill-goldtext text-goldtext" />}
                  </span>
                  <span className="mt-0.5 flex items-center gap-1 text-[0.7rem] text-muted2">
                    <Clock size={11} /> {entry.date} · {entry.words.toLocaleString()} words · {entry.sources} sources
                  </span>
                </span>
                <ArrowRight size={15} className="shrink-0 text-muted2" />
              </button>
            </li>
          ))}
        </ul>
      </div>

      {/* demo note */}
      <p className="mt-5 flex items-start gap-2 text-[0.75rem] leading-relaxed text-muted2">
        <Info size={13} className="mt-0.5 shrink-0" />
        Demo mode — the crew runs on sample data for the AI coding assistant market in 2026.
        Live research needs Gemini + Tavily keys.
      </p>
    </div>
  );
}
