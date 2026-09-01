"""Seed comprehensive demo quizzes for iGOT & NSSTA curriculum courses."""
import sys
from pathlib import Path
from datetime import UTC, datetime
from bson import ObjectId
from pymongo.database import Database

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from app.core.config import get_settings
from app.core.database import close_database, initialize_database


DEMO_QUIZZES = [
    {
        "title": "iGOT: Data Visualization, Dashboards & Official Statistics",
        "description": "Comprehensive competency evaluation for public sector data visualization, official indicators, and executive dashboards.",
        "competency_code": "TECH_DATA_VISUALIZATION",
        "status": "PUBLISHED",
        "assigned_to": [],
        "questions": [
            {
                "question": "Which visualization type is most appropriate for displaying the distribution and identifying outliers in district-level literacy data?",
                "options": [
                    "A. Box Plot (Box-and-Whisker)",
                    "B. 3D Pie Chart",
                    "C. Unsorted Bar Chart",
                    "D. Radar Chart",
                ],
                "correct_answer": "A",
                "explanation": "A Box Plot efficiently shows the median, quartiles, and statistical outliers across geographical distributions without distortion.",
                "difficulty": "MEDIUM",
                "source_chunks": ["chunk-dataviz-01"],
            },
            {
                "question": "When designing public sector KPI dashboards for senior leadership, which principle ensures maximum clarity?",
                "options": [
                    "A. Maximize color variety across all cards",
                    "B. Progressive disclosure with high-level summaries drillable to granular metrics",
                    "C. Display raw database tables without aggregations",
                    "D. Require manual page refreshes every minute",
                ],
                "correct_answer": "B",
                "explanation": "Progressive disclosure allows executive decision-makers to immediately grasp high-level trends while enabling deep-dives into district/block granular data.",
                "difficulty": "EASY",
                "source_chunks": ["chunk-dataviz-02"],
            },
            {
                "question": "In statistical maps (Choropleth), what color mapping practice is standard for sequential data like poverty rate percentages?",
                "options": [
                    "A. Random rainbow palette",
                    "B. Single hue with varying lightness/saturation from low to high",
                    "C. Alternating black and white stripes",
                    "D. Neon green for all ranges",
                ],
                "correct_answer": "B",
                "explanation": "Sequential color palettes using single hue intensity ensure intuitive cognitive interpretation of progression from low to high magnitudes.",
                "difficulty": "MEDIUM",
                "source_chunks": ["chunk-dataviz-03"],
            },
            {
                "question": "Why is minimizing the 'data-ink ratio' (Edward Tufte's principle) crucial for government statistical reports?",
                "options": [
                    "A. It reduces printer ink cost only",
                    "B. It eliminates non-essential decorative clutter so the core message is immediately apparent",
                    "C. It hides confidential information",
                    "D. It replaces all graphs with plain text",
                ],
                "correct_answer": "B",
                "explanation": "Maximizing the data-ink ratio removes visual noise, gridlines, and 3D effects, spotlighting the actual statistical evidence.",
                "difficulty": "HARD",
                "source_chunks": ["chunk-dataviz-04"],
            },
            {
                "question": "Which chart type is best suited for demonstrating the cumulative monthly expenditure progress against annual scheme budget allocation?",
                "options": [
                    "A. Scatter plot",
                    "B. Area / Step Line Chart with target benchmark overlay",
                    "C. Donut chart with 20 slices",
                    "D. Word cloud",
                ],
                "correct_answer": "B",
                "explanation": "An area or line chart with a target trajectory benchmark clearly visualizes burn rates, cumulative actuals, and pacing against annual fiscal budgets.",
                "difficulty": "MEDIUM",
                "source_chunks": ["chunk-dataviz-05"],
            },
        ],
    },
    {
        "title": "iGOT: Statistical Sampling, Estimation & Survey Design",
        "description": "Authoritative assessment on probability sampling methods, sample size determination, and survey weighting.",
        "competency_code": "STAT_SAMPLING",
        "status": "PUBLISHED",
        "assigned_to": [],
        "questions": [
            {
                "question": "In a nationwide socio-economic survey, why is Stratified Multistage Sampling preferred over Simple Random Sampling?",
                "options": [
                    "A. It guarantees a 100% response rate",
                    "B. It ensures representation of heterogeneous sub-populations (e.g. rural/urban) and reduces field logistics costs",
                    "C. It does not require any sampling frame",
                    "D. It eliminates the need for survey weights",
                ],
                "correct_answer": "B",
                "explanation": "Stratification ensures precision across diverse subgroups, while multistage clustering groups fieldwork geographically to manage operational survey costs.",
                "difficulty": "MEDIUM",
                "source_chunks": ["chunk-sampling-01"],
            },
            {
                "question": "What is the primary consequence of using an outdated sampling frame in a large-scale household survey?",
                "options": [
                    "A. Increase in non-sampling coverage errors (under-coverage and omission)",
                    "B. Automatic reduction in standard error",
                    "C. Zero sampling variance",
                    "D. Doubling of sample size",
                ],
                "correct_answer": "A",
                "explanation": "Outdated frames miss new settlements, urban expansions, or demographic shifts, introducing systematic under-coverage bias into national estimates.",
                "difficulty": "MEDIUM",
                "source_chunks": ["chunk-sampling-02"],
            },
            {
                "question": "When calculating the Design Effect (Deff) of a cluster sample, a Deff value greater than 1 indicates:",
                "options": [
                    "A. Cluster sampling is more efficient than Simple Random Sampling",
                    "B. Intra-cluster correlation has increased the variance compared to an SRS of the same size",
                    "C. Sample size can be reduced by 50%",
                    "D. There is no variance in the population",
                ],
                "correct_answer": "B",
                "explanation": "Deff > 1 indicates that clustering has introduced positive intra-cluster correlation (homogeneity within villages/blocks), requiring a larger sample size to match SRS precision.",
                "difficulty": "HARD",
                "source_chunks": ["chunk-sampling-03"],
            },
            {
                "question": "Which sampling technique is most appropriate when a complete list of all individual citizens in a remote region is unavailable, but administrative ward boundaries are well documented?",
                "options": [
                    "A. Area Sampling / Cluster Sampling",
                    "B. Quota Sampling",
                    "C. Convenience Sampling",
                    "D. Snowball Sampling",
                ],
                "correct_answer": "A",
                "explanation": "Area sampling uses defined geographic boundaries as primary sampling units (PSUs) when individual listing is unavailable prior to the survey.",
                "difficulty": "MEDIUM",
                "source_chunks": ["chunk-sampling-04"],
            },
            {
                "question": "What is the formula used in survey weighting for non-response adjustment?",
                "options": [
                    "A. Base Weight × (Selected Sample / Responding Sample)",
                    "B. Base Weight + Total Population",
                    "C. 1 / Total Sample",
                    "D. Base Weight × Standard Error",
                ],
                "correct_answer": "A",
                "explanation": "Non-response adjustment scales up the weights of responding units in a stratum by the inverse of the response rate (Selected / Responding).",
                "difficulty": "HARD",
                "source_chunks": ["chunk-sampling-05"],
            },
        ],
    },
    {
        "title": "NSSTA: Survey Design & Questionnaire Methodology",
        "description": "Practical assessment on CAPI questionnaire design, cognitive testing, and field survey administration.",
        "competency_code": "STAT_SURVEY_DESIGN",
        "status": "PUBLISHED",
        "assigned_to": [],
        "questions": [
            {
                "question": "In Computer Assisted Personal Interviewing (CAPI), what is the key advantage of embedded validation rules over paper surveys?",
                "options": [
                    "A. Paper surveys are faster to print",
                    "B. CAPI prevents impossible entries and enforces logical skip patterns at the exact point of data collection",
                    "C. CAPI eliminates the need for enumerator training",
                    "D. CAPI only works without internet",
                ],
                "correct_answer": "B",
                "explanation": "Real-time range checks, consistency validations, and automated routing in CAPI drastically reduce post-survey data cleaning bottlenecks.",
                "difficulty": "EASY",
                "source_chunks": ["chunk-survey-01"],
            },
            {
                "question": "What is a 'double-barreled question' and why must it be avoided in official public surveys?",
                "options": [
                    "A. A question translated into two languages",
                    "B. A question that touches upon two distinct issues while allowing only one answer",
                    "C. A question asked twice to verify honesty",
                    "D. A question with two options",
                ],
                "correct_answer": "B",
                "explanation": "Double-barreled questions (e.g. 'Are you satisfied with school infrastructure and teacher attendance?') confuse respondents and produce uninterpretable data.",
                "difficulty": "MEDIUM",
                "source_chunks": ["chunk-survey-02"],
            },
            {
                "question": "Cognitive pre-testing of survey questionnaires primarily helps identify:",
                "options": [
                    "A. Server memory requirements",
                    "B. How respondents interpret question wording, retrieve memories, and formulate answers",
                    "C. GPS satellite coordinates",
                    "D. Printing margins",
                ],
                "correct_answer": "B",
                "explanation": "Cognitive interviewing uncovers comprehension ambiguities, recall difficulties, and social desirability biases before rollout.",
                "difficulty": "HARD",
                "source_chunks": ["chunk-survey-03"],
            },
            {
                "question": "Which recall period is standard for high-frequency minor household expenditures (e.g. vegetables, transit) to minimize recall decay?",
                "options": [
                    "A. 365 days",
                    "B. 7 days / 30 days",
                    "C. 5 years",
                    "D. 10 years",
                ],
                "correct_answer": "B",
                "explanation": "Frequent daily/weekly purchases suffer severe recall loss if extended beyond a 7 to 30 day reference period.",
                "difficulty": "EASY",
                "source_chunks": ["chunk-survey-04"],
            },
            {
                "question": "What is the purpose of conducting a pilot survey (dress rehearsal) prior to national census or survey launch?",
                "options": [
                    "A. To publish preliminary statistics immediately",
                    "B. To test survey instruments, logistics, supervisor-to-enumerator ratios, and CAPI synchronization workflows",
                    "C. To reduce the overall budget by 90%",
                    "D. To replace sample survey methodology",
                ],
                "correct_answer": "B",
                "explanation": "Pilot surveys test all operational dimensions end-to-end under real field conditions.",
                "difficulty": "MEDIUM",
                "source_chunks": ["chunk-survey-05"],
            },
        ],
    },
    {
        "title": "iGOT: National Data Quality Framework & Statistical Governance",
        "description": "Assessment on United Nations NQAF dimensions, MoSPI standards, metadata management, and data integrity.",
        "competency_code": "STAT_DATA_QUALITY_FRAMEWORKS",
        "status": "PUBLISHED",
        "assigned_to": [],
        "questions": [
            {
                "question": "Under the UN National Quality Assurance Framework (NQAF), which dimension measures the degree to which statistical information meets user needs?",
                "options": [
                    "A. Relevance",
                    "B. Timeliness",
                    "C. Punctuality",
                    "D. Accessibility",
                ],
                "correct_answer": "A",
                "explanation": "Relevance assesses whether the statistical outputs address current and emerging user priorities and policy requirements.",
                "difficulty": "MEDIUM",
                "source_chunks": ["chunk-dq-01"],
            },
            {
                "question": "What does the 'Accuracy and Reliability' dimension of data quality evaluate?",
                "options": [
                    "A. Whether the survey was completed in 10 minutes",
                    "B. How close estimated statistical measures are to the true unknown population values",
                    "C. The font size used in the PDF publication",
                    "D. The number of downloads from the portal",
                ],
                "correct_answer": "B",
                "explanation": "Accuracy relates to the closeness between computations and true population parameters, accounting for sampling and non-sampling errors.",
                "difficulty": "MEDIUM",
                "source_chunks": ["chunk-dq-02"],
            },
            {
                "question": "Which practice ensures statistical data accessibility according to Open Data guidelines?",
                "options": [
                    "A. Publishing only locked PDF scans of printed tables",
                    "B. Providing machine-readable data formats (CSV/JSON) alongside comprehensive standardized metadata and methodology notes",
                    "C. Charging high subscription fees for public indicators",
                    "D. Deleting raw datasets after 30 days",
                ],
                "correct_answer": "B",
                "explanation": "Open Data mandates machine-readability, standardized schemas, and transparent methodological metadata for public re-use.",
                "difficulty": "EASY",
                "source_chunks": ["chunk-dq-03"],
            },
            {
                "question": "What is the role of Data Quality Audits and Re-interview programs in national survey quality control?",
                "options": [
                    "A. To punish respondents",
                    "B. To independently verify a subsample of collected records and quantify enumerator variance and fabrication risks",
                    "C. To change survey objectives mid-way",
                    "D. To reduce questionnaire length",
                ],
                "correct_answer": "B",
                "explanation": "Re-interviews by independent supervisors catch enumerator drift, misunderstanding of concepts, or fraudulent submissions.",
                "difficulty": "HARD",
                "source_chunks": ["chunk-dq-04"],
            },
            {
                "question": "In official statistics, what constitutes 'Coherence and Comparability'?",
                "options": [
                    "A. Statistics are consistent over time, across regions, and between different data sources covering the same domain",
                    "B. All surveys use identical sample sizes regardless of population",
                    "C. Results are published only once every decade",
                    "D. Data is presented in a single language",
                ],
                "correct_answer": "A",
                "explanation": "Coherence ensures that statistical indicators derived from different sources or time periods can be reliably compared and integrated.",
                "difficulty": "HARD",
                "source_chunks": ["chunk-dq-05"],
            },
        ],
    },
    {
        "title": "iGOT: Python Programming for Public Administration & Policy Analytics",
        "description": "Evaluation of Python programming concepts, pandas data manipulation, and automated reporting in civil service.",
        "competency_code": "TECH_PYTHON",
        "status": "PUBLISHED",
        "assigned_to": [],
        "questions": [
            {
                "question": "In pandas, which method is recommended for loading large district census CSV files while handling missing indicator values properly?",
                "options": [
                    "A. pd.read_csv('data.csv', na_values=['NA', '-', ' '])",
                    "B. open('data.csv').readlines()",
                    "C. csv.load_all()",
                    "D. pd.import_excel()",
                ],
                "correct_answer": "A",
                "explanation": "pd.read_csv with explicit na_values converts non-standard null markers directly into clean NaN floats for statistical calculations.",
                "difficulty": "EASY",
                "source_chunks": ["chunk-python-01"],
            },
            {
                "question": "Which pandas operation computes summary statistics (mean, median, count) of public school enrollment grouped by district?",
                "options": [
                    "A. df.filter('district').sum()",
                    "B. df.groupby('district')['enrollment'].agg(['count', 'mean', 'median'])",
                    "C. df.sort_values('district')",
                    "D. df.drop_duplicates('district')",
                ],
                "correct_answer": "B",
                "explanation": "The groupby().agg() chain computes multi-metric aggregations across categorical administrative levels.",
                "difficulty": "MEDIUM",
                "source_chunks": ["chunk-python-02"],
            },
            {
                "question": "Why is vectorized computation in numpy and pandas superior to Python 'for' loops for multi-million record citizen databases?",
                "options": [
                    "A. Vectorized code runs in C under the hood, executing array-level operations orders of magnitude faster with lower memory overhead",
                    "B. For loops are deprecated in modern Python",
                    "C. Vectorization prevents network disconnection",
                    "D. Vectorization requires no RAM",
                ],
                "correct_answer": "A",
                "explanation": "Vectorized operations leverage contiguous memory buffers and optimized SIMD instructions in C/Fortran backends.",
                "difficulty": "HARD",
                "source_chunks": ["chunk-python-03"],
            },
            {
                "question": "Which Python library is standard for creating interactive web dashboards and public policy analytical charts?",
                "options": [
                    "A. Plotly / Seaborn / Matplotlib",
                    "B. Socket",
                    "C. Tkinter",
                    "D. Regex",
                ],
                "correct_answer": "A",
                "explanation": "Plotly, Seaborn, and Matplotlib are the primary data visualization libraries in the Python scientific ecosystem.",
                "difficulty": "EASY",
                "source_chunks": ["chunk-python-04"],
            },
            {
                "question": "What is the best practice for handling sensitive Personally Identifiable Information (PII) during Python data pipeline processing?",
                "options": [
                    "A. Save PII in public GitHub repos",
                    "B. Anonymize/Pseudonymize identifiers using cryptographic hashing (e.g. SHA-256 with salt) and drop unnecessary PII fields early",
                    "C. Convert all text to lowercase",
                    "D. Print citizen phone numbers to console logs",
                ],
                "correct_answer": "B",
                "explanation": "Data privacy guidelines mandate early hashing or pseudonymization of PII before exploratory analysis.",
                "difficulty": "MEDIUM",
                "source_chunks": ["chunk-python-05"],
            },
        ],
    },
    {
        "title": "iGOT: Digital Governance Architecture & e-Service Delivery",
        "description": "Assessment of India Stack, API-driven e-governance, digital public infrastructure (DPI), and citizen service delivery.",
        "competency_code": "DIGITAL_GOVERNANCE",
        "status": "PUBLISHED",
        "assigned_to": [],
        "questions": [
            {
                "question": "Which architectural principle forms the foundation of India's Digital Public Infrastructure (DPI)?",
                "options": [
                    "A. Monolithic proprietary lock-in databases",
                    "B. Open, modular, interoperable API protocols enabling inclusive public and private innovation",
                    "C. Paper-based dual verification at every step",
                    "D. Isolated district servers without internet connectivity",
                ],
                "correct_answer": "B",
                "explanation": "DPI relies on open API specifications, minimalist verifiable registries, and federated architecture.",
                "difficulty": "EASY",
                "source_chunks": ["chunk-dpi-01"],
            },
            {
                "question": "What is the primary role of DigiLocker in citizen service delivery workflows?",
                "options": [
                    "A. Social media file sharing",
                    "B. Secure, consent-driven issuance, verification, and storage of legally recognized digital credentials",
                    "C. Email client for government departments",
                    "D. Video streaming portal",
                ],
                "correct_answer": "B",
                "explanation": "DigiLocker acts as a trusted document issuance and digital verification framework under the IT Act.",
                "difficulty": "MEDIUM",
                "source_chunks": ["chunk-dpi-02"],
            },
            {
                "question": "How does API-based Direct Benefit Transfer (DBT) improve scheme governance compared to manual cheque disbursement?",
                "options": [
                    "A. Increases paperwork overhead",
                    "B. Eliminates ghost beneficiaries through Aadhaar authentication and ensures instant electronic fund transfer directly to bank accounts",
                    "C. Delays payments by several months",
                    "D. Requires citizens to visit state capitals",
                ],
                "correct_answer": "B",
                "explanation": "DBT integrates Aadhaar payment bridges with PFMS, minimizing leakage and administrative intermediaries.",
                "difficulty": "EASY",
                "source_chunks": ["chunk-dpi-03"],
            },
            {
                "question": "In government web applications, compliance with GIGW (Guidelines for Indian Government Websites) ensures:",
                "options": [
                    "A. Websites use heavy video animations",
                    "B. Digital accessibility (WCAG 2.1 AA), bilingual capability, device responsiveness, and cybersecurity hardening",
                    "C. Restricted access to government officials only",
                    "D. Daily redesign of the home page",
                ],
                "correct_answer": "B",
                "explanation": "GIGW establishes strict accessibility standards for persons with disabilities, security standards, and responsive design.",
                "difficulty": "MEDIUM",
                "source_chunks": ["chunk-dpi-04"],
            },
            {
                "question": "What is the primary benefit of deploying a Microservices architecture for a nationwide portal serving millions of daily citizen requests?",
                "options": [
                    "A. Independent scalability, fault isolation, and agile deployment of distinct business modules without entire system downtime",
                    "B. Eliminates need for cloud servers",
                    "C. Guarantees zero code testing is required",
                    "D. Forces all features to use the same database table",
                ],
                "correct_answer": "A",
                "explanation": "Microservices decouple services so high-load components (e.g. OTP verification) scale independently without affecting reporting modules.",
                "difficulty": "HARD",
                "source_chunks": ["chunk-dpi-05"],
            },
        ],
    },
]


