import csv
import os
import math

CANDLE_FILE = "data/candles_1m.csv"
DATA_FILE = "data/ai_dataset.csv"

# AI melihat apakah harga 15 menit kemudian
# naik cukup besar untuk layak ditradingkan.
HORIZON = 15

# Target minimum pergerakan harga.
# Kita mulai dari 0.30%.
TARGET_RETURN = 0.003


def ema(values, period):
    result = [None] * len(values)

    if len(values) < period:
        return result

    multiplier = 2 / (period + 1)

    current = sum(values[:period]) / period
    result[period - 1] = current

    for i in range(period, len(values)):
        current = (
            (values[i] - current) * multiplier
            + current
        )

        result[i] = current

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
            losses.append(0.0)
        else:
            gains.append(0.0)
            losses.append(abs(change))

    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period

    if avg_loss == 0:
        result[period] = 100.0
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
            result[i] = 100.0
        else:
            rs = avg_gain / avg_loss
            result[i] = 100 - (100 / (1 + rs))

    return result


def main():

    print("=" * 40)
    print("AI DATASET BUILDER - 15 MIN")
    print("=" * 40)

    if not os.path.exists(CANDLE_FILE):
        print("Candle file tidak ditemukan.")
        return

    candles = []

    with open(CANDLE_FILE, "r") as f:

        reader = csv.DictReader(f)

        for row in reader:

            try:

                candles.append({
                    "timestamp": int(row["timestamp"]),
                    "open": float(row["open"]),
                    "high": float(row["high"]),
                    "low": float(row["low"]),
                    "close": float(row["close"]),
                    "volume": float(row["volume"])
                })

            except (ValueError, KeyError):
                continue

    print("Candles:", len(candles))

    minimum = 50 + HORIZON

    if len(candles) < minimum:
        print(
            f"Minimal {minimum} candle diperlukan."
        )
        return

    closes = [
        x["close"]
        for x in candles
    ]

    volumes = [
        x["volume"]
        for x in candles
    ]

    ema20 = ema(closes, 20)
    ema50 = ema(closes, 50)
    rsi14 = rsi(closes, 14)

    rows = []

    for i in range(50, len(candles) - HORIZON):

        if ema20[i] is None:
            continue

        if ema50[i] is None:
            continue

        if rsi14[i] is None:
            continue

        close = closes[i]

        # Momentum 5 menit
        momentum = 0.0

        if closes[i - 5] != 0:

            momentum = (
                (close - closes[i - 5])
                / closes[i - 5]
            )

        # Volatility candle
        volatility = 0.0

        if close != 0:

            volatility = (
                candles[i]["high"]
                - candles[i]["low"]
            ) / close

        # Perubahan volume
        volume_change = 0.0

        if volumes[i - 1] != 0:

            volume_change = (
                (volumes[i] - volumes[i - 1])
                / volumes[i - 1]
            )

        # Harga 15 menit ke depan
        future_price = closes[
            i + HORIZON
        ]

        future_return = (
            (future_price - close)
            / close
        )

        # TARGET
        #
        # 1 = harga naik >= 0.30%
        # 0 = tidak mencapai target

        target = (
            1
            if future_return >= TARGET_RETURN
            else 0
        )

        rows.append({
            "timestamp": candles[i]["timestamp"],
            "close": close,
            "ema20": ema20[i],
            "ema50": ema50[i],
            "rsi14": rsi14[i],
            "momentum": momentum,
            "volatility": volatility,
            "volume": volumes[i],
            "volume_change": volume_change,
            "future_return": future_return,
            "target": target
        })

    with open(
        DATA_FILE,
        "w",
        newline=""
    ) as f:

        fields = [
            "timestamp",
            "close",
            "ema20",
            "ema50",
            "rsi14",
            "momentum",
            "volatility",
            "volume",
            "volume_change",
            "future_return",
            "target"
        ]

        writer = csv.DictWriter(
            f,
            fieldnames=fields
        )

        writer.writeheader()
        writer.writerows(rows)

    target0 = sum(
        x["target"] == 0
        for x in rows
    )

    target1 = sum(
        x["target"] == 1
        for x in rows
    )

    print()
    print("Dataset:", len(rows))
    print(
        f"TARGET 0: {target0} "
        f"({target0 / len(rows) * 100:.2f}%)"
    )
    print(
        f"TARGET 1: {target1} "
        f"({target1 / len(rows) * 100:.2f}%)"
    )

    print()
    print(
        "Horizon:",
        HORIZON,
        "menit"
    )

    print(
        "Target return:",
        TARGET_RETURN * 100,
        "%"
    )

    print()
    print(
        "Saved:",
        DATA_FILE
    )


if __name__ == "__main__":
    main()
