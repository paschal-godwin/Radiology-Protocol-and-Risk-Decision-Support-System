from app.schemas.input import RadiologyCaseInput, PriorContrastReaction


def assess_contrast_reaction_risk(case: RadiologyCaseInput) -> dict:
    if not case.contrast_requested:
        return {
            "flag": None,
            "message": "Contrast reaction risk not applicable because contrast is not requested."
        }

    if case.prior_contrast_reaction == PriorContrastReaction.unknown:
        return {
            "flag": "contrast_reaction_history_unknown",
            "message": "Prior contrast reaction history is unknown and should be clarified before proceeding."
        }

    if case.prior_contrast_reaction == PriorContrastReaction.severe:
        return {
            "flag": "high_contrast_reaction_risk",
            "message": "History of severe prior contrast reaction. Contrast use should be reviewed carefully before proceeding."
        }

    if case.prior_contrast_reaction == PriorContrastReaction.moderate:
        return {
            "flag": "moderate_contrast_reaction_risk",
            "message": "History of moderate prior contrast reaction. Caution and review are recommended."
        }

    if case.prior_contrast_reaction == PriorContrastReaction.mild:
        return {
            "flag": "mild_contrast_reaction_risk",
            "message": "History of mild prior contrast reaction. Proceed only with appropriate caution under current policy."
        }

    return {
        "flag": None,
        "message": "No prior contrast reaction risk detected by current V1 rule."
    }