def sync_demo_quizzes(database: Database) -> None:
    """Sync all demo course quizzes into the database."""
    print("\nSynchronizing Demo Course Quizzes...")
    now = datetime.now(UTC)
    
    # Get trainer or admin ID as creator
    trainer = database.users.find_one({"access_role": {"$in": ["TRAINER", "ADMIN"]}})
    trainer_id = str(trainer["_id"]) if trainer else str(ObjectId())

    for quiz_spec in DEMO_QUIZZES:
        comp_code = quiz_spec["competency_code"]
        title = quiz_spec["title"]
        
        # Check if quiz already exists
        existing = database.quizzes.find_one({"title": title})
        
        # Prepare questions with IDs
        questions = []
        for idx, q in enumerate(quiz_spec["questions"]):
            qid = f"demo-{comp_code.lower()}-q{idx + 1}"
            q_doc = {
                "question_id": qid,
                "question": q["question"],
                "options": q["options"],
                "correct_answer": q["correct_answer"],
                "explanation": q["explanation"],
                "difficulty": q["difficulty"],
                "source_chunks": q.get("source_chunks", []),
                "trainer_id": trainer_id,
                "status": "APPROVED",
                "updated_at": now,
            }
            questions.append(q_doc)
            # Upsert into trainer_questions
            database.trainer_questions.update_one(
                {"question_id": qid},
                {"$set": q_doc, "$setOnInsert": {"created_at": now}},
                upsert=True,
            )

        quiz_doc = {
            "title": title,
            "description": quiz_spec["description"],
            "competency_code": comp_code,
            "trainer_id": trainer_id,
            "status": "PUBLISHED",
            "assigned_to": [],  # Open to all learners
            "question_count": len(questions),
            "questions": questions,
            "is_demo": True,
            "updated_at": now,
        }

        database.quizzes.update_one(
            {"title": title},
            {"$set": quiz_doc, "$setOnInsert": {"_id": ObjectId(), "created_at": now}},
            upsert=True,
        )
        print(f"  -> Synced Quiz: '{title}' ({len(questions)} Questions) [Competency: {comp_code}]")


def main() -> None:
    settings = get_settings()
    client, database = initialize_database(settings.mongodb_uri, settings.mongodb_database)
    print(f"Connected to Database: {database.name}")
    try:
        sync_demo_quizzes(database)
        print("\nDEMO QUIZZES SYNCHRONIZED SUCCESSFULLY!")
    finally:
        close_database(client)


if __name__ == "__main__":
    main()
