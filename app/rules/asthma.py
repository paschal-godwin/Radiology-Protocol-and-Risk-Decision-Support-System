from app.schemas.input import RadiologyCaseInput


def assess_asthma_risk(case: RadiologyCaseInput) -> dict:
    """
    Assesses asthma history as a contrast safety modifier.

    This rule is separate from:
    - unrelated allergy history
    - prior contrast reaction history

    In V1, asthma history is treated as a caution-level finding,
    not an automatic reason to withhold iodinated contrast.
    """

    if not case.contrast_requested:
        return {
            "flag": None,
            "message": "Asthma-related contrast risk not applicable because contrast is not requested."
        }

    if case.asthma_history is True:
        return {
            "flag": "asthma_history_caution",
            "message": (
                "Asthma history noted. This does not automatically prevent iodinated "
                "contrast use, but proceed with caution and ensure readiness to manage "
                "bronchospasm or allergic-like reaction according to local department protocol."
            )
        }

    return {
        "flag": "no_asthma_risk_detected",
        "message": "No asthma-related contrast risk detected by current rule."
    }