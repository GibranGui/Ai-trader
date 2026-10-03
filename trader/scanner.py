import json
import os
import time
import urllib.request
from datetime import datetime


URL = "https://indodax.com/api/tickers"

SCAN_INTERVAL = 60

MIN_VOLUME_IDR = 100_000_000

TOP_RESULTS = 10

LOG_FILE = "data/scanner_log.json"


def get_market_data():

    request = urllib.request.Request(
        URL,
        headers={
            "User-Agent": "Local-AI-Trader/1.0"
        }
    )

    try:

        with urllib.request.urlopen(
            request,
            timeout=15
        ) as response:

            return json.loads(
                response.read().decode()
            )

    except Exception as e:

        print("ERROR:", e)

        return None


def save_log(results):

    os.makedirs(
        "data",
        exist_ok=True
    )

    data = {
        "time": datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        ),
        "results": results
    }

    with open(
        LOG_FILE,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            data,
            f,
            indent=2
        )


def calculate_score(ticker):

    try:

        last = float(
            ticker.get("last", 0)
        )

        high = float(
            ticker.get("high", 0)
        )

        low = float(
            ticker.get("low", 0)
        )

        volume = float(
            ticker.get("vol_idr", 0)
        )

    except Exception:

        return None

    if last <= 0:
        return None

    if volume < MIN_VOLUME_IDR:
        return None

    # Volatilitas intraday
    volatility = 0.0

    if low > 0:

        volatility = (
            (high - low)
            / low
        )

    # Posisi harga terhadap range
    range_position = 0.5

    if high > low:

        range_position = (
            (last - low)
            / (high - low)
        )

    # Momentum sederhana
    momentum_score = (
        range_position
        * 100
    )

    volatility_score = min(
        volatility * 1000,
        100
    )

    volume_score = min(
        volume / 10_000_000,
        100
    )

    score = (
        momentum_score * 0.40
        +
        volatility_score * 0.30
        +
        volume_score * 0.30
    )

    return {
        "price": last,
        "volume_idr": volume,
        "high": high,
        "low": low,
        "volatility": volatility,
        "score": score
    }


def scan():

    data = get_market_data()

    if not data:

        return []

    tickers = data.get(
        "tickers",
        {}
    )

    results = []

    for pair, ticker in tickers.items():

        # Hanya market IDR
        if not pair.endswith("_idr"):
            continue

        result = calculate_score(
            ticker
        )

        if result is None:
            continue

        result["pair"] = pair

        results.append(
            result
        )

    results.sort(
        key=lambda x: x["score"],
        reverse=True
    )

    return results[:TOP_RESULTS]


def main():

    print()
    print("=" * 60)
    print("           LOCAL AI CRYPTO SCANNER")
    print("=" * 60)
    print("Market       : INDODAX IDR")
    print("Mode         : PAPER TRADING")
    print("Capital      : Rp200,000")
    print("Auto Scan    : ENABLED")
    print("=" * 60)

    while True:

        print()
        print(
            datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S"
            )
        )

        results = scan()

        if not results:

            print(
                "Tidak ada kandidat."
            )

        else:

            print()
            print(
                "TOP COIN AKTIF:"
            )

            print("-" * 60)

            for i, coin in enumerate(
                results,
                1
            ):

                pair = coin["pair"]

                price = coin["price"]

                volume = coin[
                    "volume_idr"
                ]

                volatility = coin[
                    "volatility"
                ]

                score = coin[
                    "score"
                ]

                print(
                    f"{i:02d}. "
                    f"{pair.upper():15s} "
                    f"Price Rp{price:,.8f} | "
                    f"Vol Rp{volume:,.0f} | "
                    f"Volatility "
                    f"{volatility * 100:.2f}% | "
                    f"Score {score:.2f}"
                )

            save_log(
                results
            )

        print()
        print(
            f"Scan berikutnya "
            f"dalam {SCAN_INTERVAL} detik..."
        )

        time.sleep(
            SCAN_INTERVAL
        )


if __name__ == "__main__":

    main()
