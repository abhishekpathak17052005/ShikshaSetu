"""
Seed comprehensive question bank for BEH_ETHICS and additional competencies.

Competencies covered:
  BEH_ETHICS                  — 20 questions (EASY/MEDIUM/HARD, MCQ + SCENARIO)
  BEH_DECISION_MAKING         — 12 questions
  STAT_PRICE_STATISTICS       — 12 questions
  STAT_LABOUR_STATISTICS      — 10 questions
  STAT_NATIONAL_ACCOUNTS      — 10 questions
  TECH_SQL                    — additional 5 harder questions (top-up)
  TECH_PYTHON                 — additional 5 harder questions (top-up)

All questions are grounded in:
  - MoSPI official statistical framework
  - DoPT conduct rules
  - Government of India ethics guidelines
  - Mission Karmayogi / CBC competency framework
  - iGOT Karmayogi curriculum
"""
from datetime import UTC, datetime
from pymongo.database import Database
from app.questions.repository import insert_many_questions


def _q(
    question_id: str,
    competency_code: str,
    question_type: str,
    difficulty: str,
    question_text: str,
    options: list[str],
    correct_answer: str,
    explanation: str = "",
    scenario_context: str | None = None,
    weight: float = 1.0,
    source: str = "DoPT_Ethics_Framework",
    evidence_confidence: float = 0.90,
) -> dict:
    """Create a question document matching the existing schema."""
    now = datetime.now(UTC)
    return {
        "question_id": question_id,
        "competency_code": competency_code,
        "question_type": question_type,
        "question_text": question_text,
        "options": options,
        "correct_answer": correct_answer,
        "difficulty": difficulty,
        "explanation": explanation,
        "scenario_context": scenario_context,
        "weight": weight,
        "source": source,
        "evidence_confidence": evidence_confidence,
        "source_type": "GOVERNMENT_DOCUMENT",
        "source_reference": source,
        "status": "ACTIVE",
        "created_at": now,
        "updated_at": now,
    }


def seed_ethics_and_more(database: Database) -> dict[str, int]:
    """
    Idempotent seed — skips questions whose question_id already exists.
    Returns counts of inserted questions per competency.
    """
    all_questions = _build_all_questions()

    # Idempotency: filter out already-existing question_ids
    existing_ids = set(
        doc["question_id"]
        for doc in database.question_bank.find(
            {"question_id": {"$in": [q["question_id"] for q in all_questions]}},
            {"question_id": 1, "_id": 0},
        )
    )
    new_questions = [q for q in all_questions if q["question_id"] not in existing_ids]

    if not new_questions:
        counts: dict[str, int] = {}
        for q in all_questions:
            c = q["competency_code"]
            counts[c] = counts.get(c, 0) + 1
        return {"skipped_already_present": len(all_questions), "by_competency": counts}

    inserted_ids = insert_many_questions(database, new_questions)

    counts = {}
    for q in new_questions:
        c = q["competency_code"]
        counts[c] = counts.get(c, 0) + 1

    return {
        "total_inserted": len(inserted_ids),
        "total_skipped": len(existing_ids),
        "by_competency": counts,
    }


# ===========================================================================
# MASTER QUESTION LIST
# ===========================================================================

def _build_all_questions() -> list[dict]:
    questions: list[dict] = []
    questions.extend(_ethics_questions())
    questions.extend(_decision_making_questions())
    questions.extend(_price_statistics_questions())
    questions.extend(_labour_statistics_questions())
    questions.extend(_national_accounts_questions())
    questions.extend(_sql_advanced_questions())
    questions.extend(_python_data_analytics_questions())
    return questions


# ===========================================================================
# BEH_ETHICS — 20 questions
# Source: DoPT Conduct Rules, Central Vigilance Commission, CBC Mission Karmayogi
# ===========================================================================

