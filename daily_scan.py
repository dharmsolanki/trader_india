import json
import time

from auth import fetch_candles
from market_hours import CLOSE, is_trading_day, now_ist

MIN_BARS = 30


def load_token():
    with open("token.json") as f:
        return json.load(f)["access_token"]


def rsi(closes, n=14):
    if len(closes) < n + 1:
        return None
    g = [max(0.0, closes[i] - closes[i - 1]) for i in range(1, len(closes))]
    lo = [max(0.0, closes[i - 1] - closes[i]) for i in range(1, len(closes))]
    ag, al = sum(g[:n]) / n, sum(lo[:n]) / n
    for i in range(n, len(g)):
        ag = (ag * (n - 1) + g[i]) / n
        al = (al * (n - 1) + lo[i]) / n
    return 100 - 100 / (1 + ag / al) if al else 100.0


def find_setups(c):
    last = c[-1]
    hi20 = max(c[-21:-1])
    ma20 = sum(c[-20:]) / 20.0
    ma20_prev = sum(c[-21:-1]) / 20.0
    run = c[-6] / c[-16] - 1
    rng5 = (max(c[-5:]) - min(c[-5:])) / last
    r, r_prev = rsi(c), rsi(c[:-1])
    tags = []
    if last > hi20:
        tags.append("breakout_20d")
    if run > 0.10 and rng5 < 0.05:
        tags.append("bull_flag")
    if c[-2] < ma20_prev and last > ma20:
        tags.append("reclaim_ma20")
    if r is not None and r < 30:
        tags.append("oversold")
    if r_prev is not None and r_prev < 30 and last > c[-2]:
        tags.append("oversold_bounce")
    return tags, r


def complete_closes(candles):
    """Newest-first candles -> (dates, closes) oldest-first, aaj ka adhoora bar hata ke."""
    rows = sorted((c[0][:10], float(c[4])) for c in candles if c[4] is not None)
    now = now_ist()
    today = now.date().isoformat()
    if rows and rows[-1][0] == today and is_trading_day(now.date()) \
            and now.time() < CLOSE:
        rows = rows[:-1]
    return [r[0] for r in rows], [r[1] for r in rows]


INDEX_KEY = "NSE_INDEX|Nifty 50"
RS_MIN = 0.05                      # stock ko Nifty se kam se kam 5 points aage hona chahiye
SKIP_WORDS = ("ETF", "BEES", "LIQUID")


def ten_day_run(c):
    return c[-6] / c[-16] - 1


if __name__ == "__main__":
    tok = load_token()

    r = fetch_candles(tok, INDEX_KEY, days=75)
    if r.status_code != 200:
        raise SystemExit(f"Index candles fail {r.status_code}: {r.text[:300]}")
    _, idx_closes = complete_closes(r.json()["data"]["candles"])
    idx_run = ten_day_run(idx_closes)
    print(f"Nifty 50: 10-session run {idx_run*100:.1f}%, last close {idx_closes[-1]}")

    with open("universe.json", encoding="utf-8") as f:
        names = {u["key"]: u["name"] for u in json.load(f)}
    with open("liquid.json", encoding="utf-8") as f:
        stocks = json.load(f)

    skipped = 0
    hits, short, failed = [], 0, []
    for i, s in enumerate(stocks, 1):
        label = (s["symbol"] + " " + (names.get(s["key"]) or "")).upper()
        if any(w in label for w in SKIP_WORDS):
            skipped += 1
            continue
        r = fetch_candles(tok, s["key"], days=75)
        if r.status_code == 429:
            time.sleep(5)
            r = fetch_candles(tok, s["key"], days=75)
        if r.status_code != 200:
            failed.append((s["symbol"], r.status_code))
            continue
        dates, closes = complete_closes(r.json()["data"]["candles"])
        if len(closes) < MIN_BARS:
            short += 1
            continue
        tags, rs = find_setups(closes)
        rel = ten_day_run(closes) - idx_run
        if rel < RS_MIN:
            tags = [t for t in tags if t not in ("breakout_20d", "bull_flag")]
        if tags:
            hits.append({"symbol": s["symbol"], "key": s["key"],
                         "setups": tags, "close": round(closes[-1], 2),
                         "close_date": dates[-1],
                         "rsi": round(rs, 1) if rs is not None else None,
                         "rs_pts": round(rel * 100, 1),
                         "turnover_cr": s["turnover_cr"]})
        if i % 50 == 0:
            print(f"  {i}/{len(stocks)} done")
        time.sleep(0.25)

    hits.sort(key=lambda h: -h["rs_pts"])
    with open("watchlist.json", "w", encoding="utf-8") as f:
        json.dump(hits, f, ensure_ascii=False, indent=1)

    print(f"\nHits: {len(hits)} | ETF skip: {skipped} | kam history: {short} | fail: {len(failed)}")
    for tag in ["breakout_20d", "bull_flag", "reclaim_ma20",
                "oversold", "oversold_bounce"]:
        rows = [h for h in hits if tag in h["setups"]]
        print(f"\n{tag} ({len(rows)}):")
        for h in rows[:10]:
            print(f"  {h['symbol']:<12} close {h['close']:>9}  RS {h['rs_pts']:>6}  RSI {h['rsi']}")