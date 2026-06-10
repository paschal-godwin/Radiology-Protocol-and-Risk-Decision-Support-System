def generate_protocol_recommendation(
    overall_decision: dict,
    missing_information: list[str],
    missing_information_severity: str,
    renal_risk: dict,
    pregnancy_risk: dict,
    contrast_reaction_risk: dict,
    metformin_risk: dict,
    thyroid_risk: dict,
) -> dict:
    renal_flag = renal_risk.get("flag")
    pregnancy_flag = pregnancy_risk.get("flag")
    contrast_flag = contrast_reaction_risk.get("flag")
    metformin_flag = metformin_risk.get("flag")
    thyroid_flag = thyroid_risk.get("flag")
    action = overall_decision.get("recommended_action")
    contrast_medication_precautions = overall_decision.get("contrast_medication_precautions", [])
    
    if action == "hold_and_clarify":
        if missing_information_severity == "high":
            severity_note = (
                "High-severity missing information detected. "
                "Do not proceed until this information is clarified."
            )
        elif missing_information_severity == "moderate":
            severity_note = (
                "Moderate-severity missing information detected. "
                "Clarify before proceeding under current policy."
            )
        else:
            severity_note = (
                "Missing information detected. "
                "Clarify before final protocol decision."
            )

        return {
            "suggested_protocol": "do_not_proceed_yet",
            "next_steps": [severity_note] + missing_information,
            "alternative_consideration": "Reassess protocol after missing information is obtained."
        }
    if action == "urgent_radiologist_review":
        next_steps = []

        if missing_information:
            next_steps.append(
                "High-severity missing information is present in an emergency context."
            )
            next_steps.append(
                "Proceed only after immediate radiologist review and documented risk-benefit assessment."
            )
            next_steps.append(
                "Clarify missing information as soon as clinically feasible, but do not treat the missing field as routine workflow delay if emergency imaging is time-critical."
            )

        if renal_flag == "high_renal_risk":
            next_steps.append(
                "Urgent radiologist review required due to severe renal risk and emergency imaging context."
            )
            next_steps.append(
                "Proceed only if the emergency diagnostic benefit outweighs the renal risk."
            )
            next_steps.append(
                "Use renal-protective precautions according to local department policy where appropriate."
            )

        if pregnancy_flag == "pregnancy_risk_review_required":
            next_steps.append(
                "Urgent senior review required due to pregnancy-related imaging risk and emergency context."
            )

        if contrast_flag == "high_contrast_reaction_risk":
            next_steps.append(
                "Urgent review required due to severe prior contrast reaction history."
            )

        if metformin_flag == "metformin_risk_hold_required":
            next_steps.append(
                "Review Metformin use urgently and arrange post-contrast renal function monitoring if contrast is administered."
            )

        if thyroid_flag == "hyperthyroid_contrast_risk":
            next_steps.append(
                "Urgent thyroid-risk review required before iodinated contrast if clinically feasible."
            )

        return {
            "suggested_protocol": "emergency_radiologist_review_protocol",
            "next_steps": next_steps,
            "alternative_consideration": (
                "Emergency imaging may proceed only after urgent risk-benefit review; "
                "consider non-contrast CT or alternative modality if it can answer the clinical question."
            )
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

        if thyroid_flag == "hyperthyroid_contrast_risk":
            next_steps.append("Review thyroid status and consider endocrinology consultation before proceeding with contrast.")
            next_steps.append("Consider non-contrast imaging or alternative modality if appropriate.")

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

        if thyroid_flag == "autonomous_nodule_contrast_risk":
            next_steps.append("Review thyroid status and consider endocrinology consultation before proceeding with contrast.")
            next_steps.append("Consider non-contrast imaging or alternative modality if appropriate.")

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