def _ethics_questions() -> list[dict]:
    src = "DoPT_Conduct_Rules_CVC_CBC"
    return [
        # ── EASY (Foundation L1-L2) ────────────────────────────────────────
        _q("ETH001", "BEH_ETHICS", "MCQ", "EASY",
           "Which value is MOST fundamental to a public servant's conduct?",
           ["Efficiency", "Integrity", "Speed", "Seniority"],
           "B",
           "Integrity — being honest and having strong moral principles — is the foundation of ethical public service as defined in the DoPT Conduct Rules and Mission Karmayogi framework.",
           source=src, evidence_confidence=0.95),

        _q("ETH002", "BEH_ETHICS", "MCQ", "EASY",
           "A government officer receives a gift worth ₹500 from a contractor whose tender is under evaluation. What should the officer do?",
           ["Accept it — it is below the reporting threshold",
            "Accept it but declare it to the department",
            "Decline politely and report the attempt to the competent authority",
            "Accept it after the tender decision is announced"],
           "C",
           "Accepting gifts from parties having official dealings is prohibited under CCS Conduct Rules 1964, Rule 13. The officer must decline and report the attempt.",
           source=src, evidence_confidence=0.95),

        _q("ETH003", "BEH_ETHICS", "MCQ", "EASY",
           "What is 'conflict of interest' in the context of public service?",
           ["Disagreement between two colleagues",
            "A situation where personal interest could improperly influence official duty",
            "Conflict between two government departments",
            "Policy disagreement with superiors"],
           "B",
           "A conflict of interest arises when personal, financial, or other interests could interfere with the unbiased exercise of official functions, per CBC competency framework.",
           source=src, evidence_confidence=0.93),

        _q("ETH004", "BEH_ETHICS", "MCQ", "EASY",
           "What does 'probity in public life' mean?",
           ["Speed in completing tasks",
            "Complete and confirmed integrity in official actions",
            "Following supervisor instructions only",
            "Achieving high performance scores"],
           "B",
           "Probity means complete and confirmed integrity — being honest and free from corruption in all official actions. It is a core Mission Karmayogi competency.",
           source=src, evidence_confidence=0.95),

        _q("ETH005", "BEH_ETHICS", "MCQ", "EASY",
           "Under Rule 4 of CCS Conduct Rules, a government servant must maintain absolute integrity. This means:",
           ["Completing all tasks on time",
            "Being honest and avoiding corrupt practices in all official and personal dealings",
            "Reporting only financial misconduct",
            "Following instructions from supervisors without question"],
           "B",
           "Rule 4 of CCS Conduct Rules 1964 requires absolute integrity — honesty and freedom from corrupt practice in all dealings, official or personal.",
           source=src, evidence_confidence=0.97),

        # ── MEDIUM (Intermediate L2-L3) ────────────────────────────────────
        _q("ETH006", "BEH_ETHICS", "SCENARIO", "MEDIUM",
           "What is the most appropriate response to this situation?",
           ["Alter the data as instructed — the supervisor bears responsibility",
            "Request the supervisor to put the instruction in writing before proceeding",
            "Refuse the instruction and escalate to the next higher authority or CVC if needed",
            "Comply this time and flag in the annual report"],
           "C",
           "Falsifying official statistics violates the Official Statistics Act, the National Statistical Commission guidelines, and fundamental public service ethics. The officer must refuse and escalate — responsibility cannot be delegated downward for illegal acts.",
           scenario_context="A senior officer instructs a statistical officer to alter district-level literacy data before it is sent to MoSPI headquarters, claiming the data 'does not reflect ground reality' and will 'embarrass the Ministry'.",
           source=src, weight=1.5, evidence_confidence=0.96),

        _q("ETH007", "BEH_ETHICS", "SCENARIO", "MEDIUM",
           "The officer should:",
           ["Provide the draft data under a signed confidentiality agreement",
            "Consult the competent authority and if not authorized, decline to share pre-publication data",
            "Share the data as it is in the public interest",
            "Ask the journalist for the story angle before deciding"],
           "B",
           "Pre-publication statistical data is protected. Unauthorized disclosure of official data violates CCS Conduct Rules 7 and the Official Secrets Act. The officer must consult authority before sharing.",
           scenario_context="A journalist contacts a MoSPI officer directly, requesting access to draft CPI data before official publication, arguing it is in the public interest.",
           source=src, weight=1.5, evidence_confidence=0.95),

        _q("ETH008", "BEH_ETHICS", "MCQ", "MEDIUM",
           "Which of the following best describes 'whistleblowing' in the public sector?",
           ["Leaking classified documents to the media",
            "Reporting suspected wrongdoing to a competent authority through appropriate channels",
            "Complaining about a colleague to a senior",
            "Filing a public interest litigation"],
           "B",
           "Whistleblowing is the act of reporting suspected illegal activity, corruption, or misconduct to the appropriate authority (CVC, CBI, departmental vigilance, or the PMSF). The Whistle Blowers Protection Act 2014 provides safeguards.",
           source=src, evidence_confidence=0.94),

        _q("ETH009", "BEH_ETHICS", "MCQ", "MEDIUM",
           "What is 'misuse of official position' according to Prevention of Corruption Act 1988?",
           ["Using official authority to create extra work for colleagues",
            "Using official position to obtain undue advantage for oneself or someone else",
            "Making decisions that later prove to be wrong",
            "Delegating work to subordinates"],
           "B",
           "Under Prevention of Corruption Act 1988, using official position or authority to obtain pecuniary advantage for self or others constitutes corruption and is a criminal offence.",
           source=src, evidence_confidence=0.97),

        _q("ETH010", "BEH_ETHICS", "SCENARIO", "MEDIUM",
           "The officer's most ethical course of action is:",
           ["Approve the file — the decision is already made above",
            "Approve with a note expressing reservations",
            "Refuse to sign and formally record the basis for refusal on the file",
            "Transfer the file to a colleague"],
           "C",
           "Government officers are personally accountable for files they approve. An officer must not approve a decision they believe to be illegal or unethical and should formally record the basis for refusal. Blind deference to authority does not absolve personal responsibility.",
           scenario_context="An officer is asked to sign a file approving procurement that bypasses tender norms. The superior claims verbal approval from the ministry but no written authorization is on the file.",
           source=src, weight=1.5, evidence_confidence=0.96),

        _q("ETH011", "BEH_ETHICS", "MCQ", "MEDIUM",
           "Under the RTI Act 2005, what is the default presumption about government information?",
           ["All information is confidential unless declared public",
            "Information should be proactively disclosed; secrecy is the exception",
            "Information can only be disclosed on court order",
            "Information belongs to the government, not citizens"],
           "B",
           "The RTI Act 2005 establishes transparency as the default. Information must be provided unless covered by specific exemptions under Sections 8 and 9. The spirit of the Act is maximum disclosure.",
           source=src, evidence_confidence=0.95),

        _q("ETH012", "BEH_ETHICS", "SCENARIO", "MEDIUM",
           "An ethical officer should:",
           ["Promote based on friendship — morale matters more than process",
            "Recommend the most capable candidate based on objective criteria, regardless of personal relationship",
            "Avoid making the recommendation by citing a conflict of interest",
            "Ask the manager to decide without input from you"],
           "B",
           "Personal relationships must not influence official decisions. The officer should recommend objectively OR formally declare a conflict of interest and recuse. Option B (objective recommendation) and option C (recusal) are both defensible; the key is not allowing the friendship to bias the outcome. Option B is preferred if objectivity can be maintained.",
           scenario_context="An officer sits on a promotion committee. One of the candidates is a close friend. The officer's assessment will carry significant weight in the final decision.",
           source=src, weight=1.5, evidence_confidence=0.94),

        # ── HARD (Advanced L4-L5) ──────────────────────────────────────────
        _q("ETH013", "BEH_ETHICS", "SCENARIO", "HARD",
           "What is the most appropriate course of action?",
           ["Adjust the methodology as requested — policy considerations are legitimate",
            "Consult with NSC and document the methodology change with full justification in the report",
            "Refuse any change and publish the original methodology without notifying the ministry",
            "Change the methodology but omit any reference to the change in published documentation"],
           "B",
           "Statistical methodology changes must be transparent, justified, and documented. While statistical bodies should be independent from political influence, consultation with NSC and full documentation in the report is the professional path. Undisclosed methodology changes violate international statistical standards (UN Fundamental Principles of Official Statistics).",
           scenario_context="A ministry official requests that a MoSPI team modify the price-index calculation methodology before publication because the result under the current method shows higher inflation than the government's target. The official argues this is a legitimate 'policy-aligned' adjustment.",
           source=src, weight=2.0, evidence_confidence=0.97),

        _q("ETH014", "BEH_ETHICS", "SCENARIO", "HARD",
           "The correct action is:",
           ["Report to the CBI anonymously",
            "Report to the departmental vigilance officer and/or CVC with documented evidence",
            "Ignore it — this is above your responsibility level",
            "Confront the senior officer directly before taking any other step"],
           "B",
           "The CVC Act 2003 and Whistle Blowers Protection Act 2014 provide the correct mechanism: report to departmental vigilance or directly to CVC with documented evidence. Anonymous CBI complaints may be investigated but proper channels are preferred. Direct confrontation is dangerous and not the established procedure.",
           scenario_context="A junior officer discovers that a senior colleague is systematically directing government contracts to a vendor in which the colleague has a family stake. The junior has documented evidence including emails and file notings.",
           source=src, weight=2.0, evidence_confidence=0.96),

        _q("ETH015", "BEH_ETHICS", "MCQ", "HARD",
           "What is the 'duty of care' obligation of a public servant regarding government data integrity?",
           ["Ensuring data is stored in an approved format only",
            "Taking all reasonable precautions to ensure data accuracy, prevent falsification, and maintain audit trails",
            "Delegating data quality to the IT department",
            "Reporting data quality issues only in the annual review"],
           "B",
           "Public servants have a duty of care to ensure data integrity — including accuracy, completeness, and tamper-resistance. This flows from Rule 3 of CCS Conduct Rules (maintaining absolute devotion to duty) and international standards (GSBPM, DQAF).",
           source=src, weight=2.0, evidence_confidence=0.95),

        _q("ETH016", "BEH_ETHICS", "SCENARIO", "HARD",
           "The statistically and ethically sound approach is:",
           ["Aggregate all sources into a single figure — consistency is more important",
            "Publish both series with clear methodological notes and initiate a reconciliation process",
            "Suppress the conflicting series to avoid public confusion",
            "Wait for political guidance before publishing either series"],
           "B",
           "Transparency is the foundation of official statistics. When legitimate methodological differences produce different results, both series should be published with clear notes. Suppression or political deferment violates UN Fundamental Principles of Official Statistics, especially Principle 1 (independence) and Principle 3 (accountability).",
           scenario_context="Two MoSPI divisions produce different estimates of national unemployment using legitimate but different methodologies. A minister's office requests that only the more favourable figure be published.",
           source=src, weight=2.0, evidence_confidence=0.97),

        _q("ETH017", "BEH_ETHICS", "MCQ", "HARD",
           "Under the concept of 'ethical pluralism', public servants must navigate situations where:",
           ["Rules always provide complete guidance",
            "Different ethical principles conflict and judgment is required to prioritize them",
            "Personal ethics override organizational rules",
            "Public interest is the only consideration"],
           "B",
           "Ethical pluralism recognizes that different ethical frameworks (duty-based, consequence-based, virtue ethics) may point in different directions. A mature public servant exercises practical wisdom (phronesis) to navigate such conflicts within the bounds of law.",
           source="CBC_Mission_Karmayogi", weight=2.0, evidence_confidence=0.92),

        _q("ETH018", "BEH_ETHICS", "SCENARIO", "HARD",
           "The legally and ethically correct course is:",
           ["Disclose the information — the public's right to know outweighs other concerns",
            "Decline to share, citing official confidentiality; suggest the requester use RTI",
            "Share a summary only, omitting sensitive elements",
            "Ask the requester to submit a formal request through proper channels before deciding"],
           "B",
           "Pre-publication official data has statutory confidentiality protection. The correct response is to decline and redirect to official channels (RTI). Even if the cause appears legitimate, the officer does not have unilateral authority to release protected information.",
           scenario_context="An officer is approached by an academic researcher who claims urgent need for unpublished census microdata to complete research that could benefit public health policy. The researcher presents institutional credentials.",
           source=src, weight=2.0, evidence_confidence=0.96),

        _q("ETH019", "BEH_ETHICS", "MCQ", "HARD",
           "What distinguishes 'ethical conduct' from merely 'legal conduct' in public service?",
           ["There is no difference — all legal acts are ethical",
            "Ethical conduct may require doing more than the law demands and refusing acts that are legal but wrong",
            "Legal conduct is always superior to ethical principles",
            "Ethics only applies to financial matters"],
           "B",
           "Law sets the minimum. Ethical public service demands higher standards: avoiding actions that are technically legal but violate public trust, fairness, or the spirit of service. The CBC Mission Karmayogi framework emphasizes values-driven public service beyond mere rule compliance.",
           source="CBC_Mission_Karmayogi", weight=2.0, evidence_confidence=0.93),

        _q("ETH020", "BEH_ETHICS", "SCENARIO", "HARD",
           "The most appropriate action combining legality, ethics, and professional duty is:",
           ["Apply the penalty mechanically as stated in the rules",
            "Assess proportionality; apply the rule with reasoned discretion documented on file",
            "Use maximum penalty to deter future violations",
            "Defer the decision to avoid controversy"],
           "B",
           "Good governance requires proportionate application of rules. A public servant has discretion to apply sanctions proportionately while remaining within the legal framework, with reasons documented. Mechanical rule application without proportionality can violate natural justice principles upheld by Indian courts.",
           scenario_context="An officer must apply a penalty provision under departmental rules. The rules specify a mandatory penalty, but the circumstances of the case suggest the outcome may be disproportionate to the actual harm caused. No appeal mechanism exists within the officer's jurisdiction.",
           source=src, weight=2.0, evidence_confidence=0.95),
    ]


