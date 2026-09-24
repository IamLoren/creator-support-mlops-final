import json
from pathlib import Path

import mlflow
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, f1_score
from sklearn.model_selection import StratifiedGroupKFold
from sklearn.pipeline import Pipeline


DATASET_PATH = Path(
    "data/annotated/customer_support_intents.json"
)

SPLIT_PATH = Path(
    "data/splits/dataset_v0.2_split.json"
)

OUTPUT_PATH = Path(
    "artifacts/augmentation_impact.json"
)

TRACKING_URI = "http://127.0.0.1:5000"

EXPERIMENT_NAME = (
    "customer-support-intent-classification"
)

RANDOM_STATE = 42
CV_FOLDS = 3


def load_json(path):
    with path.open(
        "r",
        encoding="utf-8",
    ) as file:
        return json.load(file)


def build_model():
    return Pipeline(
        [
            (
                "tfidf",
                TfidfVectorizer(
                    analyzer="word",
                    ngram_range=(1, 1),
                ),
            ),
            (
                "classifier",
                LogisticRegression(
                    C=10.0,
                    max_iter=2000,
                    random_state=RANDOM_STATE,
                ),
            ),
        ]
    )


def calculate_metrics(
    y_true,
    y_pred,
):
    return {
        "accuracy": accuracy_score(
            y_true,
            y_pred,
        ),
        "macro_f1": f1_score(
            y_true,
            y_pred,
            average="macro",
        ),
        "weighted_f1": f1_score(
            y_true,
            y_pred,
            average="weighted",
        ),
        "errors": sum(
            true != predicted
            for true, predicted
            in zip(y_true, y_pred)
        ),
    }


def log_mlflow_run(
    run_name,
    metrics,
    training_mode,
):
    with mlflow.start_run(
        run_name=run_name
    ):
        mlflow.log_params(
            {
                "classifier":
                    "logistic_regression",
                "C":
                    10.0,
                "features":
                    "word_tfidf",
                "ngram_range":
                    "1-1",
                "cv_folds":
                    CV_FOLDS,
                "evaluation_population":
                    "frozen_v02_development",
                "training_mode":
                    training_mode,
                "final_test_used":
                    False,
            }
        )

        mlflow.log_metrics(
            metrics
        )


