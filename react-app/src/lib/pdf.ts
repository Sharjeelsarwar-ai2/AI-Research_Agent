import { jsPDF } from "jspdf";
import type { Inline, ReportData } from "../data/demo";

/* ------------------------------------------------------------------ */
/*  Real PDF export — generated directly with jsPDF.                    */
/*                                                                     */
/*  This replaces the old window.print() export. Chrome (especially     */
/*  mobile) writes a printed page with Type 3 fonts whose glyphs do    */
/*  not paint in PDF viewers, so the report came out as blank pages     */
/*  even though the text was in the file. Generating the PDF from the   */
/*  report data sidesteps the browser's print pipeline entirely: the    */
/*  file is a proper text PDF with embedded standard fonts.            */
/* ------------------------------------------------------------------ */

const PAGE_W = 612; // letter, pt
const PAGE_H = 792;
const MARGIN = 56;
const CONTENT_W = PAGE_W - MARGIN * 2;
const BOTTOM = PAGE_H - 48;

const C = {
  ink: [27, 37, 48], // #1B2530 paperink
  ink2: [17, 22, 29], // #11161D paperink2
  muted: [91, 100, 114], // #5B6472 papermuted
  navy: [30, 58, 95], // #1E3A5F
  emerald: [0, 135, 90], // darkened #00D97A for print
  amber: [180, 83, 9], // darkened #E8A317
  rule: [214, 218, 214],
} as const;

type RGB = readonly [number, number, number];

interface Seg {
  text: string;
  url?: string;
}

function segments(parts: Inline[]): Seg[] {
  const out: Seg[] = [];
  for (const p of parts) {
    if (typeof p === "string") {
      if (p) out.push({ text: p });
    } else {
      out.push({ text: p.label, url: p.url });
    }
  }
  return out;
}

