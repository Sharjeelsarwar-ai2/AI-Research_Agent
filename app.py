import re
import time
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

KEYS_READY = bool(GEMINI_API_KEY and TAVILY_API_KEY)
if not KEYS_READY:
    st.warning(
        "Live research is paused: add GEMINI_API_KEY and TAVILY_API_KEY "
        "in Streamlit Cloud → App settings → Secrets. "
        "Demo mode below still works without keys."
    )

# =========================================================
# Session memory
# =========================================================
if "messages" not in st.session_state:
    st.session_state.messages = []

if "research_history" not in st.session_state:
    st.session_state.research_history = []

if "live_sources" not in st.session_state:
    st.session_state.live_sources = []

if "agent_status" not in st.session_state:
    st.session_state.agent_status = {"scout": "idle", "analyst": "idle", "verifier": "idle", "writer": "idle"}

if "agent_feed" not in st.session_state:
    st.session_state.agent_feed = []

if "demo_notice" not in st.session_state:
    st.session_state.demo_notice = False

# CrewAI can execute tools outside Streamlit's immediate script context. Keep
# a process-level buffer as a reliable citation bridge for the active run.
LIVE_SOURCE_BUFFER = []

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

div.stDownloadButton > button {
    border: 1px solid rgba(126,224,255,.25);
    border-radius: 14px;
    background: linear-gradient(135deg, rgba(48,126,162,.88), rgba(103,76,171,.88));
    color: white;
    font-weight: 700;
    min-height: 2.7rem;
}

div.stDownloadButton > button:hover {
    border-color: rgba(126,224,255,.7);
    transform: translateY(-1px);
    color: white;
}

