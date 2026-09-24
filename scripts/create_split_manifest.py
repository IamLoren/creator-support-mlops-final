import json
from pathlib import Path

from sklearn.model_selection import train_test_split


DATASET_PATH = Path(
    "data/annotated/customer_support_intents.json"
)

OUTPUT_PATH = Path(
    "data/splits/dataset_v0.2_split.json"
)

RANDOM_STATE = 42
TEST_SIZE = 0.25


def main():
    with DATASET_PATH.open(
        "r",
        encoding="utf-8",
    ) as file:
        records = json.load(file)

    scenario_to_intent = {}

    for record in records:
        scenario_id = record["scenario_id"]
        intent = record["intent"]

        if scenario_id in scenario_to_intent:
            if scenario_to_intent[scenario_id] != intent:
                raise ValueError(
                    f"{scenario_id} has multiple intents."
                )
        else:
            scenario_to_intent[scenario_id] = intent

    scenario_ids = list(
        scenario_to_intent.keys()
    )

    labels = [
        scenario_to_intent[scenario_id]
        for scenario_id in scenario_ids
    ]

    dev_scenarios, test_scenarios = train_test_split(
        scenario_ids,
        test_size=TEST_SIZE,
        random_state=RANDOM_STATE,
        stratify=labels,
    )

    manifest = {
        "dataset_version": "dataset-v0.2",
        "random_state": RANDOM_STATE,
        "test_size": TEST_SIZE,
        "development_scenarios": sorted(
            dev_scenarios
        ),
        "final_test_scenarios": sorted(
            test_scenarios
        ),
    }

    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with OUTPUT_PATH.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            manifest,
            file,
            ensure_ascii=False,
            indent=2,
        )

    print(
        f"Development scenarios: "
        f"{len(dev_scenarios)}"
    )
    print(
        f"Final test scenarios: "
        f"{len(test_scenarios)}"
    )
    print(
        f"Saved to: {OUTPUT_PATH}"
    )


if __name__ == "__main__":
    main()
