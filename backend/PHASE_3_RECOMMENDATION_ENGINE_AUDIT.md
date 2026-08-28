# PHASE 3: RECOMMENDATION ENGINE FOUNDATION — ARCHITECTURE AUDIT

**Date:** August 27, 2026  
**Status:** AUDIT COMPLETE - Architecture recommendations ready  
**Baseline:** 139/139 tests passing  

---

## EXECUTIVE SUMMARY

The backend has strong competency and skill-gap foundations. To build the Personalized Learning Recommendation Engine, we need:

1. **Unified learning resource abstraction** (iGOT + NSSTA)
2. **Competency-to-resource mapping collection**
3. **Deterministic recommendation scoring** (built on top of existing skill-gap priority scores)
4. **Provider architecture** (prototype + live)
5. **Recommendation API endpoints**

All existing systems (competency, skill gap, assessment, evidence, quiz engine) remain untouched.

---

## 1. ANSWER TO KEY QUESTIONS

### Q1: How do we retrieve a user's current competencies?

**Files:** `app/skill_gaps/repository.py`, `app/competencies/repository.py`

```python
# Via competency_profiles collection
profiles = database.competency_profiles.find({
    "user_id": ObjectId(user_id),
    "competency_id": {"$in": competency_object_ids},
})

# Returns:
# - competency_id
# - current_level (1-5)
# - confidence (0-1)
# - last_assessed_at (datetime)
```

**Status:** ✅ **AVAILABLE**

---

### Q2: How do we retrieve role-required competencies?

**Files:** `app/skill_gaps/repository.py`, `app/skill_gaps/engine.py`

```python
# Via role_requirements collection (enriched with competency details)
requirements = database.role_requirements.find({
    "role_id": ObjectId(role_id)
})

# Enriched with:
# - competency_id, competency_code, competency_name, domain
# - required_level (1-5)
# - priority (1-4, where 1 = highest)
# - importance (0-1)
```

**Status:** ✅ **AVAILABLE**

---

### Q3: How do we retrieve skill gaps?

**Files:** `app/skill_gaps/service.py`, `app/skill_gaps/engine.py`

```python
# Function: calculate_skill_gaps(database, user_id)
# Returns SkillGapResponse with:
# - role: {id, code, name}
# - summary: {total_gaps, critical_gaps, high_gaps, medium_gaps, low_gaps, ...}
# - gaps: [{competency_id, competency_code, gap, gap_category, priority_score, ...}]

# Gaps already SORTED by priority (highest first)
```

**Status:** ✅ **AVAILABLE** — Already sorted by priority

---

### Q4: What fields are available for each gap?

**File:** `app/skill_gaps/schemas.py`

```python
class SkillGapCompetency(BaseModel):
    competency_id: str
    competency_code: str
    competency_name: str
    domain: str
    required_level: float          # 1-5
    current_level: float | None    # 1-5 or None (not assessed)
    gap: float                     # Required - Current (0-4)
    gap_category: str              # NO_GAP, LOW, MEDIUM, HIGH, CRITICAL
    assessment_status: str         # ASSESSED, NOT_ASSESSED
    confidence: float              # 0-1 (assessment confidence)
    priority: int                  # 1-4 (role priority)
    importance: float              # 0-1 (role importance)
    priority_score: float          # 0-1 (calculated ranking)
    last_assessed_at: datetime | None
```

**Status:** ✅ **AVAILABLE** — Rich data for recommendations

---

### Q5: How are competencies linked to learning resources?

**Files:** `app/ai/models.py`, `app/quizzes/schemas.py`

**Current State:**

```
Competency
    ↓ (via competency_code in quiz)
Quiz
    ↓ (via material_id)
LearningMaterial (document chunks with embeddings)
```

**Problem:** LOOSE coupling. No explicit mapping collection exists.

**Mapping Routes:**
- Quiz → Material: via `material_id` in quiz
- Quiz → Competency: via `competency_code` in quiz
- Material → Competency: only through quizzes (indirect)

**Status:** ⚠️ **PARTIAL** — Needs formal mapping collection

---

### Q6: Does an existing iGOT course model exist?

**Files:** Searched entire codebase

**Result:** ❌ **NO** — No iGOT model, schema, or API integration found.

**What exists:**
- LearningMaterial (user-uploaded documents)
- Quiz (generated from materials)
- No official iGOT data structure

---

### Q7: Does an existing NSSTA programme model exist?

**Files:** Searched entire codebase

**Result:** ❌ **NO** — No NSSTA model, schema, or API integration found.

**What exists:**
- No TPAC/NSSTA data structures
- No government training programme references

---

### Q8: Are course/programme competency mappings already present?

**Files:** Searched entire codebase

**Result:** ❌ **NO FORMAL MAPPING COLLECTION** 

