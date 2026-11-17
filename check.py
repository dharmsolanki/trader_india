import json

from auth import fetch_candles
from daily_scan import complete_closes, load_token

tok = load_token()
with open("liquid.json", encoding="utf-8") as f:
    stocks = json.load(f)

for sym in ["RELIANCE", "HDFCBANK", "ICICIBANK"]:
    s = next(x for x in stocks if x["symbol"] == sym)
    r = fetch_candles(tok, s["key"], days=75)
    d, c = complete_closes(r.json()["data"]["candles"])
    run = c[-6] / c[-16] - 1
    rng5 = (max(c[-5:]) - min(c[-5:])) / c[-1]
    print(f"\n{sym}: run10={run*100:.1f}%  range5={rng5*100:.1f}%  bars={len(c)}")
    for a, b in list(zip(d, c))[-16:]:
        print("  ", a, b)