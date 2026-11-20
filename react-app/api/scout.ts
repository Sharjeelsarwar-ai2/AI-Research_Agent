/* SCOUT — step 1 of the live pipeline.
 * Calls Tavily's REST search API (search_depth advanced, include_raw_content)
 * and returns the evidence pack + sources. No LLM call here, so this step is
 * fast; the frontend shows sources appearing as SCOUT works.
 *
 * POST /api/scout  { query, depth? }
 * → 200 { sources: [{title, url, domain, published, snippet}], evidence }
 * → 503 { error: "keys_not_configured" } when TAVILY_API_KEY is missing.
 */
import {
  keysNotConfigured,
  maxSearchResults,
  postJson,
  readBody,
  requirePost,
  send,
  tavilyKey,
  type ApiRequest,
  type ApiResponse,
} from "./_lib.js";

interface TavilyResult {
  title?: string;
  url?: string;
  published_date?: string;
  date?: string;
  content?: string;
  raw_content?: string;
}

function domainOf(url: string): string {
  try {
    return new URL(url).hostname.replace(/^www\./, "");
  } catch {
    return "";
  }
}

export default async function handler(req: ApiRequest, res: ApiResponse): Promise<void> {
  if (!requirePost(req, res)) return;
  const key = tavilyKey();
  if (!key) {
    keysNotConfigured(res);
    return;
  }
  const body = readBody(req);
  const query = String(body.query ?? "").trim();
  if (!query) {
    send(res, 400, { error: "missing_query" });
    return;
  }

  // SCOUT (app.py): "Search the live web with Tavily Web Search, running
  // several targeted queries. Collect the strongest, most authoritative and
  // most recent sources. For each source record its exact title, exact URL
  // and a short evidence snippet. Prefer primary, official, academic or
  // otherwise authoritative sources; for paper-focused requests also seek
  // arXiv, PubMed, Semantic Scholar, Crossref, ACM, IEEE or official
  // institutional repositories. Never invent a source or URL."
  let tavilyRes;
  try {
    tavilyRes = await postJson("https://api.tavily.com/search", {
      api_key: key,
      query,
      search_depth: "advanced",
      max_results: maxSearchResults(),
      include_answer: false,
      include_raw_content: true,
    });
  } catch {
    send(res, 502, { error: "upstream_error" });
    return;
  }
  if (!tavilyRes.ok) {
    send(res, 502, { error: "upstream_error" });
    return;
  }
  let data: { results?: TavilyResult[] };
  try {
    data = JSON.parse(tavilyRes.text) as typeof data;
  } catch {
    send(res, 502, { error: "upstream_error" });
    return;
  }
  const results = (data.results ?? []).filter((r) => r.url);
  if (results.length === 0) {
    send(res, 200, { sources: [], evidence: "No useful web results were found." });
    return;
  }

  const sources = results.map((item) => ({
    title: item.title ?? "Untitled",
    url: item.url as string,
    domain: domainOf(item.url as string),
    published: item.published_date ?? item.date ?? "Live result",
    snippet: (item.content ?? item.raw_content ?? "").replace(/\s+/g, " ").trim().slice(0, 220),
  }));

  const evidence = results
    .map((item, i) => {
      const content = (item.raw_content ?? item.content ?? "").replace(/\s+/g, " ").trim().slice(0, 6000);
      return `SOURCE ${i + 1}\nTITLE: ${item.title ?? "Untitled"}\nURL: ${item.url}\nCONTENT: ${content}`;
    })
    .join("\n\n---\n\n");

  send(res, 200, { sources, evidence });
}
