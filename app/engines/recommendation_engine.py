def generate_protocol_recommendation(
    overall_decision: dict,
    missing_information: list[str],
    renal_risk: dict,
    pregnancy_risk: dict,
    contrast_reaction_risk: dict,
    metformin_risk: dict,
) -> dict:
    renal_flag = renal_risk.get("flag")
    pregnancy_flag = pregnancy_risk.get("flag")
    contrast_flag = contrast_reaction_risk.get("flag")
    metformin_flag = metformin_risk.get("flag")
    action = overall_decision.get("recommended_action")
    cautionary_notes = overall_decision.get("cautionary_notes")

    if action == "hold_and_clarify":
        return {
            "suggested_protocol": "do_not_proceed_yet",
            "next_steps": missing_information,
            "alternative_consideration": "Reassess protocol after missing information is obtained."
        }

    if action == "hold_and_review":
        next_steps = []

        if renal_flag == "high_renal_risk":
            next_steps.append("Avoid proceeding with contrast until renal risk is reviewed.")
            next_steps.append("Consider non-contrast CT if clinically appropriate.")

        if pregnancy_flag == "pregnancy_risk_review_required":
            next_steps.append("Review pregnancy-related imaging risk before proceeding.")
            next_steps.append("Consider alternative imaging such as ultrasound or MRI where appropriate.")

        if contrast_flag == "high_contrast_reaction_risk":
            next_steps.append("Review severe prior contrast reaction history before proceeding.")
            next_steps.append("Consider non-contrast imaging or alternative modality if appropriate.")
        
        if metformin_flag == "metformin_risk_hold_required":
            next_steps.append("Review Metformin use and eGFR before proceeding.")
            next_steps.append("Consider holding Metformin and monitoring renal function post-scan if proceeding with contrast-enhanced CT.")

        return {
            "suggested_protocol": "hold_contrast_exam_and_review",
            "next_steps": next_steps,
            "alternative_consideration": "Alternative protocol or modality may be required depending on review outcome."
        }

    if action == "proceed_with_caution_or_review":
        next_steps = []

        if renal_flag == "moderate_renal_risk":
            next_steps.append("Proceed only after renal risk review under department policy.")

        if pregnancy_flag == "pregnancy_status_unknown":
            next_steps.append("Confirm pregnancy status before proceeding.")

        if contrast_flag == "moderate_contrast_reaction_risk":
            next_steps.append("Review moderate prior contrast reaction before proceeding.")

        if contrast_flag == "mild_contrast_reaction_risk":
            next_steps.append("Use caution due to mild prior contrast reaction history.")

        if contrast_flag == "contrast_reaction_history_unknown":
            next_steps.append("Clarify prior contrast reaction history before proceeding.")

        if metformin_flag == "metformin_risk_low_review_recommended":
            next_steps.append("Review Metformin use and eGFR before proceeding.")
            next_steps.append("Monitor renal function post-scan if proceeding with contrast-enhanced CT.")

        return {
            "suggested_protocol": "conditional_contrast_protocol",
            "next_steps": next_steps,
            "alternative_consideration": "Proceed only if review is satisfactory; otherwise consider non-contrast CT or another modality."
        }

    return {
        "suggested_protocol": "proceed_with_requested_contrast_protocol",
        "next_steps": ["No major V1 barriers detected. Proceed under current protocol."],
        "alternative_consideration": "No alternative protocol currently required."
    }