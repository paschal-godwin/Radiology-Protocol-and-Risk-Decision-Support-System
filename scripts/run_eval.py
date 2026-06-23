import sys
import os
import json
from pathlib import Path
from dotenv import load_dotenv

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.schemas.input import RadiologyCaseInput
from app.services.assessment_service import run_assessment



load_dotenv()


EVAL_CASES = [
    {
        "name": "high_renal_and_unknown_thyroid",
        "input": {
            "age": 68,
            "sex": "male",
            "pregnancy_status": "not_applicable",
            "exam_requested": "CT",
            "contrast_requested": True,
            "urgency_level": "routine",
            "egfr": 22.0,
            "allergy_history": False,
            "prior_contrast_reaction": "none",
            "diabetes_status": "non_diabetic",
            "thyroid_status": "unknown",
            "metformin_use": "no"
        },
        "expected": {
            "expected_overall_risk": "high",
            "expected_action": "hold_and_review",
            "expected_claims": ["renal_risk", "thyroid_risk"],
            "expected_topics": ["renal", "thyroid"],

            # NEW: lightweight evidence-quality expectations
            "expected_primary_source_title_by_claim": {
                "renal_risk": "CT imaging_guidelines",
                "thyroid_risk": "ACR-Manual-on-Contrast-Media"
            },
            "expected_primary_topic_by_claim": {
                "renal_risk": "renal",
                "thyroid_risk": "thyroid"
            },
            "expected_multi_risk_escalation": True,
            "manual_evidence_quality": "acceptable"
        }
    },
    {
        "name": "severe_reaction_only",
        "input": {
            "age": 45,
            "sex": "female",
            "pregnancy_status": "not_pregnant",
            "exam_requested": "CT",
            "contrast_requested": True,
            "urgency_level": "routine",
            "egfr": 78.0,
            "allergy_history": False,
            "prior_contrast_reaction": "severe",
            "diabetes_status": "non_diabetic",
            "thyroid_status": "normal",
            "metformin_use": "no"
        },
        "expected": {
            "expected_overall_risk": "high",
            "expected_action": "hold_and_review",
            "expected_claims": ["contrast_reaction_risk"],
            "expected_topics": ["contrast_reaction"],

            "expected_primary_source_title_by_claim": {
                "contrast_reaction_risk": "ACR-Manual-on-Contrast-Media"
            },
            "expected_primary_topic_by_claim": {
                "contrast_reaction_risk": "contrast_reaction"
            },
            "manual_evidence_quality": "strong"
        }
    },
    {
        "name": "high_renal_and_severe_reaction",
        "input": {
            "age": 60,
            "sex": "male",
            "pregnancy_status": "not_applicable",
            "exam_requested": "CT",
            "contrast_requested": True,
            "urgency_level": "routine",
            "egfr": 20.0,
            "allergy_history": False ,
            "prior_contrast_reaction": "severe",
            "thyroid_status": "unknown",
            "metformin_use": "no",
            "diabetes_status": "non_diabetic"
        },
        "expected": {
            "expected_overall_risk": "high",
            "expected_action": "hold_and_review",
            "expected_claims": ["renal_risk", "contrast_reaction_risk", "thyroid_risk"],
            "expected_topics": ["renal", "contrast_reaction", "thyroid"],

            "expected_primary_source_title_by_claim": {
                "renal_risk": "CT imaging_guidelines",
                "contrast_reaction_risk": "ACR-Manual-on-Contrast-Media",
                "thyroid_risk": "ACR-Manual-on-Contrast-Media"
            },
            "expected_primary_topic_by_claim": {
                "renal_risk": "renal",
                "contrast_reaction_risk": "contrast_reaction",
                "thyroid_risk": "thyroid"
            },
            "expected_multi_risk_escalation": True,
            "manual_evidence_quality": "acceptable"
        }
    },
    {
    "name": "allergy_only_caution_case",
    "input": {
        "age": 42,
        "sex": "female",
        "pregnancy_status": "not_pregnant",
        "exam_requested": "CT",
        "contrast_requested": True,
        "urgency_level": "routine",
        "egfr": 86.0,
        "allergy_history": True,
        "asthma_history": False,
        "prior_contrast_reaction": "none",
        "thyroid_status": "normal",
        "metformin_use": "no",
        "diabetes_status": "non_diabetic"
    },
    "expected": {
        "expected_overall_risk": "moderate",
        "expected_action": "proceed_with_caution",
        "expected_claims": ["contrast_safety_modifier_risk"],
        "expected_topics": ["contrast_reaction"],

        "expected_primary_source_title_by_claim": {
            "contrast_safety_modifier_risk": "ACR-Manual-on-Contrast-Media"
        },
        "expected_primary_topic_by_claim": {
            "contrast_safety_modifier_risk": "contrast_reaction"
        },
        "expected_multi_risk_escalation": False,
        "manual_evidence_quality": "acceptable"
    }
},
{
    "name": "asthma_only_caution_case",
    "input": {
        "age": 36,
        "sex": "male",
        "pregnancy_status": "not_applicable",
        "exam_requested": "CT",
        "contrast_requested": True,
        "urgency_level": "routine",
        "egfr": 92.0,
        "allergy_history": False,
        "asthma_history": True,
        "prior_contrast_reaction": "none",
        "thyroid_status": "normal",
        "metformin_use": "no",
        "diabetes_status": "non_diabetic"
    },
    "expected": {
        "expected_overall_risk": "moderate",
        "expected_action": "proceed_with_caution",
        "expected_claims": ["contrast_safety_modifier_risk"],
        "expected_topics": ["contrast_reaction"],

        "expected_primary_source_title_by_claim": {
            "contrast_safety_modifier_risk": "ACR-Manual-on-Contrast-Media"
        },
        "expected_primary_topic_by_claim": {
            "contrast_safety_modifier_risk": "contrast_reaction"
        },
        "expected_multi_risk_escalation": False,
        "manual_evidence_quality": "acceptable"
    }
},
 {
        "name": "pregnancy_review_case",
        "input": {
            "age": 31,
            "sex": "female",
            "pregnancy_status": "pregnant",
            "exam_requested": "CT",
            "contrast_requested": True,
            "urgency_level": "routine",
            "egfr": 90.0,
            "allergy_history": False,
            "prior_contrast_reaction": "none",
            "thyroid_status": "normal",
            "metformin_use": "no",
            "diabetes_status": "non_diabetic"
        },
        "expected": {
            "expected_overall_risk": "high",
            "expected_action": "hold_and_review",
            "expected_claims": ["pregnancy_risk"],
            "expected_topics": ["pregnancy"],

            "expected_primary_source_title_by_claim": {
                "pregnancy_risk": "ACR-Manual-on-Contrast-Media"
            },
            "expected_primary_topic_by_claim": {
                "pregnancy_risk": "pregnancy"
            },
            "manual_evidence_quality": "strong"
        }
    },
    {
        "name": "missing_egfr_for_contrast_ct",
        "input": {
            "age": 57,
            "sex": "male",
            "pregnancy_status": "not_applicable",
            "exam_requested": "CT",
            "contrast_requested": True,
            "urgency_level": "routine",
            "egfr": None,
            "allergy_history": False,
            "prior_contrast_reaction": "none",
            "thyroid_status": "normal",
            "metformin_use": "no",
            "diabetes_status": "non_diabetic"
        },
        "expected": {
            "expected_overall_risk": "insufficient_information",
            "expected_missing_information_severity": "high",
            "expected_action": "hold_and_clarify",
            "expected_claims": [],
            "expected_topics": [],

            # No evidence expectations for missing-info-only case
            "expected_primary_source_title_by_claim": {},
            "expected_primary_topic_by_claim": {},
            "manual_evidence_quality": "not_applicable"
        }
    },
    {
        "name": "emergency_high_renal_risk_override",
        "input": {
            "age": 70,
            "sex": "male",
            "pregnancy_status": "not_applicable",
            "exam_requested": "CT",
            "contrast_requested": True,
            "urgency_level": "emergency",
            "egfr": 22.0,
            "allergy_history": False,
            "prior_contrast_reaction": "none",
            "diabetes_status": "non_diabetic",
            "metformin_use": "no",
            "thyroid_status": "normal"
        },
        "expected": {
            "expected_overall_risk": "high",
            "expected_action": "urgent_radiologist_review",
            "expected_claims": ["renal_risk"],
            "expected_topics": ["renal"],
            "expected_primary_source_title_by_claim": {
                "renal_risk": "CT imaging_guidelines"
            },
            "expected_primary_topic_by_claim": {
                "renal_risk": "renal"
            },
            "manual_evidence_quality": "acceptable"
        }
    },
    {
        "name": "multi_risk_escalation_case",
        "input": {
            "age": 66,
            "sex": "male",
            "pregnancy_status": "not_applicable",
            "exam_requested": "CT",
            "contrast_requested": True,
            "urgency_level": "routine",
            "egfr": 24.0,
            "allergy_history": True,
            "prior_contrast_reaction": "severe",
            "diabetes_status": "diabetic",
            "metformin_use": "yes",
            "thyroid_status": "normal"
        },
        "expected": {
            "expected_overall_risk": "high",
            "expected_action": "hold_and_review",
            "expected_claims": [
                "renal_risk",
                "contrast_reaction_risk",
                "contrast_safety_modifier_risk",
                "metformin_risk"
            ],
            "expected_topics": [
                "renal",
                "contrast_reaction",
                "metformin"
            ],
            "expected_primary_source_title_by_claim": {
                "renal_risk": "CT imaging_guidelines",
                "contrast_reaction_risk": "ACR-Manual-on-Contrast-Media",
                "metformin_risk": "ACR-Manual-on-Contrast-Media"
            },
            "expected_primary_topic_by_claim": {
                "renal_risk": "renal",
                "contrast_reaction_risk": "contrast_reaction",
                "metformin_risk": "metformin"
            },
            "manual_evidence_quality": "acceptable",
            "expected_multi_risk_escalation": True
        }
    },
    {
        "name": "emergency_missing_egfr_override",
        "input": {
            "age": 45,
            "sex": "male",
            "pregnancy_status": "not_applicable",
            "exam_requested": "CT",
            "contrast_requested": True,
            "urgency_level": "emergency",
            "egfr": None,
            "allergy_history": False,
            "prior_contrast_reaction": "none",
            "diabetes_status": "non_diabetic",
            "metformin_use": "no",
            "thyroid_status": "normal"
        },
        "expected": {
            "expected_overall_risk": "high",
            "expected_action": "urgent_radiologist_review",
            "expected_claims": [],
            "expected_topics": [],
            "expected_primary_source_title_by_claim": {},
            "expected_primary_topic_by_claim": {},
            "manual_evidence_quality": "not_applicable",
            "expected_multi_risk_escalation": False,
            "expected_missing_information_severity": "high"
        }
    },
    {
        "name": "low_risk_proceed_case",
        "input": {
            "age": 39,
            "sex": "female",
            "pregnancy_status": "not_pregnant",
            "exam_requested": "CT",
            "contrast_requested": True,
            "urgency_level": "routine",
            "egfr": 88.0,
            "allergy_history": False,
            "prior_contrast_reaction": "none",
            "thyroid_status": "normal",
            "metformin_use": "no",
            "diabetes_status": "non_diabetic"
        },
        "expected": {
            "expected_overall_risk": "low",
            "expected_action": "proceed",
            "expected_claims": [],
            "expected_topics": [],

            "expected_primary_source_title_by_claim": {},
            "expected_primary_topic_by_claim": {},
            "manual_evidence_quality": "not_applicable"
        }
    }
]


