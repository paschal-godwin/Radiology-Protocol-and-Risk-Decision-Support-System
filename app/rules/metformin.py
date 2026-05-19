from app.schemas.input import RadiologyCaseInput, MetforminUse, DiabetesStatus 


def assess_metformin_risk(case: RadiologyCaseInput) -> dict:
    if contrast_not_requested := not case.contrast_requested:
        return {
            "flag": None,
            "message": "No Metformin-related risk because contrast is not requested."
        }
    
    if case.diabetes_status == DiabetesStatus.non_diabetic:
        return {
            "flag": None,
            "message": "Patient is non-diabetic. Metformin use not applicable."
        }
    
    if case.diabetes_status == DiabetesStatus.unknown:
        return {
            "flag": "diabetes_status_unknown",
            "message": "Diabetes status is unknown. Metformin use should be interpreted with caution."
        }

    if case.metformin_use == MetforminUse.unknown:
        return {
            "flag": "metformin_risk_hold_required",
            "message": "Metformin use is unknown and should be confirmed before proceeding."
        }
    
    if case.metformin_use == MetforminUse.yes and case.egfr is None:
        return {
            "flag": "metformin_risk_hold_required",
            "message": "Patient is on Metformin, but eGFR is missing. Renal function should be confirmed before contrast-related Metformin guidance is applied.",
            "post_scan_instructions": "Confirm eGFR before deciding whether Metformin should be withheld or continued."
        }

    if case.metformin_use == MetforminUse.yes and case.egfr < 30:
        return {
            "flag": "metformin_risk_hold_required",
            "message": f"Patient is on Metformin. Requested CT exam should be reviewed for potential risk of lactic acidosis.",
            "post_scan_instructions": "Consider holding Metformin for 48 hours post-scan and monitor renal function before resuming."
        }
    
    if case.metformin_use == MetforminUse.yes and case.egfr >=30:
            return {
                "flag": "metformin_risk_low_review_recommended",
                "message": f"Patient is on Metformin. Risk of lactic acidosis is low but monitor renal function post-scan.",
                "post_scan_instructions": "Continue metformin per local policy if eGFR is stable and no AKI is present; advise renal-function review if clinically indicated."
            }


    return {
        "flag": "no_metformin_risk_detected",
        "message": "No Metformin-related risk detected by current V1 rule."
    }