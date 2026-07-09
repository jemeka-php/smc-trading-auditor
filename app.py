"""
AI Trading Auditor — Multi-Strategy Edition
Streamlit + Google Gemini Vision AI
8 Strategies: SMC, Trendline Mastery, Wyckoff, ICT, Supply & Demand,
               Breakout & Retest, EMA Confluence, Order Flow Analysis
"""

import os
import io
import requests
import streamlit as st
from PIL import Image
from google import genai
from google.genai import types
from dotenv import load_dotenv
from strategies import (
    STRATEGIES,
    SIGNAL_SYSTEM_INSTRUCTION, SIGNAL_OUTPUT_TEMPLATE,
    FEEDBACK_SYSTEM_INSTRUCTION, FEEDBACK_OUTPUT_TEMPLATE,
    DEBATE_CHALLENGER_INSTRUCTION, DEBATE_SYNTHESIS_INSTRUCTION
)
from coin_scanner import get_top_midcap_coins

load_dotenv()

# ── Page Config ───────────────────────────────
st.set_page_config(
    page_title="AI Trading Auditor | Multi-Strategy Risk Engine",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;600&display=swap');

html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
.stApp { background-color: #0d1117; color: #c9d1d9; }
.block-container { padding-top: 2rem; padding-bottom: 2rem; max-width: 1400px; }

[data-testid="stSidebar"] {
    background-color: #161b22;
    border-right: 1px solid #21262d;
}
[data-testid="stSidebar"] * { color: #c9d1d9 !important; }
h1, h2, h3 { color: #58a6ff !important; font-weight: 700; }

.title-banner {
    background: linear-gradient(135deg, #0d1117 0%, #161b22 50%, #0d1117 100%);
    border: 1px solid #21262d;
    border-top: 3px solid #58a6ff;
    border-radius: 10px;
    padding: 1.5rem 2rem;
    margin-bottom: 2rem;
    text-align: center;
}
.title-banner h1 { font-size: 2rem; color: #58a6ff !important; margin: 0; letter-spacing: -0.5px; }
.title-banner p { color: #8b949e; font-size: 0.95rem; margin-top: 0.5rem; }

.panel-label {
    font-size: 0.7rem; font-weight: 600; letter-spacing: 1.5px;
    text-transform: uppercase; color: #58a6ff; margin-bottom: 0.8rem;
}
.strategy-card {
    background: linear-gradient(135deg, #0c2a4a 0%, #0d1117 100%);
    border: 1px solid #1f6feb;
    border-radius: 8px;
    padding: 0.7rem 1rem;
    margin-bottom: 1rem;
}
.strategy-card .s-name { color: #58a6ff; font-weight: 700; font-size: 0.95rem; }
.strategy-card .s-desc { color: #8b949e; font-size: 0.75rem; margin-top: 0.25rem; }

div[data-testid="stButton"] > button {
    background-color: #238636; color: #ffffff; border: none;
    border-radius: 8px; padding: 0.75rem 2rem; font-size: 1rem;
    font-weight: 600; width: 100%; cursor: pointer;
    transition: background-color 0.2s ease, transform 0.1s ease, box-shadow 0.2s ease;
}
div[data-testid="stButton"] > button:hover {
    background-color: #2ea043;
    transform: translateY(-1px);
    box-shadow: 0 4px 20px rgba(46,160,67,0.35);
}
div[data-testid="stButton"] > button:active { transform: translateY(0px); }
div[data-testid="stButton"] > button:disabled {
    background-color: #21262d !important; color: #484f58 !important; cursor: not-allowed;
}

.stTextInput input {
    background-color: #0d1117 !important;
    border: 1px solid #30363d !important;
    color: #c9d1d9 !important;
    border-radius: 6px !important;
}
.stTextInput input:focus {
    border-color: #58a6ff !important;
    box-shadow: 0 0 0 2px rgba(88,166,255,0.2) !important;
}
.stRadio > div { gap: 0.5rem; }

.chip-row { display: flex; gap: 0.5rem; flex-wrap: wrap; margin-bottom: 1rem; }
.chip {
    background-color: #21262d; border: 1px solid #30363d; color: #8b949e;
    border-radius: 20px; padding: 0.2rem 0.75rem;
    font-size: 0.75rem; font-weight: 500; font-family: 'JetBrains Mono', monospace;
}
.chip-blue  { border-color: #1f6feb; color: #58a6ff; background-color: #0c2a4a; }
.chip-green { border-color: #238636; color: #3fb950; background-color: #0d2a1a; }
.chip-amber { border-color: #9e6a03; color: #e3b341; background-color: #2a1f0d; }

.placeholder-box {
    display: flex; flex-direction: column; align-items: center; justify-content: center;
    background-color: #0d1117; border: 1px dashed #30363d; border-radius: 10px;
    padding: 3rem 2rem; text-align: center; color: #484f58; min-height: 300px;
}
.placeholder-icon { font-size: 3rem; margin-bottom: 1rem; }
.placeholder-text { font-size: 0.95rem; line-height: 1.6; }

.report-box {
    background-color: #0d1117; border: 1px solid #21262d; border-radius: 8px;
    padding: 1.5rem; line-height: 1.7; font-size: 0.9rem;
}
.verdict-tradable {
    display: inline-block; background: linear-gradient(135deg,#1a3d1f,#1e4d24);
    border: 1px solid #2ea043; color: #3fb950; padding: 0.4rem 1.2rem;
    border-radius: 20px; font-weight: 700; font-size: 1rem; margin-bottom: 1rem; letter-spacing: 1px;
}
.verdict-not-tradable {
    display: inline-block; background: linear-gradient(135deg,#3d1a1a,#4d1e1e);
    border: 1px solid #f85149; color: #f85149; padding: 0.4rem 1.2rem;
    border-radius: 20px; font-weight: 700; font-size: 1rem; margin-bottom: 1rem; letter-spacing: 1px;
}
.verdict-adjustment {
    display: inline-block; background: linear-gradient(135deg,#3d2f1a,#4d3a1e);
    border: 1px solid #d29922; color: #e3b341; padding: 0.4rem 1.2rem;
    border-radius: 20px; font-weight: 700; font-size: 1rem; margin-bottom: 1rem; letter-spacing: 1px;
}
.pillar-row {
    display: flex; align-items: center; gap: 0.6rem;
    padding: 0.4rem 0; border-bottom: 1px solid #21262d;
}
.pillar-icon { font-size: 0.9rem; min-width: 1.2rem; text-align: center; }
.pillar-text { font-size: 0.82rem; color: #8b949e; }

.model-badge {
    background-color: #21262d; border: 1px solid #30363d; border-radius: 6px;
    padding: 0.5rem 0.75rem; font-size: 0.8rem; color: #8b949e;
    font-family: 'JetBrains Mono', monospace; margin-top: 0.5rem; text-align: center;
}
hr { border-color: #21262d; }
.stSpinner > div > div { border-top-color: #58a6ff !important; }
</style>
""", unsafe_allow_html=True)

# ── Constants ─────────────────────────────────
MODELS = {
    "gemini-2.5-flash (Free Tier — Recommended)": "gemini-2.5-flash",
    "gemini-2.5-pro (Deep Reasoning)": "gemini-2.5-pro",
}
STRATEGY_NAMES = list(STRATEGIES.keys())

# ── Helper Functions ──────────────────────────
def get_api_key(sidebar_key: str) -> str:
    env_key = os.environ.get("GEMINI_API_KEY", "").strip()
    if env_key:
        return env_key
    return sidebar_key.strip() if sidebar_key else ""


def fetch_image_from_url(url: str) -> bytes | None:
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept": "image/avif,image/webp,image/apng,image/*,*/*;q=0.8",
    }
    try:
        resp = requests.get(url, headers=headers, timeout=20, stream=True)
        resp.raise_for_status()
        ct = resp.headers.get("Content-Type", "")
        if "image" not in ct and "octet-stream" not in ct:
            st.error(f"❌ URL did not return an image (Content-Type: `{ct}`). Use a direct image URL.")
            return None
        return resp.content
    except requests.exceptions.Timeout:
        st.error("❌ Request timed out.")
    except requests.exceptions.ConnectionError:
        st.error("❌ Connection error. Check the URL and your internet connection.")
    except requests.exceptions.HTTPError as e:
        st.error(f"❌ HTTP Error {e.response.status_code}: {e.response.reason}")
    except Exception as e:
        st.error(f"❌ Unexpected error: {e}")
    return None


def run_audit(image_bytes: bytes, model_id: str, api_key: str, strategy_name: str) -> str:
    strat = STRATEGIES[strategy_name]
    try:
        client = genai.Client(api_key=api_key)
        image_part = types.Part.from_bytes(data=image_bytes, mime_type="image/png")
        prompt = (
            f"Please audit this trading chart using the {strategy_name} framework "
            f"and deliver your verdict.\n\n{strat['output_template']}"
        )
        response = client.models.generate_content(
            model=model_id,
            contents=[image_part, prompt],
            config=types.GenerateContentConfig(
                system_instruction=strat["system_instruction"],
                temperature=0.1,
            ),
        )
        return response.text
    except Exception as e:
        err = str(e)
        if "API_KEY_INVALID" in err or "invalid" in err.lower():
            return "❌ **Invalid API Key.** Please double-check your Gemini API key in the sidebar."
        elif "quota" in err.lower() or "429" in err:
            return "❌ **API Quota Exceeded.** Wait a moment and retry, or switch models."
        elif "not found" in err.lower() or "404" in err:
            return f"❌ **Model Not Found:** `{model_id}`. Try `gemini-2.5-flash`."
        else:
            return f"❌ **Gemini API Error:** {err}"

def run_signal_debate(image_bytes: bytes, initial_signal: str, api_key: str) -> dict:
    """
    Runs the multi-round AI debate.
    Uses gemini-2.5-pro for the challenger, with an automatic fallback to gemini-2.5-flash if 429 quota error.
    Then uses the original proposer model (or flash) for arbitration.
    """
    client = genai.Client(api_key=api_key)
    image_part = types.Part.from_bytes(data=image_bytes, mime_type="image/png")
    
    debate_log = []
    
    # --- Round 1: Challenger (Pro with Flash Fallback) ---
    challenger_model = "gemini-2.5-pro"
    challenger_prompt = f"Here is the proposed trade signal:\n\n{initial_signal}\n\nCritique this setup."
    
    try:
        challenger_resp = client.models.generate_content(
            model=challenger_model,
            contents=[image_part, challenger_prompt],
            config=types.GenerateContentConfig(
                system_instruction=DEBATE_CHALLENGER_INSTRUCTION,
                temperature=0.45,
            )
        )
    except Exception as e:
        if "429" in str(e) or "quota" in str(e).lower():
            challenger_model = "gemini-2.5-flash"
            challenger_resp = client.models.generate_content(
                model=challenger_model,
                contents=[image_part, challenger_prompt],
                config=types.GenerateContentConfig(
                    system_instruction=DEBATE_CHALLENGER_INSTRUCTION,
                    temperature=0.45,
                )
            )
        else:
            raise e

    challenger_text = challenger_resp.text
    debate_log.append({"round": 1, "role": "Challenger", "model": challenger_model, "content": challenger_text})
    
    # If Challenger accepts, no arbitration needed.
    if "VERDICT: ACCEPT" in challenger_text.upper():
        return {
            "debate_log": debate_log,
            "final_signal": initial_signal,
            "consensus": True,
            "rounds_taken": 1
        }
        
    # --- Round 2: Arbitration ---
    arbitrator_model = "gemini-2.5-flash" # Use flash for synthesis to ensure it completes
    arbitrator_prompt = (
        f"Original Signal:\n{initial_signal}\n\n"
        f"Challenger Critique:\n{challenger_text}\n\n"
        "Please synthesize the final signal."
    )
    
    arbitrator_resp = client.models.generate_content(
        model=arbitrator_model,
        contents=[image_part, arbitrator_prompt],
        config=types.GenerateContentConfig(
            system_instruction=DEBATE_SYNTHESIS_INSTRUCTION,
            temperature=0.1,
        )
    )
    
    debate_log.append({"round": 2, "role": "Arbitrator", "model": arbitrator_model, "content": "Synthesis complete."})
    
    return {
        "debate_log": debate_log,
        "final_signal": arbitrator_resp.text,
        "consensus": False,
        "rounds_taken": 2
    }


# NOTE: Signal generation is handled inline inside tab_signal to support
# dynamic TF override and strategy hint injection into the system prompt.
# A standalone function would bypass those runtime patches.


# ── Session State Init ────────────────────────
for key, default in [
    ("image_bytes", None),
    ("audit_report", None),
    ("active_strategy", STRATEGY_NAMES[0]),
    ("signal_image_bytes", None),
    ("signal_report", None),
    ("feedback_report", None),
    ("debate_log", []),
    ("debate_final", None),
]:
    if key not in st.session_state:
        st.session_state[key] = default


# ── Sidebar ───────────────────────────────────
with st.sidebar:
    st.markdown(
        "<div style='text-align:center;margin-bottom:1.5rem;'>"
        "<span style='font-size:2rem;'>📊</span>"
        "<p style='color:#58a6ff;font-weight:700;font-size:1.1rem;margin:0.3rem 0 0;'>AI Trading Auditor</p>"
        "<p style='color:#484f58;font-size:0.75rem;margin:0;'>Multi-Strategy Risk Engine v4.0</p>"
        "</div>",
        unsafe_allow_html=True,
    )
    st.markdown("---")

    # ── API Key ───────────────────────────────
    st.markdown("**🔑 API Configuration**")
    env_key_present = bool(os.environ.get("GEMINI_API_KEY", "").strip())
    if env_key_present:
        st.success("✅ GEMINI_API_KEY loaded from environment.")
        sidebar_api_key = ""
    else:
        st.caption("No environment variable found. Enter your key below:")
        sidebar_api_key = st.text_input(
            "Gemini API Key", type="password",
            placeholder="AIzaSy...", key="api_key_input",
            help="Get a free key at https://aistudio.google.com/app/apikey",
        )

    st.markdown("---")

    # ── Model Selector ────────────────────────
    st.markdown("**🤖 Model Selection**")
    model_label = st.selectbox("Inference Model", options=list(MODELS.keys()), index=0, key="model_selector")
    selected_model = MODELS[model_label]
    st.markdown(f"<div class='model-badge'>🧠 {selected_model}</div>", unsafe_allow_html=True)

    st.markdown("---")

    # ── Strategy Selector ─────────────────────
    st.markdown("**🧩 Audit Strategy**")
    strategy_icons = {name: STRATEGIES[name]["icon"] for name in STRATEGY_NAMES}
    strategy_display = [f"{strategy_icons[n]}  {n}" for n in STRATEGY_NAMES]

    prev_strategy = st.session_state.active_strategy
    selected_display = st.radio(
        "Choose a strategy framework:",
        options=strategy_display,
        index=STRATEGY_NAMES.index(st.session_state.active_strategy),
        key="strategy_radio",
    )
    selected_strategy = STRATEGY_NAMES[strategy_display.index(selected_display)]

    # Auto-clear report on strategy switch
    if selected_strategy != prev_strategy:
        st.session_state.audit_report = None
        st.session_state.active_strategy = selected_strategy

    active = STRATEGIES[selected_strategy]

    # Strategy info card
    st.markdown(
        f"<div class='strategy-card'>"
        f"<div class='s-name'>{active['icon']} {selected_strategy}</div>"
        f"<div class='s-desc'>{active['description']}</div>"
        f"</div>",
        unsafe_allow_html=True,
    )

    # Dynamic pillars
    st.markdown("**📐 Audit Pillars**")
    for icon, label in active["pillars"]:
        st.markdown(
            f"<div class='pillar-row'>"
            f"<span class='pillar-icon'>{icon}</span>"
            f"<span class='pillar-text'>{label}</span>"
            f"</div>",
            unsafe_allow_html=True,
        )
    st.markdown(
        "<div style='margin-top:1.5rem;padding:0.8rem;background:#0d1117;"
        "border:1px solid #21262d;border-radius:6px;font-size:0.75rem;color:#484f58;'>"
        "Temperature locked at <code style='color:#58a6ff'>0.1</code> for clinical precision."
        "</div>",
        unsafe_allow_html=True,
    )


# ── Main Layout ───────────────────────────────
api_key = get_api_key(sidebar_api_key if not env_key_present else "")

st.markdown(
    "<div class='title-banner'>"
    "<h1>📊 AI Trading Auditor</h1>"
    "<p>Institutional-grade chart analysis · 8 strategies · Powered by Google Gemini AI</p>"
    "</div>",
    unsafe_allow_html=True,
)

st.markdown(
    f"<div class='chip-row'>"
    f"<div class='chip chip-blue'>🧠 {selected_model}</div>"
    f"<div class='chip'>🌡️ temp=0.1</div>"
    f"<div class='chip {'chip-green' if api_key else ''}'>{'🟢 API Key Active' if api_key else '🔴 API Key Missing'}</div>"
    f"<div class='chip chip-amber'>{active['icon']} {selected_strategy}</div>"
    f"</div>",
    unsafe_allow_html=True,
)

if not api_key:
    st.warning(
        "⚠️ No API key detected. Set the `GEMINI_API_KEY` environment variable "
        "or enter your key in the sidebar.",
        icon="🔑",
    )

# ── Tabs ──────────────────────────────────────
tab_audit, tab_signal, tab_feedback, tab_scanner = st.tabs([
    "🔍 Strategy Audit", "⚡ Signal Generator", "📝 Trade Feedback", "🔎 Coin Scanner"
])


# ════════════════════════════════════════════
#  TAB 1 — Strategy Audit
# ════════════════════════════════════════════
with tab_audit:
    col1, col2 = st.columns([1, 1], gap="large")

    with col1:
        st.markdown("<div class='panel-label'>📥 Chart Input Panel</div>", unsafe_allow_html=True)
        input_mode = st.radio(
            "Select input method:",
            options=["📎 Paste Chart Link", "🖼️ Upload Image File"],
            key="input_mode", horizontal=True,
        )
        st.markdown("<div style='margin-top:1rem;'></div>", unsafe_allow_html=True)

        if input_mode == "📎 Paste Chart Link":
            url_input = st.text_input(
                "Chart Image URL",
                placeholder="https://www.tradingview.com/x/xxxxxxxx/",
                key="url_input",
                help="Paste any direct image URL (TradingView snapshot, etc.)",
            )
            if url_input and url_input.strip():
                with st.status("🔗 Fetching chart from URL...", expanded=False) as status:
                    img_data = fetch_image_from_url(url_input.strip())
                    if img_data:
                        st.session_state.image_bytes = img_data
                        status.update(label="✅ Chart loaded successfully!", state="complete")
                    else:
                        st.session_state.image_bytes = None
                        status.update(label="❌ Failed to load image.", state="error")
        else:
            uploaded_file = st.file_uploader(
                "Drop your chart screenshot here",
                type=["png", "jpg", "jpeg", "webp", "bmp"],
                key="file_uploader",
            )
            if uploaded_file is not None:
                st.session_state.image_bytes = uploaded_file.read()

        if st.session_state.image_bytes:
            st.markdown("<div style='margin-top:1rem;'></div>", unsafe_allow_html=True)
            st.markdown("<div class='panel-label'>📈 Chart Preview</div>", unsafe_allow_html=True)
            try:
                pil_img = Image.open(io.BytesIO(st.session_state.image_bytes))
                st.image(pil_img, use_container_width=True,
                         caption=f"Resolution: {pil_img.width}×{pil_img.height}px | Mode: {pil_img.mode}")
            except Exception as e:
                st.error(f"❌ Could not render preview: {e}")
        else:
            st.markdown(
                "<div class='placeholder-box' style='margin-top:1rem;min-height:250px;'>"
                "<div class='placeholder-icon'>🖼️</div>"
                "<div class='placeholder-text'>"
                "<strong style='color:#484f58;'>No chart loaded yet</strong><br>"
                "Paste a chart link or upload a screenshot above."
                "</div></div>",
                unsafe_allow_html=True,
            )

        st.markdown("<div style='margin-top:1.5rem;'></div>", unsafe_allow_html=True)
        audit_button = st.button(
            f"🚀 Run {selected_strategy} Audit",
            key="audit_btn",
            disabled=not (st.session_state.image_bytes and api_key),
        )
        if not st.session_state.image_bytes:
            st.caption("⬆️ Load a chart to enable the audit engine.")
        elif not api_key:
            st.caption("🔑 Configure your API key in the sidebar.")

    with col2:
        st.markdown("<div class='panel-label'>🤖 AI Risk Audit Output</div>", unsafe_allow_html=True)

        if audit_button and st.session_state.image_bytes and api_key:
            st.session_state.audit_report = None
            with st.spinner(f"🧠 Analyzing with {selected_strategy} via Gemini... 15–30 seconds."):
                st.session_state.audit_report = run_audit(
                    image_bytes=st.session_state.image_bytes,
                    model_id=selected_model,
                    api_key=api_key,
                    strategy_name=selected_strategy,
                )

        if st.session_state.audit_report:
            report = st.session_state.audit_report
            upper = report.upper()
            if "NOT TRADABLE" in upper:
                badge_cls, badge_txt = "verdict-not-tradable", "❌ NOT TRADABLE"
            elif "NEEDS ADJUSTMENT" in upper:
                badge_cls, badge_txt = "verdict-adjustment", "⚠️ NEEDS ADJUSTMENT"
            elif "TRADABLE" in upper:
                badge_cls, badge_txt = "verdict-tradable", "✅ TRADABLE"
            else:
                badge_cls, badge_txt = "", ""
            if badge_txt:
                st.markdown(f"<div class='{badge_cls}'>{badge_txt}</div>", unsafe_allow_html=True)
            st.markdown(f"<div class='report-box'>{report}</div>", unsafe_allow_html=True)
            safe_name = selected_strategy.lower().replace(" ", "_").replace("&", "and").replace("/", "_")
            st.download_button(
                label="⬇️ Download Audit Report (.md)",
                data=report.encode("utf-8"),
                file_name=f"{safe_name}_audit_report.md",
                mime="text/markdown",
                key="download_report",
            )
        elif audit_button and not api_key:
            st.error("🔑 Please configure your Gemini API key in the sidebar.")
        elif audit_button and not st.session_state.image_bytes:
            st.warning("📤 Please load a chart image first.")
        else:
            pillar_pills = " &nbsp;·&nbsp; ".join(
                [f"<span style='color:#58a6ff;'>{icon} {lbl}</span>"
                 for icon, lbl in active["pillars"][:4]]
            )
            st.markdown(
                "<div class='placeholder-box' style='min-height:400px;'>"
                "<div class='placeholder-icon'>🛡️</div>"
                "<div class='placeholder-text'>"
                "<strong style='color:#484f58;'>Waiting for an image upload...</strong><br><br>"
                f"Load a chart and press <strong style='color:#2ea043;'>🚀 Run {selected_strategy} Audit</strong>"
                f" to receive an institutional-grade verdict across<br><br>{pillar_pills}"
                "</div></div>",
                unsafe_allow_html=True,
            )


# ════════════════════════════════════════════
#  TAB 2 — Signal Generator
# ════════════════════════════════════════════
with tab_signal:
    st.markdown(
        "<div style='background:linear-gradient(135deg,#0d1f0d,#0d1117);border:1px solid #238636;"
        "border-left:4px solid #3fb950;border-radius:8px;padding:1rem 1.25rem;margin-bottom:1.5rem;'>"
        "<p style='color:#3fb950;font-weight:700;font-size:1rem;margin:0;'>⚡ AI Trade Signal Generator</p>"
        "<p style='color:#8b949e;font-size:0.83rem;margin:0.4rem 0 0;'>"
        "Upload any TradingView screenshot or paste a link — the AI scans across all 8 strategy "
        "frameworks to find the single best, highest-probability trade setup and outputs a "
        "complete signal with Entry · Stop Loss · 3 Take Profit targets · R:R · Confluence Score."
        "</p></div>",
        unsafe_allow_html=True,
    )

    sig_col1, sig_col2 = st.columns([1, 1], gap="large")

    with sig_col1:
        st.markdown("<div class='panel-label'>📥 Chart Input</div>", unsafe_allow_html=True)
        sig_input_mode = st.radio(
            "Input method:",
            options=["📎 Paste Chart Link", "🖼️ Upload Image File"],
            key="sig_input_mode", horizontal=True,
        )
        st.markdown("<div style='margin-top:1rem;'></div>", unsafe_allow_html=True)

        if sig_input_mode == "📎 Paste Chart Link":
            sig_url = st.text_input(
                "Chart Image URL",
                placeholder="https://www.tradingview.com/x/xxxxxxxx/",
                key="sig_url_input",
                help="Paste any direct TradingView snapshot URL",
            )
            if sig_url and sig_url.strip():
                with st.status("🔗 Fetching chart...", expanded=False) as sig_status:
                    sig_img_data = fetch_image_from_url(sig_url.strip())
                    if sig_img_data:
                        st.session_state.signal_image_bytes = sig_img_data
                        sig_status.update(label="✅ Chart loaded!", state="complete")
                    else:
                        st.session_state.signal_image_bytes = None
                        sig_status.update(label="❌ Failed to load image.", state="error")
        else:
            sig_uploaded = st.file_uploader(
                "Drop your chart screenshot here",
                type=["png", "jpg", "jpeg", "webp", "bmp"],
                key="sig_file_uploader",
            )
            if sig_uploaded is not None:
                st.session_state.signal_image_bytes = sig_uploaded.read()

        if st.session_state.signal_image_bytes:
            st.markdown("<div style='margin-top:1rem;'></div>", unsafe_allow_html=True)
            st.markdown("<div class='panel-label'>📈 Chart Preview</div>", unsafe_allow_html=True)
            try:
                sig_pil = Image.open(io.BytesIO(st.session_state.signal_image_bytes))
                st.image(sig_pil, use_container_width=True,
                         caption=f"{sig_pil.width}×{sig_pil.height}px")
            except Exception as e:
                st.error(f"❌ Preview error: {e}")
        else:
            st.markdown(
                "<div class='placeholder-box' style='margin-top:1rem;min-height:220px;'>"
                "<div class='placeholder-icon'>🖼️</div>"
                "<div class='placeholder-text'>"
                "<strong style='color:#484f58;'>No chart loaded</strong><br>"
                "Paste a TradingView link or upload a screenshot."
                "</div></div>",
                unsafe_allow_html=True,
            )

        st.markdown("<div style='margin-top:1.5rem;'></div>", unsafe_allow_html=True)

        # ── TF Preference ──────────────────────
        st.markdown("<div class='panel-label'>⏱️ Preferred Execution Timeframe</div>", unsafe_allow_html=True)
        sig_tf_pref = st.radio(
            "Preferred execution TF",
            options=["Auto (AI decides)", "30M — Day Trade", "15M — Intraday", "5M — Precision Entry", "1M — Scalp"],
            index=0,
            key="sig_tf_pref",
            horizontal=False,
            help="The AI will calibrate entry, SL, and TP levels to this timeframe. Auto lets the AI choose based on setup quality.",
            label_visibility="collapsed",
        )

        # TF descriptions
        tf_desc = {
            "Auto (AI decides)":         ("🤖", "AI picks the best TF based on setup quality"),
            "30M — Day Trade":           ("🟦", "Clean setups · 2-8hr hold · SL 0.4%-1.2%"),
            "15M — Intraday":            ("🟩", "Kill zones · FVG fills · 30min-3hr hold"),
            "5M — Precision Entry":      ("🟨", "Tight entries · Key level touches · 15-90min"),
            "1M — Scalp":               ("🟥", "Ultra-fast · Must be 8+/10 confluence · High risk"),
        }
        icon, desc = tf_desc[sig_tf_pref]
        st.markdown(
            f"<div style='background:#161b22;border:1px solid #21262d;border-radius:6px;"
            f"padding:0.5rem 0.8rem;font-size:0.78rem;color:#8b949e;margin-top:0.4rem;'>"
            f"{icon} {desc}</div>",
            unsafe_allow_html=True,
        )
        st.markdown("<div style='margin-top:0.8rem;'></div>", unsafe_allow_html=True)

        # Strategy hint (optional)
        sig_hint = st.selectbox(
            "🎯 Strategy hint (optional)",
            options=["Auto-detect best setup"] + STRATEGY_NAMES,
            key="sig_hint",
            help="Leave on Auto to let the AI pick the best framework. Or hint a specific strategy.",
        )

        signal_button = st.button(
            "⚡ Generate Trade Signal",
            key="signal_btn",
            disabled=not (st.session_state.signal_image_bytes and api_key),
        )
        if not st.session_state.signal_image_bytes:
            st.caption("⬆️ Load a chart to generate a signal.")
        elif not api_key:
            st.caption("🔑 Configure your API key in the sidebar.")

        # What this checks
        st.markdown("<div style='margin-top:1.5rem;'></div>", unsafe_allow_html=True)
        st.markdown("<div class='panel-label'>🔎 AI Scans For</div>", unsafe_allow_html=True)
        for item in [
            ("🌊", "Liquidity sweeps & order blocks"),
            ("📐", "Trendline bounces & break-retests"),
            ("🔬", "Wyckoff springs & upthrsts"),
            ("⬜", "ICT Fair Value Gaps & OTE zones"),
            ("⚖️", "Fresh supply & demand zones"),
            ("💥", "Breakout & retest patterns"),
            ("📈", "EMA stack pullback entries"),
            ("Δ",  "Order flow delta & absorption"),
        ]:
            st.markdown(
                f"<div class='pillar-row'>"
                f"<span class='pillar-icon'>{item[0]}</span>"
                f"<span class='pillar-text'>{item[1]}</span>"
                f"</div>",
                unsafe_allow_html=True,
            )

    with sig_col2:
        st.markdown("<div class='panel-label'>⚡ Trade Signal Output</div>", unsafe_allow_html=True)

        if signal_button and st.session_state.signal_image_bytes and api_key:
            st.session_state.signal_report = None
            st.session_state.debate_log = []
            st.session_state.debate_final = None
            hint_text = (
                f" Focus particularly on {sig_hint} patterns."
                if sig_hint != "Auto-detect best setup" else ""
            )
            # Build TF instruction
            tf_map = {
                "Auto (AI decides)":    "",
                "30M — Day Trade":      "30M",
                "15M — Intraday":       "15M",
                "5M — Precision Entry": "5M",
                "1M — Scalp":          "1M",
            }
            chosen_tf = tf_map.get(sig_tf_pref, "")
            tf_instruction = (
                f"\n\nTRADER TF OVERRIDE: The trader has explicitly requested the execution timeframe "
                f"be {chosen_tf}. Calibrate the entry trigger, stop loss distance, and TP targets "
                f"specifically for the {chosen_tf} chart. If {chosen_tf} is unsuitable for this setup "
                f"(e.g. not enough structure visible), state this in the Timeframe Rationale section "
                f"and recommend the next closest preferred TF (30M > 15M > 5M > 1M)."
                if chosen_tf else ""
            )
            with st.spinner("🧠 Scanning chart for highest-probability setup... 15–30 seconds."):
                from strategies import SIGNAL_SYSTEM_INSTRUCTION as _SYS
                patched_sys = _SYS + (
                    f"\n\nUSER HINT: The user suspects a {sig_hint} setup. "
                    f"Give it priority if it is clearly present, but still pick the best setup overall."
                    if sig_hint != "Auto-detect best setup" else ""
                ) + tf_instruction
                try:
                    client = genai.Client(api_key=api_key)
                    image_part = types.Part.from_bytes(
                        data=st.session_state.signal_image_bytes, mime_type="image/png"
                    )
                    prompt = (
                        "Scan this trading chart and generate the single best, "
                        "highest-probability trade signal you can identify." + hint_text
                        + "\n\n" + SIGNAL_OUTPUT_TEMPLATE
                    )
                    resp = client.models.generate_content(
                        model=selected_model,
                        contents=[image_part, prompt],
                        config=types.GenerateContentConfig(
                            system_instruction=patched_sys,
                            temperature=0.15,
                        ),
                    )
                    st.session_state.signal_report = resp.text
                except Exception as e:
                    st.session_state.signal_report = f"❌ **Gemini API Error:** {e}"

        if st.session_state.signal_report:
            sig_report = st.session_state.signal_report
            sig_upper = sig_report.upper()

            # Direction badge
            if "NOT RECOMMENDED" in sig_upper or "⛔" in sig_report:
                st.markdown("<div class='verdict-not-tradable'>⛔ NO SIGNAL — NOT RECOMMENDED</div>",
                            unsafe_allow_html=True)
            elif "🔴 SHORT" in sig_report or "| 🔴" in sig_report:
                st.markdown("<div class='verdict-not-tradable'>🔴 SHORT SIGNAL</div>",
                            unsafe_allow_html=True)
            elif "🟢 LONG" in sig_report or "| 🟢" in sig_report:
                st.markdown("<div class='verdict-tradable'>🟢 LONG SIGNAL</div>",
                            unsafe_allow_html=True)

            st.markdown(f"<div class='report-box'>{sig_report}</div>", unsafe_allow_html=True)
            st.download_button(
                label="⬇️ Download Signal (.md)",
                data=sig_report.encode("utf-8"),
                file_name="trade_signal.md",
                mime="text/markdown",
                key="download_signal",
            )
            
            # --- AI Debate Section ---
            st.markdown("<div style='margin-top:2rem;'></div>", unsafe_allow_html=True)
            st.markdown(
                "<div style='background:linear-gradient(135deg,#2a1f0d,#0d1117);border:1px solid #d29922;"
                "border-left:4px solid #e3b341;border-radius:8px;padding:1rem 1.25rem;margin-bottom:1rem;'>"
                "<p style='color:#e3b341;font-weight:700;font-size:1rem;margin:0;'>🥊 Stress-Test Setup (AI Debate)</p>"
                "<p style='color:#8b949e;font-size:0.83rem;margin:0.4rem 0 0;'>"
                "Have a second Gemini instance (Devil's Advocate) critique this signal to find flaws "
                "the first model missed. If flaws are found, a final consensus signal will be synthesized."
                "</p></div>",
                unsafe_allow_html=True,
            )
            
            debate_button = st.button("🥊 Run AI Debate", key="debate_btn")
            
            if debate_button:
                st.session_state.debate_log = []
                st.session_state.debate_final = None
                with st.status("🥊 Running AI Signal Debate...", expanded=True) as status:
                    try:
                        st.write("🧠 Challenger (Devil's Advocate) analyzing chart...")
                        debate_results = run_signal_debate(
                            image_bytes=st.session_state.signal_image_bytes,
                            initial_signal=st.session_state.signal_report,
                            api_key=api_key,
                        )
                        st.session_state.debate_log = debate_results["debate_log"]
                        st.session_state.debate_final = debate_results["final_signal"]
                        if debate_results["consensus"]:
                            status.update(label="✅ Consensus Reached! (Signal Flawless)", state="complete")
                        else:
                            status.update(label="⚖️ Arbitration Complete (Signal Optimized)", state="complete")
                    except Exception as e:
                        status.update(label=f"❌ Debate failed: {e}", state="error")
            
            if st.session_state.debate_log:
                st.markdown("<div class='panel-label' style='margin-top:1.5rem;'>🥊 Debate Timeline</div>", unsafe_allow_html=True)
                for entry in st.session_state.debate_log:
                    if entry["role"] == "Challenger":
                        st.markdown(
                            f"<div style='background:#1a150d;border:1px solid #3d2f1a;border-radius:8px;padding:1rem;margin-bottom:1rem;'>"
                            f"<div style='color:#e3b341;font-weight:700;margin-bottom:0.5rem;'>⚡ Challenger Critique (Round {entry['round']} - {entry['model']})</div>"
                            f"<div style='font-size:0.9rem;'>{entry['content']}</div>"
                            f"</div>",
                            unsafe_allow_html=True
                        )
                
                if st.session_state.debate_final:
                    st.markdown("<div class='panel-label' style='margin-top:1.5rem;'>🏆 Final Optimized Signal</div>", unsafe_allow_html=True)
                    st.markdown(f"<div class='report-box'>{st.session_state.debate_final}</div>", unsafe_allow_html=True)
                    
                    st.download_button(
                        label="⬇️ Download Consensus Signal (.md)",
                        data=st.session_state.debate_final.encode("utf-8"),
                        file_name="trade_signal_consensus.md",
                        mime="text/markdown",
                        key="download_consensus_signal",
                    )
        elif signal_button and not api_key:
            st.error("🔑 Please configure your Gemini API key in the sidebar.")
        elif signal_button and not st.session_state.signal_image_bytes:
            st.warning("📤 Please load a chart image first.")
        else:
            st.markdown(
                "<div class='placeholder-box' style='min-height:500px;'>"
                "<div class='placeholder-icon'>⚡</div>"
                "<div class='placeholder-text'>"
                "<strong style='color:#484f58;'>No signal generated yet</strong><br><br>"
                "The AI will output a <strong style='color:#3fb950;'>complete trade signal</strong> with:<br><br>"
                "<span style='color:#3fb950;'>📍 Entry Zone</span> &nbsp;·&nbsp; "
                "<span style='color:#f85149;'>🛑 Stop Loss</span><br>"
                "<span style='color:#58a6ff;'>🎯 TP1 · TP2 · TP3</span> &nbsp;·&nbsp; "
                "<span style='color:#e3b341;'>📊 R:R Ratio</span><br><br>"
                "<span style='color:#8b949e;font-size:0.85rem;'>Confluence Score · Invalidation Conditions · Execution Notes</span>"
                "</div></div>",
                unsafe_allow_html=True,
            )



# ════════════════════════════════════════════
#  TAB 3 — Trade Feedback / Post-Mortem
# ════════════════════════════════════════════
with tab_feedback:
    st.markdown(
        "<div style='background:linear-gradient(135deg,#1f0d0d,#0d1117);border:1px solid #f85149;"
        "border-left:4px solid #f85149;border-radius:8px;padding:1rem 1.25rem;margin-bottom:1.5rem;'>"
        "<p style='color:#f85149;font-weight:700;font-size:1rem;margin:0;'>📝 Trade Post-Mortem Analyzer</p>"
        "<p style='color:#8b949e;font-size:0.83rem;margin:0.4rem 0 0;'>"
        "Took a loss? Submit your chart and trade details — the AI diagnoses exactly what went wrong, "
        "identifies warning signs you missed, gives you the corrected setup, and builds 3 rules "
        "to add to your checklist so you never repeat the same mistake."
        "</p></div>",
        unsafe_allow_html=True,
    )

    fb_col1, fb_col2 = st.columns([1, 1], gap="large")

    with fb_col1:
        # ── Chart Uploads ──────────────────────
        st.markdown("<div class='panel-label'>📥 Chart Upload</div>", unsafe_allow_html=True)

        fb_setup_file = st.file_uploader(
            "📈 Original Setup Chart (required)",
            type=["png", "jpg", "jpeg", "webp", "bmp"],
            key="fb_setup_file",
            help="Upload the chart you were looking at when you took the trade.",
        )
        fb_outcome_file = st.file_uploader(
            "📉 Post-Trade / Outcome Chart (optional)",
            type=["png", "jpg", "jpeg", "webp", "bmp"],
            key="fb_outcome_file",
            help="Upload a chart showing what actually happened after your entry.",
        )

        if fb_setup_file:
            try:
                setup_pil = __import__("PIL").Image.open(fb_setup_file)
                st.image(setup_pil, use_container_width=True, caption="Setup Chart")
            except Exception:
                pass
        if fb_outcome_file:
            try:
                outcome_pil = __import__("PIL").Image.open(fb_outcome_file)
                st.image(outcome_pil, use_container_width=True, caption="Outcome Chart")
            except Exception:
                pass

        st.markdown("<div style='margin-top:1.2rem;'></div>", unsafe_allow_html=True)

        # ── Trade Details Form ─────────────────
        st.markdown("<div class='panel-label'>📋 Trade Details</div>", unsafe_allow_html=True)

        fb_strategy = st.selectbox(
            "Strategy Used",
            options=STRATEGY_NAMES + ["Other / Mixed"],
            key="fb_strategy",
        )
        fb_direction = st.radio(
            "Trade Direction",
            options=["🟢 Long (Buy)", "🔴 Short (Sell)"],
            key="fb_direction", horizontal=True,
        )

        fb_c1, fb_c2 = st.columns(2)
        with fb_c1:
            fb_entry = st.text_input("Entry Price", placeholder="e.g. 64,250", key="fb_entry")
            fb_sl    = st.text_input("Stop Loss",   placeholder="e.g. 63,800", key="fb_sl")
            fb_tp    = st.text_input("Take Profit", placeholder="e.g. 65,500", key="fb_tp")
        with fb_c2:
            fb_exit  = st.text_input("Actual Exit Price", placeholder="e.g. 63,800", key="fb_exit")
            fb_result = st.selectbox(
                "Result",
                options=["❌ Stop Loss Hit", "✅ Take Profit Hit", "⚠️ Breakeven", "🔄 Manually Closed"],
                key="fb_result",
            )
            fb_pnl = st.text_input("P&L (optional)", placeholder="e.g. -$120 or -2R", key="fb_pnl")

        fb_description = st.text_area(
            "What happened? (your own words)",
            placeholder=(
                "e.g. 'I entered on what looked like a trendline bounce but price broke through "
                "immediately after. I thought the 4H was bullish but hadn't checked the daily...'"
            ),
            height=120,
            key="fb_description",
        )

        st.markdown("<div style='margin-top:1rem;'></div>", unsafe_allow_html=True)
        feedback_button = st.button(
            "🔬 Run Post-Mortem Analysis",
            key="feedback_btn",
            disabled=not (fb_setup_file and api_key),
        )
        if not fb_setup_file:
            st.caption("⬆️ Upload your setup chart to run the post-mortem.")
        elif not api_key:
            st.caption("🔑 Configure your API key in the sidebar.")

    # ── Output Column ──────────────────────────
    with fb_col2:
        st.markdown("<div class='panel-label'>🔬 Post-Mortem Report</div>", unsafe_allow_html=True)

        if feedback_button and fb_setup_file and api_key:
            st.session_state.feedback_report = None

            # Build structured trade context
            trade_context = (
                f"TRADE DETAILS SUBMITTED BY TRADER:\n"
                f"- Strategy Used: {fb_strategy}\n"
                f"- Direction: {fb_direction}\n"
                f"- Entry Price: {fb_entry or 'Not provided'}\n"
                f"- Stop Loss: {fb_sl or 'Not provided'}\n"
                f"- Take Profit: {fb_tp or 'Not provided'}\n"
                f"- Actual Exit Price: {fb_exit or 'Not provided'}\n"
                f"- Result: {fb_result}\n"
                f"- P&L: {fb_pnl or 'Not provided'}\n"
                f"- Trader's Description: {fb_description or 'Not provided'}\n\n"
                f"Please perform a thorough post-mortem analysis of this trade.\n\n"
                + FEEDBACK_OUTPUT_TEMPLATE
            )

            with st.spinner("🧠 Analyzing your trade... Diagnosing what went wrong..."):
                try:
                    client = genai.Client(api_key=api_key)

                    # Build image parts — always include setup, optionally outcome
                    fb_setup_file.seek(0)
                    setup_bytes = fb_setup_file.read()
                    contents = [
                        types.Part.from_bytes(data=setup_bytes, mime_type="image/png"),
                    ]
                    if fb_outcome_file:
                        fb_outcome_file.seek(0)
                        outcome_bytes = fb_outcome_file.read()
                        contents.append(
                            types.Part.from_bytes(data=outcome_bytes, mime_type="image/png")
                        )
                    contents.append(trade_context)

                    resp = client.models.generate_content(
                        model=selected_model,
                        contents=contents,
                        config=types.GenerateContentConfig(
                            system_instruction=FEEDBACK_SYSTEM_INSTRUCTION,
                            temperature=0.1,
                        ),
                    )
                    st.session_state.feedback_report = resp.text
                except Exception as e:
                    st.session_state.feedback_report = f"❌ **Gemini API Error:** {e}"

        if st.session_state.feedback_report:
            fb_report = st.session_state.feedback_report
            fb_upper = fb_report.upper()

            # Root cause badge
            tag_colors = {
                "PREMATURE_ENTRY":  ("#e3b341", "#3d2f1a"),
                "SL_TOO_TIGHT":     ("#e3b341", "#3d2f1a"),
                "COUNTER_TREND":    ("#f85149", "#3d1a1a"),
                "NO_CONFLUENCE":    ("#f85149", "#3d1a1a"),
                "WRONG_ZONE":       ("#f85149", "#3d1a1a"),
                "CHASED_ENTRY":     ("#e3b341", "#3d2f1a"),
                "POOR_RR":          ("#e3b341", "#3d2f1a"),
                "NEWS_EVENT":       ("#8b949e", "#21262d"),
                "FAKEOUT":          ("#8b949e", "#21262d"),
                "EMOTIONAL_TRADE":  ("#f85149", "#3d1a1a"),
                "VALID_LOSS":       ("#3fb950", "#1a3d1f"),
            }
            for tag, (fg, bg) in tag_colors.items():
                if tag in fb_upper:
                    st.markdown(
                        f"<div style='display:inline-block;background:{bg};border:1px solid {fg};"
                        f"color:{fg};padding:0.35rem 1rem;border-radius:20px;font-weight:700;"
                        f"font-size:0.9rem;margin-bottom:1rem;letter-spacing:1px;'>"
                        f"🏷️ {tag.replace('_', ' ')}</div>",
                        unsafe_allow_html=True,
                    )
                    break

            st.markdown(f"<div class='report-box'>{fb_report}</div>", unsafe_allow_html=True)
            st.download_button(
                label="⬇️ Download Post-Mortem (.md)",
                data=fb_report.encode("utf-8"),
                file_name="trade_post_mortem.md",
                mime="text/markdown",
                key="download_feedback",
            )
        elif feedback_button and not api_key:
            st.error("🔑 Please configure your Gemini API key in the sidebar.")
        elif feedback_button and not fb_setup_file:
            st.warning("📤 Please upload your setup chart first.")
        else:
            st.markdown(
                "<div class='placeholder-box' style='min-height:550px;'>"
                "<div class='placeholder-icon'>🔬</div>"
                "<div class='placeholder-text'>"
                "<strong style='color:#484f58;'>Post-mortem report will appear here</strong><br><br>"
                "<span style='color:#f85149;'>🏷️ Root Cause Tag</span><br>"
                "<span style='color:#8b949e;font-size:0.85rem;'>e.g. PREMATURE_ENTRY · SL_TOO_TIGHT · COUNTER_TREND</span>"
                "<br><br>"
                "<span style='color:#58a6ff;'>🔍 Chart Warning Signs</span> &nbsp;·&nbsp; "
                "<span style='color:#3fb950;'>✅ Corrected Setup</span><br>"
                "<span style='color:#e3b341;'>📚 3 Checklist Rules</span> &nbsp;·&nbsp; "
                "<span style='color:#8b949e;'>🧠 Mental Assessment</span><br><br>"
                "<span style='color:#484f58;font-size:0.82rem;'>"
                "Upload your setup chart + fill in trade details,<br>then click 🔬 Run Post-Mortem Analysis"
                "</span>"
                "</div></div>",
                unsafe_allow_html=True,
            )


# ════════════════════════════════════════════
#  TAB 4 — Coin Scanner
# ════════════════════════════════════════════
with tab_scanner:
    st.markdown(
        "<div style='background:linear-gradient(135deg,#0a1628,#0d1117);border:1px solid #1f6feb;"
        "border-left:4px solid #58a6ff;border-radius:8px;padding:1rem 1.25rem;margin-bottom:1.5rem;'>"
        "<p style='color:#58a6ff;font-weight:700;font-size:1rem;margin:0;'>🔎 MEXC Mid-Cap Coin Scanner</p>"
        "<p style='color:#8b949e;font-size:0.83rem;margin:0.4rem 0 0;'>"
        "Scans MEXC live market data in real-time to find mid-cap USDT pairs with strong volume and trend momentum. "
        "Each coin is scored and matched to the strategy it is best suited for."
        "</p></div>",
        unsafe_allow_html=True,
    )

    # ── Scan Controls ──────────────────────────────────────────────────
    sc_col_a, sc_col_b, sc_col_c, sc_col_d = st.columns([1.2, 1.2, 1, 0.8])
    with sc_col_a:
        sc_min_vol = st.select_slider(
            "Min 24h Volume (USDT)",
            options=[500_000, 1_000_000, 2_000_000, 5_000_000, 10_000_000],
            value=2_000_000,
            format_func=lambda x: f"${x/1_000_000:.1f}M",
            key="sc_min_vol",
        )
    with sc_col_b:
        sc_max_vol = st.select_slider(
            "Max 24h Volume (USDT)",
            options=[20_000_000, 50_000_000, 100_000_000, 150_000_000, 300_000_000],
            value=150_000_000,
            format_func=lambda x: f"${x/1_000_000:.0f}M",
            key="sc_max_vol",
        )
    with sc_col_c:
        sc_min_chg = st.select_slider(
            "Min 24h Move",
            options=[1.0, 2.0, 3.0, 5.0, 8.0],
            value=2.0,
            format_func=lambda x: f"{x:.0f}%",
            key="sc_min_chg",
        )
    with sc_col_d:
        sc_direction = st.selectbox(
            "Direction",
            options=["Both", "Bullish", "Bearish"],
            key="sc_direction",
        )

    scan_btn = st.button("🔎 Scan MEXC Now", key="scan_btn", use_container_width=False)

    if "scan_results" not in st.session_state:
        st.session_state.scan_results = None
    if "scan_error" not in st.session_state:
        st.session_state.scan_error = None

    if scan_btn:
        st.session_state.scan_results = None
        st.session_state.scan_error = None
        with st.spinner("📡 Fetching live MEXC market data..."):
            try:
                coins = get_top_midcap_coins(
                    min_vol_usdt=sc_min_vol,
                    max_vol_usdt=sc_max_vol,
                    min_change_pct=sc_min_chg,
                    direction=sc_direction,
                    top_n=10,
                )
                st.session_state.scan_results = coins
            except Exception as e:
                st.session_state.scan_error = str(e)

    if st.session_state.scan_error:
        st.error(f"❌ {st.session_state.scan_error}")

    elif st.session_state.scan_results:
        coins = st.session_state.scan_results
        st.markdown(
            f"<div class='chip-row'>"
            f"<div class='chip chip-blue'>📡 Live MEXC Data</div>"
            f"<div class='chip chip-green'>✅ {len(coins)} Coins Found</div>"
            f"<div class='chip'>💰 Vol ${sc_min_vol/1e6:.1f}M–${sc_max_vol/1e6:.0f}M</div>"
            f"<div class='chip'>📈 ≥{sc_min_chg:.0f}% Move</div>"
            f"<div class='chip'>{sc_direction}</div>"
            f"</div>",
            unsafe_allow_html=True,
        )

        for i, coin in enumerate(coins, 1):
            chg    = coin["change_pct"]
            chg_color = "#3fb950" if chg >= 0 else "#f85149"
            chg_arrow = "▲" if chg >= 0 else "▼"
            vol_m  = coin["quote_volume"] / 1_000_000
            score  = coin["score"]
            score_color = "#3fb950" if score >= 60 else "#e3b341" if score >= 40 else "#f85149"
            strats = coin["strategies"]
            mom    = coin["momentum"].upper()
            vola   = coin["volatility"].upper()

            strat_chips = " ".join(
                [f"<span style='background:#0c2a4a;border:1px solid #1f6feb;color:#58a6ff;"
                 f"border-radius:12px;padding:0.15rem 0.6rem;font-size:0.72rem;"
                 f"font-family:JetBrains Mono,monospace;'>{s}</span>"
                 for s in strats]
            )

            st.markdown(
                f"<div style='background:#161b22;border:1px solid #21262d;border-left:3px solid {score_color};"
                f"border-radius:8px;padding:0.9rem 1.1rem;margin-bottom:0.7rem;'>"
                f"<div style='display:flex;justify-content:space-between;align-items:flex-start;'>"
                # Left: rank + symbol + price
                f"<div>"
                f"<span style='color:#484f58;font-size:0.75rem;font-family:JetBrains Mono,monospace;'>#{i:02d}</span>&nbsp;"
                f"<span style='color:#c9d1d9;font-weight:700;font-size:1.05rem;font-family:JetBrains Mono,monospace;'>{coin['base']}/USDT</span>&nbsp;"
                f"<span style='color:#8b949e;font-size:0.82rem;'>${coin['price']:,.6g}</span>"
                f"<br>"
                f"<span style='font-size:0.75rem;margin-top:0.3rem;display:inline-block;'>"
                f"📊 Vol: <strong style='color:#c9d1d9;'>${vol_m:.2f}M</strong>&nbsp;&nbsp;"
                f"Momentum: <span style='color:#e3b341;'>{mom}</span>&nbsp;&nbsp;"
                f"Volatility: <span style='color:#8b949e;'>{vola}</span>"
                f"</span>"
                f"</div>"
                # Right: change + score
                f"<div style='text-align:right;'>"
                f"<span style='color:{chg_color};font-weight:700;font-size:1.1rem;'>{chg_arrow} {abs(chg):.2f}%</span><br>"
                f"<span style='background:{score_color}22;border:1px solid {score_color};color:{score_color};"
                f"border-radius:12px;padding:0.1rem 0.6rem;font-size:0.78rem;font-weight:700;'>"
                f"Score {score:.0f}/100</span>"
                f"</div></div>"
                # Strategy chips
                f"<div style='margin-top:0.6rem;display:flex;flex-wrap:wrap;gap:0.4rem;align-items:center;'>"
                f"<span style='color:#484f58;font-size:0.72rem;'>Best for:</span> {strat_chips}"
                f"</div></div>",
                unsafe_allow_html=True,
            )

        # MEXC link helper
        st.markdown(
            "<div style='margin-top:1rem;padding:0.7rem 1rem;background:#0d1117;"
            "border:1px solid #21262d;border-radius:6px;font-size:0.78rem;color:#484f58;'>"
            "💡 <strong style='color:#8b949e;'>Tip:</strong> Click a coin's symbol above to search it on "
            "<a href='https://www.mexc.com/exchange/' target='_blank' "
            "style='color:#58a6ff;text-decoration:none;'>MEXC Exchange</a>. "
            "Then take a screenshot of the TradingView chart and run it through the "
            "<strong style='color:#58a6ff;'>Strategy Audit</strong> or "
            "<strong style='color:#3fb950;'>Signal Generator</strong> tab."
            "</div>",
            unsafe_allow_html=True,
        )

    else:
        st.markdown(
            "<div class='placeholder-box' style='min-height:400px;'>"
            "<div class='placeholder-icon'>📡</div>"
            "<div class='placeholder-text'>"
            "<strong style='color:#484f58;'>No scan run yet</strong><br><br>"
            "Set your filters above and click "
            "<strong style='color:#58a6ff;'>🔎 Scan MEXC Now</strong><br><br>"
            "<span style='color:#8b949e;font-size:0.85rem;'>"
            "Scans live MEXC market data · Filters mid-cap USDT pairs<br>"
            "Scores by volume, momentum & range quality<br>"
            "Matches each coin to your best-fit strategy"
            "</span>"
            "</div></div>",
            unsafe_allow_html=True,
        )


# ── Footer ────────────────────────────────────

st.markdown("<div style='margin-top:3rem;'></div>", unsafe_allow_html=True)
st.markdown(
    "<hr style='border-color:#21262d;'>"
    "<p style='text-align:center;color:#484f58;font-size:0.78rem;margin-top:0.8rem;'>"
    "AI Trading Auditor v4.0 · 8 Strategies · Signal Generator · Trade Post-Mortem · MEXC Coin Scanner · Powered by Google Gemini AI · "
    "For educational purposes only. Not financial advice."
    "</p>",
    unsafe_allow_html=True,
)



