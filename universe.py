import gzip
import json
from collections import Counter

import requests

URL = "https://assets.upstox.com/market-quote/instruments/exchange/NSE.json.gz"
OUT = "universe.json"


def download():
    r = requests.get(URL, timeout=180)
    r.raise_for_status()
    try:
        return json.loads(gzip.decompress(r.content))
    except OSError:
        return json.loads(r.content)  # server ne pehle hi decompress kar diya


if __name__ == "__main__":
    rows = download()
    print("Total NSE rows:", len(rows))

    eq = [r for r in rows if r.get("segment") == "NSE_EQ"]
    print("NSE_EQ rows   :", len(eq))
    print("Fields        :", sorted(eq[0].keys()))
    print("instrument_type:", dict(Counter(r.get("instrument_type") for r in eq)))
    print("security_type  :", dict(Counter(r.get("security_type") for r in eq)))

    keep = []
    for r in eq:
        if r.get("instrument_type") != "EQ":
            continue
        if r.get("security_type") != "NORMAL":
            continue
        keep.append({
            "symbol": r.get("trading_symbol") or r.get("tradingsymbol"),
            "name": r.get("name"),
            "isin": r.get("isin"),
            "key": r.get("instrument_key"),
        })

    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(keep, f, ensure_ascii=False)

    print(f"\nSaved {len(keep)} stocks -> {OUT}")
    print("Sample:", keep[:3])
    rel = [k for k in keep if k["symbol"] == "RELIANCE"]
    print("RELIANCE:", rel)