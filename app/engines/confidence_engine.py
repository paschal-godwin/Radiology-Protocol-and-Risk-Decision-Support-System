from typing import List, Tuple

from app.schemas.output import (
    ConfidenceBreakdown,
    ConfidenceComponent,
)


def derive_active_topics_and_claims(
    missing_information: List[str],
    renal_risk: dict,
    pregnancy_risk: dict,
    contrast_reaction_risk: dict,
) -> Tuple[List[str], List[str]]:
    active_topics = []
    active_claims = []

    if renal_risk.get("flag") in {"high_renal_risk", "moderate_renal_risk"}:
        active_topics.append("renal")
        active_claims.append("renal_risk")

    if contrast_reaction_risk.get("flag") in {
        "high_contrast_reaction_risk",
        "moderate_contrast_reaction_risk",
        "mild_contrast_reaction_risk",
    }:
        active_topics.append("contrast_reaction")
        active_claims.append("contrast_reaction_risk")

    if pregnancy_risk.get("flag") == "pregnancy_risk_review_required":
        active_topics.append("pregnancy")
        active_claims.append("pregnancy_risk")

    # Missing information is intentionally NOT added as an active claim/topic.
    # It is handled through completeness confidence, not retrieval/citation support.

    return active_topics, active_claims


def compute_rule_confidence(
    missing_information: List[str],
    renal_risk: dict,
    pregnancy_risk: dict,
    contrast_reaction_risk: dict,
    overall_decision: dict,
) -> ConfidenceComponent:
    reasons = []

    if missing_information:
        return ConfidenceComponent(
            score=0.35,
            reasons=[
                "Critical information is missing, so deterministic decision certainty is limited."
            ],
        )

    active_high_flags = [
        renal_risk.get("flag") == "high_renal_risk",
        pregnancy_risk.get("flag") == "pregnancy_risk_review_required",
        contrast_reaction_risk.get("flag") == "high_contrast_reaction_risk",
    ]

    active_moderate_flags = [
        renal_risk.get("flag") == "moderate_renal_risk",
        pregnancy_risk.get("flag") == "pregnancy_status_unknown",
        contrast_reaction_risk.get("flag") in {
            "moderate_contrast_reaction_risk",
            "mild_contrast_reaction_risk",
            "contrast_reaction_history_unknown",
        },
    ]

    if any(active_high_flags):
        reasons.append("One or more high-risk deterministic rule conditions were triggered.")
        reasons.append(
            f"Overall decision is '{overall_decision.get('overall_risk_level')}' with action "
            f"'{overall_decision.get('recommended_action')}'."
        )
        return ConfidenceComponent(score=0.92, reasons=reasons)

    if any(active_moderate_flags):
        reasons.append("Moderate or review-requiring deterministic rule conditions were triggered.")
        reasons.append(
            f"Overall decision is '{overall_decision.get('overall_risk_level')}' with action "
            f"'{overall_decision.get('recommended_action')}'."
        )
        return ConfidenceComponent(score=0.75, reasons=reasons)

    reasons.append("No major deterministic V1 risk flags were triggered.")
    reasons.append(
        f"Overall decision is '{overall_decision.get('overall_risk_level')}' with action "
        f"'{overall_decision.get('recommended_action')}'."
    )
    return ConfidenceComponent(score=0.85, reasons=reasons)


def compute_completeness_confidence(
    missing_information: List[str],
) -> ConfidenceComponent:
    if missing_information:
        return ConfidenceComponent(
            score=0.20,
            reasons=[
                f"Missing information present: {len(missing_information)} item(s).",
                "Missing screening information reduces confidence in safe decision support.",
            ],
        )

    return ConfidenceComponent(
        score=0.95,
        reasons=["Required screening information is present."],
    )


def compute_retrieval_confidence(
    active_topics: List[str],
    retrieved_guideline_evidence,
) -> ConfidenceComponent:
    reasons = []

    if not active_topics:
        return ConfidenceComponent(
            score=0.90,
            reasons=["No active risk topics required evidence support."],
        )

    if (
        not retrieved_guideline_evidence
        or not retrieved_guideline_evidence.evidence_items
    ):
        return ConfidenceComponent(
            score=0.20,
            reasons=["No evidence items were retrieved for active risk topics."],
        )

    selected_topics = {
        item.topic for item in retrieved_guideline_evidence.evidence_items if item.topic
    }

    covered_topics = [topic for topic in active_topics if topic in selected_topics]
    coverage_ratio = len(covered_topics) / len(active_topics)

    scores = [
        item.score
        for item in retrieved_guideline_evidence.evidence_items
        if item.score is not None
    ]

    if scores:
        avg_distance = sum(scores) / len(scores)
        avg_strength = max(0.0, min(1.0, 1.0 - avg_distance))
    else:
        avg_strength = 0.40

    score = (0.60 * coverage_ratio) + (0.40 * avg_strength)

    if coverage_ratio == 1.0:
        reasons.append("All active risk topics received selected evidence.")
    else:
        reasons.append("Not all active risk topics received selected evidence.")

    reasons.append(f"Topic coverage ratio: {coverage_ratio:.2f}.")
    reasons.append(f"Average evidence strength proxy: {avg_strength:.2f}.")

    return ConfidenceComponent(
        score=max(0.0, min(1.0, score)),
        reasons=reasons,
    )


