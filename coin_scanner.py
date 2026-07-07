"""
coin_scanner.py — MEXC Mid-Cap Coin Scanner
Fetches live ticker data from MEXC public API and identifies
trending mid-cap coins suitable for the 8 trading strategies.
"""

import requests

# ── MEXC Public API ────────────────────────────────────────────────────────────
MEXC_TICKER_URL  = "https://api.mexc.com/api/v3/ticker/24hr"
MEXC_KLINE_URL   = "https://api.mexc.com/api/v3/klines"
MEXC_BASE        = "https://api.mexc.com"

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json",
}

# ── Exclusion Lists ────────────────────────────────────────────────────────────
MEGA_CAPS = {
    "BTC", "ETH", "BNB", "SOL", "XRP", "ADA", "AVAX", "DOT",
    "MATIC", "LINK", "TRX", "DOGE", "SHIB", "LTC", "UNI", "ATOM",
    "ICP", "FIL", "APT", "ARB", "OP", "SUI", "TON", "NEAR",
    "HBAR", "VET", "ALGO", "MANA", "SAND", "AXS", "GALA",
    "WXT",  # exchange token, not a tradable mid-cap
}

STABLECOINS = {
    "USDT", "USDC", "BUSD", "DAI", "TUSD", "USDP", "GUSD",
    "FRAX", "USDD", "FDUSD", "PYUSD", "LUSD", "SUSD",
}

# Non-crypto USDT pairs to skip (forex, commodities etc.)
EXCLUDE_SYMBOLS = {
    "EURUSDT", "GBPUSDT", "JPYUSDT", "XAUUSDT", "XAGUSDT",
    "BNBXUSDT", "WBTCUSDT",
}

# ── Scoring Weights ────────────────────────────────────────────────────────────
# Strategy → which characteristics it prefers
STRATEGY_FIT_RULES = {
    "SMC — 4-Pillar Audit":        {"min_vol": 3_000_000, "momentum": "any",  "volatility": "medium"},
    "Trendline Mastery":           {"min_vol": 2_000_000, "momentum": "high", "volatility": "medium"},
    "Wyckoff Method":              {"min_vol": 5_000_000, "momentum": "low",  "volatility": "low"},
    "ICT Concepts":                {"min_vol": 3_000_000, "momentum": "high", "volatility": "high"},
    "Supply & Demand Zones":       {"min_vol": 2_000_000, "momentum": "any",  "volatility": "medium"},
    "Breakout & Retest":           {"min_vol": 5_000_000, "momentum": "high", "volatility": "high"},
    "EMA Confluence Swing":        {"min_vol": 2_000_000, "momentum": "medium","volatility": "medium"},
    "Order Flow Analysis":         {"min_vol": 8_000_000, "momentum": "any",  "volatility": "any"},
}


