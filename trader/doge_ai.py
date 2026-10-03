import csv
import json
import math
import os
import time
import urllib.request
from datetime import datetime


# ============================================================
# CONFIG
# ============================================================

PAIR = "doge_idr"

COIN_NAME = "DOGE/IDR"

INITIAL_BALANCE = 200_000.0

FEE_RATE = 0.001

POLL_SECONDS = 60

TAKE_PROFIT = 0.004
STOP_LOSS = 0.003

BUY_THRESHOLD = 0.65
SELL_THRESHOLD = 0.40

DATA_DIR = "data"

CANDLE_FILE = os.path.join(
    DATA_DIR,
    "doge_idr_1m.csv"
)

MEMORY_FILE = os.path.join(
    DATA_DIR,
    "doge_memory.json"
)

STATE_FILE = os.path.join(
    DATA_DIR,
    "doge_state.json"
)

LOG_FILE = os.path.join(
    DATA_DIR,
    "doge_bot.log"
)


# ============================================================
# DIRECTORY
# ============================================================

os.makedirs(DATA_DIR, exist_ok=True)


# ============================================================
# LOG
# ============================================================

def log(message):

    timestamp = datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S"
    )

    text = f"[{timestamp}] {message}"

    print(text)

    with open(
        LOG_FILE,
        "a",
        encoding="utf-8"
    ) as f:

        f.write(text + "\n")


# ============================================================
# HTTP
# ============================================================

def get_json(url):

    try:

        request = urllib.request.Request(
            url,
            headers={
                "User-Agent": "Local-AI-Trader/1.0"
            }
        )

        with urllib.request.urlopen(
            request,
            timeout=15
        ) as response:

            data = response.read().decode(
                "utf-8"
            )

            return json.loads(data)

    except Exception as e:

        log(
            f"Network error: {e}"
        )

        return None


# ============================================================
# INDODAX TICKER
# ============================================================

def get_ticker():

    url = (
        "https://indodax.com/api/ticker/"
        + PAIR
    )

    data = get_json(url)

    if not data:
        return None

    ticker = data.get("ticker")

    if not ticker:
        return None

    try:

        return {
            "timestamp": int(
                ticker.get(
                    "server_time",
                    time.time()
                )
            ),

            "last": float(
                ticker["last"]
            ),

            "high": float(
                ticker.get(
                    "high",
                    ticker["last"]
                )
            ),

            "low": float(
                ticker.get(
                    "low",
                    ticker["last"]
                )
            ),

            "volume": float(
                ticker.get(
                    "vol_idr",
                    0
                )
            )
        }

    except Exception as e:

        log(
            f"Ticker error: {e}"
        )

        return None


# ============================================================
# CANDLE STORAGE
# ============================================================

def ensure_candle_file():

    if os.path.exists(CANDLE_FILE):
        return

    with open(
        CANDLE_FILE,
        "w",
        newline="",
        encoding="utf-8"
    ) as f:

        writer = csv.writer(f)

        writer.writerow([
            "timestamp",
            "open",
            "high",
            "low",
            "close",
            "volume"
        ])


def load_candles():

    ensure_candle_file()

    candles = []

    try:

        with open(
            CANDLE_FILE,
            "r",
            encoding="utf-8"
        ) as f:

            reader = csv.DictReader(f)

            for row in reader:

                try:

                    candles.append({
                        "timestamp": int(
                            row["timestamp"]
                        ),

                        "open": float(
                            row["open"]
                        ),

                        "high": float(
                            row["high"]
                        ),

                        "low": float(
                            row["low"]
                        ),

                        "close": float(
                            row["close"]
                        ),

                        "volume": float(
                            row["volume"]
                        )
                    })

                except Exception:
                    continue

    except Exception as e:

        log(
            f"Read candle error: {e}"
        )

    return candles


def save_candle(candle):

    ensure_candle_file()

    with open(
        CANDLE_FILE,
        "a",
        newline="",
        encoding="utf-8"
    ) as f:

        writer = csv.writer(f)

        writer.writerow([
            candle["timestamp"],
            candle["open"],
            candle["high"],
            candle["low"],
            candle["close"],
            candle["volume"]
        ])


# ============================================================
# INDICATORS
# ============================================================

def ema(values, period):

    if len(values) < period:
        return None

    current = (
        sum(values[:period])
        / period
    )

    multiplier = (
        2 / (period + 1)
    )

    for value in values[period:]:

        current = (
            (value - current)
            * multiplier
            + current
        )

    return current


