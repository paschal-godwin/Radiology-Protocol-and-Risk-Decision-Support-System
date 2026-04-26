def generate_overall_decision(
    missing_information: list[str],
    renal_risk: dict,
    pregnancy_risk: dict,
    contrast_reaction_risk: dict,
) -> dict:
    renal_flag = renal_risk.get("flag")
    pregnancy_flag = pregnancy_risk.get("flag")
    contrast_flag = contrast_reaction_risk.get("flag")

    if missing_information:
        return {
            "overall_risk_level": "insufficient_information",
            "recommended_action": "hold_and_clarify",
            "can_proceed": False,
            "summary": "Critical information is missing. Do not proceed until the required information is clarified."
        }

    if (
        renal_flag == "high_renal_risk"
        or pregnancy_flag == "pregnancy_risk_review_required"
        or contrast_flag == "high_contrast_reaction_risk"
    ):
        return {
            "overall_risk_level": "high",
            "recommended_action": "hold_and_review",
            "can_proceed": False,
            "summary": "High-risk findings detected. Case should be reviewed before proceeding with contrast-enhanced CT."
        }

    if (
        renal_flag == "moderate_renal_risk"
        or pregnancy_flag == "pregnancy_status_unknown"
        or contrast_flag in [
            "moderate_contrast_reaction_risk",
            "mild_contrast_reaction_risk",
            "contrast_reaction_history_unknown",
        ]
    ):
        return {
            "overall_risk_level": "moderate",
            "recommended_action": "proceed_with_caution_or_review",
            "can_proceed": False,
            "summary": "Moderate-risk findings detected. Proceed only after cautionary review under current policy."
        }

    return {
        "overall_risk_level": "low",
        "recommended_action": "proceed",
        "can_proceed": True,
        "summary": "No major V1 risk flags detected. Requested exam may proceed under current rule set."
    }