/* ANALYST — step 2 of the live pipeline. One Gemini call.
 *
 * POST /api/analyst  { query, depth?, evidence }
 * → 200 { synthesis }
 * → 503 { error: "keys_not_configured" } when GEMINI_API_KEY is missing.
 */
import {
  DEPTH_RULES,
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
  const depth = String(body.depth ?? "Standard");
  const evidence = String(body.evidence ?? "").trim();
  if (!query || !evidence) {
    send(res, 400, { error: "missing_input" });
    return;
  }

  // ANALYST (app.py) — goal: "Synthesize the scout's evidence into clear
  // patterns, comparisons and trade-offs." Backstory: "You are a sharp
  // insight analyst. You read the scout's evidence, spot agreements and
  // contradictions, compare options side by side, and turn raw findings
  // into structured insight. You never invent numbers or claims that the
  // evidence does not support."
  const prompt = `You are ANALYST, the Insight Analyst of the Nexus Research crew.
Goal: Synthesize the scout's evidence into clear patterns, comparisons and trade-offs.

CURRENT USER REQUEST:
${query}

RESEARCH DEPTH:
${DEPTH_RULES[depth] ?? DEPTH_RULES.Standard}

SCOUT'S EVIDENCE PACK:
${evidence}

You are ANALYST. Using SCOUT's evidence pack, synthesize the findings: find
patterns, agreements and contradictions, compare the main options side by side,
and draw out the trade-offs and implications. Organize the synthesis into clear
themes with the evidence behind each. Do not invent numbers or claims the
evidence does not support; mark anything weakly supported as uncertain.
Return a structured synthesis: themes, patterns, comparisons and trade-offs,
each tied to the scout's evidence.`;

  try {
    const synthesis = await geminiCall(prompt);
    send(res, 200, { synthesis });
  } catch (err) {
    const status = typeof (err as { status?: unknown } | null)?.status === "number" ? (err as { status: number }).status : 502;
    send(res, status, { error: "upstream_error" });
  }
}