**Implicit mappings:**
- Quiz has `competency_code` (links quiz to competency)
- Material is chunked and embedded (can be searched by competency via semantic search)
- No structured resource-competency join table

**Status:** ⚠️ **NEEDS DESIGN** — Recommend new collection

---

### Q9: What data is missing for recommendation ranking?

**Gap Analysis:**

| Data Element | Current | Needed |
|--------------|---------|--------|
| User competency levels | ✅ | ✅ |
| Role requirements | ✅ | ✅ |
| Skill gaps | ✅ | ✅ |
| Gap prioritization | ✅ | ✅ |
| **Learning resources** | ⚠️ Partial | ❌ NEEDED |
| **Resource competency mapping** | ❌ | ❌ NEEDED |
| **Resource metadata** (duration, difficulty, provider) | ⚠️ Partial | ❌ NEEDED |
| **Resource ranking factors** | ❌ | ❌ NEEDED |
| **User learning history** (resources completed) | ⚠️ Partial | ❌ NEEDED |
| **Prerequisite tracking** | ❌ | ❌ NEEDED |
| **Resource availability** (iGOT seat availability, NSSTA enrollment) | ❌ | ❌ NEEDED |

---

## 2. CURRENT MONGODB COLLECTIONS

### Existing Collections (Verified)

| Collection | Purpose | Indexed Fields | Status |
|-----------|---------|-----------------|--------|
| `users` | User profiles | email, employee_id, role_id | ✅ |
| `roles` | Role definitions | role_code | ✅ |
| `role_requirements` | Competency requirements per role | (role_id, competency_id) | ✅ |
| `competencies` | Competency framework | code | ✅ |
| `competency_profiles` | User competency levels | (user_id, competency_id) | ✅ |
| `competency_evidence` | Assessment results | (user_id, competency_id) | ✅ |
| `assessments` | Assessment templates | assessment_key | ✅ |
| `assessment_attempts` | User assessment attempts | (user_id, assessment_id) | ✅ |
| `question_bank` | Quiz questions | (competency_code, question_type) | ✅ |
| `capability_assessments` | Capability assessment instances | (user_id, competency_code) | ✅ |
| `quizzes` | Quiz definitions | material_id | ✅ |
| `quiz_attempts` | User quiz attempts | (user_id, quiz_id) | ✅ |
| `learning_materials` | Uploaded documents | - | ✅ |
| `document_chunks` | Material chunks | material_id | ✅ |

---

## 3. ARCHITECTURE: LEARNING RESOURCE ABSTRACTION

### Design Decision

**Unified Resource Model** to support both iGOT and NSSTA.

### Proposed Collection: `learning_resources`

```json
{
  "_id": ObjectId,
  "resource_id": "IGOT-COURSE-12345" | "NSSTA-TPAC-2024-SQL",
  "provider": "IGOT" | "NSSTA",
  "resource_type": "COURSE" | "TRAINING_PROGRAMME" | "SELF_PACED_MODULE",
  
  "metadata": {
    "title": "SQL Fundamentals for Data Analysis",
    "description": "Comprehensive introduction to SQL...",
    "duration_hours": 12,
    "difficulty": "BEGINNER" | "INTERMEDIATE" | "ADVANCED",
    "target_roles": ["DATA_ANALYST", "STATISTICAL_OFFICER"],
    "prerequisites": ["TECH_BASIC_COMPUTER", "TECH_SPREADSHEET"],
    "language": "EN",
    "status": "ACTIVE" | "ARCHIVED" | "BETA"
  },
  
  "competencies": [
    {
      "competency_code": "TECH_SQL",
      "competency_id": ObjectId,
      "coverage_level": "FOUNDATIONAL" | "INTERMEDIATE" | "ADVANCED",
      "weight": 0.8,  // Primary competency (80% of course)
    },
    {
      "competency_code": "TECH_DATABASES",
      "competency_id": ObjectId,
      "coverage_level": "FOUNDATIONAL",
      "weight": 0.2,   // Secondary competency
    }
  ],
  
  "provider_specific": {
    // Provider-specific fields
    // iGOT: {course_id, track_id, batch_info, availability, seats_available, ...}
    // NSSTA: {programme_id, training_year, mopspi_ref, state_approved, max_participants, ...}
  },
  
  "source": {
    "source_type": "OFFICIAL_API" | "MANUAL_ENTRY" | "GOVERNMENT_PUBLICATION",
    "source_url": "https://api.igot.gov.in/courses/12345",
    "source_document": "NSSTA_Directory_2024.pdf",
    "import_timestamp": datetime,
    "last_verified_at": datetime,
    "verification_status": "VERIFIED" | "PENDING" | "OUTDATED",
  },
  
  "engagement": {
    "enrollment_count": 123,
    "completion_rate": 0.75,
    "average_rating": 4.2,
    "user_reviews_count": 45,
  },
  
  "created_at": datetime,
  "updated_at": datetime,
  "status": "ACTIVE" | "INACTIVE" | "ARCHIVED",
}
```

