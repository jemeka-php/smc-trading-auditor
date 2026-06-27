"""
SMC Crypto Trading Auditor
Streamlit + Google Gemini Vision AI
"""

import os
import io
import requests
import streamlit as st
from PIL import Image
from google import genai
from google.genai import types
from dotenv import load_dotenv

# Load .env file automatically (works locally; on hosted platforms use their
# built-in env var UI instead — the file is git-ignored for safety)
load_dotenv()

# ── Page Config ──────────────────────────────
st.set_page_config(
    page_title="SMC Crypto Trading Auditor | AI Risk Engine",
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

.chip-row { display: flex; gap: 0.5rem; flex-wrap: wrap; margin-bottom: 1rem; }
.chip {
    background-color: #21262d; border: 1px solid #30363d; color: #8b949e;
    border-radius: 20px; padding: 0.2rem 0.75rem;
    font-size: 0.75rem; font-weight: 500; font-family: 'JetBrains Mono', monospace;
}
.chip-blue { border-color: #1f6feb; color: #58a6ff; background-color: #0c2a4a; }

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
SYSTEM_INSTRUCTION = (
    "You are an expert institutional Risk Manager and Smart Money Concepts (SMC) trading assistant. "
    "Your sole job is to audit the user's uploaded trading chart setup and deliver an uncompromising "
    "trading verdict based strictly on these rules:\n\n"
    "1. LIQUIDITY SWEEP: Look at the chart candlesticks. Did price aggressively sweep retail liquidity "
    "(equal highs/lows, trendline breaks, or channel boundaries) via a clear rejection wick before "
    "approaching the Order Block?\n\n"
    "2. PREMIUM/DISCOUNT & FIBONACCI ALIGNMENT: Identify the full impulse leg swing (significant low to "
    "high, or vice versa). Overlay the Fibonacci retracement grid across this leg, then evaluate in two steps:\n"
    "   a) ZONE CLASSIFICATION — Where does the OB sit relative to the 50% equilibrium level?\n"
    "      - DISCOUNT ZONE (below 0.5): Valid for bullish OBs. Strongest confluence at 0.618, 0.705, 0.786.\n"
    "      - PREMIUM ZONE (above 0.5): Valid for bearish OBs. Strongest confluence at 0.382, 0.236.\n"
    "      - AT EQUILIBRIUM (~0.5): Neutral. Requires stronger confirmation from other pillars.\n"
    "   b) FIB LEVEL PINPOINTING — Identify which exact level(s) the OB body overlaps from this set:\n"
    "      [0.236 | 0.382 | 0.5 Equilibrium | 0.618 Golden Pocket top | 0.65 | 0.705 Golden Pocket base | 0.786 Deep Discount]\n"
    "      The 0.618-0.705 Golden Pocket is the strongest institutional zone. 0.786 is valid but higher risk.\n"
    "   c) VERDICT: PASS if OB is in a contextually correct zone with Fib confluence. FAIL if OB is in the\n"
    "      wrong zone (e.g., bullish OB in Premium) or floats between levels with no Fib alignment.\n\n"
    "3. VOLUME PROFILE VALIDATION: Look at the Fixed Range Volume Profile (FRVP) overlay. The Point of "
    "Control (POC) or a prominent High Volume Node (HVN) mountain MUST align directly inside or tightly "
    "hug the labeled Order Block. If the OB sits in a Low Volume Node (LVN) valley, the setup is invalid.\n\n"
    "4. RISK/REWARD & TARGETS: The SL must be safely behind structural invalidation or the VAL/VAH edge. "
    "The TP should be slightly front-run before the opposite channel line or major opposing volume cluster."
)

OUTPUT_TEMPLATE = (
    "Format your entire response using this exact markdown template:\n\n"
    "## 🚨 VERDICT: [TRADABLE | NOT TRADABLE | NEEDS ADJUSTMENT]\n\n"
    "### 🔍 Pillar-by-Pillar Breakdown:\n"
    "* **Liquidity Sweep:** [State analysis of candlestick wicks]\n"
    "* **Premium/Discount & Fibonacci Alignment:**\n"
    "  * Zone: [DISCOUNT ZONE ↓ | PREMIUM ZONE ↑ | AT EQUILIBRIUM ~0.5] — [brief reason why]\n"
    "  * Fib Level(s): [e.g., OB body spans 0.618–0.705 (Golden Pocket) | OB at 0.786 (Deep Discount) | OB at 0.382 (Premium short zone)]\n"
    "  * Pillar Status: [✅ PASS | ❌ FAIL | ⚠️ MARGINAL] — [one-line verdict]\n"
    "* **Volume Profile Validation:** [Analyze the relationship between the OB, POC, HVN, and LVNs]\n"
    "* **Channel & Targets:** [Audit the SL/TP placement relative to channel boundaries]\n\n"
    "### 🛠️ Optimization & Adjustments:\n"
    "[Provide 2-3 specific spatial or structural improvements to maximize risk-to-reward ratio]"
)

MODELS = {
    "gemini-2.5-flash (Free Tier — Recommended)": "gemini-2.5-flash",
    "gemini-2.5-pro (Deep Reasoning)": "gemini-2.5-pro",
}

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
        st.error("❌ Request timed out. The server took too long to respond.")
    except requests.exceptions.ConnectionError:
        st.error("❌ Connection error. Check the URL and your internet connection.")
    except requests.exceptions.HTTPError as e:
        st.error(f"❌ HTTP Error {e.response.status_code}: {e.response.reason}")
    except Exception as e:
        st.error(f"❌ Unexpected error: {e}")
    return None


def run_audit(image_bytes: bytes, model_id: str, api_key: str) -> str:
    try:
        client = genai.Client(api_key=api_key)
        image_part = types.Part.from_bytes(data=image_bytes, mime_type="image/png")
        prompt = (
            "Please audit this trading chart using all four SMC pillars and deliver your verdict.\n\n"
            + OUTPUT_TEMPLATE
        )
        response = client.models.generate_content(
            model=model_id,
            contents=[image_part, prompt],
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_INSTRUCTION,
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


# ── Sidebar ───────────────────────────────────
with st.sidebar:
    st.markdown(
        "<div style='text-align:center;margin-bottom:1.5rem;'>"
        "<span style='font-size:2rem;'>📊</span>"
        "<p style='color:#58a6ff;font-weight:700;font-size:1.1rem;margin:0.3rem 0 0;'>SMC Auditor</p>"
        "<p style='color:#484f58;font-size:0.75rem;margin:0;'>AI Risk Engine v1.0</p>"
        "</div>",
        unsafe_allow_html=True,
    )
    st.markdown("---")
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
    st.markdown("**🤖 Model Selection**")
    model_label = st.selectbox("Inference Model", options=list(MODELS.keys()), index=0, key="model_selector")
    selected_model = MODELS[model_label]
    st.markdown(f"<div class='model-badge'>🧠 {selected_model}</div>", unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("**📐 SMC Audit Pillars**")
    for icon, label in [
        ("🌊", "Liquidity Sweep"),
        ("📏", "Premium/Discount + Fib Levels"),
        ("📊", "Volume Profile (POC/HVN)"),
        ("🎯", "SL/TP Channel Audit"),
    ]:
        st.markdown(
            f"<div style='display:flex;align-items:center;gap:0.6rem;"
            f"padding:0.4rem 0;border-bottom:1px solid #21262d;'>"
            f"<span>{icon}</span>"
            f"<span style='font-size:0.82rem;color:#8b949e;'>{label}</span>"
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
st.markdown(
    "<div class='title-banner'>"
    "<h1>📊 SMC Crypto Trading Auditor</h1>"
    "<p>Upload your TradingView chart · Get an institutional-grade risk verdict powered by Gemini AI</p>"
    "</div>",
    unsafe_allow_html=True,
)

api_key = get_api_key(sidebar_api_key if not env_key_present else "")
st.markdown(
    f"<div class='chip-row'>"
    f"<div class='chip chip-blue'>🧠 {selected_model}</div>"
    f"<div class='chip'>🌡️ temp=0.1</div>"
    f"<div class='chip'>{'🟢 API Key Active' if api_key else '🔴 API Key Missing'}</div>"
    f"<div class='chip'>📐 4-Pillar SMC Audit</div>"
    f"</div>",
    unsafe_allow_html=True,
)

if not api_key:
    st.warning(
        "⚠️ No API key detected. Set the `GEMINI_API_KEY` environment variable "
        "or enter your key in the sidebar.",
        icon="🔑",
    )

# Session state init
for key, default in [("image_bytes", None), ("audit_report", None)]:
    if key not in st.session_state:
        st.session_state[key] = default

col1, col2 = st.columns([1, 1], gap="large")

# ── Column 1: Input Panel ─────────────────────
with col1:
    st.markdown("<div class='panel-label'>📥 Chart Input Panel</div>", unsafe_allow_html=True)

    input_mode = st.radio(
        "Select input method:",
        options=["📎 Paste TradingView Link", "🖼️ Upload Image File"],
        key="input_mode", horizontal=True,
    )
    st.markdown("<div style='margin-top:1rem;'></div>", unsafe_allow_html=True)

    if input_mode == "📎 Paste TradingView Link":
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
            st.image(
                pil_img,
                use_container_width=True,
                caption=f"Resolution: {pil_img.width}×{pil_img.height}px | Mode: {pil_img.mode}",
            )
        except Exception as e:
            st.error(f"❌ Could not render preview: {e}")
    else:
        st.markdown(
            "<div class='placeholder-box' style='margin-top:1rem;min-height:250px;'>"
            "<div class='placeholder-icon'>🖼️</div>"
            "<div class='placeholder-text'>"
            "<strong style='color:#484f58;'>No chart loaded yet</strong><br>"
            "Paste a TradingView link or upload a screenshot above."
            "</div></div>",
            unsafe_allow_html=True,
        )

    st.markdown("<div style='margin-top:1.5rem;'></div>", unsafe_allow_html=True)
    audit_button = st.button(
        "🚀 Run SMC Audit",
        key="audit_btn",
        disabled=not (st.session_state.image_bytes and api_key),
    )
    if not st.session_state.image_bytes:
        st.caption("⬆️ Load a chart to enable the audit engine.")
    elif not api_key:
        st.caption("🔑 Configure your API key in the sidebar.")


# ── Column 2: AI Output ───────────────────────
with col2:
    st.markdown("<div class='panel-label'>🤖 AI Risk Audit Output</div>", unsafe_allow_html=True)

    if audit_button and st.session_state.image_bytes and api_key:
        st.session_state.audit_report = None
        with st.spinner("🧠 Analyzing chart with Gemini... This may take 15–30 seconds."):
            st.session_state.audit_report = run_audit(
                image_bytes=st.session_state.image_bytes,
                model_id=selected_model,
                api_key=api_key,
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
        st.download_button(
            label="⬇️ Download Audit Report (.md)",
            data=report.encode("utf-8"),
            file_name="smc_audit_report.md",
            mime="text/markdown",
            key="download_report",
        )
    elif audit_button and not api_key:
        st.error("🔑 Please configure your Gemini API key in the sidebar.")
    elif audit_button and not st.session_state.image_bytes:
        st.warning("📤 Please load a chart image first.")
    else:
        st.markdown(
            "<div class='placeholder-box' style='min-height:400px;'>"
            "<div class='placeholder-icon'>🛡️</div>"
            "<div class='placeholder-text'>"
            "<strong style='color:#484f58;'>Waiting for an image upload...</strong><br><br>"
            "Load a chart and press <strong style='color:#2ea043;'>🚀 Run SMC Audit</strong>"
            " to receive an institutional-grade verdict across<br><br>"
            "<span style='color:#3fb950;'>📊 Liquidity Sweep</span> &nbsp;·&nbsp; "
            "<span style='color:#58a6ff;'>📏 Premium/Discount + Fib</span><br>"
            "<span style='color:#e3b341;'>🌊 Volume Profile</span> &nbsp;·&nbsp; "
            "<span style='color:#f0883e;'>🎯 SL/TP Audit</span>"
            "</div></div>",
            unsafe_allow_html=True,
        )


# ── Footer ────────────────────────────────────
st.markdown("<div style='margin-top:3rem;'></div>", unsafe_allow_html=True)
st.markdown(
    "<hr style='border-color:#21262d;'>"
    "<p style='text-align:center;color:#484f58;font-size:0.78rem;margin-top:0.8rem;'>"
    "SMC Crypto Trading Auditor · Powered by Google Gemini AI · "
    "For educational purposes only. Not financial advice."
    "</p>",
    unsafe_allow_html=True,
)
