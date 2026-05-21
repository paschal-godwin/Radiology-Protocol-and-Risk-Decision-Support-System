import json
from pathlib import Path


BASELINE_PATH = Path("eval/results/baseline_run.json")
LATEST_PATH = Path("eval/results/latest_run.json")
OUTPUT_PATH = Path("eval/results/comparison_report.json")


def load_json(path):
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def index_results_by_case(run_data):
    return {
        case["case_name"]: case
        for case in run_data.get("results", [])
    }


def get_confidence(case):
    confidence = case.get("confidence") or {}
    return confidence.get("final_confidence")


def compare_runs(baseline, latest):
    baseline_cases = index_results_by_case(baseline)
    latest_cases = index_results_by_case(latest)

    all_case_names = sorted(set(baseline_cases) | set(latest_cases))

    case_changes = []
    regressions = []
    improvements = []

    for case_name in all_case_names:
        old = baseline_cases.get(case_name)
        new = latest_cases.get(case_name)

        if old is None:
            case_changes.append({
                "case_name": case_name,
                "change_type": "new_case_added",
            })
            continue

        if new is None:
            case_changes.append({
                "case_name": case_name,
                "change_type": "case_removed",
            })
            regressions.append(case_name)
            continue

        old_pass = old.get("pass")
        new_pass = new.get("pass")

        old_conf = get_confidence(old)
        new_conf = get_confidence(new)

        changes = {
            "case_name": case_name,
            "baseline_pass": old_pass,
            "latest_pass": new_pass,
            "baseline_failure_types": old.get("failure_types", []),
            "latest_failure_types": new.get("failure_types", []),
            "baseline_confidence": old_conf,
            "latest_confidence": new_conf,
            "changed_fields": [],
        }

        if old_pass != new_pass:
            changes["changed_fields"].append("pass_status")

            if old_pass is True and new_pass is False:
                regressions.append(case_name)

            if old_pass is False and new_pass is True:
                improvements.append(case_name)

        if old.get("actual") != new.get("actual"):
            changes["changed_fields"].append("actual_outputs")

        if old.get("checks") != new.get("checks"):
            changes["changed_fields"].append("checks")

        if old_conf is not None and new_conf is not None:
            confidence_delta = round(new_conf - old_conf, 4)
            changes["confidence_delta"] = confidence_delta

            if confidence_delta <= -0.10:
                changes["changed_fields"].append("confidence_drop")
                regressions.append(case_name)

        if changes["changed_fields"]:
            case_changes.append(changes)

    report = {
        "baseline_summary": {
            "total_cases": baseline.get("total_cases"),
            "passed_cases": baseline.get("passed_cases"),
            "failed_cases": baseline.get("failed_cases"),
            "pass_rate": baseline.get("pass_rate"),
            "metric_summary": baseline.get("metric_summary", {}),
        },
        "latest_summary": {
            "total_cases": latest.get("total_cases"),
            "passed_cases": latest.get("passed_cases"),
            "failed_cases": latest.get("failed_cases"),
            "pass_rate": latest.get("pass_rate"),
            "metric_summary": latest.get("metric_summary", {}),
        },
        "regression_detected": len(regressions) > 0,
        "regressions": sorted(set(regressions)),
        "improvements": sorted(set(improvements)),
        "case_changes": case_changes,
    }

    return report


def main():
    baseline = load_json(BASELINE_PATH)
    latest = load_json(LATEST_PATH)

    report = compare_runs(baseline, latest)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print("=== EVAL COMPARISON REPORT ===")
    print(f"Baseline pass rate: {report['baseline_summary']['pass_rate']}")
    print(f"Latest pass rate:   {report['latest_summary']['pass_rate']}")
    print(f"Regression detected: {report['regression_detected']}")
    print(f"Regressions: {report['regressions']}")
    print(f"Improvements: {report['improvements']}")
    print(f"Report saved to: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()