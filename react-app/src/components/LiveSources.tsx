import { motion } from "motion/react";
import { ArrowUpRight } from "lucide-react";
import { DEMO_SOURCES, type DemoSource } from "../data/demo";

function SourceRow({ source, index, reducedMotion }: { source: DemoSource; index: number; reducedMotion: boolean }) {
  return (
    <motion.a
      href={source.url}
      target="_blank"
      rel="noopener noreferrer"
      initial={reducedMotion ? false : { opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.35, ease: "easeOut" }}
      className="flex items-start gap-3 rounded-xl border border-muted/[0.13] bg-[linear-gradient(135deg,rgba(255,253,246,0.72),rgba(247,245,236,0.65))] px-3.5 py-3 text-[#1B2530] transition hover:-translate-y-px hover:border-emerald/60 hover:shadow-[0_10px_24px_rgba(0,0,0,0.18)]"
    >
      <span className="mt-0.5 shrink-0 whitespace-nowrap text-[0.62rem] font-extrabold tracking-[0.07em] text-[#0B7A5E]">
        {String(index + 1).padStart(2, "0")}
      </span>
      <span className="min-w-0 flex-1">
        <strong className="block text-[0.85rem] font-semibold leading-snug">{source.title}</strong>
        <small className="mt-0.5 block text-[0.68rem] text-[#0B7A5E]">
          {source.domain} · {source.published}
        </small>
        <span className="mt-1 block text-[0.75rem] leading-relaxed text-papermuted">{source.snippet}</span>
      </span>
      <ArrowUpRight size={15} className="mt-0.5 shrink-0 text-[#0B7A5E]" />
    </motion.a>
  );
}

/** Dense single-column source list (Sources tab / Sources library view). */
export default function LiveSources({
  visibleCount,
  reducedMotion,
  sources,
}: {
  visibleCount: number;
  reducedMotion: boolean;
  /** Live Tavily sources; defaults to the demo sources. */
  sources?: DemoSource[];
}) {
  const all = sources ?? DEMO_SOURCES;
  const visible = all.slice(0, visibleCount);

  if (visibleCount === 0) {
    return (
      <p className="rounded-xl border border-muted/[0.14] bg-panel/50 px-4 py-6 text-center text-[0.85rem] text-muted">
        No sources yet — SCOUT gathers them once the run starts.
      </p>
    );
  }

  return (
    <div className="space-y-2" data-testid="live-sources">
      {visible.map((s, i) => (
        <SourceRow key={s.url} source={s} index={i} reducedMotion={reducedMotion} />
      ))}
    </div>
  );
}
