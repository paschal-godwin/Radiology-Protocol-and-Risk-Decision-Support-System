from app.schemas.input import (
    RadiologyCaseInput,
    Sex,
    PregnancyStatus,
    PriorContrastReaction,
    UrgencyLevel,
)
from app.rules.renal import assess_renal_risk


def test_renal_risk_unknown_when_egfr_missing():
    case = RadiologyCaseInput(
        age=60,
        sex=Sex.male,
        pregnancy_status=PregnancyStatus.not_applicable,
        exam_requested="CT Abdomen",
        contrast_requested=True,
        urgency_level=UrgencyLevel.routine,
        egfr=None,
        allergy_history=False,
        prior_contrast_reaction=PriorContrastReaction.none,
    )

    result = assess_renal_risk(case)

    assert result["flag"] == "renal_function_unknown"


def test_high_renal_risk():
    case = RadiologyCaseInput(
        age=65,
        sex=Sex.male,
        pregnancy_status=PregnancyStatus.not_applicable,
        exam_requested="CT Abdomen",
        contrast_requested=True,
        urgency_level=UrgencyLevel.routine,
        egfr=25,
        allergy_history=False,
        prior_contrast_reaction=PriorContrastReaction.none,
    )

    result = assess_renal_risk(case)

    assert result["flag"] == "high_renal_risk"


def test_moderate_renal_risk():
    case = RadiologyCaseInput(
        age=65,
        sex=Sex.male,
        pregnancy_status=PregnancyStatus.not_applicable,
        exam_requested="CT Abdomen",
        contrast_requested=True,
        urgency_level=UrgencyLevel.routine,
        egfr=40,
        allergy_history=False,
        prior_contrast_reaction=PriorContrastReaction.none,
    )

    result = assess_renal_risk(case)

    assert result["flag"] == "moderate_renal_risk"


def test_no_renal_risk():
    case = RadiologyCaseInput(
        age=45,
        sex=Sex.male,
        pregnancy_status=PregnancyStatus.not_applicable,
        exam_requested="CT Abdomen",
        contrast_requested=True,
        urgency_level=UrgencyLevel.routine,
        egfr=75,
        allergy_history=False,
        prior_contrast_reaction=PriorContrastReaction.none,
    )

    result = assess_renal_risk(case)

    assert result["flag"] == "no_renal_risk_detected"