export function reportPdfFilename(query: string): string {
  const base = query
    .replace(/[\\/:*?"<>|]/g, " ")
    .replace(/\s+/g, " ")
    .trim()
    .slice(0, 100);
  return `${base || "Nexus Research"} — Nexus Research.pdf`;
}

export function buildReportPdf(opts: {
  data: ReportData;
  query: string;
  meta: { sources: number; claims: number; sections: number };
  words: number;
  readMin: number;
  isLive?: boolean;
}): jsPDF {
  const { data, query, meta, words, readMin, isLive } = opts;
  const doc = new jsPDF({ unit: "pt", format: "letter", orientation: "portrait", compress: true });
  let y = 0;

  const setColor = (c: RGB) => doc.setTextColor(c[0], c[1], c[2]);
  const setFill = (c: RGB) => doc.setFillColor(c[0], c[1], c[2]);

  function newPage() {
    doc.addPage();
    y = MARGIN;
  }

  function ensureSpace(needed: number) {
    if (y + needed > BOTTOM) newPage();
  }

  /* No space before closing punctuation, or after an opening paren — so
     "( [GitHub Copilot](url) )" renders as "(GitHub Copilot)", not
     "( GitHub Copilot )". */
  function needsSpace(prev: string | null, next: string): boolean {
    if (!prev) return false;
    if (prev.endsWith("(")) return false;
    if (/^[),.;:?!%]/.test(next)) return false;
    return true;
  }

  /* Draw one paragraph of mixed plain/link segments with word wrap.
     Link words are drawn in navy and made clickable. Returns nothing;
     advances y. */
  function drawParagraph(parts: Inline[], size = 10.5, lineH = 15.5) {
    const segs = segments(parts);
    doc.setFont("helvetica", "normal");
    doc.setFontSize(size);
    // Flatten into words, keeping each word's link (if any).
    const words: { text: string; url?: string }[] = [];
    for (const s of segs) {
      for (const w of s.text.split(/\s+/).filter(Boolean)) {
        words.push({ text: w, url: s.url });
      }
    }
    let x = MARGIN;
    let lineStart = true;
    let prevWord: string | null = null;
    const spaceW = doc.getTextWidth(" ");
    for (const w of words) {
      const wW = doc.getTextWidth(w.text);
      const gap = !lineStart && needsSpace(prevWord, w.text) ? spaceW : 0;
      if (!lineStart && x + gap + wW > MARGIN + CONTENT_W) {
        y += lineH;
        ensureSpace(lineH);
        x = MARGIN;
        lineStart = true;
      }
      if (!lineStart) x += gap;
      setColor(w.url ? C.navy : C.ink);
      if (w.url) {
        doc.textWithLink(w.text, x, y, { url: w.url });
      } else {
        doc.text(w.text, x, y);
      }
      x += wW;
      lineStart = false;
      prevWord = w.text;
    }
    y += lineH;
  }

  function drawHeading(num: string, title: string) {
    ensureSpace(52);
    y += 10;
    doc.setFont("helvetica", "bold");
    doc.setFontSize(13);
    setColor(C.navy);
    doc.text(`${num}.  ${title}`, MARGIN, y);
    y += 8;
    setFill(C.rule);
    doc.rect(MARGIN, y, CONTENT_W, 0.75, "F");
    y += 16;
  }

  function drawSubHeading(title: string) {
    ensureSpace(40);
    doc.setFont("helvetica", "bold");
    doc.setFontSize(11.5);
    setColor(C.ink2);
    doc.text(title, MARGIN, y);
    y += 18;
  }

  /* ---------------- header ---------------- */
  y = MARGIN;
  // accent bar: emerald → amber
  setFill(C.emerald);
  doc.rect(MARGIN, y, CONTENT_W * 0.62, 5, "F");
  setFill(C.amber);
  doc.rect(MARGIN + CONTENT_W * 0.62, y, CONTENT_W * 0.38, 5, "F");
  y += 24;

  doc.setFont("helvetica", "bold");
  doc.setFontSize(9);
  setColor(C.navy);
  doc.text(
    `NEXUS RESEARCH AI  ·  RESEARCH REPORT  ·  ${isLive ? "LIVE RESEARCH" : "DEMO — SAMPLE DATA"}`,
    MARGIN,
    y,
  );
  y += 26;

  doc.setFont("helvetica", "bold");
  doc.setFontSize(20);
  setColor(C.ink2);
  const titleLines = doc.splitTextToSize(query, CONTENT_W);
  for (const line of titleLines) {
    ensureSpace(26);
    doc.text(line, MARGIN, y);
    y += 26;
  }
  y += 6;

  doc.setFont("helvetica", "normal");
  doc.setFontSize(9.5);
  setColor(C.muted);
  const findings = data.findings.length;
  doc.text(
    `${meta.sources} sources  ·  ${meta.claims} verified claims  ·  ${meta.sections}/8 sections  ·  ${words.toLocaleString()} words  ·  ${readMin} min read  ·  ${findings} findings`,
    MARGIN,
    y,
  );
  y += 10;
  setFill(C.rule);
  doc.rect(MARGIN, y, CONTENT_W, 0.75, "F");
  y += 22;

  /* ---------------- sections ---------------- */
  const sections: { num: string; title: string; body: () => void }[] = [
    {
      num: "1",
      title: "Executive Summary",
      body: () => data.execSummary.forEach((p) => drawParagraph(p)),
    },
    {
      num: "2",
      title: "Research Scope & Method",
      body: () => data.scope.forEach((p) => drawParagraph(p)),
    },
    {
      num: "3",
      title: "Key Findings",
      body: () => {
        data.findings.forEach((f, i) => {
          ensureSpace(34);
          doc.setFont("helvetica", "bold");
          doc.setFontSize(10.5);
          setColor(C.emerald);
          doc.text(`${i + 1}.`, MARGIN, y);
          // finding text, indented past the number
          const indent = 22;
          const segs = segments(f.text);
          doc.setFont("helvetica", "normal");
          doc.setFontSize(10.5);
          const wordsArr: { text: string; url?: string }[] = [];
          for (const s of segs) {
            for (const w of s.text.split(/\s+/).filter(Boolean)) {
              wordsArr.push({ text: w, url: s.url });
            }
          }
          let x = MARGIN + indent;
          let lineStart = true;
          let prevWord: string | null = null;
          const spaceW = doc.getTextWidth(" ");
          const lineH = 15.5;
          for (const w of wordsArr) {
            const wW = doc.getTextWidth(w.text);
            const gap = !lineStart && needsSpace(prevWord, w.text) ? spaceW : 0;
            if (!lineStart && x + gap + wW > MARGIN + CONTENT_W) {
              y += lineH;
              ensureSpace(lineH);
              x = MARGIN + indent;
              lineStart = true;
            }
            if (!lineStart) x += gap;
            setColor(w.url ? C.navy : C.ink);
            if (w.url) doc.textWithLink(w.text, x, y, { url: w.url });
            else doc.text(w.text, x, y);
            x += wW;
            lineStart = false;
            prevWord = w.text;
          }
          y += lineH;
          if (f.flag) {
            doc.setFont("helvetica", "normal");
            doc.setFontSize(9);
            setColor(C.amber);
            doc.text(`Flag: ${f.flag}`, MARGIN + indent, y);
            y += 14;
          }
          y += 4;
        });
      },
    },
    {
      num: "4",
      title: "Detailed Analysis",
      body: () => {
        data.analysis.forEach((sub) => {
          drawSubHeading(sub.title);
          sub.paragraphs.forEach((p) => drawParagraph(p));
          y += 4;
        });
      },
    },
    {
      num: "5",
      title: "Comparative Perspective",
      body: () => data.comparative.forEach((p) => drawParagraph(p)),
    },
    {
      num: "6",
      title: "Implications",
      body: () => data.implications.forEach((p) => drawParagraph(p)),
    },
    {
      num: "7",
      title: "Limitations & Caveats",
      body: () => data.limitations.forEach((p) => drawParagraph(p)),
    },
    {
      num: "8",
      title: "Sources",
      body: () => {
        data.sources.forEach((s, i) => {
          ensureSpace(30);
          doc.setFont("helvetica", "bold");
          doc.setFontSize(10);
          setColor(C.ink2);
          doc.text(`${i + 1}.`, MARGIN, y);
          const indent = 22;
          const labelLines = doc.splitTextToSize(s.label, CONTENT_W - indent);
          doc.setFont("helvetica", "normal");
          setColor(C.ink);
          labelLines.forEach((line: string, li: number) => {
            if (li > 0) {
              y += 14;
              ensureSpace(14);
            }
            doc.text(line, MARGIN + indent, y);
          });
          y += 14;
          // clickable URL, wrapped
          doc.setFont("helvetica", "normal");
          doc.setFontSize(8.5);
          setColor(C.navy);
          const urlLines = doc.splitTextToSize(s.url, CONTENT_W - indent);
          urlLines.forEach((line: string, li: number) => {
            if (li > 0) {
              y += 12;
              ensureSpace(12);
            }
            doc.textWithLink(line, MARGIN + indent, y, { url: s.url });
          });
          y += 18;
        });
      },
    },
  ];

  for (const s of sections) {
    // Skip a section that has no content (e.g. a run still composing).
    const hasContent =
      s.num === "3"
        ? data.findings.length > 0
        : s.num === "4"
          ? data.analysis.length > 0
          : s.num === "8"
            ? data.sources.length > 0
            : true;
    if (!hasContent) continue;
    drawHeading(s.num, s.title);
    s.body();
    y += 6;
  }

  /* ---------------- footer + page numbers ---------------- */
  const pages = doc.getNumberOfPages();
  for (let p = 1; p <= pages; p++) {
    doc.setPage(p);
    doc.setFont("helvetica", "normal");
    doc.setFontSize(8.5);
    setColor(C.muted);
    doc.text(`Nexus Research AI  ·  ${query}`, MARGIN, PAGE_H - 30);
    const pageLabel = `Page ${p} of ${pages}`;
    const pw = doc.getTextWidth(pageLabel);
    doc.text(pageLabel, PAGE_W - MARGIN - pw, PAGE_H - 30);
    setFill(C.rule);
    doc.rect(MARGIN, PAGE_H - 38, CONTENT_W, 0.5, "F");
  }
  // closing line on the last page
  doc.setPage(pages);
  y += 8;
  ensureSpace(20);
  doc.setFont("helvetica", "normal");
  doc.setFontSize(9);
  setColor(C.muted);
  doc.text("Generated by Nexus Research AI. Citation links open source pages.", MARGIN, y);

  return doc;
}
