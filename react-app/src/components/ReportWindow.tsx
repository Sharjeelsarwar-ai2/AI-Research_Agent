import { Fragment, useEffect, useMemo, useState } from "react";
import { motion } from "motion/react";
import { ArrowUpRight, Download, FileText, FileCode2, FileDown, TriangleAlert } from "lucide-react";
import {
  DEMO_QUERY,
  DEMO_REPORT_MD,
  FINDING_COLORS,
  FINDING_TEXT_COLORS,
  REPORT,
  type Cite,
  type Inline,
  type ReportData,
} from "../data/demo";

const SECTIONS = [
  { n: 1, title: "Executive Summary" },
  { n: 2, title: "Research Scope & Method" },
  { n: 3, title: "Key Findings" },
  { n: 4, title: "Detailed Analysis" },
  { n: 5, title: "Comparative Perspective" },
  { n: 6, title: "Implications" },
  { n: 7, title: "Limitations & Caveats" },
  { n: 8, title: "Sources" },
] as const;

export function renderInline(parts: Inline[], keyPrefix: string) {
  return parts.map((part, i) =>
    typeof part === "string" ? (
      <Fragment key={`${keyPrefix}-${i}`}>{part}</Fragment>
    ) : (
      <a key={`${keyPrefix}-${i}`} href={part.url} target="_blank" rel="noopener noreferrer">
        {part.label}
      </a>
    ),
  );
}

function SectionTitle({ children, sub }: { children: React.ReactNode; sub?: string }) {
  return (
    <h3 className="mb-2.5 mt-5 font-display text-[1.02rem] font-bold tracking-[-0.01em] text-paperink2 first:mt-0">
      {children}
      {sub && <span className="ml-2 font-body text-[0.72rem] font-medium text-papermuted">{sub}</span>}
    </h3>
  );
}

function SectionBlock({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="mb-3 rounded-2xl border border-[#E3DECB] bg-cream px-4 py-4">
      <div className="mb-1.5 font-display text-[1.02rem] font-bold text-paperink2">{title}</div>
      {children}
    </div>
  );
}

function Para({ parts }: { parts: Inline[] }) {
  return <p className="my-1.5 leading-[1.7] text-paperink">{renderInline(parts, "p")}</p>;
}

const sectionAnim = (reducedMotion: boolean, delay = 0) =>
  reducedMotion
    ? {}
    : {
        initial: { opacity: 0, y: 14 },
        animate: { opacity: 1, y: 0 },
        transition: { duration: 0.45, ease: "easeOut" as const, delay },
      };

