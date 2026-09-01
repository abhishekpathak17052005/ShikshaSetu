export interface CourseModuleChapter {
  id: string;
  title: string;
  duration: string;
  summary: string;
  content: string[];
  keyTakeaways: string[];
  practicalCaseStudy?: {
    title: string;
    scenario: string;
    actionTaken: string;
    impact: string;
  };
}

export interface CourseCurriculumData {
  courseId: string;
  title: string;
  provider: "iGOT Karmayogi" | "NSSTA" | "DoPT" | "MoSPI";
  competencyCode: string;
  competencyName: string;
  estimatedTime: string;
  difficulty: "Foundational" | "Intermediate" | "Advanced";
  overview: string;
  learningObjectives: string[];
  chapters: CourseModuleChapter[];
}

export const COURSE_CURRICULUM_CATALOG: Record<string, CourseCurriculumData> = {
  TECH_DATA_VISUALIZATION: {
    courseId: "igot-dataviz-101",
    title: "Data Visualization, Dashboards & Official Statistics",
    provider: "NSSTA",
    competencyCode: "TECH_DATA_VISUALIZATION",
    competencyName: "Data Visualization & Analytics",
    estimatedTime: "45 Mins",
    difficulty: "Intermediate",
    overview:
      "A comprehensive applied course for civil service officers on transforming district and scheme datasets into high-impact visual dashboards, choropleth maps, and executive briefing charts.",
    learningObjectives: [
      "Select optimal visual encodings for continuous, discrete, and geographical public datasets",
      "Apply Edward Tufte's data-ink ratio to minimize cognitive load in government publications",
      "Design progressive-disclosure KPI dashboards for district collectors and department heads",
      "Avoid common statistical distortions in scale, 3D charts, and truncation",
    ],
    chapters: [
      {
        id: "ch1",
        title: "1. Visual Encodings & Chart Grammar in Public Service",
        duration: "10 Mins",
        summary: "Understand the visual hierarchy of position, length, angle, and area for statistical accuracy.",
        content: [
          "In public administration, clarity of data communication directly influences resource allocation and citizen welfare decisions.",
          "Visual encodings rank by human perceptual accuracy: Position along a common scale is decoded most accurately, followed by length, angle, area, and volume.",
          "Avoid 3D pie charts and decorative visual effects that distort baseline proportions and deceive stakeholder perception.",
        ],
        keyTakeaways: [
          "Bar charts with a zero baseline remain the gold standard for category comparisons.",
          "Box plots communicate distribution spread, median, and district outliers simultaneously.",
        ],
        practicalCaseStudy: {
          title: "District Aspirational Program Dashboard",
          scenario: "A state health department used pie charts with 18 slices to report maternal health outcomes, obscuring underperforming blocks.",
          actionTaken: "Redesigned with horizontal ranked bar charts and target benchmark line overlays.",
          impact: "Identified 4 critical outlier blocks in the first week, leading to immediate medical officer redeployment.",
        },
      },
      {
        id: "ch2",
        title: "2. Choropleth Mapping & Spatial Distribution",
        duration: "12 Mins",
        summary: "Best practices for district and block level spatial visualizations.",
        content: [
          "Choropleth maps display geographical regions colored in proportion to a statistical variable (e.g., vaccination coverage percentage).",
          "Always normalize data as rates, ratios, or percentages (e.g., cases per 10,000 citizens) rather than raw counts to prevent land-area distortion bias.",
          "Use sequential single-hue palettes (e.g., light green to dark teal) for continuous performance indicators.",
        ],
        keyTakeaways: [
          "Never map raw population counts on choropleth maps without area or density normalization.",
          "Ensure colorblind-accessible palettes (tested for deuteranopia and protanopia).",
        ],
      },
      {
        id: "ch3",
        title: "3. Executive Dashboards & Progressive Disclosure",
        duration: "15 Mins",
        summary: "Structuring multi-tier dashboards for fast administrative decision-making.",
        content: [
          "Executive dashboards must follow the 5-second rule: the top-level status of key schemes must be immediately obvious.",
          "Progressive disclosure structure: Tier 1 (Headline KPIs & Trajectory) -> Tier 2 (District Breakdown & Variances) -> Tier 3 (Raw Exportable Records).",
          "Automate anomaly highlighting with automated conditional alerts rather than manual report scanning.",
        ],
        keyTakeaways: [
          "Group related indicators logically into Cards with clear trend indicators (+/- %).",
          "Embed metadata notes and last-updated timestamps on all public data outputs.",
        ],
        practicalCaseStudy: {
          title: "PM-Poshan Nutrition Pacing System",
          scenario: "State education secretary needed real-time tracking of mid-day meal grain stock replenishment across 45,000 schools.",
          actionTaken: "Built an alert-driven dashboard displaying deficit severity using RAG (Red/Amber/Green) thresholds.",
          impact: "Reduced stockout incidents from 12.4% to under 0.8% within 90 days.",
        },
      },
    ],
  },

  STAT_SAMPLING: {
    courseId: "igot-stat-sampling-201",
    title: "Statistical Sampling, Estimation & Large-Scale Surveys",
    provider: "iGOT Karmayogi",
    competencyCode: "STAT_SAMPLING",
    competencyName: "Statistical Sampling & Survey Design",
    estimatedTime: "55 Mins",
    difficulty: "Advanced",
    overview:
      "Master the mathematical and operational principles of probability sampling, stratified multistage sampling, weighting, and sampling error estimation for national sample surveys.",
    learningObjectives: [
      "Construct robust sampling frames and evaluate frame coverage errors",
      "Formulate stratified multistage sample designs with PPS (Probability Proportional to Size)",
      "Calculate Design Effects (Deff) and intra-cluster correlation coefficients",
      "Compute design weights, post-stratification adjustments, and non-response weights",
    ],
    chapters: [
      {
        id: "ch1",
        title: "1. Sampling Frames & Coverage Error Mitigation",
        duration: "15 Mins",
        summary: "Building and updating enumeration blocks for national surveys.",
        content: [
          "A sampling frame is the operational specification of all target population units from which sample units are selected.",
          "Coverage error arises when units in the target population are omitted (under-coverage), duplicated (over-coverage), or misclassified.",
          "Urban Frame Survey (UFS) blocks and Census Enumeration Blocks (EBs) form the foundational primary sampling units (PSUs) in Indian official statistics.",
        ],
        keyTakeaways: [
          "Frame validation must precede sample selection to minimize structural non-sampling bias.",
          "Quick listing and segmentation in large PSUs ensure manageable field enumeration workloads.",
        ],
      },
      {
        id: "ch2",
        title: "2. Stratified Multistage Sampling & PPS Methodology",
        duration: "20 Mins",
        summary: "Balancing precision, variance, and field logistical feasibility.",
        content: [
          "Stratification divides heterogeneous populations into homogeneous subpopulations (e.g. agro-climatic zones, rural/urban sectors).",
          "Probability Proportional to Size (PPS) selection at Stage 1 ensures larger villages/blocks have proportional selection chances while maintaining self-weighting properties at ultimate stage.",
          "Design Effect (Deff) measures the variance inflation due to clustering relative to Simple Random Sampling of equivalent size.",
        ],
        keyTakeaways: [
          "PPS systematic selection simplifies field operations while stabilizing sample sizes.",
          "Intra-cluster correlation (rho) guides optimal cluster size (typically 8-12 households per PSU).",
        ],
        practicalCaseStudy: {
          title: "Periodic Labour Force Survey (PLFS) Allocation",
          scenario: "MoSPI required quarterly urban employment estimates alongside annual rural indicators.",
          actionTaken: "Implemented rotational panel design with 25% sample replacement every quarter in urban areas.",
          impact: "Achieved robust sub-state unemployment precision while reducing field respondent fatigue.",
        },
      },
      {
        id: "ch3",
        title: "3. Survey Weighting & Estimation Formulas",
        duration: "20 Mins",
        summary: "From raw sample data to unbiased national parameter estimates.",
        content: [
          "The design base weight is the inverse of the overall inclusion probability (w = 1 / P_inclusion).",
          "Non-response adjustment factors scale up responding units within each stratum: W_adj = W_base * (N_selected / N_responding).",
          "Post-stratification calibrates weighted sample totals against known administrative population totals (e.g. Census projections).",
        ],
        keyTakeaways: [
          "Unweighted sample analysis leads to distorted policy conclusions in complex survey designs.",
          "Standard errors must be computed using Taylor Series Linearization or Jackknife / Bootstrap methods.",
        ],
      },
    ],
  },

  TECH_PYTHON: {
    courseId: "igot-python-policy-301",
    title: "Python Programming for Public Administration & Policy Analytics",
    provider: "iGOT Karmayogi",
    competencyCode: "TECH_PYTHON",
    competencyName: "Python Programming for Public Service",
    estimatedTime: "40 Mins",
    difficulty: "Foundational",
    overview:
      "Hands-on Python workflows using Pandas, NumPy, and Open Data APIs to automate government MIS reports, sanitize citizen datasets, and build predictive policy models.",
    learningObjectives: [
      "Load and clean massive CSV/Excel datasets using vectorized pandas operations",
      "Perform multi-index aggregation, cross-tabulations, and temporal trend analyses",
      "Anonymize Personally Identifiable Information (PII) to comply with data privacy acts",
      "Automate generation of reproducible PDF and HTML briefing reports",
    ],
    chapters: [
      {
        id: "ch1",
        title: "1. Vectorized Data Manipulation with Pandas",
        duration: "12 Mins",
        summary: "Efficiently wrangling administrative datasets with pandas DataFrames.",
        content: [
          "Pandas provides high-performance data structures built on top of NumPy C-arrays for tabular data processing.",
          "Never iterate over DataFrames using Python 'for' loops; use vectorized operations, .apply(), and boolean indexing.",
          "Handling missing data: distinquish between structural zeros and true missing values with pd.isna() and fillna().",
        ],
        keyTakeaways: [
          "df.groupby(['district', 'scheme'])['expenditure'].sum() replaces complex SQL joins in ad-hoc analysis.",
          "Memory optimization using category dtypes reduces RAM footprint by up to 80% on multi-million row datasets.",
        ],
      },
      {
        id: "ch2",
        title: "2. PII Sanitation & Cryptographic Anonymization",
        duration: "14 Mins",
        summary: "Protecting citizen privacy in public policy research data pipelines.",
        content: [
          "Under the Digital Personal Data Protection (DPDP) Act, public datasets released for research must undergo strict de-identification.",
          "Pseudonymize direct identifiers (Aadhaar, Mobile Number) using HMAC-SHA256 with an environment-managed secret salt.",
          "Apply k-anonymity principles so that rare combinations of quasi-identifiers (Age, Gender, Pin Code) cannot re-identify individuals.",
        ],
        keyTakeaways: [
          "Strip high-risk columns before saving intermediate exploratory data files.",
          "Maintain audit logs of all transformations in the automated pipeline.",
        ],
      },
      {
        id: "ch3",
        title: "3. Automated Reporting & Public Policy Analytics",
        duration: "14 Mins",
        summary: "Generating automated weekly progress reports for district administration.",
        content: [
          "Combine pandas data aggregation with Jinja2 templates and Matplotlib/Plotly charts to generate automated PDF briefing packs.",
          "Schedule automated cron jobs that pull from departmental database replicas and output executive summaries every Monday morning.",
        ],
        keyTakeaways: [
          "Automated pipelines eliminate manual spreadsheet copy-paste human error.",
          "Version-control all data transformation scripts with Git for full institutional auditability.",
        ],
      },
    ],
  },

  DIGITAL_GOVERNANCE: {
    courseId: "igot-digigov-401",
    title: "Digital India Architecture & Citizen e-Service Delivery",
    provider: "iGOT Karmayogi",
    competencyCode: "DIGITAL_GOVERNANCE",
    competencyName: "Digital Governance & e-Gov Architecture",
    estimatedTime: "35 Mins",
    difficulty: "Foundational",
    overview:
      "Deep dive into India Stack, Open API protocols, DigiLocker integration, and service level agreement (SLA) management for transparent governance.",
    learningObjectives: [
      "Understand the layers of India Stack: Identity (Aadhaar), Payments (UPI/PFMS), and Verifiable Credentials (DigiLocker)",
      "Implement citizen-centric portal design compliant with GIGW accessibility standards",
      "Deploy Direct Benefit Transfer (DBT) pipelines with end-to-end reconciliation",
      "Ensure robust uptime, cybersecurity monitoring, and disaster recovery readiness",
    ],
    chapters: [
      {
        id: "ch1",
        title: "1. The India Stack Ecosystem & Digital Public Infrastructure",
        duration: "10 Mins",
        summary: "Foundational architectural layers powering national-scale public services.",
        content: [
          "Digital Public Infrastructure (DPI) provides open rails upon which public and private sector services are built.",
          "Paperless governance through DigiLocker enables instant algorithmic verification of educational, vehicle, and land records.",
          "Unified Payments Interface (UPI) and PFMS enable real-time targeted disbursements without leakage.",
        ],
        keyTakeaways: [
          "Open protocols prevent vendor lock-in and enable interoperability across departments.",
          "Consent-driven data sharing frameworks empower citizens over their personal data.",
        ],
      },
      {
        id: "ch2",
        title: "2. GIGW Compliance & Universal Digital Accessibility",
        duration: "12 Mins",
        summary: "Building inclusive government web platforms for all citizens.",
        content: [
          "Guidelines for Indian Government Websites (GIGW 3.0) mandates compliance with WCAG 2.1 Level AA standards.",
          "Ensure complete screen reader compatibility, high contrast mode, responsive mobile layouts, and bilingual language toggling (English & Hindi).",
        ],
        keyTakeaways: [
          "All interactive elements must feature accessible ARIA labels and descriptive tooltips.",
          "Ensure fast load times on 2G/3G mobile networks in rural locations.",
        ],
      },
    ],
  },
};

