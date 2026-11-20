import type { Cite, Inline } from "../data/demo";

/* Parse a live WRITER report (Markdown, 8 sections per the report contract
   in ~/workspace/research-agent-source/app.py) into the structured
   ReportData shape the ReportWindow renders. Returns null if the text has
   no recognisable sections — the caller then shows the raw markdown. */

export interface AnalysisSub {
  title: string;
  paragraphs: Inline[][];
}

export interface ParsedReport {
  execSummary: Inline[][];
  scope: Inline[][];
  findings: { text: Inline[]; flag?: string }[];
  analysis: AnalysisSub[];
  comparative: Inline[][];
  implications: Inline[][];
  limitations: Inline[][];
  sources: Cite[];
}

const SECTION_TITLES = [
  "Executive Summary",
  "Research Scope & Method",
  "Key Findings",
  "Detailed Analysis",
  "Comparative Perspective",
  "Implications",
  "Limitations & Caveats",
  "Sources",
] as const;

function inline(text: string): Inline[] {
  const parts: Inline[] = [];
  const re = /\[([^\]]+)\]\((https?:[^)\s]+)\)/g;
  let last = 0;
  let m: RegExpExecArray | null;
  while ((m = re.exec(text)) !== null) {
    if (m.index > last) parts.push(text.slice(last, m.index));
    parts.push({ label: m[1], url: m[2] });
    last = m.index + m[0].length;
  }
  if (last < text.length) parts.push(text.slice(last));
  return parts.filter((p) => p !== "");
}

function paragraphs(body: string): Inline[][] {
  return body
    .split(/\n\s*\n/)
    .map((b) => b.replace(/\s*\n\s*/g, " ").trim())
    .filter(Boolean)
    .map((b) => inline(b.replace(/^[-*]\s+/, "")));
}

function splitSections(md: string): Map<string, string> {
  const sections = new Map<string, string>();
  const re = /^#{1,2}\s+(.+?)\s*$/gm;
  const heads: { title: string; start: number; bodyStart: number }[] = [];
  let m: RegExpExecArray | null;
  while ((m = re.exec(md)) !== null) {
    heads.push({ title: m[1].trim(), start: m.index, bodyStart: m.index + m[0].length });
  }
  heads.forEach((h, i) => {
    const end = i + 1 < heads.length ? heads[i + 1].start : md.length;
    const known = SECTION_TITLES.find((t) => h.title.toLowerCase() === t.toLowerCase());
    sections.set(known ?? h.title, md.slice(h.bodyStart, end).trim());
  });
  return sections;
}

function parseFindings(body: string): { text: Inline[]; flag?: string }[] {
  const items: string[] = [];
  let current: string | null = null;
  for (const raw of body.split("\n")) {
    const line = raw.trim();
    const num = line.match(/^\d+[.)]\s+(.*)/);
    if (num) {
      if (current !== null) items.push(current);
      current = num[1];
    } else if (current !== null && line) {
      current += " " + line;
    }
  }
  if (current !== null) items.push(current);
  return items.map((t) => ({ text: inline(t) }));
}

function parseAnalysis(body: string): AnalysisSub[] {
  const subs: AnalysisSub[] = [];
  const re = /^###\s+(.+?)\s*$/gm;
  const heads: { title: string; start: number; bodyStart: number }[] = [];
  let m: RegExpExecArray | null;
  while ((m = re.exec(body)) !== null) {
    heads.push({ title: m[1].trim(), start: m.index, bodyStart: m.index + m[0].length });
  }
  if (heads.length === 0) {
    return body.trim() ? [{ title: "Analysis", paragraphs: paragraphs(body) }] : [];
  }
  heads.forEach((h, i) => {
    const end = i + 1 < heads.length ? heads[i + 1].start : body.length;
    subs.push({ title: h.title, paragraphs: paragraphs(body.slice(h.bodyStart, end)) });
  });
  return subs;
}

function parseSources(body: string): Cite[] {
  const out: Cite[] = [];
  const seen = new Set<string>();
  const re = /\[([^\]]+)\]\((https?:[^)\s]+)\)/g;
  let m: RegExpExecArray | null;
  while ((m = re.exec(body)) !== null) {
    if (!seen.has(m[2])) {
      seen.add(m[2]);
      out.push({ label: m[1], url: m[2] });
    }
  }
  // Plain "- https://…" lines as a fallback.
  for (const line of body.split("\n")) {
    const u = line.trim().match(/^(?:-\s*)?(https?:\/\/\S+)/);
    if (u && !seen.has(u[1].replace(/[),.]+$/, ""))) {
      const url = u[1].replace(/[),.]+$/, "");
      seen.add(url);
      out.push({ label: url, url });
    }
  }
  return out;
}

export function parseReportMarkdown(md: string): ParsedReport | null {
  const sections = splitSections(md);
  const hasKnown = SECTION_TITLES.some((t) => sections.has(t));
  if (!hasKnown) return null;
  const findingsBody = sections.get("Key Findings") ?? "";
  return {
    execSummary: paragraphs(sections.get("Executive Summary") ?? ""),
    scope: paragraphs(sections.get("Research Scope & Method") ?? ""),
    findings: parseFindings(findingsBody),
    analysis: parseAnalysis(sections.get("Detailed Analysis") ?? ""),
    comparative: paragraphs(sections.get("Comparative Perspective") ?? ""),
    implications: paragraphs(sections.get("Implications") ?? ""),
    limitations: paragraphs(sections.get("Limitations & Caveats") ?? ""),
    sources: parseSources(sections.get("Sources") ?? ""),
  };
}

/** Count the words in a markdown report (same method as the demo meta line). */
export function countWords(md: string): number {
  return md.replace(/[#*`>\[\]()]/g, " ").split(/\s+/).filter(Boolean).length;
}