# ===========================================================================
# BEH_DECISION_MAKING — 12 questions
# ===========================================================================

def _decision_making_questions() -> list[dict]:
    src = "CBC_Decision_Making_Framework"
    return [
        _q("DM001", "BEH_DECISION_MAKING", "MCQ", "EASY",
           "Which of the following best defines evidence-based decision making?",
           ["Making decisions quickly based on experience",
            "Using the best available data, research and evidence to guide choices",
            "Following established precedent without analysis",
            "Delegating decisions to subject matter experts"],
           "B",
           "Evidence-based decision making integrates best available evidence with professional judgment and contextual knowledge to make informed choices.",
           source=src),

        _q("DM002", "BEH_DECISION_MAKING", "MCQ", "EASY",
           "What is 'cognitive bias' in the context of decision making?",
           ["A technical error in calculations",
            "A systematic pattern of deviation from rationality in judgment",
            "A bias towards technical solutions",
            "Overconfidence in data"],
           "B",
           "Cognitive biases are systematic errors in thinking that affect judgments and decisions. Examples include confirmation bias, anchoring, and availability heuristic.",
           source=src),

        _q("DM003", "BEH_DECISION_MAKING", "MCQ", "MEDIUM",
           "In a complex policy decision with incomplete information, what is the recommended approach?",
           ["Wait until complete information is available",
            "Decide based on intuition alone",
            "Structure the problem, identify key uncertainties, and use scenario analysis",
            "Escalate all complex decisions to senior management"],
           "C",
           "Structured decision making under uncertainty uses scenario analysis, sensitivity testing, and decision trees to identify robust options across plausible futures.",
           source=src),

        _q("DM004", "BEH_DECISION_MAKING", "MCQ", "MEDIUM",
           "What is 'escalation of commitment' (sunk cost fallacy) in decision making?",
           ["Increasing resources when a project is succeeding",
            "Continuing to invest in a failing course of action due to prior investments",
            "Escalating decisions to higher authority",
            "Adding more stakeholders to a decision"],
           "B",
           "Escalation of commitment occurs when past investment ('sunk costs') irrationally drives continued investment in a failing course. Decisions should be based on future costs and benefits, not past expenditure.",
           source=src),

        _q("DM005", "BEH_DECISION_MAKING", "SCENARIO", "MEDIUM",
           "The most appropriate decision-making approach is:",
           ["Proceed with Option A — it has already been approved in principle",
            "Defer indefinitely pending complete data",
            "Apply precautionary principle: implement Option B with reversibility built in",
            "Choose the option that minimizes short-term cost regardless of risk"],
           "C",
           "When facing irreversible decisions under uncertainty with significant downside risk, the precautionary principle recommends choosing the option that preserves future flexibility and avoids hard-to-reverse consequences.",
           scenario_context="A policy officer must recommend between two programme options. Option A promises higher immediate benefits but has irreversible negative consequences if certain assumptions prove wrong. Option B has lower benefits but is reversible. Data to distinguish the scenarios won't be available for 18 months.",
           source=src, weight=1.5),

        _q("DM006", "BEH_DECISION_MAKING", "MCQ", "MEDIUM",
           "What does RAPID decision framework stand for?",
           ["Research, Analyse, Plan, Implement, Document",
            "Recommend, Agree, Perform, Input, Decide",
            "Record, Assess, Prioritise, Implement, Deliver",
            "Review, Approve, Process, Issue, Deploy"],
           "B",
           "RAPID clarifies decision roles: Recommend (initiate), Agree (must concur), Perform (implement), Input (provide data), Decide (single point of accountability).",
           source=src),

        _q("DM007", "BEH_DECISION_MAKING", "MCQ", "HARD",
           "What is 'decision fatigue' and how does it affect governance?",
           ["Unwillingness to make decisions",
            "Deteriorating quality of decisions after a long session of decision making",
            "Fatigue caused by poor data quality",
            "Resistance to automated decision systems"],
           "B",
           "Decision fatigue describes the declining quality of choices made by a person after a long period of deciding. It leads to defaults and impulsive choices. High-stakes decisions should be scheduled when cognitive resources are fresh.",
           source=src, weight=1.5),

        _q("DM008", "BEH_DECISION_MAKING", "SCENARIO", "HARD",
           "The recommended approach is:",
           ["Accept the consensus immediately to maintain team harmony",
            "Introduce a structured devil's advocate exercise or formally solicit dissenting analysis",
            "Expand the group further to include more stakeholders",
            "Delegate the final decision to an external expert"],
           "B",
           "Groupthink is a significant risk in expert committees. Structured techniques — devil's advocate, red team/blue team, or Delphi method — surface suppressed dissent and improve decision quality without destroying cohesion.",
           scenario_context="A technical committee is reaching consensus on a statistical methodology recommendation. The committee chair notices that junior members are not voicing their doubts, and the discussion has converged very quickly despite significant methodological complexity.",
           source=src, weight=2.0),

        _q("DM009", "BEH_DECISION_MAKING", "MCQ", "HARD",
           "When making decisions that affect vulnerable populations, which ethical framework should be prioritized?",
           ["Utilitarian: maximize aggregate benefit",
            "Rights-based: ensure non-negotiable rights are not violated even for aggregate gain",
            "Procedural: follow process regardless of outcome",
            "Virtue: do what a good person would do"],
           "B",
           "Rights-based frameworks hold that certain rights — of vulnerable groups, minorities — cannot be traded off for aggregate gain. This is foundational to constitutional governance in India and international human rights law.",
           source="CBC_Mission_Karmayogi", weight=2.0),

        _q("DM010", "BEH_DECISION_MAKING", "MCQ", "HARD",
           "What is 'bounded rationality' in organizational decision making?",
           ["A decision made within budget boundaries",
            "The concept that human decision makers operate with limited information, time, and cognitive capacity",
            "A legally bounded decision with no discretion",
            "A decision limited to one department"],
           "B",
           "Herbert Simon's bounded rationality recognizes that decision makers 'satisfice' (find good-enough solutions) rather than optimize, due to information and cognitive limits. Understanding this improves institutional design.",
           source=src, weight=2.0),

        _q("DM011", "BEH_DECISION_MAKING", "SCENARIO", "HARD",
           "Best practice for this decision is:",
           ["Choose the option with the highest expected value",
            "Use a multi-criteria analysis weighing cost, equity, sustainability, and risk",
            "Select the cheapest option and use savings for other programmes",
            "Delay until more data is available"],
           "B",
           "Infrastructure investment decisions involve multiple competing values (efficiency, equity, sustainability). Multi-criteria analysis (MCDA) explicitly weights these factors and produces a transparent, auditable rationale superior to pure cost-benefit analysis.",
           scenario_context="A state-level officer must recommend between two water infrastructure investment options. One option maximizes coverage at lower cost but disadvantages remote tribal communities. The other ensures equitable coverage but costs 30% more.",
           source=src, weight=2.0),

        _q("DM012", "BEH_DECISION_MAKING", "MCQ", "MEDIUM",
           "What is 'pre-mortem' analysis in decision making?",
           ["Reviewing a decision after it has failed",
            "Imagining a decision has already failed and working backwards to identify why",
            "Obtaining death certificate before proceeding",
            "Post-implementation review process"],
           "B",
           "Pre-mortem analysis (Gary Klein) asks teams to assume the decision has already failed, then identify reasons. This surfaces risks and blind spots before implementation, improving decision quality.",
           source=src, weight=1.5),
    ]


