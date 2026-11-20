/* HISTORY — saved reports in Supabase (Postgres table `reports`).
 *
 * The browser never talks to Supabase directly: these routes use the
 * SERVICE-ROLE key (server env only, bypasses RLS) and the table has
 * Row Level Security on with no public policies, so the anon key can
 * read/write nothing. Without SUPABASE_URL / SUPABASE_SERVICE_ROLE_KEY
 * the routes answer 503 supabase_not_configured and the frontend falls
 * back to on-device history (localStorage).
 *
 * GET  /api/history            → 200 [{id,title,question,mode,depth,style,words,sources,findings,saved,created_at}] (newest first, 50)
 * GET  /api/history?id=<uuid>  → 200 {…full row incl. data} | 404 {error:"not_found"}
 * POST /api/history            {title,question,mode,depth,style,words,sources,findings,data} → 200 {…created row}
 * PATCH /api/history?id=<uuid> {saved} → 200 {…updated row}
 * DELETE /api/history?id=<uuid> → 200 {deleted:true}
 */
import {
  readBody,
  send,
  supabaseNotConfigured,
  supabaseRest,
  supabaseServiceKey,
  supabaseUrl,
  type ApiRequest,
  type ApiResponse,
} from "./_lib.js";

const LIST_COLUMNS = "id,title,question,mode,depth,style,words,sources,findings,saved,created_at";

function configured(res: ApiResponse): boolean {
  if (!supabaseUrl() || !supabaseServiceKey()) {
    supabaseNotConfigured(res);
    return false;
  }
  return true;
}

function bad(res: ApiResponse, error: string): void {
  send(res, 400, { error });
}

export default async function handler(req: ApiRequest, res: ApiResponse): Promise<void> {
  const method = req.method ?? "GET";
  if (!["GET", "POST", "PATCH", "DELETE"].includes(method)) {
    send(res, 405, { error: "method_not_allowed" });
    return;
  }
  if (!configured(res)) return;
  const id = (req.query?.id ?? "").trim();

  try {
    if (method === "GET") {
      if (id) {
        const r = await supabaseRest(`reports?select=*&id=eq.${encodeURIComponent(id)}`, "GET");
        if (!r.ok) return send(res, 502, { error: "upstream_error" });
        const rows = JSON.parse(r.text) as unknown[];
        if (rows.length === 0) return send(res, 404, { error: "not_found" });
        return send(res, 200, rows[0]);
      }
      const r = await supabaseRest(
        `reports?select=${LIST_COLUMNS}&order=created_at.desc&limit=50`,
        "GET",
      );
      if (!r.ok) return send(res, 502, { error: "upstream_error" });
      return send(res, 200, JSON.parse(r.text));
    }

    if (method === "POST") {
      const b = readBody(req);
      const title = String(b.title ?? "").trim().slice(0, 200);
      const question = String(b.question ?? "").trim().slice(0, 2000);
      const mode = b.mode === "live" || b.mode === "demo" ? b.mode : "";
      const data = b.data;
      if (!title || !question || !mode || !data || typeof data !== "object") {
        return bad(res, "missing_fields");
      }
      const row = {
        title,
        question,
        mode,
        depth: String(b.depth ?? "Standard").slice(0, 40),
        style: String(b.style ?? "Detailed Report").slice(0, 40),
        words: Math.max(0, Math.floor(Number(b.words) || 0)),
        sources: Math.max(0, Math.floor(Number(b.sources) || 0)),
        findings: Math.max(0, Math.floor(Number(b.findings) || 0)),
        saved: false,
        data,
      };
      const r = await supabaseRest("reports", "POST", row);
      if (!r.ok) return send(res, 502, { error: "upstream_error" });
      const rows = JSON.parse(r.text) as unknown[];
      return send(res, 200, rows[0] ?? row);
    }

    if (!id) return bad(res, "missing_id");
    if (method === "PATCH") {
      const b = readBody(req);
      if (typeof b.saved !== "boolean") return bad(res, "missing_fields");
      const r = await supabaseRest(
        `reports?id=eq.${encodeURIComponent(id)}`,
        "PATCH",
        { saved: b.saved },
      );
      if (!r.ok) return send(res, 502, { error: "upstream_error" });
      const rows = JSON.parse(r.text) as unknown[];
      if (rows.length === 0) return send(res, 404, { error: "not_found" });
      return send(res, 200, rows[0]);
    }

    // DELETE
    const r = await supabaseRest(`reports?id=eq.${encodeURIComponent(id)}`, "DELETE");
    if (!r.ok) return send(res, 502, { error: "upstream_error" });
    return send(res, 200, { deleted: true });
  } catch {
    return send(res, 502, { error: "upstream_error" });
  }
}
