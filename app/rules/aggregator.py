def count_active_risk_flags(*flags):
    non_risk_flags = {
        None,
        "no_renal_risk_detected",
        "no_pregnancy_risk_detected",
        "no_contrast_reaction_risk_detected",
        "no_allergy_history_risk_detected",
        "no_asthma_risk_detected",
        "no_metformin_risk_detected",
        "no_thyroid_risk_detected",
    }

    return sum(1 for flag in flags if flag not in non_risk_flags)

def generate_overall_decision(
    urgency_level: str,
    missing_information: list[str],
    missing_information_severity: str,
    renal_risk: dict,
    pregnancy_risk: dict,
    contrast_reaction_risk: dict,
    allergy_risk: dict,
    asthma_risk: dict,
    metformin_risk: dict,
    thyroid_risk: dict
) -> dict:
    renal_flag = renal_risk.get("flag")
    pregnancy_flag = pregnancy_risk.get("flag")
    contrast_flag = contrast_reaction_risk.get("flag")
    allergy_flag = allergy_risk.get("flag")
    asthma_flag= asthma_risk.get("flag")
    metformin_flag = metformin_risk.get("flag")
    thyroid_flag = thyroid_risk.get("flag")
    metformin_message = metformin_risk.get("post_scan_instructions")

    active_risk_count = count_active_risk_flags(
        renal_flag,
        pregnancy_flag,
        contrast_flag,
        allergy_flag,
        asthma_flag,
        metformin_flag,
        thyroid_flag,
    )

    multi_risk_escalation = active_risk_count >= 2

    # 1. Missing information should stop routine progression first.
    if missing_information:
        if urgency_level == "emergency" and missing_information_severity == "high":
            return {
                "overall_risk_level": "high",
                "recommended_action": "urgent_radiologist_review",
                "can_proceed": False,
                "summary": (
                    "High-severity missing information is present, but emergency imaging urgency "
                    "may justify proceeding after immediate radiologist review and documented "
                    "risk-benefit assessment."
                ),
                "missing_information_severity": missing_information_severity,
                "emergency_override": True,
                "multi_risk_escalation": False,
            }

        return {
            "overall_risk_level": "insufficient_information",
            "recommended_action": "hold_and_clarify",
            "can_proceed": False,
            "summary": (
                "Critical information is missing. Do not proceed until the required "
                "information is clarified."
            ),
            "missing_information_severity": missing_information_severity,
            "emergency_override": False,
            "multi_risk_escalation": False,
        }

    # 2. Unknown clinical states should be clarified, not treated as simple caution.
    clarify_required = (
        pregnancy_flag == "pregnancy_status_unknown"
        or contrast_flag == "contrast_reaction_history_unknown"
    )

    if clarify_required:
        return {
            "overall_risk_level": "insufficient_information",
            "recommended_action": "hold_and_clarify",
            "can_proceed": False,
            "summary": (
                "Important screening information is unknown. Clarify the relevant "
                "clinical history before proceeding with routine contrast imaging."
            ),
            "cautionary_notes": metformin_message if metformin_message else None,
            "multi_risk_escalation": multi_risk_escalation,
            "missing_information_severity": "moderate",
            "emergency_override": False,
        }

    # 3. Known high/review-level risks should not proceed as routine.
    review_required = (
        renal_flag == "high_renal_risk"
        or pregnancy_flag == "pregnancy_risk_review_required"
        or contrast_flag in {
            "high_contrast_reaction_risk",
        }
        or metformin_flag == "metformin_risk_hold_required"
        or thyroid_flag in {
            "hyperthyroid_contrast_risk",
        }
    )

    if review_required:
        if urgency_level == "emergency":
            return {
                "overall_risk_level": "high",
                "recommended_action": "urgent_radiologist_review",
                "can_proceed": False,
                "summary": (
                    "High-risk or review-level findings are present, but emergency imaging "
                    "urgency may justify proceeding only after immediate radiologist review "
                    "and documented risk-benefit assessment."
                ),
                "cautionary_notes": metformin_message if metformin_message else None,
                "emergency_override": True,
                "multi_risk_escalation": multi_risk_escalation,
                "missing_information_severity": "none",
            }

        return {
            "overall_risk_level": "high",
            "recommended_action": "hold_and_review",
            "can_proceed": False,
            "summary": (
                "Review-level risk findings detected. Case should be reviewed before "
                "proceeding with contrast-enhanced CT."
            ),
            "cautionary_notes": metformin_message if metformin_message else None,
            "multi_risk_escalation": multi_risk_escalation,
            "missing_information_severity": "none",
            "emergency_override": False,
        }

    # 4. Caution-only risks can proceed, but should trigger a yellow/caution state.
    caution_required = (
        renal_flag == "moderate_renal_risk"
        or contrast_flag in {
            "mild_contrast_reaction_risk",
            "moderate_contrast_reaction_risk"}
        or allergy_flag == "unrelated_allergy_history_caution"
        or asthma_flag == "asthma_history_caution"
        or metformin_flag == "metformin_risk_low_review_recommended"
        or thyroid_flag == "autonomous_nodule_contrast_risk"
    )

    if caution_required:
        return {
            "overall_risk_level": "moderate",
            "recommended_action": "proceed_with_caution",
            "can_proceed": True,
            "summary": (
                "Caution-level findings detected. The examination may proceed, but "
                "additional attention and local protocol precautions are required."
            ),
            "cautionary_notes": metformin_message if metformin_message else None,
            "multi_risk_escalation": multi_risk_escalation,
            "missing_information_severity": "none",
            "emergency_override": False,
        }

    # 5. No active risk flags.
    return {
        "overall_risk_level": "low",
        "recommended_action": "proceed",
        "can_proceed": True,
        "summary": "No major V1 risk flags detected. Requested exam may proceed under current rule set.",
        "multi_risk_escalation": False,
        "missing_information_severity": "none",
        "emergency_override": False,
    }