### Proposed Collection: `learning_resource_mappings`

**Purpose:** Explicitly link resources to competencies with ranking factors.

```json
{
  "_id": ObjectId,
  "resource_id": ObjectId,  // Reference to learning_resources
  "competency_id": ObjectId,
  "competency_code": "TECH_SQL",
  
  "mapping_quality": {
    "content_alignment": 0.95,      // How well does resource cover this competency (0-1)
    "accuracy_score": 0.90,         // Verification of accuracy
    "recency_score": 0.85,          // How current is the content (0-1)
    "effectiveness_score": 0.88,    // Learning effectiveness score (0-1)
  },
  
  "ranking_factors": {
    "difficulty_match": 0.0,        // Will be filled in at recommendation time
    "role_relevance": 0.0,
    "prerequisite_coverage": 0.0,
    "learning_path_position": 0,    // Position in recommended learning path
  },
  
  "created_at": datetime,
  "verified_at": datetime,
}
```

### Proposed Collection: `user_learning_history`

**Purpose:** Track user engagement with resources.

```json
{
  "_id": ObjectId,
  "user_id": ObjectId,
  "resource_id": ObjectId,
  "competency_id": ObjectId,
  
  "interaction_type": "ENROLLED" | "STARTED" | "COMPLETED" | "ABANDONED" | "BOOKMARKED",
  "progress": 0.75,                // 0-1
  "time_spent_hours": 8.5,
  "completion_date": datetime | null,
  "rating": 4,                     // 1-5 stars
  "feedback": "Very helpful course...",
  
  "first_engagement": datetime,
  "last_engagement": datetime,
  "engagement_count": 12,          // How many times accessed
}
```

### Related Updates to Existing Collections

**Enhance `competency_evidence`:**
```python
# Add optional field for learning resource reference:
"resource_id": ObjectId,  # If evidence came from a learning resource
"resource_provider": "IGOT" | "NSSTA" | null,
```

---

## 4. RECOMMENDATION INPUT SPECIFICATION

### API Endpoint

```
GET /api/v1/recommendations/me
GET /api/v1/recommendations?role_id={role_id}&user_id={user_id}
```

### Internal Input Structure

```python
class RecommendationInput:
    """Input to recommendation engine"""
    user_id: str
    role_id: str
    skill_gaps: List[SkillGapCompetency]  # From /skill-gaps endpoint (already sorted)
    user_competency_profiles: Dict[str, CompetencyProfile]
    user_learning_history: List[UserLearningHistory]
    
    # Optional filters
    preferred_provider: "IGOT" | "NSSTA" | "ANY" = "ANY"
    max_recommendations: int = 5
    target_gap_categories: List[str] = ["CRITICAL", "HIGH"]  # Default to urgent gaps
```

### Context Example

```python
# For demo user (Statistical Officer):

skill_gaps = [
    {
        "competency_id": "...",
        "competency_code": "STAT_SAMPLING",
        "current_level": 2.55,
        "required_level": 4.0,
        "gap": 1.45,
        "gap_category": "HIGH",
        "priority_score": 0.75,
        "importance": 1.0,
    },
    {
        "competency_id": "...",
        "competency_code": "TECH_SQL",
        "current_level": 1.8,
        "required_level": 3.5,
        "gap": 1.7,
        "gap_category": "HIGH",
        "priority_score": 0.70,
        "importance": 0.8,
    },
    # ... other gaps
]

# Recommendation engine should ask:
# "What resources best address STAT_SAMPLING and TECH_SQL gaps?"
```

---

## 5. CANDIDATE GENERATION STRATEGY

### Algorithm: Competency-Driven Resource Search

**For each high-priority skill gap:**

```
1. Get competency_code from gap (e.g., "STAT_SAMPLING")
2. Query learning_resources collection:
   - Filter by competencies.competency_code = "STAT_SAMPLING"
   - Filter by resource.status = "ACTIVE"
   - Filter by provider = user_preferred_provider (or ALL)
3. Join with learning_resource_mappings to get alignment scores
4. Sort by mapping quality (content_alignment, accuracy_score)
5. Fetch top N candidates (e.g., top 10)
6. Return candidates with metadata
```

### SQL-like Pseudocode

```sql
SELECT 
    r.*, 
    m.mapping_quality,
    COUNT(DISTINCT h.user_id) as engagement_count
FROM learning_resources r
LEFT JOIN learning_resource_mappings m 
    ON r._id = m.resource_id
LEFT JOIN user_learning_history h 
    ON r._id = h.resource_id
WHERE 
    r.competencies.competency_code = ?  -- Gap competency
    AND r.status = 'ACTIVE'
    AND r.provider IN (?, ?, ...)        -- User preferred providers
GROUP BY r._id
ORDER BY 
    m.mapping_quality.content_alignment DESC,
    m.mapping_quality.accuracy_score DESC,
    r.engagement.completion_rate DESC
LIMIT 10;
```

