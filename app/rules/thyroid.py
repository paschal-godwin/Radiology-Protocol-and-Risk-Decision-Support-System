from app.schemas.input import RadiologyCaseInput, ThyroidStatus

def assess_thyroid_risk(case: RadiologyCaseInput) -> dict:
      if contrast_not_requested := not case.contrast_requested:
        return {
            "flag": None,
            "message": "No thyroid-related risk because contrast is not requested."
        }
      
      if case.thyroid_status == ThyroidStatus.unknown:
            return {
                "flag": "hyperthyroid_contrast_risk",
                "message": "Thyroid status is unknown. Assess for potential thyroid dysfunction that may impact contrast administration."
            }
      if case.thyroid_status == ThyroidStatus.hyperthyroid:
            return {
                "flag": "hyperthyroid_contrast_risk",
                "message": "Patient has hyperthyroidism which may increase risk of thyroid storm with iodinated contrast. Assess clinical status and consider endocrinology consultation before proceeding."
            }
      if case.thyroid_status == ThyroidStatus.autonomous_nodule:
            return {
                "flag": "autonomous_nodule_contrast_risk",
                "message": "Patient has an autonomous thyroid nodule which may increase risk of thyrotoxicosis with iodinated contrast. Assess clinical status and consider endocrinology consultation before proceeding."
            }
      return {
        "flag": "no_thyroid_risk_detected",
        "message": "No thyroid-related risk detected by current V1 rule."
    }