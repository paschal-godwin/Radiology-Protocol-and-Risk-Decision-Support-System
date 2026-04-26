from app.schemas.input import (
    RadiologyCaseInput,
    Sex,
    PregnancyStatus,
    PriorContrastReaction,
    UrgencyLevel,
)
from app.rules.missing_info import detect_missing_information


def test_detects_missing_egfr_for_contrast_exam():
    case = RadiologyCaseInput(
        age=45,
        sex=Sex.female,
        pregnancy_status=PregnancyStatus.not_pregnant,
        exam_requested="CT Abdomen",
        contrast_requested=True,
        urgency_level=UrgencyLevel.routine,
        egfr=None,
        allergy_history=False,
        prior_contrast_reaction=PriorContrastReaction.none,
    )

    result = detect_missing_information(case)

    assert "eGFR is missing for a contrast-requested CT exam" in result


def test_detects_unknown_pregnancy_status():
    case = RadiologyCaseInput(
        age=30,
        sex=Sex.female,
        pregnancy_status=PregnancyStatus.unknown,
        exam_requested="CT Abdomen",
        contrast_requested=True,
        urgency_level=UrgencyLevel.routine,
        egfr=80,
        allergy_history=False,
        prior_contrast_reaction=PriorContrastReaction.none,
    )

    result = detect_missing_information(case)

    assert "Pregnancy status is unknown" in result


def test_detects_missing_allergy_history():
    case = RadiologyCaseInput(
        age=50,
        sex=Sex.male,
        pregnancy_status=PregnancyStatus.not_applicable,
        exam_requested="CT Abdomen",
        contrast_requested=True,
        urgency_level=UrgencyLevel.routine,
        egfr=75,
        allergy_history=None,
        prior_contrast_reaction=PriorContrastReaction.none,
    )

    result = detect_missing_information(case)

    assert "Allergy history is missing" in result


def test_returns_empty_list_when_no_missing_information():
    case = RadiologyCaseInput(
        age=50,
        sex=Sex.male,
        pregnancy_status=PregnancyStatus.not_applicable,
        exam_requested="CT Abdomen",
        contrast_requested=True,
        urgency_level=UrgencyLevel.routine,
        egfr=75,
        allergy_history=False,
        prior_contrast_reaction=PriorContrastReaction.none,
    )

    result = detect_missing_information(case)

    assert result == []