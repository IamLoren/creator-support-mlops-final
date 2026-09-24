import csv
from pathlib import Path
from statistics import mean, pstdev

import mlflow
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import (
    StratifiedGroupKFold,
    cross_validate,
)
from sklearn.pipeline import FeatureUnion, Pipeline
from sklearn.svm import LinearSVC

from error_analysis import (
    DATASET_PATH,
    RANDOM_STATE,
    load_dataset,
    split_scenarios,
)


TRACKING_URI = "http://127.0.0.1:5000"
EXPERIMENT_NAME = "customer-support-intent-classification"

CV_FOLDS = 3

OUTPUT_PATH = Path(
    "artifacts/model_comparison.csv"
)


def build_candidates():
    return {
        "compare-word-unigram-lr": {
            "model": Pipeline(
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
            ),
            "params": {
                "features": "word_tfidf",
                "ngram_range": "1-1",
                "classifier": "logistic_regression",
                "C": 10.0,
            },
        },

        "compare-word-bigram-lr": {
            "model": Pipeline(
                [
                    (
                        "tfidf",
                        TfidfVectorizer(
                            analyzer="word",
                            ngram_range=(1, 2),
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
            ),
            "params": {
                "features": "word_tfidf",
                "ngram_range": "1-2",
                "classifier": "logistic_regression",
                "C": 10.0,
            },
        },

        "compare-char-lr": {
            "model": Pipeline(
                [
                    (
                        "tfidf",
                        TfidfVectorizer(
                            analyzer="char_wb",
                            ngram_range=(3, 5),
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
            ),
            "params": {
                "features": "char_tfidf",
                "ngram_range": "3-5",
                "classifier": "logistic_regression",
                "C": 10.0,
            },
        },

        "compare-word-linearsvc": {
            "model": Pipeline(
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
                        LinearSVC(
                            C=1.0,
                            random_state=RANDOM_STATE,
                        ),
                    ),
                ]
            ),
            "params": {
                "features": "word_tfidf",
                "ngram_range": "1-1",
                "classifier": "linear_svc",
                "C": 1.0,
            },
        },

        "compare-char-linearsvc": {
            "model": Pipeline(
                [
                    (
                        "tfidf",
                        TfidfVectorizer(
                            analyzer="char_wb",
                            ngram_range=(3, 5),
                        ),
                    ),
                    (
                        "classifier",
                        LinearSVC(
                            C=1.0,
                            random_state=RANDOM_STATE,
                        ),
                    ),
                ]
            ),
            "params": {
                "features": "char_tfidf",
                "ngram_range": "3-5",
                "classifier": "linear_svc",
                "C": 1.0,
            },
        },

        "compare-word-char-linearsvc": {
            "model": Pipeline(
                [
                    (
                        "features",
                        FeatureUnion(
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
                        ),
                    ),
                    (
                        "classifier",
                        LinearSVC(
                            C=1.0,
                            random_state=RANDOM_STATE,
                        ),
                    ),
                ]
            ),
            "params": {
                "features": "word_char_tfidf",
                "word_ngram_range": "1-2",
                "char_ngram_range": "3-5",
                "classifier": "linear_svc",
                "C": 1.0,
            },
        },
    }


def main():
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

    print(
        f"Development records: {len(dev_records)}"
    )
    print(
        f"Held-out test records: {len(test_records)}"
    )
    print(
        "Final test is NOT used for model selection."
    )
    print()

    mlflow.set_tracking_uri(
        TRACKING_URI
    )
    mlflow.set_experiment(
        EXPERIMENT_NAME
    )

    scoring = {
        "accuracy": "accuracy",
        "macro_f1": "f1_macro",
        "weighted_f1": "f1_weighted",
    }

    results = []

    for run_name, candidate in build_candidates().items():
        print(
            f"Evaluating: {run_name}"
        )

        cv = StratifiedGroupKFold(
            n_splits=CV_FOLDS,
            shuffle=True,
            random_state=RANDOM_STATE,
        )

        scores = cross_validate(
            candidate["model"],
            x_dev,
            y_dev,
            groups=groups,
            cv=cv,
            scoring=scoring,
            return_train_score=False,
        )

        accuracy_values = scores[
            "test_accuracy"
        ]
        macro_f1_values = scores[
            "test_macro_f1"
        ]
        weighted_f1_values = scores[
            "test_weighted_f1"
        ]

        result = {
            "run_name": run_name,
            "cv_accuracy_mean": mean(
                accuracy_values
            ),
            "cv_accuracy_std": pstdev(
                accuracy_values
            ),
            "cv_macro_f1_mean": mean(
                macro_f1_values
            ),
            "cv_macro_f1_std": pstdev(
                macro_f1_values
            ),
            "cv_weighted_f1_mean": mean(
                weighted_f1_values
            ),
            "cv_weighted_f1_std": pstdev(
                weighted_f1_values
            ),
        }

        results.append(result)

        with mlflow.start_run(
            run_name=run_name
        ):
            mlflow.log_params(
                candidate["params"]
            )

            mlflow.log_param(
                "dataset_version",
                "dataset-v0.3",
            )

            mlflow.log_param(
                "cv_folds",
                CV_FOLDS,
            )

            mlflow.log_param(
                "grouping",
                "scenario_id",
            )

            mlflow.log_metrics(
                {
                    "cv_accuracy_mean":
                        result["cv_accuracy_mean"],
                    "cv_accuracy_std":
                        result["cv_accuracy_std"],
                    "cv_macro_f1_mean":
                        result["cv_macro_f1_mean"],
                    "cv_macro_f1_std":
                        result["cv_macro_f1_std"],
                    "cv_weighted_f1_mean":
                        result["cv_weighted_f1_mean"],
                    "cv_weighted_f1_std":
                        result["cv_weighted_f1_std"],
                }
            )

        print(
            "  Macro F1: "
            f"{result['cv_macro_f1_mean']:.4f} "
            "± "
            f"{result['cv_macro_f1_std']:.4f}"
        )

        print(
            "  Accuracy: "
            f"{result['cv_accuracy_mean']:.4f}"
        )

        print()

    results.sort(
        key=lambda item:
            item["cv_macro_f1_mean"],
        reverse=True,
    )

    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with OUTPUT_PATH.open(
        "w",
        encoding="utf-8",
        newline="",
    ) as file:
        writer = csv.DictWriter(
            file,
            fieldnames=results[0].keys(),
        )

        writer.writeheader()
        writer.writerows(results)

    print()
    print("MODEL RANKING")
    print("-------------")

    for index, result in enumerate(
        results,
        start=1,
    ):
        print(
            f"{index}. "
            f"{result['run_name']}: "
            f"Macro F1 = "
            f"{result['cv_macro_f1_mean']:.4f} "
            f"± "
            f"{result['cv_macro_f1_std']:.4f}"
        )

    print()
    print(
        f"Results saved to {OUTPUT_PATH}"
    )


if __name__ == "__main__":
    main()
