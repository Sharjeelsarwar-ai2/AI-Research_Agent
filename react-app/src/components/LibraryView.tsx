import { Bookmark, ChevronRight, Clock, Star } from "lucide-react";
import { RECENT_RESEARCH, type RecentResearch } from "../data/demo";
import LiveSources from "./LiveSources";
import type { NavView } from "./Sidebar";

function HistoryRow({
  entry,
  onSelect,
}: {
  entry: RecentResearch;
  onSelect: (entry: RecentResearch) => void;
}) {
  return (
    <li>
      <button
        type="button"
        onClick={() => onSelect(entry)}
        className="flex w-full items-center gap-3 rounded-xl border border-muted/[0.12] bg-panel/60 px-4 py-3 text-left transition hover:border-emerald/50 hover:bg-panel"
      >
        <span className="min-w-0 flex-1">
          <span className="flex items-center gap-1.5 truncate text-[0.92rem] font-semibold">
            {entry.title}
            {entry.saved && <Star size={13} className="shrink-0 fill-goldtext text-goldtext" />}
          </span>
          <span className="mt-0.5 flex items-center gap-1 text-[0.72rem] text-muted2">
            <Clock size={11} /> {entry.date} · {entry.words.toLocaleString()} words · {entry.sources} sources
          </span>
        </span>
        <ChevronRight size={16} className="shrink-0 text-muted2" />
      </button>
    </li>
  );
}

export default function LibraryView({
  view,
  onSelectRecent,
  reducedMotion,
}: {
  view: Exclude<NavView, "research">;
  onSelectRecent: (entry: RecentResearch) => void;
  reducedMotion: boolean;
}) {
  const saved = RECENT_RESEARCH.filter((e) => e.saved);

  return (
    <div className="mx-auto w-full max-w-[760px] px-4 py-6 sm:px-6">
      {view === "history" && (
        <>
          <h2 className="font-display text-[1.4rem] font-bold">History</h2>
          <p className="mt-1 text-[0.85rem] text-muted">Past research in this workspace. Select one to load its question into the composer.</p>
          <ul className="mt-5 space-y-2">
            {RECENT_RESEARCH.map((entry) => (
              <HistoryRow key={entry.title} entry={entry} onSelect={onSelectRecent} />
            ))}
          </ul>
        </>
      )}

      {view === "saved" && (
        <>
          <h2 className="font-display text-[1.4rem] font-bold">Saved reports</h2>
          <p className="mt-1 flex items-center gap-1.5 text-[0.85rem] text-muted">
            <Bookmark size={13} /> {saved.length} saved report{saved.length === 1 ? "" : "s"} in this workspace.
          </p>
          <ul className="mt-5 space-y-2">
            {saved.map((entry) => (
              <HistoryRow key={entry.title} entry={entry} onSelect={onSelectRecent} />
            ))}
          </ul>
        </>
      )}

      {view === "sources" && (
        <>
          <h2 className="font-display text-[1.4rem] font-bold">Sources</h2>
          <p className="mt-1 text-[0.85rem] text-muted">
            From your latest research — AI coding assistant market 2026. Captured directly from Tavily.
          </p>
          <div className="mt-5">
            <LiveSources visibleCount={7} reducedMotion={reducedMotion} />
          </div>
        </>
      )}
    </div>
  );
}