def normalize_list(values):
    return sorted(set(v for v in values if v)) if values else []


def extract_claims(citations):
    claims = []
    for c in citations:
        if isinstance(c, dict):
            claims.append(c.get("claim"))
        else:
            claims.append(c.claim)
    return claims


def extract_topics(citations):
    topics = []
    for c in citations:
        if isinstance(c, dict):
            topics.append(c.get("topic"))
        else:
            topics.append(c.topic)
    return topics


def extract_primary_citation_by_claim(citations):
    """
    Build a simple per-claim map of the first citation emitted for each claim.
    Since your explanation layer is claim-aware and emits one citation per claim,
    this is enough for V1 manual evidence-quality checking.
    """
    primary = {}

    for c in citations:
        if isinstance(c, dict):
            claim = c.get("claim")
            if claim not in primary:
                primary[claim] = {
                    "source_title": c.get("source_title"),
                    "topic": c.get("topic"),
                    "page_number": c.get("page_number"),
                    "snippet": c.get("snippet"),
                }
        else:
            claim = c.claim
            if claim not in primary:
                primary[claim] = {
                    "source_title": c.source_title,
                    "topic": c.topic,
                    "page_number": c.page_number,
                    "snippet": c.snippet,
                }

    return primary


def evaluate_evidence_expectations(expected, primary_citations_by_claim):
    expected_sources = expected.get("expected_primary_source_title_by_claim", {})
    expected_topics = expected.get("expected_primary_topic_by_claim", {})

    source_checks = {}
    topic_checks = {}

    source_ok = True
    topic_ok = True

    for claim, expected_source in expected_sources.items():
        actual = primary_citations_by_claim.get(claim)
        actual_source = actual.get("source_title") if actual else None
        ok = actual_source == expected_source
        source_checks[claim] = {
            "expected": expected_source,
            "actual": actual_source,
            "ok": ok,
        }
        if not ok:
            source_ok = False

    for claim, expected_topic in expected_topics.items():
        actual = primary_citations_by_claim.get(claim)
        actual_topic = actual.get("topic") if actual else None
        ok = actual_topic == expected_topic
        topic_checks[claim] = {
            "expected": expected_topic,
            "actual": actual_topic,
            "ok": ok,
        }
        if not ok:
            topic_ok = False

    overall_ok = source_ok and topic_ok

    return {
        "source_ok": source_ok,
        "topic_ok": topic_ok,
        "overall_ok": overall_ok,
        "source_checks": source_checks,
        "topic_checks": topic_checks,
    }


