import csv
import json
import math


DATA_FILE = "data/ai_dataset.csv"
MODEL_FILE = "models/model_test.json"


def sigmoid(x):
    if x < -50:
        return 0.0
    if x > 50:
        return 1.0
    return 1 / (1 + math.exp(-x))


with open(MODEL_FILE, "r") as f:
    model = json.load(f)

with open(DATA_FILE, "r") as f:
    data = list(csv.DictReader(f))


split = int(len(data) * 0.8)
test_data = data[split:]


print("================================")
print("      AI PREDICTION CHECK")
print("================================")

print(f"Total data : {len(data)}")
print(f"Test data  : {len(test_data)}")
print()

for i, row in enumerate(test_data):

    z = model["bias"]

    for j, name in enumerate(model["features"]):

        value = float(row[name])

        normalized = (
            (value - model["means"][j])
            / model["stds"][j]
        )

        z += model["weights"][j] * normalized

    probability = sigmoid(z)

    target = row["target"]

    print(
        f"{i+1:02d} | "
        f"AI UP: {probability * 100:6.2f}% | "
        f"Target: {target}"
    )

print()
print("================================")
