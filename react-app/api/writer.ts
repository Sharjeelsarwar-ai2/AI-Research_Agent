/* WRITER — step 4 of the live pipeline. One Gemini call.
 * Returns the full 8-section Markdown report with inline citations to real
 * Tavily URLs only. Like app.py, it deterministically appends any Tavily
 * source the model forgot to list, so the Sources section never depends on
 * the model remembering to repeat URLs.
 *
 * POST /api/writer  { query, depth?, style?, evidence, synthesis, verification, sources }
 * → 200 { report }
 * → 503 { error: "keys_not_configured" } when GEMINI_API_KEY is missing.
 */
import {
  DEPTH_RULES,
  geminiCall,
  geminiKey,
  keysNotConfigured,
  readBody,
  REPORT_CONTRACT,
  requirePost,
  send,
  STYLE_RULES,
  type ApiRequest,
  type ApiResponse,
} from "./_lib.js";

interface SourceIn {
  title?: string;
  url?: string;
}

function ensureSourcesListed(report: string, sources: SourceIn[]): string {
  const used = sources.filter((s) => s.url);
  if (used.length === 0) return report;
  const missing = used.filter((s) => !report.includes(s.url as string));
  if (missing.length === 0) return report;
  const lines = missing.map((s) => `- [${s.title ?? s.url}](${s.url})`);
  const trimmed = report.trimEnd();
  if (/^#{1,2}\s+Sources\s*$/m.test(trimmed)) {
    return `${trimmed}\n${lines.join("\n")}\n`;
  }
  return `${trimmed}\n\n# Sources\n\n${lines.join("\n")}\n`;
}

export default async function handler(req: ApiRequest, res: ApiResponse): Promise<void> {
  if (!requirePost(req, res)) return;
  if (!geminiKey()) {
    keysNotConfigured(res);
    return;
  }
  const body = readBody(req);
  const query = String(body.query ?? "").trim();
  const depth = String(body.depth ?? "Standard");
  const style = String(body.style ?? "Detailed Report");
  const evidence = String(body.evidence ?? "").trim();
  const synthesis = String(body.synthesis ?? "").trim();
  const verification = String(body.verification ?? "").trim();
  const sources = Array.isArray(body.sources) ? (body.sources as SourceIn[]) : [];
  if (!query || !evidence || !synthesis || !verification) {
    send(res, 400, { error: "missing_input" });
    return;
  }

  // WRITER (app.py) — goal: "Write the final structured report in the
  // requested style and depth, citing only real Tavily URLs." Backstory:
  // "You are a precise report composer. You turn verified findings into a
  // polished, well-structured report in the requested style, with clear
  // headings and a Sources section that lists only URLs actually returned
  // by Tavily. You never add a source you did not receive."
  const prompt = `You are WRITER, the Report Composer of the Nexus Research crew.
Goal: Write the final structured report in the requested style and depth, citing only real Tavily URLs.

CURRENT USER REQUEST:
${query}

OUTPUT STYLE: ${STYLE_RULES[style] ?? STYLE_RULES["Detailed Report"]}

RESEARCH DEPTH:
${DEPTH_RULES[depth] ?? DEPTH_RULES.Standard}

SCOUT'S EVIDENCE PACK:
${evidence}

ANALYST'S SYNTHESIS:
${synthesis}

VERIFIER'S VERIFICATION REPORT:
${verification}

You are WRITER. Write the final report from the VERIFIER's verified findings,
in the output style above.

${REPORT_CONTRACT}`;

  try {
    const report = await geminiCall(prompt);
    send(res, 200, { report: ensureSourcesListed(report, sources) });
  } catch (err) {
    const status = typeof (err as { status?: unknown } | null)?.status === "number" ? (err as { status: number }).status : 502;
    send(res, status, { error: "upstream_error" });
  }
}
