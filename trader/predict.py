import csv
import json
import math

MODEL_FILE = "models/model.json"
DATA_FILE = "data/ai_dataset.csv"


def sigmoid(x):
    if x < -50:
        return 0.0

    if x > 50:
        return 1.0

    return 1 / (1 + math.exp(-x))


def load_model():
    with open(MODEL_FILE, "r") as f:
        return json.load(f)


def load_latest():
    with open(DATA_FILE, "r") as f:
        rows = list(csv.DictReader(f))

    if not rows:
        return None

    return rows[-1]


def predict(model, row):

    features = model["features"]
    weights = model["weights"]
    bias = model["bias"]
    means = model["means"]
    stds = model["stds"]

    values = []

    for name in features:
        value = float(row[name])

        index = features.index(name)

        normalized = (
            (value - means[index])
            / stds[index]
        )

        values.append(normalized)

    z = bias

    for i in range(len(values)):
        z += weights[i] * values[i]

    probability_up = sigmoid(z)

    return probability_up


def main():

    print("================================")
    print("       LOCAL AI ANALYSIS")
    print("================================")

    model = load_model()
    row = load_latest()

    if row is None:
        print("Dataset kosong.")
        return

    probability = predict(model, row)

    up = probability * 100
    down = (1 - probability) * 100

    print()
    print("BTC/IDR")
    print(
        "Harga : Rp"
        + f"{float(row['close']):,.0f}"
    )

    print()
    print("INDICATORS")
    print(
        "EMA20 : "
        + f"{float(row['ema20']):,.2f}"
    )

    print(
        "EMA50 : "
        + f"{float(row['ema50']):,.2f}"
    )

    print(
        "RSI14 : "
        + f"{float(row['rsi14']):.2f}"
    )

    print()
    print("AI PROBABILITY")
    print(
        f"UP    : {up:.2f}%"
    )

    print(
        f"DOWN  : {down:.2f}%"
    )

    if probability >= 0.60:
        decision = "BUY"

    elif probability <= 0.40:
        decision = "SELL"

    else:
        decision = "HOLD"

    print()
    print(
        "AI Decision : "
        + decision
    )

    print(
        "Confidence  : "
        + f"{max(up, down):.2f}%"
    )

    print()
    print("Mode : PAPER TRADING")
    print()


if __name__ == "__main__":
    main()
