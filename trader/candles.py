import csv
import json
import os
import time
import urllib.request

PAIR = "BTCIDR"
TIMEFRAME = "1"

FILE = "data/candles_1m.csv"


def get_candles():
    now = int(time.time())
    start = now - (60 * 120)

    url = (
        "https://indodax.com/tradingview/history_v2"
        f"?from={start}&to={now}"
        f"&symbol={PAIR}"
        f"&tf={TIMEFRAME}"
    )

    try:
        request = urllib.request.Request(
            url,
            headers={
                "User-Agent": "Mozilla/5.0"
            }
        )

        with urllib.request.urlopen(request, timeout=10) as response:
            return json.loads(response.read().decode())

    except Exception as e:
        print("Gagal mengambil candle:", e)
        return []


def save_candles(candles):
    os.makedirs("data", exist_ok=True)

    existing = set()

    if os.path.exists(FILE):
        with open(FILE, "r", newline="") as f:
            reader = csv.DictReader(f)

            for row in reader:
                existing.add(row["timestamp"])

    new_count = 0

    with open(FILE, "a", newline="") as f:
        writer = csv.writer(f)

        if os.path.getsize(FILE) == 0:
            writer.writerow([
                "timestamp",
                "open",
                "high",
                "low",
                "close",
                "volume"
            ])

        for candle in candles:
            timestamp = str(candle["Time"])

            if timestamp in existing:
                continue

            writer.writerow([
                timestamp,
                candle["Open"],
                candle["High"],
                candle["Low"],
                candle["Close"],
                candle["Volume"]
            ])

            existing.add(timestamp)
            new_count += 1

    return new_count


print("================================")
print("      BTC/IDR CANDLE COLLECTOR")
print("================================")
print("Timeframe : 1 menit")
print("Mode      : DATA COLLECTION")
print("Tekan CTRL+C untuk berhenti")
print()

while True:
    candles = get_candles()

    if candles:
        new_count = save_candles(candles)

        latest = candles[-1]

        print(
            time.strftime("%H:%M:%S"),
            "| Close:",
            f"Rp{float(latest['Close']):,.0f}",
            "| Candle baru:",
            new_count
        )

    time.sleep(60)