### Why Structured Search First

- ✅ Deterministic and auditable
- ✅ Uses existing MongoDB indexes
- ✅ Fast query performance
- ✅ No LLM dependency (but can add semantic search as Phase 3.5)

### Later Enhancement: Semantic Search

Phase 3.5 can add:
```
UNION
SELECT ... FROM learning_resources r
WHERE COSINE(r.embedding, gap_competency_embedding) > 0.85
```

---

## 6. RECOMMENDATION SCORING FORMULA

### Design Principles

- **Deterministic:** Same input always produces same score
- **Explainable:** Each component contributes transparently
- **Weighted:** Combine multiple ranking factors
- **Normalized:** 0.0-1.0 scale for easier interpretation

### Proposed Scoring Model

```
RECOMMENDATION_SCORE = 
    (competency_match × 0.35) +           // How well does resource cover the gap?
    (gap_priority × 0.25) +               // How urgent is this gap?
    (difficulty_match × 0.15) +           // Is difficulty appropriate for current level?
    (role_match × 0.15) +                 // Is this resource recommended for user's role?
    (prerequisite_coverage × 0.05) +      // Are prerequisites satisfied?
    (engagement_quality × 0.05)           // How well do other similar users rate it?

RESULT: Score 0.0-1.0 (higher = better recommendation)
```

### Component Definitions

#### 1. Competency Match (0.35 weight)

```python
competency_match = mapping_quality.content_alignment * mapping_quality.accuracy_score
# Range: 0.0-1.0
# Example: 0.95 * 0.90 = 0.855
```

#### 2. Gap Priority (0.25 weight)

```python
gap_priority = skill_gap.priority_score
# Already calculated by skill_gap engine
# Range: 0.0-1.0 (from weighted formula: 60% gap, 25% importance, 15% priority)
# Example: 0.75 (high priority gap)
```

#### 3. Difficulty Match (0.15 weight)

```python
# If resource difficulty == user current level ± 1 level: 1.0
# If resource difficulty == user current level ± 2 levels: 0.7
# If resource difficulty > user current level + 2: 0.3
# If resource difficulty < user current level - 1: 0.5

current_level = user_competency_profile[competency].current_level  # 1-5
resource_difficulty_level = {
    "BEGINNER": 1.5,
    "FOUNDATIONAL": 2.0,
    "INTERMEDIATE": 3.0,
    "ADVANCED": 4.0,
    "EXPERT": 5.0,
}

difficulty_diff = abs(current_level - resource_difficulty_level)

if difficulty_diff <= 1:
    difficulty_match = 1.0
elif difficulty_diff <= 2:
    difficulty_match = 0.7
elif difficulty_diff <= 3:
    difficulty_match = 0.4
else:
    difficulty_match = 0.1
```

#### 4. Role Match (0.15 weight)

```python
# Is this resource recommended for the user's role?

resource_target_roles = learning_resource.metadata.target_roles
user_role = user.role_code

if user_role in resource_target_roles:
    role_match = 1.0
else:
    # Check if role is similar to target roles (semantic)
    # For now: boolean check
    role_match = 0.5
```

#### 5. Prerequisite Coverage (0.05 weight)

```python
# How many prerequisites does user already have?

resource_prerequisites = learning_resource.metadata.prerequisites  # [comp_code, ...]
user_competencies = {comp.code: comp.level for comp in user_profiles}

satisfied = 0
for prereq_code in resource_prerequisites:
    if user_competencies.get(prereq_code, 0) >= 2.0:
        satisfied += 1

prerequisite_coverage = satisfied / len(resource_prerequisites) if prerequisites else 1.0
# Range: 0.0-1.0
```

#### 6. Engagement Quality (0.05 weight)

```python
# How well do other users rate this resource?

engagement_quality = (
    (resource.engagement.completion_rate * 0.5) +           # 50% completion rate
    (resource.engagement.average_rating / 5.0 * 0.3) +      # 30% user rating
    (min(resource.engagement.enrollment_count / 1000, 1.0) * 0.2)  # 20% popularity
)
# Range: 0.0-1.0
```

### Example Calculation

