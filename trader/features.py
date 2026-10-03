import csv
import os
import math

INPUT_FILE = "data/candles_1m.csv"
OUTPUT_FILE = "data/ai_dataset.csv"


def ema(values, period):
    result = [None] * len(values)

    if len(values) < period:
        return result

    multiplier = 2 / (period + 1)

    first = sum(values[:period]) / period
    result[period - 1] = first

    previous = first

    for i in range(period, len(values)):
        current = (
            (values[i] - previous) * multiplier
            + previous
        )

        result[i] = current
        previous = current

    return result


def rsi(values, period=14):
    result = [None] * len(values)

    if len(values) <= period:
        return result

    gains = []
    losses = []

    for i in range(1, len(values)):
        change = values[i] - values[i - 1]

        if change > 0:
            gains.append(change)
            losses.append(0)
        else:
            gains.append(0)
            losses.append(abs(change))

    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period

    if avg_loss == 0:
        result[period] = 100
    else:
        rs = avg_gain / avg_loss
        result[period] = 100 - (100 / (1 + rs))

    for i in range(period + 1, len(values)):
        avg_gain = (
            (avg_gain * (period - 1))
            + gains[i - 1]
        ) / period

        avg_loss = (
            (avg_loss * (period - 1))
            + losses[i - 1]
        ) / period

        if avg_loss == 0:
            result[i] = 100
        else:
            rs = avg_gain / avg_loss
            result[i] = 100 - (100 / (1 + rs))

    return result


def load_candles():
    candles = []

    with open(INPUT_FILE, "r") as f:
        reader = csv.DictReader(f)

        for row in reader:
            candles.append({
                "timestamp": int(row["timestamp"]),
                "open": float(row["open"]),
                "high": float(row["high"]),
                "low": float(row["low"]),
                "close": float(row["close"]),
                "volume": float(row["volume"])
            })

    return candles


def build_dataset():
    candles = load_candles()

    if len(candles) < 60:
        print(
            f"Data belum cukup: {len(candles)} candle."
        )
        print("Minimal 60 candle diperlukan.")
        return

    closes = [x["close"] for x in candles]
    volumes = [x["volume"] for x in candles]

    ema20 = ema(closes, 20)
    ema50 = ema(closes, 50)
    rsi14 = rsi(closes, 14)

    rows = []

    for i in range(50, len(candles) - 1):

        if ema20[i] is None:
            continue

        if ema50[i] is None:
            continue

        if rsi14[i] is None:
            continue

        close = closes[i]

        if close == 0:
            continue

        momentum = (
            (close - closes[i - 5])
            / closes[i - 5]
        ) * 100

        volatility = (
            (candles[i]["high"] - candles[i]["low"])
            / close
        ) * 100

        previous_volume = volumes[i - 1]

        if previous_volume == 0:
            volume_change = 0
        else:
            volume_change = (
                (volumes[i] - previous_volume)
                / previous_volume
            ) * 100

        # Target:
        # 1 = candle berikutnya naik
        # 0 = candle berikutnya tidak naik

        next_close = closes[i + 1]

        if next_close > close:
            target = 1
        else:
            target = 0

        rows.append([
            candles[i]["timestamp"],
            close,
            ema20[i],
            ema50[i],
            rsi14[i],
            momentum,
            volatility,
            volumes[i],
            volume_change,
            target
        ])

    os.makedirs("data", exist_ok=True)

    with open(OUTPUT_FILE, "w", newline="") as f:
        writer = csv.writer(f)

        writer.writerow([
            "timestamp",
            "close",
            "ema20",
            "ema50",
            "rsi14",
            "momentum",
            "volatility",
            "volume",
            "volume_change",
            "target"
        ])

        writer.writerows(rows)

    print()
    print("================================")
    print("       AI FEATURE ENGINE")
    print("================================")
    print(f"Candle        : {len(candles)}")
    print(f"Dataset       : {len(rows)}")
    print(f"Output        : {OUTPUT_FILE}")
    print()
    print("Fitur:")
    print("- EMA20")
    print("- EMA50")
    print("- RSI14")
    print("- Momentum")
    print("- Volatility")
    print("- Volume")
    print("- Volume Change")
    print()
    print("Target:")
    print("1 = harga candle berikutnya naik")
    print("0 = harga candle berikutnya tidak naik")
    print()


if __name__ == "__main__":
    build_dataset()
