from app.schemas.input import RadiologyCaseInput, MetforminUse


def assess_metformin_risk(case: RadiologyCaseInput) -> dict:
    if not case.contrast_requested:
        return {
            "flag": None,
            "message": "No Metformin-related risk because contrast is not requested."
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
    
    if case.metformin_use == MetforminUse.yes and 30 <= case.egfr < 45:
        return {
            "flag": "metformin_risk_low_review_recommended",
            "message": "Patient is on Metformin with moderately reduced eGFR. Contrast use may proceed only with cautionary review under local policy.",
            "post_scan_instructions": "Consider renal-function review and follow local policy on Metformin withholding/resumption."
        }

    if case.metformin_use == MetforminUse.yes and case.egfr >= 45:
        return {
            "flag": "metformin_risk_low_review_recommended",
            "message": "Patient is on Metformin with acceptable eGFR. Metformin-related contrast risk is low under current V1 rule.",
            "post_scan_instructions": "Continue Metformin per local policy if renal function is stable and no AKI is present."
        }


    return {
        "flag": "no_metformin_risk_detected",
        "message": "No Metformin-related risk detected by current V1 rule."
    }