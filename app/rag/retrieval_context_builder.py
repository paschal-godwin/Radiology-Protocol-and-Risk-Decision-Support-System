from app.schemas.input import RadiologyCaseInput


def build_retrieval_queries(
    case: RadiologyCaseInput,
    missing_information: list[str],
    renal_risk: dict,
    pregnancy_risk: dict,
    contrast_reaction_risk: dict,
    metformin_risk: dict,
    thyroid_risk: dict,
    overall_decision: dict,
    protocol_recommendation: dict,
) -> list[dict]:
    """
    Build focused retrieval queries only for true risk-supporting topics.
    Missing-information states do not trigger retrieval, because they are
    workflow/completeness issues rather than evidence-backed risk claims.
    """

    queries = []

    common_context = (
        f"Exam requested: {case.exam_requested}. "
        f"Contrast requested: {'yes' if case.contrast_requested else 'no'}. "
        f"Urgency level: {case.urgency_level.value}. "
        f"Overall risk level: {overall_decision.get('overall_risk_level')}. "
        f"Recommended action: {overall_decision.get('recommended_action')}. "
        f"Suggested protocol: {protocol_recommendation.get('suggested_protocol')}."
    )

    renal_flag = renal_risk.get("flag")
    if renal_flag == "high_renal_risk":
        queries.append({
            "topic": "renal",
            "query": (
                f"{common_context} "
                f"Patient eGFR: {case.egfr}. "
                "Iodinated contrast use in severe renal impairment, eGFR threshold precautions, "
                "review before proceeding, renal risk considerations."
            )
        })
    elif renal_flag == "moderate_renal_risk":
        queries.append({
            "topic": "renal",
            "query": (
                f"{common_context} "
                f"Patient eGFR: {case.egfr}. "
                "Iodinated contrast renal risk precautions and kidney function screening."
            )
        })

    reaction_flag = contrast_reaction_risk.get("flag")
    if reaction_flag == "high_contrast_reaction_risk":
        queries.append({
            "topic": "contrast_reaction",
            "query": (
                f"{common_context} "
                f"Prior contrast reaction: {case.prior_contrast_reaction.value}. "
                "Prior severe contrast reaction, hypersensitivity precautions, "
                "contrast re-administration risk, premedication or avoidance."
            )
        })
    elif reaction_flag in {
        "moderate_contrast_reaction_risk",
        "mild_contrast_reaction_risk",
    }:
        queries.append({
            "topic": "contrast_reaction",
            "query": (
                f"{common_context} "
                f"Prior contrast reaction: {case.prior_contrast_reaction.value}. "
                "Contrast reaction precautions and adverse reaction screening."
            )
        })

    pregnancy_flag = pregnancy_risk.get("flag")
    if pregnancy_flag == "pregnancy_risk_review_required":
        queries.append({
            "topic": "pregnancy",
            "query": (
                f"{common_context} "
                f"Pregnancy status: {case.pregnancy_status.value}. "
                "Imaging in pregnancy, contrast safety in pregnancy, precautions before proceeding."
            )
        })

    metformin_flag = metformin_risk.get("flag")
    if metformin_flag in {"metformin_risk_hold_required", "metformin_risk_low_review_recommended"}:
        queries.append({
            "topic": "metformin",
            "query": (
                f"{common_context} "
                f"Patient is on metformin: {case.metformin_use.value}. "
                "Iodinated contrast use in patients on metformin, renal function monitoring, "
                "precautions and contraindications."
            )
        })
    
    thyroid_flag = thyroid_risk.get("flag")
    if thyroid_flag in {"hyperthyroid_contrast_risk", "autonomous_nodule_contrast_risk"}:
        queries.append({
            "topic": "thyroid",
            "query": (
                f"{common_context} "
                f"Patient thyroid status: {case.thyroid_status.value}. "
                "Iodinated contrast use in patients with thyroid conditions, hyperthyroidism, "
                "autonomous nodules, endocrinology consultation, precautions before proceeding."
            )
        })

    # No fallback retrieval for missing-information-only cases.
    # Retrieval is now reserved for real risk-supporting evidence.

    if not queries and overall_decision.get("overall_risk_level") not in {"low", "insufficient_information"}:
        queries.append({
            "topic": "general",
            "query": (
                f"{common_context} "
                "General iodinated contrast safety screening and appropriate next-step recommendations."
            )
        })

    return queries