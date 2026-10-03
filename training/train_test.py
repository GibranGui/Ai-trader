import csv
import json
import math
import os
import random

DATA_FILE = "data/ai_dataset.csv"
MODEL_FILE = "models/model_test.json"

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
                rows.append({
                    "features": [
                        float(row[name])
                        for name in FEATURES
                    ],
                    "target": int(row["target"])
                })
            except:
                pass

    return rows


def calculate_normalization(data):
    n = len(FEATURES)

    means = [0.0] * n
    stds = [0.0] * n

    for row in data:
        for i in range(n):
            means[i] += row["features"][i]

    for i in range(n):
        means[i] /= len(data)

    for row in data:
        for i in range(n):
            diff = row["features"][i] - means[i]
            stds[i] += diff * diff

    for i in range(n):
        stds[i] = math.sqrt(stds[i] / len(data))

        if stds[i] == 0:
            stds[i] = 1.0

    return means, stds


def normalize(data, means, stds):
    result = []

    for row in data:

        values = []

        for i in range(len(FEATURES)):
            values.append(
                (row["features"][i] - means[i])
                / stds[i]
            )

        result.append({
            "features": values,
            "target": row["target"]
        })

    return result


def train(data, epochs=1500, learning_rate=0.03):

    weights = [
        random.uniform(-0.01, 0.01)
        for _ in FEATURES
    ]

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
                + (1 - y)
                * math.log(1 - prediction)
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
            print(
                f"Epoch {epoch:4d} | "
                f"Loss: {total_loss / len(data):.6f}"
            )

    return weights, bias


def evaluate(data, weights, bias):

    correct = 0

    for row in data:

        z = bias

        for i in range(len(FEATURES)):
            z += (
                weights[i]
                * row["features"][i]
            )

        probability = sigmoid(z)

        prediction = (
            1 if probability >= 0.5 else 0
        )

        if prediction == row["target"]:
            correct += 1

    return correct / len(data) * 100


def main():

    print("================================")
    print("     LOCAL AI TRAIN / TEST")
    print("================================")

    data = load_data()

    print(f"Total data : {len(data)}")

    if len(data) < 60:
        print("Data minimal 60.")
        return

    split = int(len(data) * 0.8)

    train_data = data[:split]
    test_data = data[split:]

    print(f"Training   : {len(train_data)}")
    print(f"Testing    : {len(test_data)}")

    means, stds = calculate_normalization(
        train_data
    )

    train_normalized = normalize(
        train_data,
        means,
        stds
    )

    test_normalized = normalize(
        test_data,
        means,
        stds
    )

    weights, bias = train(
        train_normalized
    )

    train_accuracy = evaluate(
        train_normalized,
        weights,
        bias
    )

    test_accuracy = evaluate(
        test_normalized,
        weights,
        bias
    )

    print()
    print("==============================")
    print("RESULT")
    print("==============================")
    print(
        f"Training accuracy : "
        f"{train_accuracy:.2f}%"
    )

    print(
        f"Test accuracy     : "
        f"{test_accuracy:.2f}%"
    )

    os.makedirs("models", exist_ok=True)

    model = {
        "features": FEATURES,
        "weights": weights,
        "bias": bias,
        "means": means,
        "stds": stds
    }

    with open(MODEL_FILE, "w") as f:
        json.dump(model, f, indent=2)

    print()
    print("Model test disimpan:")
    print(MODEL_FILE)


if __name__ == "__main__":
    main()
