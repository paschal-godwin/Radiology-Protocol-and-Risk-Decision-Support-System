from pydantic import BaseModel
from typing import Optional
from enum import Enum


class Sex(str, Enum):
    male = "male"
    female = "female"
    other = "other"


class PregnancyStatus(str, Enum):
    pregnant = "pregnant"
    not_pregnant = "not_pregnant"
    unknown = "unknown"
    not_applicable = "not_applicable"


class PriorContrastReaction(str, Enum):
    none = "none"
    mild = "mild"
    moderate = "moderate"
    severe = "severe"
    unknown = "unknown"


class UrgencyLevel(str, Enum):
    routine = "routine"
    urgent = "urgent"
    emergency = "emergency"

class MetforminUse(str, Enum):
    yes = "yes"
    no = "no"
    unknown = "unknown"

class ThyroidStatus(str, Enum):
    normal = "normal"
    hyperthyroid = "hyperthyroid"
    autonomous_nodule = "autonomous_nodule"
    unknown = "unknown"

class RadiologyCaseInput(BaseModel):
    
    # Patient info
    age: int
    sex: Sex
    pregnancy_status: PregnancyStatus

    # Exam request
    exam_requested: str
    contrast_requested: bool
    urgency_level: UrgencyLevel

    # Risk-related info
    egfr: Optional[float] = None
    allergy_history: Optional[bool] = None
    asthma_history: Optional[bool] = None
    prior_contrast_reaction: PriorContrastReaction = PriorContrastReaction.none
    metformin_use: MetforminUse = MetforminUse.unknown
    thyroid_status: ThyroidStatus = ThyroidStatus.unknown