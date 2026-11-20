import { Bookmark, ChevronsLeft, ChevronsRight, Clock, Globe, History, Plus, Search, Settings, Star, X } from "lucide-react";
import type { HistoryEntry } from "../lib/history";

export type NavView = "research" | "history" | "saved" | "sources";

const NAV_ITEMS: { id: NavView; label: string; icon: typeof Search }[] = [
  { id: "research", label: "Research", icon: Search },
  { id: "history", label: "History", icon: History },
  { id: "saved", label: "Saved reports", icon: Bookmark },
  { id: "sources", label: "Sources", icon: Globe },
];

export default function Sidebar({
  collapsed,
  onToggleCollapse,
  view,
  onSelectView,
  onNewResearch,
  history,
  onSelectRecent,
  onCloseMobile,
  className = "",
}: {
  collapsed: boolean;
  onToggleCollapse: () => void;
  view: NavView;
  onSelectView: (v: NavView) => void;
  onNewResearch: () => void;
  history: HistoryEntry[];
  onSelectRecent: (entry: HistoryEntry) => void;
  onCloseMobile?: () => void;
  className?: string;
}) {
  return (
    <aside
      aria-label="Primary"
      className={`flex h-full flex-col border-r border-muted/[0.14] bg-panel/70 transition-[width] duration-200 ${collapsed ? "w-16" : "w-[260px]"} ${className}`}
    >
      {/* brand */}
      <div className={`flex h-14 shrink-0 items-center gap-2.5 border-b border-muted/[0.10] px-3 ${collapsed ? "justify-center px-0" : ""}`}>
        <span className="grid h-9 w-9 shrink-0 place-items-center rounded-[11px] bg-emerald text-[0.95rem] font-extrabold text-[#06231A]">
          ✦
        </span>
        {!collapsed && (
          <span className="min-w-0 flex-1 truncate font-display text-[1rem] font-bold leading-tight">
            Nexus Research <span className="text-emeraldink">AI</span>
          </span>
        )}
        {onCloseMobile && (
          <button
            type="button"
            onClick={onCloseMobile}
            aria-label="Close menu"
            className="ml-auto grid h-8 w-8 shrink-0 place-items-center rounded-lg text-muted transition hover:bg-ink/[0.06] hover:text-ink lg:hidden"
          >
            <X size={17} />
          </button>
        )}
      </div>

      {/* new research */}
      <div className="shrink-0 px-3 pt-3">
        <button
          type="button"
          onClick={onNewResearch}
          title="New research"
          className={`flex h-10 items-center justify-center gap-2 rounded-xl bg-emerald text-[0.85rem] font-bold text-[#06231A] shadow-[0_8px_20px_rgba(0,217,122,0.25)] transition hover:bg-emeraldsoft ${collapsed ? "w-10 px-0" : "w-full px-3"}`}
        >
          <Plus size={17} strokeWidth={2.75} />
          {!collapsed && "New research"}
        </button>
      </div>

      {/* nav */}
      <nav className="mt-3 shrink-0 px-2" aria-label="Sections">
        {NAV_ITEMS.map((item) => {
          const Icon = item.icon;
          const active = view === item.id;
          return (
            <button
              key={item.id}
              type="button"
              onClick={() => onSelectView(item.id)}
              aria-current={active ? "page" : undefined}
              title={item.label}
              className={`relative mb-0.5 flex h-10 w-full items-center gap-3 rounded-r-xl rounded-l-[4px] px-3 text-[0.85rem] font-semibold transition ${
                active
                  ? "bg-emerald/[0.12] text-ink"
                  : "text-muted hover:bg-ink/[0.05] hover:text-ink"
              } ${collapsed ? "justify-center px-0" : ""}`}
            >
              {active && <span className="absolute left-0 top-1.5 bottom-1.5 w-[3px] rounded-full bg-emerald" aria-hidden="true" />}
              <Icon size={17} strokeWidth={2.25} className={active ? "text-emeraldink" : ""} />
              {!collapsed && <span className="truncate">{item.label}</span>}
            </button>
          );
        })}
      </nav>

      {/* recent research — real saved history, newest first */}
      {!collapsed && (
        <div className="mt-4 min-h-0 flex-1 overflow-y-auto px-3">
          <div className="mb-1.5 px-1 text-[0.65rem] font-extrabold uppercase tracking-[0.14em] text-muted2">
            Recent research
          </div>
          {history.length === 0 ? (
            <p className="px-1 text-[0.75rem] leading-relaxed text-muted2">
              No reports yet — your finished research will appear here.
            </p>
          ) : (
            <ul className="space-y-0.5">
              {history.map((entry) => (
                <li key={entry.id}>
                  <button
                    type="button"
                    onClick={() => onSelectRecent(entry)}
                    title={entry.question}
                    className="group flex w-full flex-col gap-0.5 rounded-xl px-2.5 py-2 text-left transition hover:bg-ink/[0.05]"
                  >
                    <span className="flex items-center gap-1.5 truncate text-[0.82rem] font-semibold text-ink">
                      <span className="truncate">{entry.title}</span>
                      {entry.saved && <Star size={11} className="shrink-0 fill-goldtext text-goldtext" />}
                      <span
                        className={`shrink-0 rounded-full px-1.5 py-px text-[0.58rem] font-extrabold uppercase tracking-wide ${
                          entry.mode === "live" ? "bg-emerald text-[#06231A]" : "bg-gold text-[#0A1418]"
                        }`}
                      >
                        {entry.mode === "live" ? "Live" : "Demo"}
                      </span>
                    </span>
                    <span className="flex items-center gap-1 text-[0.68rem] text-muted2">
                      <Clock size={10} /> {entry.date} · {entry.words.toLocaleString()} words · {entry.sources} sources
                    </span>
                  </button>
                </li>
              ))}
            </ul>
          )}
        </div>
      )}

      {/* bottom: settings + user */}
      <div className="shrink-0 border-t border-muted/[0.10] px-2 py-2">
        <button
          type="button"
          title="Settings"
          className={`mb-1 flex h-9 w-full items-center gap-3 rounded-lg px-3 text-[0.82rem] font-semibold text-muted transition hover:bg-ink/[0.05] hover:text-ink ${collapsed ? "justify-center px-0" : ""}`}
        >
          <Settings size={16} />
          {!collapsed && "Settings"}
        </button>
        <div className={`flex items-center gap-2.5 rounded-xl px-2 py-1.5 ${collapsed ? "justify-center px-0" : ""}`}>
          <span className="grid h-8 w-8 shrink-0 place-items-center rounded-full bg-emerald text-[0.7rem] font-extrabold text-[#06231A]">
            SS
          </span>
          {!collapsed && (
            <span className="min-w-0 flex-1">
              <span className="block truncate text-[0.82rem] font-bold leading-tight">Sharjeel Sarwar</span>
              <span className="block truncate text-[0.66rem] text-muted2">UET Lahore · BSCS</span>
            </span>
          )}
          {!collapsed && (
            <button
              type="button"
              onClick={onToggleCollapse}
              aria-label="Collapse sidebar"
              title="Collapse sidebar"
              className="grid h-7 w-7 shrink-0 place-items-center rounded-md text-muted transition hover:bg-ink/[0.06] hover:text-ink"
            >
              <ChevronsLeft size={15} />
            </button>
          )}
        </div>
        {collapsed && (
          <button
            type="button"
            onClick={onToggleCollapse}
            aria-label="Expand sidebar"
            title="Expand sidebar"
            className="mx-auto mt-1 grid h-8 w-8 place-items-center rounded-lg text-muted transition hover:bg-ink/[0.06] hover:text-ink"
          >
            <ChevronsRight size={15} />
          </button>
        )}
      </div>
    </aside>
  );
}
