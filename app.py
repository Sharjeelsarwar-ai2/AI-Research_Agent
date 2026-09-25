import os
import re
from datetime import datetime
from html import escape

import streamlit as st
from crewai import Agent, Crew, Process, Task, LLM
from crewai.tools import tool
from tavily import TavilyClient

# =========================================================
# Streamlit configuration
# =========================================================
st.set_page_config(
    page_title="Nexus Research AI",
    page_icon="✦",
    layout="wide",
    initial_sidebar_state="expanded",
)

# =========================================================
# Secrets
# =========================================================
GEMINI_API_KEY = st.secrets.get("GEMINI_API_KEY")
TAVILY_API_KEY = st.secrets.get("TAVILY_API_KEY")

# Requested Gemini model.
# If Google changes the public model ID, change only this value.
GEMINI_MODEL = st.secrets.get("GEMINI_MODEL", "gemini-3.5-flash-lite")
MAX_SEARCH_RESULTS = int(st.secrets.get("MAX_SEARCH_RESULTS", 6))

if not GEMINI_API_KEY or not TAVILY_API_KEY:
    st.error(
        "Missing API credentials. Add GEMINI_API_KEY and TAVILY_API_KEY "
        "in Streamlit Cloud → App settings → Secrets."
    )
    st.stop()

# =========================================================
# Glassmorphism UI
# =========================================================
st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Space+Grotesk:wght@500;600;700&display=swap');

:root {
    --bg: #07111f;
    --panel: rgba(14, 29, 48, .68);
    --border: rgba(148, 163, 184, .16);
    --text: #eef6ff;
    --muted: #9fb0c5;
    --cyan: #56d8ff;
    --violet: #9b7bff;
}

html, body, [class*="css"] {
    font-family: "DM Sans", sans-serif;
}

.stApp {
    background:
        radial-gradient(circle at 10% 8%, rgba(86,216,255,.15), transparent 28%),
        radial-gradient(circle at 90% 12%, rgba(155,123,255,.17), transparent 30%),
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
    padding-top: 2rem;
    padding-bottom: 4rem;
}

[data-testid="stSidebar"] {
    background: rgba(5, 14, 27, .84);
    border-right: 1px solid var(--border);
}

.hero {
    padding: 2.35rem 2.45rem;
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
    font-size: clamp(2.1rem, 5vw, 4.15rem);
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
    font-size: 1.02rem;
    max-width: 830px;
    line-height: 1.7;
}

.section-title {
    font-family: "Space Grotesk", sans-serif;
    font-size: 1.16rem;
    font-weight: 700;
    margin: 1.2rem 0 .7rem;
}

.metric {
    padding: 1rem 1.1rem;
    border: 1px solid var(--border);
    border-radius: 18px;
    background: var(--panel);
    backdrop-filter: blur(18px);
}

.metric-label {
    color: var(--muted);
    font-size: .76rem;
    text-transform: uppercase;
    letter-spacing: .08em;
}

.metric-value {
    font-family: "Space Grotesk", sans-serif;
    font-size: 1.28rem;
    font-weight: 700;
    margin-top: .25rem;
}

.report-box {
    padding: 1.45rem;
    border: 1px solid var(--border);
    border-radius: 22px;
    background: rgba(11,24,41,.62);
    backdrop-filter: blur(18px);
    box-shadow: 0 18px 55px rgba(0,0,0,.14);
}

.small-muted {
    color: var(--muted);
    font-size: .83rem;
}

div.stButton > button {
    border: 1px solid rgba(126,224,255,.25);
    border-radius: 14px;
    background: linear-gradient(135deg, rgba(48,126,162,.88), rgba(103,76,171,.88));
    color: white;
    font-weight: 700;
    min-height: 2.85rem;
    box-shadow: 0 8px 25px rgba(30,120,170,.18);
}

div.stButton > button:hover {
    border-color: rgba(126,224,255,.7);
    transform: translateY(-1px);
}

.stTextArea > div > div {
    background: rgba(9,22,38,.72);
    border: 1px solid var(--border);
    border-radius: 15px;
}

