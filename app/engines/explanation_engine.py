from app.schemas.output import RetrievedGuidelineEvidence, ExplanationCitation


def _build_citation_label(item) -> str:
    label = item.source_title
    if item.page_number is not None:
        label += f" (p. {item.page_number})"
    return label


def _get_best_citation_by_topic(retrieved_guideline_evidence, topic: str):
    if not retrieved_guideline_evidence or not retrieved_guideline_evidence.evidence_items:
        return None

    for item in retrieved_guideline_evidence.evidence_items:
        if item.topic == topic:
            return item

    return None


def generate_explanation(
    case: dict,
    missing_information: list[str],
    renal_risk: dict,
    pregnancy_risk: dict,
    contrast_reaction_risk: dict,
    overall_decision: dict,
    protocol_recommendation: dict,
    retrieved_guideline_evidence: RetrievedGuidelineEvidence | None = None,
) -> dict:
    explanation_parts = []
    rule_based_factors = []
    citations: list[ExplanationCitation] = []
    evidence_lines = []

    if missing_information:
        explanation_parts.append(
            "Critical information is missing, so a safe protocol decision cannot yet be finalized."
        )
        rule_based_factors.append(
            "Missing required screening information prevents final protocol clearance."
        )

    renal_message = renal_risk.get("message")
    if renal_message and renal_risk.get("flag") is not None:
        explanation_parts.append(renal_message)
        rule_based_factors.append(renal_message)

    pregnancy_message = pregnancy_risk.get("message")
    if pregnancy_message and pregnancy_risk.get("flag") is not None:
        explanation_parts.append(pregnancy_message)
        rule_based_factors.append(pregnancy_message)

    contrast_message = contrast_reaction_risk.get("message")
    if contrast_message and contrast_reaction_risk.get("flag") is not None:
        explanation_parts.append(contrast_message)
        rule_based_factors.append(contrast_message)

    decision_summary = overall_decision.get("summary")
    if decision_summary:
        explanation_parts.append(decision_summary)

    renal_citation = None
    reaction_citation = None
    pregnancy_citation = None

    if retrieved_guideline_evidence and retrieved_guideline_evidence.evidence_items:
        if renal_risk.get("flag") in {"high_renal_risk", "moderate_renal_risk"}:
            renal_citation = _get_best_citation_by_topic(retrieved_guideline_evidence, "renal")

        if contrast_reaction_risk.get("flag") in {
            "high_contrast_reaction_risk",
            "moderate_contrast_reaction_risk",
            "mild_contrast_reaction_risk",
        }:
            reaction_citation = _get_best_citation_by_topic(
                retrieved_guideline_evidence, "contrast_reaction"
            )

        if pregnancy_risk.get("flag") == "pregnancy_risk_review_required":
            pregnancy_citation = _get_best_citation_by_topic(
                retrieved_guideline_evidence, "pregnancy"
            )

    if renal_citation:
        evidence_lines.append(
            f"Renal-risk support was retrieved from {_build_citation_label(renal_citation)}."
        )
        citations.append(
            ExplanationCitation(
                claim="renal_risk",
                topic=renal_citation.topic,
                source_title=renal_citation.source_title,
                page_number=renal_citation.page_number,
                section=renal_citation.section,
                snippet=renal_citation.snippet,
            )
        )

    if reaction_citation:
        evidence_lines.append(
            f"Contrast-reaction support was retrieved from {_build_citation_label(reaction_citation)}."
        )
        citations.append(
            ExplanationCitation(
                claim="contrast_reaction_risk",
                topic=reaction_citation.topic,
                source_title=reaction_citation.source_title,
                page_number=reaction_citation.page_number,
                section=reaction_citation.section,
                snippet=reaction_citation.snippet,
            )
        )

    if pregnancy_citation:
        evidence_lines.append(
            f"Pregnancy-related support was retrieved from {_build_citation_label(pregnancy_citation)}."
        )
        citations.append(
            ExplanationCitation(
                claim="pregnancy_risk",
                topic=pregnancy_citation.topic,
                source_title=pregnancy_citation.source_title,
                page_number=pregnancy_citation.page_number,
                section=pregnancy_citation.section,
                snippet=pregnancy_citation.snippet,
            )
        )

    evidence_summary = " ".join(evidence_lines) if evidence_lines else None

    if evidence_summary:
        explanation_parts.append("Supporting guideline evidence: " + evidence_summary)

    concise_summary = " ".join(explanation_parts)

    return {
        "reasoning_summary": concise_summary,
        "decision_basis": {
            "exam_requested": case.get("exam_requested"),
            "contrast_requested": case.get("contrast_requested"),
            "overall_risk_level": overall_decision.get("overall_risk_level"),
            "recommended_action": overall_decision.get("recommended_action"),
            "suggested_protocol": protocol_recommendation.get("suggested_protocol"),
        },
        "rule_based_factors": rule_based_factors,
        "evidence_summary": evidence_summary,
        "citations": citations,
    }