import re
from collections import Counter
from io import BytesIO
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

if "live_sources" not in st.session_state:
    st.session_state.live_sources = []

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

/* Restored wide floating glass chat dock */
[data-testid="stBottomBlockContainer"] {
    position:fixed !important;
    left:50% !important;
    right:auto !important;
    transform:translateX(-50%) !important;
    bottom:18px !important;
    z-index:999998 !important;
    width:min(1120px,calc(100vw - 2rem)) !important;
    min-height:70px !important;
    padding:.55rem !important;
    border:1px solid rgba(148,163,184,.28) !important;
    border-radius:25px !important;
    background:linear-gradient(135deg,rgba(15,30,49,.94),rgba(23,27,52,.90)) !important;
    backdrop-filter:blur(26px) saturate(160%) !important;
    -webkit-backdrop-filter:blur(26px) saturate(160%) !important;
    box-shadow:0 20px 60px rgba(0,0,0,.48),inset 0 1px 0 rgba(255,255,255,.10) !important;
}

[data-testid="stBottomBlockContainer"] > div {
    width:100% !important;
    margin:0 !important;
    padding:0 !important;
    background:transparent !important;
    border:0 !important;
    box-shadow:none !important;
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
.analytics-heading{font-family:"Space Grotesk",sans-serif;font-size:1.02rem;font-weight:700;margin:1.35rem 0 .65rem;color:#eaf6ff}.analytics-heading span{font-family:"DM Sans",sans-serif;color:#7891a8;font-size:.73rem;font-weight:500;margin-left:.45rem}.trend-cloud{display:flex;flex-wrap:wrap;gap:.45rem;margin-top:.7rem}.trend-chip{display:inline-flex;align-items:center;gap:.38rem;padding:.4rem .62rem;border:1px solid rgba(141,230,255,.15);border-radius:999px;background:rgba(16,39,61,.58);color:#d8ecfa;font-size:.73rem}.trend-chip b{color:#8de6ff;font-size:.63rem}.trend-chip em{font-style:normal;color:#b6a4ff;font-weight:700}.analytics-shell{padding:1rem;border:1px solid rgba(166,190,214,.13);border-radius:20px;background:rgba(10,24,41,.38)}
.live-sources-heading{font-family:"Space Grotesk",sans-serif;font-size:1rem;font-weight:700;margin:1.25rem 0 .65rem;color:#eaf6ff}.live-sources-heading span{font-family:"DM Sans",sans-serif;color:#7891a8;font-size:.7rem;font-weight:500;margin-left:.45rem}.live-source-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:.65rem}.live-source-card{display:flex;align-items:flex-start;gap:.6rem;padding:.78rem .85rem;border:1px solid rgba(145,241,197,.15);border-radius:15px;background:linear-gradient(135deg,rgba(12,37,48,.72),rgba(16,31,53,.65));text-decoration:none!important;color:#dcecff!important;transition:.2s;box-shadow:inset 0 1px 0 rgba(255,255,255,.04)}.live-source-card:hover{transform:translateY(-2px);border-color:rgba(145,241,197,.45);box-shadow:0 12px 28px rgba(0,0,0,.18)}.live-source-card strong{display:block;font-size:.76rem;line-height:1.35}.live-source-card small{display:block;color:#91f1c5;font-size:.63rem;margin-top:.2rem}.live-source-card em{display:block;color:#7e96a9;font-size:.66rem;font-style:normal;line-height:1.4;margin-top:.28rem}.live-source-card>b{margin-left:auto;color:#91f1c5}.live-source-badge{color:#91f1c5;font-size:.62rem;font-weight:800;letter-spacing:.07em;white-space:nowrap}@media(max-width:700px){.live-source-grid{grid-template-columns:1fr}}

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
        live_record = {
            "title": title,
            "url": url,
            "domain": urlparse(url).netloc.replace("www.", ""),
            "published": item.get("published_date") or item.get("date") or "Live result",
            "snippet": item.get("content") or item.get("raw_content") or "",
        }
        if url and not any(source.get("url") == url for source in st.session_state.live_sources):
            st.session_state.live_sources.append(live_record)
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
   For paper-focused requests, actively seek current scholarly records from sources such as
   arXiv, PubMed, Semantic Scholar, Crossref, ACM, IEEE, or official institutional repositories.
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


ANALYTICS_STOPWORDS = {
    "about", "after", "again", "also", "among", "been", "being", "could", "does", "from",
    "have", "into", "more", "most", "other", "over", "should", "some", "such", "than",
    "their", "there", "these", "they", "this", "those", "through", "under", "using", "were",
    "which", "while", "with", "would", "your", "that", "what", "when", "where", "will",
    "research", "sources", "source", "based", "according", "reported", "information",
}


def keyword_counts(text, limit=14):
    """Return the most frequent meaningful terms from the current answer."""
    words = re.findall(r"\b[a-zA-Z][a-zA-Z0-9-]{3,}\b", text.lower())
    counts = Counter(word.strip("-") for word in words if word not in ANALYTICS_STOPWORDS)
    return counts.most_common(limit)


def build_citation_graph(answer):
    """Create a Graphviz citation map from cited domains and answer keywords."""
    sources = extract_sources(answer)[:12]
    terms = [term for term, _count in keyword_counts(answer, 8)]
    lines = [
        "graph G {",
        '  graph [bgcolor="transparent", pad="0.2", nodesep="0.48", ranksep="0.8"];',
        '  node [shape=box, style="rounded,filled", fontname="Arial", fontsize=11, color="#5ecbe9", fillcolor="#122e49", fontcolor="#eaf6ff", margin="0.16,0.10"];',
        '  edge [color="#527b99", penwidth=1.2];',
        '  nexus [label="NEXUS\nRESEARCH", shape=ellipse, color="#a99bff", fillcolor="#302e62", penwidth=2];',
    ]
    for index, (_title, url) in enumerate(sources, 1):
        domain = urlparse(url).netloc.replace("www.", "") or f"source-{index}"
        node_id = f"source_{index}"
        lines.append(f'  {node_id} [label="{domain}", fillcolor="#123d52", color="#73dded"];')
        lines.append(f'  nexus -- {node_id};')
    for index, term in enumerate(terms, 1):
        safe_term = re.sub(r"[^a-zA-Z0-9_-]", "", term)
        node_id = f"term_{index}"
        lines.append(f'  {node_id} [label="{safe_term}", shape=note, fillcolor="#302d58", color="#ad9fff"];')
        lines.append(f'  nexus -- {node_id} [style=dashed, color="#765fa8"];')
    lines.append("}")
    return "\n".join(lines), len(sources), len(terms)


def render_analytics_panel():
    """Render the analytics tab from the session's accumulated research outputs."""
    answers = [item["assistant"] for item in st.session_state.research_history if item.get("assistant")]
    if not answers:
        st.info("Run a research query to populate citation-network and keyword-trend analytics.")
        return

    combined = "\n\n".join(answers)
    terms = keyword_counts(combined)
    graph, source_count, term_count = build_citation_graph(combined)
    analytics_cols = st.columns(3)
    with analytics_cols[0]:
        st.markdown(f'<div class="metric"><div class="metric-label">Research turns</div><div class="metric-value">{len(answers)}</div></div>', unsafe_allow_html=True)
    with analytics_cols[1]:
        st.markdown(f'<div class="metric"><div class="metric-label">Citation nodes</div><div class="metric-value">{source_count}</div></div>', unsafe_allow_html=True)
    with analytics_cols[2]:
        st.markdown(f'<div class="metric"><div class="metric-label">Tracked keywords</div><div class="metric-value">{term_count}</div></div>', unsafe_allow_html=True)

    st.markdown('<div class="analytics-heading">Citation network <span>Research center → cited domains and recurring concepts</span></div>', unsafe_allow_html=True)
    st.graphviz_chart(graph, use_container_width=True)

    st.markdown('<div class="analytics-heading">Keyword trends <span>Term frequency across the current research session</span></div>', unsafe_allow_html=True)
    if terms:
        st.bar_chart({"Mentions": dict(terms)}, color="#8de6ff", use_container_width=True)
        trend_cards = "".join(
            f'<span class="trend-chip"><b>{index:02d}</b>{escape(term)} <em>{count}</em></span>'
            for index, (term, count) in enumerate(terms, 1)
        )
        st.markdown(f'<div class="trend-cloud">{trend_cards}</div>', unsafe_allow_html=True)


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


def render_live_sources(sources):
    """Render the exact live-search records captured during the current run."""
    if not sources:
        return

    cards = []
    for index, source in enumerate(sources[:12], 1):
        title = escape(source.get("title", "Untitled"))
        url = source.get("url", "")
        domain = escape(source.get("domain") or urlparse(url).netloc.replace("www.", ""))
        published = escape(str(source.get("published", "Live result")))
        snippet = escape(re.sub(r"\s+", " ", source.get("snippet", "")).strip()[:220])
        cards.append(
            f'<a class="live-source-card" href="{escape(url, quote=True)}" target="_blank" rel="noopener noreferrer">'
            f'<span class="live-source-badge">LIVE {index:02d}</span><span><strong>{title}</strong>'
            f'<small>{domain} · {published}</small><em>{snippet}</em></span><b>↗</b></a>'
        )

    st.markdown(
        f'<div class="live-sources-heading">Live web sources <span>Captured directly from Tavily · {len(sources[:12])} results</span></div>'
        f'<div class="live-source-grid">{"".join(cards)}</div>',
        unsafe_allow_html=True,
    )


def build_pdf_report(answer, query):
    """Build a polished, standalone PDF report using ReportLab."""
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import LETTER
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import inch
    from reportlab.platypus import HRFlowable, Paragraph, SimpleDocTemplate, Spacer

    def inline_markup(text):
        rendered = escape(text)
        rendered = re.sub(
            r"\[([^\]]+)\]\((https?://[^)]+)\)",
            lambda match: f'<link href="{escape(match.group(2), quote=True)}" color="#147c9f">{escape(match.group(1))}</link>',
            rendered,
        )
        rendered = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", rendered)
        return rendered

    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=LETTER, rightMargin=.68 * inch, leftMargin=.68 * inch,
        topMargin=.72 * inch, bottomMargin=.62 * inch,
        title=f"{query} — Nexus Research", author="Nexus Research AI",
    )
    stylesheet = getSampleStyleSheet()
    title_style = ParagraphStyle("NexusTitle", parent=stylesheet["Title"], fontName="Helvetica-Bold", fontSize=24, leading=29, textColor=colors.HexColor("#10233d"), spaceAfter=8)
    meta_style = ParagraphStyle("NexusMeta", parent=stylesheet["Normal"], fontName="Helvetica", fontSize=8.5, leading=12, textColor=colors.HexColor("#6b7f93"), spaceAfter=14)
    heading_style = ParagraphStyle("NexusHeading", parent=stylesheet["Heading2"], fontName="Helvetica-Bold", fontSize=15, leading=19, textColor=colors.HexColor("#123f5c"), spaceBefore=14, spaceAfter=6)
    subheading_style = ParagraphStyle("NexusSubheading", parent=stylesheet["Heading3"], fontName="Helvetica-Bold", fontSize=11.5, leading=15, textColor=colors.HexColor("#1b5f7b"), spaceBefore=10, spaceAfter=4)
    body_style = ParagraphStyle("NexusBody", parent=stylesheet["BodyText"], fontName="Helvetica", fontSize=9.7, leading=14.5, textColor=colors.HexColor("#26384b"), spaceAfter=7)
    bullet_style = ParagraphStyle("NexusBullet", parent=body_style, leftIndent=14, firstLineIndent=-8, bulletIndent=0, spaceAfter=4)

    story = [Spacer(1, .20 * inch), Paragraph(inline_markup(query), title_style), Paragraph(f"NEXUS RESEARCH AI &nbsp;·&nbsp; Exported {datetime.now().strftime('%B %d, %Y at %H:%M')}", meta_style), HRFlowable(width="100%", thickness=1.2, color=colors.HexColor("#8de6ff"), spaceAfter=14)]
    for raw_line in answer.splitlines():
        line = raw_line.strip()
        if not line:
            story.append(Spacer(1, 3))
        elif line.startswith("### "):
            story.append(Paragraph(inline_markup(line[4:]), subheading_style))
        elif line.startswith("## "):
            story.append(Paragraph(inline_markup(line[3:]), heading_style))
        elif line.startswith("# "):
            story.append(Paragraph(inline_markup(line[2:]), heading_style))
        elif re.match(r"^[-*]\s+", line):
            bullet_text = re.sub(r"^[-*]\s+", "", line)
            story.append(Paragraph(f"• {inline_markup(bullet_text)}", bullet_style))
        else:
            story.append(Paragraph(inline_markup(line), body_style))

    def draw_page(canvas, _doc):
        canvas.saveState()
        width, height = LETTER
        canvas.setFillColor(colors.HexColor("#0a1c31"))
        canvas.rect(0, height - .28 * inch, width, .28 * inch, fill=1, stroke=0)
        canvas.setFillColor(colors.HexColor("#8de6ff"))
        canvas.setFont("Helvetica-Bold", 8)
        canvas.drawString(.68 * inch, height - .19 * inch, "NEXUS RESEARCH")
        canvas.setFillColor(colors.HexColor("#73879b"))
        canvas.setFont("Helvetica", 8)
        canvas.drawRightString(width - .68 * inch, .34 * inch, f"Nexus Research AI  ·  Page {canvas.getPageNumber()}")
        canvas.setStrokeColor(colors.HexColor("#d9e4eb"))
        canvas.line(.68 * inch, .49 * inch, width - .68 * inch, .49 * inch)
        canvas.restoreState()

    doc.build(story, onFirstPage=draw_page, onLaterPages=draw_page)
    return buffer.getvalue()


def build_html_report(answer, query):
    """Convert the research answer into a structured, readable HTML report."""
    def inline_html(text):
        rendered = escape(text)
        rendered = re.sub(
            r"\[([^\]]+)\]\((https?://[^)]+)\)",
            lambda match: f'<a href="{escape(match.group(2), quote=True)}" target="_blank" rel="noopener">{escape(match.group(1))}</a>',
            rendered,
        )
        rendered = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", rendered)
        rendered = re.sub(r"`([^`]+)`", r"<code>\1</code>", rendered)
        return rendered

    content = []
    list_items = []

    def flush_list():
        if list_items:
            content.append("<ul>" + "".join(f"<li>{item}</li>" for item in list_items) + "</ul>")
            list_items.clear()

    for raw_line in answer.splitlines():
        line = raw_line.strip()
        if not line:
            flush_list()
        elif line.startswith("### "):
            flush_list()
            content.append(f"<h3>{inline_html(line[4:])}</h3>")
        elif line.startswith("## "):
            flush_list()
            content.append(f"<h2>{inline_html(line[3:])}</h2>")
        elif line.startswith("# "):
            flush_list()
            content.append(f"<h2>{inline_html(line[2:])}</h2>")
        elif re.match(r"^[-*]\s+", line):
            list_items.append(inline_html(re.sub(r"^[-*]\s+", "", line)))
        else:
            flush_list()
            content.append(f"<p>{inline_html(line)}</p>")
    flush_list()

    sources = extract_sources(answer)[:12]
    source_cards = "".join(
        f'<a class="citation" href="{escape(url, quote=True)}" target="_blank" rel="noopener">'
        f'<span class="citation-index">{index:02d}</span><span><strong>{escape(title)}</strong>'
        f'<small>{escape(urlparse(url).netloc.replace("www.", ""))}</small></span><b>↗</b></a>'
        for index, (title, url) in enumerate(sources, 1)
    )
    source_panel = f'<details class="sources" open><summary>Citations <span>{len(sources)} sources</span></summary><div class="citation-grid">{source_cards or "<p class=muted>No citations were found in this report.</p>"}</div></details>'
    timestamp = datetime.now().strftime("%B %d, %Y at %H:%M")
    return f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{escape(query)} — Nexus Research</title>
<style>
:root{{--ink:#16283c;--muted:#667d92;--line:#dbe7ee;--cyan:#117c9d;--wash:#f4f9fb;--violet:#6555a8}}
*{{box-sizing:border-box}}body{{margin:0;background:linear-gradient(135deg,#f5fbfd,#f8f7ff);color:var(--ink);font-family:Inter,ui-sans-serif,system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;line-height:1.7}}
.page{{max-width:1040px;margin:0 auto;padding:34px 24px 64px}}.topbar{{height:8px;border-radius:99px;background:linear-gradient(90deg,#72dff4,var(--violet));margin-bottom:34px}}
.eyebrow{{color:var(--cyan);font-size:12px;font-weight:800;letter-spacing:.14em;text-transform:uppercase}}h1{{font-size:clamp(2rem,5vw,3.7rem);line-height:1.08;letter-spacing:-.05em;margin:10px 0 12px;color:#10233d}}.meta{{color:var(--muted);font-size:14px;margin-bottom:26px}}
.layout{{display:grid;grid-template-columns:minmax(0,1fr) 290px;gap:28px;align-items:start}}.report,.sources{{background:rgba(255,255,255,.82);border:1px solid rgba(136,171,194,.28);border-radius:22px;box-shadow:0 18px 50px rgba(34,59,82,.10)}}.report{{padding:28px 30px}}h2{{font-size:1.35rem;margin:26px 0 8px;color:#164a67;border-bottom:1px solid var(--line);padding-bottom:7px}}h3{{font-size:1.05rem;margin:20px 0 5px;color:#245e79}}p{{margin:0 0 12px}}ul{{padding-left:22px;margin-top:5px}}li{{margin:5px 0}}a{{color:#126f93;font-weight:650}}code{{background:#edf5f7;border-radius:6px;padding:2px 5px;font-size:.9em}}
.sources{{position:sticky;top:20px;padding:18px}}summary{{cursor:pointer;font-weight:800;color:#183e56;list-style:none}}summary::-webkit-details-marker{{display:none}}summary span{{float:right;color:var(--muted);font-size:12px;font-weight:600}}.citation-grid{{display:grid;gap:9px;margin-top:14px}}.citation{{display:flex;align-items:center;gap:10px;text-decoration:none;border:1px solid var(--line);border-radius:13px;padding:10px;background:var(--wash);transition:.18s}}.citation:hover{{transform:translateY(-2px);border-color:#7bd9ec;background:#fff;box-shadow:0 8px 20px rgba(40,93,116,.12)}}.citation-index{{display:grid;place-items:center;width:28px;height:28px;border-radius:9px;background:#dff7fb;color:#0d7695;font-size:12px;font-weight:800;flex:0 0 auto}}.citation strong{{display:block;font-size:12px;line-height:1.35;color:#1a354b}}.citation small{{display:block;color:var(--muted);font-size:11px;margin-top:2px}}.citation b{{margin-left:auto;color:var(--cyan)}}.muted{{color:var(--muted)}}footer{{color:var(--muted);font-size:12px;margin-top:22px}}@media(max-width:800px){{.layout{{grid-template-columns:1fr}}.sources{{position:static}}.report{{padding:22px}}}}
</style></head><body><main class="page"><div class="topbar"></div><div class="eyebrow">✦ Nexus Research AI · Research report</div><h1>{escape(query)}</h1><div class="meta">Exported {timestamp} · Interactive citation panel included</div><div class="layout"><article class="report">{"".join(content)}</article>{source_panel}</div><footer>Generated by Nexus Research AI. Citation cards open source pages in a new tab.</footer></main></body></html>'''


def render_export_panel(answer, query, key_prefix="latest"):
    """Render native Streamlit downloads for the current research result."""
    plain_text = re.sub(r"[`*_>#]", "", answer)
    plain_text = re.sub(r"\n{3,}", "\n\n", plain_text).strip()
    html_report = build_html_report(answer, query)

    try:
        pdf_report = build_pdf_report(answer, query)
        pdf_error = None
    except ImportError:
        pdf_report = None
        pdf_error = "Add reportlab>=4.0 to requirements.txt to enable PDF export."

    st.markdown('<div class="export-panel"><div class="export-label">Export this research</div></div>', unsafe_allow_html=True)
    export_cols = st.columns(4)
    safe_name = re.sub(r"[^a-zA-Z0-9]+", "-", query.lower()).strip("-")[:48] or "nexus-research"
    with export_cols[0]:
        st.download_button("↓ Markdown", data=answer, file_name=f"{safe_name}.md", mime="text/markdown", use_container_width=True, key=f"{key_prefix}_markdown")
    with export_cols[1]:
        st.download_button("↓ Text", data=plain_text, file_name=f"{safe_name}.txt", mime="text/plain", use_container_width=True, key=f"{key_prefix}_text")
    with export_cols[2]:
        st.download_button("↓ HTML", data=html_report, file_name=f"{safe_name}.html", mime="text/html", use_container_width=True, key=f"{key_prefix}_html")
    with export_cols[3]:
        if pdf_report:
            st.download_button("↓ PDF", data=pdf_report, file_name=f"{safe_name}.pdf", mime="application/pdf", use_container_width=True, key=f"{key_prefix}_pdf")
        else:
            st.caption(pdf_error)


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
        st.session_state.live_sources = []
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

research_tab, analytics_tab = st.tabs(["Research workspace", "Advanced analytics"])

with analytics_tab:
    render_analytics_panel()

with research_tab:
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

    last_user_request = "Research report"
    for message_index, message in enumerate(st.session_state.messages):
        role = message["role"]

        if role == "user":
            last_user_request = message["content"]
            st.markdown(
                f'<div class="user-message"><div class="user-message-label">You</div>{escape(message["content"])}</div>',
                unsafe_allow_html=True,
            )
        else:
            with st.chat_message("assistant"):
                st.markdown(message["content"])
                render_source_panel(message["content"])
                history_turn = message_index // 2
                if history_turn < len(st.session_state.research_history):
                    render_live_sources(st.session_state.research_history[history_turn].get("live_sources", []))
                render_export_panel(message["content"], last_user_request, key_prefix=f"history_{message_index}")

    # =========================================================

# Chat input
# =========================================================
user_request = st.chat_input(
    "Ask a research question or continue the conversation…"
)

if user_request:
    st.session_state.live_sources = []
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
        render_live_sources(st.session_state.live_sources)
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
            "live_sources": list(st.session_state.live_sources),
        }
    )

    # Keep the UI state synchronized immediately.
    st.rerun()