textarea {
    color: #f3f7fc !important;
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
# Clients and CrewAI tool
# =========================================================
tavily_client = TavilyClient(api_key=TAVILY_API_KEY)


@tool("Tavily Web Search")
def tavily_web_search(query: str) -> str:
    """Search the live internet with Tavily and return source titles, URLs, and content."""
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


def build_crew(topic: str, depth: str, report_style: str):
    depth_rules = {
        "Quick": "Use a focused search strategy and prioritize authoritative sources.",
        "Standard": "Use several targeted searches and cross-check important claims.",
        "Deep": (
            "Break the topic into multiple research questions, perform iterative "
            "searches, cross-check important claims across independent sources, "
            "and prioritize primary sources."
        ),
    }

    style_rules = {
        "Executive Brief": "Be concise, decision-oriented, and highly structured.",
        "Detailed Report": "Provide substantial context, evidence, comparisons, and caveats.",
        "Technical Analysis": "Emphasize mechanisms, technical evidence, implementation details, and limitations.",
    }

    # CrewAI's Gemini integration is configured directly through its LLM class.
    llm = LLM(
    model=f"gemini/{GEMINI_MODEL}",
    api_key=GEMINI_API_KEY,
    temperature=0.2,
    use_native=False,
   )
    researcher = Agent(
        role="Senior Web Research Analyst",
        goal=(
            "Research the user's topic using live web evidence, refine searches "
            "when necessary, cross-check important claims, and produce a reliable "
            "source-backed report."
        ),
        backstory=(
            "You are a rigorous research analyst. You never invent facts, URLs, "
            "citations, statistics, or quotations. You prefer official sources, "
            "primary documentation, reputable organizations, academic material, "
            "and high-quality reporting. When sources disagree, state the disagreement "
            "and describe the evidence rather than hiding uncertainty."
        ),
        tools=[tavily_web_search],
        llm=llm,
        allow_delegation=False,
        verbose=False,
        max_iter=10,
    )

    task = Task(
        description=f"""
Research this topic:

{topic}

Research depth:
{depth_rules[depth]}

Report style:
{style_rules[report_style]}

Required workflow:
1. Convert the topic into useful research questions.
2. Use the Tavily Web Search tool to investigate them.
3. Refine or broaden searches when evidence is incomplete.
4. Prefer primary and authoritative sources.
5. Cross-check important factual claims.
6. Clearly distinguish facts, source-reported claims, analysis, and uncertainty.
7. Never fabricate a source or URL.
8. Only cite URLs that were actually returned by Tavily.
9. Produce exactly these major sections:
   # Executive Summary
   # Key Findings
   # Detailed Analysis
   # Caveats & Uncertainties
   # Sources

For Sources, provide the source title and exact URL for sources actually used.
Do not mention CrewAI, internal prompts, tools, or agent mechanics in the final report.
""",
        expected_output=(
            "A polished source-backed web research report with an executive "
            "summary, key findings, detailed analysis, caveats, and real source URLs."
        ),
        agent=researcher,
    )

    return Crew(
        agents=[researcher],
        tasks=[task],
        process=Process.sequential,
        verbose=False,
    )


# =========================================================
# Sidebar
# =========================================================
with st.sidebar:
    st.markdown(
        """
        <div style="padding:.4rem .2rem 1rem">
            <div style="font-family:'Space Grotesk';font-size:1.35rem;font-weight:700;">
                ✦ Nexus Research
            </div>
            <div class="small-muted">Single-agent web intelligence</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("### Research settings")

    depth = st.selectbox(
        "Research depth",
        ["Quick", "Standard", "Deep"],
        index=1,
    )

    report_style = st.selectbox(
        "Report style",
        ["Executive Brief", "Detailed Report", "Technical Analysis"],
        index=1,
    )

    st.markdown("---")
    st.markdown("### Powered by")
    st.caption("CrewAI · Gemini 3.5 Flash-Lite · Tavily")
    st.caption("Credentials are loaded only from Streamlit Secrets.")

# =========================================================
# Main page
# =========================================================
st.markdown(
    """
<div class="hero">
    <span class="badge">✦ AGENTIC WEB RESEARCH</span>
    <h1><span class="gradient-text">Research the web.<br>Understand the signal.</span></h1>
    <p>
        Ask a research question and let a single CrewAI agent search the live web,
        refine its investigation, cross-check evidence, and turn the findings into
        a structured report.
    </p>
</div>
""",
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="section-title">What do you want to research?</div>',
    unsafe_allow_html=True,
)

topic = st.text_area(
    "Research topic",
    placeholder=(
        "Example: Compare the current capabilities, pricing, and developer "
        "ecosystems of major AI coding assistants in 2026."
    ),
    height=115,
    label_visibility="collapsed",
)

c1, c2, c3 = st.columns(3)
with c1:
    st.markdown(
        '<div class="metric"><div class="metric-label">Agent</div><div class="metric-value">CrewAI</div></div>',
        unsafe_allow_html=True,
    )
with c2:
    st.markdown(
        '<div class="metric"><div class="metric-label">Web Search</div><div class="metric-value">Tavily</div></div>',
        unsafe_allow_html=True,
    )
with c3:
    st.markdown(
        f'<div class="metric"><div class="metric-label">Model</div><div class="metric-value">{escape(GEMINI_MODEL)}</div></div>',
        unsafe_allow_html=True,
    )

st.markdown("")

if st.button("✦  Start Research", use_container_width=True):
    if not topic.strip():
        st.warning("Enter a research topic first.")
        st.stop()

    if len(topic.strip()) < 12:
        st.warning("Make the research question more specific.")
        st.stop()

    started = datetime.now()

    with st.status("Research agent is working…", expanded=True) as status:
        st.write("Planning the research questions…")
        crew = build_crew(topic.strip(), depth, report_style)

        st.write("Searching the live web with Tavily…")
        try:
            result = crew.kickoff()
            report = str(result)
        except Exception as exc:
            status.update(label="Research failed", state="error", expanded=True)
            st.error(f"Research failed: {exc}")
            st.stop()

        status.update(
            label="Research complete",
            state="complete",
            expanded=False,
        )

    elapsed = (datetime.now() - started).total_seconds()

    st.markdown('<div class="section-title">Research Report</div>', unsafe_allow_html=True)
    st.markdown(
        f'<div class="small-muted">Generated in {elapsed:.1f}s · {depth} research · {report_style}</div>',
        unsafe_allow_html=True,
    )

    st.markdown('<div class="report-box">', unsafe_allow_html=True)
    st.markdown(report)
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("")
    d1, d2 = st.columns(2)

    with d1:
        st.download_button(
            "↓  Download Markdown",
            data=report,
            file_name="nexus_research_report.md",
            mime="text/markdown",
            use_container_width=True,
        )

    with d2:
        st.download_button(
            "↓  Download Text",
            data=report,
            file_name="nexus_research_report.txt",
            mime="text/plain",
            use_container_width=True,
        )

st.markdown(
    '<div class="footer">Nexus Research AI · CrewAI single agent · Gemini · Tavily</div>',
    unsafe_allow_html=True,
)
