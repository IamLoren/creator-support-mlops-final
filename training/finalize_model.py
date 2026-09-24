import csv
import json
from pathlib import Path

import joblib
import mlflow
import mlflow.sklearn
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
)
from sklearn.pipeline import FeatureUnion, Pipeline
from sklearn.svm import LinearSVC


DATASET_PATH = Path(
    "data/annotated/customer_support_intents.json"
)

SPLIT_MANIFEST_PATH = Path(
    "data/splits/dataset_v0.2_split.json"
)

OUTPUT_DIR = Path(
    "artifacts/final_model"
)

TRACKING_URI = "http://127.0.0.1:5000"

EXPERIMENT_NAME = (
    "customer-support-intent-classification"
)

MODEL_NAME = (
    "customer-support-intent-classifier"
)

DATASET_VERSION = "dataset-v0.3"

RANDOM_STATE = 42


def load_json(path: Path):
    with path.open(
        "r",
        encoding="utf-8",
    ) as file:
        return json.load(file)


def split_using_frozen_test(records):
    manifest = load_json(
        SPLIT_MANIFEST_PATH
    )

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

    development_records = [
        record
        for record in records
        if record["scenario_id"]
        not in final_test_scenarios
    ]

    final_test_records = [
        record
        for record in records
        if record["scenario_id"]
        in final_test_scenarios
    ]

    return (
        development_records,
        final_test_records,
    )


def build_model():
    features = FeatureUnion(
        [
            (
                "word",
                TfidfVectorizer(
                    analyzer="word",
                    ngram_range=(1, 2),
                ),
            ),
            (
                "char",
                TfidfVectorizer(
                    analyzer="char_wb",
                    ngram_range=(3, 5),
                ),
            ),
        ]
    )

    classifier = LinearSVC(
        C=1.0,
        random_state=RANDOM_STATE,
    )

    return Pipeline(
        [
            (
                "features",
                features,
            ),
            (
                "classifier",
                classifier,
            ),
        ]
    )


def save_confusion_matrix(
    labels,
    matrix,
):
    path = (
        OUTPUT_DIR
        / "confusion_matrix.csv"
    )

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


def save_test_predictions(
    records,
    predictions,
):
    path = (
        OUTPUT_DIR
        / "final_test_predictions.csv"
    )

    fieldnames = [
        "id",
        "scenario_id",
        "language",
        "domain",
        "text",
        "true_intent",
        "predicted_intent",
        "correct",
    ]

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

        for record, prediction in zip(
            records,
            predictions,
        ):
            writer.writerow(
                {
                    "id":
                        record["id"],
                    "scenario_id":
                        record["scenario_id"],
                    "language":
                        record["language"],
                    "domain":
                        record["domain"],
                    "text":
                        record["text"],
                    "true_intent":
                        record["intent"],
                    "predicted_intent":
                        prediction,
                    "correct":
                        (
                            record["intent"]
                            == prediction
                        ),
                }
            )


