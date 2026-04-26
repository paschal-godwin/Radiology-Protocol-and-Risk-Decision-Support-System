from app.schemas.input import RadiologyCaseInput, PregnancyStatus, Sex


def assess_pregnancy_risk(case: RadiologyCaseInput) -> dict:
    if case.sex != Sex.female:
        return {
            "flag": None,
            "message": "Pregnancy risk not applicable."
        }
    
    # Handle incorrect "not_applicable" for female
    if case.sex == Sex.female and case.pregnancy_status == PregnancyStatus.not_applicable:
        return {
            "flag": "pregnancy_status_unknown",
            "message": "Pregnancy status incorrectly marked as not applicable for a female patient. Treating as unknown."
        }

    if case.pregnancy_status == PregnancyStatus.not_applicable:
        return {
            "flag": None,
            "message": "Pregnancy risk not applicable."
        }

    if case.pregnancy_status == PregnancyStatus.unknown:
        return {
            "flag": "pregnancy_status_unknown",
            "message": "Pregnancy status is unknown and should be confirmed before proceeding."
        }

    if case.pregnancy_status == PregnancyStatus.pregnant:
        return {
            "flag": "pregnancy_risk_review_required",
            "message": "Patient is pregnant. Requested CT exam should be reviewed before proceeding."
        }

    return {
        "flag": "no_pregnancy_risk_detected",
        "message": "No pregnancy-related risk detected by current V1 rule."
    }