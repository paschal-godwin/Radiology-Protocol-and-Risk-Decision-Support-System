from app.rag.retrieval_context_builder import build_retrieval_context
from app.schemas.input import (
    RadiologyCaseInput,
    Sex,
    PregnancyStatus,
    PriorContrastReaction,
    UrgencyLevel,
)


def test_build_retrieval_context_includes_key_case_and_decision_fields():
    case = RadiologyCaseInput(
        age=67,
        sex=Sex.female,
        pregnancy_status=PregnancyStatus.not_applicable,
        exam_requested="CT abdomen",
        contrast_requested=True,
        urgency_level=UrgencyLevel.routine,
        egfr=28,
        allergy_history=True,
        prior_contrast_reaction=PriorContrastReaction.severe,
    )

    missing_information = []

    renal_risk = {
        "flag": "high",
        "message": "eGFR is below 30; high renal risk.",
    }

    pregnancy_risk = {
        "flag": None,
        "message": "Pregnancy not applicable.",
    }

    contrast_reaction_risk = {
        "flag": "high",
        "message": "Prior severe contrast reaction.",
    }

    overall_decision = {
        "overall_risk_level": "high",
        "recommended_action": "hold_and_review",
        "can_proceed": False,
        "summary": "High-risk case requiring review before contrast administration.",
    }

    protocol_recommendation = {
        "suggested_protocol": "hold_contrast_exam_and_review",
        "next_steps": [
            "Review renal function",
            "Review reaction history",
        ],
        "alternative_consideration": "Consider non-contrast imaging if clinically appropriate.",
    }

    context = build_retrieval_context(
        case=case,
        missing_information=missing_information,
        renal_risk=renal_risk,
        pregnancy_risk=pregnancy_risk,
        contrast_reaction_risk=contrast_reaction_risk,
        overall_decision=overall_decision,
        protocol_recommendation=protocol_recommendation,
    )

    assert "Exam requested: CT abdomen" in context
    assert "Contrast requested: yes" in context
    assert "eGFR: 28.0" in context or "eGFR: 28" in context
    assert "Renal risk: high" in context
    assert "Contrast reaction risk: high" in context
    assert "Recommended action: hold_and_review" in context
    assert "Suggested protocol: hold_contrast_exam_and_review" in context