def rsi(values, period=14):

    if len(values) <= period:
        return None

    gains = []
    losses = []

    for i in range(1, len(values)):

        change = (
            values[i]
            - values[i - 1]
        )

        if change > 0:

            gains.append(change)
            losses.append(0.0)

        else:

            gains.append(0.0)
            losses.append(
                abs(change)
            )

    avg_gain = (
        sum(gains[:period])
        / period
    )

    avg_loss = (
        sum(losses[:period])
        / period
    )

    for i in range(
        period,
        len(gains)
    ):

        avg_gain = (
            (
                avg_gain * (period - 1)
            )
            + gains[i]
        ) / period

        avg_loss = (
            (
                avg_loss * (period - 1)
            )
            + losses[i]
        ) / period

    if avg_loss == 0:
        return 100.0

    rs = (
        avg_gain
        / avg_loss
    )

    return 100 - (
        100 / (1 + rs)
    )


def volatility(candles):

    if len(candles) < 10:
        return 0.0

    values = []

    for candle in candles[-10:]:

        if candle["close"] == 0:
            continue

        value = (
            candle["high"]
            - candle["low"]
        ) / candle["close"]

        values.append(value)

    if not values:
        return 0.0

    return (
        sum(values)
        / len(values)
    )


# ============================================================
# AI MEMORY
# ============================================================

def default_memory():

    return {
        "trades": [],
        "wins": 0,
        "losses": 0,
        "total_profit": 0.0,
        "buy_threshold": BUY_THRESHOLD,
        "sell_threshold": SELL_THRESHOLD
    }


def load_memory():

    if not os.path.exists(
        MEMORY_FILE
    ):

        return default_memory()

    try:

        with open(
            MEMORY_FILE,
            "r",
            encoding="utf-8"
        ) as f:

            memory = json.load(f)

        return memory

    except Exception:

        return default_memory()


def save_memory(memory):

    with open(
        MEMORY_FILE,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            memory,
            f,
            indent=2
        )


# ============================================================
# PAPER STATE
# ============================================================

def default_state():

    return {
        "cash": INITIAL_BALANCE,
        "doge": 0.0,
        "entry_price": None,
        "entry_cost": None
    }


def load_state():

    if not os.path.exists(
        STATE_FILE
    ):

        return default_state()

    try:

        with open(
            STATE_FILE,
            "r",
            encoding="utf-8"
        ) as f:

            return json.load(f)

    except Exception:

        return default_state()


def save_state(state):

    with open(
        STATE_FILE,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            state,
            f,
            indent=2
        )


# ============================================================
# AI DECISION
# ============================================================

def analyze(candles, memory):

    if len(candles) < 50:

        return (
            "HOLD",
            0.50,
            {}
        )

    closes = [
        c["close"]
        for c in candles
    ]

    volumes = [
        c["volume"]
        for c in candles
    ]

    price = closes[-1]

    ema20 = ema(
        closes,
        20
    )

    ema50 = ema(
        closes,
        50
    )

    current_rsi = rsi(
        closes,
        14
    )

    momentum = 0.0

    if closes[-6] != 0:

        momentum = (
            (
                price
                - closes[-6]
            )
            / closes[-6]
        )

    volume_change = 0.0

    if volumes[-2] != 0:

        volume_change = (
            (
                volumes[-1]
                - volumes[-2]
            )
            / volumes[-2]
        )

    vol = volatility(
        candles
    )

    score = 0.50

    reasons = []

    # Trend
    if ema20 > ema50:

        score += 0.15

        reasons.append(
            "EMA20 > EMA50"
        )

    else:

        score -= 0.15

        reasons.append(
            "EMA20 < EMA50"
        )

    # RSI
    if current_rsi < 30:

        score += 0.10

        reasons.append(
            "RSI oversold"
        )

    elif (
        current_rsi >= 45
        and current_rsi <= 65
    ):

        score += 0.10

        reasons.append(
            "RSI sehat"
        )

    elif current_rsi > 75:

        score -= 0.15

        reasons.append(
            "RSI tinggi"
        )

    # Momentum
    if momentum > 0:

        score += 0.10

        reasons.append(
            "Momentum positif"
        )

    else:

        score -= 0.10

        reasons.append(
            "Momentum negatif"
        )

    # Volume
    if volume_change > 0:

        score += 0.05

        reasons.append(
            "Volume meningkat"
        )

    # Volatility
    if vol > 0.002:

        score += 0.02

        reasons.append(
            "Volatilitas cukup"
        )

    score = max(
        0.0,
        min(1.0, score)
    )

    buy_threshold = float(
        memory.get(
            "buy_threshold",
            BUY_THRESHOLD
        )
    )

    sell_threshold = float(
        memory.get(
            "sell_threshold",
            SELL_THRESHOLD
        )
    )

    if score >= buy_threshold:

        signal = "BUY"

    elif score <= sell_threshold:

        signal = "SELL"

    else:

        signal = "HOLD"

    indicators = {

        "price": price,

        "ema20": ema20,

        "ema50": ema50,

        "rsi": current_rsi,

        "momentum": momentum,

        "volume_change":
            volume_change,

        "volatility":
            vol,

        "reasons":
            reasons
    }

    return (
        signal,
        score,
        indicators
    )


