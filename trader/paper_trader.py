import csv
import json
import os
import time
from datetime import datetime


# ==================================================
# KONFIGURASI
# ==================================================

COIN = "ETH/IDR"

DATA_FILE = "data/candles_1m.csv"
MEMORY_FILE = "data/trade_memory.json"

INITIAL_BALANCE = 1_000_000.0

FEE_RATE = 0.001

BUY_THRESHOLD = 0.60
SELL_THRESHOLD = 0.40

TAKE_PROFIT = 0.003
STOP_LOSS = 0.002

CHECK_INTERVAL = 10


# ==================================================
# MEMORY
# ==================================================

def load_memory():

    if not os.path.exists(MEMORY_FILE):

        return {
            "trades": [],
            "wins": 0,
            "losses": 0,
            "total_profit": 0.0
        }

    try:

        with open(MEMORY_FILE, "r") as f:
            return json.load(f)

    except Exception:

        return {
            "trades": [],
            "wins": 0,
            "losses": 0,
            "total_profit": 0.0
        }


def save_memory(memory):

    os.makedirs("data", exist_ok=True)

    with open(MEMORY_FILE, "w") as f:

        json.dump(
            memory,
            f,
            indent=2
        )


# ==================================================
# CANDLE DATA
# ==================================================

def load_candles():

    if not os.path.exists(DATA_FILE):
        return []

    candles = []

    try:

        with open(DATA_FILE, "r") as f:

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

                except Exception:
                    continue

    except Exception:
        return []

    return candles


# ==================================================
# EMA
# ==================================================

def ema(values, period):

    if len(values) < period:
        return None

    multiplier = 2 / (period + 1)

    current = sum(
        values[:period]
    ) / period

    for price in values[period:]:

        current = (
            (price - current)
            * multiplier
            + current
        )

    return current


# ==================================================
# RSI
# ==================================================

def calculate_rsi(values, period=14):

    if len(values) <= period:
        return None

    gains = 0.0
    losses = 0.0

    start = len(values) - period

    for i in range(start, len(values)):

        change = (
            values[i]
            - values[i - 1]
        )

        if change > 0:
            gains += change

        else:
            losses += abs(change)

    if losses == 0:
        return 100.0

    rs = gains / losses

    return 100 - (
        100 / (1 + rs)
    )


# ==================================================
# AI DECISION
# ==================================================

def calculate_signal(candles):

    closes = [
        x["close"]
        for x in candles
    ]

    volumes = [
        x["volume"]
        for x in candles
    ]

    if len(closes) < 50:

        return (
            "HOLD",
            0.5,
            {}
        )

    price = closes[-1]

    ema20 = ema(
        closes[-20:],
        20
    )

    ema50 = ema(
        closes[-50:],
        50
    )

    rsi = calculate_rsi(
        closes
    )

    momentum = (
        (price - closes[-6])
        / closes[-6]
    )

    volume_change = 0.0

    if volumes[-2] != 0:

        volume_change = (
            (volumes[-1] - volumes[-2])
            / volumes[-2]
        )

    score = 0.5

    # Trend
    if ema20 and ema50:

        if ema20 > ema50:
            score += 0.15

        else:
            score -= 0.15

    # RSI
    if rsi is not None:

        if 45 <= rsi <= 65:

            score += 0.15

        elif rsi > 75:

            score -= 0.15

        elif rsi < 30:

            score += 0.10

    # Momentum
    if momentum > 0:

        score += 0.10

    else:

        score -= 0.10

    # Volume
    if volume_change > 0:

        score += 0.05

    score = max(
        0.0,
        min(1.0, score)
    )

    if score >= BUY_THRESHOLD:

        signal = "BUY"

    elif score <= SELL_THRESHOLD:

        signal = "SELL"

    else:

        signal = "HOLD"

    indicators = {

        "price": price,

        "ema20": ema20,

        "ema50": ema50,

        "rsi": rsi,

        "momentum": momentum,

        "volume_change": volume_change

    }

    return (
        signal,
        score,
        indicators
    )


# ==================================================
# PAPER TRADER
# ==================================================