def compute_citation_alignment_confidence(
    active_claims: List[str],
    explanation: dict,
) -> ConfidenceComponent:
    reasons = []

    citations = explanation.get("citations", []) if explanation else []

    actual_claims = []
    for citation in citations:
        if isinstance(citation, dict):
            actual_claims.append(citation.get("claim"))
        else:
            actual_claims.append(citation.claim)

    if not active_claims:
        if actual_claims:
            return ConfidenceComponent(
                score=0.60,
                reasons=[
                    "No active evidence-backed claims were expected, but citations were still emitted.",
                    "This may indicate unnecessary evidence attachment.",
                ],
            )
        return ConfidenceComponent(
            score=0.95,
            reasons=["No active evidence-backed claims required citation support."],
        )

    matched = sum(1 for claim in active_claims if claim in actual_claims)
    coverage = matched / len(active_claims)

    unexpected_claims = [
        claim for claim in actual_claims
        if claim and claim not in active_claims
    ]

    missing_claims = [
        claim for claim in active_claims
        if claim not in actual_claims
    ]

    score = coverage

    if missing_claims:
        score -= 0.15 * len(missing_claims)
        reasons.append(
            f"Missing citation support for claim(s): {', '.join(missing_claims)}."
        )

    if unexpected_claims:
        score -= 0.15 * len(unexpected_claims)
        reasons.append(
            f"Unexpected citation claim(s) emitted: {', '.join(unexpected_claims)}."
        )

    if coverage == 1.0:
        reasons.append("Each active claim received citation support.")
    else:
        reasons.append("One or more active claims did not receive citation support.")

    reasons.append(f"Claim-citation coverage ratio: {coverage:.2f}.")

    return ConfidenceComponent(
        score=max(0.0, min(1.0, score)),
        reasons=reasons,
    )


def confidence_label(score: float) -> str:
    if score >= 0.85:
        return "high"
    if score >= 0.60:
        return "moderate"
    if score >= 0.35:
        return "low"
    return "very_low"


def build_confidence(
    missing_information: List[str],
    renal_risk: dict,
    pregnancy_risk: dict,
    contrast_reaction_risk: dict,
    overall_decision: dict,
    retrieved_guideline_evidence,
    explanation: dict,
) -> ConfidenceBreakdown:
    active_topics, active_claims = derive_active_topics_and_claims(
        missing_information=missing_information,
        renal_risk=renal_risk,
        pregnancy_risk=pregnancy_risk,
        contrast_reaction_risk=contrast_reaction_risk,
    )

    rule_conf = compute_rule_confidence(
        missing_information=missing_information,
        renal_risk=renal_risk,
        pregnancy_risk=pregnancy_risk,
        contrast_reaction_risk=contrast_reaction_risk,
        overall_decision=overall_decision,
    )

    completeness_conf = compute_completeness_confidence(
        missing_information=missing_information,
    )

    retrieval_conf = compute_retrieval_confidence(
        active_topics=active_topics,
        retrieved_guideline_evidence=retrieved_guideline_evidence,
    )

    citation_conf = compute_citation_alignment_confidence(
        active_claims=active_claims,
        explanation=explanation,
    )

    component_scores = {
        "rule_confidence": rule_conf.score,
        "completeness_confidence": completeness_conf.score,
        "retrieval_confidence": retrieval_conf.score,
        "citation_alignment_confidence": citation_conf.score,
    }

    final_confidence = min(component_scores.values())
    capped_by = min(component_scores, key=component_scores.get)

    return ConfidenceBreakdown(
        rule_confidence=rule_conf,
        retrieval_confidence=retrieval_conf,
        citation_alignment_confidence=citation_conf,
        completeness_confidence=completeness_conf,
        final_confidence=final_confidence,
        confidence_label=confidence_label(final_confidence),
        capped_by=capped_by,
    )