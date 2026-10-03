import csv
import os
import time
from datetime import datetime

from market import get_btc_price

FILE = "../data/market.csv"


def save_data(market):
    file_exists = os.path.exists(FILE)

    with open(FILE, "a", newline="") as f:
        writer = csv.writer(f)

        if not file_exists:
            writer.writerow([
                "timestamp",
                "price",
                "buy",
                "sell",
                "high",
                "low",
                "volume_btc",
                "volume_idr"
            ])

        writer.writerow([
            datetime.now().isoformat(),
            market["last"],
            market["buy"],
            market["sell"],
            market["high"],
            market["low"],
            market["volume_btc"],
            market["volume_idr"]
        ])


print("================================")
print("      MARKET DATA COLLECTOR")
print("================================")
print("Pair : BTC/IDR")
print("Mode : DATA COLLECTION")
print("Tekan CTRL+C untuk berhenti")
print()

while True:
    market = get_btc_price()

    if market:
        save_data(market)

        print(
            datetime.now().strftime("%H:%M:%S"),
            "| BTC/IDR:",
            f"Rp{market['last']:,.0f}"
        )

    time.sleep(30)
