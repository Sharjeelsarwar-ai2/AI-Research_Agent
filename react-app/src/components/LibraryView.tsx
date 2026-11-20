import { Bookmark, ChevronRight, Clock, Star, Trash2 } from "lucide-react";
import type { HistoryEntry, HistorySource } from "../lib/history";
import LiveSources from "./LiveSources";
import type { NavView } from "./Sidebar";

function HistoryRow({
  entry,
  onSelect,
  onToggleSaved,
  onDelete,
}: {
  entry: HistoryEntry;
  onSelect: (entry: HistoryEntry) => void;
  onToggleSaved: (id: string, saved: boolean) => void;
  onDelete: (id: string) => void;
}) {
  return (
    <li className="flex items-center gap-2 rounded-xl border border-muted/[0.12] bg-panel/60 transition hover:border-emerald/50 hover:bg-panel">
      <button
        type="button"
        onClick={() => onSelect(entry)}
        data-testid={`history-row-${entry.id}`}
        className="min-w-0 flex-1 px-4 py-3 text-left"
      >
        <span className="flex items-center gap-1.5 truncate text-[0.92rem] font-semibold">
          <span className="truncate">{entry.title}</span>
          {entry.saved && <Star size={13} className="shrink-0 fill-goldtext text-goldtext" />}
          <span
            className={`shrink-0 rounded-full px-1.5 py-px text-[0.58rem] font-extrabold uppercase tracking-wide ${
              entry.mode === "live" ? "bg-emerald text-[#06231A]" : "bg-gold text-[#0A1418]"
            }`}
          >
            {entry.mode === "live" ? "Live" : "Demo"}
          </span>
        </span>
        <span className="mt-0.5 flex items-center gap-1 text-[0.72rem] text-muted2">
          <Clock size={11} /> {entry.date} · {entry.words.toLocaleString()} words · {entry.sources} sources
        </span>
      </button>
      <button
        type="button"
        onClick={() => onToggleSaved(entry.id, !entry.saved)}
        aria-label={entry.saved ? "Remove from saved reports" : "Save this report"}
        title={entry.saved ? "Remove from saved reports" : "Save this report"}
        className="grid h-8 w-8 shrink-0 place-items-center rounded-lg text-muted transition hover:bg-ink/[0.06] hover:text-ink"
      >
        <Star size={15} className={entry.saved ? "fill-goldtext text-goldtext" : ""} />
      </button>
      <button
        type="button"
        onClick={() => onDelete(entry.id)}
        aria-label="Delete this report"
        title="Delete this report"
        className="mr-2 grid h-8 w-8 shrink-0 place-items-center rounded-lg text-muted transition hover:bg-ink/[0.06] hover:text-ink"
      >
        <Trash2 size={15} />
      </button>
      <ChevronRight size={16} className="mr-3 hidden shrink-0 text-muted2 sm:block" />
    </li>
  );
}

export default function LibraryView({
  view,
  history,
  historySource,
  onSelectRecent,
  onToggleSaved,
  onDeleteReport,
  reducedMotion,
}: {
  view: Exclude<NavView, "research">;
  history: HistoryEntry[];
  historySource: HistorySource;
  onSelectRecent: (entry: HistoryEntry) => void;
  onToggleSaved: (id: string, saved: boolean) => void;
  onDeleteReport: (id: string) => void;
  reducedMotion: boolean;
}) {
  const saved = history.filter((e) => e.saved);

  return (
    <div className="mx-auto w-full max-w-[760px] px-4 py-6 sm:px-6">
      {view === "history" && (
        <>
          <h2 className="font-display text-[1.4rem] font-bold">History</h2>
          <p className="mt-1 text-[0.85rem] text-muted">
            Past research in this workspace. Select one to reopen its full report.
          </p>
          {historySource === "local" && history.length > 0 && (
            <p className="mt-2 text-[0.78rem] text-muted2">
              Saved on this device only — add your Supabase keys in Vercel to sync history.
            </p>
          )}
          {history.length === 0 ? (
            <p className="mt-5 text-[0.88rem] text-muted">
              No reports yet. Run your first research and it will show up here.
            </p>
          ) : (
            <ul className="mt-5 space-y-2">
              {history.map((entry) => (
                <HistoryRow
                  key={entry.id}
                  entry={entry}
                  onSelect={onSelectRecent}
                  onToggleSaved={onToggleSaved}
                  onDelete={onDeleteReport}
                />
              ))}
            </ul>
          )}
        </>
      )}

      {view === "saved" && (
        <>
          <h2 className="font-display text-[1.4rem] font-bold">Saved reports</h2>
          <p className="mt-1 flex items-center gap-1.5 text-[0.85rem] text-muted">
            <Bookmark size={13} /> {saved.length} saved report{saved.length === 1 ? "" : "s"} in this workspace.
          </p>
          {saved.length === 0 ? (
            <p className="mt-5 text-[0.88rem] text-muted">
              Nothing saved yet — tap the star on a report to keep it here.
            </p>
          ) : (
            <ul className="mt-5 space-y-2">
              {saved.map((entry) => (
                <HistoryRow
                  key={entry.id}
                  entry={entry}
                  onSelect={onSelectRecent}
                  onToggleSaved={onToggleSaved}
                  onDelete={onDeleteReport}
                />
              ))}
            </ul>
          )}
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
