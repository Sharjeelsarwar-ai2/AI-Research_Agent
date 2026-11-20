import { useEffect, useRef } from "react";
import { Check } from "lucide-react";
import { AGENT_CSS_VAR, AGENT_DEFS, type AgentId, type AgentStatus } from "../data/demo";
import RobotAvatar from "./RobotAvatar";

export interface FeedLine {
  id: number;
  agent: string;
  color: string;
  text: string;
  /** ms offset from the run start — rendered as a wall-clock timestamp */
  at: number;
}

const STATUS_LABEL: Record<AgentStatus, string> = { idle: "Idle", working: "Working", done: "Done" };

function statusProgress(status: AgentStatus): number {
  if (status === "working") return 55;
  if (status === "done") return 100;
  return 0;
}

export function formatClock(epochMs: number): string {
  return new Date(epochMs).toLocaleTimeString("en-GB", { hour12: false });
}

/** Compact agent rows — one row per agent, 3px accent bar, solid status pill. */
export function AgentRows({ status }: { status: Record<AgentId, AgentStatus> }) {
  return (
    <ul className="space-y-2" data-testid="agent-dock">
      {AGENT_DEFS.map((agent) => {
        const state = status[agent.id];
        const progress = statusProgress(state);
        return (
          <li
            key={agent.id}
            data-testid={`agent-card-${agent.id}`}
            data-status={state}
            className="rounded-r-xl rounded-l-[4px] border border-muted/[0.12] border-l-[3px] bg-panel/70 px-3 py-2.5 transition hover:bg-panel"
            style={{ borderLeftColor: AGENT_CSS_VAR[agent.id] }}
          >
            <div className="flex items-center gap-2.5">
              <span
                className="grid h-9 w-9 shrink-0 place-items-center rounded-[10px] border border-ink/[0.09] bg-obsidian"
              >
                <RobotAvatar color={AGENT_CSS_VAR[agent.id]} size={30} working={state === "working"} />
              </span>
              <span className="min-w-0 flex-1">
                <span className="flex items-baseline gap-2">
                  <span className="font-display text-[0.82rem] font-bold tracking-[0.05em]" style={{ color: AGENT_CSS_VAR[agent.id] }}>
                    {agent.name}
                  </span>
                  <span className="truncate text-[0.68rem] text-muted">{agent.role}</span>
                </span>
                <span className="block truncate text-[0.66rem] text-muted2">{agent.tagline}</span>
              </span>
              <span
                data-testid={`agent-pill-${agent.id}`}
                className={`inline-flex shrink-0 items-center gap-1 rounded-full px-2 py-1 text-[0.6rem] font-extrabold uppercase tracking-[0.08em] ${
                  state === "idle" ? "border border-ink/[0.10] bg-ink/[0.05] text-muted" : "text-[var(--on-agent)]"
                } ${state === "working" ? "animate-pulse-fast" : ""}`}
                style={state === "idle" ? undefined : { background: AGENT_CSS_VAR[agent.id] }}
              >
                {state === "done" && <Check size={10} strokeWidth={3.5} />}
                {STATUS_LABEL[state]}
              </span>
            </div>
            <div className="ml-[46px] mt-2 h-[3px] overflow-hidden rounded-full bg-ink/[0.08]">
              <span
                className={`block h-full rounded-full transition-[width] duration-500 ${state === "working" ? "working-bar" : ""}`}
                style={{ width: `${progress}%`, background: state === "working" ? undefined : AGENT_CSS_VAR[agent.id], ["--ac" as string]: AGENT_CSS_VAR[agent.id] }}
              />
            </div>
          </li>
        );
      })}
    </ul>
  );
}

/** Timestamped activity timeline. */
export function ActivityFeed({
  feed,
  startedAt,
}: {
  feed: FeedLine[];
  startedAt: number | null;
}) {
  const feedRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const el = feedRef.current;
    if (el) el.scrollTop = el.scrollHeight;
  }, [feed.length]);

  return (
    <div
      ref={feedRef}
      data-testid="agent-feed"
      className="feed-scroll min-h-0 flex-1 overflow-y-auto pr-1"
    >
      {feed.length === 0 ? (
        <p className="py-2 text-[0.78rem] leading-relaxed text-muted">
          Crew idle — press Run demo to watch the four agents work.
        </p>
      ) : (
        <ol className="space-y-2 py-1">
          {feed.map((line) => (
            <li key={line.id} className="flex items-baseline gap-2 text-[0.78rem] leading-snug">
              <time className="shrink-0 tabular-nums text-[0.68rem] text-muted2" dateTime={startedAt !== null ? new Date(startedAt + line.at).toISOString() : undefined}>
                {startedAt !== null ? formatClock(startedAt + line.at) : "--:--:--"}
              </time>
              <span>
                <b style={{ color: line.color }}>{line.agent}</b>{" "}
                <span className="text-ink">{line.text}</span>
              </span>
            </li>
          ))}
        </ol>
      )}
    </div>
  );
}

/** The crew panel: compact agent rows + live activity timeline. */
export default function AgentDock({
  status,
  feed,
  startedAt,
}: {
  status: Record<AgentId, AgentStatus>;
  feed: FeedLine[];
  startedAt: number | null;
}) {
  return (
    <div className="flex min-h-0 flex-1 flex-col gap-4">
      <AgentRows status={status} />
      <div className="flex min-h-0 flex-1 flex-col">
        <div className="mb-1.5 flex items-center gap-2">
          <span className="text-[0.65rem] font-extrabold uppercase tracking-[0.14em] text-muted2">Activity</span>
          <span className="text-[0.68rem] tabular-nums text-muted2">{feed.length > 0 ? `${feed.length} events` : ""}</span>
        </div>
        <ActivityFeed feed={feed} startedAt={startedAt} />
      </div>
    </div>
  );
}