```
Resource: "SQL Fundamentals for Data Analysis" (IGOT Course)
Gap: TECH_SQL (current 1.8, required 3.5, gap 1.7, priority 0.70)
User: Statistical Officer with current level 1.8

competency_match = 0.95 × 0.90 = 0.855
gap_priority = 0.70
difficulty_match = 1.0 (BEGINNER resource for user at level 1.8)
role_match = 1.0 (SQL is target role skill)
prerequisite_coverage = 1.0 (no prerequisites)
engagement_quality = (0.75 × 0.5) + (4.2/5.0 × 0.3) + (0.45 × 0.2) = 0.375 + 0.252 + 0.090 = 0.717

RECOMMENDATION_SCORE = 
    (0.855 × 0.35) +
    (0.70 × 0.25) +
    (1.0 × 0.15) +
    (1.0 × 0.15) +
    (1.0 × 0.05) +
    (0.717 × 0.05)

= 0.299 + 0.175 + 0.150 + 0.150 + 0.050 + 0.036
= 0.860

RESULT: 0.860/1.0 (highly recommended)
```

---

## 7. EXPLANATION MECHANISM

### Recommendation Response Structure

```json
{
  "recommendation_id": "REC-20260827-001",
  "user_id": "...",
  "created_at": "2026-08-27T10:30:00Z",
  
  "recommendations": [
    {
      "rank": 1,
      "resource": {
        "resource_id": "IGOT-COURSE-12345",
        "provider": "IGOT",
        "title": "SQL Fundamentals for Data Analysis",
        "description": "...",
        "duration_hours": 12,
        "difficulty": "BEGINNER",
        "url": "https://igot.gov.in/courses/..."
      },
      
      "gap_addressed": {
        "competency_code": "TECH_SQL",
        "competency_name": "SQL Database Querying",
        "current_level": 1.8,
        "required_level": 3.5,
        "gap": 1.7,
        "gap_category": "HIGH",
        "priority_score": 0.70
      },
      
      "score": {
        "overall_score": 0.860,
        "components": {
          "competency_match": 0.855,
          "gap_priority": 0.70,
          "difficulty_match": 1.0,
          "role_match": 1.0,
          "prerequisite_coverage": 1.0,
          "engagement_quality": 0.717
        }
      },
      
      "explanation": {
        "summary": "This resource directly addresses your high-priority SQL gap and is appropriate for your current skill level.",
        "details": [
          "✅ Resource covers SQL at BEGINNER level (you're at 1.8/5, resource targets 1-2)",
          "✅ SQL is required for your Statistical Officer role",
          "✅ Content alignment verified: 95% match on SQL concepts",
          "✅ 12-hour course fits typical learning path",
          "⚠️ User completion rate: 75% (good engagement)"
        ],
        "next_steps": [
          "1. Enroll in this course",
          "2. Complete within 2 weeks",
          "3. After completion, take TECH_SQL assessment to verify competency gain"
        ]
      },
      
      "similar_alternatives": [
        {
          "rank": "1a",
          "title": "SQL for Statistical Analysis (NSSTA TPAC)",
          "provider": "NSSTA",
          "score": 0.845,
          "reason": "Similar content, NSSTA provider, slightly lower recency"
        }
      ]
    },
    
    {
      "rank": 2,
      "resource": { ... },
      ...
    }
  ],
  
  "summary": {
    "total_gaps": 8,
    "recommendations_generated": 5,
    "critical_gaps_addressed": 1,
    "high_gaps_addressed": 2,
    "estimated_learning_path_duration_hours": 45,
    "next_assessment_date": "2026-09-27"
  }
}
```

### Explanation Template (Can Use LLM Later)

For now: **Static templates** + **component scores**

```
TEMPLATE:
"This resource addresses your {gap_category} {competency_name} gap (current {current_level}/5, required {required_level}/5). 
The course difficulty ({resource_difficulty}) matches your current level, and covers {competency_match}% of the required concepts. 
{engagement_callout}. After completion, your gap is estimated to reduce to {estimated_gap}."

VARIABLES (deterministic):
- gap_category: HIGH, CRITICAL, MEDIUM (from skill gap)
- competency_name: SQL Database Querying
- current_level, required_level: from profile
- resource_difficulty: BEGINNER, INTERMEDIATE, ADVANCED
- competency_match: 95% (from mapping)
- engagement_callout: Generated from engagement_quality
- estimated_gap: Calculated using learning outcome model (Phase 3.5)
```

**LLM Enhancement (Phase 3.5):** Use Claude/Gemini to generate natural language explanation from structured scores.

---

## 8. PROVIDER ARCHITECTURE

### Abstraction Layer