# ===========================================================================
# STAT_PRICE_STATISTICS — 12 questions
# Source: MoSPI CPI/WPI framework
# ===========================================================================

def _price_statistics_questions() -> list[dict]:
    src = "MoSPI_CPI_WPI_Technical_Manual"
    return [
        _q("PRICE001", "STAT_PRICE_STATISTICS", "MCQ", "EASY",
           "What does CPI stand for in Indian official statistics?",
           ["Central Price Index", "Consumer Price Index", "Composite Price Indicator", "Current Price Index"],
           "B",
           "CPI — Consumer Price Index — measures the weighted average of prices of a basket of consumer goods and services purchased by households. India's CPI is compiled by MoSPI.",
           source=src, evidence_confidence=0.97),

        _q("PRICE002", "STAT_PRICE_STATISTICS", "MCQ", "EASY",
           "What does WPI measure?",
           ["Wholesale prices of goods at the producer level",
            "Retail prices paid by consumers",
            "Export prices of goods",
            "Import prices of goods"],
           "A",
           "WPI (Wholesale Price Index) measures price changes at the wholesale/producer level for goods. It is compiled by DPIIT (Ministry of Commerce), distinct from MoSPI's CPI.",
           source=src, evidence_confidence=0.97),

        _q("PRICE003", "STAT_PRICE_STATISTICS", "MCQ", "MEDIUM",
           "In India's CPI basket, the largest weight is assigned to which category?",
           ["Housing", "Fuel and Light", "Food and Beverages", "Clothing and Footwear"],
           "C",
           "Food and Beverages carry the highest weight in India's CPI basket (approximately 45.86%), reflecting the importance of food expenditure in household budgets, especially in rural India.",
           source=src, evidence_confidence=0.97),

        _q("PRICE004", "STAT_PRICE_STATISTICS", "MCQ", "MEDIUM",
           "What is 'core inflation' as used in monetary policy analysis?",
           ["Inflation in the core sector (steel, cement, etc.)",
            "Overall CPI inflation",
            "CPI inflation excluding food and fuel prices",
            "WPI inflation excluding manufactured goods"],
           "C",
           "Core inflation excludes volatile food and energy prices to reveal underlying demand-driven inflation trends. RBI monitors core inflation alongside headline CPI for monetary policy decisions.",
           source=src, evidence_confidence=0.96),

        _q("PRICE005", "STAT_PRICE_STATISTICS", "MCQ", "MEDIUM",
           "What is the Laspeyres price index formula used for?",
           ["Measuring export price changes",
            "Measuring price changes using a fixed base-period quantity basket",
            "Measuring current-period price and quantity changes",
            "Measuring geometric average of price relatives"],
           "B",
           "Laspeyres index = (Current prices × Base quantities) / (Base prices × Base quantities) × 100. India's CPI uses a modified Laspeyres formula with base year quantities as weights.",
           source=src, evidence_confidence=0.96),

        _q("PRICE006", "STAT_PRICE_STATISTICS", "MCQ", "HARD",
           "What is 'substitution bias' in a fixed-weight price index?",
           ["Bias from substituting one data source for another",
            "The tendency of a Laspeyres index to overstate inflation because it ignores consumer substitution toward cheaper goods",
            "Bias from seasonal substitution in food prices",
            "Replacing high-priced goods with low-priced imports"],
           "B",
           "When prices rise, consumers substitute to relatively cheaper goods. A Laspeyres (fixed-weight) index does not capture this substitution, overstating the cost of living increase. This is why chained indices or Fisher ideal indices are preferred in advanced systems.",
           source=src, weight=1.5, evidence_confidence=0.96),

        _q("PRICE007", "STAT_PRICE_STATISTICS", "SCENARIO", "HARD",
           "The analyst's next step should be to:",
           ["Publish the unadjusted data — any adjustment may be seen as manipulation",
            "Apply standard seasonal adjustment (e.g. X-12-ARIMA) and publish both adjusted and unadjusted series with methodology notes",
            "Delay publication until the seasonal effect naturally disappears",
            "Apply an ad hoc adjustment based on last year's seasonal factor"],
           "B",
           "Best practice requires transparent seasonal adjustment using standard methods (X-12-ARIMA, X-13ARIMA-SEATS, STL). Both original and adjusted series should be published with methodology documentation, per IMF Data Quality Assessment Framework.",
           scenario_context="A price statistics analyst finds that vegetable prices in the CPI series show a large seasonal spike every monsoon quarter, distorting year-on-year comparisons and causing misleading headlines.",
           source=src, weight=2.0, evidence_confidence=0.95),

        _q("PRICE008", "STAT_PRICE_STATISTICS", "MCQ", "HARD",
           "What does 'rebasing' a price index involve?",
           ["Recalculating index with updated base-period weights and/or base year",
            "Removing outliers from the price series",
            "Switching from WPI to CPI",
            "Changing the price collection methodology"],
           "A",
           "Rebasing updates the reference period (base year) and/or the expenditure weights used in the index, ensuring the basket reflects current consumption patterns. India rebased its CPI in 2012 (base year 2012=100).",
           source=src, weight=1.5, evidence_confidence=0.96),

        _q("PRICE009", "STAT_PRICE_STATISTICS", "MCQ", "MEDIUM",
           "What is the 'geometric mean' approach used for in some CPI components?",
           ["Calculating average household income",
            "Computing price relatives within elementary aggregates to reduce upper-level substitution bias",
            "Measuring geometric population growth",
            "Calculating compound annual growth rate"],
           "B",
           "The geometric mean of price relatives within elementary aggregates (Jevons index) implicitly allows for substitution at the lowest level and has better axiomatic properties than arithmetic mean, reducing bias.",
           source=src, weight=1.5, evidence_confidence=0.94),

        _q("PRICE010", "STAT_PRICE_STATISTICS", "MCQ", "HARD",
           "What is 'hedonic price adjustment' and why is it used in price statistics?",
           ["Adjustment for seasonal hedonic patterns",
            "Adjusting prices for quality changes in products so that only pure price change is measured",
            "Using happiness/welfare measures in price calculation",
            "A hedging approach to price risk measurement"],
           "B",
           "Hedonic methods separate price changes due to quality improvement from pure price inflation. Important for rapidly evolving goods (electronics, vehicles). Without it, quality improvements are mis-measured as price changes.",
           source=src, weight=2.0, evidence_confidence=0.95),

        _q("PRICE011", "STAT_PRICE_STATISTICS", "SCENARIO", "MEDIUM",
           "The recommended action is:",
           ["Use the IIP data — it is more comprehensive",
            "Use the WPI data — it covers production directly",
            "Consult the conceptual framework: if measuring producer prices, use PPI/WPI; if measuring living costs, use CPI",
            "Use an average of CPI and WPI"],
           "C",
           "CPI and WPI/PPI measure different economic phenomena. The choice depends on the analytical question. For monetary policy and living cost analysis, CPI is appropriate. For producer/manufacturing cost analysis, WPI/PPI is appropriate. They should not be averaged.",
           scenario_context="A policy analyst needs to measure the 'true' inflation facing industrial workers. She is unsure whether to use CPI (Urban) or WPI for her analysis.",
           source=src, weight=1.5, evidence_confidence=0.95),

        _q("PRICE012", "STAT_PRICE_STATISTICS", "MCQ", "MEDIUM",
           "What is the base year effect in India's CPI calculation?",
           ["Effect of economic events in the base year distorting year-on-year comparison",
            "The weight given to the base year in index construction",
            "The effect of government subsidies on prices",
            "The adjustment made for inflation in the base year"],
           "A",
           "Base year effects occur when year-on-year CPI changes are influenced by unusual events (e.g. very high or low prices) in the same period of the base year, distorting current trend analysis. Analysts must account for this when interpreting month-on-month vs year-on-year CPI data.",
           source=src, weight=1.5, evidence_confidence=0.94),
    ]


