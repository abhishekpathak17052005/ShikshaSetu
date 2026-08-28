# PHASE 3: IMPLEMENTATION PLAN

**Status:** Ready for development  
**Baseline:** 139/139 tests passing  
**Target:** 159+ tests passing (139 existing + 20 new)  
**Timeline:** 3 weeks  

---

## DATA INTEGRATION STRATEGY

### Source Files (DO NOT MODIFY)

```
✅ igot_courses_enriched.csv         (68 iGOT courses - FINAL)
✅ nssta_training_programmes.csv     (80 NSSTA programmes - FINAL)
✅ course_competency_mapping.csv     (68 iGOT → competency mappings)
✅ nssta_competency_mapping.csv      (46 NSSTA → competency mappings)
✅ competency_taxonomy.csv           (42 competencies + subskills)
✅ source_registry.csv               (provenance tracking)

❌ igot_courses_seed_56.csv          (DO NOT USE - seed for enriched dataset)
❌ igot_courses_dataset.csv          (DO NOT USE - superseded by enriched)
❌ igot_courses_enriched.json        (DO NOT USE - CSV is canonical)
❌ nssta_training_programmes.json    (DO NOT USE - CSV is canonical)
```

### Data Flow

```
Source Files (CSV)
       ↓
   Validation Layer (scripts/seed_*.py)
       ↓
   Normalization (map CSV → MongoDB schema)
       ↓
   MongoDB Collections:
       ├─ competencies (42 records)
       ├─ learning_resources (148 records: 68 iGOT + 80 NSSTA)
       └─ learning_resource_mappings (114 records: 68 iGOT + 46 NSSTA)
       ↓
   Create Indexes
       ↓
   Recommendation Engine Ready
```

---

## PHASE 3 WEEK 1: FOUNDATION

### Task 1: Create Seed Scripts

**Files to Create:**

```
app/scripts/
  ├── seed_competencies.py
  ├── seed_learning_resources.py
  └── seed_resource_mappings.py
```

**script/seed_competencies.py** - Load competency_taxonomy.csv

```python
"""Load competency taxonomy into MongoDB."""

import csv
from datetime import datetime, UTC
from bson import ObjectId
from pymongo.database import Database

async def seed_competencies(database: Database):
    """
    Load competency_taxonomy.csv into competencies collection.
    
    File structure:
      competency_id, competency_name, domain, parent_competency_id, is_subskill,
      description, level_1_definition, ..., level_5_definition, 
      related_skills, related_roles, framework_status
    
    Example:
      STAT-SAMPLING,Sampling,Statistical Competencies,NULL,N,"Ability to...",
      "Aware of...", "Can perform...", ..., "Recognized authority..."
    
    Output MongoDB document:
      {
        "_id": ObjectId,
        "code": "STAT-SAMPLING",
        "name": "Sampling",
        "domain": "Statistical Competencies",
        "parent_competency_code": None,  // For subskills
        "is_subskill": False,
        "description": "Ability to...",
        "level_definitions": {
          "1": "Aware of...",
          "2": "Can perform...",
          ...
          "5": "Recognized authority..."
        },
        "framework_status": "prototype",
        "source": "competency_taxonomy.csv",
        "created_at": datetime,
        "updated_at": datetime
      }
    """
    
    collection = database.competencies
    
    # Drop existing (for fresh seed)
    # collection.drop()
    
    competencies = []
    
    with open("competency_taxonomy.csv", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        
        for row in reader:
            competency = {
                "code": row["competency_id"],
                "name": row["competency_name"],
                "domain": row["domain"],
                "parent_competency_code": row["parent_competency_id"] if row["parent_competency_id"] != "NULL" else None,
                "is_subskill": row["is_subskill"] == "Y",
                "description": row["description"],
                "level_definitions": {
                    "1": row["level_1_definition"],
                    "2": row["level_2_definition"],
                    "3": row["level_3_definition"],
                    "4": row["level_4_definition"],
                    "5": row["level_5_definition"],
                },
                "related_skills": [s.strip() for s in row.get("related_skills", "").split(",") if s.strip()],
                "related_roles": [r.strip() for r in row.get("related_roles", "").split(",") if r.strip()],
                "framework_status": row["framework_status"],  # "prototype"
                "source": "competency_taxonomy.csv",
                "created_at": datetime.now(UTC),
                "updated_at": datetime.now(UTC),
            }
            competencies.append(competency)
    
    if competencies:
        result = collection.insert_many(competencies)
        print(f"✓ Inserted {len(result.inserted_ids)} competencies")
        
        # Create index
        collection.create_index([("code", 1)], unique=True)
        print(f"✓ Created index on competencies.code")
    
    return len(competencies)
```

