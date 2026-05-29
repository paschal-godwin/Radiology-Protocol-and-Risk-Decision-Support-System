def count_active_risk_flags(*flags):
    non_risk_flags = {
        None,
        "no_renal_risk_detected",
        "no_pregnancy_risk_detected",
        "no_contrast_reaction_risk_detected",
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
    metformin_risk: dict,
    thyroid_risk: dict
) -> dict:
    renal_flag = renal_risk.get("flag")
    pregnancy_flag = pregnancy_risk.get("flag")
    contrast_flag = contrast_reaction_risk.get("flag")
    metformin_flag = metformin_risk.get("flag")
    thyroid_flag = thyroid_risk.get("flag")     
    metformin_message= metformin_risk.get("post_scan_instructions")
    
    active_risk_count = count_active_risk_flags(
    renal_flag,
    pregnancy_flag,
    contrast_flag,
    metformin_flag,
    thyroid_flag,
)

    multi_risk_escalation = active_risk_count >= 2

    if missing_information:
        return {
            "overall_risk_level": "insufficient_information",
            "recommended_action": "hold_and_clarify",
            "can_proceed": False,
            "summary": "Critical information is missing. Do not proceed until the required information is clarified.",
            "missing_information_severity": missing_information_severity,
        }

    if (
        renal_flag == "high_renal_risk"
        or pregnancy_flag == "pregnancy_risk_review_required"
        or contrast_flag == "high_contrast_reaction_risk"
        or metformin_flag == "metformin_risk_hold_required"
        or thyroid_flag == "hyperthyroid_contrast_risk"
    ):
        if urgency_level == "emergency":
                return {
                    "overall_risk_level": "high",
                    "recommended_action": "urgent_radiologist_review",
                    "can_proceed": False,
                    "summary": (
                        "High-risk findings detected, but emergency imaging urgency "
                        "may justify proceeding after immediate radiologist review "
                        "and risk-benefit assessment."
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
            "summary": "High-risk findings detected. Case should be reviewed before proceeding with contrast-enhanced CT.",
            "cautionary_notes": metformin_message if metformin_message else None,
            "multi_risk_escalation": multi_risk_escalation,
            "missing_information_severity": "none",
        }

    if (
        renal_flag == "moderate_renal_risk"
        or pregnancy_flag == "pregnancy_status_unknown"
        or contrast_flag in [
            "moderate_contrast_reaction_risk",
            "mild_contrast_reaction_risk",
            "contrast_reaction_history_unknown",
        ]
        or metformin_flag == "metformin_risk_low_review_recommended"
        or thyroid_flag == "autonomous_nodule_contrast_risk"
    ):
        return {
            "overall_risk_level": "moderate",
            "recommended_action": "proceed_with_caution_or_review",
            "can_proceed": False,
            "summary": "Moderate-risk findings detected. Proceed only after cautionary review under current policy.",
            "cautionary_notes": metformin_message if metformin_message else None,
            "multi_risk_escalation": multi_risk_escalation,
            "missing_information_severity": "none",
        }

    return {
        "overall_risk_level": "low",
        "recommended_action": "proceed",
        "can_proceed": True,
        "summary": "No major V1 risk flags detected. Requested exam may proceed under current rule set.",
        "multi_risk_escalation": False,
        "missing_information_severity": "none",
    }