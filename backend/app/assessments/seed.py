from datetime import UTC, datetime

from bson import ObjectId
from pymongo.database import Database

from app.assessments.schemas import AssessmentType, QuestionType

ASSESSMENT_KEY = "initial-competency-v1"
HERO_COMPETENCY_CODES = (
    "STAT_SAMPLING",
    "STAT_SURVEY_DESIGN",
    "STAT_DATA_QUALITY_FRAMEWORKS",
    "TECH_PYTHON",
    "TECH_SQL",
    "TECH_DATA_VISUALIZATION",
    "TECH_GIS",
    "TECH_AI_ML",
)

QUESTION_TEMPLATES = {
    "STAT_SAMPLING": ("Which sampling method gives every population member a known non-zero probability of selection?", ["Convenience sampling", "Probability sampling", "Snowball sampling", "Judgment sampling"], "Probability sampling"),
    "STAT_SURVEY_DESIGN": ("Which activity should precede finalizing a survey questionnaire?", ["Pilot testing", "Publishing results", "Deleting metadata", "Selecting respondents after collection"], "Pilot testing"),
    "STAT_DATA_QUALITY_FRAMEWORKS": ("Which dimension describes whether data values are correct?", ["Accuracy", "Timeliness", "Accessibility", "Uniqueness"], "Accuracy"),
    "TECH_PYTHON": ("Which Python structure stores key-value pairs?", ["List", "Tuple", "Dictionary", "Set"], "Dictionary"),
    "TECH_SQL": ("Which SQL clause filters grouped results?", ["WHERE", "GROUP BY", "HAVING", "ORDER BY"], "HAVING"),
    "TECH_DATA_VISUALIZATION": ("Which chart is generally suitable for showing a trend over time?", ["Line chart", "Pie chart", "Single-value card", "Scatterless table"], "Line chart"),
    "TECH_GIS": ("What does GIS primarily allow users to analyze?", ["Spatial relationships", "Password strength", "Text grammar", "Audio frequencies"], "Spatial relationships"),
    "TECH_AI_ML": ("What is a labelled dataset commonly used for?", ["Supervised learning", "File compression", "Encryption only", "Manual sampling only"], "Supervised learning"),
}


def seed_assessment(database: Database) -> dict[str, int]:
    competency_documents = list(database.competencies.find({"code": {"$in": list(HERO_COMPETENCY_CODES)}}, {"_id": 1, "code": 1}))
    competency_ids = {item["code"]: item["_id"] for item in competency_documents}
    missing = set(HERO_COMPETENCY_CODES) - set(competency_ids)
    if missing:
        raise ValueError(f"missing seeded competencies: {sorted(missing)}")

    now = datetime.now(UTC)
    questions = []
    for code in HERO_COMPETENCY_CODES:
        questions.append({
            "question_id": f"self_{code.lower()}",
            "competency_id": competency_ids[code],
            "question_type": QuestionType.SELF_RATING.value,
            "question_text": f"Rate your current {code} competency from 1 to 5.",
            "options": [],
            "correct_answer": None,
            "difficulty": "FOUNDATION",
            "weight": 1.0,
        })
        question, options, correct = QUESTION_TEMPLATES[code]
        questions.append({
            "question_id": f"knowledge_{code.lower()}",
            "competency_id": competency_ids[code],
            "question_type": QuestionType.MCQ.value,
            "question_text": question,
            "options": options,
            "correct_answer": correct,
            "difficulty": "FOUNDATION",
            "weight": 1.0,
        })
        scenario_question = {
            "STAT_SAMPLING": "A field team needs a representative sample and must quantify selection probability. Which approach is most appropriate?",
            "STAT_SURVEY_DESIGN": "A pilot reveals respondents misunderstand a question. What should the team do before launch?",
            "STAT_DATA_QUALITY_FRAMEWORKS": "A release contains correct values but is published months late. Which quality concern is evident?",
            "TECH_PYTHON": "An analyst needs to process repeated records and preserve named fields. Which Python capability is most useful?",
            "TECH_SQL": "A report must show departments whose average value exceeds a threshold. Which SQL pattern is needed?",
            "TECH_DATA_VISUALIZATION": "A manager wants to compare monthly movement across a year. Which visualization best supports this?",
            "TECH_GIS": "A planner wants to identify facilities within a district boundary. Which capability is needed?",
            "TECH_AI_ML": "A model is trained using examples paired with known outcomes. What learning setting is this?",
        }[code]
        scenario_options = {
            "STAT_SAMPLING": ["Probability sampling", "Convenience sampling", "No sampling", "Only volunteers"],
            "STAT_SURVEY_DESIGN": ["Revise and retest the question", "Ignore the pilot", "Remove all responses", "Publish immediately"],
            "STAT_DATA_QUALITY_FRAMEWORKS": ["Timeliness", "Accuracy", "Validity", "Completeness"],
            "TECH_PYTHON": ["Use dictionaries and iteration", "Delete field names", "Use only comments", "Disable processing"],
            "TECH_SQL": ["GROUP BY with HAVING", "ORDER BY only", "DROP TABLE", "WHERE without grouping"],
            "TECH_DATA_VISUALIZATION": ["Line chart", "Unordered labels", "Password list", "Raw binary"],
            "TECH_GIS": ["Spatial overlay/query", "Text translation", "Password reset", "Audio mixing"],
            "TECH_AI_ML": ["Supervised learning", "Unlabelled compression", "Manual filing", "Random deletion"],
        }[code]
        questions.append({
            "question_id": f"scenario_{code.lower()}",
            "competency_id": competency_ids[code],
            "question_type": QuestionType.SCENARIO.value,
            "question_text": scenario_question,
            "options": scenario_options,
            "correct_answer": scenario_options[0],
            "difficulty": "INTERMEDIATE",
            "weight": 1.0,
        })

    document = {
        "assessment_type": AssessmentType.INITIAL_COMPETENCY.value,
        "assessment_key": ASSESSMENT_KEY,
        "title": "Initial Competency Assessment",
        "description": "ShikshaSetu prototype assessment for the Statistical Officer demonstration.",
        "competencies": [competency_ids[code] for code in HERO_COMPETENCY_CODES],
        "questions": questions,
        "status": "active",
        "version": 1,
        "updated_at": now,
    }
    database.assessments.update_one(
        {"assessment_key": ASSESSMENT_KEY},
        {"$set": document, "$setOnInsert": {"created_at": now}},
        upsert=True,
    )
    return {"assessments": database.assessments.count_documents({"assessment_key": ASSESSMENT_KEY}), "questions": len(questions), "competencies": len(HERO_COMPETENCY_CODES)}


if __name__ == "__main__":
    from app.core.config import get_settings
    from app.core.database import close_database, initialize_database

    client, database = initialize_database(get_settings().mongodb_uri, get_settings().mongodb_database)
    try:
        print(seed_assessment(database))
    finally:
        close_database(client)
