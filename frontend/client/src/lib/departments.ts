/**
 * Indian Civil Services & Ministry Department Taxonomy
 * Defines hierarchical Department -> Professional Role -> Designation structure.
 */

export interface RoleConfig {
  role_code: string;
  role_name: string;
  domain: string;
  description: string;
  designations: string[];
}

export interface DepartmentConfig {
  department_name: string;
  department_code: string;
  description: string;
  roles: RoleConfig[];
}

export const DEPARTMENT_TAXONOMY: DepartmentConfig[] = [
  {
    department_name: "Ministry of Education",
    department_code: "MOE",
    description: "Department of School Education & Literacy, Higher Education & NCERT",
    roles: [
      {
        role_code: "EDUCATION_OFFICER",
        role_name: "Education & Curriculum Officer",
        domain: "Academic Standards & Pedagogy",
        description: "Responsible for curriculum standards, pedagogical assessment, institutional learning quality, and teacher capability building.",
        designations: [
          "Teacher",
          "Senior Teacher (PGT/TGT)",
          "Headmaster / Principal",
          "Assistant Professor / Lecturer",
          "Block Education Officer (BEO)",
          "District Education Officer (DEO)",
          "Curriculum & Assessment Specialist",
          "Education Research Officer",
        ],
      },
      {
        role_code: "DIGITAL_LEARNING_SPECIALIST",
        role_name: "Digital Pedagogy & EdTech Specialist",
        domain: "Educational Technology & DIKSHA",
        description: "Designs digital learning frameworks, online assessment systems, and Karmayogi/DIKSHA e-content.",
        designations: [
          "Digital Learning Specialist",
          "EdTech Coordinator",
          "Smart Classroom Lead",
          "Online Assessment Officer",
          "ICT In-charge",
        ],
      },
    ],
  },
  {
    department_name: "Ministry of Statistics & Programme Implementation (MoSPI)",
    department_code: "MOSPI",
    description: "National Statistical Office (NSO), NSSTA & Central Statistics",
    roles: [
      {
        role_code: "STATISTICAL_OFFICER",
        role_name: "Statistical Officer",
        domain: "Statistical Analysis & Governance",
        description: "Designs surveys, validates sampling methodology, and analyzes large-scale national datasets.",
        designations: [
          "Statistical Officer",
          "Senior Statistical Officer (SSO)",
          "Assistant Director (Statistics)",
          "Deputy Director (Data Management)",
          "Joint Director (Field Operations)",
          "Director (Macroeconomic Statistics)",
        ],
      },
      {
        role_code: "DATA_ANALYST_OFFICER",
        role_name: "Survey & Data Analytics Officer",
        domain: "Computational Statistics & Big Data",
        description: "Focuses on computational statistics, big data wrangling, and national SDG indicator monitoring.",
        designations: [
          "Data Analyst",
          "Senior Data Analyst",
          "Lead Statistician",
          "Survey Informatics Officer",
        ],
      },
    ],
  },
  {
    department_name: "Ministry of Electronics and Information Technology (MeitY)",
    department_code: "MEITY",
    description: "National Informatics Centre (NIC), Digital India & Cyber Governance",
    roles: [
      {
        role_code: "DIGITAL_GOVERNANCE_ARCHITECT",
        role_name: "Digital Governance & e-Gov Architect",
        domain: "Digital Governance & Architecture",
        description: "Architects citizen-facing digital public infrastructure and secure government portals.",
        designations: [
          "Informatics Officer / Scientist 'B'",
          "Technical Director (e-Gov)",
          "IT Systems Officer",
          "e-Governance Project Lead",
          "Enterprise Architect",
        ],
      },
      {
        role_code: "CYBERSECURITY_GOVERNANCE_OFFICER",
        role_name: "Cybersecurity & Data Privacy Officer",
        domain: "Cyber Defense & Compliance",
        description: "Oversees public sector cyber defense, data protection compliance, and threat mitigation.",
        designations: [
          "Cybersecurity Lead",
          "Information Security Officer (CISO Team)",
          "Data Protection Officer",
          "Security Auditor",
        ],
      },
    ],
  },
  {
    department_name: "Department of Personnel and Training (DoPT)",
    department_code: "DOPT",
    description: "Ministry of Personnel, Public Grievances and Pensions & Karmayogi Mission",
    roles: [
      {
        role_code: "CAPACITY_BUILDING_OFFICER",
        role_name: "Civil Services Capacity Building Officer",
        domain: "Civil Services HR & Mission Karmayogi",
        description: "Coordinates Mission Karmayogi, competency-based HR management, and civil service training frameworks.",
        designations: [
          "Under Secretary",
          "Section Officer (SO)",
          "Assistant Section Officer (ASO)",
          "Deputy Secretary",
          "Director (Training)",
          "Capacity Building Manager",
        ],
      },
    ],
  },
  {
    department_name: "Ministry of Finance",
    department_code: "MOF",
    description: "Department of Expenditure, Economic Affairs & Public Financial Management",
    roles: [
      {
        role_code: "PUBLIC_FINANCIAL_MANAGEMENT_OFFICER",
        role_name: "Financial Management & Audit Officer",
        domain: "Public Finance & Fiscal Governance",
        description: "Monitors government budget expenditure, fiscal analytics, and procurement compliance.",
        designations: [
          "Accounts Officer (AAO / AO)",
          "Senior Accounts Officer",
          "Audit Officer",
          "Assistant Commissioner (Revenue)",
          "Financial Analyst",
        ],
      },
    ],
  },
  {
    department_name: "Ministry of Health and Family Welfare (MoHFW)",
    department_code: "MOHFW",
    description: "National Health Authority, Ayushman Bharat Digital Mission & DGHS",
    roles: [
      {
        role_code: "PUBLIC_HEALTH_DATA_OFFICER",
        role_name: "Public Health & Epidemiological Data Officer",
        domain: "Public Health Systems & Analytics",
        description: "Tracks epidemiological datasets, disease surveillance, and digital health mission metrics.",
        designations: [
          "Medical Officer (Public Health)",
          "Health Data Analyst",
          "District Health Programme Officer",
          "Surveillance Officer",
          "Hospital Administrator",
        ],
      },
    ],
  },
  {
    department_name: "Ministry of Rural Development & Panchayati Raj",
    department_code: "MORD",
    description: "Department of Rural Development, Panchayati Raj Institutions & NRLM",
    roles: [
      {
        role_code: "RURAL_DEVELOPMENT_OFFICER",
        role_name: "Rural Schemes & Grassroots Governance Officer",
        domain: "Grassroots Public Service Delivery",
        description: "Supervises grassroots public service delivery, rural infrastructure schemes, and citizen governance.",
        designations: [
          "Block Development Officer (BDO)",
          "District Project Manager (NRLM/MGNREGS)",
          "Panchayat Secretary",
          "Rural Infrastructure Specialist",
        ],
      },
    ],
  },
];