# ===========================================================================
# STAT_LABOUR_STATISTICS — 10 questions
# Source: MoSPI PLFS, NSS Labour Survey guidelines
# ===========================================================================

def _labour_statistics_questions() -> list[dict]:
    src = "MoSPI_PLFS_NSS_Labour_Manual"
    return [
        _q("LAB001", "STAT_LABOUR_STATISTICS", "MCQ", "EASY",
           "What does PLFS stand for?",
           ["Periodic Labour Force Survey", "Primary Labour Force Study", "Public Labour Force Statistics", "Planned Labour Flow Survey"],
           "A",
           "PLFS — Periodic Labour Force Survey — is conducted by MoSPI to provide estimates of key employment and unemployment indicators. It replaced the earlier Employment and Unemployment Survey (EUS) from 2017-18.",
           source=src, evidence_confidence=0.97),

        _q("LAB002", "STAT_LABOUR_STATISTICS", "MCQ", "EASY",
           "How does ILO define 'unemployment'?",
           ["Not having a formal job",
            "Being without work, available for work, and actively seeking work",
            "Working fewer hours than desired",
            "Not earning income above poverty line"],
           "B",
           "ILO's three-criterion definition of unemployment: (1) without work, (2) currently available for work, (3) actively seeking work. India's PLFS uses this definition for measuring unemployment rates.",
           source=src, evidence_confidence=0.97),

        _q("LAB003", "STAT_LABOUR_STATISTICS", "MCQ", "MEDIUM",
           "What is the Worker Population Ratio (WPR)?",
           ["Ratio of male to female workers",
            "Percentage of population that is employed",
            "Ratio of formal to informal workers",
            "Number of workers per factory"],
           "B",
           "WPR = (Number of employed persons / Total population) × 100. It measures the share of population in employment. PLFS reports WPR by rural/urban, gender, and age groups.",
           source=src, evidence_confidence=0.96),

        _q("LAB004", "STAT_LABOUR_STATISTICS", "MCQ", "MEDIUM",
           "What is LFPR (Labour Force Participation Rate)?",
           ["Ratio of workers in labour force to total working-age population",
            "Percentage of workers in the formal sector",
            "Ratio of employed to unemployed",
            "Share of labour costs in GDP"],
           "A",
           "LFPR = (Labour Force / Working-Age Population) × 100. Labour force includes both employed and unemployed persons who are seeking work. It reflects the share of working-age people participating in the labour market.",
           source=src, evidence_confidence=0.96),

        _q("LAB005", "STAT_LABOUR_STATISTICS", "MCQ", "MEDIUM",
           "What is 'usual principal activity status' (UPS) in PLFS classification?",
           ["Current week activity status",
            "The activity in which a person spent the major part of the year (reference period of 365 days)",
            "The activity a person does in the morning",
            "The main income source"],
           "B",
           "UPS categorizes a person based on the activity on which they spent the longest time (6+ months) during the reference year. It provides a longer-term picture of labour market status, distinct from current weekly status (CWS).",
           source=src, evidence_confidence=0.95),

        _q("LAB006", "STAT_LABOUR_STATISTICS", "MCQ", "HARD",
           "What is 'disguised unemployment' in Indian labour context?",
           ["Workers hiding their employment status in surveys",
            "A situation where marginal productivity of labour is zero or near-zero, often in agricultural family labour",
            "Informal workers not captured in official statistics",
            "Workers employed through agencies without direct contracts"],
           "B",
           "Disguised unemployment occurs when more workers are employed in a task than necessary, particularly in subsistence agriculture. The extra workers add zero to production. Removing them would not reduce output. It is a major structural issue in India's agricultural labour market.",
           source=src, weight=1.5, evidence_confidence=0.95),

        _q("LAB007", "STAT_LABOUR_STATISTICS", "SCENARIO", "HARD",
           "The analyst should:",
           ["Use CWS data — it is more current",
            "Report both UPS and CWS with a note explaining the difference and the policy implications of each",
            "Use whichever shows lower unemployment to present a positive picture",
            "Average the two rates"],
           "B",
           "UPS and CWS measure different dimensions of labour market activity. Both are valid. The choice depends on the policy question. Transparency requires reporting both with methodological notes. Using only the favourable number would be ethically and statistically wrong.",
           scenario_context="An analyst finds that the usual principal activity status (UPS) shows lower unemployment than current weekly status (CWS) for the same district. A ministry official wants to use the lower figure in a press release.",
           source=src, weight=2.0, evidence_confidence=0.96),

        _q("LAB008", "STAT_LABOUR_STATISTICS", "MCQ", "HARD",
           "What adjustment is needed when comparing PLFS data across years?",
           ["No adjustment needed — PLFS uses consistent methodology",
            "Adjust for differences in survey methodology, reference periods, and population projection changes",
            "Deflate by CPI inflation",
            "Standardize by GDP growth"],
           "B",
           "Comparability requires checking for methodology changes between survey rounds. PLFS introduced quarterly urban estimates from the first annual round. Earlier EUS data used different sampling and reference periods, making direct comparison problematic without adjustment.",
           source=src, weight=2.0, evidence_confidence=0.94),

        _q("LAB009", "STAT_LABOUR_STATISTICS", "MCQ", "MEDIUM",
           "What is 'under-employment' in labour statistics?",
           ["Working part-time by choice",
            "Working in a job below one's qualification or working fewer hours than desired",
            "Not being registered with employment exchange",
            "Working in the informal sector"],
           "B",
           "Under-employment covers both time-related under-employment (insufficient hours) and skills-based under-employment (over-qualified for the role). PLFS captures time-related under-employment through subsidiary activity status.",
           source=src, weight=1.5, evidence_confidence=0.94),

        _q("LAB010", "STAT_LABOUR_STATISTICS", "MCQ", "HARD",
           "Why does India's female LFPR remain significantly lower than male LFPR despite economic growth?",
           ["Women are not counted in labour surveys",
            "Multiple factors: education access gaps, care responsibilities, social norms, sectoral concentration, and discouraged worker effects",
            "Women prefer not to work",
            "Female employment data is collected separately"],
           "B",
           "Female LFPR in India reflects structural, social, and economic constraints. The 'discouraged worker effect' (women exit when job opportunities are scarce) combined with care burden, social norms, and limited access to quality formal employment explains the gender gap. This is a key focus of India's National Skill Development strategy.",
           source=src, weight=2.0, evidence_confidence=0.95),
    ]