```python
# Abstract base
class LearningResourceProvider(ABC):
    """Abstract provider for learning resources."""
    
    @abstractmethod
    async def search_by_competency(
        self, 
        competency_code: str,
        filters: Dict
    ) -> List[LearningResource]:
        """Find resources covering competency."""
        pass
    
    @abstractmethod
    async def get_resource_details(
        self, 
        resource_id: str
    ) -> LearningResource:
        """Get full resource metadata."""
        pass
    
    @abstractmethod
    async def check_availability(
        self, 
        resource_id: str
    ) -> AvailabilityStatus:
        """Check if resource is available (seats, enrollment open)."""
        pass
    
    @abstractmethod
    async def enroll_user(
        self, 
        user_id: str,
        resource_id: str
    ) -> EnrollmentResult:
        """Enroll user in resource."""
        pass


# Round 1: Prototype implementation
class PrototypeIGOTProvider(LearningResourceProvider):
    """
    Prototype iGOT provider using locally cached/seeded data.
    
    In Round 1: Load from learning_resources collection.
    In Round 2: Call live iGOT API.
    """
    
    async def search_by_competency(self, competency_code: str, filters: Dict):
        # Query: learning_resources where provider="IGOT" and competencies.code=competency_code
        return database.learning_resources.find({
            "provider": "IGOT",
            "competencies.competency_code": competency_code,
            "status": "ACTIVE"
        }).limit(filters.get("limit", 10))


class PrototypeNSSTAProvider(LearningResourceProvider):
    """
    Prototype NSSTA provider using officially published material.
    
    Source: NSSTA/TPAC directories, MoSPI publications.
    """
    
    async def search_by_competency(self, competency_code: str, filters: Dict):
        # Query: learning_resources where provider="NSSTA" and competencies.code=competency_code
        return database.learning_resources.find({
            "provider": "NSSTA",
            "competencies.competency_code": competency_code,
            "status": "ACTIVE"
        }).limit(filters.get("limit", 10))


# Round 2: Live implementations (future)
class LiveIGOTProvider(LearningResourceProvider):
    """Live iGOT API integration."""
    pass

class LiveNSSTAProvider(LearningResourceProvider):
    """Live NSSTA/TPAC API integration."""
    pass


# Factory
class ProviderFactory:
    @staticmethod
    def get_provider(provider_name: str, mode: str = "prototype") -> LearningResourceProvider:
        if provider_name == "IGOT":
            return PrototypeIGOTProvider() if mode == "prototype" else LiveIGOTProvider()
        elif provider_name == "NSSTA":
            return PrototypeNSSTAProvider() if mode == "prototype" else LiveNSSTAProvider()
        else:
            raise ValueError(f"Unknown provider: {provider_name}")
```

### Round 1 Implementation

- Use locally seeded data in `learning_resources` collection
- Source: Manually curated iGOT course list + NSSTA/TPAC training programmes
- Store provenance: `source_url`, `source_document`, `import_timestamp`, `verification_status`
- No live API calls

### Round 2 Implementation (Phase 4+)

- Call official iGOT API
- Call official NSSTA API
- Sync with live seat availability
- Handle authentication/billing

---

## 9. NSSTA REQUIREMENTS

### Important Notes

NSSTA integration is **REQUIRED** by PS, but we must be honest:

✅ **What we CAN do:**
- Store officially published NSSTA/TPAC training programme metadata
- Link programmes to competencies
- Recommend programmes to employees
- Track hypothetical enrollments (in prototype)

❌ **What we CANNOT fake:**
- Live seat availability (requires NSSTA API)
- Live enrollment confirmation
- Completion verification
- State-level approvals

### Data Model: NSSTA Provenance

```python
class NSSTAProvenance:
    """Track source of NSSTA data."""
    
    source_type: str  # OFFICIAL_TPAC | MoSPI_PUBLICATION | VERIFIED_DIRECTORY
    source_url: str  # Link to official document
    source_document: str  # "NSSTA_Directory_2024.pdf"
    training_year: int  # 2024
    state_approved: bool  # True if approved for state use
    last_verified_at: datetime  # When we last verified with official source
    verification_status: str  # VERIFIED | PENDING | OUTDATED
    notes: str  # Any additional context
```

### Seeding Strategy

1. **Manually curate** list of key NSSTA/TPAC programmes from MoSPI official publications
2. **Map** programmes to ShikshaSetu competency framework
3. **Store** with full provenance (source URL, training year, etc.)
4. **Don't claim** enrollment availability until live API is ready
5. **Document** that prototype data is for demonstration only

### Example NSSTA Programme Entry

```json
{
  "_id": ObjectId,
  "resource_id": "NSSTA-TPAC-2024-SQL-ANALYSIS",
  "provider": "NSSTA",
  "metadata": {
    "title": "Data Analysis Using SQL",
    "description": "Advanced SQL for statistical data analysis",
    "duration_hours": 24,
    "difficulty": "INTERMEDIATE",
    "target_roles": ["DATA_ANALYST", "STATISTICAL_OFFICER"],
  },
  "competencies": [
    {"competency_code": "TECH_SQL", "weight": 0.9},
    {"competency_code": "STAT_DATA_QUALITY", "weight": 0.1}
  ],
  "provider_specific": {
    "tpac_programme_code": "TPAC-2024-005",
    "training_year": 2024,
    "maximum_participants": 30,
    "state_eligible": ["MH", "UP", "KA", ...],
    "mopspi_reference": "MoSPI/NSSTA/Dir2024"
  },
  "source": {
    "source_type": "OFFICIAL_TPAC",
    "source_url": "https://nssta.org/tpac/programmes/2024",
    "source_document": "NSSTA_TPAC_Directory_2024.pdf",
    "import_timestamp": "2026-06-15T00:00:00Z",
    "last_verified_at": "2026-08-15T00:00:00Z",
    "verification_status": "VERIFIED",
    "notes": "Programme information verified from official NSSTA TPAC directory"
  }
}
```

