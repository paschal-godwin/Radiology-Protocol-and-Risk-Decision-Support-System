from app.rules.missing_info import detect_missing_information
from app.rules.renal import assess_renal_risk
from app.rules.pregnancy import assess_pregnancy_risk
from app.rules.contrast_reaction import assess_contrast_reaction_risk
from app.rules.metformin import assess_metformin_risk
from app.rules.aggregator import generate_overall_decision
from app.engines.recommendation_engine import generate_protocol_recommendation
from app.engines.explanation_engine import generate_explanation
from app.schemas.input import RadiologyCaseInput
from app.rag.retrieval_context_builder import build_retrieval_queries
from app.rag.retriever import retrieve_guideline_evidence
from app.engines.confidence_engine import (
    derive_active_topics_and_claims,
    build_confidence,
)


def run_assessment(case: RadiologyCaseInput) -> dict:
    missing_info = detect_missing_information(case)
    renal_risk = assess_renal_risk(case)
    pregnancy_risk = assess_pregnancy_risk(case)
    contrast_reaction_risk = assess_contrast_reaction_risk(case)
    metformin_risk = assess_metformin_risk(case)
    overall_decision = generate_overall_decision(
        missing_information=missing_info,
        renal_risk=renal_risk,
        pregnancy_risk=pregnancy_risk,
        contrast_reaction_risk=contrast_reaction_risk,
        metformin_risk=metformin_risk,
    )
    

    protocol_recommendation = generate_protocol_recommendation(
        overall_decision=overall_decision,
        missing_information=missing_info,
        renal_risk=renal_risk,
        pregnancy_risk=pregnancy_risk,
        contrast_reaction_risk=contrast_reaction_risk,
        metformin_risk=metformin_risk,
    )

    retrieval_queries = build_retrieval_queries(
        case=case,
        missing_information=missing_info,
        renal_risk=renal_risk,
        pregnancy_risk=pregnancy_risk,
        contrast_reaction_risk=contrast_reaction_risk,
        metformin_risk=metformin_risk,      
        overall_decision=overall_decision,
        protocol_recommendation=protocol_recommendation,
    )

    retrieved_guideline_evidence, retrieval_topic_traces = retrieve_guideline_evidence(
        queries=retrieval_queries,
        per_query_k=3,
        max_total_items=2,
    )

    explanation = generate_explanation(
        case=case.model_dump(),
        missing_information=missing_info,
        renal_risk=renal_risk,
        pregnancy_risk=pregnancy_risk,
        contrast_reaction_risk=contrast_reaction_risk,
        metformin_risk=metformin_risk,
        overall_decision=overall_decision,
        protocol_recommendation=protocol_recommendation,
        retrieved_guideline_evidence=retrieved_guideline_evidence,
    )

    active_topics, active_claims = derive_active_topics_and_claims(
        missing_information=missing_info,
        renal_risk=renal_risk,
        pregnancy_risk=pregnancy_risk,
        contrast_reaction_risk=contrast_reaction_risk,
        metformin_risk=metformin_risk,
    )

    confidence = build_confidence(
        missing_information=missing_info,
        renal_risk=renal_risk,
        pregnancy_risk=pregnancy_risk,
        contrast_reaction_risk=contrast_reaction_risk,
        metformin_risk=metformin_risk,
        overall_decision=overall_decision,
        retrieved_guideline_evidence=retrieved_guideline_evidence,
        explanation=explanation,
    )

    selected_evidence = []
    if retrieved_guideline_evidence and retrieved_guideline_evidence.evidence_items:
        for item in retrieved_guideline_evidence.evidence_items:
            selected_for_claim = None

            for citation in explanation.get("citations", []):
                citation_topic = citation.get("topic") if isinstance(citation, dict) else citation.topic
                citation_claim = citation.get("claim") if isinstance(citation, dict) else citation.claim

                if citation_topic == item.topic:
                    selected_for_claim = citation_claim
                    break

            adjusted_score = None
            for topic_trace in retrieval_topic_traces:
                for candidate in topic_trace.candidates:
                    if (
                        candidate.topic == item.topic
                        and candidate.source_title == item.source_title
                        and candidate.page_number == item.page_number
                    ):
                        adjusted_score = candidate.adjusted_score
                        break

            selected_evidence.append(
                {
                    "topic": item.topic,
                    "source_title": item.source_title,
                    "page_number": item.page_number,
                    "raw_score": item.score,
                    "adjusted_score": adjusted_score,
                    "selected_for_claim": selected_for_claim,
                }
            )

    debug_trace = {
        "rule_trace": {
            "missing_information": missing_info,
            "renal_flag": renal_risk.get("flag"),
            "pregnancy_flag": pregnancy_risk.get("flag"),
            "contrast_reaction_flag": contrast_reaction_risk.get("flag"),
            "active_topics": active_topics,
            "active_claims": active_claims,
        },
        "retrieval_queries": retrieval_queries,
        "selected_evidence": selected_evidence,
        "retrieval_topics": [topic_trace.model_dump() for topic_trace in retrieval_topic_traces],
    }

    return {
        "received_case": case,
        "missing_information": missing_info,
        "renal_risk": renal_risk,
        "pregnancy_risk": pregnancy_risk,
        "contrast_reaction_risk": contrast_reaction_risk,
        "metformin_risk": metformin_risk,
        "overall_decision": overall_decision,
        "protocol_recommendation": protocol_recommendation,
        "explanation": explanation,
        "retrieved_guideline_evidence": retrieved_guideline_evidence,
        "confidence": confidence,
        "debug_trace": debug_trace,
    }