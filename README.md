# ✦ Nexus Research AI

A single-agent **agentic web research and report application** built for deployment on Streamlit Community Cloud.

## Stack

- Python
- CrewAI
- Gemini 3.5 Flash-Lite
- Tavily Web Search
- Streamlit
- GitHub
- Streamlit Secrets

## Architecture

```text
User
  ↓
Streamlit UI
  ↓
CrewAI Single Agent
  ↓
Gemini 3.5 Flash-Lite
  ↕
Tavily Web Search Tool
  ↓
Source-backed research report
```

The agent is not a fixed search pipeline. It can decide when to use the Tavily tool, refine searches, inspect returned evidence, and synthesize the final report.

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
