/* VERIFIER — step 3 of the live pipeline. One Gemini call.
 *
 * POST /api/verifier  { query, evidence, synthesis }
 * → 200 { verification }
 * → 503 { error: "keys_not_configured" } when GEMINI_API_KEY is missing.
 */
import {
  geminiCall,
  geminiKey,
  keysNotConfigured,
  readBody,
  requirePost,
  send,
  type ApiRequest,
  type ApiResponse,
} from "./_lib.js";

export default async function handler(req: ApiRequest, res: ApiResponse): Promise<void> {
  if (!requirePost(req, res)) return;
  if (!geminiKey()) {
    keysNotConfigured(res);
    return;
  }
  const body = readBody(req);
  const query = String(body.query ?? "").trim();
  const evidence = String(body.evidence ?? "").trim();
  const synthesis = String(body.synthesis ?? "").trim();
  if (!query || !evidence || !synthesis) {
    send(res, 400, { error: "missing_input" });
    return;
  }

  // VERIFIER (app.py) — goal: "Cross-check important claims against
  // independent sources and flag anything uncertain or unverified."
  // Backstory: "You are a sceptical fact checker. You re-check the
  // important claims against independent sources, mark anything that is
  // single-sourced, outdated or uncertain, and strike anything that cannot
  // be verified. You never invent a URL, a statistic or a quotation."
  const prompt = `You are VERIFIER, the Fact Checker of the Nexus Research crew.
Goal: Cross-check important claims against independent sources and flag anything uncertain or unverified.

CURRENT USER REQUEST:
${query}

SCOUT'S EVIDENCE PACK:
${evidence}

ANALYST'S SYNTHESIS:
${synthesis}

You are VERIFIER. Cross-check the ANALYST's important claims against
independent sources in SCOUT's evidence pack. Confirm what is corroborated,
flag anything single-sourced, outdated or uncertain, and strike anything that
cannot be verified. Also check that every finding carries a citation to a real
URL from the evidence pack — flag any finding without one. List the verified
claims and the flagged items separately. Never invent a URL, statistic or
quotation. Only cite URLs from the evidence pack.
Return a verification report: verified claims plus a flagged-items list of
uncertain or unverified claims.`;

  try {
    const verification = await geminiCall(prompt);
    send(res, 200, { verification });
  } catch (err) {
    const status = typeof (err as { status?: unknown } | null)?.status === "number" ? (err as { status: number }).status : 502;
    send(res, status, { error: "upstream_error" });
  }
}
