from fastapi import APIRouter
from app.schemas.input import RadiologyCaseInput
from app.schemas.output import AssessmentResponse
from app.services.assessment_service import run_assessment

router = APIRouter()


@router.post("/assess-case", response_model=AssessmentResponse)
def assess_case(case: RadiologyCaseInput):
    return run_assessment(case)