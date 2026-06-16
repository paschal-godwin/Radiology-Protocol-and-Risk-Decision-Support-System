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
    metformin_risk: dict,
    thyroid_risk: dict,
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

    active_risks = []

    if renal_risk.get("flag") not in {None, "no_renal_risk_detected"}:
        active_risks.append("renal risk")

    if pregnancy_risk.get("flag") not in {None, "no_pregnancy_risk_detected"}:
        active_risks.append("pregnancy considerations")

    if contrast_reaction_risk.get("flag") not in {None, "no_contrast_reaction_risk_detected"}:
        active_risks.append("contrast reaction history")

    if metformin_risk.get("flag") not in {None, "no_metformin_risk_detected"}:
        active_risks.append("metformin-related considerations")

    if thyroid_risk.get("flag") not in {None, "no_thyroid_risk_detected"}:
        active_risks.append("thyroid-related considerations")

    # Keep detailed factors for auditability
    non_risk_flags = {
        None,
        "no_renal_risk_detected",
        "no_pregnancy_risk_detected",
        "no_contrast_reaction_risk_detected",
        "no_metformin_risk_detected",
        "no_thyroid_risk_detected",
    }

    for risk_dict in [
        renal_risk,
        pregnancy_risk,
        contrast_reaction_risk,
        metformin_risk,
        thyroid_risk,
    ]:
        message = risk_dict.get("message")
        flag = risk_dict.get("flag")

        if message and flag not in non_risk_flags:
            rule_based_factors.append(message)
    # Build concise narrative summary
    if active_risks:
        explanation_parts.append(
            f"The case contains the following relevant findings: {', '.join(active_risks)}."
        )

    decision_summary = overall_decision.get("summary")
    if decision_summary:
        explanation_parts.append(decision_summary)

    renal_citation = None
    reaction_citation = None
    pregnancy_citation = None
    metformin_citation = None
    thyroid_citation = None
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

        if metformin_risk.get("flag") in {"metformin_risk_hold_required", "metformin_risk_low_review_recommended"}:
            metformin_citation = _get_best_citation_by_topic(
                retrieved_guideline_evidence, "metformin"
            )

        if thyroid_risk.get("flag") in {"hyperthyroid_contrast_risk", "autonomous_nodule_contrast_risk"}:
            thyroid_citation = _get_best_citation_by_topic(
                retrieved_guideline_evidence, "thyroid"
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

    if metformin_citation:
        evidence_lines.append(
            f"Methformin-related support was retrieved from {_build_citation_label(metformin_citation)}."
        )
        citations.append(
            ExplanationCitation(
                claim="metformin_risk",
                topic=metformin_citation.topic,
                source_title=metformin_citation.source_title,
                page_number=metformin_citation.page_number,
                section=metformin_citation.section,
                snippet=metformin_citation.snippet,
            )
        )

    if thyroid_citation:
        evidence_lines.append(
            f"Thyroid-related support was retrieved from {_build_citation_label(thyroid_citation)}."
        )
        citations.append(
            ExplanationCitation(
                claim="thyroid_risk",
                topic=thyroid_citation.topic,
                source_title=thyroid_citation.source_title,
                page_number=thyroid_citation.page_number,
                section=thyroid_citation.section,
                snippet=thyroid_citation.snippet,
            )
        )

    evidence_summary = " ".join(evidence_lines) if evidence_lines else None


    summary_lines = []

    if active_risks:
        summary_lines.append(
            f"Relevant findings: {', '.join(active_risks)}."
        )

    if decision_summary:
        summary_lines.append(decision_summary)

    concise_summary = "\n\n".join(summary_lines)

    return {
        "reasoning_summary": concise_summary,
        "decision_basis": {
            "exam_requested": case.get("exam_requested"),
            "contrast_requested": case.get("contrast_requested"),
            "overall_risk_level": overall_decision.get("overall_risk_level"),
            "recommended_action": overall_decision.get("recommended_action"),
            "can_proceed": overall_decision.get("can_proceed"),
            "suggested_protocol": protocol_recommendation.get("suggested_protocol"),
        },
        "rule_based_factors": rule_based_factors,
        "evidence_summary": evidence_summary,
        "citations": citations,
    }