def build_failure_types(
    risk_ok,
    action_ok,
    actual_claims,
    expected_claims,
    actual_topics,
    expected_topics,
    evidence_eval,
    confidence=None,
):
    failures = []

    if not risk_ok:
        failures.append("decision_error")

    if not action_ok:
        failures.append("action_error")

    actual_claim_set = set(actual_claims or [])
    expected_claim_set = set(expected_claims or [])

    missing_claims = sorted(expected_claim_set - actual_claim_set)
    extra_claims = sorted(actual_claim_set - expected_claim_set)

    if missing_claims:
        failures.append("missing_expected_claim")

    if extra_claims:
        failures.append("unexpected_extra_claim")

    actual_topic_set = set(actual_topics or [])
    expected_topic_set = set(expected_topics or [])

    missing_topics = sorted(expected_topic_set - actual_topic_set)
    extra_topics = sorted(actual_topic_set - expected_topic_set)

    if missing_topics:
        failures.append("missing_expected_topic")

    if extra_topics:
        failures.append("unexpected_extra_topic")

    if not evidence_eval.get("source_ok", True):
        failures.append("wrong_evidence_source")

    if not evidence_eval.get("topic_ok", True):
        failures.append("wrong_evidence_topic")

    if confidence:
        final_confidence = getattr(confidence, "final_confidence", None)
        if final_confidence is not None and final_confidence < 0.70:
            failures.append("low_confidence_warning")

    return failures