/* Buttons wrapped in a tooltip target (st.button with help=) keep the same look. */
div.stTooltipHoverTarget > button {
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

/* ---- Agent Dock ---- */
.agent-dock{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:.7rem;margin:.4rem 0 .2rem}
.agent-card{position:relative;padding:.85rem .8rem .8rem;border:1px solid rgba(166,190,214,.15);border-radius:20px;background:linear-gradient(150deg,rgba(16,32,54,.78),rgba(11,22,39,.62));backdrop-filter:blur(16px);text-align:center;transition:.25s}
.agent-card.working{border-color:var(--ac,#8de6ff);box-shadow:0 0 0 1px var(--ac,#8de6ff),0 12px 34px rgba(0,0,0,.35),0 0 26px var(--ac,#8de6ff)}
.agent-card.done{border-color:rgba(145,241,197,.35)}
.agent-card .robot{display:block;margin:0 auto .45rem}
.agent-card.working .robot{animation:robot-bob 1s ease-in-out infinite}
@keyframes robot-bob{0%,100%{transform:translateY(0)}50%{transform:translateY(-6px)}}
.agent-name{font-family:"Space Grotesk",sans-serif;font-weight:700;font-size:.86rem;letter-spacing:.04em}
.agent-role{color:#96a9bc;font-size:.7rem;margin-top:.12rem}
.agent-pill{display:inline-block;margin-top:.5rem;padding:.22rem .6rem;border-radius:999px;font-size:.62rem;font-weight:800;letter-spacing:.09em;text-transform:uppercase}
.pill-idle{background:rgba(255,255,255,.06);color:#8fa3ba;border:1px solid rgba(255,255,255,.08)}
.pill-working{background:var(--ac,#8de6ff);color:#07101d;animation:pulse 1.2s ease-in-out infinite}
.pill-done{background:rgba(145,241,197,.16);color:#91f1c5;border:1px solid rgba(145,241,197,.35)}
.agent-check{position:absolute;top:.55rem;right:.6rem;width:20px;height:20px;border-radius:50%;background:#91f1c5;color:#07101d;font-size:.68rem;font-weight:800;display:grid;place-items:center}
.agent-feed{margin:.55rem 0 .2rem;padding:.6rem .9rem;border:1px solid rgba(148,163,184,.13);border-radius:14px;background:rgba(8,22,38,.5);font-size:.78rem;color:#c4d8ea}
.agent-feed div{padding:.14rem 0}
.agent-feed b{color:#8de6ff}
.demo-banner{margin:.6rem 0;padding:.6rem .9rem;border:1px dashed rgba(255,196,107,.55);border-radius:14px;background:rgba(255,196,107,.08);color:#ffd9a0;font-size:.8rem}

/* ---- Report Window ---- */
[data-testid="stVerticalBlockBorderWrapper"]{border:1px solid rgba(141,220,255,.30)!important;border-radius:22px!important;background:linear-gradient(160deg,rgba(13,30,50,.88),rgba(9,20,36,.80))!important;box-shadow:0 26px 70px rgba(0,0,0,.35)!important;margin:.9rem 0}
.report-window{border:1px solid rgba(141,220,255,.28);border-radius:22px;overflow:hidden;background:linear-gradient(160deg,rgba(13,30,50,.85),rgba(9,20,36,.78));backdrop-filter:blur(22px);box-shadow:0 26px 70px rgba(0,0,0,.35);margin:.9rem 0}
.report-titlebar{display:flex;align-items:center;gap:.7rem;padding:.75rem 1.05rem;border-bottom:1px solid rgba(166,190,214,.14);background:rgba(255,255,255,.03)}
.traffic-dots{display:flex;gap:.35rem}
.traffic-dots span{width:11px;height:11px;border-radius:50%}
.traffic-dots span:nth-child(1){background:#ff5f57}.traffic-dots span:nth-child(2){background:#febc2e}.traffic-dots span:nth-child(3){background:#28c840}
.report-titlebar .rw-label{font-family:"Space Grotesk",sans-serif;font-weight:700;font-size:.72rem;letter-spacing:.14em;color:#8de6ff}
.report-titlebar .rw-query{font-size:.82rem;color:#eaf6ff;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;flex:1}
.report-titlebar .rw-time{font-size:.68rem;color:#7f94aa;white-space:nowrap}
.report-body{padding:1.15rem 1.25rem 1.25rem}
.exec-box{padding:1rem 1.15rem;border:1px solid rgba(141,230,255,.25);border-left:4px solid #8de6ff;border-radius:16px;background:linear-gradient(135deg,rgba(141,230,255,.10),rgba(182,164,255,.07));line-height:1.7;color:#e6f3ff}
.rw-section{font-family:"Space Grotesk",sans-serif;font-size:1.02rem;font-weight:700;margin:1.35rem 0 .6rem;color:#eaf6ff}
.rw-section span{color:#7891a8;font-size:.72rem;font-family:"DM Sans",sans-serif;font-weight:500;margin-left:.4rem}
.finding-card{display:flex;gap:.8rem;padding:.85rem 1rem;border:1px solid rgba(148,163,184,.14);border-radius:16px;background:linear-gradient(135deg,rgba(13,31,51,.72),rgba(18,28,53,.58));margin-bottom:.55rem;line-height:1.6}
.finding-num{flex:0 0 auto;width:28px;height:28px;border-radius:9px;display:grid;place-items:center;background:rgba(141,230,255,.12);color:#8de6ff;font-weight:800;font-size:.78rem}
.rw-h3{font-family:"Space Grotesk",sans-serif;font-size:.95rem;font-weight:700;color:#bfeaff;margin:1rem 0 .3rem}
.rw-block{padding:.95rem 1.05rem;border:1px solid rgba(148,163,184,.13);border-radius:16px;background:rgba(255,255,255,.025);margin-bottom:.65rem}
.rw-block .rw-section{margin-top:0}
.report-body p{line-height:1.7;color:#dcecff;margin:.35rem 0 .7rem}
.report-body ul{margin:.3rem 0 .7rem;padding-left:1.2rem;line-height:1.65;color:#dcecff}
@media(max-width:700px){.agent-dock{grid-template-columns:repeat(2,minmax(0,1fr))}.report-titlebar .rw-time{display:none}}

</style>
""",
    unsafe_allow_html=True,
)

# =========================================================
# Tavily tool
# =========================================================
tavily_client = TavilyClient(api_key=TAVILY_API_KEY) if TAVILY_API_KEY else None


@tool("Tavily Web Search")
def tavily_web_search(query: str) -> str:
    """Search the live internet with Tavily and return useful source content, titles, and URLs."""
    if tavily_client is None:
        return "Web search unavailable: TAVILY_API_KEY is not configured."
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
        if url:
            if not any(source.get("url") == url for source in LIVE_SOURCE_BUFFER):
                LIVE_SOURCE_BUFFER.append(live_record)
            try:
                if not any(source.get("url") == url for source in st.session_state.live_sources):
                    st.session_state.live_sources.append(live_record)
            except Exception:
                pass
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


def is_greeting(text):
    """Return True for a standalone greeting that should not start research."""
    normalized = re.sub(r"[^a-z\s]", "", text.lower()).strip()
    return normalized in {
        "hi", "hello", "hey", "hiya", "howdy", "greetings",
        "good morning", "good afternoon", "good evening", "how are you",
    }


# =========================================================
# Multi-agent crew: SCOUT -> ANALYST -> VERIFIER -> WRITER
# =========================================================
AGENT_DEFS = [
    {
        "id": "scout",
        "name": "SCOUT",
        "role": "Web Scout",
        "color": "#38e1ff",
        "tagline": "Live web search · Tavily",
        "goal": "Gather fresh, authoritative live sources for the user's request using Tavily web search.",
        "backstory": (
            "You are a fast, thorough web scout. You run targeted searches, "
            "collect the most authoritative and recent sources, and hand over "
            "exact titles, URLs and evidence snippets. You never summarise away "
            "the source — the next agent must be able to check your work."
        ),
    },
    {
        "id": "analyst",
        "name": "ANALYST",
        "role": "Insight Analyst",
        "color": "#b6a4ff",
        "tagline": "Patterns · comparisons",
        "goal": "Synthesize the scout's evidence into clear patterns, comparisons and trade-offs.",
        "backstory": (
            "You are a sharp insight analyst. You read the scout's evidence, "
            "spot agreements and contradictions, compare options side by side, "
            "and turn raw findings into structured insight. You never invent "
            "numbers or claims that the evidence does not support."
        ),
    },
    {
        "id": "verifier",
        "name": "VERIFIER",
        "role": "Fact Checker",
        "color": "#5df0a8",
        "tagline": "Cross-checks · flags doubt",
        "goal": "Cross-check important claims against independent sources and flag anything uncertain or unverified.",
        "backstory": (
            "You are a sceptical fact checker. You re-check the important claims "
            "against independent sources, mark anything that is single-sourced, "
            "outdated or uncertain, and strike anything that cannot be verified. "
            "You never invent a URL, a statistic or a quotation."
        ),
    },
    {
        "id": "writer",
        "name": "WRITER",
        "role": "Report Composer",
        "color": "#ffc46b",
        "tagline": "Structured final report",
        "goal": "Write the final structured report in the requested style and depth, citing only real Tavily URLs.",
        "backstory": (
            "You are a precise report composer. You turn verified findings into "
            "a polished, well-structured report in the requested style, with "
            "clear headings and a Sources section that lists only URLs actually "
            "returned by Tavily. You never add a source you did not receive."
        ),
    },
]

DOCK_PLACEHOLDER = None
FEED_PLACEHOLDER = None


def robot_svg(color, size=62, working=False):
    """A distinct little robot avatar (inline SVG) for one crew agent."""
    cls = "robot robot-working" if working else "robot"
    return (
        f'<svg class="{cls}" width="{size}" height="{size}" viewBox="0 0 64 64" '
        f'xmlns="http://www.w3.org/2000/svg" role="img" aria-label="robot avatar">'
        f'<line x1="32" y1="12" x2="32" y2="5" stroke="{color}" stroke-width="2.5" stroke-linecap="round"/>'
        f'<circle cx="32" cy="5" r="3.4" fill="{color}"/>'
        f'<rect x="14" y="12" width="36" height="27" rx="10" fill="#0e2237" stroke="{color}" stroke-width="2"/>'
        f'<circle cx="24.5" cy="24" r="3.6" fill="{color}"/>'
        f'<circle cx="39.5" cy="24" r="3.6" fill="{color}"/>'
        f'<path d="M26 31 Q32 35.5 38 31" stroke="{color}" stroke-width="2" fill="none" stroke-linecap="round"/>'
        f'<rect x="18" y="42" width="28" height="15" rx="7.5" fill="#0e2237" stroke="{color}" stroke-width="2"/>'
        f'<circle cx="32" cy="49.5" r="3.2" fill="{color}"/>'
        f'<line x1="14" y1="48" x2="8" y2="44" stroke="{color}" stroke-width="2" stroke-linecap="round"/>'
        f'<line x1="50" y1="48" x2="56" y2="44" stroke="{color}" stroke-width="2" stroke-linecap="round"/>'
        f'</svg>'
    )


def agent_status_label(status):
    return {"idle": "Idle", "working": "Working", "done": "Done"}.get(status, "Idle")


def render_agent_dock(status, feed=None):
    """HTML for the Agent Dock: 4 robot avatars with name, role and status pill."""
    cards = []
    for agent in AGENT_DEFS:
        state = status.get(agent["id"], "idle")
        color = agent["color"]
        check = '<span class="agent-check">✓</span>' if state == "done" else ""
        cards.append(
            f'<div class="agent-card {state}" style="--ac:{color}">'
            f'{check}{robot_svg(color, working=(state == "working"))}'
            f'<div class="agent-name" style="color:{color}">{agent["name"]}</div>'
            f'<div class="agent-role">{agent["role"]}</div>'
            f'<div class="agent-role" style="font-size:.64rem">{agent["tagline"]}</div>'
            f'<span class="agent-pill pill-{state}">{agent_status_label(state)}</span>'
            f'</div>'
        )
    html = '<div class="agent-dock">' + "".join(cards) + "</div>"
    if feed:
        lines = "".join(f"<div>{line}</div>" for line in feed[-6:])
        html += f'<div class="agent-feed">{lines}</div>'
    return html


def refresh_dock():
    """Re-render the live dock + feed placeholders during a run (no-op outside a run)."""
    if DOCK_PLACEHOLDER is not None:
        DOCK_PLACEHOLDER.markdown(
            render_agent_dock(st.session_state.agent_status, st.session_state.agent_feed),
            unsafe_allow_html=True,
        )


def _task_callback_factory():
    """CrewAI task_callback: mark each agent done in order as its task finishes."""
    order = [a["id"] for a in AGENT_DEFS]
    counter = {"n": 0}

    def _callback(_task_output):
        idx = counter["n"]
        counter["n"] += 1
        if idx < len(order):
            done_id = order[idx]
            st.session_state.agent_status[done_id] = "done"
            agent = AGENT_DEFS[idx]
            st.session_state.agent_feed.append(
                f"<b>{agent['name']}</b> finished — {agent['role']} complete ✓"
            )
            if idx + 1 < len(order):
                nxt = AGENT_DEFS[idx + 1]
                st.session_state.agent_status[nxt["id"]] = "working"
                st.session_state.agent_feed.append(
                    f"<b>{nxt['name']}</b> is now working…"
                )
        refresh_dock()

    return _callback


def run_research(user_request: str, depth: str, report_style: str, dock_ph=None, feed_ph=None):
    if is_greeting(user_request):
        return (
            "Hello! I’m Nexus Research AI. What would you like to investigate today? "
            "You can ask me to research a topic, compare sources, or continue an earlier thread."
        )

    if not KEYS_READY:
        return (
            "Live research needs API keys. Add GEMINI_API_KEY and TAVILY_API_KEY "
            "in Streamlit Cloud → App settings → Secrets, then ask again — "
            "or try the ▶ Run demo button to see the crew work with sample data."
        )

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
        "Detailed Report": (
            "Produce a deep, multi-page academic-style report of approximately 2200–3200 words "
            "unless the evidence genuinely does not support that length. Use formal but readable prose, "
            "define important terms, synthesize multiple independent sources, and distinguish evidence from inference. "
            "Include all of these sections in this order: Executive Summary (5–8 substantial paragraphs), "
            "Research Scope & Method, Key Findings (at least 8 numbered findings with citations), "
            "Detailed Analysis (at least 4 clearly titled subsections), Comparative Perspective, "
            "Implications, Limitations & Caveats, and Sources. Do not compress this into a brief."
        ),
        "Technical Analysis": "Emphasize mechanisms, technical evidence, implementation details, and limitations.",
    }

    conversation_context = build_context()

    llm = LLM(
        model=f"gemini/{GEMINI_MODEL}",
        api_key=GEMINI_API_KEY,
        temperature=0.2,
    )

    global DOCK_PLACEHOLDER, FEED_PLACEHOLDER
    DOCK_PLACEHOLDER, FEED_PLACEHOLDER = dock_ph, feed_ph
    st.session_state.agent_status = {a["id"]: "idle" for a in AGENT_DEFS}
    st.session_state.agent_status["scout"] = "working"
    st.session_state.agent_feed = ["<b>SCOUT</b> is now working…"]
    refresh_dock()

    scout = Agent(
        role="Web Scout",
        goal=AGENT_DEFS[0]["goal"],
        backstory=AGENT_DEFS[0]["backstory"],
        tools=[tavily_web_search],
        llm=llm,
        allow_delegation=False,
        verbose=False,
        max_iter=10,
    )
    analyst = Agent(
        role="Insight Analyst",
        goal=AGENT_DEFS[1]["goal"],
        backstory=AGENT_DEFS[1]["backstory"],
        tools=[],
        llm=llm,
        allow_delegation=False,
        verbose=False,
        max_iter=8,
    )
    verifier = Agent(
        role="Fact Checker",
        goal=AGENT_DEFS[2]["goal"],
        backstory=AGENT_DEFS[2]["backstory"],
        tools=[],
        llm=llm,
        allow_delegation=False,
        verbose=False,
        max_iter=8,
    )
    writer = Agent(
        role="Report Composer",
        goal=AGENT_DEFS[3]["goal"],
        backstory=AGENT_DEFS[3]["backstory"],
        tools=[],
        llm=llm,
        allow_delegation=False,
        verbose=False,
        max_iter=8,
    )

    scout_task = Task(
        description=f"""
CURRENT USER REQUEST:
{user_request}

CONVERSATION MEMORY:
{conversation_context}

RESEARCH DEPTH:
{depth_rules[depth]}

You are SCOUT. Search the live web with Tavily Web Search, running several
targeted queries. Collect the strongest, most authoritative and most recent
sources. For each source record its exact title, exact URL and a short evidence
snippet. Prefer primary, official, academic or otherwise authoritative sources;
for paper-focused requests also seek arXiv, PubMed, Semantic Scholar, Crossref,
ACM, IEEE or official institutional repositories. Never invent a source or URL.
Return a structured evidence pack: the key facts found, grouped by theme, each
with its source title and URL.
""",
        expected_output="A structured evidence pack: key facts grouped by theme, each with exact source title and URL.",
        agent=scout,
    )
    analyst_task = Task(
        description="""
You are ANALYST. Using SCOUT's evidence pack, synthesize the findings: find
patterns, agreements and contradictions, compare the main options side by side,
and draw out the trade-offs and implications. Organize the synthesis into clear
themes with the evidence behind each. Do not invent numbers or claims the
evidence does not support; mark anything weakly supported as uncertain.
""",
        expected_output="A structured synthesis: themes, patterns, comparisons and trade-offs, each tied to the scout's evidence.",
        agent=analyst,
        context=[scout_task],
    )
    verifier_task = Task(
        description="""
You are VERIFIER. Cross-check the ANALYST's important claims against
independent sources in SCOUT's evidence pack. Confirm what is corroborated,
flag anything single-sourced, outdated or uncertain, and strike anything that
cannot be verified. Also check that every finding carries a citation to a real
URL from the evidence pack — flag any finding without one. List the verified
claims and the flagged items separately. Never invent a URL, statistic or
quotation. Only cite URLs from the evidence pack.
""",
        expected_output="A verification report: verified claims plus a flagged-items list of uncertain or unverified claims.",
        agent=verifier,
        context=[analyst_task],
    )
    writer_task = Task(
        description=f"""
You are WRITER. Write the final report from the VERIFIER's verified findings,
in this output style: {style_rules[report_style]}

RESEARCH DEPTH:
{depth_rules[depth]}

COMPLETE REPORT CONTRACT — the final report must be a COMPLETE research
report, never a brief summary. It must contain ALL of these Markdown sections,
in this exact order, with every section completed. No section may be skipped,
merged away, or compressed into a short list:

# Executive Summary
# Research Scope & Method
# Key Findings
# Detailed Analysis
# Comparative Perspective
# Implications
# Limitations & Caveats
# Sources

Section requirements:
- Executive Summary: a substantial opening synthesis of the whole answer.
- Research Scope & Method: what was investigated, how sources were searched
  and selected, and what was out of scope.
- Key Findings: at least 8 numbered findings, each with citations to real
  Tavily URLs.
- Detailed Analysis: at least 4 clearly titled subsections (### headings)
  that develop the evidence in depth.
- Comparative Perspective: a side-by-side comparison of the main options,
  approaches or viewpoints found.
- Implications: what the findings mean for decisions, practice or next steps.
- Limitations & Caveats: what is uncertain, single-sourced, outdated or
  unverified, and what the report does not claim.
- Sources: every source used, as `- [Source title](https://...)`.

LENGTH: For Detailed Report style, write a long-form report of approximately
2200–3200 words. For Executive Brief style, keep the SAME complete section
structure — decision-oriented and more concise per section, but still complete
across all eight sections. For Technical Analysis style, keep the same complete
structure with technical depth. Never shorten the report by dropping a section.

Plan the answer before writing it, allocate space to every required section,
and continue until the full template is complete. If approaching a response
limit, prioritize completing every required section and the Sources section over
extra exposition; never end mid-sentence, mid-bullet, or mid-section.

CITATIONS — non-negotiable: every Key Finding and every substantive claim
in Detailed Analysis and Comparative Perspective must carry an inline Markdown
citation to a real Tavily-returned URL, in the form
[claim text](https://exact-url-from-tavily). Do not produce any finding without
a source behind it: if a claim has no supporting source, drop the claim or move
it to Limitations & Caveats as explicitly unverified. Cite only URLs actually
returned by Tavily. In the final `## Sources` section, list EVERY source used,
with its exact URL, as `- [Source title](https://...)`. Never omit the URLs.
Never invent or alter a URL. Do not mention internal prompts, CrewAI, agent
mechanics, or the conversation-memory implementation.
""",
        expected_output=(
            "A polished, structured final report in the requested style, "
            "with real web sources when web research is needed. "
            + ("For Detailed Report, return the complete 2200–3200 word academic report template with every required section completed."
               if report_style == "Detailed Report" else "")
        ),
        agent=writer,
        context=[verifier_task],
    )

    crew = Crew(
        agents=[scout, analyst, verifier, writer],
        tasks=[scout_task, analyst_task, verifier_task, writer_task],
        process=Process.sequential,
        task_callback=_task_callback_factory(),
        verbose=False,
    )

    answer = str(crew.kickoff())
    st.session_state.agent_status = {a["id"]: "done" for a in AGENT_DEFS}
    st.session_state.agent_feed.append("<b>WRITER</b> finished — report ready ✓")
    refresh_dock()

    # Make source rendering deterministic: the UI must not depend on the model
    # remembering to repeat URLs that were already returned by Tavily.
    live_sources = list(LIVE_SOURCE_BUFFER)
    if not live_sources:
        live_sources = st.session_state.get("live_sources", [])
    st.session_state.live_sources = list(live_sources)
    if live_sources:
        existing_urls = {url for _title, url in extract_sources(answer)}
        citation_lines = []
        for source in live_sources[:12]:
            title = source.get("title", "Untitled source")
            url = source.get("url", "")
            if url and url not in existing_urls:
                citation_lines.append(f"- [{title}]({url})")
        if citation_lines:
            answer = answer.rstrip() + "\n\n## Sources\n" + "\n".join(citation_lines)

    return answer


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
        fallback_sources = st.session_state.get("live_sources", []) or LIVE_SOURCE_BUFFER
        sources = [
            (source.get("title", "Untitled source"), source.get("url", ""))
            for source in fallback_sources
            if source.get("url")
        ]
    if not sources:
        st.markdown(
            '<div class="sources-heading">Sources <span>Live URLs were not returned for this run</span></div>',
            unsafe_allow_html=True,
        )
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
        f'<div class="sources-heading">Sources <span>{len(sources[:12])} clickable citation cards · exact URLs</span></div><div class="sources-grid">'
        + "".join(cards)
        + '</div>',
        unsafe_allow_html=True,
    )


def render_live_sources(sources):
    """Render the exact live-search records captured during the current run."""
    sources = sources or LIVE_SOURCE_BUFFER
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


DEMO_QUERY = "Research the current AI coding assistant market in 2026."

DEMO_REPORT = """# Executive Summary

AI coding assistants have moved from autocomplete curiosities to core developer
tooling in 2026. GitHub Copilot remains the broadest-installed assistant
([GitHub Copilot](https://github.com/features/copilot)), Cursor has become the
reference point for AI-native editing ([Cursor](https://cursor.com)), Windsurf
and Amazon Q Developer compete on team and cloud-integrated workflows
([Windsurf](https://windsurf.com), [Amazon Q Developer](https://aws.amazon.com/q/developer/)),
Sourcegraph Cody leans on whole-codebase context
([Sourcegraph Cody](https://sourcegraph.com/cody)), JetBrains AI brings
assistance into its mature IDEs ([JetBrains AI](https://www.jetbrains.com/ai/)),
and Replit Agent targets building full apps from a prompt
([Replit](https://replit.com)).

The market is no longer decided by raw model quality alone. The differentiators
in 2026 are agentic workflows — assistants that plan, edit across files, run
tests and iterate — plus codebase understanding, model choice, privacy controls
and pricing. Teams now evaluate assistants on how much of a real task they can
complete unsupervised, not on how good a single suggestion looks.

# Research Scope & Method

This sample report covers the leading AI coding assistants available in 2026:
GitHub Copilot, Cursor, Windsurf, Amazon Q Developer, Sourcegraph Cody,
JetBrains AI and Replit Agent. It compares them on agentic capability,
codebase context, privacy and deployment options, and pricing approach. The
sample is drawn from the vendors' own product pages (listed in Sources); it
does not include hands-on benchmarking or usage telemetry, and it does not
assert market-share figures, which would need independent measurement.

# Key Findings

1. GitHub Copilot is the most widely deployed assistant, deeply integrated
   into Visual Studio Code, JetBrains IDEs, Neovim and GitHub itself, with
   agent mode and code review features
   ([GitHub Copilot](https://github.com/features/copilot)).
2. Cursor pioneered the AI-native editor model and set the bar for agentic
   multi-file editing and codebase-aware chat
   ([Cursor](https://cursor.com)).
3. Windsurf (formerly Codeium) targets teams with agentic flows and
   enterprise deployment options
   ([Windsurf](https://windsurf.com)).
4. Amazon Q Developer is the AWS-integrated assistant, built for developers
   working inside the AWS cloud and its services
   ([Amazon Q Developer](https://aws.amazon.com/q/developer/)).
5. Sourcegraph Cody uses the whole codebase — including dependencies and
   history — as context for answers and edits
   ([Sourcegraph Cody](https://sourcegraph.com/cody)).
6. JetBrains AI integrates assistance across the JetBrains IDE family with
   local-model options for sensitive code
   ([JetBrains AI](https://www.jetbrains.com/ai/)).
7. Replit Agent aims at full-app generation from natural language, lowering
   the barrier for non-developers
   ([Replit](https://replit.com)).
8. Model choice matters: most assistants now let users switch between
   frontier models, so the assistant's workflow matters more than the model
   ([Cursor](https://cursor.com), [GitHub Copilot](https://github.com/features/copilot)).

# Detailed Analysis

### The agentic shift

The defining change in 2026 is the move from completion to agency. Assistants
now take a task, plan the changes, edit several files, run the test suite and
fix their own mistakes. Cursor's agent mode and GitHub Copilot's agent mode
are the clearest examples, and every competitor has followed
([Cursor](https://cursor.com), [GitHub Copilot](https://github.com/features/copilot)).

### Codebase context wins

Assistants that understand the whole repository — its structure, conventions
and history — produce far more useful edits. Sourcegraph Cody and Cursor
invest most heavily here, while Copilot leans on its deep editor integration
([Sourcegraph Cody](https://sourcegraph.com/cody), [Cursor](https://cursor.com)).

### Privacy and enterprise deployment

Regulated teams care where code goes. Windsurf offers enterprise deployment
options, and most vendors now publish explicit no-training-on-your-code
commitments. This is a buying criterion, not a footnote, for banks,
healthcare and government teams
([Windsurf](https://windsurf.com), [Amazon Q Developer](https://aws.amazon.com/q/developer/)).

### Pricing and model choice

Per-seat subscriptions dominate, with free tiers for individuals. Because
most tools now offer a choice of frontier models, switching costs are falling
and teams increasingly standardise on the workflow rather than the model
([JetBrains AI](https://www.jetbrains.com/ai/), [Replit](https://replit.com)).

# Comparative Perspective

Copilot leads on reach and ecosystem integration
([GitHub Copilot](https://github.com/features/copilot)); Cursor leads on the
AI-native editing experience ([Cursor](https://cursor.com)); Windsurf and
Amazon Q Developer lead on enterprise and cloud-integrated deployment
([Windsurf](https://windsurf.com), [Amazon Q Developer](https://aws.amazon.com/q/developer/));
Cody leads on whole-codebase context
([Sourcegraph Cody](https://sourcegraph.com/cody)); JetBrains AI leads for
teams already living in JetBrains IDEs
([JetBrains AI](https://www.jetbrains.com/ai/)); Replit Agent leads for
building complete apps from a prompt ([Replit](https://replit.com)). No single
tool wins on every axis, so the right choice depends on the team's editor,
codebase size, privacy needs and budget.

# Implications

Teams choosing an assistant in 2026 should trial two or three tools on a real
task from their own backlog rather than judging by demos. Measure how much of
the task completes without intervention, how often the assistant's edits pass
review and tests, and how it behaves on the team's own codebase. Procurement
should also confirm data-handling terms in writing before rollout.

# Limitations & Caveats

This is a sample report generated for demonstration. Product capabilities and
pricing change frequently; verify current details on the vendors' own pages
before making a purchasing decision. No usage statistics or market-share
figures are asserted here, because reliable current figures were not part of
this sample. The comparisons reflect vendor positioning and widely reported
capabilities, not independent hands-on benchmarking.

# Sources

- [GitHub Copilot](https://github.com/features/copilot)
- [Cursor](https://cursor.com)
- [Windsurf](https://windsurf.com)
- [Amazon Q Developer](https://aws.amazon.com/q/developer/)
- [Sourcegraph Cody](https://sourcegraph.com/cody)
- [JetBrains AI](https://www.jetbrains.com/ai/)
- [Replit](https://replit.com)
"""


def run_demo(dock_ph, feed_ph):
    """Simulated crew run: agents activate in sequence, no API calls."""
    st.session_state.agent_status = {a["id"]: "idle" for a in AGENT_DEFS}
    st.session_state.agent_feed = []
    st.session_state.demo_notice = True
    for agent in AGENT_DEFS:
        st.session_state.agent_status[agent["id"]] = "working"
        st.session_state.agent_feed.append(f"<b>{agent['name']}</b> is now working…")
        dock_ph.markdown(
            render_agent_dock(st.session_state.agent_status, st.session_state.agent_feed),
            unsafe_allow_html=True,
        )
        time.sleep(1.4)
        st.session_state.agent_status[agent["id"]] = "done"
        st.session_state.agent_feed.append(
            f"<b>{agent['name']}</b> finished — {agent['role']} complete ✓"
        )
        dock_ph.markdown(
            render_agent_dock(st.session_state.agent_status, st.session_state.agent_feed),
            unsafe_allow_html=True,
        )
    st.session_state.agent_feed.append("<b>WRITER</b> finished — report ready ✓")
    st.session_state.live_sources = [
        {"title": "GitHub Copilot", "url": "https://github.com/features/copilot", "domain": "github.com", "published": "Sample", "snippet": "AI pair programmer in your editor."},
        {"title": "Cursor", "url": "https://cursor.com", "domain": "cursor.com", "published": "Sample", "snippet": "The AI code editor."},
        {"title": "Windsurf", "url": "https://windsurf.com", "domain": "windsurf.com", "published": "Sample", "snippet": "Agentic IDE for teams."},
        {"title": "Amazon Q Developer", "url": "https://aws.amazon.com/q/developer/", "domain": "aws.amazon.com", "published": "Sample", "snippet": "AWS-integrated AI coding assistant."},
        {"title": "Sourcegraph Cody", "url": "https://sourcegraph.com/cody", "domain": "sourcegraph.com", "published": "Sample", "snippet": "AI coding assistant with codebase context."},
        {"title": "JetBrains AI", "url": "https://www.jetbrains.com/ai/", "domain": "jetbrains.com", "published": "Sample", "snippet": "AI in JetBrains IDEs."},
        {"title": "Replit", "url": "https://replit.com", "domain": "replit.com", "published": "Sample", "snippet": "Build apps from a prompt."},
    ]
    st.session_state.messages.append({"role": "user", "content": DEMO_QUERY})
    st.session_state.messages.append({"role": "assistant", "content": DEMO_REPORT, "demo": True})
    st.session_state.research_history.append(
        {"user": DEMO_QUERY, "assistant": DEMO_REPORT, "live_sources": list(st.session_state.live_sources)}
    )


def _split_report_sections(answer):
    """Split a markdown report into {section title: body} by # or ## headings."""
    parts = re.split(r"(?m)^#{1,2}\s+(.+?)\s*$", answer)
    sections = {}
    intro = parts[0].strip()
    if intro:
        sections["__intro__"] = intro
    for i in range(1, len(parts) - 1, 2):
        sections[parts[i].strip()] = parts[i + 1].strip()
    return sections


def _md_inline(text):
    rendered = escape(text)
    rendered = re.sub(
        r"\[([^\]]+)\]\((https?://[^)]+)\)",
        lambda m: f'<a href="{escape(m.group(2), quote=True)}" target="_blank" rel="noopener">{escape(m.group(1))}</a>',
        rendered,
    )
    rendered = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", rendered)
    return rendered


def _md_paragraphs(text):
    out = []
    buf = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            if buf:
                out.append(f"<p>{' '.join(_md_inline(x) for x in buf)}</p>")
                buf = []
            continue
        if line.startswith("### "):
            if buf:
                out.append(f"<p>{' '.join(_md_inline(x) for x in buf)}</p>")
                buf = []
            out.append(f'<div class="rw-h3">{escape(line[4:])}</div>')
        elif line.startswith("# "):
            if buf:
                out.append(f"<p>{' '.join(_md_inline(x) for x in buf)}</p>")
                buf = []
            out.append(f'<div class="rw-section">{escape(line[2:])}</div>')
        elif line.startswith("## "):
            if buf:
                out.append(f"<p>{' '.join(_md_inline(x) for x in buf)}</p>")
                buf = []
            out.append(f'<div class="rw-section">{escape(line[3:])}</div>')
        elif re.match(r"^[-*]\s+", line):
            if buf:
                out.append(f"<p>{' '.join(_md_inline(x) for x in buf)}</p>")
                buf = []
            out.append(f"<ul><li>{_md_inline(re.sub(r'^[-*]\s+', '', line))}</li></ul>")
        elif re.match(r"^\d+\.\s+", line):
            buf.append(line)
        else:
            buf.append(line)
    if buf:
        out.append(f"<p>{' '.join(_md_inline(x) for x in buf)}</p>")
    return "".join(out)


def _numbered_findings(body):
    """Numbered findings, keeping wrapped continuation lines (and their citations)."""
    items = []
    current = None
    for line in body.splitlines():
        m = re.match(r"^(\d+)\.\s+(.*)", line.strip())
        if m:
            if current is not None:
                items.append(current)
            current = m.group(2).strip()
        elif current is not None and line.strip():
            current += " " + line.strip()
    if current is not None:
        items.append(current)
    return items


def render_report_window(answer, query, key_prefix="latest", demo=False):
    """Render the final report in its own dedicated glass window.

    The window is one Streamlit bordered container, so the title bar, the
    structured sections, the citation cards and the export buttons all live
    inside a single bordered panel.
    """
    stamp = datetime.now().strftime("%b %d, %Y · %H:%M")
    demo_tag = (
        '<span style="background:#ffc46b;color:#07101d;border-radius:999px;padding:.18rem .55rem;'
        'font-size:.62rem;font-weight:800;letter-spacing:.08em">DEMO — SAMPLE DATA, NOT LIVE RESEARCH</span>'
        if demo else ""
    )
    with st.container(border=True):
        st.markdown(
            f'<div class="report-titlebar">'
            f'<span class="traffic-dots"><span></span><span></span><span></span></span>'
            f'<span class="rw-label">RESEARCH REPORT</span>'
            f'<span class="rw-query">{escape(query)}</span>{demo_tag}'
            f'<span class="rw-time">{stamp}</span></div>',
            unsafe_allow_html=True,
        )
        sections = _split_report_sections(answer)
        exec_text = (
            sections.get("Executive Summary")
            or sections.get("__intro__")
            or ""
        )
        if exec_text:
            st.markdown(
                f'<div class="exec-box">{_md_paragraphs(exec_text)}</div>',
                unsafe_allow_html=True,
            )
        findings = _numbered_findings(sections.get("Key Findings", ""))
        if findings:
            st.markdown('<div class="rw-section">Key Findings <span>numbered, evidence-backed</span></div>', unsafe_allow_html=True)
            cards = "".join(
                f'<div class="finding-card"><span class="finding-num">{i}</span><span>{_md_inline(item)}</span></div>'
                for i, item in enumerate(findings, 1)
            )
            st.markdown(cards, unsafe_allow_html=True)
        for title, body in sections.items():
            if title in ("Executive Summary", "Key Findings", "Sources", "__intro__"):
                continue
            if not body:
                continue
            st.markdown(
                f'<div class="rw-block"><div class="rw-section">{escape(title)}</div>'
                f"{_md_paragraphs(body)}</div>",
                unsafe_allow_html=True,
            )
        if not sections or (len(sections) == 1 and "__intro__" in sections):
            st.markdown(answer)
        render_source_panel(answer)
        render_export_panel(answer, query, key_prefix=key_prefix)


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
        LIVE_SOURCE_BUFFER.clear()
        st.rerun()

# =========================================================
# Hero
# =========================================================
st.markdown(
    """
<div class="hero">
    <span class="badge">✦ 4-AGENT CREW · SCOUT · ANALYST · VERIFIER · WRITER</span>
    <h1><span class="gradient-text">Research the web.<br>Keep the context.</span></h1>
    <p>
        Ask a question and watch a four-agent crew go to work: SCOUT gathers live
        sources, ANALYST finds the patterns, VERIFIER cross-checks every claim, and
        WRITER composes your structured report. Nexus remembers the current chat
        session so follow-up questions can refer to earlier research without
        starting from zero.
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
# Agent Dock + Demo mode
# =========================================================
    st.markdown(
        '<div class="section-title">Agent Dock '
        '<span style="font-size:.72rem;color:#7891a8;font-family:\'DM Sans\',sans-serif;font-weight:500">'
        'Four specialists, one crew — watch them work</span></div>',
        unsafe_allow_html=True,
    )
    dock_ph = st.empty()
    dock_ph.markdown(
        render_agent_dock(st.session_state.agent_status, st.session_state.agent_feed),
        unsafe_allow_html=True,
    )

    demo_col, demo_note = st.columns([1.5, 3])
    with demo_col:
        demo_clicked = st.button(
            "▶ Run demo",
            use_container_width=True,
        )
    with demo_note:
        st.markdown(
            '<div class="small-muted" style="padding-top:.65rem">'
            "Demo mode runs the four agents on sample data — clearly labelled, never live research.</div>",
            unsafe_allow_html=True,
        )

    if demo_clicked:
        run_demo(dock_ph, None)
        st.rerun()

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
            if is_greeting(last_user_request):
                with st.chat_message("assistant"):
                    st.markdown(message["content"])
            else:
                render_report_window(
                    message["content"],
                    last_user_request,
                    key_prefix=f"history_{message_index}",
                    demo=bool(message.get("demo")),
                )

    # =========================================================

# Chat input
# =========================================================
user_request = st.chat_input(
    "Ask a research question or continue the conversation…"
)

if user_request:
    st.session_state.live_sources = []
    LIVE_SOURCE_BUFFER.clear()
    st.session_state.messages.append(
        {"role": "user", "content": user_request}
    )

    st.markdown(
        f'<div class="user-message"><div class="user-message-label">You</div>{escape(user_request)}</div>',
        unsafe_allow_html=True,
    )

    started = datetime.now()

    if is_greeting(user_request):
        answer = run_research(user_request=user_request, depth=depth, report_style=report_style)
        with st.chat_message("assistant"):
            st.markdown(answer)
    else:
        with st.chat_message("assistant"):
            try:
                answer = run_research(
                    user_request=user_request,
                    depth=depth,
                    report_style=report_style,
                    dock_ph=dock_ph,
                )
            except Exception as exc:
                st.markdown('<div class="activity-wrap"><span class="activity-dot" style="background:#ff7f9a;box-shadow:0 0 0 5px rgba(255,127,154,.08),0 0 18px rgba(255,127,154,.65);"></span><div><div class="activity-text">Research stopped</div><div class="activity-sub">Something went wrong while processing the request</div></div></div>', unsafe_allow_html=True)
                st.error(f"Research failed: {exc}")
                st.stop()
            render_report_window(answer, user_request, key_prefix="latest")

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
