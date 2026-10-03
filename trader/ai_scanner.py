import csv
import json
import math
import os
import time
import urllib.request
import threading
from trader.discord_bridge import discord_bridge
from http.server import BaseHTTPRequestHandler, HTTPServer
from datetime import datetime

# ============================================================
# CONFIG
# ============================================================

INITIAL_BALANCE = 200_000.0

FEE_RATE = 0.001

SCAN_INTERVAL = 60

MAX_CANDIDATES = 10

MIN_VOLUME_IDR = 100_000_000

BUY_THRESHOLD = 0.65
SELL_THRESHOLD = 0.40

TAKE_PROFIT = 0.004
STOP_LOSS = 0.003

DATA_DIR = "data"

STATE_FILE = os.path.join(
    DATA_DIR,
    "ai_state.json"
)

MEMORY_FILE = os.path.join(
    DATA_DIR,
    "ai_memory.json"
)

LOG_FILE = os.path.join(
    DATA_DIR,
    "ai_trader.log"
)

os.makedirs(DATA_DIR, exist_ok=True)


# ============================================================
# LOG
# ============================================================

def log(message):

    text = (
        f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] "
        f"{message}"
    )

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
                "User-Agent":
                "Local-AI-Paper-Trader/1.0"
            }
        )

        with urllib.request.urlopen(
            request,
            timeout=15
        ) as response:

            return json.loads(
                response.read().decode()
            )

    except Exception as e:

        log(
            f"Network error: {e}"
        )

        return None


# ============================================================
# ALL TICKERS
# ============================================================

def get_all_tickers():

    url = (
        "https://indodax.com/api/tickers"
    )

    data = get_json(url)

    if not data:
        return {}

    return data.get(
        "tickers",
        {}
    )


# ============================================================
# INDIVIDUAL MARKET
# ============================================================

def get_market(pair):

    url = (
        "https://indodax.com/api/ticker/"
        + pair
    )

    data = get_json(url)

    if not data:
        return None

    return data.get(
        "ticker"
    )


# ============================================================
# SCANNER
# ============================================================

def scan_markets():

    tickers = get_all_tickers()

    candidates = []

    for pair, ticker in tickers.items():

        if not pair.endswith("_idr"):
            continue

        try:

            price = float(
                ticker.get(
                    "last",
                    0
                )
            )

            high = float(
                ticker.get(
                    "high",
                    0
                )
            )

            low = float(
                ticker.get(
                    "low",
                    0
                )
            )

            volume = float(
                ticker.get(
                    "vol_idr",
                    0
                )
            )

        except Exception:

            continue

        if price <= 0:
            continue

        if volume < MIN_VOLUME_IDR:
            continue

        if high <= low:
            continue

        volatility = (
            high - low
        ) / low

        position = (
            price - low
        ) / (
            high - low
        )

        volume_score = min(
            volume / 10_000_000,
            100
        )

        momentum_score = (
            position * 100
        )

        volatility_score = min(
            volatility * 1000,
            100
        )

        scan_score = (
            momentum_score * 0.40
            + volatility_score * 0.30
            + volume_score * 0.30
        )

        candidates.append({

            "pair": pair,

            "price": price,

            "volume": volume,

            "high": high,

            "low": low,

            "volatility": volatility,

            "scan_score": scan_score
        })

    candidates.sort(
        key=lambda x:
        x["scan_score"],
        reverse=True
    )

    return candidates[
        :MAX_CANDIDATES
    ]


# ============================================================
# HISTORICAL DATA
# ============================================================

def get_history(pair):

    url = (
        "https://indodax.com/api/"
        "pair/"
        + pair
        + "/ticker"
    )

    # Fallback: gunakan ticker
    # jika endpoint history tidak tersedia.

    data = get_json(url)

    if data and "ticker" in data:

        ticker = data["ticker"]

        try:

            price = float(
                ticker["last"]
            )

            return [
                price
            ] * 60

        except Exception:

            pass

    return []


# ============================================================
# EMA
# ============================================================

