import argparse
import json
import statistics
from pathlib import Path

import mlflow
import mlflow.sklearn
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, f1_score
from sklearn.model_selection import (
    StratifiedGroupKFold,
    train_test_split,
)
from sklearn.pipeline import Pipeline


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

DATASET_PATH = Path(
    "data/annotated/customer_support_intents.json"
)

DATASET_VERSION = "dataset-v0.3"

TRACKING_URI = "http://127.0.0.1:5000"

EXPERIMENT_NAME = (
    "customer-support-intent-classification"
)

RANDOM_STATE = 42

TEST_SIZE = 0.25

CV_FOLDS = 3

MAX_ITER = 1000


# ---------------------------------------------------------------------------
# CLI arguments
# ---------------------------------------------------------------------------

def parse_args():
    parser = argparse.ArgumentParser(
        description=(
            "Train and evaluate the customer-support "
            "intent classifier."
        )
    )

    parser.add_argument(
        "--run-name",
        required=True,
        help="Name of the MLflow run.",
    )

    parser.add_argument(
        "--c",
        type=float,
        default=1.0,
        help=(
            "Inverse regularization strength for "
            "LogisticRegression."
        ),
    )

    parser.add_argument(
        "--ngram-max",
        type=int,
        choices=[1, 2],
        default=2,
        help=(
            "Maximum n-gram size used by "
            "TfidfVectorizer."
        ),
    )

    return parser.parse_args()


# ---------------------------------------------------------------------------
# Dataset loading
# ---------------------------------------------------------------------------

def load_dataset(path: Path) -> list[dict]:
    with path.open(
        "r",
        encoding="utf-8",
    ) as file:
        records = json.load(file)

    if not isinstance(records, list):
        raise ValueError(
            "Dataset must contain a JSON list."
        )

    return records


# ---------------------------------------------------------------------------
# Development / final test split
# ---------------------------------------------------------------------------