def fetch_mexc_tickers() -> list[dict]:
    """Fetch all 24h ticker stats from MEXC public API."""
    try:
        resp = requests.get(MEXC_TICKER_URL, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.Timeout:
        raise ConnectionError("MEXC API request timed out. Try again.")
    except requests.exceptions.ConnectionError:
        raise ConnectionError("Cannot reach MEXC API. Check your internet connection.")
    except Exception as e:
        raise RuntimeError(f"MEXC API error: {e}")


def classify_volatility(change_pct: float) -> str:
    """Classify volatility based on 24h price change magnitude."""
    abs_chg = abs(change_pct)
    if abs_chg < 3:
        return "low"
    elif abs_chg < 8:
        return "medium"
    else:
        return "high"


def classify_momentum(change_pct: float) -> str:
    """Classify momentum level."""
    abs_chg = abs(change_pct)
    if abs_chg < 2:
        return "low"
    elif abs_chg < 6:
        return "medium"
    else:
        return "high"


def score_coin(coin: dict) -> float:
    """
    Score a coin 0-100 based on tradability.
    Weights: volume (40%), momentum (35%), consistency (25%)
    """
    vol   = coin["quote_volume"]
    chg   = abs(coin["change_pct"])
    high  = coin["high"]
    low   = coin["low"]
    price = coin["price"]

    # Volume score (log-scale, normalized around $5M sweet spot)
    import math
    vol_score = min(40, (math.log10(max(vol, 1)) - 6) * 20)  # peaks at ~$100M
    vol_score = max(0, vol_score)

    # Momentum score (2-15% is ideal — not too dead, not blow-off)
    if chg < 1:
        mom_score = 5
    elif chg < 3:
        mom_score = 15
    elif chg < 8:
        mom_score = 35
    elif chg < 15:
        mom_score = 25
    else:
        mom_score = 10  # blow-off top — riskier

    # Range consistency score (tight range = Wyckoff; wide = breakout)
    if price > 0 and low > 0:
        range_pct = (high - low) / low * 100
        if 3 <= range_pct <= 12:
            range_score = 25
        elif range_pct < 3:
            range_score = 10
        else:
            range_score = 15
    else:
        range_score = 10

    return round(vol_score + mom_score + range_score, 1)


def get_best_strategies(coin: dict) -> list[str]:
    """Return the top 3 strategy names that best fit this coin's characteristics."""
    vol       = coin["quote_volume"]
    momentum  = classify_momentum(coin["change_pct"])
    volatility = classify_volatility(coin["change_pct"])

    fits = []
    for strat, rules in STRATEGY_FIT_RULES.items():
        if vol < rules["min_vol"]:
            continue
        m_ok = rules["momentum"] in ("any", momentum)
        v_ok = rules["volatility"] in ("any", volatility)
        if m_ok and v_ok:
            fits.append(strat)

    # Always show at least top 2 by fallback
    if not fits:
        fits = ["SMC — 4-Pillar Audit", "Trendline Mastery"]

    # Return max 3
    return fits[:3]


def filter_and_score(
    tickers: list[dict],
    min_vol_usdt: float = 2_000_000,
    max_vol_usdt: float = 150_000_000,
    min_change_pct: float = 2.0,
    direction: str = "Both",   # "Bullish", "Bearish", "Both"
    top_n: int = 10,
) -> list[dict]:
    """
    Filter MEXC tickers to mid-cap trending coins and return scored list.
    """
    results = []

    for t in tickers:
        symbol = t.get("symbol", "")

        # Only USDT spot pairs, skip forex/commodity USDT pairs
        if not symbol.endswith("USDT"):
            continue
        if symbol in EXCLUDE_SYMBOLS:
            continue

        base = symbol.replace("USDT", "")

        # Exclude mega-caps and stablecoins
        if base in MEGA_CAPS or base in STABLECOINS:
            continue

        # Parse fields safely
        # NOTE: MEXC returns priceChangePercent as a decimal fraction (e.g. 0.0097 = 0.97%)
        try:
            quote_vol  = float(t.get("quoteVolume", 0) or 0)
            change_pct = float(t.get("priceChangePercent", 0) or 0) * 100  # convert to %
            price      = float(t.get("lastPrice", 0) or 0)
            high       = float(t.get("highPrice", 0) or 0)
            low        = float(t.get("lowPrice", 0) or 0)
            base_vol   = float(t.get("volume", 0) or 0)
        except (ValueError, TypeError):
            continue

        # Volume filter (mid-cap range)
        if not (min_vol_usdt <= quote_vol <= max_vol_usdt):
            continue

        # Minimum price movement (trending)
        if abs(change_pct) < min_change_pct:
            continue

        # Price sanity check
        if price <= 0:
            continue

        # Direction filter
        if direction == "Bullish" and change_pct < 0:
            continue
        if direction == "Bearish" and change_pct > 0:
            continue

        coin = {
            "symbol":      symbol,
            "base":        base,
            "price":       price,
            "change_pct":  change_pct,
            "quote_volume": quote_vol,
            "base_volume": base_vol,
            "high":        high,
            "low":         low,
            "momentum":    classify_momentum(change_pct),
            "volatility":  classify_volatility(change_pct),
        }
        coin["score"]      = score_coin(coin)
        coin["strategies"] = get_best_strategies(coin)
        results.append(coin)

    # Sort by score descending
    results.sort(key=lambda x: x["score"], reverse=True)
    return results[:top_n]


def get_top_midcap_coins(
    min_vol_usdt: float = 2_000_000,
    max_vol_usdt: float = 150_000_000,
    min_change_pct: float = 2.0,
    direction: str = "Both",
    top_n: int = 10,
) -> list[dict]:
    """Main entry point — fetches and filters in one call."""
    tickers = fetch_mexc_tickers()
    return filter_and_score(
        tickers,
        min_vol_usdt=min_vol_usdt,
        max_vol_usdt=max_vol_usdt,
        min_change_pct=min_change_pct,
        direction=direction,
        top_n=top_n,
    )
