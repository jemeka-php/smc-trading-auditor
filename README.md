# 📊 SMC Crypto Trading Auditor

An institutional-grade Smart Money Concepts (SMC) trading chart auditor powered by **Google Gemini Vision AI** and built with **Streamlit**.

---

## 🚀 Quick Setup (Local)

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Set Your Gemini API Key

Edit the `.env` file in the project root (created automatically):

```env
GEMINI_API_KEY=your_actual_api_key_here
```

> 🔑 Get a free key at [Google AI Studio](https://aistudio.google.com/app/apikey)

The app loads this file automatically on startup — you only need to paste your key **once**. The `.env` file is git-ignored so it never gets pushed to GitHub.

### 3. Launch the App

```bash
streamlit run app.py
```

Opens automatically at `http://localhost:8501`

---

## ☁️ Free Hosting Options

> ⚠️ **Vercel and Netlify are not compatible with Streamlit.** They only support static sites and serverless functions. Streamlit requires a persistent Python server.

### ✅ Option 1 — Streamlit Community Cloud (Recommended, 100% Free)

The official free hosting platform built specifically for Streamlit apps.

**Steps:**
1. Push your project to a **public or private GitHub repo**
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git remote add origin https://github.com/YOUR_USERNAME/smc-auditor.git
   git push -u origin main
   ```
2. Go to [share.streamlit.io](https://share.streamlit.io) and sign in with GitHub
3. Click **"New app"** → select your repo → set `app.py` as the main file
4. Go to **"Advanced settings" → "Secrets"** and add:
   ```toml
   GEMINI_API_KEY = "your_actual_api_key_here"
   ```
5. Click **Deploy** — live in ~60 seconds ✅

> The `.env` file stays local. On Streamlit Cloud, secrets are injected as environment variables via their secure UI.

---

### ✅ Option 2 — Railway (Free Tier Available)

Good for more control or private deployments.

**Steps:**
1. Push repo to GitHub (see step above)
2. Go to [railway.app](https://railway.app) → **New Project → Deploy from GitHub repo**
3. Select your repo
4. In the Railway dashboard → **Variables tab** → add:
   ```
   GEMINI_API_KEY = your_actual_api_key_here
   ```
5. In **Settings → Start Command**, set:
   ```
   streamlit run app.py --server.port $PORT --server.address 0.0.0.0
   ```
6. Deploy ✅

---

### ✅ Option 3 — Render (Free Tier Available)

1. Push repo to GitHub
2. Go to [render.com](https://render.com) → **New → Web Service**
3. Connect your repo
4. Set **Build Command**: `pip install -r requirements.txt`
5. Set **Start Command**: `streamlit run app.py --server.port $PORT --server.address 0.0.0.0 --server.headless true`
6. Go to **Environment** tab → add `GEMINI_API_KEY`
7. Deploy ✅

---

## 🧠 AI Audit Engine

Runs your chart through **4 SMC pillars**:

| Pillar | Description |
|--------|-------------|
| 🌊 Liquidity Sweep | Detects rejection wicks sweeping equal highs/lows |
| 📏 Premium/Discount + Fib | Zone classification (above/below 0.5) + exact Fib level (0.236–0.786) |
| 📊 Volume Profile | Checks POC/HVN confluence with the Order Block |
| 🎯 SL/TP Audit | Reviews Stop Loss and Take Profit vs channel structure |

**Verdict output:** `TRADABLE` / `NOT TRADABLE` / `NEEDS ADJUSTMENT`

---

## ⚙️ Configuration

| Setting | Value |
|---------|-------|
| Default Model | `gemini-2.5-flash` (Free Tier) |
| Pro Model | `gemini-2.5-pro` (Deep Reasoning) |
| Temperature | `0.1` (locked for clinical precision) |

---

## 📁 Project Structure

```
AI Trading Assistant/
├── app.py              # Main Streamlit application
├── requirements.txt    # Python dependencies
├── .env                # Your API key (local only, git-ignored)
├── .env.example        # Safe template to share/commit
├── .gitignore          # Excludes .env from git
└── README.md           # This file
```

---

## ⚠️ Disclaimer

This tool is for **educational purposes only** and does not constitute financial advice.
