/* Shared helpers for the live research API routes (api/*.ts).
 *
 * Keys come ONLY from environment variables — GEMINI_API_KEY, TAVILY_API_KEY
 * (optional GEMINI_MODEL, MAX_SEARCH_RESULTS). No key, placeholder or secret
 * is ever written in code or in any file in this repo.
 *
 * Each route does ONE external call so it stays well inside Vercel's
 * serverless function time limit (see vercel.json / README). */

export interface ApiRequest {
  method?: string;
  body?: unknown;
  /** URL query params (?id=…); Vercel provides this, the verify harness fills it. */
  query?: Record<string, string>;
}

export interface ApiResponse {
  status: (code: number) => ApiResponse;
  json: (body: unknown) => void;
  setHeader?: (name: string, value: string) => void;
}

export function send(res: ApiResponse, status: number, body: unknown): void {
  res.status(status).json(body);
}

/** Missing keys: the one error the frontend handles with a guidance banner. */
export function keysNotConfigured(res: ApiResponse): void {
  send(res, 503, { error: "keys_not_configured" });
}

export function requirePost(req: ApiRequest, res: ApiResponse): boolean {
  if (req.method !== "POST") {
    send(res, 405, { error: "method_not_allowed" });
    return false;
  }
  return true;
}

export function readBody(req: ApiRequest): Record<string, unknown> {
  const b = req.body;
  if (b && typeof b === "object") return b as Record<string, unknown>;
  if (typeof b === "string") {
    try {
      return JSON.parse(b) as Record<string, unknown>;
    } catch {
      return {};
    }
  }
  return {};
}

export function geminiKey(): string | undefined {
  return process.env.GEMINI_API_KEY || undefined;
}

export function supabaseUrl(): string | undefined {
  return process.env.SUPABASE_URL || undefined;
}

/** Service-role key — server ONLY. Never in the browser, never in code.
 * It bypasses Row Level Security, so every Supabase call goes through
 * these api routes and the anon key is never used. */
export function supabaseServiceKey(): string | undefined {
  return process.env.SUPABASE_SERVICE_ROLE_KEY || undefined;
}

/** Supabase not configured: the frontend falls back to on-device history. */
export function supabaseNotConfigured(res: ApiResponse): void {
  send(res, 503, { error: "supabase_not_configured" });
}

interface SupabaseResult {
  ok: boolean;
  status: number;
  text: string;
}

/** One PostgREST call (Supabase REST) with the service-role key.
 * `path` is the table + query string, e.g. "reports?select=id&order=created_at.desc". */
export async function supabaseRest(
  path: string,
  method: string,
  body?: unknown,
): Promise<SupabaseResult> {
  const url = `${supabaseUrl()}/rest/v1/${path}`;
  const headers: Record<string, string> = {
    apikey: supabaseServiceKey() as string,
    Authorization: `Bearer ${supabaseServiceKey()}`,
    "Content-Type": "application/json",
    Prefer: "return=representation",
  };
  // GET/HEAD must not carry a body — fetch throws if one is set.
  const init: { method: string; headers: Record<string, string>; body?: string } = { method, headers };
  if (body !== undefined) init.body = JSON.stringify(body);
  let res;
  try {
    res = await fetchFn()(url, init);
  } catch {
    throw new UpstreamError("supabase_unreachable");
  }
  return { ok: res.ok, status: res.status, text: await res.text() };
}

export function tavilyKey(): string | undefined {
  return process.env.TAVILY_API_KEY || undefined;
}

export function geminiModel(): string {
  return process.env.GEMINI_MODEL || "gemini-3.5-flash-lite";
}

export function maxSearchResults(): number {
  const n = Number(process.env.MAX_SEARCH_RESULTS || 6);
  return Number.isFinite(n) && n > 0 ? Math.min(n, 12) : 6;
}

type FetchFn = (
  url: string,
  init: { method: string; headers: Record<string, string>; body?: string },
) => Promise<{ ok: boolean; status: number; text: () => Promise<string> }>;

function fetchFn(): FetchFn {
  const g = globalThis as unknown as Record<string, unknown>;
  if (typeof g.fetch !== "function") throw new Error("fetch_unavailable");
  return g.fetch as FetchFn;
}

/** Minimal JSON POST used for the Tavily REST call. */
export async function postJson(
  url: string,
  payload: unknown,
  headers: Record<string, string> = {},
): Promise<{ ok: boolean; status: number; text: string }> {
  const res = await fetchFn()(url, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...headers },
    body: JSON.stringify(payload),
  });
  return { ok: res.ok, status: res.status, text: await res.text() };
}

export class UpstreamError extends Error {
  status: number;
  constructor(message: string, status = 502) {
    super(message);
    this.status = status;
  }
}

