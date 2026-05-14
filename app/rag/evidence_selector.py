from collections import defaultdict
from typing import List

from app.schemas.output import GuidelineEvidence


TOPIC_KEYWORDS = {
    "renal": [
        "renal", "kidney", "egfr", "creatinine", "dialysis",
        "iodinated contrast", "contrast-induced", "renal function"
    ],
    "contrast_reaction": [
        "reaction", "hypersensitivity", "allergy", "premedication",
        "adverse event", "severe reaction", "contrast media reaction"
    ],
    "pregnancy": [
        "pregnancy", "pregnant", "fetus", "fetal", "maternal"
    ],
    "metformin": [
        "metformin", "diabetes", "type 2 diabetes", "renal function", "contrast"
    ]
}

# NEW:
# These are more claim-specific phrases.
# They try to capture whether the chunk supports the actual decision claim,
# not just the general topic.
CLAIM_KEYWORDS = {
    "renal": [
        "egfr",
        "severe renal",
        "renal impairment",
        "kidney function",
        "contrast nephropathy",
        "acute kidney injury",
        "aki",
        "review before proceeding",
        "renal risk",
        "caution",
        "avoid contrast",
        "threshold",
    ],
    "contrast_reaction": [
        "severe reaction",
        "prior reaction",
        "hypersensitivity",
        "premedication",
        "high-risk patient",
        "avoidance",
        "re-administration",
        "contrast medium",
        "review before proceeding",
        "caution",
    ],
    "pregnancy": [
        "pregnant",
        "pregnancy",
        "fetus",
        "fetal",
        "maternal",
        "iodinated contrast",
        "harm to the fetus",
        "safety in pregnancy",
        "before proceeding",
        "review",
    ],
    "metformin": [
        "metformin",
        "diabetes",
        "type 2 diabetes",
        "renal function",
        "contrast",
        "review before proceeding",
        "caution",
        "AKI",
        "acute kidney injury",
        "CKD",
        "hold metformin",
    ]
}

GENERIC_SIGNALS = [
    "history obtained should focus",
    "personnel with sufficient expertise",
    "available to treat reactions",
    "patient selection and preparation strategies",
    "in rare clinical situations",
]


def count_keyword_matches(topic: str, snippet: str) -> int:
    lowered = snippet.lower()
    keywords = TOPIC_KEYWORDS.get(topic, [])
    return sum(1 for kw in keywords if kw in lowered)


def generic_penalty(snippet: str) -> float:
    lowered = snippet.lower()
    matches = sum(1 for signal in GENERIC_SIGNALS if signal in lowered)
    return matches * 0.02


def section_bonus(section: str | None, topic: str) -> float:
    if not section:
        return 0.0

    lowered = section.lower()

    bonus = 0.0
    if topic == "renal" and any(term in lowered for term in ["renal", "kidney", "contrast"]):
        bonus += 0.02
    elif topic == "contrast_reaction" and any(term in lowered for term in ["reaction", "hypersensitivity", "contrast"]):
        bonus += 0.02
    elif topic == "pregnancy" and "pregnan" in lowered:
        bonus += 0.02

    return bonus


# NEW:
def count_claim_keyword_matches(topic: str, snippet: str) -> int:
    lowered = snippet.lower()
    keywords = CLAIM_KEYWORDS.get(topic, [])
    return sum(1 for kw in keywords if kw in lowered)


# NEW:
def claim_alignment_bonus(topic: str, snippet: str) -> float:
    """
    Reward chunks that better support the actual claim for the topic,
    not just the general topic itself.
    """
    matches = count_claim_keyword_matches(topic, snippet)
    return matches * 0.02


def compute_selection_details(item: GuidelineEvidence) -> dict:
    """
    Return the full deterministic scoring breakdown for one evidence item.
    Lower adjusted_score is better.
    """
    base = item.score if item.score is not None else 999.0
    topic = item.topic or "general"

    kw_matches = count_keyword_matches(topic, item.snippet)
    kw_bonus = kw_matches * 0.015

    claim_kw_matches = count_claim_keyword_matches(topic, item.snippet)
    claim_bonus = claim_alignment_bonus(topic, item.snippet)

    sec_bonus = section_bonus(item.section, topic)
    penalty = generic_penalty(item.snippet)

    adjusted = base - kw_bonus - claim_bonus - sec_bonus + penalty

    return {
        "raw_score": base,
        "keyword_matches": kw_matches,
        "keyword_bonus": kw_bonus,
        "claim_keyword_matches": claim_kw_matches,   # NEW
        "claim_alignment_bonus": claim_bonus,        # NEW
        "section_bonus": sec_bonus,
        "generic_penalty": penalty,
        "adjusted_score": adjusted,
    }


def compute_selection_score(item: GuidelineEvidence) -> float:
    return compute_selection_details(item)["adjusted_score"]


def select_best_evidence_per_topic(
    evidence_items: List[GuidelineEvidence],
    max_total_items: int = 2,
) -> List[GuidelineEvidence]:
    """
    Select the strongest evidence item per topic first,
    then fill remaining slots with the best leftover evidence.
    """
    grouped = defaultdict(list)

    for item in evidence_items:
        grouped[item.topic or "general"].append(item)

    for _, items in grouped.items():
        items.sort(key=compute_selection_score)

    selected: List[GuidelineEvidence] = []

    # First pass: best item per topic
    for topic in grouped:
        if grouped[topic]:
            selected.append(grouped[topic][0])

    # Second pass: best leftovers up to max_total_items
    leftovers: List[GuidelineEvidence] = []
    for topic in grouped:
        leftovers.extend(grouped[topic][1:])

    leftovers.sort(key=compute_selection_score)

    for item in leftovers:
        if len(selected) >= max_total_items:
            break
        selected.append(item)

    selected.sort(key=compute_selection_score)
    return selected[:max_total_items]