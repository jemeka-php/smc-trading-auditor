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
from strategies import STRATEGIES, SIGNAL_SYSTEM_INSTRUCTION, SIGNAL_OUTPUT_TEMPLATE

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


def run_signal_generator(image_bytes: bytes, model_id: str, api_key: str) -> str:
    try:
        client = genai.Client(api_key=api_key)
        image_part = types.Part.from_bytes(data=image_bytes, mime_type="image/png")
        prompt = (
            "Scan this trading chart and generate the single best, highest-probability "
            "trade signal you can identify.\n\n" + SIGNAL_OUTPUT_TEMPLATE
        )
        response = client.models.generate_content(
            model=model_id,
            contents=[image_part, prompt],
            config=types.GenerateContentConfig(
                system_instruction=SIGNAL_SYSTEM_INSTRUCTION,
                temperature=0.15,
            ),
        )
        return response.text
    except Exception as e:
        err = str(e)
        if "API_KEY_INVALID" in err or "invalid" in err.lower():
            return "❌ **Invalid API Key.** Check your Gemini API key in the sidebar."
        elif "quota" in err.lower() or "429" in err:
            return "❌ **API Quota Exceeded.** Wait a moment and retry, or switch models."
        else:
            return f"❌ **Gemini API Error:** {err}"


# ── Session State Init ────────────────────────
for key, default in [
    ("image_bytes", None),
    ("audit_report", None),
    ("active_strategy", STRATEGY_NAMES[0]),
    ("signal_image_bytes", None),
    ("signal_report", None),
]:
    if key not in st.session_state:
        st.session_state[key] = default


# ── Sidebar ───────────────────────────────────
with st.sidebar:
    st.markdown(
        "<div style='text-align:center;margin-bottom:1.5rem;'>"
        "<span style='font-size:2rem;'>📊</span>"
        "<p style='color:#58a6ff;font-weight:700;font-size:1.1rem;margin:0.3rem 0 0;'>AI Trading Auditor</p>"
        "<p style='color:#484f58;font-size:0.75rem;margin:0;'>Multi-Strategy Risk Engine v2.0</p>"
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
tab_audit, tab_signal = st.tabs(["🔍 Strategy Audit", "⚡ Signal Generator"])


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
            hint_text = (
                f" Focus particularly on {sig_hint} patterns."
                if sig_hint != "Auto-detect best setup" else ""
            )
            with st.spinner("🧠 Scanning chart for highest-probability setup... 15–30 seconds."):
                # Temporarily patch prompt if hint given
                from strategies import SIGNAL_SYSTEM_INSTRUCTION as _SYS
                patched_sys = _SYS + (
                    f"\n\nUSER HINT: The user suspects a {sig_hint} setup. "
                    f"Give it priority if it is clearly present, but still pick the best setup overall."
                    if sig_hint != "Auto-detect best setup" else ""
                )
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


# ── Footer ────────────────────────────────────
st.markdown("<div style='margin-top:3rem;'></div>", unsafe_allow_html=True)
st.markdown(
    "<hr style='border-color:#21262d;'>"
    "<p style='text-align:center;color:#484f58;font-size:0.78rem;margin-top:0.8rem;'>"
    "AI Trading Auditor v2.0 · 8 Strategies + Signal Generator · Powered by Google Gemini AI · "
    "For educational purposes only. Not financial advice."
    "</p>",
    unsafe_allow_html=True,
)



