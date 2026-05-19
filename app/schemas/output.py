from pydantic import BaseModel, Field
from typing import List, Optional, Any


class RiskAssessmentResult(BaseModel):
    flag: Optional[str]
    message: str


class OverallDecision(BaseModel):
    overall_risk_level: str
    recommended_action: str
    can_proceed: bool
    summary: str


class ProtocolRecommendation(BaseModel):
    suggested_protocol: str
    next_steps: List[str]
    alternative_consideration: str


class ExplanationDecisionBasis(BaseModel):
    exam_requested: str
    contrast_requested: bool
    overall_risk_level: str
    recommended_action: str
    suggested_protocol: str


class ExplanationCitation(BaseModel):
    claim: str
    topic: Optional[str] = None
    source_title: str
    page_number: Optional[int] = None
    section: Optional[str] = None
    snippet: str


class ExplanationResult(BaseModel):
    reasoning_summary: str
    decision_basis: ExplanationDecisionBasis
    rule_based_factors: List[str] = []
    evidence_summary: Optional[str] = None
    citations: List[ExplanationCitation] = []


class GuidelineEvidence(BaseModel):
    topic: Optional[str] = None
    source_title: str
    section: Optional[str] = None
    score: Optional[float] = None
    page_number: Optional[int] = None
    snippet: str


class RetrievedGuidelineEvidence(BaseModel):
    query_used: str
    top_k: int
    evidence_items: List[GuidelineEvidence]


class ConfidenceComponent(BaseModel):
    score: float = Field(ge=0.0, le=1.0)
    reasons: List[str] = []


class ConfidenceBreakdown(BaseModel):
    rule_confidence: ConfidenceComponent
    retrieval_confidence: ConfidenceComponent
    citation_alignment_confidence: ConfidenceComponent
    completeness_confidence: ConfidenceComponent
    final_confidence: float = Field(ge=0.0, le=1.0)
    confidence_label: str
    capped_by: Optional[str] = None


class RuleTrace(BaseModel):
    missing_information: List[str]
    renal_flag: Optional[str] = None
    pregnancy_flag: Optional[str] = None
    contrast_reaction_flag: Optional[str] = None
    metformin_flag: Optional[str] = None
    thyroid_flag: Optional[str] = None
    active_topics: List[str] = []
    active_claims: List[str] = []


class RetrievalQueryTrace(BaseModel):
    topic: str
    query: str


class RetrievalSelectionTrace(BaseModel):
    topic: Optional[str] = None
    source_title: str
    page_number: Optional[int] = None
    raw_score: Optional[float] = None
    adjusted_score: Optional[float] = None
    selected_for_claim: Optional[str] = None


class RetrievalCandidateTrace(BaseModel):
    topic: str
    source_title: str
    page_number: Optional[int] = None
    section: Optional[str] = None
    raw_score: Optional[float] = None
    cleaned_snippet: str
    keyword_matches: int = 0
    keyword_bonus: float = 0.0
    claim_keyword_matches: int = 0
    claim_alignment_bonus: float = 0.0
    section_bonus: float = 0.0
    generic_penalty: float = 0.0
    adjusted_score: Optional[float] = None
    selected: bool = False
    rejection_reason: Optional[str] = None

class RetrievalTopicTrace(BaseModel):
    topic: str
    query: str
    candidates: List[RetrievalCandidateTrace] = []

class MedicationPrecaution(BaseModel):
    medication: str
    flag: Optional[str] = None
    message: str
    post_scan_instructions: Optional[str] = None


class DebugTrace(BaseModel):
    rule_trace: RuleTrace
    retrieval_queries: List[RetrievalQueryTrace] = []
    selected_evidence: List[RetrievalSelectionTrace] = []
    retrieval_topics: List[RetrievalTopicTrace] = []


class AssessmentResponse(BaseModel):
    received_case: Any
    missing_information: List[str]
    renal_risk: RiskAssessmentResult
    pregnancy_risk: RiskAssessmentResult
    contrast_reaction_risk: RiskAssessmentResult
    metformin_risk: RiskAssessmentResult
    thyroid_risk: RiskAssessmentResult
    contrast_medication_precautions: List[MedicationPrecaution] = []
    overall_decision: OverallDecision
    protocol_recommendation: ProtocolRecommendation
    explanation: ExplanationResult
    retrieved_guideline_evidence: Optional[RetrievedGuidelineEvidence] = None
    confidence: Optional[ConfidenceBreakdown] = None
    debug_trace: Optional[DebugTrace] = None