def ema(values, period):

    if len(values) < period:
        return None

    result = sum(
        values[:period]
    ) / period

    multiplier = (
        2 / (period + 1)
    )

    for value in values[period:]:

        result = (
            (value - result)
            * multiplier
            + result
        )

    return result


# ============================================================
# RSI
# ============================================================

def calculate_rsi(
    values,
    period=14
):

    if len(values) <= period:
        return None

    gains = []
    losses = []

    for i in range(
        1,
        len(values)
    ):

        change = (
            values[i]
            - values[i - 1]
        )

        if change > 0:

            gains.append(change)
            losses.append(0)

        else:

            gains.append(0)
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
                avg_gain
                * (period - 1)
            )
            + gains[i]
        ) / period

        avg_loss = (
            (
                avg_loss
                * (period - 1)
            )
            + losses[i]
        ) / period

    if avg_loss == 0:
        return 100.0

    rs = (
        avg_gain
        / avg_loss
    )

    return (
        100
        - 100 / (1 + rs)
    )


# ============================================================
# MEMORY
# ============================================================

def default_memory():

    return {

        "trades": [],

        "wins": 0,

        "losses": 0,

        "total_profit": 0.0,

        "buy_threshold":
            BUY_THRESHOLD,

        "sell_threshold":
            SELL_THRESHOLD
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

            return json.load(f)

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
# STATE
# ============================================================

def default_state():

    return {

        "cash":
            INITIAL_BALANCE,

        "coin":
            0.0,

        "pair":
            None,

        "entry_price":
            None,

        "entry_cost":
            None
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
# AI ANALYSIS
# ============================================================

def analyze(
    candidate,
    memory
):

    price = candidate["price"]

    high = candidate["high"]

    low = candidate["low"]

    volatility = candidate[
        "volatility"
    ]

    volume = candidate[
        "volume"
    ]

    position = 0.5

    if high > low:

        position = (
            price - low
        ) / (
            high - low
        )

    score = 0.50

    reasons = []

    # ==========================================
    # PRICE POSITION
    # ==========================================

    if position >= 0.60:

        score += 0.10

        reasons.append(
            "harga dekat high"
        )

    elif position <= 0.30:

        score -= 0.05

        reasons.append(
            "harga dekat low"
        )

    # ==========================================
    # VOLUME
    # ==========================================

    if volume >= 1_000_000_000:

        score += 0.10

        reasons.append(
            "volume tinggi"
        )

    elif volume >= 500_000_000:

        score += 0.05

        reasons.append(
            "volume cukup"
        )

    # ==========================================
    # VOLATILITY
    # ==========================================

    if (
        volatility >= 0.02
        and volatility <= 0.15
    ):

        score += 0.10

        reasons.append(
            "volatilitas aktif"
        )

    elif volatility > 0.20:

        score -= 0.10

        reasons.append(
            "volatilitas terlalu tinggi"
        )

    # ==========================================
    # SCANNER SCORE
    # ==========================================

    scanner_score = (
        candidate["scan_score"]
        / 100
    )

    score += (
        scanner_score
        * 0.10
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

    return (
        signal,
        score,
        reasons
    )


# ============================================================
# BUY
# ============================================================

def paper_buy(
    state,
    candidate,
    score
):

    price = candidate["price"]

    pair = candidate["pair"]

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

    amount = (
        usable
        / price
    )

    state["coin"] = amount

    state["pair"] = pair

    state["entry_price"] = price

    state["entry_cost"] = (
        state["cash"]
    )

    state["cash"] = 0.0

    save_state(
        state
    )

    # ==========================================
    # DISCORD - OPEN ORDER
    # ==========================================

    discord_bridge.order(
        "BUY",
        pair,
        price,
        score,
        [
            "AI BUY signal",
            f"Entry score {score * 100:.2f}%"
        ]
    )

    discord_bridge.sync_state()

    log(
        f"PAPER BUY | "
        f"{pair.upper()} | "
        f"Rp{price:,.8f} | "
        f"Score {score * 100:.2f}%"
    )


# ============================================================
# SELL
# ============================================================

def paper_sell(
    state,
    memory,
    candidate,
    score
):

    price = candidate["price"]

    pair = state["pair"]

    if state["coin"] <= 0:
        return

    gross = (
        state["coin"]
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

        "pair":
            pair,

        "entry":
            state["entry_price"],

        "exit":
            price,

        "profit":
            profit,

        "score":
            score
    }

    memory[
        "trades"
    ].append(
        trade
    )

    if profit > 0:

        memory["wins"] += 1

    else:

        memory["losses"] += 1

    memory[
        "total_profit"
    ] += profit

    # ==========================================
    # LOCAL LEARNING
    # ==========================================

    recent = memory[
        "trades"
    ][-3:]

    recent_losses = 0

    for trade in recent:

        if trade["profit"] < 0:

            recent_losses += 1

    if recent_losses >= 3:

        old = float(
            memory.get(
                "buy_threshold",
                BUY_THRESHOLD
            )
        )

        memory[
            "buy_threshold"
        ] = min(
            0.80,
            old + 0.03
        )

        log(
            "LEARNING: "
            "3 loss berturut-turut. "
            f"threshold {old:.2f} -> "
            f"{memory['buy_threshold']:.2f}"
        )

    elif len(recent) >= 3:

        recent_profit = sum(
            x["profit"]
            for x in recent
        )

        if recent_profit > 0:

            old = float(
                memory.get(
                    "buy_threshold",
                    BUY_THRESHOLD
                )
            )

            memory[
                "buy_threshold"
            ] = max(
                0.60,
                old - 0.01
            )

            log(
                "LEARNING: "
                f"threshold {old:.2f} -> "
                f"{memory['buy_threshold']:.2f}"
            )

    state["cash"] = final_cash

    state["coin"] = 0.0

    state["pair"] = None

    state["entry_price"] = None

    state["entry_cost"] = None

    save_state(
        state
    )

    save_memory(
        memory
    )

    # ==========================================
    # DISCORD - CLOSE ORDER
    # ==========================================

    discord_bridge.order(
        "SELL",
        pair,
        price,
        score,
        [
            f"Profit/Loss Rp{profit:,.0f}",
            f"AI score {score * 100:.2f}%"
        ]
    )

    # Simpan learning terbaru ke Discord
    discord_bridge.sync_memory()

    # Simpan state terbaru ke Discord
    discord_bridge.sync_state()

    log(
        f"PAPER SELL | "
        f"{pair.upper()} | "
        f"Rp{price:,.8f} | "
        f"P/L Rp{profit:,.0f}"
    )

# ============================================================
# KOYEB HEALTH CHECK
# ============================================================

PORT = int(os.environ.get("PORT", 8000))


class HealthHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()
        self.wfile.write(b"OK")

    def log_message(self, format, *args):
        return


def start_health_server():

    server = HTTPServer(
        ("0.0.0.0", PORT),
        HealthHandler
    )

    server.serve_forever()

# ============================================================
# MAIN
# ============================================================

def main():

    health_thread = threading.Thread(
        target=start_health_server,
        daemon=True
    )

    health_thread.start()

    # ==========================================
    # DISCORD BRIDGE
    # ==========================================

    print()
    print("Menghubungkan Discord...")

    discord_bridge.start()

    print("Discord bridge siap.")

    print()
    print("=" * 60)
    print("          LOCAL AI CRYPTO TRADER")
    print("=" * 60)
    print(
        "MODE           : PAPER TRADING"
    )
    print(
        "MODAL          : Rp200,000"
    )
    print(
        "MARKET         : INDODAX IDR"
    )
    print(
        "LOCAL LEARNING : ENABLED"
    )
    print(
        "REAL ORDER     : DISABLED"
    )
    print("=" * 60)

    memory = load_memory()

    state = load_state()

    while True:

        try:

            # ======================================
            # SCAN
            # ======================================

            candidates = scan_markets()

            if not candidates:

                log(
                    "Tidak ada kandidat."
                )

                time.sleep(
                    SCAN_INTERVAL
                )

                continue

            print()
            print(
                "=" * 60
            )

            print(
                "TOP CANDIDATES"
            )

            print(
                "-" * 60
            )

            # ======================================
            # ANALYZE TOP CANDIDATES
            # ======================================

            analyses = []

            for candidate in candidates:

                signal, score, reasons = (
                    analyze(
                        candidate,
                        memory
                    )
                )

                candidate = dict(
                    candidate
                )

                candidate[
                    "signal"
                ] = signal

                candidate[
                    "ai_score"
                ] = score

                candidate[
                    "reasons"
                ] = reasons

                analyses.append(
                    candidate
                )

                print(
                    f"{candidate['pair'].upper():15s} "
                    f"AI {score * 100:6.2f}% "
                    f"{signal:5s} "
                    f"Vol Rp"
                    f"{candidate['volume']:,.0f}"
                )

            # ======================================
            # POSITION EXISTS
            # ======================================

            if state["coin"] > 0:

                current = None

                for candidate in analyses:

                    if (
                        candidate["pair"]
                        == state["pair"]
                    ):

                        current = candidate
                        break

                if current:

                    price = current[
                        "price"
                    ]

                    change = (
                        price
                        - state[
                            "entry_price"
                        ]
                    ) / state[
                        "entry_price"
                    ]

                    print()
                    print(
                        f"POSITION : "
                        f"{state['pair'].upper()}"
                    )

                    print(
                        f"RETURN   : "
                        f"{change * 100:.3f}%"
                    )

                    should_sell = (

                        change
                        >= TAKE_PROFIT

                        or

                        change
                        <= -STOP_LOSS

                        or

                        current["signal"]
                        == "SELL"
                    )

                    if should_sell:

                        paper_sell(
                            state,
                            memory,
                            current,
                            current[
                                "ai_score"
                            ]
                        )

            # ======================================
            # NO POSITION
            # ======================================

            elif state["cash"] > 0:

                buy_candidates = [

                    x for x in analyses

                    if x["signal"] == "BUY"

                ]

                if buy_candidates:

                    buy_candidates.sort(
                        key=lambda x:
                        x["ai_score"],
                        reverse=True
                    )

                    selected = (
                        buy_candidates[0]
                    )

                    print()
                    print(
                        "AI SELECTED:"
                    )

                    print(
                        f"{selected['pair'].upper()}"
                    )

                    print(
                        f"Score: "
                        f"{selected['ai_score'] * 100:.2f}%"
                    )

                    print(
                        "Reason:"
                    )

                    for reason in selected[
                        "reasons"
                    ]:

                        print(
                            f"- {reason}"
                        )

                    paper_buy(
                        state,
                        selected,
                        selected[
                            "ai_score"
                        ]
                    )

                else:

                    print()
                    print(
                        "AI: "
                        "belum menemukan "
                        "setup BUY."
                    )

            # ======================================
            # STATUS
            # ======================================

            total_trades = (
                memory["wins"]
                + memory["losses"]
            )

            win_rate = 0.0

            if total_trades:

                win_rate = (
                    memory["wins"]
                    / total_trades
                    * 100
                )

            print()
            print(
                "-" * 60
            )

            print(
                f"CASH       : "
                f"Rp{state['cash']:,.0f}"
            )

            print(
                f"POSITION   : "
                f"{state['pair'] or 'NONE'}"
            )

            print(
                f"TRADES     : "
                f"{total_trades}"
            )

            print(
                f"WIN RATE   : "
                f"{win_rate:.2f}%"
            )

            print(
                f"TOTAL P/L  : "
                f"Rp{memory['total_profit']:,.0f}"
            )

            print(
                f"BUY LEVEL  : "
                f"{memory['buy_threshold']:.2f}"
            )

            # Auto save

            save_memory(
                memory
            )

            save_state(
                state
            )

            print()
            print(
                f"Scan berikutnya "
                f"dalam {SCAN_INTERVAL} detik..."
            )

            time.sleep(
                SCAN_INTERVAL
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
                f"ERROR: {e}"
            )

            save_memory(
                memory
            )

            save_state(
                state
            )

            time.sleep(
                SCAN_INTERVAL
            )


# ============================================================
# START
# ============================================================

if __name__ == "__main__":
    main()