# ============================================================
# LOCAL LEARNING
# ============================================================

def learn(memory, profit):

    # Profit
    if profit > 0:

        memory["wins"] += 1

    else:

        memory["losses"] += 1

    memory["total_profit"] += profit

    recent = memory["trades"][-3:]

    recent_losses = 0

    for trade in recent:

        if trade["profit"] < 0:
            recent_losses += 1

    # Jika 3 trade terakhir rugi,
    # AI menjadi lebih selektif.

    if recent_losses >= 3:

        old_threshold = float(
            memory.get(
                "buy_threshold",
                BUY_THRESHOLD
            )
        )

        new_threshold = min(
            0.80,
            old_threshold + 0.03
        )

        memory[
            "buy_threshold"
        ] = new_threshold

        log(
            "LEARNING: 3 loss berturut-turut. "
            f"BUY threshold "
            f"{old_threshold:.2f} -> "
            f"{new_threshold:.2f}"
        )

    # Jika beberapa trade terakhir
    # menguntungkan, sedikit lebih agresif.

    elif len(recent) >= 3:

        recent_profit = sum(
            t["profit"]
            for t in recent
        )

        if recent_profit > 0:

            old_threshold = float(
                memory.get(
                    "buy_threshold",
                    BUY_THRESHOLD
                )
            )

            new_threshold = max(
                0.60,
                old_threshold - 0.01
            )

            memory[
                "buy_threshold"
            ] = new_threshold

            log(
                "LEARNING: hasil positif. "
                f"BUY threshold "
                f"{old_threshold:.2f} -> "
                f"{new_threshold:.2f}"
            )


# ============================================================
# PAPER BUY
# ============================================================

def paper_buy(
    state,
    price,
    score,
    indicators
):

    if state["cash"] <= 0:
        return

    fee = (
        state["cash"]
        * FEE_RATE
    )

    usable = (
        state["cash"]
        - fee
    )

    doge = (
        usable
        / price
    )

    state["doge"] = doge

    state["entry_price"] = price

    state["entry_cost"] = (
        state["cash"]
    )

    state["cash"] = 0.0

    save_state(state)

    log(
        f"PAPER BUY | "
        f"{COIN_NAME} | "
        f"Price Rp{price:,.0f} | "
        f"Score {score * 100:.2f}%"
    )


# ============================================================
# PAPER SELL
# ============================================================

def paper_sell(
    state,
    memory,
    price,
    score,
    indicators
):

    if state["doge"] <= 0:
        return

    gross = (
        state["doge"]
        * price
    )

    fee = (
        gross
        * FEE_RATE
    )

    final_cash = (
        gross
        - fee
    )

    profit = (
        final_cash
        - state["entry_cost"]
    )

    trade = {

        "time":
            datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S"
            ),

        "coin":
            COIN_NAME,

        "entry":
            state["entry_price"],

        "exit":
            price,

        "profit":
            profit,

        "score":
            score,

        "rsi":
            indicators["rsi"],

        "ema20":
            indicators["ema20"],

        "ema50":
            indicators["ema50"],

        "momentum":
            indicators["momentum"]
    }

    memory["trades"].append(
        trade
    )

    learn(
        memory,
        profit
    )

    state["cash"] = (
        final_cash
    )

    state["doge"] = 0.0

    state["entry_price"] = None

    state["entry_cost"] = None

    save_memory(
        memory
    )

    save_state(
        state
    )

    log(
        f"PAPER SELL | "
        f"{COIN_NAME} | "
        f"Price Rp{price:,.0f} | "
        f"P/L Rp{profit:,.0f}"
    )


# ============================================================
# MAIN LOOP
# ============================================================