# ===========================================================================
# STAT_NATIONAL_ACCOUNTS — 10 questions
# Source: MoSPI National Accounts Manual, CSO SNA 2008
# ===========================================================================

def _national_accounts_questions() -> list[dict]:
    src = "MoSPI_National_Accounts_Manual_SNA2008"
    return [
        _q("NAS001", "STAT_NATIONAL_ACCOUNTS", "MCQ", "EASY",
           "What does GDP stand for?",
           ["Gross Domestic Product", "General Development Planning", "Gross Development Programme", "Government Development Product"],
           "A",
           "GDP — Gross Domestic Product — is the total monetary value of all final goods and services produced within a country's borders in a specific time period, regardless of who produces them.",
           source=src, evidence_confidence=0.97),

        _q("NAS002", "STAT_NATIONAL_ACCOUNTS", "MCQ", "EASY",
           "What are the three approaches to measuring GDP?",
           ["Production, Income, and Expenditure approaches",
            "Supply, Demand, and Trade approaches",
            "Fiscal, Monetary, and Real approaches",
            "Nominal, Real, and Deflated approaches"],
           "A",
           "GDP is measured using three equivalent approaches: (1) Production/Value Added: sum of value added across sectors; (2) Income: sum of factor incomes; (3) Expenditure: C+I+G+(X-M). In theory all three give the same result.",
           source=src, evidence_confidence=0.97),

        _q("NAS003", "STAT_NATIONAL_ACCOUNTS", "MCQ", "MEDIUM",
           "What is the difference between GDP at Market Prices and GDP at Factor Cost?",
           ["No difference — they measure the same thing",
            "GDP at Factor Cost = GDP at Market Prices − Net Indirect Taxes",
            "GDP at Factor Cost = GDP at Market Prices + Net Indirect Taxes",
            "GDP at Factor Cost includes net factor income from abroad"],
           "B",
           "GDP at Factor Cost (now GVA at basic prices in SNA 2008) removes the effect of indirect taxes and subsidies. GDP at Market Prices = GVA at Basic Prices + Taxes on Products − Subsidies on Products.",
           source=src, evidence_confidence=0.96),

        _q("NAS004", "STAT_NATIONAL_ACCOUNTS", "MCQ", "MEDIUM",
           "What is GNP and how does it differ from GDP?",
           ["They are identical",
            "GNP = GDP + Net Factor Income from Abroad",
            "GNP = GDP − Depreciation",
            "GNP = GDP at Constant Prices"],
           "B",
           "GNP (Gross National Product) = GDP + income earned by residents abroad − income earned by foreigners domestically. It measures output attributable to a nation's residents rather than within its territory.",
           source=src, evidence_confidence=0.96),

        _q("NAS005", "STAT_NATIONAL_ACCOUNTS", "MCQ", "MEDIUM",
           "What is the GDP deflator used for?",
           ["Adjusting for seasonal price changes",
            "Converting GDP from nominal to real terms by accounting for price level changes",
            "Estimating purchasing power parity",
            "Measuring inflation at the wholesale level"],
           "B",
           "GDP deflator = (Nominal GDP / Real GDP) × 100. It measures the average price level of all domestically produced goods and services. Unlike CPI, it covers the entire economy's output, not just a consumer basket.",
           source=src, evidence_confidence=0.96),

        _q("NAS006", "STAT_NATIONAL_ACCOUNTS", "MCQ", "HARD",
           "What is 'imputed rent' in national accounts?",
           ["Rent collected by the government",
            "An estimate of what owner-occupiers would pay if they rented their own home",
            "Tax revenue from real estate",
            "Price of land in the national balance sheet"],
           "A",
           "Imputed rent is included in GDP to ensure consistency: owner-occupied housing provides a service equivalent to rental housing. Without imputation, GDP would vary based on ownership rates rather than actual housing consumption.",
           source=src, weight=1.5, evidence_confidence=0.95),

        _q("NAS007", "STAT_NATIONAL_ACCOUNTS", "SCENARIO", "HARD",
           "The correct treatment under SNA 2008 is:",
           ["Include only the net resale value in GDP",
            "Include only the service charge/commission in GDP — the vehicle itself is a second-hand transfer",
            "Include the full resale price in GDP",
            "Exclude entirely — it is a private transaction"],
           "B",
           "Under SNA 2008, the sale of a second-hand good is not included in GDP as a new production — the vehicle was already counted in GDP when first produced. Only the dealer's margin (service) is included. This prevents double-counting.",
           scenario_context="A statistical analyst is calculating GDP for a period. A large volume of second-hand car transactions occurred through dealers. How should these be treated?",
           source=src, weight=2.0, evidence_confidence=0.96),

        _q("NAS008", "STAT_NATIONAL_ACCOUNTS", "MCQ", "HARD",
           "What is the System of National Accounts (SNA) 2008?",
           ["An Indian national accounts framework",
            "An internationally agreed standard framework for compiling national accounts statistics",
            "A software system for national accounts data collection",
            "A bilateral agreement between India and the UN"],
           "B",
           "SNA 2008 is the international statistical standard for compiling national accounts, jointly published by UN, IMF, World Bank, OECD, and EU. India adopted SNA 2008 in its 2015 national accounts revision.",
           source=src, weight=1.5, evidence_confidence=0.97),

        _q("NAS009", "STAT_NATIONAL_ACCOUNTS", "MCQ", "MEDIUM",
           "What is value added in national accounts?",
           ["Value of all sales",
            "Output minus intermediate inputs consumed in production",
            "Profit earned by a firm",
            "Total wages paid"],
           "B",
           "Value Added = Output − Intermediate Consumption. Summing value added across all producers avoids double-counting intermediate inputs. GDP at basic prices = sum of GVA across all sectors.",
           source=src, weight=1.5, evidence_confidence=0.96),

        _q("NAS010", "STAT_NATIONAL_ACCOUNTS", "SCENARIO", "HARD",
           "The correct approach to reconcile the discrepancy is:",
           ["Use the highest estimate to avoid underestimating the economy",
            "Investigate source-level discrepancies; apply balancing items with documentation; publish with uncertainty ranges",
            "Average the two approaches",
            "Report both without reconciliation"],
           "B",
           "When production and expenditure GDP estimates diverge, national accountants investigate source discrepancies and apply a 'statistical discrepancy' item (balancing item). This should be minimized and documented. Publishing unreconciled competing estimates would be misleading.",
           scenario_context="India's GDP estimation shows a 1.2% gap between the production-side estimate and the expenditure-side estimate for the same quarter. The CSO must decide how to present this in the advance estimate.",
           source=src, weight=2.0, evidence_confidence=0.95),
    ]


