import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { X } from "lucide-react";
import TopBar, { type Depth, type ReportStyle } from "./components/TopBar";
import Sidebar, { type NavView } from "./components/Sidebar";
import Composer from "./components/Composer";
import ActivityRail from "./components/ActivityRail";
import AgentDock, { type FeedLine } from "./components/AgentDock";
import LiveSources from "./components/LiveSources";
import ReportWindow from "./components/ReportWindow";
import LibraryView from "./components/LibraryView";
import {
  AGENT_CSS_VAR,
  DEMO_QUERY,
  DEMO_SOURCES,
  RECENT_RESEARCH,
  type AgentId,
  type AgentStatus,
  type DemoSource,
  type RecentResearch,
  type ReportData,
} from "./data/demo";
import { api, isKeysError, type LiveSource } from "./lib/live";
import { parseReportMarkdown } from "./lib/report";
import { applyTheme, resolveTheme, type Theme } from "./lib/theme";

const IDLE_STATUS: Record<AgentId, AgentStatus> = { scout: "idle", analyst: "idle", verifier: "idle", writer: "idle" };

interface KpiData {
  sources: number;
  claims: number;
  findings: number;
  sections: number;
}

const IDLE_KPIS: KpiData = { sources: 0, claims: 0, findings: 0, sections: 0 };

interface RunEvent {
  at: number;
  apply: (s: RunState) => Partial<RunState>;
}

interface RunState {
  status: Record<AgentId, AgentStatus>;
  feed: FeedLine[];
  visibleSources: number;
  visibleSections: number;
  flagged: boolean;
  kpis: KpiData;
}

function buildTimeline(): RunEvent[] {
  const events: RunEvent[] = [];
  let feedId = 0;
  const line = (agent: string, color: string, text: string, at: number): FeedLine => ({
    id: ++feedId,
    agent,
    color,
    text,
    at,
  });

  // t = 0 — SCOUT starts
  events.push({
    at: 0,
    apply: (s) => ({
      status: { ...s.status, scout: "working" },
      feed: [...s.feed, line("SCOUT", AGENT_CSS_VAR.scout, "is now working…", 0)],
    }),
  });

  // Sources appear one by one while SCOUT works
  DEMO_SOURCES.forEach((_, i) => {
    events.push({
      at: 900 + i * 700,
      apply: (s) => ({
        visibleSources: i + 1,
        kpis: { ...s.kpis, sources: i + 1 },
      }),
    });
  });

  // SCOUT done → ANALYST working
  events.push({
    at: 6200,
    apply: (s) => ({
      status: { ...s.status, scout: "done", analyst: "working" },
      feed: [
        ...s.feed,
        line("SCOUT", AGENT_CSS_VAR.scout, "finished — Web Scout complete ✓", 6200),
        line("ANALYST", AGENT_CSS_VAR.analyst, "is now working…", 6200),
      ],
    }),
  });

  // ANALYST done → VERIFIER working
  events.push({
    at: 10200,
    apply: (s) => ({
      status: { ...s.status, analyst: "done", verifier: "working" },
      feed: [
        ...s.feed,
        line("ANALYST", AGENT_CSS_VAR.analyst, "finished — Insight Analyst complete ✓", 10200),
        line("VERIFIER", AGENT_CSS_VAR.verifier, "is now working…", 10200),
      ],
    }),
  });

  // VERIFIER flags one single-sourced item
  events.push({
    at: 12300,
    apply: (s) => ({
      flagged: true,
      feed: [
        ...s.feed,
        line("VERIFIER", AGENT_CSS_VAR.verifier, "flagged Finding 1 — single-sourced (GitHub Copilot only)", 12300),
      ],
    }),
  });

  // VERIFIER done → WRITER working
  events.push({
    at: 14000,
    apply: (s) => ({
      status: { ...s.status, verifier: "done", writer: "working" },
      kpis: { ...s.kpis, claims: 8 },
      feed: [
        ...s.feed,
        line("VERIFIER", AGENT_CSS_VAR.verifier, "finished — Fact Checker complete ✓", 14000),
        line("WRITER", AGENT_CSS_VAR.writer, "is now working…", 14000),
      ],
    }),
  });

  // Report streams in section by section
  const sectionStarts = [15600, 16400, 17300, 18200, 19000, 19700, 20300, 20900];
  sectionStarts.forEach((at, i) => {
    events.push({
      at,
      apply: (s) => ({
        visibleSections: i + 1,
        kpis: {
          ...s.kpis,
          sections: i + 1,
          findings: i + 1 >= 3 ? 8 : s.kpis.findings,
        },
      }),
    });
  });

  // WRITER done — report ready
  events.push({
    at: 21600,
    apply: (s) => ({
      status: { ...s.status, writer: "done" },
      feed: [...s.feed, line("WRITER", AGENT_CSS_VAR.writer, "finished — report ready ✓", 21600)],
    }),
  });

  return events;
}