**script/seed_learning_resources.py** - Load iGOT + NSSTA

```python
"""Load learning resources (iGOT courses + NSSTA programmes) into MongoDB."""

import csv
from datetime import datetime, UTC
from bson import ObjectId
from pymongo.database import Database

async def seed_learning_resources(database: Database):
    """
    Load iGOT and NSSTA resources into learning_resources collection.
    
    Files:
      - igot_courses_enriched.csv
      - nssta_training_programmes.csv
    
    Output schema:
      {
        "_id": ObjectId,
        "resource_id": "IGOT-do_1144751221..." | "NSSTA-PROT-001",
        "provider": "IGOT" | "NSSTA",
        "resource_type": "COURSE" | "TRAINING_PROGRAMME",
        "title": "...",
        "metadata": {
          "duration_hours": 2.7 | 5 | null,
          "difficulty": "BEGINNER" | "INTERMEDIATE" | null,
          "target_roles": [],
          "prerequisites": []
        },
        "competencies": [],  // Populated by seed_resource_mappings
        "source": {
          "source_type": "GOVERNMENT_PUBLICATION" | "PDF",
          "source_url": "https://...",
          "source_document": "SRC-01, SRC-03, etc.",
          "verification_status": "VERIFIED" | "TENTATIVE"
        },
        "provider_specific": {
          // iGOT fields
          "course_id": "do_1144...",
          "course_url": "https://portal.igotkarmayogi...",
          "provider_name": "Kyndryl & Data Security...",
          "extraction_note": "IDs reconstructed from PDF..."
          // OR NSSTA fields
          "programme_id": "NSSTA-PROT-001",
          "training_category": "ISS Probationary Training",
          "batch_size": 28,
          "venue": "ISI, Kolkata",
          "training_year": "FY 2025-2026",
          "schedule": "Wk1-2"
        },
        "status": "ACTIVE",
        "created_at": datetime,
        "updated_at": datetime
      }
    """
    
    collection = database.learning_resources
    resources = []
    
    # Load iGOT courses
    print("Loading iGOT courses...")
    with open("igot_courses_enriched.csv", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        
        for row in reader:
            # Parse duration (e.g., "2h 42m" → 2.7 hours)
            duration_hours = None
            if row.get("duration"):
                # Simple parsing: assume format like "2h 42m"
                parts = row["duration"].split()
                hours = 0
                for i, part in enumerate(parts):
                    if "h" in part:
                        hours += int(part.rstrip("h"))
                    elif "m" in part:
                        hours += int(part.rstrip("m")) / 60
                duration_hours = round(hours, 2) if hours else None
            
            resource = {
                "resource_id": f"IGOT-{row['course_id']}",
                "provider": "IGOT",
                "resource_type": "COURSE",
                "title": row["course_title"],
                "metadata": {
                    "duration_hours": duration_hours,
                    "difficulty": row.get("difficulty_level") or None,
                    "target_roles": [],
                    "prerequisites": []
                },
                "competencies": [],  # Linked by seed_resource_mappings
                "source": {
                    "source_type": "GOVERNMENT_PUBLICATION",
                    "source_url": row.get("course_url") or row.get("source_url"),
                    "source_document": "SRC-01 (seed) or SRC-02 (discovered)",
                    "verification_status": "VERIFIED"
                },
                "provider_specific": {
                    "course_id": row["course_id"],
                    "course_url": row.get("course_url") or row.get("source_url"),
                    "provider_name": row.get("provider") or row.get("author_creator"),
                    "extraction_note": row.get("extraction_note")
                },
                "status": "ACTIVE",
                "created_at": datetime.now(UTC),
                "updated_at": datetime.now(UTC)
            }
            resources.append(resource)
    
    # Load NSSTA programmes
    print("Loading NSSTA programmes...")
    with open("nssta_training_programmes.csv", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        
        for row in reader:
            # Parse duration (e.g., "5 day(s)" → 5*8 = 40 hours)
            duration_hours = None
            if row.get("duration"):
                parts = row["duration"].split()
                if parts[0].isdigit():
                    days = int(parts[0])
                    duration_hours = days * 8  # Assume 8-hour day
            
            resource = {
                "resource_id": f"NSSTA-{row['programme_id']}",
                "provider": "NSSTA",
                "resource_type": "TRAINING_PROGRAMME",
                "title": row["programme_name"],
                "metadata": {
                    "duration_hours": duration_hours,
                    "difficulty": None,  # NSSTA doesn't specify
                    "target_roles": [],
                    "prerequisites": []
                },
                "competencies": [],  # Linked by seed_resource_mappings
                "source": {
                    "source_type": "GOVERNMENT_PUBLICATION",
                    "source_url": row.get("source_url"),
                    "source_document": "SRC-03 (FY 2025-26 Advance Training Calendar)",
                    "verification_status": "TENTATIVE"  # Calendar marked tentative
                },
                "provider_specific": {
                    "programme_id": row["programme_id"],
                    "training_category": row.get("training_category"),
                    "batch_size": int(row.get("batch_size", 0)) if row.get("batch_size", "").isdigit() else None,
                    "venue": row.get("venue"),
                    "institute": row.get("institute"),
                    "training_year": row.get("training_year"),
                    "schedule": row.get("schedule"),
                    "recommended_by_TPAC": row.get("recommended_by_TPAC") == "Y"
                },
                "status": "ACTIVE",
                "created_at": datetime.now(UTC),
                "updated_at": datetime.now(UTC)
            }
            resources.append(resource)
    
    if resources:
        result = collection.insert_many(resources)
        print(f"✓ Inserted {len(result.inserted_ids)} learning resources")
        
        # Create indexes
        collection.create_index([("provider", 1)])
        collection.create_index([("status", 1)])
        print(f"✓ Created indexes on learning_resources")
    
    return len(resources)
```

