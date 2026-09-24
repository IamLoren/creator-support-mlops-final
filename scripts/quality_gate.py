import json
import sys
from pathlib import Path


METRICS_PATH = Path(
    "artifacts/final_model/metrics.json"
)

BASELINE_PATH = Path(
    "config/production_model.json"
)

EPSILON = 1e-6


def load_json(path: Path) -> dict:
    if not path.exists():
        raise FileNotFoundError(
            f"Required file not found: {path}"
        )

    return json.loads(
        path.read_text(encoding="utf-8")
    )


def main() -> None:
    metrics = load_json(METRICS_PATH)
    baseline = load_json(BASELINE_PATH)

    new_macro_f1 = float(
        metrics["macro_f1"]
    )

    production_macro_f1 = float(
        baseline["production_macro_f1"]
    )

    print("=" * 60)
    print("MODEL QUALITY GATE")
    print("=" * 60)

    print(
        f"Production Macro F1: "
        f"{production_macro_f1:.4f}"
    )

    print(
        f"Candidate Macro F1:  "
        f"{new_macro_f1:.4f}"
    )

    if (
        new_macro_f1 + EPSILON
        < production_macro_f1
    ):
        print()
        print(
            "QUALITY GATE: FAILED"
        )

        print(
            "Candidate model performs worse "
            "than the production model."
        )

        sys.exit(1)

    print()
    print(
        "QUALITY GATE: PASSED"
    )

    print(
        "Candidate model is not worse "
        "than the current production model."
    )


if __name__ == "__main__":
    main()
