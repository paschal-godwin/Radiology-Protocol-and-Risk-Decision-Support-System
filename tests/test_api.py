from fastapi.testclient import TestClient
from app.api.main import app

client = TestClient(app)


def test_health_endpoint():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_assess_case_returns_low_risk_for_clean_case():
    payload = {
        "age": 45,
        "sex": "male",
        "pregnancy_status": "not_applicable",
        "exam_requested": "CT Abdomen",
        "contrast_requested": True,
        "urgency_level": "routine",
        "egfr": 80,
        "allergy_history": False,
        "prior_contrast_reaction": "none"
    }

    response = client.post("/assess-case", json=payload)

    assert response.status_code == 200

    data = response.json()
    assert data["overall_decision"]["overall_risk_level"] == "low"
    assert data["overall_decision"]["recommended_action"] == "proceed"
    assert data["protocol_recommendation"]["suggested_protocol"] == "proceed_with_requested_contrast_protocol"
    assert "retrieved_guideline_evidence" in data
    assert data["retrieved_guideline_evidence"]["top_k"] == 3
    assert len(data["retrieved_guideline_evidence"]["evidence_items"]) == 3
    assert data["retrieved_guideline_evidence"]["evidence_items"][0]["source_title"] == "ACR Manual on Contrast Media"

def test_assess_case_returns_insufficient_information_when_egfr_missing():
    payload = {
        "age": 32,
        "sex": "female",
        "pregnancy_status": "not_pregnant",
        "exam_requested": "CT Abdomen",
        "contrast_requested": True,
        "urgency_level": "routine",
        "egfr": None,
        "allergy_history": False,
        "prior_contrast_reaction": "none"
    }

    response = client.post("/assess-case", json=payload)

    assert response.status_code == 200

    data = response.json()
    assert data["overall_decision"]["overall_risk_level"] == "insufficient_information"
    assert data["overall_decision"]["recommended_action"] == "hold_and_clarify"
    assert data["protocol_recommendation"]["suggested_protocol"] == "do_not_proceed_yet"
    assert "retrieved_guideline_evidence" in data
    assert data["retrieved_guideline_evidence"]["top_k"] == 3
    assert len(data["retrieved_guideline_evidence"]["evidence_items"]) == 3
    assert data["retrieved_guideline_evidence"]["evidence_items"][0]["source_title"] == "ACR Manual on Contrast Media"

def test_assess_case_rejects_invalid_enum_value():
    payload = {
        "age": 45,
        "sex": "invalid_value",
        "pregnancy_status": "not_applicable",
        "exam_requested": "CT Abdomen",
        "contrast_requested": True,
        "urgency_level": "routine",
        "egfr": 80,
        "allergy_history": False,
        "prior_contrast_reaction": "none"
    }

    response = client.post("/assess-case", json=payload)

    assert response.status_code == 422