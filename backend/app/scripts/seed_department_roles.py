"""
Department & Role Catalog Synchronization for ShikshaSetu.

Provides structured Ministry & Department hierarchy with:
- Department name, code, description
- Department-specific professional roles
- Department & role-specific designations
- Canonical role requirements linked to active competency ObjectIds
"""

from datetime import datetime, UTC
from bson import ObjectId
from pymongo import ReturnDocument
from pymongo.database import Database

from app.core.config import get_settings
from app.core.database import initialize_database, close_database

DEPARTMENT_ROLES_TAXONOMY = [
    {
        "department_name": "Ministry of Education",
        "department_code": "MOE",
        "description": "Department of School Education & Literacy, Higher Education & NCERT",
        "roles": [
            {
                "role_code": "EDUCATION_OFFICER",
                "role_name": "Education & Curriculum Officer",
                "domain": "Academic Standards & Pedagogy",
                "description": "Responsible for curriculum standards, pedagogical assessment, institutional learning quality, and teacher capability building.",
                "designations": [
                    "Teacher",
                    "Senior Teacher (PGT/TGT)",
                    "Headmaster / Principal",
                    "Assistant Professor / Lecturer",
                    "Block Education Officer (BEO)",
                    "District Education Officer (DEO)",
                    "Curriculum & Assessment Specialist",
                    "Education Research Officer",
                ],
                "requirements": [
                    {"code": "BEH_COMMUNICATION", "required_level": 4.0, "priority": 1, "importance": 0.9},
                    {"code": "BEH_LEADERSHIP", "required_level": 3.5, "priority": 2, "importance": 0.8},
                    {"code": "TECH_DATA_VISUALIZATION", "required_level": 3.0, "priority": 3, "importance": 0.7},
                    {"code": "BEH_ETHICS", "required_level": 4.5, "priority": 1, "importance": 0.95},
                    {"code": "STAT_DATA_QUALITY_FRAMEWORKS", "required_level": 3.0, "priority": 3, "importance": 0.75},
                    {"code": "DIGOV_DIGITAL_PUBLIC_INFRASTRUCTURE", "required_level": 3.5, "priority": 2, "importance": 0.8},
                ],
            },
            {
                "role_code": "DIGITAL_LEARNING_SPECIALIST",
                "role_name": "Digital Pedagogy & EdTech Specialist",
                "domain": "Educational Technology & DIKSHA",
                "description": "Designs digital learning frameworks, online assessment systems, and Karmayogi/DIKSHA e-content.",
                "designations": [
                    "Digital Learning Specialist",
                    "EdTech Coordinator",
                    "Smart Classroom Lead",
                    "Online Assessment Officer",
                    "ICT In-charge",
                ],
                "requirements": [
                    {"code": "TECH_AI_ML", "required_level": 3.5, "priority": 2, "importance": 0.85},
                    {"code": "DIGOV_DIGITAL_PUBLIC_INFRASTRUCTURE", "required_level": 4.0, "priority": 1, "importance": 0.9},
                    {"code": "TECH_DATA_VISUALIZATION", "required_level": 3.5, "priority": 2, "importance": 0.8},
                    {"code": "BEH_PROJECT_MANAGEMENT", "required_level": 3.5, "priority": 2, "importance": 0.75},
                    {"code": "BEH_ETHICS", "required_level": 4.0, "priority": 1, "importance": 0.9},
                ],
            },
        ],
    },
    {
        "department_name": "Ministry of Statistics & Programme Implementation (MoSPI)",
        "department_code": "MOSPI",
        "description": "National Statistical Office (NSO), NSSTA & Central Statistics",
        "roles": [
            {
                "role_code": "STATISTICAL_OFFICER",
                "role_name": "Statistical Officer",
                "domain": "Statistical Analysis & Governance",
                "description": "Designs surveys, validates sampling methodology, and analyzes large-scale national datasets.",
                "designations": [
                    "Statistical Officer",
                    "Senior Statistical Officer (SSO)",
                    "Assistant Director (Statistics)",
                    "Deputy Director (Data Management)",
                    "Joint Director (Field Operations)",
                    "Director (Macroeconomic Statistics)",
                ],
                "requirements": [
                    {"code": "STAT_SURVEY_DESIGN", "required_level": 4.0, "priority": 1, "importance": 0.9},
                    {"code": "STAT_SAMPLING", "required_level": 4.0, "priority": 1, "importance": 0.9},
                    {"code": "STAT_DATA_QUALITY_FRAMEWORKS", "required_level": 4.0, "priority": 1, "importance": 0.85},
                    {"code": "TECH_PYTHON", "required_level": 3.5, "priority": 2, "importance": 0.8},
                    {"code": "TECH_DATA_VISUALIZATION", "required_level": 3.5, "priority": 2, "importance": 0.75},
                    {"code": "BEH_ETHICS", "required_level": 4.0, "priority": 2, "importance": 0.8},
                ],
            },
            {
                "role_code": "DATA_ANALYST_OFFICER",
                "role_name": "Survey & Data Analytics Officer",
                "domain": "Computational Statistics & Big Data",
                "description": "Focuses on computational statistics, big data wrangling, and national SDG indicator monitoring.",
                "designations": [
                    "Data Analyst",
                    "Senior Data Analyst",
                    "Lead Statistician",
                    "Survey Informatics Officer",
                ],
                "requirements": [
                    {"code": "TECH_PYTHON", "required_level": 4.0, "priority": 1, "importance": 0.9},
                    {"code": "TECH_SQL", "required_level": 3.5, "priority": 2, "importance": 0.85},
                    {"code": "TECH_DATA_VISUALIZATION", "required_level": 4.0, "priority": 1, "importance": 0.9},
                    {"code": "STAT_SDG_INDICATORS", "required_level": 3.5, "priority": 2, "importance": 0.8},
                    {"code": "BEH_DECISION_MAKING", "required_level": 3.5, "priority": 2, "importance": 0.75},
                ],
            },
        ],
    },
    {
        "department_name": "Ministry of Electronics and Information Technology (MeitY)",
        "department_code": "MEITY",
        "description": "National Informatics Centre (NIC), Digital India & Cyber Governance",
        "roles": [
            {
                "role_code": "DIGITAL_GOVERNANCE_ARCHITECT",
                "role_name": "Digital Governance & e-Gov Architect",
                "domain": "Digital Governance & Architecture",
                "description": "Architects citizen-facing digital public infrastructure and secure government portals.",
                "designations": [
                    "Informatics Officer / Scientist 'B'",
                    "Technical Director (e-Gov)",
                    "IT Systems Officer",
                    "e-Governance Project Lead",
                    "Enterprise Architect",
                ],
                "requirements": [
                    {"code": "DIGOV_DIGITAL_PUBLIC_INFRASTRUCTURE", "required_level": 4.5, "priority": 1, "importance": 0.95},
                    {"code": "DIGOV_CYBERSECURITY", "required_level": 4.0, "priority": 1, "importance": 0.9},
                    {"code": "DIGOV_DATA_PRIVACY", "required_level": 4.0, "priority": 1, "importance": 0.85},
                    {"code": "TECH_APIS", "required_level": 4.0, "priority": 2, "importance": 0.8},
                    {"code": "BEH_PROJECT_MANAGEMENT", "required_level": 3.5, "priority": 2, "importance": 0.75},
                ],
            },
            {
                "role_code": "CYBERSECURITY_GOVERNANCE_OFFICER",
                "role_name": "Cybersecurity & Data Privacy Officer",
                "domain": "Cyber Defense & Compliance",
                "description": "Oversees public sector cyber defense, data protection compliance, and threat mitigation.",
                "designations": [
                    "Cybersecurity Lead",
                    "Information Security Officer (CISO Team)",
                    "Data Protection Officer",
                    "Security Auditor",
                ],
                "requirements": [
                    {"code": "DIGOV_CYBERSECURITY", "required_level": 4.5, "priority": 1, "importance": 0.95},
                    {"code": "DIGOV_DATA_PRIVACY", "required_level": 4.5, "priority": 1, "importance": 0.9},
                    {"code": "DIGOV_DIGITAL_SIGNATURES", "required_level": 4.0, "priority": 2, "importance": 0.85},
                    {"code": "BEH_ETHICS", "required_level": 4.5, "priority": 1, "importance": 0.95},
                ],
            },
        ],
    },
    {
        "department_name": "Department of Personnel and Training (DoPT)",
        "department_code": "DOPT",
        "description": "Ministry of Personnel, Public Grievances and Pensions & Karmayogi Mission",
        "roles": [
            {
                "role_code": "CAPACITY_BUILDING_OFFICER",
                "role_name": "Civil Services Capacity Building Officer",
                "domain": "Civil Services HR & Mission Karmayogi",
                "description": "Coordinates Mission Karmayogi, competency-based HR management, and civil service training frameworks.",
                "designations": [
                    "Under Secretary",
                    "Section Officer (SO)",
                    "Assistant Section Officer (ASO)",
                    "Deputy Secretary",
                    "Director (Training)",
                    "Capacity Building Manager",
                ],
                "requirements": [
                    {"code": "BEH_LEADERSHIP", "required_level": 4.0, "priority": 1, "importance": 0.9},
                    {"code": "BEH_CHANGE_MANAGEMENT", "required_level": 4.0, "priority": 1, "importance": 0.85},
                    {"code": "BEH_COMMUNICATION", "required_level": 4.0, "priority": 2, "importance": 0.8},
                    {"code": "BEH_ETHICS", "required_level": 4.5, "priority": 1, "importance": 0.95},
                    {"code": "DIGOV_DIGITAL_PUBLIC_INFRASTRUCTURE", "required_level": 3.5, "priority": 2, "importance": 0.75},
                ],
            },
        ],
    },
    {
        "department_name": "Ministry of Finance",
        "department_code": "MOF",
        "description": "Department of Expenditure, Economic Affairs & Public Financial Management",
        "roles": [
            {
                "role_code": "PUBLIC_FINANCIAL_MANAGEMENT_OFFICER",
                "role_name": "Financial Management & Audit Officer",
                "domain": "Public Finance & Fiscal Governance",
                "description": "Monitors government budget expenditure, fiscal analytics, and procurement compliance.",
                "designations": [
                    "Accounts Officer (AAO / AO)",
                    "Senior Accounts Officer",
                    "Audit Officer",
                    "Assistant Commissioner (Revenue)",
                    "Financial Analyst",
                ],
                "requirements": [
                    {"code": "STAT_PRICE_STATISTICS", "required_level": 3.5, "priority": 2, "importance": 0.8},
                    {"code": "TECH_SQL", "required_level": 3.5, "priority": 2, "importance": 0.8},
                    {"code": "BEH_ETHICS", "required_level": 4.5, "priority": 1, "importance": 0.95},
                    {"code": "BEH_DECISION_MAKING", "required_level": 4.0, "priority": 1, "importance": 0.85},
                ],
            },
        ],
    },
    {
        "department_name": "Ministry of Health and Family Welfare (MoHFW)",
        "department_code": "MOHFW",
        "description": "National Health Authority, Ayushman Bharat Digital Mission & DGHS",
        "roles": [
            {
                "role_code": "PUBLIC_HEALTH_DATA_OFFICER",
                "role_name": "Public Health & Epidemiological Data Officer",
                "domain": "Public Health Systems & Analytics",
                "description": "Tracks epidemiological datasets, disease surveillance, and digital health mission metrics.",
                "designations": [
                    "Medical Officer (Public Health)",
                    "Health Data Analyst",
                    "District Health Programme Officer",
                    "Surveillance Officer",
                    "Hospital Administrator",
                ],
                "requirements": [
                    {"code": "STAT_SURVEY_DESIGN", "required_level": 3.5, "priority": 2, "importance": 0.8},
                    {"code": "STAT_DATA_QUALITY_FRAMEWORKS", "required_level": 4.0, "priority": 1, "importance": 0.9},
                    {"code": "TECH_DATA_VISUALIZATION", "required_level": 3.5, "priority": 2, "importance": 0.8},
                    {"code": "BEH_ETHICS", "required_level": 4.5, "priority": 1, "importance": 0.95},
                ],
            },
        ],
    },
    {
        "department_name": "Ministry of Rural Development & Panchayati Raj",
        "department_code": "MORD",
        "description": "Department of Rural Development, Panchayati Raj Institutions & NRLM",
        "roles": [
            {
                "role_code": "RURAL_DEVELOPMENT_OFFICER",
                "role_name": "Rural Schemes & Grassroots Governance Officer",
                "domain": "Grassroots Public Service Delivery",
                "description": "Supervises grassroots public service delivery, rural infrastructure schemes, and citizen governance.",
                "designations": [
                    "Block Development Officer (BDO)",
                    "District Project Manager (NRLM/MGNREGS)",
                    "Panchayat Secretary",
                    "Rural Infrastructure Specialist",
                ],
                "requirements": [
                    {"code": "BEH_LEADERSHIP", "required_level": 4.0, "priority": 1, "importance": 0.9},
                    {"code": "BEH_COMMUNICATION", "required_level": 4.0, "priority": 1, "importance": 0.85},
                    {"code": "STAT_SDG_INDICATORS", "required_level": 3.5, "priority": 2, "importance": 0.8},
                    {"code": "BEH_ETHICS", "required_level": 4.5, "priority": 1, "importance": 0.95},
                ],
            },
        ],
    },
]


