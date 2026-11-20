/* Saved-report history: Supabase (via /api/history) with an on-device
 * localStorage mirror as the fallback. The app works before Supabase is
 * configured — entries are then kept on this device only — and switches
 * to the database automatically once SUPABASE_URL /
 * SUPABASE_SERVICE_ROLE_KEY are set in Vercel and the app is redeployed.
 * The browser never talks to Supabase directly. */
import type { RecentResearch } from "../data/demo";
import type { LiveSource } from "./live";

export type ReportMode = "live" | "demo";

export interface HistoryEntry extends RecentResearch {
  id: string;
  mode: ReportMode;
  createdAt: string; // ISO timestamp
  depth: string;
  style: string;
  findings: number;
}

/** Full saved report: list entry + the payload needed to reopen it. */
export interface SavedReport extends HistoryEntry {
  data: {
    md: string | null; // live: full markdown; demo: null (static demo data)
    sources: LiveSource[];
    kpis: { sources: number; claims: number; findings: number; sections: number };
    flagged: boolean;
  };
}

export interface SavePayload {
  title: string;
  question: string;
  mode: ReportMode;
  depth: string;
  style: string;
  words: number;
  sources: number;
  findings: number;
  data: SavedReport["data"];
}

export type HistorySource = "supabase" | "local";

const CACHE_KEY = "nexus-history-v1";
const CACHE_MAX = 50;

function uid(): string {
  try {
    return `local-${crypto.randomUUID()}`;
  } catch {
    return `local-${Date.now().toString(36)}-${Math.floor(Math.random() * 1e9).toString(36)}`;
  }
}

export function formatHistoryDate(iso: string): string {
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return iso;
  return d.toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" });
}

interface ApiRow {
  id: string;
  title: string;
  question: string;
  mode: ReportMode;
  depth: string;
  style: string;
  words: number;
  sources: number;
  findings: number;
  saved: boolean;
  created_at: string;
  data?: SavedReport["data"];
}

function toEntry(row: ApiRow): HistoryEntry {
  return {
    id: row.id,
    title: row.title,
    question: row.question,
    date: formatHistoryDate(row.created_at),
    words: row.words,
    sources: row.sources,
    saved: row.saved,
    mode: row.mode,
    createdAt: row.created_at,
    depth: row.depth,
    style: row.style,
    findings: row.findings,
  };
}

function toSaved(row: ApiRow): SavedReport | null {
  if (!row.data) return null;
  return { ...toEntry(row), data: row.data };
}

/* ---- on-device cache (fallback + instant first paint) ---- */

export function readCacheEntries(): HistoryEntry[] {
  return readCache().map(({ data: _data, ...entry }) => entry);
}

export function readCache(): SavedReport[] {
  try {
    const raw = window.localStorage.getItem(CACHE_KEY);
    if (!raw) return [];
    const parsed = JSON.parse(raw) as SavedReport[];
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return [];
  }
}

function writeCache(rows: SavedReport[]): void {
  try {
    window.localStorage.setItem(CACHE_KEY, JSON.stringify(rows.slice(0, CACHE_MAX)));
  } catch {
    /* storage full or unavailable — the database is the source of truth */
  }
}

function upsertCache(row: SavedReport): void {
  const rows = readCache().filter((r) => r.id !== row.id);
  rows.unshift(row);
  writeCache(rows);
}

/* ---- api ---- */

/** Newest first. Prefers the database; falls back to the device cache.
 * The cache only ever holds reports saved on this device (with their
 * full payload); the database is the source of truth for everything. */
export async function loadHistory(): Promise<{ entries: HistoryEntry[]; source: HistorySource }> {
  try {
    const res = await fetch("/api/history");
    if (!res.ok) throw new Error(`history ${res.status}`);
    const rows = (await res.json()) as ApiRow[];
    return { entries: rows.map(toEntry), source: "supabase" };
  } catch {
    const cached = readCache();
    return { entries: cached.map(({ data: _data, ...entry }) => entry), source: "local" };
  }
}

/** Full report by id (database first, device cache second). */
export async function loadReport(id: string): Promise<SavedReport | null> {
  if (!id) return null;
  if (id.startsWith("local-")) {
    return readCache().find((r) => r.id === id) ?? null;
  }
  try {
    const res = await fetch(`/api/history?id=${encodeURIComponent(id)}`);
    if (!res.ok) throw new Error(`history ${res.status}`);
    return toSaved((await res.json()) as ApiRow);
  } catch {
    return readCache().find((r) => r.id === id) ?? null;
  }
}

/** Save a finished run. Returns the list entry, or null when even the
 * device cache could not keep it. Always mirrors to the device cache. */
export async function saveReport(payload: SavePayload): Promise<HistoryEntry | null> {
  const createdAt = new Date().toISOString();
  try {
    const res = await fetch("/api/history", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    if (!res.ok) throw new Error(`history ${res.status}`);
    const row = (await res.json()) as ApiRow;
    const saved = toSaved(row);
    if (saved) upsertCache(saved);
    return saved ? toEntry(row) : null;
  } catch {
    const local: SavedReport = {
      ...payload,
      id: uid(),
      date: formatHistoryDate(createdAt),
      createdAt,
      saved: false,
    };
    upsertCache(local);
    const { data: _data, ...entry } = local;
    return entry;
  }
}

export async function toggleSaved(id: string, saved: boolean): Promise<boolean> {
  const rows = readCache();
  const cached = rows.find((r) => r.id === id);
  if (cached) {
    cached.saved = saved;
    writeCache(rows);
  }
  if (id.startsWith("local-")) return true;
  try {
    const res = await fetch(`/api/history?id=${encodeURIComponent(id)}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ saved }),
    });
    return res.ok;
  } catch {
    return false;
  }
}

export async function deleteReport(id: string): Promise<boolean> {
  writeCache(readCache().filter((r) => r.id !== id));
  if (id.startsWith("local-")) return true;
  try {
    const res = await fetch(`/api/history?id=${encodeURIComponent(id)}`, { method: "DELETE" });
    return res.ok;
  } catch {
    return false;
  }
}
