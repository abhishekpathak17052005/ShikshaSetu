from enum import StrEnum


class Domain(StrEnum):
    STATISTICAL = "STATISTICAL"
    TECHNICAL = "TECHNICAL"
    DIGITAL_GOVERNANCE = "DIGITAL_GOVERNANCE"
    BEHAVIOURAL_MANAGERIAL = "BEHAVIOURAL_MANAGERIAL"


class FrameworkStatus(StrEnum):
    PROTOTYPE = "prototype"
    OFFICIAL = "official"
    DERIVED = "derived"


class SourceType(StrEnum):
    PROTOTYPE = "PROTOTYPE"
    OFFICIAL = "OFFICIAL"
    DERIVED = "DERIVED"


class EvidenceType(StrEnum):
    SELF_ASSESSMENT = "SELF_ASSESSMENT"
    KNOWLEDGE_TEST = "KNOWLEDGE_TEST"
    SCENARIO_TEST = "SCENARIO_TEST"
    TRAINING = "TRAINING"
    QUIZ = "QUIZ"
