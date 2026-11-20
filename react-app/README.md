# Nexus Research AI — React + Vite (Vercel-ready)

Four-agent research crew (SCOUT → ANALYST → VERIFIER → WRITER) rebuilt from
the Streamlit original (`~/workspace/research-agent-source/app.py`) as a
React + Vite app shell. Demo mode runs on sample data; **Run live research**
does real research through serverless API routes backed by Tavily + Gemini.

## Run it

```bash
npm install
npm run dev      # local preview (demo works; live needs keys — see below)
npm run build    # production build (tsc + vite, includes api/*.ts typecheck)
```

## Themes

Dark is the default ("Midnight Institutional", unchanged from the approved
preview). The Sun/Moon toggle in the top bar switches to the light
"Ivory & Navy" theme instantly; the choice persists in `localStorage`
(`nexus-theme`) and first visits follow `prefers-color-scheme`. A tiny inline
script in `index.html` sets `data-theme` on `<html>` before first paint, so
there is no flash of the wrong theme.

Light theme hex values: page `#F7F5EF`, panels `#FFFFFF`, ink `#101828`,
muted `#5B6472`, navy `#1E3A5F`, bronze `#A16207`. Agent colours are deepened
for light backgrounds — SCOUT `#00875A`, ANALYST `#1D6FE0`, VERIFIER `#B45309`,
WRITER `#0B7C6E` (dark: `#00D97A` / `#4DA3FF` / `#E8A317` / `#00B8A9`). The
CTA stays vivid jade `#00D97A` with dark text; the report window stays cream
paper `#FFFDF6` in both themes. No violet, no pastels, no rainbow gradients.

## Live research — API contract

The run is split into **one serverless function per agent** so each call
stays within Vercel's function time limits (see below). The frontend calls
them in sequence and updates agent status, the activity feed, sources and
the report as each step returns — the live feed works exactly like the demo.

| Endpoint | Does | Request (JSON) | Response (JSON) |
|---|---|---|---|
| `POST /api/scout` | Tavily search (advanced, `include_raw_content`) | `{ query, depth? }` | `{ sources: [{title, url, domain, published, snippet}], evidence }` |
| `POST /api/analyst` | One Gemini call — synthesis from the evidence pack | `{ query, depth?, evidence }` | `{ synthesis }` |
| `POST /api/verifier` | One Gemini call — cross-checks, verified claims + flagged items | `{ query, evidence, synthesis }` | `{ verification }` |
| `POST /api/writer` | One Gemini call — full 8-section Markdown report, citations to real Tavily URLs only | `{ query, depth?, style?, evidence, synthesis, verification, sources }` | `{ report }` |

Agent prompts, depth rules (Quick / Standard / Deep), style rules
(Executive Brief / Detailed Report / Technical Analysis) and the 8-section
report contract are ported faithfully from `app.py` (see `api/_lib.ts` and
each route file). WRITER also deterministically appends any Tavily source
the model forgot to list, exactly like the Streamlit app does.

**Error shape** (all routes): missing keys → HTTP 503
`{ "error": "keys_not_configured" }`. The UI shows a dismissible guidance
banner ("add GEMINI_API_KEY and TAVILY_API_KEY in Vercel → Project Settings
→ Environment Variables, then redeploy") and the demo keeps working. Other
failures return `{ "error": "upstream_error" }` (HTTP 502) or
`{ "error": "method_not_allowed" }` (405) / `{ "error": "missing_query" }` /
`{ "error": "missing_input" }` (400).

### Function time limits — why 60s

`vercel.json` sets `functions["api/*.ts"].maxDuration = 60`. Reasoning: each
route makes exactly **one** external call (one Tavily search or one Gemini
generation at temperature 0.2), which normally completes in a few seconds to
~30s for a long Detailed Report; 60s is the maximum the Vercel Hobby plan
allows, so it is the largest safe ceiling without a plan upgrade. The
frontend's sequential orchestration means a slow step only delays the next
agent, it never aborts the whole run. If a route ever times out on the Hobby
plan, the fix is a Pro plan (up to 300s) — not a longer single call.

## Environment variables (keys only from env — never in code)

| Variable | Required | Default | Notes |
|---|---|---|---|
| `GEMINI_API_KEY` | yes, for live | — | Google AI Studio key |
| `TAVILY_API_KEY` | yes, for live | — | Tavily API key |
| `GEMINI_MODEL` | no | `gemini-3.5-flash-lite` | Gemini model for analyst/verifier/writer |
| `MAX_SEARCH_RESULTS` | no | `6` | Tavily `max_results` (clamped to 12) |

## Deploy to Vercel

1. Create a GitHub repo and push this project (no repo exists yet).
2. In Vercel: **Add New → Project → Import** the repo (framework: Vite,
   build `npm run build`, output `dist` — all set in `vercel.json`).
3. **Before the first live run:** Project Settings → Environment Variables →
   add `GEMINI_API_KEY` and `TAVILY_API_KEY` (Production scope; optionally
   `GEMINI_MODEL` / `MAX_SEARCH_RESULTS`), then **Redeploy**.
4. Open the deployment, press **Run live research**, and check the report
   renders. **Run demo** works with no keys at all.

## What is installed

| Library | Version | For |
|---|---|---|
| tailwindcss + @tailwindcss/vite | 4.3.5 | Utility styling, Vite plugin |
| motion | 14.14.0 | React animations |
| lucide-react | 1.73.0 | Icons |
| react / react-dom | 19.3.1 | UI |

## Notes

- `vite.config.ts` keeps `base: './'` — valid for Vercel static output.
- Demo data and the staged demo state machine are untouched; the live run
  reuses the same `runState` shape (status / feed / sources / report), so
  the rail, tabs and TOC behave identically in both modes.
- The report TOC highlight follows scroll position (IntersectionObserver
  rooted on the workspace scroll pane), not just clicks.
