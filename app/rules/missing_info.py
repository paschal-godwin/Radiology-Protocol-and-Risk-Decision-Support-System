from app.schemas.input import (
    RadiologyCaseInput,
    PregnancyStatus,
    Sex,
    PriorContrastReaction,
)


def detect_missing_information(case: RadiologyCaseInput) -> list[str]:
    missing_items = []

    if case.contrast_requested and case.egfr is None:
        missing_items.append("eGFR is missing for a contrast-requested CT exam")

    if case.sex == Sex.female and case.pregnancy_status == PregnancyStatus.unknown:
        missing_items.append("Pregnancy status is unknown")

    if case.allergy_history is None:
        missing_items.append("Allergy history is missing")

    if case.prior_contrast_reaction == PriorContrastReaction.unknown:
        missing_items.append("Prior contrast reaction history is unknown")

    return missing_items