def make_json_safe(value):
    if hasattr(value, "model_dump"):
        return value.model_dump()
    if isinstance(value, list):
        return [make_json_safe(v) for v in value]
    if isinstance(value, dict):
        return {k: make_json_safe(v) for k, v in value.items()}
    return value

def build_metric_summary(results):
    total = len(results)

    if total == 0:
        return {}

    decision_passes = sum(1 for r in results if r["checks"]["risk_ok"])
    action_passes = sum(1 for r in results if r["checks"]["action_ok"])
    claims_passes = sum(1 for r in results if r["checks"]["claims_ok"])
    topics_passes = sum(1 for r in results if r["checks"]["topics_ok"])
    evidence_passes = sum(1 for r in results if r["checks"]["evidence_expectation_ok"])

    confidence_scores = []
    low_confidence_cases = []

    for r in results:
        confidence = r.get("confidence") or {}
        final_confidence = confidence.get("final_confidence")

        if final_confidence is not None:
            confidence_scores.append(final_confidence)

            if final_confidence < 0.70:
                low_confidence_cases.append({
                    "case_name": r["case_name"],
                    "final_confidence": final_confidence,
                    "confidence_label": confidence.get("confidence_label"),
                    "capped_by": confidence.get("capped_by"),
                })

    failure_type_counts = {}

    for r in results:
        for failure_type in r.get("failure_types", []):
            failure_type_counts[failure_type] = failure_type_counts.get(failure_type, 0) + 1

    average_confidence = (
        round(sum(confidence_scores) / len(confidence_scores), 4)
        if confidence_scores
        else None
    )

    return {
        "decision_pass_rate": round(decision_passes / total, 4),
        "action_pass_rate": round(action_passes / total, 4),
        "claims_pass_rate": round(claims_passes / total, 4),
        "topics_pass_rate": round(topics_passes / total, 4),
        "evidence_expectation_pass_rate": round(evidence_passes / total, 4),
        "average_final_confidence": average_confidence,
        "low_confidence_cases": low_confidence_cases,
        "failure_type_counts": failure_type_counts,
    }

