import csv
import math
import json
import os
import random

DATA_FILE = "data/ai_dataset.csv"
MODEL_FILE = "models/model.json"

FEATURES = [
    "ema20",
    "ema50",
    "rsi14",
    "momentum",
    "volatility",
    "volume_change"
]


def sigmoid(x):
    if x < -50:
        return 0.0

    if x > 50:
        return 1.0

    return 1 / (1 + math.exp(-x))


def load_data():
    rows = []

    with open(DATA_FILE, "r") as f:
        reader = csv.DictReader(f)

        for row in reader:
            try:
                values = [float(row[name]) for name in FEATURES]
                target = int(row["target"])

                rows.append({
                    "features": values,
                    "target": target
                })

            except (ValueError, KeyError):
                continue

    return rows


def normalize(data):
    count = len(data[0]["features"])
    means = [0.0] * count
    stds = [0.0] * count

    for row in data:
        for i, value in enumerate(row["features"]):
            means[i] += value

    for i in range(count):
        means[i] /= len(data)

    for row in data:
        for i, value in enumerate(row["features"]):
            diff = value - means[i]
            stds[i] += diff * diff

    for i in range(count):
        stds[i] = math.sqrt(stds[i] / len(data))

        if stds[i] == 0:
            stds[i] = 1.0

    normalized = []

    for row in data:
        values = []

        for i, value in enumerate(row["features"]):
            values.append(
                (value - means[i]) / stds[i]
            )

        normalized.append({
            "features": values,
            "target": row["target"]
        })

    return normalized, means, stds


def train(data, epochs=1500, learning_rate=0.03):

    weights = [random.uniform(-0.01, 0.01)
               for _ in FEATURES]

    bias = 0.0

    for epoch in range(epochs):

        total_loss = 0.0

        for row in data:

            x = row["features"]
            y = row["target"]

            z = bias

            for i in range(len(x)):
                z += weights[i] * x[i]

            prediction = sigmoid(z)

            prediction = min(
                max(prediction, 1e-7),
                1 - 1e-7
            )

            loss = -(
                y * math.log(prediction)
                + (1 - y) * math.log(1 - prediction)
            )

            total_loss += loss

            error = prediction - y

            for i in range(len(weights)):
                weights[i] -= (
                    learning_rate
                    * error
                    * x[i]
                )

            bias -= learning_rate * error

        if epoch % 300 == 0:
            average_loss = total_loss / len(data)

            print(
                f"Epoch {epoch:4d} | "
                f"Loss: {average_loss:.6f}"
            )

    return weights, bias


def accuracy(data, weights, bias):

    correct = 0

    for row in data:

        z = bias

        for i, value in enumerate(row["features"]):
            z += weights[i] * value

        probability = sigmoid(z)

        prediction = 1 if probability >= 0.5 else 0

        if prediction == row["target"]:
            correct += 1

    return correct / len(data) * 100


def save_model(weights, bias, means, stds, accuracy_value):

    os.makedirs("models", exist_ok=True)

    model = {
        "features": FEATURES,
        "weights": weights,
        "bias": bias,
        "means": means,
        "stds": stds,
        "accuracy": accuracy_value
    }

    with open(MODEL_FILE, "w") as f:
        json.dump(model, f, indent=2)

    print()
    print("Model disimpan:")
    print(MODEL_FILE)


def main():

    print("================================")
    print("       LOCAL AI TRAINER")
    print("================================")

    data = load_data()

    print(f"Dataset : {len(data)}")

    if len(data) < 60:
        print()
        print("Data belum cukup.")
        print("Minimal 60 data diperlukan.")
        return

    random.shuffle(data)

    normalized, means, stds = normalize(data)

    weights, bias = train(normalized)

    acc = accuracy(
        normalized,
        weights,
        bias
    )

    print()
    print(f"Training accuracy : {acc:.2f}%")

    save_model(
        weights,
        bias,
        means,
        stds,
        acc
    )


if __name__ == "__main__":
    main()