export function getCourseCurriculum(competencyCode?: string, resourceTitle?: string): CourseCurriculumData {
  if (competencyCode && COURSE_CURRICULUM_CATALOG[competencyCode]) {
    return COURSE_CURRICULUM_CATALOG[competencyCode];
  }

  // Fallback dynamic generator for any competency
  const code = competencyCode || "GENERAL_GOV";
  const title = resourceTitle || code.replace(/_/g, " ");

  return {
    courseId: `course-${code.toLowerCase()}`,
    title: title,
    provider: "iGOT Karmayogi",
    competencyCode: code,
    competencyName: code.replace(/_/g, " "),
    estimatedTime: "45 Mins",
    difficulty: "Intermediate",
    overview: `Official public service curriculum module on ${title}. Covers key administrative frameworks, operational best practices, and capability growth standards.`,
    learningObjectives: [
      `Understand fundamental principles and legal frameworks governing ${title}`,
      "Apply standard operating procedures in day-to-day administrative execution",
      "Analyze real-world public governance case studies and field scenarios",
      "Validate capability acquisition through grounded practice quizzes and assessments",
    ],
    chapters: [
      {
        id: "ch1",
        title: "1. Regulatory Foundations & Core Concepts",
        duration: "15 Mins",
        summary: `Overview of statutory guidelines and key objectives for ${title}.`,
        content: [
          `Public servants must understand the overarching policy mandates and standard operating procedures related to ${title}.`,
          "Governance frameworks prioritize transparency, accountability, speed of service delivery, and citizen impact.",
        ],
        keyTakeaways: [
          "Adhere strictly to official departmental guidelines and circulars.",
          "Document all administrative actions in the transparent audit trail.",
        ],
        practicalCaseStudy: {
          title: "Public Administration Implementation Showcase",
          scenario: `Department needed to streamline operational procedures for ${title}.`,
          actionTaken: "Adopted standardized digital protocols and real-time monitoring benchmarks.",
          impact: "Reduced processing turnaround time by 65% and improved citizen satisfaction.",
        },
      },
      {
        id: "ch2",
        title: "2. Field Application & Standard Operating Procedures",
        duration: "15 Mins",
        summary: "Step-by-step methodologies and practical execution workflows.",
        content: [
          "Detailed execution protocol for field officers and administrative personnel.",
          "Mitigating common bottlenecks and ensuring cross-departmental coordination.",
        ],
        keyTakeaways: [
          "Ensure proactive stakeholder communication and periodic review meetings.",
          "Leverage digital dashboards to monitor progress against weekly targets.",
        ],
      },
      {
        id: "ch3",
        title: "3. Case Studies, Key Learnings & Self-Assessment",
        duration: "15 Mins",
        summary: "Applied review and preparation for capability validation.",
        content: [
          "Synthesizing key takeaways and evaluating administrative decision points.",
          "Proceed to the Practice Quiz to test your retention and record supporting evidence in your capability ledger.",
        ],
        keyTakeaways: [
          "Learning modules build foundational knowledge; quizzes and proctored assessments validate true capability.",
        ],
      },
    ],
  };
}