**script/seed_resource_mappings.py** - Link resources to competencies

```python
"""Load resource-to-competency mappings."""

import csv
from datetime import datetime, UTC
from bson import ObjectId
from pymongo.database import Database

async def seed_resource_mappings(database: Database):
    """
    Load iGOT and NSSTA competency mappings into learning_resource_mappings.
    
    Files:
      - course_competency_mapping.csv
      - nssta_competency_mapping.csv
    
    Output schema:
      {
        "_id": ObjectId,
        "resource_id": ObjectId,  // FK to learning_resources
        "competency_id": ObjectId,
        "competency_code": "TECH-AIML",
        "provider": "IGOT" | "NSSTA",
        "mapping_quality": {
          "content_alignment": 0.5,
          "accuracy_score": null,
          "recency_score": null
        },
        "mapping_type": "DERIVED",
        "confidence": 0.5 | 0.55,
        "evidence": "Course title keyword matching",
        "verified_at": null,
        "verified_by": null,
        "created_at": datetime
      }
    """
    
    mapping_collection = database.learning_resource_mappings
    resource_collection = database.learning_resources
    competency_collection = database.competencies
    
    # Build lookup maps
    resources_by_id = {}
    for resource in resource_collection.find():
        resources_by_id[resource["resource_id"]] = resource
    
    competencies_by_code = {}
    for comp in competency_collection.find():
        competencies_by_code[comp["code"]] = comp
    
    mappings = []
    
    # Load iGOT mappings
    print("Loading iGOT mappings...")
    with open("course_competency_mapping.csv", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        
        for row in reader:
            course_id = row["course_id"]
            competency_code = row["competency_id"]
            
            # Find resource
            resource = None
            for r in resource_collection.find({"provider_specific.course_id": course_id}):
                resource = r
                break
            
            if not resource:
                print(f"  ⚠️  iGOT course {course_id} not found in learning_resources")
                continue
            
            # Find competency
            competency = competencies_by_code.get(competency_code)
            if not competency:
                print(f"  ⚠️  Competency {competency_code} not found")
                continue
            
            mapping = {
                "resource_id": resource["_id"],
                "competency_id": competency["_id"],
                "competency_code": competency_code,
                "provider": "IGOT",
                "mapping_quality": {
                    "content_alignment": float(row.get("confidence", 0.5)),
                    "accuracy_score": None,
                    "recency_score": None
                },
                "mapping_type": row.get("mapping_type", "DERIVED"),
                "confidence": float(row.get("confidence", 0.5)),
                "evidence": row.get("evidence", ""),
                "verified_at": None,
                "verified_by": None,
                "created_at": datetime.now(UTC)
            }
            mappings.append(mapping)
    
    # Load NSSTA mappings
    print("Loading NSSTA mappings...")
    with open("nssta_competency_mapping.csv", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        
        for row in reader:
            programme_id = row["programme_id"]
            competency_code = row["competency_id"]
            
            # Find resource
            resource = None
            for r in resource_collection.find({"provider_specific.programme_id": programme_id}):
                resource = r
                break
            
            if not resource:
                print(f"  ⚠️  NSSTA programme {programme_id} not found in learning_resources")
                continue
            
            # Find competency
            competency = competencies_by_code.get(competency_code)
            if not competency:
                print(f"  ⚠️  Competency {competency_code} not found")
                continue
            
            mapping = {
                "resource_id": resource["_id"],
                "competency_id": competency["_id"],
                "competency_code": competency_code,
                "provider": "NSSTA",
                "mapping_quality": {
                    "content_alignment": float(row.get("confidence", 0.55)),
                    "accuracy_score": None,
                    "recency_score": None
                },
                "mapping_type": row.get("mapping_type", "DERIVED"),
                "confidence": float(row.get("confidence", 0.55)),
                "evidence": row.get("evidence", ""),
                "verified_at": None,
                "verified_by": None,
                "created_at": datetime.now(UTC)
            }
            mappings.append(mapping)
    
    if mappings:
        result = mapping_collection.insert_many(mappings)
        print(f"✓ Inserted {len(result.inserted_ids)} resource-competency mappings")
        
        # Create indexes
        mapping_collection.create_index([("resource_id", 1)])
        mapping_collection.create_index([("competency_id", 1)])
        mapping_collection.create_index([("competency_code", 1)])
        mapping_collection.create_index([("provider", 1)])
        print(f"✓ Created indexes on learning_resource_mappings")
    
    return len(mappings)
```

