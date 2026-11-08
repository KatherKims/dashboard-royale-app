from pathlib import Path
import json

report_path = Path("data/analysis_results.json")

report = json.loads(
    report_path.read_text(
        encoding="utf-8"
    )
)

wanted_sections = [
    "forecast",
    "simulation",
    "downtime",
    "bottom10",
    "action_catalog",
    "players",
    "loyalty",
    "event_associations",
    "traffic",
]

for section in wanted_sections:
    print("\n" + "=" * 100)
    print(section.upper())
    print("=" * 100)

    value = report.get(section)

    if value is None:
        print("NOT PRESENT")
    else:
        print(
            json.dumps(
                value,
                indent=2,
                default=str,
            )
        )