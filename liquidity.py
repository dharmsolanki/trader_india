import json
import time

import requests

BASE = "https://api.upstox.com/v2"
BATCH = 100        # ek call mein kitne stocks
MIN_PRICE = 50     # isse sasta stock hata do (andaza, badal sakte ho)
TOP_N = 300        # turnover ke hisaab se top kitne rakhne hain (andaza)


def load_token():
    with open("token.json") as f:
        return json.load(f)["access_token"]


def get_quotes(tok, keys):
    r = requests.get(
        f"{BASE}/market-quote/quotes",
        params={"instrument_key": ",".join(keys)},
        headers={"accept": "application/json",
                 "Authorization": f"Bearer {tok}"},
        timeout=30,
    )
    if r.status_code != 200:
        raise SystemExit(f"Quote fail {r.status_code}: {r.text[:300]}")
    return r.json().get("data", {})


if __name__ == "__main__":
    tok = load_token()
    with open("universe.json", encoding="utf-8") as f:
        uni = json.load(f)
    by_key = {u["key"]: u for u in uni}
    keys = list(by_key)
    print("Universe:", len(keys))

    rows = []
    shown = False
    for i in range(0, len(keys), BATCH):
        data = get_quotes(tok, keys[i:i + BATCH])
        for v in data.values():
            if not shown:
                print("Quote ke fields:", sorted(v.keys()))
                shown = True
            k = v.get("instrument_token")
            if k not in by_key:
                continue
            price = v.get("last_price") or 0
            vol = v.get("volume") or 0
            rows.append({
                "symbol": by_key[k]["symbol"],
                "key": k,
                "price": price,
                "volume": vol,
                "turnover_cr": round(price * vol / 1e7, 2),
            })
        time.sleep(0.3)

    print("Quote mile:", len(rows))
    if not rows:
        raise SystemExit("Koi match nahi hua. Upar wale 'Quote ke fields' bhejo.")

    rows = [r for r in rows if r["price"] >= MIN_PRICE and r["volume"] > 0]
    rows.sort(key=lambda r: r["turnover_cr"], reverse=True)
    top = rows[:TOP_N]

    with open("liquid.json", "w", encoding="utf-8") as f:
        json.dump(top, f)

    print(f"Filter ke baad: {len(rows)}, saved top {len(top)} -> liquid.json")
    print("Top 10 turnover (Cr):")
    for r in top[:10]:
        print(f"  {r['symbol']:<12} Rs{r['price']:>9}  {r['turnover_cr']:>9}")
    print("Aakhri:", top[-1] if top else None)