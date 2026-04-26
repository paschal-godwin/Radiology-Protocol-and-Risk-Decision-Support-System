from app.schemas.output import GuidelineEvidence, RetrievedGuidelineEvidence


def retrieve_guideline_evidence(query: str, top_k: int = 3) -> RetrievedGuidelineEvidence:
    """
    Temporary mock retriever used to wire the RAG architecture end-to-end.

    Later, this will be replaced by a real vector-store retriever
    backed by guideline PDFs, embeddings, and FAISS.
    """

    mock_items = [
        GuidelineEvidence(
            source_title="ACR Manual on Contrast Media",
            section="Renal Function Assessment",
            page_number=12,
            snippet="Patients with impaired renal function may require additional review before iodinated contrast administration.",
            relevance_reason="Relevant because this case includes renal risk evaluation.",
        ),
        GuidelineEvidence(
            source_title="ACR Manual on Contrast Media",
            section="Contrast Reaction History",
            page_number=25,
            snippet="A prior contrast reaction should be considered when evaluating the safety of future contrast administration.",
            relevance_reason="Relevant because prior contrast reaction history affects risk assessment.",
        ),
        GuidelineEvidence(
            source_title="Institutional CT Contrast Safety Guideline",
            section="Pre-contrast Screening",
            page_number=4,
            snippet="Missing clinical screening information should be clarified before proceeding when contrast safety cannot be fully assessed.",
            relevance_reason="Relevant because missing information influences whether the exam can proceed.",
        ),
    ]

    return RetrievedGuidelineEvidence(
        query_used=query,
        top_k=top_k,
        evidence_items=mock_items[:top_k],
    )