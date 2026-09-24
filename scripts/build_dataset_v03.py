import json
from collections import Counter
from pathlib import Path


BASE_DATASET = Path(
    "data/annotated/customer_support_intents.json"
)

AUGMENTATION = Path(
    "data/augmentation/v0.3_targeted_scenarios.json"
)

OUTPUT = BASE_DATASET

EXPECTED_BASE_RECORDS = 144
EXPECTED_BASE_SCENARIOS = 72
EXPECTED_NEW_SCENARIOS = 36
EXPECTED_FINAL_RECORDS = 216
EXPECTED_FINAL_SCENARIOS = 108

INTENTS = {
    "ACCESS_ACCOUNT",
    "TECHNICAL_ISSUE",
    "SCHEDULE_DEADLINE",
    "SERVICE_INFO",
    "CONTENT_USAGE_QUESTION",
    "CHANGE_CANCEL",
    "FEEDBACK_COMPLAINT",
    "HUMAN_SUPPORT",
    "OTHER",
}

DOMAINS = {
    "education",
    "fitness",
    "beauty",
    "professional_services",
}


def load_json(path):
    with path.open(
        "r",
        encoding="utf-8",
    ) as file:
        return json.load(file)


def main():
    base_records = load_json(BASE_DATASET)
    new_scenarios = load_json(AUGMENTATION)

    base_scenario_ids = {
        record["scenario_id"]
        for record in base_records
    }

    base_record_ids = {
        record["id"]
        for record in base_records
    }

    if len(base_records) != EXPECTED_BASE_RECORDS:
        raise ValueError(
            f"Expected {EXPECTED_BASE_RECORDS} base records, "
            f"found {len(base_records)}. "
            "The builder must run on dataset-v0.2."
        )

    if len(base_scenario_ids) != EXPECTED_BASE_SCENARIOS:
        raise ValueError(
            f"Expected {EXPECTED_BASE_SCENARIOS} base scenarios, "
            f"found {len(base_scenario_ids)}."
        )

    if len(new_scenarios) != EXPECTED_NEW_SCENARIOS:
        raise ValueError(
            f"Expected {EXPECTED_NEW_SCENARIOS} new scenarios, "
            f"found {len(new_scenarios)}."
        )

    new_scenario_ids = [
        item["scenario_id"]
        for item in new_scenarios
    ]

    if len(new_scenario_ids) != len(set(new_scenario_ids)):
        raise ValueError(
            "Duplicate scenario IDs found in augmentation."
        )

    overlap = (
        base_scenario_ids
        & set(new_scenario_ids)
    )

    if overlap:
        raise ValueError(
            f"Scenario IDs already exist: {sorted(overlap)}"
        )

    intent_counts = Counter(
        item["intent"]
        for item in new_scenarios
    )

    domain_counts = Counter(
        item["domain"]
        for item in new_scenarios
    )

    if set(intent_counts) != INTENTS:
        raise ValueError(
            f"Unexpected intent set: {set(intent_counts)}"
        )

    if any(
        count != 4
        for count in intent_counts.values()
    ):
        raise ValueError(
            f"Expected 4 new scenarios per intent: "
            f"{dict(intent_counts)}"
        )

    if set(domain_counts) != DOMAINS:
        raise ValueError(
            f"Unexpected domain set: {set(domain_counts)}"
        )

    if any(
        count != 9
        for count in domain_counts.values()
    ):
        raise ValueError(
            f"Expected 9 new scenarios per domain: "
            f"{dict(domain_counts)}"
        )

    max_message_number = max(
        int(
            record["id"].split("_")[1]
        )
        for record in base_records
    )

    records = list(base_records)

    next_message_number = (
        max_message_number + 1
    )

    for scenario in new_scenarios:
        for language in ("uk", "en"):
            record_id = (
                f"msg_{next_message_number:06d}"
            )

            if record_id in base_record_ids:
                raise ValueError(
                    f"Duplicate record ID: {record_id}"
                )

            records.append(
                {
                    "id": record_id,
                    "scenario_id": scenario[
                        "scenario_id"
                    ],
                    "text": scenario[language],
                    "language": language,
                    "domain": scenario[
                        "domain"
                    ],
                    "source": "synthetic",
                    "intent": scenario[
                        "intent"
                    ],
                }
            )

            next_message_number += 1

    scenario_ids = {
        record["scenario_id"]
        for record in records
    }

    record_ids = {
        record["id"]
        for record in records
    }

    if len(records) != EXPECTED_FINAL_RECORDS:
        raise ValueError(
            f"Expected {EXPECTED_FINAL_RECORDS} records, "
            f"found {len(records)}."
        )

    if len(scenario_ids) != EXPECTED_FINAL_SCENARIOS:
        raise ValueError(
            f"Expected {EXPECTED_FINAL_SCENARIOS} scenarios, "
            f"found {len(scenario_ids)}."
        )

    if len(record_ids) != len(records):
        raise ValueError(
            "Duplicate record IDs found."
        )

    OUTPUT.write_text(
        json.dumps(
            records,
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    final_intents = Counter(
        record["intent"]
        for record in records
    )

    final_domains = Counter(
        record["domain"]
        for record in records
    )

    final_languages = Counter(
        record["language"]
        for record in records
    )

    print("dataset-v0.3 created successfully.")
    print()
    print(
        f"Records:   {len(records)}"
    )
    print(
        f"Scenarios: {len(scenario_ids)}"
    )

    print()
    print("Intent distribution:")
    for key in sorted(final_intents):
        print(
            f"  {key}: {final_intents[key]}"
        )

    print()
    print("Domain distribution:")
    for key in sorted(final_domains):
        print(
            f"  {key}: {final_domains[key]}"
        )

    print()
    print("Language distribution:")
    for key in sorted(final_languages):
        print(
            f"  {key}: {final_languages[key]}"
        )


if __name__ == "__main__":
    main()