def sync_department_roles(database: Database) -> dict[str, ObjectId]:
    """
    Synchronizes all department roles, metadata, designations, and role requirements.
    """
    now = datetime.now(UTC)
    role_map: dict[str, ObjectId] = {}

    # Build competency code map
    comp_map: dict[str, ObjectId] = {}
    for comp in database.competencies.find({}, {"_id": 1, "code": 1}):
        comp_map[comp["code"]] = comp["_id"]

    total_roles = 0
    total_requirements = 0

    for dept in DEPARTMENT_ROLES_TAXONOMY:
        dept_name = dept["department_name"]
        dept_code = dept["department_code"]

        for role_spec in dept["roles"]:
            role_code = role_spec["role_code"]
            role_name = role_spec["role_name"]
            description = role_spec["description"]
            designations = role_spec["designations"]
            domain = role_spec.get("domain", "Civil Services Governance")

            role_doc = {
                "role_code": role_code,
                "role_name": role_name,
                "domain": domain,
                "description": description,
                "department": dept_name,
                "department_code": dept_code,
                "designations": designations,
                "status": "active",
                "mapping_status": "PROTOTYPE_CONFIGURED",
                "source": "INTERNAL_PROTOTYPE_V1",
                "source_type": "PROTOTYPE",
                "framework_status": "prototype",
                "updated_at": now,
            }

            res = database.roles.find_one_and_update(
                {"role_code": role_code},
                {"$set": role_doc, "$setOnInsert": {"created_at": now}},
                upsert=True,
                return_document=ReturnDocument.AFTER,
            )
            role_id = res["_id"]
            role_map[role_code] = role_id
            total_roles += 1

            # Sync role requirements
            database.role_requirements.delete_many({"role_id": role_id})
            req_docs = []
            for req in role_spec.get("requirements", []):
                code = req["code"]
                comp_id = comp_map.get(code)
                if not comp_id:
                    # Try with or without DIGOV / GOV prefix
                    alt_code = code.replace("DIGOV_", "GOV_") if "DIGOV_" in code else code.replace("GOV_", "DIGOV_")
                    comp_id = comp_map.get(alt_code)

                if comp_id:
                    req_docs.append({
                        "role_id": role_id,
                        "competency_id": comp_id,
                        "competency_code": code,
                        "required_level": float(req["required_level"]),
                        "priority": int(req["priority"]),
                        "importance": float(req["importance"]),
                        "mapping_status": "PROTOTYPE_CONFIGURED",
                        "source": "INTERNAL_PROTOTYPE_V1",
                        "active": True,
                        "framework_status": "prototype",
                        "created_at": now,
                        "updated_at": now,
                    })


            if req_docs:
                database.role_requirements.insert_many(req_docs)
                total_requirements += len(req_docs)

    print(f"Synced {total_roles} department roles and {total_requirements} role requirements.")
    return role_map


if __name__ == "__main__":
    settings = get_settings()
    client, database = initialize_database(settings.mongodb_uri, settings.mongodb_database)
    sync_department_roles(database)
    close_database(client)