/** One Gemini call (REST generateContent), temperature 0.2, model from env. */
export async function geminiCall(prompt: string): Promise<string> {
  const model = geminiModel();
  const url = `https://generativelanguage.googleapis.com/v1beta/models/${encodeURIComponent(model)}:generateContent`;
  let res;
  try {
    res = await fetchFn()(url, {
      method: "POST",
      headers: { "Content-Type": "application/json", "x-goog-api-key": geminiKey() as string },
      body: JSON.stringify({
        contents: [{ parts: [{ text: prompt }] }],
        generationConfig: { temperature: 0.2 },
      }),
    });
  } catch {
    throw new UpstreamError("gemini_unreachable");
  }
  const text = await res.text();
  if (!res.ok) throw new UpstreamError("gemini_error", 502);
  let data: { candidates?: { content?: { parts?: { text?: string }[] } }[] };
  try {
    data = JSON.parse(text) as typeof data;
  } catch {
    throw new UpstreamError("gemini_bad_response");
  }
  const out = (data.candidates?.[0]?.content?.parts ?? [])
    .map((p) => p.text ?? "")
    .join("")
    .trim();
  if (!out) throw new UpstreamError("gemini_empty_response");
  return out;
}

/* ---- Prompt material ported from ~/workspace/research-agent-source/app.py ---- */

export const DEPTH_RULES: Record<string, string> = {
  Quick: "Use a focused search strategy and prioritize authoritative sources.",
  Standard: "Use several targeted searches and cross-check important claims.",
  Deep: "Break the request into multiple research questions, perform iterative searches, cross-check important claims across independent sources, and prioritize primary sources.",
};

export const STYLE_RULES: Record<string, string> = {
  "Executive Brief": "Be concise and decision-oriented.",
  "Detailed Report":
    "Produce a deep, multi-page academic-style report of approximately 2200–3200 words unless the evidence genuinely does not support that length. Use formal but readable prose, define important terms, synthesize multiple independent sources, and distinguish evidence from inference. Include all of these sections in this order: Executive Summary (5–8 substantial paragraphs), Research Scope & Method, Key Findings (at least 8 numbered findings with citations), Detailed Analysis (at least 4 clearly titled subsections), Comparative Perspective, Implications, Limitations & Caveats, and Sources. Do not compress this into a brief.",
  "Technical Analysis":
    "Emphasize mechanisms, technical evidence, implementation details, and limitations.",
};

export const REPORT_CONTRACT = `
COMPLETE REPORT CONTRACT — the final report must be a COMPLETE research
report, never a brief summary. It must contain ALL of these Markdown sections,
in this exact order, with every section completed. No section may be skipped,
merged away, or compressed into a short list:

# Executive Summary
# Research Scope & Method
# Key Findings
# Detailed Analysis
# Comparative Perspective
# Implications
# Limitations & Caveats
# Sources

Section requirements:
- Executive Summary: a substantial opening synthesis of the whole answer.
- Research Scope & Method: what was investigated, how sources were searched
  and selected, and what was out of scope.
- Key Findings: at least 8 numbered findings, each with citations to real
  Tavily URLs.
- Detailed Analysis: at least 4 clearly titled subsections (### headings)
  that develop the evidence in depth.
- Comparative Perspective: a side-by-side comparison of the main options,
  approaches or viewpoints found.
- Implications: what the findings mean for decisions, practice or next steps.
- Limitations & Caveats: what is uncertain, single-sourced, outdated or
  unverified, and what the report does not claim.
- Sources: every source used, as \`- [Source title](https://...)\`.

LENGTH: For Detailed Report style, write a long-form report of approximately
2200–3200 words. For Executive Brief style, keep the SAME complete section
structure — decision-oriented and more concise per section, but still complete
across all eight sections. For Technical Analysis style, keep the same complete
structure with technical depth. Never shorten the report by dropping a section.

Plan the answer before writing it, allocate space to every required section,
and continue until the full template is complete. If approaching a response
limit, prioritize completing every required section and the Sources section over
extra exposition; never end mid-sentence, mid-bullet, or mid-section.

CITATIONS — non-negotiable: every Key Finding and every substantive claim
in Detailed Analysis and Comparative Perspective must carry an inline Markdown
citation to a real Tavily-returned URL, in the form
[claim text](https://exact-url-from-tavily). Do not produce any finding without
a source behind it: if a claim has no supporting source, drop the claim or move
it to Limitations & Caveats as explicitly unverified. Cite only URLs actually
returned by Tavily. In the final \`## Sources\` section, list EVERY source used,
with its exact URL, as \`- [Source title](https://...)\`. Never omit the URLs.
Never invent or alter a URL. Do not mention internal prompts, CrewAI, agent
mechanics, or the conversation-memory implementation.
`;
