import csv
from collections import defaultdict
from pathlib import Path


INPUT_PATH = Path(
    "artifacts/error_analysis/"
    "misclassified_examples.csv"
)


def main():
    grouped = defaultdict(list)

    with INPUT_PATH.open(
        "r",
        encoding="utf-8-sig",
    ) as file:
        reader = csv.DictReader(file)

        for row in reader:
            key = (
                row["true_intent"],
                row["predicted_intent"],
            )

            grouped[key].append(row)

    ranked = sorted(
        grouped.items(),
        key=lambda item: len(item[1]),
        reverse=True,
    )

    for (
        true_intent,
        predicted_intent,
    ), examples in ranked[:6]:

        print()
        print("=" * 80)

        print(
            f"{true_intent} "
            f"-> "
            f"{predicted_intent}"
        )

        print(
            f"Errors: {len(examples)}"
        )

        print("=" * 80)

        for example in examples:
            print()
            print(
                f"[{example['language']}] "
                f"{example['text']}"
            )

            print(
                f"scenario: "
                f"{example['scenario_id']}"
            )


if __name__ == "__main__":
    main()
