import csv
import json
import math

DATA_FILE = "data/ai_dataset.csv"
MODEL_FILE = "models/model_test.json"

INITIAL_BALANCE = 1_000_000

# Asumsi biaya simulasi.
# Bisa kita ubah nanti sesuai biaya exchange yang ingin digunakan.
FEE_RATE = 0.001

BUY_THRESHOLD = 0.60


def sigmoid(x):
    if x < -50:
        return 0.0

    if x > 50:
        return 1.0

    return 1 / (1 + math.exp(-x))


def load_model():

    with open(MODEL_FILE, "r") as f:
        return json.load(f)


def load_data():

    with open(DATA_FILE, "r") as f:
        return list(csv.DictReader(f))


def predict(model, row):

    features = model["features"]
    weights = model["weights"]
    means = model["means"]
    stds = model["stds"]
    bias = model["bias"]

    z = bias

    for i, name in enumerate(features):

        value = float(row[name])

        normalized = (
            (value - means[i])
            / stds[i]
        )

        z += weights[i] * normalized

    return sigmoid(z)


def main():

    print("================================")
    print("       LOCAL AI BACKTEST")
    print("================================")

    model = load_model()
    data = load_data()

    split = int(len(data) * 0.8)

    test_data = data[split:]

    balance = INITIAL_BALANCE

    trades = 0
    wins = 0
    losses = 0

    total_profit = 0.0

    print()
    print(f"Initial balance : Rp{balance:,.0f}")
    print(f"Test candles    : {len(test_data)}")
    print()

    for i in range(len(test_data) - 1):

        current = test_data[i]
        next_candle = test_data[i + 1]

        probability = predict(
            model,
            current
        )

        current_price = float(
            current["close"]
        )

        next_price = float(
            next_candle["close"]
        )

        # AI hanya BUY jika probabilitas
        # melewati threshold.
        if probability < BUY_THRESHOLD:
            continue

        trades += 1

        # Simulasi beli seluruh saldo.
        quantity = balance / current_price

        buy_fee = balance * FEE_RATE

        quantity_after_fee = (
            (balance - buy_fee)
            / current_price
        )

        sell_value = (
            quantity_after_fee
            * next_price
        )

        sell_fee = sell_value * FEE_RATE

        final_value = sell_value - sell_fee

        profit = final_value - balance

        balance = final_value

        total_profit += profit

        if profit > 0:
            wins += 1
        else:
            losses += 1

        print(
            f"Trade {trades:02d} | "
            f"AI {probability * 100:6.2f}% | "
            f"Entry Rp{current_price:,.0f} | "
            f"Exit Rp{next_price:,.0f} | "
            f"P/L Rp{profit:,.0f}"
        )

    print()
    print("================================")
    print("           BACKTEST RESULT")
    print("================================")

    print(
        f"Initial balance : "
        f"Rp{INITIAL_BALANCE:,.0f}"
    )

    print(
        f"Final balance   : "
        f"Rp{balance:,.0f}"
    )

    print(
        f"Net P/L         : "
        f"Rp{balance - INITIAL_BALANCE:,.0f}"
    )

    print(
        f"Trades          : {trades}"
    )

    print(
        f"Wins            : {wins}"
    )

    print(
        f"Losses          : {losses}"
    )

    if trades > 0:

        win_rate = (
            wins / trades
        ) * 100

        print(
            f"Trade win rate  : "
            f"{win_rate:.2f}%"
        )

    print()


if __name__ == "__main__":
    main()
