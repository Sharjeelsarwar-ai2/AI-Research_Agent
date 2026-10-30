# ✦ Nexus Research AI

A professional **multi-agent web research and report application** built for deployment on Streamlit Community Cloud. A four-agent CrewAI crew researches every question — each agent is shown live in the Agent Dock as its own robot avatar — and the final report is delivered in a dedicated Report Window.

## Stack

- Python
- CrewAI (sequential multi-agent crew)
- Gemini 3.5 Flash-Lite
- Tavily Web Search
- Streamlit
- GitHub
- Streamlit Secrets

## Architecture

```text
User
  ↓
Streamlit UI — Agent Dock (SCOUT · ANALYST · VERIFIER · WRITER)
  ↓
CrewAI sequential crew
  SCOUT (Tavily Web Search) → ANALYST (synthesis) → VERIFIER (fact-check) → WRITER (report)
  ↓
Gemini 3.5 Flash-Lite
  ↕
Tavily Web Search Tool
  ↓
Complete, citation-backed research report in the Report Window
```

## The crew

| Agent | Role | Colour | Job |
| --- | --- | --- | --- |
| SCOUT | Web Scout | Cyan | Runs Tavily searches, gathers live sources with exact titles and URLs |
| ANALYST | Insight Analyst | Violet | Synthesizes evidence into patterns, comparisons and trade-offs |
| VERIFIER | Fact Checker | Mint green | Cross-checks claims against independent sources, flags uncertainty |
| WRITER | Report Composer | Amber | Writes the final structured report, citing only real Tavily URLs |

Each agent has its own role, goal and backstory, and tasks are chained so each agent works from the previous agent's output. The Agent Dock shows every agent's live status (Idle / Working / Done) and an activity feed line as each task finishes.

## Complete report structure

Every report — in every style — contains all eight sections, completed:

1. Executive Summary
2. Research Scope & Method
3. Key Findings (numbered, each with inline citations)
4. Detailed Analysis (multiple titled subsections)
5. Comparative Perspective
6. Implications
7. Limitations & Caveats
8. Sources (every source used, with its exact URL)

No finding is produced without a source behind it: every Key Finding and every substantive claim carries an inline citation to a real Tavily-returned URL, and the Verifier checks that every finding is cited. The Report Window renders the sections as distinct structured blocks, the Sources as clickable citation cards, and the Markdown / Text / HTML / PDF export buttons inside the window. PDF and HTML exports include the same citations and Sources.

Detailed Report style targets a long-form 2200–3200 word report; Executive Brief keeps the same complete structure, more concise per section.

## Demo mode

The workspace has a **▶ Run demo** button that runs the four agents on a pre-written sample report (the AI coding assistant market in 2026) with no API calls and no keys needed. It is clearly labelled **"Demo — sample data, not live research"** in the Report Window, and it never runs automatically. Live research still requires real secrets.

## GitHub deployment

This project is designed for **cloud-only deployment**. There is no `.env.example` and no local secrets file in the repository.

Upload these files:

```text
app.py
requirements.txt
README.md
.gitignore
.streamlit/config.toml
```

## Streamlit Cloud Secrets

In Streamlit Cloud:

**App → Settings → Secrets**

Add:

```toml
GEMINI_API_KEY = "YOUR_GEMINI_API_KEY"
TAVILY_API_KEY = "YOUR_TAVILY_API_KEY"

GEMINI_MODEL = "gemini-3.5-flash-lite"
MAX_SEARCH_RESULTS = 6
```

The application reads the API keys directly from `st.secrets`.

Do not put either API key in GitHub.

## Model

The application defaults to:

```text
gemini-3.5-flash-lite
```

If Google's Gemini API uses a different public model identifier for your account, change only:

```toml
GEMINI_MODEL = "..."
```

in Streamlit Secrets. No code change is required.

## Deployment

1. Create a GitHub repository.
2. Upload the project files.
3. Open Streamlit Community Cloud.
4. Create a new app from the GitHub repository.
5. Select `app.py` as the main file.
6. Add the Secrets shown above.
7. Deploy.

## Research modes

### Quick
Focused research with a smaller search scope.

### Standard
Several targeted searches with cross-checking.

### Deep
Broader iterative research with stronger cross-checking and preference for primary sources.

## Report styles

- Executive Brief
- Detailed Report
- Technical Analysis

## Security

API keys are never entered into the Streamlit interface and are never stored in the GitHub repository.

`.gitignore` excludes:

```text
.streamlit/secrets.toml
.env
.env.*
```

## Important

The model and package ecosystem can change. If Google changes the public Gemini model identifier or CrewAI changes its Gemini integration, update the corresponding model/package configuration rather than exposing API credentials in the app.

Web research can contain outdated, incorrect, incomplete, or conflicting information. Review generated reports before using them for consequential decisions.