### Task 2: Create Collection Schemas

**Files to Create:**

```
app/learning_resources/
  ├── __init__.py
  ├── models.py          (Pydantic schemas)
  └── repository.py      (CRUD operations)
```

**Models to Define:**

```python
# learning_resources/models.py

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field

class CompetencyReference(BaseModel):
    competency_code: str
    competency_id: str
    coverage_level: Optional[str] = None  # FOUNDATIONAL, INTERMEDIATE, ADVANCED
    weight: Optional[float] = None

class ResourceMetadata(BaseModel):
    duration_hours: Optional[int] = None
    difficulty: Optional[str] = None
    target_roles: List[str] = Field(default_factory=list)
    prerequisites: List[str] = Field(default_factory=list)

class ResourceSource(BaseModel):
    source_type: str
    source_url: Optional[str] = None
    source_document: Optional[str] = None
    verification_status: str
    extraction_note: Optional[str] = None

class LearningResource(BaseModel):
    resource_id: str
    provider: str  # IGOT, NSSTA
    resource_type: str  # COURSE, TRAINING_PROGRAMME
    title: str
    metadata: ResourceMetadata
    competencies: List[CompetencyReference] = Field(default_factory=list)
    source: ResourceSource
    provider_specific: dict
    status: str = "ACTIVE"
    created_at: datetime
    updated_at: datetime

class LearningResourceMapping(BaseModel):
    resource_id: str
    competency_id: str
    competency_code: str
    provider: str
    mapping_quality: dict  # { content_alignment, accuracy_score, recency_score }
    mapping_type: str  # DERIVED
    confidence: float
    evidence: str
    verified_at: Optional[datetime] = None
    verified_by: Optional[str] = None
    created_at: datetime
```

