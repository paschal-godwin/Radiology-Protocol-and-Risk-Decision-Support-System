from app.schemas.input import (
    RadiologyCaseInput,
    Sex,
    PregnancyStatus,
    PriorContrastReaction,
    UrgencyLevel,
)
from app.services.assessment_service import run_assessment


def test_run_assessment_returns_low_risk_for_clean_case():
    case = RadiologyCaseInput(
        age=45,
        sex=Sex.male,
        pregnancy_status=PregnancyStatus.not_applicable,
        exam_requested="CT Abdomen",
        contrast_requested=True,
        urgency_level=UrgencyLevel.routine,
        egfr=78,
        allergy_history=False,
        prior_contrast_reaction=PriorContrastReaction.none,
    )

    result = run_assessment(case)

    assert result["overall_decision"]["overall_risk_level"] == "low"
    assert result["overall_decision"]["recommended_action"] == "proceed"
    assert result["protocol_recommendation"]["suggested_protocol"] == "proceed_with_requested_contrast_protocol"
    assert "retrieved_guideline_evidence" in result
    assert result["retrieved_guideline_evidence"].top_k == 3
    assert len(result["retrieved_guideline_evidence"].evidence_items) == 3
    assert result["retrieved_guideline_evidence"].evidence_items[0].source_title == "ACR Manual on Contrast Media"



def test_run_assessment_returns_insufficient_information_when_egfr_missing():
    case = RadiologyCaseInput(
        age=32,
        sex=Sex.female,
        pregnancy_status=PregnancyStatus.not_pregnant,
        exam_requested="CT Abdomen",
        contrast_requested=True,
        urgency_level=UrgencyLevel.routine,
        egfr=None,
        allergy_history=False,
        prior_contrast_reaction=PriorContrastReaction.none,
    )

    result = run_assessment(case)

    assert result["overall_decision"]["overall_risk_level"] == "insufficient_information"
    assert result["overall_decision"]["recommended_action"] == "hold_and_clarify"
    assert result["protocol_recommendation"]["suggested_protocol"] == "do_not_proceed_yet"
    assert "retrieved_guideline_evidence" in result
    assert result["retrieved_guideline_evidence"].top_k == 3
    assert len(result["retrieved_guideline_evidence"].evidence_items) == 3
    assert result["retrieved_guideline_evidence"].evidence_items[0].source_title == "ACR Manual on Contrast Media"


def test_run_assessment_returns_high_risk_for_severe_contrast_reaction():
    case = RadiologyCaseInput(
        age=50,
        sex=Sex.female,
        pregnancy_status=PregnancyStatus.not_pregnant,
        exam_requested="CT Abdomen",
        contrast_requested=True,
        urgency_level=UrgencyLevel.routine,
        egfr=70,
        allergy_history=True,
        prior_contrast_reaction=PriorContrastReaction.severe,
    )

    result = run_assessment(case)

    assert result["overall_decision"]["overall_risk_level"] == "high"
    assert result["overall_decision"]["recommended_action"] == "hold_and_review"
    assert result["protocol_recommendation"]["suggested_protocol"] == "hold_contrast_exam_and_review"
    assert "retrieved_guideline_evidence" in result
    assert result["retrieved_guideline_evidence"].top_k == 3
    assert len(result["retrieved_guideline_evidence"].evidence_items) == 3
    assert result["retrieved_guideline_evidence"].evidence_items[0].source_title == "ACR Manual on Contrast Media"