---

## 10. API DESIGN (PROPOSAL)

### Endpoints

#### 1. Get Recommendations

```
GET /api/v1/recommendations/me
GET /api/v1/recommendations?role_id={role_id}&user_id={user_id}

Response: RecommendationResponse (see section 7)
Status: 200 OK | 401 UNAUTHORIZED | 422 NO_ROLE
```

#### 2. Get Single Recommendation

```
GET /api/v1/recommendations/{recommendation_id}

Response: Single recommendation with full details
Status: 200 OK | 404 NOT_FOUND
```

#### 3. List Learning Resources

```
GET /api/v1/learning-resources?provider={IGOT|NSSTA|ANY}&competency={code}&difficulty={BEGINNER|...}

Query Parameters:
  provider: IGOT | NSSTA | ANY (default)
  competency: Competency code filter
  difficulty: BEGINNER | INTERMEDIATE | ADVANCED
  target_role: Role code filter
  limit: 1-100 (default 20)
  offset: 0-based pagination

Response: {
  items: [LearningResourceSummary],
  total: int,
  limit: int,
  offset: int
}
```

#### 4. Get Learning Resource Details

```
GET /api/v1/learning-resources/{resource_id}

Response: LearningResource (full details)
Status: 200 OK | 404 NOT_FOUND
```

#### 5. Get User's Learning History

```
GET /api/v1/users/me/learning-history

Query Parameters:
  resource_provider: IGOT | NSSTA | ANY
  interaction_type: ENROLLED | COMPLETED | ABANDONED
  limit: 1-100 (default 20)

Response: {
  items: [UserLearningHistoryEntry],
  total: int
}
```

#### 6. Enroll in Resource

```
POST /api/v1/learning-resources/{resource_id}/enroll

Body: {}

Response: {
  enrollment_id: str,
  resource_id: str,
  user_id: str,
  enrolled_at: datetime,
  status: "PENDING" | "CONFIRMED" | "REJECTED",
  message: str
}
Status: 201 CREATED | 400 BAD_REQUEST | 409 CONFLICT (already enrolled)
```

#### 7. Rate Learning Resource

```
POST /api/v1/learning-resources/{resource_id}/rate

Body: {
  rating: 1-5,
  feedback: "Very helpful course...",
  interaction_type: "COMPLETED" | "ABANDONED" | "IN_PROGRESS"
}

Response: {
  rating_id: str,
  rating: int,
  feedback: str,
  created_at: datetime
}
```

### Response Schemas

#### LearningResourceSummary (Lightweight)

```python
class LearningResourceSummary(BaseModel):
    resource_id: str
    provider: str  # IGOT | NSSTA
    title: str
    difficulty: str
    duration_hours: int
    competency_codes: list[str]
    average_rating: float | None
    completion_rate: float | None
    match_score: float | None  # Only in recommendation context
```

#### LearningResource (Full)

```python
class LearningResource(BaseModel):
    resource_id: str
    provider: str
    resource_type: str
    metadata: dict
    competencies: list[dict]
    target_roles: list[str]
    prerequisites: list[str]
    source: dict  # Provenance
    engagement: dict  # Ratings, completion rate
    provider_specific: dict
```

#### RecommendationResponse (See Section 7 for full structure)

---

## 11. IMPLEMENTATION ROADMAP

### Phase 3.0: Foundation (Week 1)

- [ ] Create `learning_resources` collection schema
- [ ] Create `learning_resource_mappings` collection schema
- [ ] Create `user_learning_history` collection schema
- [ ] Add MongoDB indexes
- [ ] Create Pydantic schemas for all three collections
- [ ] Write repository layer (CRUD functions)

**Files to Create:**
- `app/learning_resources/__init__.py`
- `app/learning_resources/models.py`
- `app/learning_resources/schemas.py`
- `app/learning_resources/repository.py`

### Phase 3.1: Prototype Data (Week 1)

- [ ] Seed `learning_resources` with 50+ iGOT courses (curated, real)
- [ ] Seed `learning_resources` with 20+ NSSTA/TPAC programmes (from official sources)
- [ ] Map resources to competencies in `learning_resource_mappings` (manually verify alignment)
- [ ] Add quality scores (content_alignment, accuracy_score, recency_score)

