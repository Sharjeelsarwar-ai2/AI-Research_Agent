import AgentDock, { type FeedLine } from "./AgentDock";
import type { AgentId, AgentStatus } from "../data/demo";

export default function ActivityRail({
  status,
  feed,
  startedAt,
  running,
}: {
  status: Record<AgentId, AgentStatus>;
  feed: FeedLine[];
  startedAt: number | null;
  running: boolean;
}) {
  const anyWorking = Object.values(status).some((s) => s === "working");
  return (
    <aside
      aria-label="Crew activity"
      data-testid="activity-rail"
      className="hidden w-[320px] shrink-0 flex-col border-l border-muted/[0.14] bg-panel/40 xl:flex"
    >
      <div className="flex h-12 shrink-0 items-center gap-2 border-b border-muted/[0.10] px-4">
        <span className="font-display text-[0.85rem] font-bold tracking-wide">Crew activity</span>
        <span className="ml-auto inline-flex items-center gap-1.5 text-[0.62rem] font-extrabold uppercase tracking-[0.12em] text-emeraldink">
          <i
            className={`block h-2 w-2 rounded-full bg-emerald shadow-[0_0_10px_rgba(0,217,122,0.9)] ${running || anyWorking ? "animate-pulse-dot" : "opacity-60"}`}
          />
          {running || anyWorking ? "Working" : "Idle"}
        </span>
      </div>
      <div className="flex min-h-0 flex-1 flex-col px-3 py-3">
        <AgentDock status={status} feed={feed} startedAt={startedAt} />
      </div>
    </aside>
  );
}