const TIMELINE = buildTimeline();

function finalState(): RunState {
  const state: RunState = {
    status: { ...IDLE_STATUS },
    feed: [],
    visibleSources: 0,
    visibleSections: 0,
    flagged: false,
    kpis: { ...IDLE_KPIS },
  };
  for (const ev of TIMELINE) {
    Object.assign(state, ev.apply(state));
  }
  return state;
}

function emptyRunState(): RunState {
  return {
    status: { ...IDLE_STATUS },
    feed: [],
    visibleSources: 0,
    visibleSections: 0,
    flagged: false,
    kpis: { ...IDLE_KPIS },
  };
}

type TabId = "report" | "sources" | "activity";

export default function App() {
  const [theme, setTheme] = useState<Theme>(() => resolveTheme());
  const [depth, setDepth] = useState<Depth>("Standard");
  const [style, setStyle] = useState<ReportStyle>("Detailed Report");
  const [running, setRunning] = useState(false);
  const [done, setDone] = useState(false);
  const [runState, setRunState] = useState<RunState>(emptyRunState());
  const [runStartedAt, setRunStartedAt] = useState<number | null>(null);
  const [view, setView] = useState<NavView>("research");
  const [tab, setTab] = useState<TabId>("report");
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [mobileNavOpen, setMobileNavOpen] = useState(false);
  const [query, setQuery] = useState(DEMO_QUERY);
  // Live research (api/*.ts) reuses the same runState shape as the demo.
  const [liveMode, setLiveMode] = useState(false);
  const [liveSources, setLiveSources] = useState<LiveSource[]>([]);
  const [liveReport, setLiveReport] = useState<{ data: ReportData; md: string } | null>(null);
  const [keysBanner, setKeysBanner] = useState(false);
  const [liveError, setLiveError] = useState<string | null>(null);
  const timers = useRef<number[]>([]);
  const composerInputRef = useRef<HTMLInputElement | null>(null);
  const feedIdRef = useRef(0);
  const runTokenRef = useRef(0);
  const reducedMotion = useMemo(
    () =>
      typeof window !== "undefined" &&
      window.matchMedia("(prefers-reduced-motion: reduce)").matches,
    [],
  );

  useEffect(() => {
    applyTheme(theme);
  }, [theme]);

  useEffect(() => () => timers.current.forEach((t) => window.clearTimeout(t)), []);

  const focusComposer = useCallback(() => {
    setView("research");
    window.setTimeout(() => composerInputRef.current?.focus(), 0);
  }, []);

  // ⌘K / Ctrl+K jumps to the research question
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        focusComposer();
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [focusComposer]);

  const resetRun = useCallback(() => {
    timers.current.forEach((t) => window.clearTimeout(t));
    timers.current = [];
    runTokenRef.current += 1;
    setRunState(emptyRunState());
    setDone(false);
    setLiveMode(false);
    setLiveSources([]);
    setLiveReport(null);
    setKeysBanner(false);
    setLiveError(null);
    setView("research");
    setTab("report");
    setRunStartedAt(Date.now());
  }, []);

  const runDemo = useCallback(() => {
    resetRun();
    setRunning(true);

    if (reducedMotion) {
      setRunState(finalState());
      setDone(true);
      setRunning(false);
      return;
    }

    const base = emptyRunState();
    let state = base;
    TIMELINE.forEach((ev) => {
      const id = window.setTimeout(() => {
        state = { ...state, ...ev.apply(state) };
        setRunState({ ...state });
        if (ev === TIMELINE[TIMELINE.length - 1]) {
          setRunning(false);
          setDone(true);
        }
      }, ev.at);
      timers.current.push(id);
    });
  }, [reducedMotion, resetRun]);

  /** Live research: SCOUT → ANALYST → VERIFIER → WRITER via api/*.ts.
   * Each step updates the same runState the demo uses, so the rail, tabs
   * and TOC behave identically. On keys_not_configured the guidance banner
   * appears and the demo stays available. */
  const runLive = useCallback(async () => {
    if (running) return;
    resetRun();
    const token = runTokenRef.current;
    const alive = () => runTokenRef.current === token;
    const startedAt = Date.now();
    setRunning(true);
    setLiveMode(true);

    const pushFeed = (agent: AgentId, text: string) => {
      const color = AGENT_CSS_VAR[agent];
      const at = Date.now() - startedAt;
      setRunState((s) => ({
        ...s,
        feed: [...s.feed, { id: ++feedIdRef.current, agent: agent.toUpperCase(), color, text, at }],
      }));
    };
    const setStatus = (patch: Partial<Record<AgentId, AgentStatus>>) =>
      setRunState((s) => ({ ...s, status: { ...s.status, ...patch } }));

    try {
      // SCOUT
      setStatus({ scout: "working" });
      pushFeed("scout", "is now working…");
      const scoutRes = await api.scout(query, depth);
      if (!alive()) return;
      if (isKeysError(scoutRes)) {
        if (scoutRes.error === "keys_not_configured") setKeysBanner(true);
        else setLiveError("Live research failed at SCOUT. Please try again.");
        setRunning(false);
        setLiveMode(false);
        setRunState(emptyRunState());
        return;
      }
      const sources = scoutRes.sources;
      setLiveSources(sources);
      setRunState((s) => ({
        ...s,
        visibleSources: sources.length,
        kpis: { ...s.kpis, sources: sources.length },
      }));
      setStatus({ scout: "done", analyst: "working" });
      pushFeed("scout", "finished — Web Scout complete ✓");
      pushFeed("analyst", "is now working…");

      // ANALYST
      const analystRes = await api.analyst(query, depth, scoutRes.evidence);
      if (!alive()) return;
      if (isKeysError(analystRes)) {
        if (analystRes.error === "keys_not_configured") setKeysBanner(true);
        else setLiveError("Live research failed at ANALYST. Please try again.");
        setRunning(false);
        return;
      }
      setStatus({ analyst: "done", verifier: "working" });
      pushFeed("analyst", "finished — Insight Analyst complete ✓");
      pushFeed("verifier", "is now working…");

      // VERIFIER
      const verifierRes = await api.verifier(query, scoutRes.evidence, analystRes.synthesis);
      if (!alive()) return;
      if (isKeysError(verifierRes)) {
        if (verifierRes.error === "keys_not_configured") setKeysBanner(true);
        else setLiveError("Live research failed at VERIFIER. Please try again.");
        setRunning(false);
        return;
      }
      const flagged = /single-sourced|flagged/i.test(verifierRes.verification);
      setRunState((s) => ({ ...s, flagged, kpis: { ...s.kpis, claims: 8 } }));
      setStatus({ verifier: "done", writer: "working" });
      pushFeed("verifier", "finished — Fact Checker complete ✓");
      pushFeed("writer", "is now working…");

      // WRITER
      const writerRes = await api.writer(
        query,
        depth,
        style,
        scoutRes.evidence,
        analystRes.synthesis,
        verifierRes.verification,
        sources,
      );
      if (!alive()) return;
      if (isKeysError(writerRes)) {
        if (writerRes.error === "keys_not_configured") setKeysBanner(true);
        else setLiveError("Live research failed at WRITER. Please try again.");
        setRunning(false);
        return;
      }
      const parsed = parseReportMarkdown(writerRes.report);
      const data: ReportData = parsed ?? {
        execSummary: [[writerRes.report.slice(0, 4000)]],
        scope: [],
        findings: [],
        analysis: [],
        comparative: [],
        implications: [],
        limitations: [],
        sources: sources.map((s) => ({ label: s.title, url: s.url })),
      };
      setLiveReport({ data, md: writerRes.report });
      setRunState((s) => ({
        ...s,
        visibleSections: 8,
        kpis: { ...s.kpis, sections: 8, findings: Math.max(data.findings.length, 0) },
      }));
      setStatus({ writer: "done" });
      pushFeed("writer", "finished — report ready ✓");
      setRunning(false);
      setDone(true);
    } catch {
      if (!alive()) return;
      setLiveError("Live research failed (network error). Please try again — demo mode still works.");
      setRunning(false);
    }
  }, [running, resetRun, query, depth, style]);

  const newResearch = useCallback(() => {
    timers.current.forEach((t) => window.clearTimeout(t));
    timers.current = [];
    runTokenRef.current += 1;
    setRunState(emptyRunState());
    setRunning(false);
    setDone(false);
    setLiveMode(false);
    setLiveSources([]);
    setLiveReport(null);
    setKeysBanner(false);
    setLiveError(null);
    setRunStartedAt(null);
    setQuery(DEMO_QUERY);
    setView("research");
    setTab("report");
    setMobileNavOpen(false);
    window.setTimeout(() => composerInputRef.current?.focus(), 0);
  }, []);

  const selectRecent = useCallback((entry: RecentResearch) => {
    setQuery(entry.question);
    setView("research");
    setMobileNavOpen(false);
    window.setTimeout(() => composerInputRef.current?.focus(), 0);
  }, []);

  const idle = !running && !done;

  const topTitle =
    view === "research"
      ? idle
        ? "New research"
        : liveMode
          ? query
          : RECENT_RESEARCH[0].title
      : view === "history"
        ? "History"
        : view === "saved"
          ? "Saved reports"
          : "Sources";

  const stamp = useMemo(
    () =>
      new Date().toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" }) +
      " · " +
      new Date().toLocaleTimeString("en-GB", { hour: "2-digit", minute: "2-digit" }),
    [],
  );

  const tabs: { id: TabId; label: string }[] = [
    { id: "report", label: "Report" },
    { id: "sources", label: `Sources (${runState.visibleSources})` },
    { id: "activity", label: "Activity" },
  ];

  const liveSourcesForTab: DemoSource[] = liveSources.map((s) => ({ ...s }));

  return (
    <div className="app-bg flex h-dvh w-full overflow-hidden text-ink">
      {/* desktop sidebar */}
      <Sidebar
        collapsed={sidebarCollapsed}
        onToggleCollapse={() => setSidebarCollapsed((c) => !c)}
        view={view}
        onSelectView={(v) => {
          setView(v);
          setMobileNavOpen(false);
        }}
        onNewResearch={newResearch}
        onSelectRecent={selectRecent}
        className="hidden shrink-0 lg:flex"
      />

      {/* mobile drawer */}
      {mobileNavOpen && (
        <div className="fixed inset-0 z-50 lg:hidden" role="dialog" aria-label="Menu">
          <div
            className="absolute inset-0 bg-black/60"
            onClick={() => setMobileNavOpen(false)}
            data-testid="drawer-backdrop"
          />
          <div className="absolute left-0 top-0 h-full w-[280px] shadow-2xl">
            <Sidebar
              collapsed={false}
              onToggleCollapse={() => setSidebarCollapsed((c) => !c)}
              view={view}
              onSelectView={(v) => {
                setView(v);
                setMobileNavOpen(false);
              }}
              onNewResearch={newResearch}
              onSelectRecent={selectRecent}
              onCloseMobile={() => setMobileNavOpen(false)}
            />
          </div>
        </div>
      )}

      {/* right column: top bar + workspace + status bar */}
      <div className="flex min-w-0 flex-1 flex-col">
        <TopBar
          title={topTitle}
          depth={depth}
          setDepth={setDepth}
          style={style}
          setStyle={setStyle}
          running={running}
          done={done}
          onRun={runDemo}
          onRunLive={runLive}
          onMenu={() => setMobileNavOpen(true)}
          onFocusSearch={focusComposer}
          theme={theme}
          onToggleTheme={() => setTheme((t) => (t === "dark" ? "light" : "dark"))}
        />

        <div className="flex min-h-0 flex-1">
          <main id="workspace-scroll" className="min-w-0 flex-1 overflow-y-auto">
            {/* keys / live-error guidance banner (dismissible, never a crash) */}
            {(keysBanner || liveError) && view === "research" && (
              <div
                role="alert"
                data-testid={keysBanner ? "keys-banner" : "live-error-banner"}
                className="mx-3 mt-3 flex items-start gap-3 rounded-2xl border border-gold/50 bg-gold/[0.12] px-4 py-3 text-[0.85rem] leading-relaxed sm:mx-5"
              >
                <span className="min-w-0 flex-1">
                  {keysBanner ? (
                    <>
                      <b>Live research is paused.</b> Add <code>GEMINI_API_KEY</code> and{" "}
                      <code>TAVILY_API_KEY</code> in Vercel → Project Settings → Environment
                      Variables (Production), then redeploy. Demo mode below still works without
                      keys.
                    </>
                  ) : (
                    <>{liveError}</>
                  )}
                </span>
                <button
                  type="button"
                  aria-label="Dismiss"
                  onClick={() => {
                    setKeysBanner(false);
                    setLiveError(null);
                  }}
                  className="grid h-7 w-7 shrink-0 place-items-center rounded-lg text-muted transition hover:bg-ink/[0.06] hover:text-ink"
                >
                  <X size={15} />
                </button>
              </div>
            )}

            {view === "research" ? (
              idle ? (
                <Composer
                  query={query}
                  setQuery={setQuery}
                  onRun={runDemo}
                  onRunLive={runLive}
                  inputRef={composerInputRef}
                  onSelectRecent={selectRecent}
                  depth={depth}
                  setDepth={setDepth}
                  style={style}
                  setStyle={setStyle}
                />
              ) : (
                <>
                  {/* tab bar */}
                  <div className="sticky top-0 z-20 border-b border-muted/[0.12] bg-obsidian/95 backdrop-blur">
                    <div role="tablist" aria-label="Research views" className="flex items-center gap-1 px-3 sm:px-5">
                      {tabs.map((t) => {
                        const active = tab === t.id;
                        return (
                          <button
                            key={t.id}
                            type="button"
                            role="tab"
                            aria-selected={active}
                            data-testid={`tab-${t.id}`}
                            onClick={() => setTab(t.id)}
                            className={`relative h-11 px-3 text-[0.85rem] font-semibold transition ${
                              active ? "text-ink" : "text-muted hover:text-ink"
                            }`}
                          >
                            {t.label}
                            {active && <span className="absolute inset-x-2 bottom-0 h-[2px] rounded-full bg-emerald" />}
                          </button>
                        );
                      })}
                      <span className="ml-auto hidden items-center gap-2 text-[0.68rem] font-bold uppercase tracking-[0.1em] text-muted2 sm:flex">
                        {liveMode ? (
                          <span className="rounded-full bg-emerald px-2 py-0.5 text-[0.6rem] text-[#06231A]">
                            LIVE RESEARCH
                          </span>
                        ) : (
                          <span className="rounded-full bg-gold px-2 py-0.5 text-[0.6rem] text-[#0A1418]">
                            DEMO — SAMPLE DATA
                          </span>
                        )}
                      </span>
                    </div>
                  </div>

                  <div className="px-3 py-4 sm:px-5">
                    {tab === "report" && (
                      <ReportWindow
                        visibleSections={runState.visibleSections}
                        flagged={runState.flagged}
                        reducedMotion={reducedMotion}
                        stamp={stamp}
                        running={running}
                        meta={{
                          sources: runState.kpis.sources,
                          claims: runState.kpis.claims,
                          sections: runState.kpis.sections,
                        }}
                        reportData={liveReport?.data}
                        reportMd={liveReport?.md}
                        queryText={liveMode ? query : undefined}
                        isLive={liveMode}
                      />
                    )}

                    {tab === "sources" && (
                      <div className="mx-auto w-full max-w-[760px]">
                        <h2 className="font-display text-[1.15rem] font-bold">
                          Sources{" "}
                          <span className="font-body text-[0.75rem] font-medium text-muted">
                            {runState.visibleSources} results · Captured directly from Tavily
                          </span>
                        </h2>
                        <div className="mt-3">
                          <LiveSources
                            visibleCount={runState.visibleSources}
                            reducedMotion={reducedMotion}
                            sources={liveMode ? liveSourcesForTab : undefined}
                          />
                        </div>
                      </div>
                    )}

                    {tab === "activity" && (
                      <div className="mx-auto w-full max-w-[760px]">
                        <h2 className="font-display text-[1.15rem] font-bold">
                          Crew activity{" "}
                          <span className="font-body text-[0.75rem] font-medium text-muted">
                            Four specialists · one sequential pipeline
                          </span>
                        </h2>
                        <div className="mt-3">
                          <AgentDock status={runState.status} feed={runState.feed} startedAt={runStartedAt} />
                        </div>
                      </div>
                    )}
                  </div>
                </>
              )
            ) : (
              <LibraryView view={view} onSelectRecent={selectRecent} reducedMotion={reducedMotion} />
            )}
          </main>

          {/* right activity rail (desktop only) */}
          <ActivityRail
            status={runState.status}
            feed={runState.feed}
            startedAt={runStartedAt}
            running={running}
          />
        </div>

        {/* status bar */}
        <footer className="flex h-8 shrink-0 items-center justify-between gap-3 border-t border-muted/[0.10] bg-panel/50 px-4 text-[0.68rem] text-muted2">
          <span className="flex min-w-0 items-center gap-1.5 truncate">
            <i className="h-1.5 w-1.5 shrink-0 rounded-full bg-emerald" />
            Crew online · Gemini 3.5 Flash-Lite · Tavily
          </span>
          <span className="hidden shrink-0 items-center gap-2 sm:flex">
            <span className="rounded-full border border-teal/40 bg-teal/10 px-1.5 py-0.5 text-[0.58rem] font-extrabold tracking-[0.1em] text-tealink">
              REACT PREVIEW
            </span>
            <span>{liveMode ? "Live research — Gemini + Tavily" : "Demo data — sample report, not live research"}</span>
          </span>
        </footer>
      </div>
    </div>
  );
}