def main():

    print("=" * 50)
    print("        LOCAL AI PAPER TRADER")
    print("=" * 50)

    print(
        f"Coin          : {COIN}"
    )

    print(
        f"Initial money : Rp{INITIAL_BALANCE:,.0f}"
    )

    print(
        "Mode          : PAPER TRADING"
    )

    print("=" * 50)

    balance = INITIAL_BALANCE

    coin_amount = 0.0

    entry_price = None

    entry_balance = None

    memory = load_memory()

    last_timestamp = None

    while True:

        candles = load_candles()

        if len(candles) < 50:

            print(
                "Menunggu minimal "
                "50 candle..."
            )

            time.sleep(CHECK_INTERVAL)

            continue

        latest = candles[-1]

        timestamp = latest["timestamp"]

        # Jangan memproses candle
        # yang sama berulang-ulang.

        if timestamp == last_timestamp:

            time.sleep(CHECK_INTERVAL)

            continue

        last_timestamp = timestamp

        signal, score, indicators = (
            calculate_signal(candles)
        )

        price = indicators["price"]

        now = datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        )

        print()
        print("=" * 50)

        print(now)

        print(
            f"{COIN} : Rp{price:,.0f}"
        )

        print(
            f"EMA20       : "
            f"{indicators['ema20']:.2f}"
        )

        print(
            f"EMA50       : "
            f"{indicators['ema50']:.2f}"
        )

        print(
            f"RSI         : "
            f"{indicators['rsi']:.2f}"
        )

        print(
            f"Momentum    : "
            f"{indicators['momentum'] * 100:.3f}%"
        )

        print(
            f"Volume      : "
            f"{indicators['volume_change'] * 100:.2f}%"
        )

        print(
            f"AI Score    : "
            f"{score * 100:.2f}%"
        )

        print(
            f"Decision    : {signal}"
        )

        print(
            f"Cash        : "
            f"Rp{balance:,.0f}"
        )

        print(
            f"{COIN.split('/')[0]}       : "
            f"{coin_amount:.8f}"
        )

        # ==========================================
        # BUY
        # ==========================================

        if signal == "BUY" and coin_amount == 0:

            fee = (
                balance
                * FEE_RATE
            )

            usable_money = (
                balance
                - fee
            )

            coin_amount = (
                usable_money
                / price
            )

            entry_price = price

            entry_balance = balance

            balance = 0.0

            print()
            print(">>> PAPER BUY <<<")

            print(
                f"Entry price : "
                f"Rp{entry_price:,.0f}"
            )

            print(
                f"Amount      : "
                f"{coin_amount:.8f}"
            )

        # ==========================================
        # POSITION MANAGEMENT
        # ==========================================

        elif coin_amount > 0:

            change = (
                (price - entry_price)
                / entry_price
            )

            should_sell = (

                change >= TAKE_PROFIT

                or change <= -STOP_LOSS

                or signal == "SELL"
            )

            if should_sell:

                gross_value = (
                    coin_amount
                    * price
                )

                sell_fee = (
                    gross_value
                    * FEE_RATE
                )

                final_balance = (
                    gross_value
                    - sell_fee
                )

                profit = (
                    final_balance
                    - entry_balance
                )

                trade = {

                    "time": now,

                    "coin": COIN,

                    "entry": entry_price,

                    "exit": price,

                    "return": change,

                    "profit": profit,

                    "score": score

                }

                memory["trades"].append(
                    trade
                )

                if profit > 0:

                    memory["wins"] += 1

                else:

                    memory["losses"] += 1

                memory["total_profit"] += (
                    profit
                )

                balance = final_balance

                coin_amount = 0.0

                print()
                print(">>> PAPER SELL <<<")

                print(
                    f"Exit price  : "
                    f"Rp{price:,.0f}"
                )

                print(
                    f"Return      : "
                    f"{change * 100:.3f}%"
                )

                print(
                    f"Profit/Loss : "
                    f"Rp{profit:,.0f}"
                )

                print(
                    f"Balance     : "
                    f"Rp{balance:,.0f}"
                )

                save_memory(memory)

        time.sleep(
            CHECK_INTERVAL
        )


# ==================================================
# START PROGRAM
# ==================================================

if __name__ == "__main__":
    main()