# ===========================================================================
# TECH_SQL — 5 advanced top-up questions
# ===========================================================================

def _sql_advanced_questions() -> list[dict]:
    src = "SQL_Advanced_Technical_Assessment"
    return [
        _q("SQLA001", "TECH_SQL", "MCQ", "HARD",
           "What is a Common Table Expression (CTE)?",
           ["A stored procedure",
            "A named temporary result set defined within a single query using WITH clause",
            "A type of index",
            "A constraint on a table"],
           "B",
           "CTEs (WITH clause) create named temporary result sets for readability and recursive queries. They are evaluated once per query execution and not stored permanently.",
           source=src, weight=1.5),

        _q("SQLA002", "TECH_SQL", "MCQ", "HARD",
           "What is the difference between DELETE and TRUNCATE?",
           ["No difference",
            "DELETE removes rows one-by-one (logged, can be rolled back); TRUNCATE removes all rows faster (minimally logged, cannot be rolled back in most DBs)",
            "TRUNCATE allows WHERE clause; DELETE does not",
            "DELETE is faster than TRUNCATE"],
           "B",
           "DELETE is a DML operation that is fully logged and can be rolled back. TRUNCATE is a DDL operation that is minimally logged, much faster for large tables, but cannot be conditionally filtered or rolled back in most databases.",
           source=src, weight=1.5),

        _q("SQLA003", "TECH_SQL", "SCENARIO", "HARD",
           "The most efficient approach for this reporting query is:",
           ["Full table scan with filter",
            "Create a composite index on (department_id, salary) and use covered index scan",
            "Create separate indexes on department_id and salary",
            "Use a temporary table to pre-filter"],
           "B",
           "A composite index on (department_id, salary) allows an index-only scan — the query engine can satisfy the query entirely from the index without reading the main table. This is the fastest approach for this access pattern.",
           scenario_context="You have a 10-million-row employee table. A daily report filters by department_id and sorts by salary. The query is currently taking 45 seconds.",
           source=src, weight=2.0),

        _q("SQLA004", "TECH_SQL", "MCQ", "HARD",
           "What is a window function in SQL?",
           ["A function for GUI windows",
            "A function that performs calculations across a set of rows related to the current row without collapsing the result",
            "A function that creates temporary tables",
            "A function for data partitioning"],
           "B",
           "Window functions (ROW_NUMBER, RANK, LAG, LEAD, SUM OVER, etc.) perform calculations across a 'window' of related rows, preserving individual row output. Unlike GROUP BY, they don't collapse rows.",
           source=src, weight=1.5),

        _q("SQLA005", "TECH_SQL", "SCENARIO", "HARD",
           "Best SQL approach to find the top 3 earners in each department?",
           ["SELECT name, salary FROM emp ORDER BY salary DESC LIMIT 3",
            "SELECT dept, name, salary FROM (SELECT *, RANK() OVER (PARTITION BY dept ORDER BY salary DESC) AS rnk FROM emp) WHERE rnk <= 3",
            "SELECT dept, MAX(salary) FROM emp GROUP BY dept",
            "JOIN emp to a subquery of max salaries"],
           "B",
           "Window function RANK() PARTITION BY department orders salaries within each department. Filtering WHERE rnk <= 3 in the outer query gives the top 3 per department — the correct and efficient approach.",
           scenario_context="You need a query to return the top 3 highest-paid employees in each department from a table with columns: employee_id, name, department, salary.",
           source=src, weight=2.0),
    ]


