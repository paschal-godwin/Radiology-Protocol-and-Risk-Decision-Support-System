from app.schemas.input import RadiologyCaseInput


def assess_allergy_history_risk(case: RadiologyCaseInput) -> dict:
    """
    Assesses unrelated allergy history as a contrast safety modifier.

    This rule is intentionally separate from prior contrast reaction history.
    Prior contrast reaction is handled by contrast_reaction.py.
    """

    if not case.contrast_requested:
        return {
            "flag": None,
            "message": "Allergy-history risk not applicable because contrast is not requested."
        }

    if case.allergy_history is True:
        return {
            "flag": "unrelated_allergy_history_caution",
            "message": (
                "Unrelated allergy history noted. This does not automatically prevent "
                "iodinated contrast use, but proceed with caution and ensure contrast "
                "reaction readiness according to local department protocol."
            )
        }

    return {
        "flag": "no_allergy_history_risk_detected",
        "message": "No unrelated allergy-history risk detected by current rule."
    }