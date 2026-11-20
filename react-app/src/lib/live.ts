/* Client for the live research API (api/*.ts). Every call returns either
   its payload or { error: "keys_not_configured" } when GEMINI_API_KEY /
   TAVILY_API_KEY are missing on the server — the UI then shows the
   keys guidance banner and the demo stays available. */

export interface LiveSource {
  title: string;
  url: string;
  domain: string;
  published: string;
  snippet: string;
}

export const KEYS_NOT_CONFIGURED = "keys_not_configured";

async function post<T>(path: string, body: unknown): Promise<T | { error: string }> {
  const res = await fetch(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  try {
    return (await res.json()) as T | { error: string };
  } catch {
    return { error: "upstream_error" };
  }
}

export function isKeysError(r: unknown): r is { error: string } {
  return typeof r === "object" && r !== null && "error" in r;
}

export const api = {
  scout: (query: string, depth: string) =>
    post<{ sources: LiveSource[]; evidence: string }>("/api/scout", { query, depth }),
  analyst: (query: string, depth: string, evidence: string) =>
    post<{ synthesis: string }>("/api/analyst", { query, depth, evidence }),
  verifier: (query: string, evidence: string, synthesis: string) =>
    post<{ verification: string }>("/api/verifier", { query, evidence, synthesis }),
  writer: (
    query: string,
    depth: string,
    style: string,
    evidence: string,
    synthesis: string,
    verification: string,
    sources: LiveSource[],
  ) =>
    post<{ report: string }>("/api/writer", {
      query,
      depth,
      style,
      evidence,
      synthesis,
      verification,
      sources,
    }),
};