export default function ReportWindow({
  visibleSections,
  flagged,
  reducedMotion,
  stamp,
  running,
  meta,
  reportData,
  reportMd,
  queryText,
  isLive,
}: {
  visibleSections: number; // 0..8, sections in report order
  flagged: boolean;
  reducedMotion: boolean;
  stamp: string;
  running: boolean;
  meta: { sources: number; claims: number; sections: number };
  /** Live report (parsed from the WRITER markdown). Falls back to the demo report. */
  reportData?: ReportData;
  reportMd?: string;
  queryText?: string;
  isLive?: boolean;
}) {
  const show = (n: number) => visibleSections >= n;
  const data = reportData ?? REPORT;
  const md = reportMd ?? DEMO_REPORT_MD;
  const query = queryText ?? DEMO_QUERY;

  const words = useMemo(
    () => md.replace(/[#*`>\[\]()]/g, " ").split(/\s+/).filter(Boolean).length,
    [md],
  );
  const readMin = Math.max(1, Math.round(words / 200));

  const [activeSection, setActiveSection] = useState(1);

  // TOC highlight follows SCROLL position, not just clicks. The report lives
  // inside #workspace-scroll, so the scroll listener is attached to that
  // pane (a viewport-rooted IntersectionObserver never fires for a nested
  // scroll container, and a narrow observer band can go stale — at
  // scrollTop 0 section 1 sat 1px below the band). The active section is
  // the last one whose top has passed a reading line 130px below the pane
  // top; at scrollTop 0 that defaults to section 1.
  useEffect(() => {
    const scroller = document.getElementById("workspace-scroll");
    if (!scroller) return;
    let raf = 0;
    const update = () => {
      const top = scroller.getBoundingClientRect().top;
      let current = 1;
      SECTIONS.forEach((s) => {
        const el = document.getElementById(`rsec-${s.n}`);
        if (el && el.getBoundingClientRect().top - top <= 130) current = s.n;
      });
      // The final section can never cross the reading line (too little
      // content below it — at max scroll its top still sat ~359px below
      // the pane top), so reaching the bottom of the pane selects the
      // last visible section instead.
      const atBottom =
        scroller.scrollTop + scroller.clientHeight >= scroller.scrollHeight - 4;
      if (atBottom) {
        const lastVisible = SECTIONS.filter((s) => s.n <= visibleSections).at(-1);
        if (lastVisible) current = lastVisible.n;
      }
      setActiveSection((prev) => (prev === current ? prev : current));
    };
    const onScroll = () => {
      cancelAnimationFrame(raf);
      raf = requestAnimationFrame(update);
    };
    update();
    scroller.addEventListener("scroll", onScroll, { passive: true });
    return () => {
      scroller.removeEventListener("scroll", onScroll);
      cancelAnimationFrame(raf);
    };
  }, [visibleSections]);

  const scrollToSection = (n: number) => {
    if (visibleSections < n) return;
    setActiveSection(n);
    document.getElementById(`rsec-${n}`)?.scrollIntoView({
      behavior: reducedMotion ? "auto" : "smooth",
      block: "start",
    });
  };

  const download = (kind: "md" | "txt" | "html") => {
    const safeName =
      query
        .toLowerCase()
        .replace(/[^a-z0-9]+/g, "-")
        .replace(/^-+|-+$/g, "")
        .slice(0, 48) || "nexus-research";
    if (kind === "md") {
      blobDownload(`${safeName}.md`, md, "text/markdown");
    } else if (kind === "txt") {
      const plain = md.replace(/[`*_>#]/g, "").replace(/\n{3,}/g, "\n\n").trim();
      blobDownload(`${safeName}.txt`, plain, "text/plain");
    } else {
      blobDownload(`${safeName}.html`, buildHtmlExport(md, query, isLive), "text/html");
    }
  };

  /* PDF export: a real PDF file generated directly from the report data
     (jsPDF, loaded on demand so it never bloats the first load). This
     replaced window.print(): Chrome — mobile especially — writes a printed
     page with Type 3 fonts whose glyphs do not paint in PDF viewers, so
     the report came out as blank pages even though the text was in the
     file. Generating the PDF here sidesteps the print pipeline entirely. */
  const downloadPdf = async () => {
    const { buildReportPdf, reportPdfFilename } = await import("../lib/pdf");
    const doc = buildReportPdf({ data, query, meta, words, readMin, isLive });
    doc.save(reportPdfFilename(query));
  };

  return (
    <div data-testid="report-window">
      {/* document meta line */}
      <div className="mb-3 flex flex-wrap items-center gap-x-2 gap-y-1 text-[0.78rem] tabular-nums text-muted" data-testid="report-meta">
        <span><b className="text-ink">{meta.sources}</b> sources</span>
        <span aria-hidden="true">·</span>
        <span><b className="text-ink">{meta.claims}</b> verified claims</span>
        <span aria-hidden="true">·</span>
        <span><b className="text-ink">{meta.sections}/8</b> sections</span>
        <span aria-hidden="true">·</span>
        <span><b className="text-ink">{words.toLocaleString()}</b> words</span>
        <span aria-hidden="true">·</span>
        <span><b className="text-ink">{readMin} min</b> read</span>
        <span aria-hidden="true">·</span>
        <span><b className="text-ink">{data.findings.length}</b> findings</span>
      </div>

      <div className="flex items-start gap-5 print:block">
        {/* table of contents */}
        <nav aria-label="Report contents" className="sticky top-[64px] hidden w-44 shrink-0 lg:block print:hidden" data-testid="report-toc">
          <div className="mb-2 text-[0.65rem] font-extrabold uppercase tracking-[0.14em] text-muted2">Contents</div>
          <ol className="space-y-0.5">
            {SECTIONS.map((s) => {
              const available = visibleSections >= s.n;
              const active = activeSection === s.n && available;
              return (
                <li key={s.n}>
                  <button
                    type="button"
                    onClick={() => scrollToSection(s.n)}
                    disabled={!available}
                    aria-current={active ? "true" : undefined}
                    className={`relative flex w-full items-baseline gap-2 rounded-r-lg rounded-l-[3px] px-2.5 py-1.5 text-left text-[0.78rem] transition ${
                      active
                        ? "bg-emerald/[0.12] font-bold text-ink"
                        : available
                          ? "font-medium text-muted hover:bg-ink/[0.05] hover:text-ink"
                          : "cursor-default font-medium text-muted2/60"
                    }`}
                  >
                    {active && <span className="absolute left-0 top-1 bottom-1 w-[3px] rounded-full bg-emerald" aria-hidden="true" />}
                    <span className="w-4 shrink-0 text-right tabular-nums text-[0.68rem] font-bold" style={{ color: available ? FINDING_TEXT_COLORS[(s.n - 1) % FINDING_TEXT_COLORS.length] : undefined }}>
                      {s.n}
                    </span>
                    <span className="leading-snug">{s.title}</span>
                  </button>
                </li>
              );
            })}
          </ol>
        </nav>

        {/* the document */}
        <section aria-label="Research report" className="min-w-0 flex-1 print:block">
      <div className="report-paper report-frame overflow-hidden rounded-3xl border border-[#E3DECB] print:overflow-visible print:rounded-none print:border-0">
        {/* title bar */}
        <div className="flex flex-wrap items-center gap-x-3 gap-y-2 border-b border-muted/[0.14] bg-[linear-gradient(90deg,rgba(0,217,122,0.08),rgba(0,184,169,0.05)_45%,rgba(232,163,23,0.07))] px-4 py-3.5">
          <span className="flex gap-1.5" aria-hidden="true">
            <span className="h-[11px] w-[11px] rounded-full bg-[#ff5f57]" />
            <span className="h-[11px] w-[11px] rounded-full bg-[#febc2e]" />
            <span className="h-[11px] w-[11px] rounded-full bg-[#28c840]" />
          </span>
          <span className="font-display text-[0.72rem] font-bold tracking-[0.14em] text-[#1E3A5F]">RESEARCH REPORT</span>
          <span className="min-w-0 flex-1 truncate text-[0.82rem] text-paperink">{query}</span>
          {/* The sample report keeps its label so it is never mistaken for
              live research; a live report carries no badge at all. */}
          {!isLive && (
            <span className="hidden shrink-0 whitespace-nowrap rounded-full bg-gold px-2.5 py-1 text-[0.62rem] font-extrabold tracking-[0.08em] text-[#0A1418] sm:inline-block">
              DEMO — SAMPLE DATA, NOT LIVE RESEARCH
            </span>
          )}
          <span className="hidden whitespace-nowrap text-[0.68rem] tabular-nums text-papermuted md:inline">{stamp}</span>
        </div>
        {!isLive && (
          <div className="px-3 py-1.5 sm:hidden">
            <span className="inline-block rounded-full bg-gold px-2.5 py-1 text-[0.6rem] font-extrabold tracking-[0.06em] text-[#0A1418]">
              DEMO — SAMPLE DATA, NOT LIVE RESEARCH
            </span>
          </div>
        )}

        {/* export toolbar */}
        <div className="flex flex-wrap items-center gap-2 border-b border-muted/[0.12] bg-cream/70 px-4 py-2.5 print:hidden">
          <span className="text-[0.68rem] font-extrabold uppercase tracking-[0.12em] text-papermuted">Export</span>
          <ExportButton icon={<FileText size={14} />} label="Markdown" onClick={() => download("md")} />
          <ExportButton icon={<FileCode2 size={14} />} label="Text" onClick={() => download("txt")} />
          <ExportButton icon={<Download size={14} />} label="HTML" onClick={() => download("html")} />
          <ExportButton icon={<FileDown size={14} />} label="PDF" onClick={downloadPdf} />
        </div>

        <div className="px-4 py-5 sm:px-5">
          {visibleSections === 0 && (
            <div className="py-12 text-center">
              <p className="font-display text-[1.05rem] font-bold text-paperink2">
                {running ? "The crew is working" : "No report yet"}
              </p>
              <p className="mx-auto mt-1.5 max-w-[420px] text-[0.85rem] leading-relaxed text-papermuted">
                {running
                  ? "Sections will appear here as WRITER composes them — SCOUT is still gathering sources."
                  : "Press Run and the crew will research your question."}
              </p>
            </div>
          )}

          {/* 1 · Executive Summary */}
          {show(1) && (
            <motion.div id="rsec-1" {...sectionAnim(reducedMotion)}>
              <div className="rounded-2xl border border-emerald/25 border-l-4 border-l-emerald bg-[linear-gradient(135deg,rgba(0,217,122,0.09),rgba(0,184,169,0.06))] px-4 py-4 leading-[1.7] text-paperink">
                <SectionTitle>Executive Summary</SectionTitle>
                {data.execSummary.map((p, i) => (
                  <Para key={i} parts={p} />
                ))}
              </div>
            </motion.div>
          )}

          {/* 2 · Research Scope & Method */}
          {show(2) && (
            <motion.div id="rsec-2" {...sectionAnim(reducedMotion)}>
              <SectionBlock title="Research Scope & Method">
                {data.scope.map((p, i) => (
                  <Para key={i} parts={p} />
                ))}
              </SectionBlock>
            </motion.div>
          )}

          {/* 3 · Key Findings */}
          {show(3) && (
            <motion.div id="rsec-3" {...sectionAnim(reducedMotion)}>
              <SectionTitle sub="numbered, evidence-backed">Key Findings</SectionTitle>
              {data.findings.map((f, i) => (
                <div
                  key={i}
                  className="mb-2 flex gap-3 rounded-2xl border border-muted/[0.14] border-l-[3px] bg-[linear-gradient(135deg,rgba(255,253,246,0.78),rgba(247,245,236,0.62))] px-4 py-3.5 leading-[1.6] text-paperink transition hover:translate-x-[3px]"
                  style={{ borderLeftColor: FINDING_COLORS[i % FINDING_COLORS.length] }}
                  data-testid={`finding-${i + 1}`}
                >
                  <span
                    className="grid h-7 w-7 shrink-0 place-items-center rounded-[9px] text-[0.78rem] font-extrabold text-paperink2"
                    style={{ background: FINDING_COLORS[i % FINDING_COLORS.length] }}
                  >
                    {i + 1}
                  </span>
                  <span>
                    {renderInline(f.text, `f${i}`)}
                    {flagged && f.flag && (
                      <span className="ml-2 inline-flex items-center gap-1 whitespace-nowrap rounded-full border border-[#E8A317]/70 bg-[#E8A317]/20 px-2 py-0.5 align-middle text-[0.62rem] font-extrabold text-[#7A5200]">
                        <TriangleAlert size={11} /> {f.flag}
                      </span>
                    )}
                  </span>
                </div>
              ))}
            </motion.div>
          )}

          {/* 4 · Detailed Analysis */}
          {show(4) && (
            <motion.div id="rsec-4" {...sectionAnim(reducedMotion)}>
              <SectionBlock title="Detailed Analysis">
                {data.analysis.map((sub) => (
                  <div key={sub.title}>
                    <h4 className="mb-1 mt-4 font-display text-[0.95rem] font-bold text-[#1E3A5F] first:mt-0">{sub.title}</h4>
                    {sub.paragraphs.map((p, i) => (
                      <Para key={i} parts={p} />
                    ))}
                  </div>
                ))}
              </SectionBlock>
            </motion.div>
          )}

          {/* 5 · Comparative Perspective */}
          {show(5) && (
            <motion.div id="rsec-5" {...sectionAnim(reducedMotion)}>
              <SectionBlock title="Comparative Perspective">
                {data.comparative.map((p, i) => (
                  <Para key={i} parts={p} />
                ))}
              </SectionBlock>
            </motion.div>
          )}

          {/* 6 · Implications */}
          {show(6) && (
            <motion.div id="rsec-6" {...sectionAnim(reducedMotion)}>
              <SectionBlock title="Implications">
                {data.implications.map((p, i) => (
                  <Para key={i} parts={p} />
                ))}
              </SectionBlock>
            </motion.div>
          )}

          {/* 7 · Limitations & Caveats */}
          {show(7) && (
            <motion.div id="rsec-7" {...sectionAnim(reducedMotion)}>
              <SectionBlock title="Limitations & Caveats">
                {data.limitations.map((p, i) => (
                  <Para key={i} parts={p} />
                ))}
              </SectionBlock>
            </motion.div>
          )}

          {/* 8 · Sources */}
          {show(8) && (
            <motion.div id="rsec-8" {...sectionAnim(reducedMotion)}>
              <h3 className="mb-2.5 mt-5 font-display text-[1rem] font-bold text-paperink2">
                Sources{" "}
                <span className="font-body text-[0.72rem] font-medium text-papermuted">
                  {data.sources.length} clickable citation cards · exact URLs
                </span>
              </h3>
              <div className="grid gap-2.5 sm:grid-cols-2">
                {data.sources.map((s: Cite, i: number) => (
                  <a
                    key={s.url}
                    href={s.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex items-start gap-2.5 rounded-2xl border border-muted/[0.13] bg-[linear-gradient(135deg,rgba(255,253,246,0.72),rgba(247,245,236,0.58))] px-3.5 py-3 text-paperink no-underline shadow-[inset_0_1px_0_rgba(255,255,255,0.04)] transition hover:-translate-y-0.5 hover:border-emerald/50 hover:shadow-[0_12px_30px_rgba(0,0,0,0.18)]"
                  >
                    <span className="grid h-[27px] w-[27px] shrink-0 place-items-center rounded-[9px] bg-teal/[0.16] text-[#1E7A6E]">
                      <ArrowUpRight size={14} />
                    </span>
                    <span className="min-w-0">
                      <span className="block text-[0.65rem] font-bold tracking-[0.06em] text-[#1E3A5F]">
                        CITATION {i + 1} · {new URL(s.url).hostname.replace("www.", "")}
                      </span>
                      <strong className="block text-[0.78rem] font-semibold leading-[1.4]">{s.label}</strong>
                      <small className="mt-0.5 block max-w-[390px] truncate text-[0.64rem] text-papermuted">{s.url}</small>
                    </span>
                  </a>
                ))}
              </div>

            </motion.div>
          )}
        </div>
      </div>
        </section>
      </div>
    </div>
  );
}

function ExportButton({ icon, label, onClick }: { icon: React.ReactNode; label: string; onClick: () => void }) {
  return (
    <button
      type="button"
      onClick={onClick}
      className="flex h-8 items-center justify-center gap-1.5 rounded-lg border border-[#D8D2C4] bg-cream px-2.5 text-[0.75rem] font-bold text-paperink shadow-sm transition hover:border-emerald hover:text-[#0B7A5E]"
    >
      {icon} {label}
    </button>
  );
}

function blobDownload(filename: string, content: string, mime: string) {
  const blob = new Blob([content], { type: `${mime};charset=utf-8` });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}

function buildHtmlExport(md: string, query: string, isLive?: boolean): string {
  const body = md.replace(/\[([^\]]+)\]\((https?:[^)]+)\)/g, '<a href="$2" target="_blank" rel="noopener">$1</a>')
    .split("\n\n")
    .map((block) => {
      const t = block.trim();
      if (t.startsWith("# ")) return `<h1>${t.slice(2)}</h1>`;
      if (t.startsWith("### ")) return `<h3>${t.slice(4)}</h3>`;
      if (/^\d+\./.test(t) || t.startsWith("- ")) return `<ul>${t.split("\n").map((l) => `<li>${l.replace(/^\d+\.\s+/, "").replace(/^-\s+/, "")}</li>`).join("")}</ul>`;
      return `<p>${t.replace(/\n/g, " ")}</p>`;
    })
    .join("\n");
  return `<!doctype html><html lang="en"><head><meta charset="utf-8"><title>${query} — Nexus Research</title><style>body{font-family:Inter,system-ui,sans-serif;max-width:820px;margin:0 auto;padding:32px 20px;line-height:1.7;color:#1B2530;background:#FFFDF6}h1{font-size:1.6rem;color:#11161D}h3{color:#1E3A5F}a{color:#1E3A5F}</style></head><body><div style="height:8px;border-radius:99px;background:linear-gradient(90deg,#00D97A,#E8A317);margin-bottom:24px"></div><p style="color:#1E3A5F;font-size:12px;font-weight:800;letter-spacing:.14em">✦ NEXUS RESEARCH AI · RESEARCH REPORT · ${isLive ? "LIVE RESEARCH" : "DEMO — SAMPLE DATA"}</p>${body}<footer style="color:#5B6472;font-size:12px;margin-top:24px">Generated by Nexus Research AI. Citation links open source pages in a new tab.</footer></body></html>`;
}