def build_debug_summary(case_result):
    actual = case_result.get("actual", {})
    confidence = case_result.get("confidence") or {}
    debug_trace = case_result.get("debug_trace") or {}

    selected_evidence = debug_trace.get("selected_evidence") or []
    retrieval_queries = debug_trace.get("retrieval_queries") or []

    active_claims = actual.get("claims") or []
    active_topics = actual.get("topics") or []

    final_confidence = confidence.get("final_confidence")
    capped_by = confidence.get("capped_by")

    if case_result.get("pass"):
        main_debug_note = "Case passed expected decision, action, claims, and topic checks."
    elif case_result.get("failure_types"):
        main_debug_note = f"Case failed with: {', '.join(case_result['failure_types'])}."
    else:
        main_debug_note = "Case failed, but no failure type was assigned."

    return {
        "active_topics": active_topics,
        "active_claims": active_claims,
        "selected_evidence_count": len(selected_evidence),
        "retrieval_query_count": len(retrieval_queries),
        "confidence_capped_by": capped_by,
        "final_confidence": final_confidence,
        "main_debug_note": main_debug_note,
    }


def main():
    results = []
    pass_count = 0
    evidence_expectation_pass_count = 0

    for case in EVAL_CASES:
        name = case["name"]
        input_data = case["input"]
        expected = case["expected"]

        result = run_assessment(RadiologyCaseInput(**input_data))

        actual_risk = result["overall_decision"]["overall_risk_level"]
        actual_action = result["overall_decision"]["recommended_action"]
        actual_missing_information_severity = result["overall_decision"].get(
            "missing_information_severity",
            "none",
        )

        expected_missing_information_severity = expected.get(
            "expected_missing_information_severity",
            "none",
        )

        citations = result["explanation"]["citations"]
        actual_claims = extract_claims(citations)
        actual_topics = extract_topics(citations)
        primary_citations_by_claim = extract_primary_citation_by_claim(citations)
        actual_multi_risk_escalation = result["overall_decision"].get(
            "multi_risk_escalation",
            False,
        )

        expected_multi_risk_escalation = expected.get(
            "expected_multi_risk_escalation",
            False,
        )

        multi_risk_escalation_ok = (
            actual_multi_risk_escalation == expected_multi_risk_escalation
        )

        risk_ok = actual_risk == expected["expected_overall_risk"]
        action_ok = actual_action == expected["expected_action"]
        claims_ok = normalize_list(actual_claims) == normalize_list(expected["expected_claims"])
        topics_ok = normalize_list(actual_topics) == normalize_list(expected["expected_topics"])
        multi_risk_escalation_ok = actual_multi_risk_escalation == expected_multi_risk_escalation
        missing_information_severity_ok = (
            actual_missing_information_severity
            == expected_missing_information_severity
        )


        evidence_eval = evaluate_evidence_expectations(
            expected=expected,
            primary_citations_by_claim=primary_citations_by_claim,
        )
        evidence_expectation_ok = evidence_eval["overall_ok"]

        if evidence_expectation_ok:
            evidence_expectation_pass_count += 1

        overall_ok = (
            risk_ok
            and action_ok
            and claims_ok
            and topics_ok
            and multi_risk_escalation_ok
            and missing_information_severity_ok
        )
        if overall_ok:
            pass_count += 1

        confidence = result.get("confidence")
        debug_trace = result.get("debug_trace", {})


        failure_types = build_failure_types(
            risk_ok=risk_ok,
            action_ok=action_ok,
            actual_claims=actual_claims,
            expected_claims=expected["expected_claims"],
            actual_topics=actual_topics,
            expected_topics=expected["expected_topics"],
            evidence_eval=evidence_eval,
            confidence=confidence,
        )

        
        case_result = {
            "case_name": name,
            "pass": overall_ok,
            "expected": expected,
            "actual": {
                "overall_risk": actual_risk,
                "recommended_action": actual_action,
                "claims": actual_claims,
                "topics": actual_topics,
                "primary_citations_by_claim": primary_citations_by_claim,
                "multi_risk_escalation": actual_multi_risk_escalation,
                "missing_information_severity": actual_missing_information_severity,
            },
            "checks": {
                "risk_ok": risk_ok,
                "action_ok": action_ok,
                "claims_ok": claims_ok,
                "topics_ok": topics_ok,
                "evidence_expectation_ok": evidence_expectation_ok,
                "multi_risk_escalation": multi_risk_escalation_ok,
                "missing_information_severity_ok": missing_information_severity_ok,
            },
            "manual_evidence_quality": expected.get("manual_evidence_quality", "not_set"),
            "evidence_expectation_eval": evidence_eval,
            "failure_types": failure_types,
            "confidence": make_json_safe(confidence),
            "debug_trace": make_json_safe(debug_trace),
        }
        case_result["debug_summary"] = build_debug_summary(case_result)

        results.append(case_result)

        print(f"\n=== {name} ===")
        print(f"risk:    actual={actual_risk} expected={expected['expected_overall_risk']} -> {risk_ok}")
        print(f"action:  actual={actual_action} expected={expected['expected_action']} -> {action_ok}")
        print(f"claims:  actual={actual_claims} expected={expected['expected_claims']} -> {claims_ok}")
        print(f"topics:  actual={actual_topics} expected={expected['expected_topics']} -> {topics_ok}")
        print(
            f"multi_risk_escalation: actual={actual_multi_risk_escalation} "
            f"expected={expected_multi_risk_escalation} -> {multi_risk_escalation_ok}"
        )
        print(f"PASS: {overall_ok}")

        print(
            f"evidence_expectation_ok: {evidence_expectation_ok} "
            f"| manual_evidence_quality={expected.get('manual_evidence_quality', 'not_set')}"
        )

        if confidence:
            print(
                f"confidence: {confidence.final_confidence:.2f} "
                f"({confidence.confidence_label}) "
                f"| capped_by={confidence.capped_by}"
            )

        if failure_types:
            print(f"failure_types: {failure_types}")

    metric_summary = build_metric_summary(results)

    summary = {
        "total_cases": len(EVAL_CASES),
        "passed_cases": pass_count,
        "failed_cases": len(EVAL_CASES) - pass_count,
        "pass_rate": round(pass_count / len(EVAL_CASES), 4),
        "evidence_expectation_passed_cases": evidence_expectation_pass_count,
        "evidence_expectation_pass_rate": round(evidence_expectation_pass_count / len(EVAL_CASES), 4),
        "metric_summary": metric_summary,
        "results": results,
    }

    output_dir = Path("eval/results")
    output_dir.mkdir(parents=True, exist_ok=True)

    output_file = output_dir / "latest_run.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    print("\n=== SUMMARY ===")
    print(f"Passed {pass_count}/{len(EVAL_CASES)} cases")
    print(f"Evidence expectation passed {evidence_expectation_pass_count}/{len(EVAL_CASES)} cases")
    print(f"Results saved to: {output_file}")


if __name__ == "__main__":
    main()