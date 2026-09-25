import re
from datetime import datetime
from html import escape

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
    --bg: #07111f;
    --panel: rgba(14, 29, 48, .70);
    --panel2: rgba(10, 24, 41, .66);
    --border: rgba(148, 163, 184, .16);
    --text: #eef6ff;
    --muted: #9fb0c5;
}

html, body, [class*="css"] {
    font-family: "DM Sans", sans-serif;
}

.stApp {
    background:
        radial-gradient(circle at 10% 7%, rgba(86,216,255,.15), transparent 28%),
        radial-gradient(circle at 90% 10%, rgba(155,123,255,.17), transparent 30%),
        radial-gradient(circle at 50% 100%, rgba(94,230,176,.07), transparent 26%),
        #07111f;
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
    max-width: 1280px;
    padding-top: 6.5rem;
    padding-bottom: 4rem;
}

header[data-testid="stHeader"], [data-testid="stToolbar"], [data-testid="stDecoration"], [data-testid="stStatusWidget"] { display:none !important; }
[data-testid="stSidebar"], [data-testid="collapsedControl"] { display:none !important; }

.floating-nav { position:fixed; z-index:999999; top:1rem; left:50%; transform:translateX(-50%); width:min(1120px,calc(100vw - 2rem)); padding:.65rem .75rem; border:1px solid rgba(148,163,184,.18); border-radius:22px; background:rgba(8,20,35,.72); backdrop-filter:blur(24px) saturate(150%); -webkit-backdrop-filter:blur(24px) saturate(150%); box-shadow:0 18px 55px rgba(0,0,0,.28),inset 0 1px 0 rgba(255,255,255,.05); }
.nav-brand { display:flex;align-items:center;gap:.65rem;font-family:"Space Grotesk",sans-serif;font-weight:700;font-size:1.02rem;white-space:nowrap; }
.nav-orb { width:32px;height:32px;border-radius:11px;display:grid;place-items:center;background:linear-gradient(135deg,rgba(127,227,255,.25),rgba(173,149,255,.25));border:1px solid rgba(127,227,255,.25); }
.nav-label { color:#8fa3ba;font-size:.67rem;font-weight:700;text-transform:uppercase;letter-spacing:.08em;margin-bottom:.18rem; }
.nav-meta { color:#9fb0c5;font-size:.73rem;white-space:nowrap; }
.activity-wrap { display:flex;align-items:center;gap:.7rem;padding:.7rem .9rem;margin:.85rem 0 1rem;border:1px solid rgba(127,227,255,.16);border-radius:15px;background:rgba(8,25,42,.64);backdrop-filter:blur(18px);box-shadow:0 12px 35px rgba(0,0,0,.18); }
.activity-dot { width:9px;height:9px;border-radius:50%;background:#7fe3ff;box-shadow:0 0 0 5px rgba(127,227,255,.08),0 0 18px rgba(127,227,255,.75);animation:pulse 1.35s ease-in-out infinite; }
.activity-text { font-size:.82rem;color:#d9e8f7; } .activity-sub { font-size:.72rem;color:#7f94aa;margin-top:.1rem; }
@keyframes pulse { 0%,100%{transform:scale(.85);opacity:.55;} 50%{transform:scale(1.15);opacity:1;} }
@media(max-width:900px){[data-testid="stHorizontalBlock"]:first-of-type{top:.65rem;width:calc(100vw - 1rem);border-radius:18px}.block-container{padding-top:7.2rem}.nav-meta{display:none}}

.hero {
    padding: 2.2rem 2.4rem;
    border: 1px solid var(--border);
    border-radius: 28px;
    background: linear-gradient(135deg, rgba(19,39,63,.76), rgba(10,23,40,.55));
    backdrop-filter: blur(22px);
    box-shadow: 0 25px 80px rgba(0,0,0,.25);
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
    background: linear-gradient(90deg, #fff 10%, #7fe3ff 48%, #ad95ff 92%);
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

.stChatInputContainer {
    background: rgba(7,17,31,.8);
}

[data-testid="stExpander"] {
    background: rgba(12,27,46,.52);
    border: 1px solid var(--border);
    border-radius: 16px;
}

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
    recent = st.session_state.research_history[-6:]

    parts = []
    for i, item in enumerate(recent, 1):
        parts.append(
            f"""PREVIOUS TURN {i}
USER REQUEST:
{item["user"]}

AGENT RESPONSE:
{item["assistant"]}
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
        with st.chat_message("user"):
            st.markdown(message["content"])
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

    with st.chat_message("user"):
        st.markdown(user_request)

    started = datetime.now()

    with st.chat_message("assistant"):
        activity = st.empty()
        activity.markdown('<div class="activity-wrap"><span class="activity-dot"></span><div><div class="activity-text">Understanding your request</div><div class="activity-sub">Connecting the current question with session context</div></div></div>', unsafe_allow_html=True)
        try:
            activity.markdown('<div class="activity-wrap"><span class="activity-dot"></span><div><div class="activity-text">Searching the web</div><div class="activity-sub">Gathering fresh sources and checking relevant evidence</div></div></div>', unsafe_allow_html=True)
            answer = run_research(user_request=user_request, depth=depth, report_style=report_style)
        except Exception as exc:
            activity.markdown('<div class="activity-wrap"><span class="activity-dot" style="background:#ff7f9a;box-shadow:0 0 0 5px rgba(255,127,154,.08),0 0 18px rgba(255,127,154,.65);"></span><div><div class="activity-text">Research stopped</div><div class="activity-sub">Something went wrong while processing the request</div></div></div>', unsafe_allow_html=True)
            st.error(f"Research failed: {exc}")
            st.stop()
        activity.markdown('<div class="activity-wrap"><span class="activity-dot" style="background:#7ff0bd;box-shadow:0 0 0 5px rgba(127,240,189,.08),0 0 18px rgba(127,240,189,.55);"></span><div><div class="activity-text">Research complete</div><div class="activity-sub">Sources reviewed and response prepared</div></div></div>', unsafe_allow_html=True)
        st.markdown(answer)

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

st.markdown(
    '<div class="footer">Nexus Research AI · Context-aware web research · Session memory</div>',
    unsafe_allow_html=True,
)