**Data Sources:**
- iGOT: https://igot.gov.in (public course catalog)
- NSSTA: MoSPI official publications

### Phase 3.2: Provider Abstraction (Week 2)

- [ ] Create `LearningResourceProvider` abstract base class
- [ ] Implement `PrototypeIGOTProvider`
- [ ] Implement `PrototypeNSSTAProvider`
- [ ] Create `ProviderFactory`
- [ ] Write comprehensive tests for provider interface

**Files to Create:**
- `app/learning_resources/providers/base.py`
- `app/learning_resources/providers/igot_provider.py`
- `app/learning_resources/providers/nssta_provider.py`
- `app/learning_resources/providers/factory.py`

### Phase 3.3: Recommendation Engine (Week 2)

- [ ] Create `RecommendationEngine` class
- [ ] Implement scoring formula (6-component model)
- [ ] Implement candidate generation (competency-driven search)
- [ ] Implement gap-to-resource matching
- [ ] Implement explanation generation
- [ ] Write tests with expected scores for known inputs

**Files to Create:**
- `app/recommendations/__init__.py`
- `app/recommendations/engine.py`
- `app/recommendations/schemas.py`
- `app/recommendations/repository.py`

### Phase 3.4: API Endpoints (Week 2)

- [ ] Implement `GET /api/v1/recommendations/me`
- [ ] Implement `GET /api/v1/learning-resources`
- [ ] Implement `GET /api/v1/learning-resources/{id}`
- [ ] Implement `POST /api/v1/learning-resources/{id}/rate`
- [ ] Add JWT authentication to all endpoints
- [ ] Add user ownership validation

**Files to Create:**
- `app/recommendations/router.py`
- Add route registration in `app/main.py`

### Phase 3.5: Tests & Verification (Week 3)

- [ ] Write unit tests for scoring formula
- [ ] Write integration tests for recommendation engine
- [ ] Write E2E tests for recommendation API
- [ ] Verify all 139 existing tests still pass
- [ ] Create test recommendations for known scenarios (Statistical Officer, Data Analyst)
- [ ] Document scoring decisions and weights

**Files to Create:**
- `tests/test_recommendations_engine.py`
- `tests/test_recommendations_api.py`
- `tests/test_provider_factory.py`

### Success Criteria

- ✅ 150+ total tests passing (139 existing + 11+ new)
- ✅ Recommendations generated for demo users
- ✅ All scoring components transparent and auditable
- ✅ Provider architecture extensible (easy to add live iGOT/NSSTA)
- ✅ iGOT + NSSTA data properly sourced and tracked
- ✅ No breaking changes to existing systems

---

## 12. DECISION SUMMARY & RECOMMENDATIONS

### Design Decisions Made

| Decision | Rationale | Risk |
|----------|-----------|------|
| **Separate `learning_resources` collection** | Reusability across iGOT/NSSTA; single source of truth | Requires ETL for updates |
| **Explicit `learning_resource_mappings` collection** | Supports complex ranking factors; auditable quality scores | Additional collection to maintain |
| **6-component scoring formula** | Balances multiple factors; explainable; deterministic | Weights may need tuning; add A/B testing later |
| **Provider abstraction pattern** | Future-proof (easy to add live APIs); testable | Added indirection/complexity |
| **Prototype-first approach** | Demo fully functional before live APIs; lower risk | Requires data migration when going live |
| **Competency-driven search over semantic search** | Fast, structured, auditable; no LLM dependency | May miss conceptually similar resources; add semantic Phase 3.5 |

### Data Decisions

| Data | Source | Frequency | Confidence |
|------|--------|-----------|------------|
| iGOT Courses | Public API/catalog + manual curation | Quarterly (Phase 4+) | High (official) |
| NSSTA Programmes | MoSPI official publications | Annually | High (official) |
| Competency Mappings | Manual expert review | Per resource | High (manual) |
| Quality Scores | Expert review + user feedback | Quarterly | Medium (expert) |
| User Engagement | Our database (learning_history) | Real-time | High (owned) |

### Recommended Next Phase (Phase 4)

After Phase 3 verification:

1. **Phase 4.1:** Live iGOT API integration (if access available)
2. **Phase 4.2:** Live NSSTA/TPAC API integration (if access available)
3. **Phase 4.3:** Semantic search enhancement (LLM-based resource discovery)
4. **Phase 4.4:** Learning path generation (multi-step competency progression)
5. **Phase 4.5:** A/B testing recommendation weights (data-driven optimization)

---

## AUDIT COMPLETE ✅

**Status:** Ready for Phase 3 implementation

**Next Step:** User review and approval of:
1. Collection schema designs
2. Recommendation scoring formula
3. Provider architecture pattern
4. API endpoint design
5. Implementation roadmap

Once approved, Phase 3 implementation begins with Week 1 foundation work.