def split_by_scenario(records):
    """
    Split records using the frozen final-test manifest.

    All scenarios listed in the manifest remain in the final test set.
    Every other scenario, including new dataset-v0.3 scenarios,
    belongs to the development pool.
    """

    split_manifest_path = Path(
        "data/splits/dataset_v0.2_split.json"
    )

    with split_manifest_path.open(
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
            "Frozen final-test scenarios are missing "
            f"from the dataset: {sorted(missing)}"
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

def build_model(
    c_value: float,
    ngram_max: int,
) -> Pipeline:
    """
    Build the complete text-classification pipeline:

    text
        ->
    TF-IDF features
        ->
    Logistic Regression classifier
    """

    return Pipeline(
        [
            (
                "tfidf",
                TfidfVectorizer(
                    ngram_range=(
                        1,
                        ngram_max,
                    ),
                ),
            ),
            (
                "classifier",
                LogisticRegression(
                    C=c_value,
                    max_iter=MAX_ITER,
                    random_state=RANDOM_STATE,
                ),
            ),
        ]
    )


# ---------------------------------------------------------------------------
# Training
# ---------------------------------------------------------------------------

def main():
    args = parse_args()

    records = load_dataset(
        DATASET_PATH
    )

    dev_records, test_records = (
        split_by_scenario(records)
    )

    # Development data used for cross-validation
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

    # Final held-out test data.
    # We intentionally do not evaluate on it
    # during hyperparameter selection.
    x_test = [
        record["text"]
        for record in test_records
    ]

    y_test = [
        record["intent"]
        for record in test_records
    ]

    # Keep variables explicitly available for
    # the later final-evaluation step.
    _ = x_test, y_test

    cv = StratifiedGroupKFold(
        n_splits=CV_FOLDS,
        shuffle=True,
        random_state=RANDOM_STATE,
    )

    mlflow.set_tracking_uri(
        TRACKING_URI
    )

    mlflow.set_experiment(
        EXPERIMENT_NAME
    )

    with mlflow.start_run(
        run_name=args.run_name
    ) as run:

        # ---------------------------------------------------------------
        # Log experiment configuration
        # ---------------------------------------------------------------

        mlflow.log_params(
            {
                "dataset_version":
                    DATASET_VERSION,

                "test_size":
                    TEST_SIZE,

                "random_state":
                    RANDOM_STATE,

                "cv_folds":
                    CV_FOLDS,

                "tfidf_ngram_range":
                    str(
                        (
                            1,
                            args.ngram_max,
                        )
                    ),

                "logistic_regression_C":
                    args.c,

                "max_iter":
                    MAX_ITER,

                "development_records":
                    len(dev_records),

                "development_scenarios":
                    len(
                        {
                            record[
                                "scenario_id"
                            ]
                            for record
                            in dev_records
                        }
                    ),

                "final_test_records":
                    len(test_records),

                "final_test_scenarios":
                    len(
                        {
                            record[
                                "scenario_id"
                            ]
                            for record
                            in test_records
                        }
                    ),
            }
        )

        # ---------------------------------------------------------------
        # Cross-validation
        # ---------------------------------------------------------------

        fold_accuracies = []

        fold_macro_f1_scores = []

        fold_weighted_f1_scores = []

        for fold, (
            train_idx,
            val_idx,
        ) in enumerate(
            cv.split(
                x_dev,
                y_dev,
                groups=groups,
            ),
            start=1,
        ):

            x_train = [
                x_dev[index]
                for index in train_idx
            ]

            y_train = [
                y_dev[index]
                for index in train_idx
            ]

            x_val = [
                x_dev[index]
                for index in val_idx
            ]

            y_val = [
                y_dev[index]
                for index in val_idx
            ]

            fold_model = build_model(
                c_value=args.c,
                ngram_max=args.ngram_max,
            )

            fold_model.fit(
                x_train,
                y_train,
            )

            predictions = (
                fold_model.predict(
                    x_val
                )
            )

            fold_accuracy = (
                accuracy_score(
                    y_val,
                    predictions,
                )
            )

            fold_macro_f1 = (
                f1_score(
                    y_val,
                    predictions,
                    average="macro",
                    zero_division=0,
                )
            )

            fold_weighted_f1 = (
                f1_score(
                    y_val,
                    predictions,
                    average="weighted",
                    zero_division=0,
                )
            )

            fold_accuracies.append(
                fold_accuracy
            )

            fold_macro_f1_scores.append(
                fold_macro_f1
            )

            fold_weighted_f1_scores.append(
                fold_weighted_f1
            )

            # Metrics for every fold.
            # MLflow stores them as a time/step series.
            mlflow.log_metric(
                "cv_accuracy",
                fold_accuracy,
                step=fold,
            )

            mlflow.log_metric(
                "cv_macro_f1",
                fold_macro_f1,
                step=fold,
            )

            mlflow.log_metric(
                "cv_weighted_f1",
                fold_weighted_f1,
                step=fold,
            )

            print(
                f"Fold {fold}: "
                f"accuracy={fold_accuracy:.4f}, "
                f"macro_f1={fold_macro_f1:.4f}, "
                f"weighted_f1="
                f"{fold_weighted_f1:.4f}"
            )

        # ---------------------------------------------------------------
        # Aggregate CV metrics
        # ---------------------------------------------------------------

        mean_accuracy = (
            statistics.mean(
                fold_accuracies
            )
        )

        mean_macro_f1 = (
            statistics.mean(
                fold_macro_f1_scores
            )
        )

        mean_weighted_f1 = (
            statistics.mean(
                fold_weighted_f1_scores
            )
        )

        std_macro_f1 = (
            statistics.stdev(
                fold_macro_f1_scores
            )
        )

        mlflow.log_metrics(
            {
                "cv_accuracy_mean":
                    mean_accuracy,

                "cv_macro_f1_mean":
                    mean_macro_f1,

                "cv_macro_f1_std":
                    std_macro_f1,

                "cv_weighted_f1_mean":
                    mean_weighted_f1,
            }
        )

        # ---------------------------------------------------------------
        # Log CV summary as an artifact
        # ---------------------------------------------------------------

        cv_summary = {
            "fold_accuracies":
                fold_accuracies,

            "fold_macro_f1":
                fold_macro_f1_scores,

            "fold_weighted_f1":
                fold_weighted_f1_scores,

            "cv_accuracy_mean":
                mean_accuracy,

            "cv_macro_f1_mean":
                mean_macro_f1,

            "cv_macro_f1_std":
                std_macro_f1,

            "cv_weighted_f1_mean":
                mean_weighted_f1,
        }

        mlflow.log_dict(
            cv_summary,
            "evaluation/cv_summary.json",
        )

        # ---------------------------------------------------------------
        # Train candidate model on ALL development data
        # ---------------------------------------------------------------

        candidate_model = build_model(
            c_value=args.c,
            ngram_max=args.ngram_max,
        )

        candidate_model.fit(
            x_dev,
            y_dev,
        )

        # ---------------------------------------------------------------
        # Log trained candidate model
        # ---------------------------------------------------------------

        mlflow.sklearn.log_model(
            candidate_model,
            name="model",
            serialization_format=(
                "cloudpickle"
            ),
        )

        # ---------------------------------------------------------------
        # Console output
        # ---------------------------------------------------------------

        print(
            f"\nRun ID: "
            f"{run.info.run_id}"
        )

        print(
            f"Total records: "
            f"{len(records)}"
        )

        print(
            f"Development records: "
            f"{len(dev_records)}"
        )

        print(
            f"Final test records: "
            f"{len(test_records)}"
        )

        print(
            "\nCross-validation summary:"
        )

        print(
            f"Mean accuracy:    "
            f"{mean_accuracy:.4f}"
        )

        print(
            f"Mean macro F1:    "
            f"{mean_macro_f1:.4f}"
        )

        print(
            f"Macro F1 std:     "
            f"{std_macro_f1:.4f}"
        )

        print(
            f"Mean weighted F1: "
            f"{mean_weighted_f1:.4f}"
        )

        print(
            "\nFinal test set was NOT used "
            "for model selection."
        )


if __name__ == "__main__":
    main()