def main():

    print()
    print("=" * 60)
    print("        LOCAL AI PAPER TRADER")
    print("=" * 60)
    print(
        f"COIN           : {COIN_NAME}"
    )
    print(
        "MODE           : PAPER TRADING"
    )
    print(
        f"MODAL          : Rp{INITIAL_BALANCE:,.0f}"
    )
    print(
        "LIVE DATA      : INDODAX"
    )
    print(
        "LOCAL LEARNING : ENABLED"
    )
    print("=" * 60)
    print()

    memory = load_memory()

    state = load_state()

    candles = load_candles()

    last_price = None

    while True:

        try:

            ticker = get_ticker()

            if ticker is None:

                time.sleep(
                    POLL_SECONDS
                )

                continue

            price = ticker["last"]

            timestamp = ticker[
                "timestamp"
            ]

            # Simpan candle sederhana
            # setiap polling.

            candle = {

                "timestamp":
                    timestamp,

                "open":
                    price,

                "high":
                    ticker["high"],

                "low":
                    ticker["low"],

                "close":
                    price,

                "volume":
                    ticker["volume"]
            }

            # Hindari duplikat timestamp.

            if (
                not candles
                or candles[-1]["timestamp"]
                != timestamp
            ):

                save_candle(
                    candle
                )

                candles.append(
                    candle
                )

                # Batasi memory RAM.

                if len(candles) > 1000:

                    candles = candles[-1000:]

            # ==========================================
            # ANALYZE
            # ==========================================

            signal, score, indicators = (
                analyze(
                    candles,
                    memory
                )
            )

            print()
            print("-" * 60)

            print(
                datetime.now().strftime(
                    "%Y-%m-%d %H:%M:%S"
                )
            )

            print(
                f"PRICE       : Rp{price:,.0f}"
            )

            if indicators:

                print(
                    f"EMA20       : "
                    f"{indicators['ema20']:.8f}"
                )

                print(
                    f"EMA50       : "
                    f"{indicators['ema50']:.8f}"
                )

                print(
                    f"RSI         : "
                    f"{indicators['rsi']:.2f}"
                )

                print(
                    f"MOMENTUM    : "
                    f"{indicators['momentum'] * 100:.3f}%"
                )

                print(
                    f"VOLATILITY  : "
                    f"{indicators['volatility'] * 100:.3f}%"
                )

            print(
                f"AI SCORE    : "
                f"{score * 100:.2f}%"
            )

            print(
                f"DECISION    : {signal}"
            )

            print(
                f"CASH        : "
                f"Rp{state['cash']:,.0f}"
            )

            print(
                f"DOGE        : "
                f"{state['doge']:.4f}"
            )

            if state["entry_price"]:

                change = (
                    (
                        price
                        - state["entry_price"]
                    )
                    / state["entry_price"]
                )

                print(
                    f"POSITION    : "
                    f"{change * 100:.3f}%"
                )

            # ==========================================
            # BUY
            # ==========================================

            if (
                signal == "BUY"
                and state["doge"] == 0
            ):

                paper_buy(
                    state,
                    price,
                    score,
                    indicators
                )

            # ==========================================
            # POSITION
            # ==========================================

            elif state["doge"] > 0:

                change = (
                    (
                        price
                        - state["entry_price"]
                    )
                    / state["entry_price"]
                )

                if (
                    change >= TAKE_PROFIT
                    or change <= -STOP_LOSS
                    or signal == "SELL"
                ):

                    paper_sell(
                        state,
                        memory,
                        price,
                        score,
                        indicators
                    )

            # ==========================================
            # STATUS
            # ==========================================

            wins = memory["wins"]

            losses = memory["losses"]

            total_trades = (
                wins + losses
            )

            win_rate = 0.0

            if total_trades > 0:

                win_rate = (
                    wins
                    / total_trades
                    * 100
                )

            print(
                f"TRADES      : "
                f"{total_trades}"
            )

            print(
                f"WIN RATE    : "
                f"{win_rate:.2f}%"
            )

            print(
                f"TOTAL P/L   : "
                f"Rp{memory['total_profit']:,.0f}"
            )

            # Checkpoint otomatis.

            save_memory(
                memory
            )

            save_state(
                state
            )

            last_price = price

            time.sleep(
                POLL_SECONDS
            )

        except KeyboardInterrupt:

            print()
            print(
                "Bot dihentikan."
            )

            save_memory(
                memory
            )

            save_state(
                state
            )

            break

        except Exception as e:

            log(
                f"MAIN LOOP ERROR: {e}"
            )

            save_memory(
                memory
            )

            save_state(
                state
            )

            time.sleep(
                POLL_SECONDS
            )


# ============================================================
# START
# ============================================================

if __name__ == "__main__":

    main()
