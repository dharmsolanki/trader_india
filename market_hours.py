from datetime import datetime, date, time, timedelta
from zoneinfo import ZoneInfo

IST = ZoneInfo("Asia/Kolkata")
OPEN = time(9, 15)
CLOSE = time(15, 30)

# NSE equity weekday holidays. Sirf Sep-Dec 2026 bhara hai.
# Jan-Aug ke dates NSE ke official circular se khud add karo.
HOLIDAYS = {
    date(2026, 9, 14): "Ganesh Chaturthi",
    date(2026, 10, 2): "Gandhi Jayanti",
    date(2026, 10, 20): "Dussehra",
    date(2026, 11, 10): "Diwali Balipratipada",
    date(2026, 11, 24): "Guru Nanak Jayanti",
    date(2026, 12, 25): "Christmas",
}


def now_ist():
    return datetime.now(IST)


def is_trading_day(d: date) -> bool:
    return d.weekday() < 5 and d not in HOLIDAYS


def market_status(dt=None) -> str:
    dt = (dt or now_ist()).astimezone(IST)
    d, t = dt.date(), dt.time()
    if d.weekday() >= 5:
        return "CLOSED - weekend"
    if d in HOLIDAYS:
        return f"CLOSED - holiday ({HOLIDAYS[d]})"
    if t < OPEN:
        return "BEFORE OPEN"
    if t < CLOSE:
        return "OPEN"
    return "CLOSED - after hours"


def next_open(dt=None) -> datetime:
    dt = (dt or now_ist()).astimezone(IST)
    d = dt.date()
    if not (is_trading_day(d) and dt.time() < OPEN):
        d += timedelta(days=1)
        while not is_trading_day(d):
            d += timedelta(days=1)
    return datetime.combine(d, OPEN, tzinfo=IST)


if __name__ == "__main__":
    n = now_ist()
    print("Abhi (IST):", n.strftime("%a %d %b %Y %H:%M"))
    print("Status    :", market_status(n))
    print("Next open :", next_open(n).strftime("%a %d %b %Y %H:%M"))

    # self-test
    assert not is_trading_day(date(2026, 11, 10)), "holiday galat"
    assert not is_trading_day(date(2026, 11, 14)), "Saturday galat"
    assert is_trading_day(date(2026, 11, 16)), "Monday galat"
    assert market_status(datetime(2026, 11, 16, 9, 0, tzinfo=IST)) == "BEFORE OPEN"
    assert market_status(datetime(2026, 11, 16, 10, 0, tzinfo=IST)) == "OPEN"
    assert market_status(datetime(2026, 11, 16, 15, 30, tzinfo=IST)).startswith("CLOSED")
    assert next_open(datetime(2026, 11, 9, 20, 0, tzinfo=IST)).date() == date(2026, 11, 11)
    print("Tests PASS")