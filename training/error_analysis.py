import csv
import json
from collections import Counter
from pathlib import Path

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
)
from sklearn.model_selection import (
    StratifiedGroupKFold,
    cross_val_predict,
)
from sklearn.pipeline import Pipeline


DATASET_PATH = Path(
    "data/annotated/customer_support_intents.json"
)

OUTPUT_DIR = Path("artifacts/error_analysis")

RANDOM_STATE = 42
TEST_SIZE = 0.25
CV_FOLDS = 3

C_VALUE = 10.0
NGRAM_MAX = 1


def load_dataset(path: Path):
    with path.open(
        "r",
        encoding="utf-8",
    ) as file:
        return json.load(file)


def split_scenarios(records):
    """
    Use the frozen final-test scenarios from dataset-v0.2.

    New dataset-v0.3 scenarios are development-only.
    """

    manifest_path = Path(
        "data/splits/dataset_v0.2_split.json"
    )

    with manifest_path.open(
        "r",
        encoding="utf-8",
    ) as file:
        manifest = json.load(file)

    final_test_scenarios = set(
        manifest["final_test_scenarios"]
    )

    dataset_scenarios = {
        record["scenario_id"]
        for record in records
    }

    missing = (
        final_test_scenarios
        - dataset_scenarios
    )

    if missing:
        raise ValueError(
            "Frozen final-test scenarios are missing: "
            f"{sorted(missing)}"
        )

    dev_records = [
        record
        for record in records
        if record["scenario_id"]
        not in final_test_scenarios
    ]

    test_records = [
        record
        for record in records
        if record["scenario_id"]
        in final_test_scenarios
    ]

    return dev_records, test_records

def build_model():
    return Pipeline(
        [
            (
                "tfidf",
                TfidfVectorizer(
                    ngram_range=(1, NGRAM_MAX),
                ),
            ),
            (
                "classifier",
                LogisticRegression(
                    C=C_VALUE,
                    max_iter=1000,
                    random_state=RANDOM_STATE,
                ),
            ),
        ]
    )


def save_confusion_matrix(
    labels,
    matrix,
):
    path = OUTPUT_DIR / "confusion_matrix.csv"

    with path.open(
        "w",
        encoding="utf-8",
        newline="",
    ) as file:
        writer = csv.writer(file)

        writer.writerow(
            ["true_intent"] + labels
        )

        for label, row in zip(
            labels,
            matrix,
        ):
            writer.writerow(
                [label] + list(row)
            )


def save_misclassified(
    records,
    predictions,
):
    path = OUTPUT_DIR / "misclassified_examples.csv"

    fieldnames = [
        "id",
        "scenario_id",
        "language",
        "domain",
        "text",
        "true_intent",
        "predicted_intent",
    ]

    mistakes = []

    for record, prediction in zip(
        records,
        predictions,
    ):
        if record["intent"] != prediction:
            mistakes.append(
                {
                    "id": record["id"],
                    "scenario_id": record["scenario_id"],
                    "language": record["language"],
                    "domain": record["domain"],
                    "text": record["text"],
                    "true_intent": record["intent"],
                    "predicted_intent": prediction,
                }
            )

    with path.open(
        "w",
        encoding="utf-8-sig",
        newline="",
    ) as file:
        writer = csv.DictWriter(
            file,
            fieldnames=fieldnames,
        )

        writer.writeheader()
        writer.writerows(mistakes)

    return mistakes


def save_error_pairs(mistakes):
    path = OUTPUT_DIR / "error_pairs.csv"

    pairs = Counter(
        (
            item["true_intent"],
            item["predicted_intent"],
        )
        for item in mistakes
    )

    with path.open(
        "w",
        encoding="utf-8",
        newline="",
    ) as file:
        writer = csv.writer(file)

        writer.writerow(
            [
                "true_intent",
                "predicted_intent",
                "count",
            ]
        )

        for (
            true_intent,
            predicted_intent,
        ), count in pairs.most_common():
            writer.writerow(
                [
                    true_intent,
                    predicted_intent,
                    count,
                ]
            )

    return pairs


def main():
    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    records = load_dataset(
        DATASET_PATH
    )

    dev_records, test_records = split_scenarios(
        records
    )

    x_dev = [
        record["text"]
        for record in dev_records
    ]

    y_dev = [
        record["intent"]
        for record in dev_records
    ]

    groups = [
        record["scenario_id"]
        for record in dev_records
    ]

    model = build_model()

    cv = StratifiedGroupKFold(
        n_splits=CV_FOLDS,
        shuffle=True,
        random_state=RANDOM_STATE,
    )

    print(
        "Generating out-of-fold predictions "
        "on development data..."
    )

    predictions = cross_val_predict(
        model,
        x_dev,
        y_dev,
        groups=groups,
        cv=cv,
        method="predict",
    )

    accuracy = accuracy_score(
        y_dev,
        predictions,
    )

    macro_f1 = f1_score(
        y_dev,
        predictions,
        average="macro",
    )

    weighted_f1 = f1_score(
        y_dev,
        predictions,
        average="weighted",
    )

    labels = sorted(set(y_dev))

    matrix = confusion_matrix(
        y_dev,
        predictions,
        labels=labels,
    )

    save_confusion_matrix(
        labels,
        matrix,
    )

    mistakes = save_misclassified(
        dev_records,
        predictions,
    )

    pairs = save_error_pairs(
        mistakes
    )

    metrics = {
        "cv_accuracy": accuracy,
        "cv_macro_f1": macro_f1,
        "cv_weighted_f1": weighted_f1,
        "development_records": len(
            dev_records
        ),
        "held_out_test_records": len(
            test_records
        ),
        "misclassified_records": len(
            mistakes
        ),
    }

    with (
        OUTPUT_DIR / "metrics.json"
    ).open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            metrics,
            file,
            ensure_ascii=False,
            indent=2,
        )

    print()
    print("Development CV metrics")
    print("----------------------")
    print(
        f"Accuracy:    {accuracy:.4f}"
    )
    print(
        f"Macro F1:    {macro_f1:.4f}"
    )
    print(
        f"Weighted F1: {weighted_f1:.4f}"
    )

    print()
    print(
        "Misclassified records:",
        len(mistakes),
    )

    print()
    print("Most common error pairs")
    print("-----------------------")

    for (
        true_intent,
        predicted_intent,
    ), count in pairs.most_common():
        print(
            f"{true_intent}"
            f" -> "
            f"{predicted_intent}: "
            f"{count}"
        )

    print()
    print(
        "Final test records were NOT used "
        "for error analysis:",
        len(test_records),
    )

    print()
    print(
        f"Artifacts saved to: {OUTPUT_DIR}"
    )


if __name__ == "__main__":
    main()
