from app.rules.aggregator import generate_overall_decision


def test_returns_insufficient_information_when_missing_info_exists():
    result = generate_overall_decision(
        missing_information=["eGFR is missing"],
        renal_risk={"flag": "renal_function_unknown", "message": "Renal function unavailable."},
        pregnancy_risk={"flag": None, "message": "Pregnancy risk not applicable."},
        contrast_reaction_risk={"flag": None, "message": "No reaction risk."},
    )

    assert result["overall_risk_level"] == "insufficient_information"
    assert result["recommended_action"] == "hold_and_clarify"
    assert result["can_proceed"] is False


def test_returns_high_risk_for_high_renal_risk():
    result = generate_overall_decision(
        missing_information=[],
        renal_risk={"flag": "high_renal_risk", "message": "High renal risk."},
        pregnancy_risk={"flag": None, "message": "Pregnancy risk not applicable."},
        contrast_reaction_risk={"flag": None, "message": "No reaction risk."},
    )

    assert result["overall_risk_level"] == "high"
    assert result["recommended_action"] == "hold_and_review"
    assert result["can_proceed"] is False


def test_returns_high_risk_for_pregnancy_review_required():
    result = generate_overall_decision(
        missing_information=[],
        renal_risk={"flag": "no_renal_risk_detected", "message": "No renal risk."},
        pregnancy_risk={"flag": "pregnancy_risk_review_required", "message": "Pregnancy requires review."},
        contrast_reaction_risk={"flag": None, "message": "No reaction risk."},
    )

    assert result["overall_risk_level"] == "high"
    assert result["recommended_action"] == "hold_and_review"
    assert result["can_proceed"] is False


def test_returns_moderate_risk_for_moderate_renal_risk():
    result = generate_overall_decision(
        missing_information=[],
        renal_risk={"flag": "moderate_renal_risk", "message": "Moderate renal risk."},
        pregnancy_risk={"flag": None, "message": "Pregnancy risk not applicable."},
        contrast_reaction_risk={"flag": None, "message": "No reaction risk."},
    )

    assert result["overall_risk_level"] == "moderate"
    assert result["recommended_action"] == "proceed_with_caution_or_review"
    assert result["can_proceed"] is False


def test_returns_moderate_risk_for_unknown_contrast_reaction_history():
    result = generate_overall_decision(
        missing_information=[],
        renal_risk={"flag": "no_renal_risk_detected", "message": "No renal risk."},
        pregnancy_risk={"flag": None, "message": "Pregnancy risk not applicable."},
        contrast_reaction_risk={"flag": "contrast_reaction_history_unknown", "message": "Reaction history unknown."},
    )

    assert result["overall_risk_level"] == "moderate"
    assert result["recommended_action"] == "proceed_with_caution_or_review"
    assert result["can_proceed"] is False


def test_returns_low_risk_for_clean_case():
    result = generate_overall_decision(
        missing_information=[],
        renal_risk={"flag": "no_renal_risk_detected", "message": "No renal risk."},
        pregnancy_risk={"flag": "no_pregnancy_risk_detected", "message": "No pregnancy risk."},
        contrast_reaction_risk={"flag": "no_contrast_reaction_risk_detected", "message": "No reaction risk."},
    )

    assert result["overall_risk_level"] == "low"
    assert result["recommended_action"] == "proceed"
    assert result["can_proceed"] is True