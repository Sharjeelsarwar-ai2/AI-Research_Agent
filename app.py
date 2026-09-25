import re
from datetime import datetime
from html import escape
from urllib.parse import urlparse

import streamlit as st
from crewai import Agent, Crew, Process, Task, LLM
from crewai.tools import tool
from tavily import TavilyClient

# =========================================================
# Page configuration
# =========================================================
st.set_page_config(
    page_title="Nexus Research AI",
    page_icon="✦",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# =========================================================
# Streamlit Secrets
# =========================================================
GEMINI_API_KEY = st.secrets.get("GEMINI_API_KEY")
TAVILY_API_KEY = st.secrets.get("TAVILY_API_KEY")
GEMINI_MODEL = st.secrets.get("GEMINI_MODEL", "gemini-3.5-flash-lite")
MAX_SEARCH_RESULTS = int(st.secrets.get("MAX_SEARCH_RESULTS", 6))

if not GEMINI_API_KEY or not TAVILY_API_KEY:
    st.error(
        "Missing API credentials. Add GEMINI_API_KEY and TAVILY_API_KEY "
        "in Streamlit Cloud → App settings → Secrets."
    )
    st.stop()

# =========================================================
# Session memory
# =========================================================
if "messages" not in st.session_state:
    st.session_state.messages = []

if "research_history" not in st.session_state:
    st.session_state.research_history = []

# =========================================================
# Glassmorphism UI
# =========================================================
st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Space+Grotesk:wght@500;600;700&display=swap');

:root {
    --bg: #07101d;
    --panel: rgba(16, 29, 49, .72);
    --panel2: rgba(12, 24, 42, .68);
    --border: rgba(166, 190, 214, .16);
    --border-strong: rgba(141, 220, 255, .26);
    --text: #f2f7fb;
    --muted: #96a9bc;
    --cyan: #8de6ff;
    --violet: #b6a4ff;
    --mint: #91f1c5;
}

html, body, [class*="css"] {
    font-family: "DM Sans", sans-serif;
}

.stApp {
    background:
        radial-gradient(900px 520px at 8% -8%, rgba(91, 215, 255, .16), transparent 62%),
        radial-gradient(760px 520px at 96% 2%, rgba(155, 123, 255, .18), transparent 62%),
        radial-gradient(700px 480px at 50% 112%, rgba(74, 211, 160, .08), transparent 68%),
        #07101d;
    color: var(--text);
}

.stApp::before {
    content: "";
    position: fixed;
    inset: 0;
    pointer-events: none;
    background-image:
        linear-gradient(rgba(255,255,255,.017) 1px, transparent 1px),
        linear-gradient(90deg, rgba(255,255,255,.017) 1px, transparent 1px);
    background-size: 44px 44px;
    mask-image: linear-gradient(to bottom, black, transparent);
}

.block-container {
    max-width: 1180px;
    padding-top: 7.9rem;
    padding-bottom: 9.5rem;
}

header[data-testid="stHeader"], [data-testid="stToolbar"], [data-testid="stDecoration"], [data-testid="stStatusWidget"], footer { display:none !important; }
[data-testid="stSidebar"], [data-testid="collapsedControl"] { display:none !important; }

/* Floating glass navigation */
div[data-testid="stHorizontalBlock"]:has(.nav-brand) {
    position:fixed !important;
    z-index:999999 !important;
    top:1rem !important;
    left:50% !important;
    transform:translateX(-50%) !important;
    width:min(1180px,calc(100vw - 2rem)) !important;
    min-height:70px !important;
    padding:.55rem .7rem !important;
    border:1px solid rgba(182, 216, 239, .20) !important;
    border-radius:24px !important;
    background:linear-gradient(120deg,rgba(11,28,47,.82),rgba(22,25,53,.76)) !important;
    backdrop-filter:blur(30px) saturate(175%) !important;
    -webkit-backdrop-filter:blur(30px) saturate(175%) !important;
    box-shadow:0 24px 70px rgba(0,0,0,.40),inset 0 1px 0 rgba(255,255,255,.10) !important;
}

div[data-testid="stHorizontalBlock"]:has(.nav-brand)::after {
    content:""; position:absolute; inset:0; border-radius:inherit; pointer-events:none;
    background:linear-gradient(100deg,rgba(141,230,255,.08),transparent 36%,rgba(182,164,255,.08));
}

div[data-testid="stHorizontalBlock"]:has(.nav-brand) > div {
    padding:0 .25rem !important;
}

div[data-testid="stHorizontalBlock"]:has(.nav-brand) .stSelectbox > div > div {
    min-height:48px !important;
    border-radius:16px !important;
    background:rgba(255,255,255,.055) !important;
    border:1px solid rgba(255,255,255,.08) !important;
}

div[data-testid="stHorizontalBlock"]:has(.nav-brand) .stSelectbox label { display:none !important; }

div[data-testid="stHorizontalBlock"]:has(.nav-brand) div.stButton > button {
    min-height:48px !important;
    border-radius:16px !important;
    border:1px solid rgba(126,224,255,.28) !important;
    box-shadow:inset 0 1px 0 rgba(255,255,255,.08),0 8px 24px rgba(73,105,190,.16) !important;
}

.nav-brand { display:flex;align-items:center;gap:.65rem;font-family:"Space Grotesk",sans-serif;font-weight:700;font-size:1.02rem;white-space:nowrap; }
.nav-orb { width:38px;height:38px;border-radius:13px;display:grid;place-items:center;background:linear-gradient(135deg,rgba(127,227,255,.25),rgba(173,149,255,.25));border:1px solid rgba(127,227,255,.28);box-shadow:inset 0 1px 0 rgba(255,255,255,.1),0 8px 22px rgba(60,130,180,.16); }
.nav-label { color:#8fa3ba;font-size:.67rem;font-weight:700;text-transform:uppercase;letter-spacing:.08em;margin-bottom:.18rem; }
.nav-meta { color:#9fb0c5;font-size:.73rem;white-space:nowrap; }
.activity-wrap { display:flex;align-items:center;gap:.7rem;padding:.7rem .9rem;margin:.85rem 0 1rem;border:1px solid rgba(127,227,255,.16);border-radius:15px;background:rgba(8,25,42,.64);backdrop-filter:blur(18px);box-shadow:0 12px 35px rgba(0,0,0,.18); }
.activity-dot { width:9px;height:9px;border-radius:50%;background:#7fe3ff;box-shadow:0 0 0 5px rgba(127,227,255,.08),0 0 18px rgba(127,227,255,.75);animation:pulse 1.35s ease-in-out infinite; }
.activity-text { font-size:.82rem;color:#d9e8f7; } .activity-sub { font-size:.72rem;color:#7f94aa;margin-top:.1rem; }
@keyframes pulse { 0%,100%{transform:scale(.85);opacity:.55;} 50%{transform:scale(1.15);opacity:1;} }
@media(max-width:900px){
    div[data-testid="stHorizontalBlock"]:has(.nav-brand){
        top:.65rem !important; width:calc(100vw - 1rem) !important; border-radius:20px !important;
    }
    .block-container{padding-top:8rem;padding-bottom:8.5rem}
    .nav-meta{display:none}
}
@media(max-width:650px){
    div[data-testid="stHorizontalBlock"]:has(.nav-brand){min-height:64px !important}
    div[data-testid="stHorizontalBlock"]:has(.nav-brand) > div:nth-child(1){flex:1.3 1 0 !important}
    div[data-testid="stHorizontalBlock"]:has(.nav-brand) > div:nth-child(2){flex:1 1 0 !important}
    div[data-testid="stHorizontalBlock"]:has(.nav-brand) > div:nth-child(3){flex:1 1 0 !important}
    div[data-testid="stHorizontalBlock"]:has(.nav-brand) > div:nth-child(4){display:none !important}
    div[data-testid="stHorizontalBlock"]:has(.nav-brand) > div:nth-child(5){flex:1 1 0 !important}
    .nav-brand span:last-child{display:none}
    [data-testid="stBottomBlockContainer"] > div{width:calc(100vw - 1rem) !important;border-radius:21px !important}
}

.hero {
    padding: 2.2rem 2.4rem;
    border: 1px solid var(--border);
    border-radius: 28px;
    background:linear-gradient(135deg,rgba(18,39,64,.72),rgba(10,22,39,.58));
    backdrop-filter:blur(24px) saturate(135%);
    box-shadow:0 26px 85px rgba(0,0,0,.28),inset 0 1px 0 rgba(255,255,255,.07);
    margin-bottom: 1.2rem;
}

.badge {
    display: inline-flex;
    padding: .42rem .78rem;
    border: 1px solid rgba(86,216,255,.25);
    border-radius: 999px;
    background: rgba(86,216,255,.08);
    color: #8ce6ff;
    font-size: .76rem;
    font-weight: 700;
    letter-spacing: .06em;
}

.hero h1 {
    font-family: "Space Grotesk", sans-serif;
    font-size: clamp(2rem, 5vw, 4rem);
    line-height: 1.02;
    margin: 1rem 0 .7rem;
    letter-spacing: -.055em;
}

.gradient-text {
    background:linear-gradient(100deg,#ffffff 8%,#8de6ff 46%,#b6a4ff 92%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}

.hero p {
    color: var(--muted);
    font-size: 1rem;
    max-width: 850px;
    line-height: 1.7;
}

.section-title {
    font-family: "Space Grotesk", sans-serif;
    font-size: 1.15rem;
    font-weight: 700;
    margin: 1.15rem 0 .7rem;
}

.metric {
    padding: .95rem 1.05rem;
    border: 1px solid var(--border);
    border-radius: 18px;
    background: var(--panel);
    backdrop-filter: blur(18px);
}

.metric-label {
    color: var(--muted);
    font-size: .74rem;
    text-transform: uppercase;
    letter-spacing: .08em;
}

.metric-value {
    font-family: "Space Grotesk", sans-serif;
    font-size: 1.22rem;
    font-weight: 700;
    margin-top: .25rem;
}

.chat-card {
    padding: 1.1rem 1.2rem;
    border: 1px solid var(--border);
    border-radius: 20px;
    background: var(--panel2);
    backdrop-filter: blur(18px);
    margin: .7rem 0;
}

.user-label {
    color: #7fe3ff;
    font-size: .76rem;
    font-weight: 700;
    letter-spacing: .06em;
    text-transform: uppercase;
    margin-bottom: .45rem;
}

.agent-label {
    color: #b69cff;
    font-size: .76rem;
    font-weight: 700;
    letter-spacing: .06em;
    text-transform: uppercase;
    margin-bottom: .45rem;
}

.small-muted {
    color: var(--muted);
    font-size: .82rem;
}

.report-box {
    padding: 1.35rem;
    border: 1px solid var(--border);
    border-radius: 20px;
    background: rgba(8,22,38,.64);
}

div.stButton > button {
    border: 1px solid rgba(126,224,255,.25);
    border-radius: 14px;
    background: linear-gradient(135deg, rgba(48,126,162,.88), rgba(103,76,171,.88));
    color: white;
    font-weight: 700;
    min-height: 2.7rem;
}

div.stButton > button:hover {
    border-color: rgba(126,224,255,.7);
    transform: translateY(-1px);
}

/* Floating Claude-style chat composer */
[data-testid="stBottomBlockContainer"] {
    position:fixed !important; left:0 !important; right:0 !important; bottom:18px !important;
    z-index:999998 !important; background:transparent !important; border:0 !important;
    box-shadow:none !important; padding:0 !important;
}

[data-testid="stBottomBlockContainer"] > div {
    width:min(940px,calc(100vw - 2rem)) !important; margin:0 auto !important; padding:.48rem !important;
    border:1px solid rgba(177,210,236,.22) !important; border-radius:28px !important;
    background:linear-gradient(135deg,rgba(16,32,52,.90),rgba(25,28,57,.84)) !important;
    backdrop-filter:blur(30px) saturate(175%) !important; -webkit-backdrop-filter:blur(30px) saturate(175%) !important;
    box-shadow:0 26px 76px rgba(0,0,0,.48),inset 0 1px 0 rgba(255,255,255,.10) !important;
}

[data-testid="stBottomBlockContainer"] > div::before {
    content:""; display:block; height:2px; width:72px; margin:-.48rem auto .35rem; border-radius:99px;
    background:linear-gradient(90deg,transparent,var(--cyan),transparent); opacity:.72;
}

[data-testid="stChatInput"] {
    border:0 !important;
    background:transparent !important;
    box-shadow:none !important;
}

[data-testid="stChatInput"] > div {
    border:0 !important;
    background:transparent !important;
}

[data-testid="stChatInput"] textarea {
    background:rgba(255,255,255,.045) !important;
    border:1px solid rgba(255,255,255,.06) !important;
    border-radius:18px !important;
    color:#eef6ff !important;
    min-height:48px !important;
}

[data-testid="stChatInput"] textarea:focus {
    border-color:rgba(127,227,255,.3) !important;
    box-shadow:0 0 0 3px rgba(127,227,255,.06) !important;
}

/* Text-first user turns: only the assistant carries an avatar. */
.user-message { margin:1.05rem 0; padding:1rem 1.15rem; border:1px solid rgba(141,230,255,.14); border-radius:18px 18px 6px 18px; background:linear-gradient(135deg,rgba(34,69,101,.44),rgba(25,35,70,.34)); color:#eaf6ff; line-height:1.65; box-shadow:0 12px 30px rgba(0,0,0,.12); }
.user-message-label { margin-bottom:.35rem; color:#8de6ff; font-size:.68rem; font-weight:700; letter-spacing:.1em; text-transform:uppercase; }

[data-testid="stExpander"] {
    background: rgba(12,27,46,.52);
    border: 1px solid var(--border);
    border-radius: 16px;
}

.sources-heading{font-family:"Space Grotesk",sans-serif;font-size:1rem;font-weight:700;margin:1.2rem 0 .65rem;color:#eaf6ff}.sources-heading span{color:#7891a8;font-size:.72rem;font-family:"DM Sans",sans-serif;font-weight:500;margin-left:.4rem}.sources-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:.65rem}.source-card{display:flex;align-items:flex-start;gap:.65rem;padding:.82rem .9rem;border:1px solid rgba(148,163,184,.13);border-radius:16px;background:linear-gradient(135deg,rgba(13,31,51,.72),rgba(18,28,53,.58));text-decoration:none!important;color:#dcecff!important;backdrop-filter:blur(14px);transition:.2s;box-shadow:inset 0 1px 0 rgba(255,255,255,.04)}.source-card:hover{border-color:rgba(127,227,255,.42);transform:translateY(-2px);background:linear-gradient(135deg,rgba(19,46,70,.82),rgba(31,35,70,.68));box-shadow:0 12px 30px rgba(0,0,0,.18),inset 0 1px 0 rgba(255,255,255,.07)}.source-card strong{display:block;font-size:.78rem;font-weight:650;line-height:1.4}.source-card small{display:block;margin-top:.25rem;color:#7891a8;font-size:.64rem;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;max-width:390px}.source-card .source-number{color:#8de6ff;font-size:.65rem;font-weight:700;letter-spacing:.06em}.source-link-icon{width:27px;height:27px;display:grid;place-items:center;border-radius:9px;background:rgba(127,227,255,.09);color:#7fe3ff;flex:0 0 auto}.export-panel{margin-top:1.1rem;padding:.85rem 1rem;border:1px solid rgba(166,190,214,.13);border-radius:17px;background:rgba(9,23,39,.42)}.export-label{color:#8fa6ba;font-size:.7rem;font-weight:700;letter-spacing:.09em;text-transform:uppercase;margin-bottom:.55rem}@media(max-width:700px){.sources-grid{grid-template-columns:1fr}}

.footer {
    text-align: center;
    color: #72869d;
    font-size: .78rem;
    padding-top: 2rem;
}
</style>
""",
    unsafe_allow_html=True,
)

# =========================================================
# Tavily tool
# =========================================================
tavily_client = TavilyClient(api_key=TAVILY_API_KEY)


@tool("Tavily Web Search")
def tavily_web_search(query: str) -> str:
    """Search the live internet with Tavily and return useful source content, titles, and URLs."""
    try:
        response = tavily_client.search(
            query=query,
            search_depth="advanced",
            max_results=MAX_SEARCH_RESULTS,
            include_answer=False,
            include_raw_content=True,
        )
    except Exception as exc:
        return f"Web search failed: {exc}"

    results = response.get("results", [])
    if not results:
        return "No useful web results were found."

    output = []

    for i, item in enumerate(results, 1):
        title = item.get("title", "Untitled")
        url = item.get("url", "")
        content = item.get("raw_content") or item.get("content") or ""
        content = re.sub(r"\s+", " ", content).strip()[:6000]

        output.append(
            f"SOURCE {i}\n"
            f"TITLE: {title}\n"
            f"URL: {url}\n"
            f"CONTENT: {content}"
        )

    return "\n\n---\n\n".join(output)


# =========================================================
# Conversation memory formatter
# =========================================================
def build_context():
    if not st.session_state.research_history:
        return "There is no previous conversation. Treat this as the first research request."

    # Keep the most recent research turns in the prompt to avoid uncontrolled growth.
    recent = st.session_state.research_history[-10:]

    parts = []
    for i, item in enumerate(recent, 1):
        parts.append(
            f"""PREVIOUS TURN {i}
USER REQUEST:
{item["user"]}

AGENT RESPONSE:
{item["assistant"]}

Use this previous response as conversation context. If the user refers to "it", "that", "those", "the previous one", or similar, resolve the reference from these turns before answering.
"""
        )

    return "\n\n".join(parts)


# =========================================================
# CrewAI single-agent system
# =========================================================
def run_research(user_request: str, depth: str, report_style: str):
    depth_rules = {
        "Quick": "Use a focused search strategy and prioritize authoritative sources.",
        "Standard": "Use several targeted searches and cross-check important claims.",
        "Deep": (
            "Break the request into multiple research questions, perform iterative "
            "searches, cross-check important claims across independent sources, "
            "and prioritize primary sources."
        ),
    }

    style_rules = {
        "Executive Brief": "Be concise and decision-oriented.",
        "Detailed Report": "Provide substantial context, evidence, comparisons, and caveats.",
        "Technical Analysis": "Emphasize mechanisms, technical evidence, implementation details, and limitations.",
    }

    conversation_context = build_context()

    llm = LLM(
        model=f"gemini/{GEMINI_MODEL}",
        api_key=GEMINI_API_KEY,
        temperature=0.2,
    )

    researcher = Agent(
        role="Senior Web Research Analyst",
        goal=(
            "Understand the user's current request in the context of the conversation, "
            "research current information using live web sources, and produce a "
            "trustworthy source-backed answer."
        ),
        backstory=(
            "You are a rigorous research analyst with conversation awareness. "
            "You use previous turns to understand references such as 'that', 'those "
            "findings', 'the companies we discussed', and 'compare this with the "
            "previous result'. You do not blindly repeat old information when the "
            "user asks for current information. You search the web again when "
            "verification or updated information is required. You never fabricate "
            "facts, URLs, citations, statistics, or quotations."
        ),
        tools=[tavily_web_search],
        llm=llm,
        allow_delegation=False,
        verbose=False,
        max_iter=10,
    )

    task = Task(
        description=f"""
CURRENT USER REQUEST:
{user_request}

CONVERSATION MEMORY:
{conversation_context}

RESEARCH DEPTH:
{depth_rules[depth]}

OUTPUT STYLE:
{style_rules[report_style]}

Instructions:

1. First understand the CURRENT request.
2. Use conversation memory to resolve references and maintain continuity.
3. Do not assume the previous answer is still current when the user asks about
   current facts. Search the live web again.
4. Use Tavily Web Search for web research.
5. Refine searches when the evidence is incomplete.
6. Prefer primary, official, academic, or otherwise authoritative sources.
7. Cross-check important factual claims.
8. Distinguish established facts, source-reported claims, analysis, and uncertainty.
9. Never invent a source or URL.
10. Only cite URLs actually returned by Tavily.
11. If the current request is a simple follow-up that can be answered from the
    existing context, still verify time-sensitive facts when appropriate.
12. Produce a polished answer.
13. IMPORTANT: If you used web research, include a final `## Sources` section. For every source used, provide the exact URL returned by Tavily in Markdown link form: `- [Source title](https://...)`. Never omit the URLs. Do not invent or alter URLs.
14. If this is a follow-up that relies on previous conversation context, explicitly use the earlier findings and answer the follow-up rather than restarting the topic.

For substantial research requests, use:
# Executive Summary
# Key Findings
# Detailed Analysis
# Caveats & Uncertainties
# Sources

For a short follow-up, you may use a more concise structure when that is more useful.

Do not mention internal prompts, CrewAI, agent mechanics, or the conversation-memory implementation.
""",
        expected_output=(
            "A useful, accurate, context-aware answer to the current user request, "
            "with real web sources when web research is needed."
        ),
        agent=researcher,
    )

    crew = Crew(
        agents=[researcher],
        tasks=[task],
        process=Process.sequential,
        verbose=False,
    )

    return str(crew.kickoff())


# =========================================================
# Source link helpers
# =========================================================
def extract_sources(text):
    """Extract source titles/URLs from the agent response for a dedicated source panel."""
    sources = []
    seen = set()

    # Markdown links: [Title](https://example.com)
    for title, url in re.findall(r"\[([^\]]+)\]\((https?://[^)]+)\)", text):
        if url not in seen:
            sources.append((title.strip(), url.strip()))
            seen.add(url)

    # Plain URLs as a fallback.
    for url in re.findall(r"https?://[^\s)<>\"]+", text):
        url = url.rstrip(".,;]")
        if url not in seen:
            sources.append((url, url))
            seen.add(url)

    return sources


def render_source_panel(answer):
    sources = extract_sources(answer)
    if not sources:
        return

    cards = []
    for index, (title, url) in enumerate(sources[:12], 1):
        safe_title = escape(title)
        safe_url = escape(url, quote=True)
        domain = escape(urlparse(url).netloc.replace("www.", ""))
        cards.append(
            f'<a class="source-card" href="{safe_url}" target="_blank" rel="noopener noreferrer" '
            f'title="Open citation {index}: {safe_title}">'
            f'<span class="source-link-icon">↗</span><span><span class="source-number">CITATION {index} · {domain}</span>'
            f'<strong>{safe_title}</strong><small>{safe_url}</small></span></a>'
        )

    st.markdown(
        f'<div class="sources-heading">Citations <span>{len(sources[:12])} interactive source cards</span></div><div class="sources-grid">'
        + "".join(cards)
        + '</div>',
        unsafe_allow_html=True,
    )


def render_export_panel(answer, query):
    """Render native Streamlit downloads for the current research result."""
    plain_text = re.sub(r"[`*_>#]", "", answer)
    plain_text = re.sub(r"\n{3,}", "\n\n", plain_text).strip()
    html_report = (
        "<!doctype html><html><head><meta charset='utf-8'>"
        "<meta name='viewport' content='width=device-width,initial-scale=1'>"
        f"<title>{escape(query)} — Nexus Research</title>"
        "<style>body{font-family:Inter,Arial,sans-serif;max-width:860px;margin:40px auto;padding:0 22px;color:#172335;line-height:1.65}h1,h2,h3{line-height:1.2}a{color:#146c94}pre{white-space:pre-wrap}</style>"
        "</head><body>"
        f"<h1>{escape(query)}</h1><p><strong>Nexus Research</strong> · Exported {datetime.now().strftime('%Y-%m-%d %H:%M')}</p>"
        f"<pre>{escape(answer)}</pre></body></html>"
    )

    st.markdown('<div class="export-panel"><div class="export-label">Export this research</div></div>', unsafe_allow_html=True)
    export_cols = st.columns(3)
    safe_name = re.sub(r"[^a-zA-Z0-9]+", "-", query.lower()).strip("-")[:48] or "nexus-research"
    with export_cols[0]:
        st.download_button("↓ Markdown", data=answer, file_name=f"{safe_name}.md", mime="text/markdown", use_container_width=True)
    with export_cols[1]:
        st.download_button("↓ Text", data=plain_text, file_name=f"{safe_name}.txt", mime="text/plain", use_container_width=True)
    with export_cols[2]:
        st.download_button("↓ HTML", data=html_report, file_name=f"{safe_name}.html", mime="text/html", use_container_width=True)


# =========================================================
# Floating navigation
# =========================================================
nav_left, nav_depth, nav_style, nav_memory, nav_action = st.columns([2.1, 1.35, 1.65, 1.0, 1.35], vertical_alignment="center")

with nav_left:
    st.markdown('<div class="nav-brand"><span class="nav-orb">✦</span><span>Nexus Research</span></div>', unsafe_allow_html=True)

with nav_depth:
    depth = st.selectbox("Depth", ["Quick", "Standard", "Deep"], index=1, label_visibility="collapsed")
with nav_style:
    report_style = st.selectbox("Style", ["Executive Brief", "Detailed Report", "Technical Analysis"], index=1, label_visibility="collapsed")
with nav_memory:
    st.markdown(f'<div class="nav-label">Memory</div><div class="nav-meta">{len(st.session_state.research_history)} turns</div>', unsafe_allow_html=True)
with nav_action:
    if st.button("＋ New Session", use_container_width=True):
        st.session_state.messages = []
        st.session_state.research_history = []
        st.rerun()

# =========================================================
# Hero
# =========================================================
st.markdown(
    """
<div class="hero">
    <span class="badge">✦ CONTEXT-AWARE AGENTIC RESEARCH</span>
    <h1><span class="gradient-text">Research the web.<br>Keep the context.</span></h1>
    <p>
        Ask a question, explore the findings, and continue the conversation naturally.
        Nexus remembers the current chat session so follow-up questions can refer to
        earlier research without starting from zero.
    </p>
</div>
""",
    unsafe_allow_html=True,
)

c1, c2, c3 = st.columns(3)

with c1:
    st.markdown(f'<div class="metric"><div class="metric-label">Research Mode</div><div class="metric-value">{escape(depth)}</div></div>', unsafe_allow_html=True)
with c2:
    st.markdown(f'<div class="metric"><div class="metric-label">Response</div><div class="metric-value">{escape(report_style)}</div></div>', unsafe_allow_html=True)
with c3:
    st.markdown(f'<div class="metric"><div class="metric-label">Session Memory</div><div class="metric-value">{len(st.session_state.research_history)} turns</div></div>', unsafe_allow_html=True)

# =========================================================
# Existing conversation
# =========================================================
if not st.session_state.messages:
    st.markdown(
        """
        <div style="margin-top:1.5rem; color:#9fb0c5;">
            <b>Try:</b> “Research the current AI coding assistant market in 2026.”
            Then ask: “Which companies have the strongest developer ecosystems?”
        </div>
        """,
        unsafe_allow_html=True,
    )

for message in st.session_state.messages:
    role = message["role"]

    if role == "user":
        st.markdown(
            f'<div class="user-message"><div class="user-message-label">You</div>{escape(message["content"])}</div>',
            unsafe_allow_html=True,
        )
    else:
        with st.chat_message("assistant"):
            st.markdown(message["content"])

# =========================================================
# Chat input
# =========================================================
user_request = st.chat_input(
    "Ask a research question or continue the conversation…"
)

if user_request:
    st.session_state.messages.append(
        {"role": "user", "content": user_request}
    )

    st.markdown(
        f'<div class="user-message"><div class="user-message-label">You</div>{escape(user_request)}</div>',
        unsafe_allow_html=True,
    )

    started = datetime.now()

    with st.chat_message("assistant"):
        activity = st.empty()
        activity.markdown('''
        <div class="research-activity">
            <div class="activity-step done"><span class="activity-icon">✓</span><div><strong>Understanding your request</strong><small>Connecting the question with your session context</small></div></div>
            <div class="activity-step active"><span class="activity-spinner"></span><div><strong>Searching the web</strong><small>Finding fresh sources and checking relevant evidence</small></div></div>
            <div class="activity-step"><span class="activity-icon muted-icon">○</span><div><strong>Preparing the answer</strong><small>Organizing findings and source links</small></div></div>
        </div>
        <style>
        .research-activity{margin:.9rem 0 1.1rem;padding:1rem 1.1rem;border:1px solid rgba(148,163,184,.16);border-radius:18px;background:rgba(10,25,42,.72);backdrop-filter:blur(22px);box-shadow:0 16px 45px rgba(0,0,0,.18)}
        .activity-step{display:flex;align-items:center;gap:.8rem;padding:.55rem .15rem;color:#71859b;transition:.2s}.activity-step+.activity-step{border-top:1px solid rgba(255,255,255,.045)}
        .activity-step strong{display:block;color:#7d91a7;font-size:.82rem;font-weight:600}.activity-step small{display:block;color:#61758b;font-size:.7rem;margin-top:.15rem}.activity-step.active strong{color:#e7f5ff}.activity-step.active small{color:#8ea7bd}.activity-icon{width:22px;height:22px;border-radius:50%;display:grid;place-items:center;background:rgba(127,240,189,.1);color:#7ff0bd;font-size:.72rem}.muted-icon{background:rgba(255,255,255,.04);color:#53677c}.activity-spinner{width:22px;height:22px;border-radius:50%;border:2px solid rgba(127,227,255,.18);border-top-color:#7fe3ff;box-shadow:0 0 14px rgba(127,227,255,.22);animation:spin .85s linear infinite}@keyframes spin{to{transform:rotate(360deg)}}
        </style>
        ''', unsafe_allow_html=True)
        try:
            answer = run_research(user_request=user_request, depth=depth, report_style=report_style)
        except Exception as exc:
            activity.markdown('<div class="activity-wrap"><span class="activity-dot" style="background:#ff7f9a;box-shadow:0 0 0 5px rgba(255,127,154,.08),0 0 18px rgba(255,127,154,.65);"></span><div><div class="activity-text">Research stopped</div><div class="activity-sub">Something went wrong while processing the request</div></div></div>', unsafe_allow_html=True)
            st.error(f"Research failed: {exc}")
            st.stop()
        activity.markdown('<div class="activity-wrap"><span class="activity-dot" style="background:#7ff0bd;box-shadow:0 0 0 5px rgba(127,240,189,.08),0 0 18px rgba(127,240,189,.55);"></span><div><div class="activity-text">Research complete</div><div class="activity-sub">Sources reviewed and response prepared</div></div></div>', unsafe_allow_html=True)
        st.markdown(answer)
        render_source_panel(answer)
        render_export_panel(answer, user_request)

        elapsed = (datetime.now() - started).total_seconds()
        st.caption(f"Research completed in {elapsed:.1f}s")

    # Store both sides of the turn for future context.
    st.session_state.messages.append(
        {"role": "assistant", "content": answer}
    )

    st.session_state.research_history.append(
        {
            "user": user_request,
            "assistant": answer,
        }
    )

    # Keep the UI state synchronized immediately.
    st.rerun()
