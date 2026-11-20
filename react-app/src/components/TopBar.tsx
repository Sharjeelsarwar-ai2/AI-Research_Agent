import { ChevronRight, Menu, Moon, Play, RotateCcw, Search, Sun, Zap } from "lucide-react";
import type { Theme } from "../lib/theme";

export type Depth = "Quick" | "Standard" | "Deep";
export type ReportStyle = "Executive Brief" | "Detailed Report" | "Technical Analysis";

export function Segmented<T extends string>({
  label,
  options,
  value,
  onChange,
  disabled,
  shortLabels,
}: {
  label: string;
  options: readonly T[];
  value: T;
  onChange: (v: T) => void;
  disabled?: boolean;
  shortLabels?: Partial<Record<T, string>>;
}) {
  return (
    <div className="flex items-center gap-1.5" role="group" aria-label={label}>
      <span className="hidden text-[0.68rem] font-bold uppercase tracking-[0.08em] text-muted2 xl:inline">{label}</span>
      <div className="flex rounded-[10px] border border-muted/[0.2] bg-panel p-0.5">
        {options.map((opt) => {
          const active = opt === value;
          return (
            <button
              key={opt}
              type="button"
              onClick={() => onChange(opt)}
              disabled={disabled}
              aria-pressed={active}
              title={opt}
              className={`h-7 rounded-[7px] px-2.5 text-[0.72rem] font-bold transition disabled:cursor-not-allowed ${
                active ? "bg-emerald text-[#06231A]" : "text-muted hover:text-ink"
              }`}
            >
              {shortLabels?.[opt] ?? opt}
            </button>
          );
        })}
      </div>
    </div>
  );
}

export default function TopBar({
  title,
  depth,
  setDepth,
  style,
  setStyle,
  running,
  done,
  onRun,
  onRunLive,
  onMenu,
  onFocusSearch,
  theme,
  onToggleTheme,
}: {
  title: string;
  depth: Depth;
  setDepth: (d: Depth) => void;
  style: ReportStyle;
  setStyle: (s: ReportStyle) => void;
  running: boolean;
  done: boolean;
  onRun: () => void;
  onRunLive: () => void;
  onMenu: () => void;
  onFocusSearch: () => void;
  theme: Theme;
  onToggleTheme: () => void;
}) {
  return (
    <header className="flex h-14 shrink-0 items-center gap-2 border-b border-muted/[0.14] bg-obsidian/90 px-3 backdrop-blur sm:gap-3 sm:px-4">
      <button
        type="button"
        onClick={onMenu}
        aria-label="Open menu"
        className="grid h-9 w-9 shrink-0 place-items-center rounded-lg text-muted transition hover:bg-ink/[0.06] hover:text-ink lg:hidden"
      >
        <Menu size={18} />
      </button>

      {/* breadcrumb / current research */}
      <div className="flex min-w-0 flex-1 items-center gap-1.5">
        <span className="hidden shrink-0 text-[0.8rem] font-semibold text-muted2 sm:inline">Research</span>
        <ChevronRight size={14} className="hidden shrink-0 text-muted2 sm:inline" />
        <h1 className="min-w-0 truncate font-display text-[1rem] font-bold leading-tight" data-testid="topbar-title">
          {title}
        </h1>
      </div>

      {/* segmented controls */}
      <div className="hidden shrink-0 items-center gap-3 md:flex">
        <Segmented label="Depth" options={["Quick", "Standard", "Deep"] as const} value={depth} onChange={setDepth} disabled={running} />
        <Segmented
          label="Style"
          options={["Executive Brief", "Detailed Report", "Technical Analysis"] as const}
          value={style}
          onChange={setStyle}
          disabled={running}
          shortLabels={{ "Executive Brief": "Brief", "Detailed Report": "Detailed", "Technical Analysis": "Technical" }}
        />
      </div>

      {/* command-K */}
      <button
        type="button"
        onClick={onFocusSearch}
        title="Jump to the research question (Ctrl/⌘ K)"
        aria-label="Jump to the research question"
        className="hidden h-8 shrink-0 items-center gap-1.5 rounded-lg border border-muted/[0.2] bg-panel px-2 text-[0.72rem] font-semibold text-muted transition hover:border-emerald/50 hover:text-ink sm:flex"
      >
        <Search size={13} />
        <kbd className="font-body text-[0.7rem] font-bold">⌘K</kbd>
      </button>

      {/* theme toggle */}
      <button
        type="button"
        onClick={onToggleTheme}
        title={theme === "dark" ? "Switch to light theme" : "Switch to dark theme"}
        aria-label={theme === "dark" ? "Switch to light theme" : "Switch to dark theme"}
        aria-pressed={theme === "light"}
        data-testid="theme-toggle"
        className="grid h-9 w-9 shrink-0 place-items-center rounded-lg border border-muted/[0.2] bg-panel text-muted transition hover:border-emerald/50 hover:text-ink"
      >
        {theme === "dark" ? <Sun size={17} /> : <Moon size={17} />}
      </button>

      {/* run live */}
      <button
        type="button"
        onClick={onRunLive}
        disabled={running}
        data-testid="run-live-button"
        title="Run live research with Gemini + Tavily (needs API keys in Vercel)"
        className="hidden h-9 shrink-0 items-center gap-2 rounded-[10px] border border-emerald/60 bg-emerald/[0.12] px-3.5 text-[0.82rem] font-bold text-emeraldink transition hover:bg-emerald/[0.22] disabled:cursor-not-allowed disabled:opacity-60 sm:flex"
      >
        <Zap size={15} strokeWidth={2.5} />
        <span className="hidden lg:inline">Run live</span>
      </button>

      {/* run demo */}
      <button
        type="button"
        onClick={onRun}
        disabled={running}
        data-testid="run-demo-button"
        className="flex h-9 shrink-0 items-center gap-2 rounded-[10px] bg-emerald px-3.5 text-[0.82rem] font-bold text-[#06231A] shadow-[0_8px_20px_rgba(0,217,122,0.25)] transition hover:bg-emeraldsoft disabled:cursor-not-allowed disabled:opacity-60"
      >
        {done ? <RotateCcw size={15} strokeWidth={2.5} /> : <Play size={15} strokeWidth={2.5} fill="currentColor" />}
        {running ? "Crew working…" : done ? "Run again" : "Run demo"}
      </button>
    </header>
  );
}
