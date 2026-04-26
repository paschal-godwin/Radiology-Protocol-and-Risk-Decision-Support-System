from typing import List, Tuple

from app.schemas.output import (
    GuidelineEvidence,
    RetrievedGuidelineEvidence,
    RetrievalCandidateTrace,
    RetrievalTopicTrace,
)
from app.rag.vectorstore import load_faiss_index
from app.rag.evidence_selector import (
    select_best_evidence_per_topic,
    compute_selection_details,
)


SIMILARITY_THRESHOLD = 0.85


def clean_snippet(text: str, max_length: int = 320) -> str:
    cleaned = " ".join(text.strip().split())

    bibliography_signals = [
        "radiology 1991",
        "ajr 1991",
        "ajr 2001",
        "eur radiol",
        "revision history",
        "major revision",
        "et al.",
        "clin north am.",
        "expert opin drug saf.",
        "j allergy clin immunol.",
    ]

    lowered = cleaned.lower()
    if any(signal in lowered for signal in bibliography_signals):
        return ""

    return cleaned[:max_length]


def retrieve_guideline_evidence(
    queries: List[dict],
    per_query_k: int = 3,
    max_total_items: int = 2,
) -> Tuple[RetrievedGuidelineEvidence, List[RetrievalTopicTrace]]:
    """
    Retrieve candidates per topic, compute deterministic score breakdowns,
    select the best evidence, and return both selected evidence and
    full candidate-level retrieval traces.
    """
    vectorstore = load_faiss_index()
    collected_items: List[GuidelineEvidence] = []
    topic_traces: List[RetrievalTopicTrace] = []
    seen_keys = set()

    print("\n--- RETRIEVAL DEBUG ---")

    for item in queries:
        topic = item["topic"]
        query = item["query"]

        print(f"\n[TOPIC: {topic}]")
        docs_and_scores = vectorstore.similarity_search_with_score(query, k=per_query_k)

        topic_candidates: List[RetrievalCandidateTrace] = []

        for doc, score in docs_and_scores:
            source_title = doc.metadata.get("source_title", "Unknown Source")
            page_number = doc.metadata.get("page_number")
            section = doc.metadata.get("section")

            print(
                f"source={source_title} | "
                f"page={page_number} | "
                f"score={round(score, 4)}"
            )

            if score > SIMILARITY_THRESHOLD:
                topic_candidates.append(
                    RetrievalCandidateTrace(
                        topic=topic,
                        source_title=source_title,
                        page_number=page_number,
                        section=section,
                        raw_score=float(score),
                        cleaned_snippet="",
                        adjusted_score=None,
                        selected=False,
                        rejection_reason="above_similarity_threshold",
                    )
                )
                continue

            cleaned_snippet = clean_snippet(doc.page_content)
            if not cleaned_snippet:
                topic_candidates.append(
                    RetrievalCandidateTrace(
                        topic=topic,
                        source_title=source_title,
                        page_number=page_number,
                        section=section,
                        raw_score=float(score),
                        cleaned_snippet="",
                        adjusted_score=None,
                        selected=False,
                        rejection_reason="filtered_as_bibliographic_or_empty",
                    )
                )
                continue

            dedupe_key = (topic, source_title, page_number)
            if dedupe_key in seen_keys:
                topic_candidates.append(
                    RetrievalCandidateTrace(
                        topic=topic,
                        source_title=source_title,
                        page_number=page_number,
                        section=section,
                        raw_score=float(score),
                        cleaned_snippet=cleaned_snippet,
                        adjusted_score=None,
                        selected=False,
                        rejection_reason="duplicate_topic_source_page",
                    )
                )
                continue

            seen_keys.add(dedupe_key)

            evidence_item = GuidelineEvidence(
                topic=topic,
                source_title=source_title,
                section=section,
                page_number=page_number,
                snippet=cleaned_snippet,
                score=float(score),
            )
            collected_items.append(evidence_item)

            score_details = compute_selection_details(evidence_item)

            topic_candidates.append(
                RetrievalCandidateTrace(
                    topic=topic,
                    source_title=source_title,
                    page_number=page_number,
                    section=section,
                    raw_score=score_details["raw_score"],
                    cleaned_snippet=cleaned_snippet,
                    keyword_matches=score_details["keyword_matches"],
                    keyword_bonus=score_details["keyword_bonus"],
                    claim_keyword_matches=score_details["claim_keyword_matches"],
                    claim_alignment_bonus=score_details["claim_alignment_bonus"],
                    section_bonus=score_details["section_bonus"],
                    generic_penalty=score_details["generic_penalty"],
                    adjusted_score=score_details["adjusted_score"],
                    selected=False,
                    rejection_reason=None,
                )
            )
                

        topic_traces.append(
            RetrievalTopicTrace(
                topic=topic,
                query=query,
                candidates=topic_candidates,
            )
        )

    print("------------------------\n")

    selected_items = select_best_evidence_per_topic(
        evidence_items=collected_items,
        max_total_items=max_total_items,
    )

    selected_keys = {
        (item.topic, item.source_title, item.page_number)
        for item in selected_items
    }

    for topic_trace in topic_traces:
        for candidate in topic_trace.candidates:
            key = (candidate.topic, candidate.source_title, candidate.page_number)
            if key in selected_keys:
                candidate.selected = True
                candidate.rejection_reason = None
            elif candidate.rejection_reason is None:
                candidate.rejection_reason = "not_selected_after_reranking"

    for item in selected_items:
        details = compute_selection_details(item)
        print(
            f"SELECTED | topic={item.topic} | source={item.source_title} | "
            f"page={item.page_number} | semantic_score={item.score} | "
            f"adjusted_score={round(details['adjusted_score'], 4)}"
        )

    retrieved = RetrievedGuidelineEvidence(
        query_used=" || ".join([f"{q['topic']}: {q['query']}" for q in queries]),
        top_k=len(selected_items),
        evidence_items=selected_items,
    )

    return retrieved, topic_traces