def main():
    records = load_json(
        DATASET_PATH
    )

    split = load_json(
        SPLIT_PATH
    )

    old_dev_scenarios = set(
        split["development_scenarios"]
    )

    final_test_scenarios = set(
        split["final_test_scenarios"]
    )

    old_dev_records = [
        record
        for record in records
        if record["scenario_id"]
        in old_dev_scenarios
    ]

    final_test_records = [
        record
        for record in records
        if record["scenario_id"]
        in final_test_scenarios
    ]

    new_records = [
        record
        for record in records
        if (
            record["scenario_id"]
            not in old_dev_scenarios
            and record["scenario_id"]
            not in final_test_scenarios
        )
    ]

    print(
        "Frozen old development records:",
        len(old_dev_records),
    )

    print(
        "New augmentation records:",
        len(new_records),
    )

    print(
        "Frozen final-test records:",
        len(final_test_records),
    )

    if len(old_dev_records) != 108:
        raise ValueError(
            "Expected 108 frozen development records."
        )

    if len(new_records) != 72:
        raise ValueError(
            "Expected 72 augmentation records."
        )

    if len(final_test_records) != 36:
        raise ValueError(
            "Expected 36 frozen final-test records."
        )

    x_old = [
        record["text"]
        for record in old_dev_records
    ]

    y_old = [
        record["intent"]
        for record in old_dev_records
    ]

    groups_old = [
        record["scenario_id"]
        for record in old_dev_records
    ]

    x_new = [
        record["text"]
        for record in new_records
    ]

    y_new = [
        record["intent"]
        for record in new_records
    ]

    baseline_predictions = [
        None
    ] * len(old_dev_records)

    augmented_predictions = [
        None
    ] * len(old_dev_records)

    cv = StratifiedGroupKFold(
        n_splits=CV_FOLDS,
        shuffle=True,
        random_state=RANDOM_STATE,
    )

    for fold, (
        train_indices,
        validation_indices,
    ) in enumerate(
        cv.split(
            x_old,
            y_old,
            groups_old,
        ),
        start=1,
    ):
        x_train_old = [
            x_old[index]
            for index in train_indices
        ]

        y_train_old = [
            y_old[index]
            for index in train_indices
        ]

        x_validation = [
            x_old[index]
            for index in validation_indices
        ]

        print()
        print(
            f"Fold {fold}"
        )
        print(
            "Old training records:",
            len(x_train_old),
        )
        print(
            "Validation records:",
            len(x_validation),
        )

        baseline_model = build_model()

        baseline_model.fit(
            x_train_old,
            y_train_old,
        )

        baseline_fold_predictions = (
            baseline_model.predict(
                x_validation
            )
        )

        for index, prediction in zip(
            validation_indices,
            baseline_fold_predictions,
        ):
            baseline_predictions[index] = prediction

        augmented_model = build_model()

        augmented_model.fit(
            x_train_old + x_new,
            y_train_old + y_new,
        )

        augmented_fold_predictions = (
            augmented_model.predict(
                x_validation
            )
        )

        for index, prediction in zip(
            validation_indices,
            augmented_fold_predictions,
        ):
            augmented_predictions[index] = prediction

    if any(
        prediction is None
        for prediction in baseline_predictions
    ):
        raise RuntimeError(
            "Missing baseline predictions."
        )

    if any(
        prediction is None
        for prediction in augmented_predictions
    ):
        raise RuntimeError(
            "Missing augmented predictions."
        )

    baseline_metrics = calculate_metrics(
        y_old,
        baseline_predictions,
    )

    augmented_metrics = calculate_metrics(
        y_old,
        augmented_predictions,
    )

    result = {
        "evaluation_population":
            "frozen_v0.2_development",
        "evaluation_records":
            len(old_dev_records),
        "augmentation_records":
            len(new_records),
        "final_test_records":
            len(final_test_records),
        "final_test_used":
            False,
        "baseline":
            baseline_metrics,
        "augmented":
            augmented_metrics,
        "delta": {
            "accuracy":
                augmented_metrics["accuracy"]
                - baseline_metrics["accuracy"],
            "macro_f1":
                augmented_metrics["macro_f1"]
                - baseline_metrics["macro_f1"],
            "weighted_f1":
                augmented_metrics["weighted_f1"]
                - baseline_metrics["weighted_f1"],
            "errors":
                augmented_metrics["errors"]
                - baseline_metrics["errors"],
        },
    }

    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    OUTPUT_PATH.write_text(
        json.dumps(
            result,
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    print()
    print("=" * 60)
    print("FIXED VALIDATION BENCHMARK")
    print("=" * 60)

    print()
    print("WITHOUT TARGETED AUGMENTATION")
    print(
        f"Accuracy:    "
        f"{baseline_metrics['accuracy']:.4f}"
    )
    print(
        f"Macro F1:    "
        f"{baseline_metrics['macro_f1']:.4f}"
    )
    print(
        f"Weighted F1: "
        f"{baseline_metrics['weighted_f1']:.4f}"
    )
    print(
        f"Errors:      "
        f"{baseline_metrics['errors']}"
    )

    print()
    print("WITH TARGETED AUGMENTATION")
    print(
        f"Accuracy:    "
        f"{augmented_metrics['accuracy']:.4f}"
    )
    print(
        f"Macro F1:    "
        f"{augmented_metrics['macro_f1']:.4f}"
    )
    print(
        f"Weighted F1: "
        f"{augmented_metrics['weighted_f1']:.4f}"
    )
    print(
        f"Errors:      "
        f"{augmented_metrics['errors']}"
    )

    print()
    print("IMPROVEMENT")
    print(
        f"Accuracy:    "
        f"{result['delta']['accuracy']:+.4f}"
    )
    print(
        f"Macro F1:    "
        f"{result['delta']['macro_f1']:+.4f}"
    )
    print(
        f"Weighted F1: "
        f"{result['delta']['weighted_f1']:+.4f}"
    )
    print(
        f"Errors:      "
        f"{result['delta']['errors']:+d}"
    )

    print()
    print(
        "Final test was NOT used."
    )

    mlflow.set_tracking_uri(
        TRACKING_URI
    )

    mlflow.set_experiment(
        EXPERIMENT_NAME
    )

    log_mlflow_run(
        "augmentation-impact-baseline",
        baseline_metrics,
        "original_v02_only",
    )

    log_mlflow_run(
        "augmentation-impact-targeted-v03",
        augmented_metrics,
        "original_plus_targeted_v03",
    )

    print()
    print(
        f"Results saved to {OUTPUT_PATH}"
    )


if __name__ == "__main__":
    main()