# ===========================================================================
# TECH_PYTHON — 5 data analytics top-up questions
# ===========================================================================

def _python_data_analytics_questions() -> list[dict]:
    src = "Python_Data_Analytics_Official_Statistics"
    return [
        _q("PYDA001", "TECH_PYTHON", "MCQ", "HARD",
           "In pandas, what does df.groupby('region')['value'].agg(['mean','std']) produce?",
           ["A single mean of all values",
            "Mean and standard deviation of 'value' for each unique region",
            "Standard deviation of regions",
            "Count of values per region"],
           "B",
           "groupby().agg() groups the DataFrame by 'region' and applies multiple aggregation functions simultaneously, producing a multi-column result with mean and std per region group.",
           source=src, weight=1.5),

        _q("PYDA002", "TECH_PYTHON", "SCENARIO", "HARD",
           "Best approach to handle this efficiently with pandas?",
           ["Write a for loop over rows using iterrows()",
            "Use df.apply() with a custom function",
            "Use vectorized operations: pd.cut() for binning or direct arithmetic on the Series",
            "Export to Excel and calculate manually"],
           "C",
           "Vectorized pandas operations (pd.cut, arithmetic operators on Series, np.where) are 10-100x faster than row-by-row iteration. iterrows() is the slowest approach and should be avoided for large datasets.",
           scenario_context="You have a 2-million-row pandas DataFrame with district-level survey data. You need to categorize each row into income quintiles based on household income.",
           source=src, weight=2.0),

        _q("PYDA003", "TECH_PYTHON", "MCQ", "HARD",
           "What does the following return? df.merge(df2, on='id', how='left')",
           ["All rows from df2 with matching rows from df",
            "Only rows present in both df and df2",
            "All rows from df, with NaN for df2 columns where no match exists",
            "Cartesian product of both DataFrames"],
           "C",
           "LEFT JOIN in pandas merge: preserves all rows from the left DataFrame (df). Where no match exists in df2, NaN is inserted for df2's columns. This is the standard SQL LEFT JOIN behaviour.",
           source=src, weight=1.5),

        _q("PYDA004", "TECH_PYTHON", "MCQ", "HARD",
           "Which Python library is best for statistical modelling and regression analysis in official statistics?",
           ["matplotlib", "statsmodels", "seaborn", "PIL"],
           "B",
           "statsmodels provides comprehensive statistical modelling including OLS/GLS regression, time series (ARIMA, VAR), hypothesis testing, and diagnostic plots — appropriate for government econometric analysis.",
           source=src, weight=1.5),

        _q("PYDA005", "TECH_PYTHON", "SCENARIO", "HARD",
           "The correct Python approach to prevent the discrepancy is:",
           ["Use Python float arithmetic and round at the end",
            "Use the decimal module with appropriate precision for financial calculations",
            "Multiply all values by 100 before calculation",
            "Use string formatting to round outputs"],
           "B",
           "IEEE 754 floating-point arithmetic introduces rounding errors. For financial and official statistical data where precision matters, Python's decimal.Decimal with explicit precision settings avoids cumulative floating-point errors.",
           scenario_context="You are writing a Python script to compute total expenditure across 10,000 budget line items. After summing, you notice that your Python result differs from the official Excel calculation by ₹0.03 — a rounding discrepancy that will fail audit checks.",
           source=src, weight=2.0),
    ]
