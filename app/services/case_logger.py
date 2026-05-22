import json
from datetime import datetime, timezone
from pathlib import Path


LOG_PATH = Path("logs/case_runs.jsonl")


def make_json_safe(value):
    if hasattr(value, "model_dump"):
        return value.model_dump()
    if isinstance(value, list):
        return [make_json_safe(v) for v in value]
    if isinstance(value, dict):
        return {k: make_json_safe(v) for k, v in value.items()}
    return value


def extract_case_log(input_data, assessment_result):
    confidence = assessment_result.get("confidence")
    debug_trace = assessment_result.get("debug_trace", {})
    rule_trace = debug_trace.get("rule_trace", {})

    selected_evidence = debug_trace.get("selected_evidence", [])

    overall_decision = assessment_result.get("overall_decision", {})

    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "input_summary": make_json_safe(input_data),
        "overall_risk": overall_decision.get("overall_risk_level"),
        "recommended_action": overall_decision.get("recommended_action"),
        "confidence": getattr(confidence, "final_confidence", None),
        "confidence_label": getattr(confidence, "confidence_label", None),
        "capped_by": getattr(confidence, "capped_by", None),
        "active_claims": rule_trace.get("active_claims", []),
        "active_topics": rule_trace.get("active_topics", []),
        "selected_evidence_count": len(selected_evidence),
    }


def log_case_run(input_data, assessment_result, log_path=LOG_PATH):
    log_path.parent.mkdir(parents=True, exist_ok=True)

    log_entry = extract_case_log(
        input_data=input_data,
        assessment_result=assessment_result,
    )

    with open(log_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")

    return log_entry