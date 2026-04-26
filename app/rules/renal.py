from app.schemas.input import RadiologyCaseInput


def assess_renal_risk(case: RadiologyCaseInput) -> dict:
    if not case.contrast_requested:
        return {
            "flag": None,
            "message": "No renal contrast risk because contrast is not requested."
        }

    if case.egfr is None:
        return {
            "flag": "renal_function_unknown",
            "message": "Renal function is unavailable for a contrast-requested CT exam."
        }

    if case.egfr < 30:
        return {
            "flag": "high_renal_risk",
            "message": f"eGFR is {case.egfr}, which indicates high renal risk for contrast use."
        }

    if case.egfr < 45:
        return {
            "flag": "moderate_renal_risk",
            "message": f"eGFR is {case.egfr}, which indicates moderate renal risk for contrast use."
        }

    return {
        "flag": None,
        "message": f"eGFR is {case.egfr}, with no renal risk detected by current V1 rule."
    }