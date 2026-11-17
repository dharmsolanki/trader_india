import json
import os
import webbrowser
from datetime import date, timedelta
from urllib.parse import quote, urlencode, urlparse, parse_qs

import requests
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("UPSTOX_API_KEY")
API_SECRET = os.getenv("UPSTOX_API_SECRET")
REDIRECT = os.getenv("UPSTOX_REDIRECT_URI")
BASE = "https://api.upstox.com/v2"
TOKEN_FILE = "token.json"

RELIANCE = "NSE_EQ|INE002A01018"  # test ke liye


def login_url():
    q = urlencode({
        "response_type": "code",
        "client_id": API_KEY,
        "redirect_uri": REDIRECT,
    })
    return f"{BASE}/login/authorization/dialog?{q}"


def extract_code(text: str) -> str:
    text = text.strip()
    if "code=" in text:
        return parse_qs(urlparse(text).query)["code"][0]
    return text


def exchange_code(code: str) -> str:
    r = requests.post(
        f"{BASE}/login/authorization/token",
        headers={"accept": "application/json",
                 "Content-Type": "application/x-www-form-urlencoded"},
        data={
            "code": code,
            "client_id": API_KEY,
            "client_secret": API_SECRET,
            "redirect_uri": REDIRECT,
            "grant_type": "authorization_code",
        },
        timeout=20,
    )
    if r.status_code != 200:
        raise SystemExit(f"Token exchange fail {r.status_code}: {r.text}")
    return r.json()["access_token"]


def fetch_candles(token: str, instrument: str, days: int = 10):
    to_d = date.today()
    from_d = to_d - timedelta(days=days)
    url = (f"{BASE}/historical-candle/{quote(instrument, safe='')}"
           f"/day/{to_d}/{from_d}")
    return requests.get(
        url,
        headers={"accept": "application/json",
                 "Authorization": f"Bearer {token}"},
        timeout=20,
    )


def get_token() -> str:
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE) as f:
            tok = json.load(f).get("access_token")
        if tok and fetch_candles(tok, RELIANCE).status_code == 200:
            print("Saved token chal raha hai.")
            return tok
        print("Saved token expire/invalid. Naya login karna hoga.")

    url = login_url()
    print("\nBrowser khul raha hai. Upstox login karo.")
    print("Login ke baad page load nahi hoga (localhost error), yeh normal hai.")
    print("Address bar ka POORA URL copy karke yahan paste karo.\n")
    webbrowser.open(url)
    code = extract_code(input("URL ya code: "))
    tok = exchange_code(code)
    with open(TOKEN_FILE, "w") as f:
        json.dump({"access_token": tok}, f)
    print("Token save ho gaya (token.json).")
    return tok


if __name__ == "__main__":
    if not (API_KEY and API_SECRET and REDIRECT):
        raise SystemExit(".env mein 3 values bharo: KEY, SECRET, REDIRECT_URI")
    token = get_token()
    r = fetch_candles(token, RELIANCE)
    print("Status:", r.status_code)
    if r.status_code == 200:
        candles = r.json()["data"]["candles"]
        print("Reliance daily candles (latest 3) [time, O, H, L, C, vol, OI]:")
        for c in candles[:3]:
            print(c)
    else:
        print(r.text)