def main():
    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    records = load_json(
        DATASET_PATH
    )

    (
        development_records,
        final_test_records,
    ) = split_using_frozen_test(
        records
    )

    print(
        "Development records:",
        len(development_records),
    )

    print(
        "Frozen final-test records:",
        len(final_test_records),
    )

    if len(development_records) != 180:
        raise ValueError(
            "Expected 180 development records."
        )

    if len(final_test_records) != 36:
        raise ValueError(
            "Expected 36 frozen final-test records."
        )

    x_dev = [
        record["text"]
        for record in development_records
    ]

    y_dev = [
        record["intent"]
        for record in development_records
    ]

    x_test = [
        record["text"]
        for record in final_test_records
    ]

    y_test = [
        record["intent"]
        for record in final_test_records
    ]

    print()
    print(
        "Training final model on all "
        "development data..."
    )

    model = build_model()

    model.fit(
        x_dev,
        y_dev,
    )

    print(
        "Evaluating ONCE on frozen final test..."
    )

    predictions = model.predict(
        x_test
    )

    accuracy = accuracy_score(
        y_test,
        predictions,
    )

    macro_f1 = f1_score(
        y_test,
        predictions,
        average="macro",
    )

    weighted_f1 = f1_score(
        y_test,
        predictions,
        average="weighted",
    )

    errors = sum(
        true != predicted
        for true, predicted
        in zip(
            y_test,
            predictions,
        )
    )

    report = classification_report(
        y_test,
        predictions,
        output_dict=True,
        zero_division=0,
    )

    labels = sorted(
        set(y_test)
    )

    matrix = confusion_matrix(
        y_test,
        predictions,
        labels=labels,
    )

    metrics = {
        "accuracy":
            accuracy,
        "macro_f1":
            macro_f1,
        "weighted_f1":
            weighted_f1,
        "errors":
            errors,
        "development_records":
            len(development_records),
        "final_test_records":
            len(final_test_records),
    }

    metadata = {
        "dataset_version":
            DATASET_VERSION,
        "model_type":
            "LinearSVC",
        "features":
            "word_char_tfidf",
        "word_ngram_range":
            [1, 2],
        "char_ngram_range":
            [3, 5],
        "C":
            1.0,
        "random_state":
            RANDOM_STATE,
        "selection_metric":
            "cv_macro_f1",
        "selection_cv_macro_f1":
            0.8039,
        "final_test_evaluated_once":
            True,
    }

    joblib.dump(
        model,
        OUTPUT_DIR / "model.joblib",
    )

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

    with (
        OUTPUT_DIR / "model_metadata.json"
    ).open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            metadata,
            file,
            ensure_ascii=False,
            indent=2,
        )

    with (
        OUTPUT_DIR
        / "classification_report.json"
    ).open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            report,
            file,
            ensure_ascii=False,
            indent=2,
        )

    save_confusion_matrix(
        labels,
        matrix,
    )

    save_test_predictions(
        final_test_records,
        predictions,
    )

    print()
    print("=" * 60)
    print("FINAL FROZEN TEST RESULTS")
    print("=" * 60)

    print(
        f"Accuracy:    {accuracy:.4f}"
    )
    print(
        f"Macro F1:    {macro_f1:.4f}"
    )
    print(
        f"Weighted F1: {weighted_f1:.4f}"
    )
    print(
        f"Errors:      {errors}"
    )

    mlflow.set_tracking_uri(
        TRACKING_URI
    )

    mlflow.set_experiment(
        EXPERIMENT_NAME
    )

    with mlflow.start_run(
        run_name="final-v03-word-char-linearsvc"
    ):
        mlflow.log_params(
            {
                "dataset_version":
                    DATASET_VERSION,
                "classifier":
                    "LinearSVC",
                "C":
                    1.0,
                "features":
                    "word_char_tfidf",
                "word_ngram_range":
                    "1-2",
                "char_ngram_range":
                    "3-5",
                "development_records":
                    len(development_records),
                "final_test_records":
                    len(final_test_records),
                "model_selection_metric":
                    "cv_macro_f1",
            }
        )

        mlflow.log_metrics(
            {
                "final_test_accuracy":
                    accuracy,
                "final_test_macro_f1":
                    macro_f1,
                "final_test_weighted_f1":
                    weighted_f1,
                "final_test_errors":
                    errors,
            }
        )

        mlflow.log_artifact(
            str(
                OUTPUT_DIR
                / "classification_report.json"
            )
        )

        mlflow.log_artifact(
            str(
                OUTPUT_DIR
                / "confusion_matrix.csv"
            )
        )

        mlflow.log_artifact(
            str(
                OUTPUT_DIR
                / "model_metadata.json"
            )
        )

        mlflow.sklearn.log_model(
            model,
            name="model",
            registered_model_name=MODEL_NAME,
        )

    print()
    print(
        "Registered model:",
        MODEL_NAME,
    )

    print(
        "Artifacts saved to:",
        OUTPUT_DIR,
    )


if __name__ == "__main__":
    main()