### Task 3: Create Repository Layer

```python
# learning_resources/repository.py

async def get_resources_by_competency(
    database, 
    competency_code: str, 
    provider: Optional[str] = None
) -> List[dict]:
    """Find learning resources for a competency."""
    
    query = {"competencies.competency_code": competency_code}
    if provider:
        query["provider"] = provider
    
    return list(database.learning_resource_mappings.aggregate([
        {"$match": query},
        {"$lookup": {
            "from": "learning_resources",
            "localField": "resource_id",
            "foreignField": "_id",
            "as": "resource"
        }},
        {"$unwind": "$resource"}
    ]))

async def get_resource_details(database, resource_id: str) -> Optional[dict]:
    """Get full resource metadata."""
    return database.learning_resources.find_one({"resource_id": resource_id})
```

### Week 1 Deliverables

- ✅ Seed scripts created and validated
- ✅ Schemas defined
- ✅ Repository CRUD written
- ✅ 148 resources loaded (68 iGOT + 80 NSSTA)
- ✅ 114 mappings created
- ✅ 42 competencies verified
- ✅ All indexes created
- ✅ Verified 139 existing tests still pass

---

## PHASE 3 WEEK 2: ENGINE & API

(Details same as previous implementation plan)

---

## PHASE 3 WEEK 3: TESTS & VERIFICATION

(Details same as previous implementation plan)

---

## MONGODB INDEXES

Create after seeding:

```python
# learning_resources
db.learning_resources.create_index([("provider", ASCENDING)])
db.learning_resources.create_index([("status", ASCENDING)])
db.learning_resources.create_index([("resource_id", ASCENDING)], unique=True)

# learning_resource_mappings
db.learning_resource_mappings.create_index([("resource_id", ASCENDING)])
db.learning_resource_mappings.create_index([("competency_code", ASCENDING)])
db.learning_resource_mappings.create_index([("provider", ASCENDING)])
db.learning_resource_mappings.create_index([
    ("resource_id", ASCENDING), 
    ("competency_code", ASCENDING)
], unique=True)
```

---

## FINAL DATA NUMBERS

After seeding:

| Collection | Count | Source |
|---|---|---|
| competencies | 42 | competency_taxonomy.csv |
| learning_resources | 148 | igot_courses_enriched.csv (68) + nssta_training_programmes.csv (80) |
| learning_resource_mappings | 114 | course_competency_mapping.csv (68) + nssta_competency_mapping.csv (46) |

---

## KEY RULES

✅ **DO:**
- Use CSV files as canonical source
- Build seed scripts around CSVs
- Preserve all provenance fields
- Mark NSSTA as TENTATIVE
- Keep iGOT extraction_note flags
- Create indexes for performance

❌ **DON'T:**
- Modify CSV files
- Mix enriched + seed datasets
- Load both CSV and JSON formats
- Invent missing fields
- Fabricate descriptions/prerequisites
- Claim live availability

---

## SUCCESS CRITERIA (Week 1)

- ✅ 148 learning_resources documents in MongoDB
- ✅ 114 learning_resource_mappings documents
- ✅ All 42 competencies verified
- ✅ All indexes created
- ✅ Resources queryable by competency_code
- ✅ Seed scripts reusable for future updates
- ✅ 139 existing tests still passing

