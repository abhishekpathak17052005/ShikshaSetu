# PHASE 3: FINAL ARCHITECTURE (APPROVED WITH REVISIONS)

**Date:** August 27, 2026  
**Status:** Architecture finalized and approved for implementation  
**Baseline:** 139/139 tests passing  

---

## EXECUTIVE SUMMARY

Based on user feedback, Phase 3 will implement a **deterministic recommendation engine** with:

- **5-component scoring formula** (no engagement metrics yet - wait for real data)
- **Configurable weights** (prototype weights provided, not official)
- **Small prototype dataset** (20-30 iGOT + 10-15 NSSTA resources initially)
- **Provider abstraction** (ready for live APIs in Phase 4)
- **Auditable ranking** (no LLM-based selection, only explanation)
- **Multi-gap support** (handle users with multiple skill gaps)

**No invention of missing metadata.** Only use verified data.

---

## 1. REVISED SCORING FORMULA

### Round 1 Weights (PROTOTYPE - Not Official)

```
RECOMMENDATION_SCORE = 
    (competency_match × 0.40) +        // 40% - How well does resource cover gap?
    (gap_priority × 0.25) +             // 25% - How urgent is this gap?
    (role_match × 0.20) +               // 20% - Is this relevant to user's role?
    (difficulty_match × 0.10) +         // 10% - Is difficulty appropriate?
    (prerequisite_match × 0.05)         // 5%  - Are prerequisites satisfied?

Total: 100%

NO engagement_quality (5%) in Round 1 - we don't have reliable real data yet.
```

### Why These Weights

- **Competency match (40%):** Most important - resource must actually teach the needed skill
- **Gap priority (25%):** Use existing skill_gap engine priority_score (already weighted by gap + importance + priority)
- **Role match (20%):** Resources should be relevant to user's job
- **Difficulty (10%):** Secondary - resource level should match learner level
- **Prerequisites (5%):** Minimal weight - only if explicitly mapped

### Configurable Implementation

```python
class RecommendationScoringConfig:
    """Configurable weights for recommendation scoring."""
    
    competency_match_weight: float = 0.40
    gap_priority_weight: float = 0.25
    role_match_weight: float = 0.20
    difficulty_match_weight: float = 0.10
    prerequisite_match_weight: float = 0.05
    
    def validate(self) -> bool:
        total = sum([
            self.competency_match_weight,
            self.gap_priority_weight,
            self.role_match_weight,
            self.difficulty_match_weight,
            self.prerequisite_match_weight,
        ])
        return abs(total - 1.0) < 1e-9
```

**Can be:** Loaded from config file, environment, or database for A/B testing (Phase 4).

---

## 2. COMPONENT DEFINITIONS (REVISED)

### Competency Match (40%)

```python
# Query: learning_resource_mappings for this (resource, competency) pair
# Use mapping_quality fields (if available)

if mapping_available:
    competency_match = (
        mapping_quality.content_alignment × 0.6 +
        mapping_quality.accuracy_score × 0.4
    )
else:
    # No mapping metadata - assume neutral
    competency_match = 0.5  # Neutral, not 1.0
```

**Key:** Don't assume. If we don't have alignment data, use neutral (0.5), not optimistic (1.0).

---

### Gap Priority (25%)

```python
# Reuse existing skill_gap engine priority_score
# Already calculated as: (gap × 0.60 + importance × 0.25 + priority × 0.15)

gap_priority = skill_gap.priority_score  # 0.0-1.0 (already sorted by this)
```

**This is already done.** No new calculation needed.

---

### Role Match (20%)

```python
# Does the resource target the user's role?

resource_target_roles = learning_resource.metadata.get("target_roles", [])
user_role_code = user.role.role_code

if user_role_code in resource_target_roles:
    role_match = 1.0
elif not resource_target_roles:
    # Role targeting unknown - treat as neutral
    role_match = 0.5  # Not 1.0 (don't assume all roles match)
else:
    # Resource targets other roles - use lower score
    role_match = 0.3  # Not 0.0 (might still be useful for cross-role learning)
```

**Key:** Unknown ≠ Universal. If we don't know target roles, use neutral.

---

### Difficulty Match (10%)

```python
# Is resource difficulty appropriate for learner's current level?

current_level = user_competency_profile[competency].current_level  # 1-5
resource_difficulty = learning_resource.metadata.get("difficulty")

# Map difficulty labels to numeric equivalents
difficulty_levels = {
    "BEGINNER": 1.5,
    "FOUNDATIONAL": 2.0,
    "INTERMEDIATE": 3.0,
    "ADVANCED": 4.0,
    "EXPERT": 5.0,
}

if not resource_difficulty:
    difficulty_match = 0.5  # Unknown, not 1.0
else:
    resource_level = difficulty_levels[resource_difficulty]
    diff = abs(current_level - resource_level)
    
    if diff <= 1.0:
        difficulty_match = 1.0      # Perfect match
    elif diff <= 1.5:
        difficulty_match = 0.8      # Close match
    elif diff <= 2.0:
        difficulty_match = 0.5      # Acceptable stretch
    else:
        difficulty_match = 0.2      # Too far off
```

**Key:** Penalize (don't reward) missing data.

---

### Prerequisite Match (5%)

```python
# How many prerequisites does user already satisfy?

resource_prerequisites = learning_resource.metadata.get("prerequisites", [])

if not resource_prerequisites:
    # No prerequisites listed - treat as no barrier
    prerequisite_match = 1.0
else:
    user_competencies = {
        comp.code: comp.current_level 
        for comp in user_competency_profiles
    }
    
    satisfied = 0
    for prereq_code in resource_prerequisites:
        if user_competencies.get(prereq_code, 0) >= 2.0:
            satisfied += 1
    
    prerequisite_match = satisfied / len(resource_prerequisites)
```

**Key:** Unknown prerequisites = no barrier. Don't penalize.

---

## 3. DATA MODEL AUDIT

### Before Creating New Collections: Check Existing

**Already Exists - Check These First:**

1. **learning_materials** (app/ai/models.py)
   - user_id, filename, content_type, status, chunk_count
   - **Purpose:** User-uploaded documents
   - **NOT suitable for:** iGOT/NSSTA courses (not user-uploaded)

2. **document_chunks** (app/ai/models.py)
   - material_id, sequence, text, embedding
   - **Purpose:** Extracted text from learning materials
   - **NOT suitable for:** Course metadata (no title, duration, etc.)

3. **quizzes** (implied from schemas)
   - material_id, competency_code, questions
   - **Purpose:** Quizzes generated from materials
   - **NOT suitable for:** Catalog of external courses

4. **competency_evidence** (app/competencies/schemas.py)
   - user_id, competency_id, evidence_type (QUIZ, TRAINING, etc.)
   - **Purpose:** Track evidence of competency
   - **NOT suitable for:** Learning resource catalog

**Verdict:** No existing collection suitable for external course catalog. **CREATE NEW COLLECTIONS.**

---

## 4. FINAL DATA MODELS

### New Collection: learning_resources

```python
class LearningResource(BaseModel):
    """External learning resource (iGOT course, NSSTA programme)."""
    
    _id: ObjectId
    resource_id: str  # "IGOT-COURSE-12345" | "NSSTA-TPAC-2024-SQL"
    provider: str     # "IGOT" | "NSSTA"
    resource_type: str  # "COURSE" | "TRAINING_PROGRAMME" | "MODULE"
    
    # Core metadata
    title: str
    description: str
    language: str = "EN"
    status: str  # "ACTIVE" | "ARCHIVED" | "BETA"
    
    # Learning characteristics
    duration_hours: int | None  # Can be unknown (None, not 0)
    difficulty: str  # "BEGINNER" | "INTERMEDIATE" | "ADVANCED" (or None if unknown)
    target_roles: list[str] = []  # ["DATA_ANALYST", "STATISTICAL_OFFICER"] or empty if unknown
    prerequisites: list[str] = []  # Competency codes or empty if none/unknown
    
    # Competency linkage
    competencies: list[dict] = []
    # [
    #   {
    #       "competency_code": "TECH_SQL",
    #       "competency_id": ObjectId,
    #       "coverage_level": "FOUNDATIONAL" | "INTERMEDIATE" | "ADVANCED",
    #       "weight": 0.8  # 80% of course covers SQL
    #   }
    # ]
    
    # Provenance (NO INVENTED DATA)
    source: dict
    # {
    #     "source_type": "OFFICIAL_API" | "MANUAL_ENTRY" | "GOVERNMENT_PUBLICATION",
    #     "source_url": "https://igot.gov.in/courses/12345" | None if unknown,
    #     "source_document": "NSSTA_Directory_2024.pdf" | None,
    #     "import_timestamp": datetime,
    #     "last_verified_at": datetime | None,
    #     "verification_status": "VERIFIED" | "PENDING" | "OUTDATED" | "UNKNOWN",
    # }
    
    # Provider-specific fields (can be empty)
    provider_specific: dict = {}
    # For IGOT: {course_id, track_id, ...}
    # For NSSTA: {programme_code, training_year, mopspi_ref, ...}
    
    created_at: datetime
    updated_at: datetime
```

**Key Design Decisions:**
- ✅ Include all available metadata
- ❌ Don't invent missing fields
- ✅ Mark uncertainty (None, "UNKNOWN")
- ✅ Full provenance tracking
- ✅ No engagement metrics (round 1)

---

### New Collection: learning_resource_mappings

```python
class LearningResourceMapping(BaseModel):
    """Explicit mapping of resource to competency with quality scores."""
    
    _id: ObjectId
    resource_id: ObjectId  # Reference to learning_resources
    competency_id: ObjectId
    competency_code: str
    
    # Mapping quality (only if verified)
    mapping_quality: dict
    # {
    #     "content_alignment": 0.0-1.0 or None,  # How well does resource cover competency?
    #     "accuracy_score": 0.0-1.0 or None,     # Verified accuracy
    #     "recency_score": 0.0-1.0 or None,      # How current?
    # }
    
    # Metadata (for future ranking)
    ranking_factors: dict = {}
    # Will be populated at recommendation time, not stored
    
    verified_at: datetime | None  # When mapping was last verified
    verified_by: str | None        # Expert who verified
    notes: str | None              # Mapping notes
    
    created_at: datetime
```

**Key Design Decisions:**
- ✅ Only store scores IF verified
- ✅ Don't compute/estimate quality scores
- ✅ Track verification (who, when)
- ✅ Use None for unknown data

---

### New Collection: user_learning_history

```python
class UserLearningHistory(BaseModel):
    """Track user engagement with learning resources."""
    
    _id: ObjectId
    user_id: ObjectId
    resource_id: ObjectId
    competency_id: ObjectId | None  # May not be known
    
    # Interaction tracking
    interaction_type: str  # "BOOKMARKED" | "ENROLLED" | "STARTED" | "COMPLETED" | "ABANDONED"
    first_engagement: datetime
    last_engagement: datetime
    engagement_count: int = 1
    
    # Progress (only if available)
    progress_percent: float | None = None  # 0-100 or None if unknown
    time_spent_hours: float | None = None  # or None
    
    # User feedback (optional)
    rating: int | None = None  # 1-5 or None
    feedback_text: str | None = None
    
    # Later: link to competency evidence
    evidence_id: ObjectId | None = None  # Future link to competency_evidence record
    
    created_at: datetime
    updated_at: datetime
```

**Key Design Decisions:**
- ✅ Flexible interaction types
- ✅ Optional fields (None if unknown)
- ✅ Track actual engagement only
- ❌ Don't invent completion rates or ratings

---

## 5. PROVIDER ARCHITECTURE (APPROVED)

### Abstract Provider

```python
from abc import ABC, abstractmethod
from typing import List, Optional, Dict

class LearningResourceProvider(ABC):
    """Abstract provider for learning resources."""
    
    @abstractmethod
    async def search_by_competency(
        self,
        competency_code: str,
        filters: Optional[Dict] = None
    ) -> List[Dict]:
        """
        Find resources covering a competency.
        
        Args:
            competency_code: e.g., "TECH_SQL"
            filters: Optional {difficulty, role, limit}
        
        Returns:
            List of resource dicts with score metadata
        """
        pass
    
    @abstractmethod
    async def get_resource_details(
        self,
        resource_id: str
    ) -> Optional[Dict]:
        """Get full resource metadata."""
        pass
    
    @abstractmethod
    async def check_availability(
        self,
        resource_id: str
    ) -> Dict:
        """
        Check resource availability.
        
        Returns:
            {
                available: bool,
                reason: str,
                live_seats: int | None,  # Only if known
                enrollment_open: bool | None,
                metadata: {...}
            }
        """
        pass
```

---

### Round 1: Prototype Implementation

```python
class PrototypeIGOTProvider(LearningResourceProvider):
    """
    Prototype provider using locally seeded data.
    
    Round 1: Query learning_resources (provider="IGOT")
    Round 2 (Phase 4+): Call live iGOT API
    """
    
    def __init__(self, database):
        self.database = database
        self.provider_name = "IGOT"
    
    async def search_by_competency(
        self,
        competency_code: str,
        filters: Optional[Dict] = None
    ) -> List[Dict]:
        """Search learning_resources collection."""
        
        limit = filters.get("limit", 10) if filters else 10
        
        query = {
            "provider": "IGOT",
            "competencies.competency_code": competency_code,
            "status": "ACTIVE"
        }
        
        # Optional filters
        if filters and "difficulty" in filters:
            query["metadata.difficulty"] = filters["difficulty"]
        
        if filters and "target_role" in filters:
            query["metadata.target_roles"] = filters["target_role"]
        
        resources = list(
            self.database.learning_resources.find(query).limit(limit)
        )
        
        return resources
    
    async def get_resource_details(
        self,
        resource_id: str
    ) -> Optional[Dict]:
        """Get full resource metadata."""
        
        return self.database.learning_resources.find_one({
            "resource_id": resource_id,
            "provider": "IGOT"
        })
    
    async def check_availability(
        self,
        resource_id: str
    ) -> Dict:
        """
        Check availability.
        
        Round 1: Always available (prototype)
        Round 2: Query live API
        """
        
        resource = await self.get_resource_details(resource_id)
        
        if not resource:
            return {
                "available": False,
                "reason": "Resource not found",
                "metadata": None
            }
        
        return {
            "available": True,
            "reason": "Prototype - available in catalogue",
            "live_seats": None,  # Don't invent
            "enrollment_open": None,  # Don't invent
            "metadata": {
                "title": resource.get("title"),
                "provider": "IGOT"
            }
        }


class PrototypeNSSTAProvider(LearningResourceProvider):
    """Similar to PrototypeIGOTProvider but for NSSTA."""
    
    def __init__(self, database):
        self.database = database
        self.provider_name = "NSSTA"
    
    # Same methods as IGOT, filtered by provider="NSSTA"
```

---

### Factory Pattern

```python
class ProviderFactory:
    """Factory for creating learning resource providers."""
    
    _providers = {
        "IGOT": {
            "prototype": PrototypeIGOTProvider,
            "live": None,  # Will be LiveIGOTProvider in Phase 4
        },
        "NSSTA": {
            "prototype": PrototypeNSSTAProvider,
            "live": None,
        }
    }
    
    @classmethod
    def get_provider(
        cls,
        provider_name: str,
        database,
        mode: str = "prototype"
    ) -> LearningResourceProvider:
        """
        Get provider instance.
        
        Args:
            provider_name: "IGOT" | "NSSTA"
            database: MongoDB database
            mode: "prototype" | "live"
        
        Returns:
            Provider instance
        """
        
        if provider_name not in cls._providers:
            raise ValueError(f"Unknown provider: {provider_name}")
        
        provider_class = cls._providers[provider_name].get(mode)
        
        if provider_class is None:
            raise ValueError(
                f"Provider {provider_name} not available in {mode} mode"
            )
        
        return provider_class(database)
```

---

## 6. RECOMMENDATION ENGINE CORE

### Input Specification

```python
class RecommendationRequest:
    """Input to recommendation engine."""
    
    user_id: str
    role_id: str
    skill_gaps: List[SkillGapCompetency]  # From /skill-gaps endpoint
    user_competency_profiles: Dict[str, CompetencyProfile]
    user_learning_history: List[UserLearningHistory] = []
    
    # Filters
    preferred_providers: List[str] = ["IGOT", "NSSTA"]  # Or specific provider
    target_gap_categories: List[str] = ["CRITICAL", "HIGH"]  # Default urgent gaps
    max_recommendations: int = 5
    max_candidates_per_gap: int = 10  # Search width
```

---

### Recommendation Engine Algorithm

```python
class RecommendationEngine:
    """Deterministic recommendation engine."""
    
    def __init__(
        self,
        database,
        config: RecommendationScoringConfig = None
    ):
        self.database = database
        self.config = config or RecommendationScoringConfig()
        self.igot_provider = ProviderFactory.get_provider("IGOT", database)
        self.nssta_provider = ProviderFactory.get_provider("NSSTA", database)
    
    async def generate_recommendations(
        self,
        request: RecommendationRequest
    ) -> List[Dict]:
        """
        Generate recommendations from skill gaps.
        
        Algorithm:
        1. Filter skill gaps by category (HIGH, CRITICAL)
        2. For each gap, find candidate resources
        3. Score and rank candidates
        4. Deduplicate (avoid recommending same resource twice)
        5. Sort by score
        6. Return top N recommendations
        """
        
        recommendations = []
        
        # 1. Filter urgent gaps
        urgent_gaps = [
            gap for gap in request.skill_gaps
            if gap.gap_category in request.target_gap_categories
        ]
        
        if not urgent_gaps:
            # No urgent gaps - return empty
            return []
        
        # 2-3. For each gap, find and score candidates
        scored_candidates = []
        
        for gap in urgent_gaps:
            candidates = await self._find_candidates_for_gap(
                gap,
                request.preferred_providers,
                request.max_candidates_per_gap
            )
            
            for candidate in candidates:
                score = self._score_candidate(
                    candidate,
                    gap,
                    request.user_competency_profiles
                )
                
                scored_candidates.append({
                    "candidate": candidate,
                    "gap": gap,
                    "score": score,
                })
        
        # 4. Deduplicate by resource_id (keep highest score)
        deduped = {}
        for item in scored_candidates:
            resource_id = item["candidate"]["resource_id"]
            
            if resource_id not in deduped or item["score"] > deduped[resource_id]["score"]:
                deduped[resource_id] = item
        
        recommendations = list(deduped.values())
        
        # 5. Sort by score (highest first)
        recommendations.sort(key=lambda x: x["score"], reverse=True)
        
        # 6. Return top N
        return recommendations[:request.max_recommendations]
    
    async def _find_candidates_for_gap(
        self,
        gap: SkillGapCompetency,
        providers: List[str],
        limit: int
    ) -> List[Dict]:
        """Find candidate resources for a skill gap."""
        
        candidates = []
        
        # Try each provider
        for provider_name in providers:
            try:
                provider = ProviderFactory.get_provider(
                    provider_name,
                    self.database
                )
                
                results = await provider.search_by_competency(
                    gap.competency_code,
                    {"limit": limit, "difficulty": gap.current_level}
                )
                
                candidates.extend(results)
            
            except Exception as e:
                # Provider error - log and continue
                print(f"Provider {provider_name} error: {e}")
                continue
        
        return candidates[:limit]
    
    def _score_candidate(
        self,
        candidate: Dict,
        gap: SkillGapCompetency,
        user_profiles: Dict
    ) -> float:
        """
        Score a candidate resource for a gap.
        
        Uses 5-component formula.
        """
        
        # 1. Competency match (40%)
        competency_match = self._calculate_competency_match(
            candidate,
            gap.competency_code
        )
        
        # 2. Gap priority (25%)
        gap_priority = gap.priority_score  # Already calculated
        
        # 3. Role match (20%)
        role_match = self._calculate_role_match(
            candidate,
            gap  # May not have role info
        )
        
        # 4. Difficulty match (10%)
        difficulty_match = self._calculate_difficulty_match(
            candidate,
            gap.current_level
        )
        
        # 5. Prerequisite match (5%)
        prerequisite_match = self._calculate_prerequisite_match(
            candidate,
            user_profiles
        )
        
        # Weighted sum
        score = (
            (competency_match * self.config.competency_match_weight) +
            (gap_priority * self.config.gap_priority_weight) +
            (role_match * self.config.role_match_weight) +
            (difficulty_match * self.config.difficulty_match_weight) +
            (prerequisite_match * self.config.prerequisite_match_weight)
        )
        
        return round(score, 3)
    
    def _calculate_competency_match(self, candidate: Dict, competency_code: str) -> float:
        """Calculate competency match (0-1)."""
        
        competencies = candidate.get("competencies", [])
        
        for comp in competencies:
            if comp.get("competency_code") == competency_code:
                # Found mapping - use quality score if available
                mapping = self.database.learning_resource_mappings.find_one({
                    "resource_id": candidate["_id"],
                    "competency_code": competency_code
                })
                
                if mapping and mapping.get("mapping_quality"):
                    quality = mapping["mapping_quality"]
                    
                    alignment = quality.get("content_alignment")
                    accuracy = quality.get("accuracy_score")
                    
                    if alignment is not None and accuracy is not None:
                        return alignment * 0.6 + accuracy * 0.4
                    elif alignment is not None:
                        return alignment
                    elif accuracy is not None:
                        return accuracy
                
                # No mapping quality - use weight from competency
                weight = comp.get("weight", 0.5)
                return min(weight, 1.0)  # Cap at 1.0
        
        # Competency not listed - neutral
        return 0.5
    
    def _calculate_role_match(self, candidate: Dict, gap) -> float:
        """Calculate role match (0-1)."""
        
        target_roles = candidate.get("metadata", {}).get("target_roles", [])
        
        # If no target roles specified, neutral
        if not target_roles:
            return 0.5
        
        # If user's role in target_roles, match
        if hasattr(gap, "user_role_code"):
            if gap.user_role_code in target_roles:
                return 1.0
        
        # Default: roles don't match
        return 0.3
    
    def _calculate_difficulty_match(self, candidate: Dict, current_level: float) -> float:
        """Calculate difficulty match (0-1)."""
        
        difficulty = candidate.get("metadata", {}).get("difficulty")
        
        if not difficulty:
            return 0.5  # Unknown difficulty = neutral
        
        difficulty_levels = {
            "BEGINNER": 1.5,
            "FOUNDATIONAL": 2.0,
            "INTERMEDIATE": 3.0,
            "ADVANCED": 4.0,
            "EXPERT": 5.0,
        }
        
        resource_level = difficulty_levels.get(difficulty)
        
        if not resource_level:
            return 0.5
        
        diff = abs(current_level - resource_level)
        
        if diff <= 1.0:
            return 1.0
        elif diff <= 1.5:
            return 0.8
        elif diff <= 2.0:
            return 0.5
        else:
            return 0.2
    
    def _calculate_prerequisite_match(self, candidate: Dict, user_profiles: Dict) -> float:
        """Calculate prerequisite match (0-1)."""
        
        prerequisites = candidate.get("metadata", {}).get("prerequisites", [])
        
        if not prerequisites:
            return 1.0  # No prerequisites = no barrier
        
        satisfied = 0
        
        for prereq_code in prerequisites:
            profile = user_profiles.get(prereq_code)
            
            if profile and profile.get("current_level", 0) >= 2.0:
                satisfied += 1
        
        return satisfied / len(prerequisites)
```

---

## 7. MULTI-GAP SUPPORT

### Algorithm for Multiple Gaps

The engine automatically handles multiple gaps:

```
1. Get skill gaps (already sorted by priority from skill_gap engine)
2. Filter to HIGH + CRITICAL gaps
3. For EACH gap:
   - Find candidate resources
   - Score against this specific gap
4. Deduplicate across all gaps (same resource shouldn't be recommended twice)
5. Keep highest score if duplicate
6. Sort by score
7. Return top N
```

### Example: Statistical Officer with 3 Gaps

```
Input Gaps (pre-sorted by priority_score):

Gap 1: STAT_SAMPLING
  - current: 2.55, required: 4.0
  - gap: 1.45, priority_score: 0.75

Gap 2: TECH_SQL
  - current: 1.8, required: 3.5
  - gap: 1.70, priority_score: 0.70

Gap 3: TECH_PYTHON
  - current: 2.0, required: 3.5
  - gap: 1.50, priority_score: 0.68

Processing:

For Gap 1 (STAT_SAMPLING):
  - Find resources covering STAT_SAMPLING
  - Score each: importance (gap 1.45), role_match, difficulty_match, etc.
  - Candidates: [Sampling Methods (NSSTA) score 0.88, ...]

For Gap 2 (TECH_SQL):
  - Find resources covering TECH_SQL
  - Score each
  - Candidates: [SQL Fundamentals (iGOT) score 0.86, ...]

For Gap 3 (TECH_PYTHON):
  - Find resources covering TECH_PYTHON
  - Score each
  - Candidates: [Python Basics (iGOT) score 0.72, ...]

Deduplication:
  - No duplicates in this example

Final Ranking:
  1. Sampling Methods (0.88) → addresses Gap 1
  2. SQL Fundamentals (0.86) → addresses Gap 2
  3. Python Basics (0.72) → addresses Gap 3

Output:
  Top 3 recommendations covering 3 separate gaps
```

---

## 8. RECOMMENDATION RESPONSE

### Recommendation Schema

```python
class RecommendationItem(BaseModel):
    """Single recommendation."""
    
    rank: int
    resource: LearningResourceResponse
    gap_addressed: SkillGapCompetency
    
    score: dict
    # {
    #     "overall_score": 0.86,
    #     "components": {
    #         "competency_match": 0.85,
    #         "gap_priority": 0.75,
    #         "role_match": 1.0,
    #         "difficulty_match": 0.8,
    #         "prerequisite_match": 1.0
    #     }
    # }
    
    explanation: dict
    # {
    #     "summary": "High-priority SQL gap...",
    #     "gap_context": {
    #         "current_level": 1.8,
    #         "required_level": 3.5,
    #         "gap": 1.7,
    #         "gap_category": "HIGH"
    #     },
    #     "matching_factors": [
    #         "✅ Resource covers SQL (85% alignment)",
    #         "✅ BEGINNER difficulty matches your current level (1.8/5)",
    #         "✅ Required for Statistical Officer role",
    #         "⚠️ Prerequisites: TECH_BASICS (you have 2.0/5 - satisfied)"
    #     ],
    #     "next_steps": [
    #         "1. Enroll in this course",
    #         "2. Complete within 2 weeks",
    #         "3. Retake TECH_SQL assessment"
    #     ]
    # }


class RecommendationResponse(BaseModel):
    """Complete recommendation response."""
    
    user_id: str
    role_id: str
    generated_at: datetime
    
    summary: dict
    # {
    #     "total_gaps": 8,
    #     "urgent_gaps": 3,
    #     "recommendations_generated": 3,
    #     "gaps_addressed": 3,
    #     "estimated_learning_hours": 36
    # }
    
    recommendations: List[RecommendationItem]
```

---

## 9. INITIAL PROTOTYPE DATASET

### Target: Small, High-Quality Seed Data

**Do NOT aim for 50+ immediately.**

**Initial Target:**
- 20-30 iGOT courses (covering demo competencies)
- 10-15 NSSTA programmes (covering demo competencies)

**Demo Competencies to Cover:**
1. STAT_SAMPLING
2. TECH_SQL
3. TECH_PYTHON
4. STAT_DATA_QUALITY

**Sources:**
- iGOT: https://igot.gov.in (public catalog)
- NSSTA: MoSPI official TPAC directory

**Each Entry Must Have:**
- ✅ Official title
- ✅ Competency mapping (manual verification)
- ✅ Duration (hours)
- ✅ Difficulty (BEGINNER/INTERMEDIATE/ADVANCED)
- ✅ Target roles (if known)
- ✅ Source URL + verification date
- ❌ NOT: completion rates, ratings, engagement (don't invent)

**First Resources:**
- iGOT SQL Fundamentals → TECH_SQL
- iGOT Python Basics → TECH_PYTHON
- NSSTA Statistical Sampling → STAT_SAMPLING
- (Expand as engine proves itself)

---

## 10. DETERMINISTIC RANKING

### Guarantee: Same Input = Same Output

```python
def test_recommendation_determinism():
    """Verify recommendations are deterministic."""
    
    engine = RecommendationEngine(database)
    user_request = {
        "user_id": "demo-user",
        "skill_gaps": [...],
        "preferred_providers": ["IGOT", "NSSTA"],
    }
    
    # Same input, different calls
    rec1 = engine.generate_recommendations(user_request)
    rec2 = engine.generate_recommendations(user_request)
    rec3 = engine.generate_recommendations(user_request)
    
    # Should be identical
    assert rec1 == rec2 == rec3
    
    # Same scores
    assert rec1[0]["score"] == rec2[0]["score"]
    
    # Same ranking order
    assert [r["resource_id"] for r in rec1] == \
           [r["resource_id"] for r in rec2]
```

**How:** No randomness in scoring. All inputs deterministic. Database queries consistent.

---

## 11. NO LLM IN RANKING

### Scoring: Pure Logic

```
Skill Gap → Competency Match + Priority + Role + Difficulty + Prerequisites
         ↓
    Deterministic Score (0.0-1.0)
         ↓
    Sorted Rank
         ↓
    Top N Recommendations
```

### Explanation: Optional LLM Later

```
After ranking is done and resources selected:

Option 1 (Round 1): Use template + score components
  "Your {gap_category} {competency} gap (current {level}/5, required {req}/5) can be 
   addressed by this {difficulty} {resource_type}. Content alignment: {match}%. 
   Duration: {hours} hours."

Option 2 (Phase 3.5+): Use LLM to paraphrase
  Same data → LLM → "Here's a natural explanation"
```

**Key:** Ranking is never LLM-based. Ranking is auditable.

---

## 12. TESTING REQUIREMENTS

### Minimum Test Coverage

```python
# Unit Tests
test_scoring_competency_match()      # 40% component
test_scoring_gap_priority()          # 25% component (reuse from gap engine)
test_scoring_role_match()            # 20% component
test_scoring_difficulty_match()      # 10% component
test_scoring_prerequisite_match()    # 5% component
test_combined_score_calculation()    # Full formula
test_score_determinism()             # Same input = same output

# Provider Tests
test_igot_provider_search()          # Find resources
test_nssta_provider_search()         # Find resources
test_provider_factory()              # Get correct provider
test_provider_fallback()             # One provider fails, other works

# Engine Tests
test_single_gap_recommendation()     # One gap → recommendations
test_multiple_gaps_recommendation()  # Multiple gaps → ranked recommendations
test_multi_gap_deduplication()       # Same resource, different gaps
test_no_gap_user()                   # User with no gaps → empty recommendation
test_no_matching_resources()         # Gap exists, no resources cover it
test_max_recommendations_limit()     # Respects max_recommendations parameter
test_gap_category_filtering()        # Only HIGH+CRITICAL by default
test_provider_filtering()            # Filter by preferred_provider

# Integration Tests
test_end_to_end_statistical_officer()  # Demo: Statistical Officer → recommendations
test_end_to_end_data_analyst()         # Demo: Data Analyst → recommendations
test_recommendation_response_schema()  # Response matches expected structure
test_unauthorized_user()               # Cross-user access prevented
test_missing_competency_profile()      # User without profile → graceful fail
test_unknown_metadata_handling()       # Missing duration/difficulty → neutral score
test_empty_resource_database()         # No resources → empty recommendation

# Regression Tests
test_all_139_existing_tests_pass()   # No breaking changes
test_skill_gap_engine_unchanged()    # Skill gaps still work
test_competency_profiles_unchanged() # Evidence system unchanged
```

**Target:** 20+ new tests, 139 existing pass = **159+ total**

---

## 13. IMPLEMENTATION ORDER

### Week 1: Foundation

```
PHASE_1: Audit & Design (COMPLETE)
  ✓ Data model finalized
  ✓ Scoring formula finalized
  ✓ Provider abstraction finalized

PHASE_2: Collections & Indexes
  □ Create learning_resources collection
  □ Create learning_resource_mappings collection
  □ Create user_learning_history collection
  □ Add MongoDB indexes
  □ Create Pydantic schemas

PHASE_3: Seed Prototype Data
  □ Manually research 20-30 iGOT resources
  □ Manually research 10-15 NSSTA resources
  □ Create entries in learning_resources
  □ Create mappings in learning_resource_mappings
  □ Verify all data is factual (no invented data)

PHASE_4: Tests (Unit)
  □ Test each scoring component
  □ Test combined formula
  □ Test determinism
```

### Week 2: Engine & API

```
PHASE_5: Provider Implementation
  □ Create LearningResourceProvider abstract class
  □ Implement PrototypeIGOTProvider
  □ Implement PrototypeNSSTAProvider
  □ Create ProviderFactory
  □ Write provider unit tests

PHASE_6: Recommendation Engine
  □ Create RecommendationEngine class
  □ Implement find_candidates_for_gap()
  □ Implement _score_candidate()
  □ Implement generate_recommendations()
  □ Handle multiple gaps
  □ Handle deduplication
  □ Write engine integration tests

PHASE_7: API Endpoints
  □ GET /api/v1/recommendations/me
  □ GET /api/v1/learning-resources
  □ GET /api/v1/learning-resources/{resource_id}
  □ Add JWT authentication
  □ Add user ownership validation
  □ Write E2E tests
```

### Week 3: Verification

```
PHASE_8: Full Testing
  □ Run all 20+ new tests
  □ Run all 139 existing tests (verify no regressions)
  □ E2E: Demonstrate recommendation flow for demo users
  □ Document scoring decisions

PHASE_9: Final Verification
  □ Verify determinism (same user, multiple calls)
  □ Verify deduplication (no duplicate recommendations)
  □ Verify multi-gap support (3+ gaps handled correctly)
  □ Verify unknown data handling (missing fields = neutral, not invented)
  □ Document implementation decisions
  □ Generate recommendations for Statistical Officer + Data Analyst examples
```

---

## 14. SUCCESS CRITERIA

### Must Have ✅

- [ ] 159+ total tests passing (139 existing + 20 new)
- [ ] Deterministic recommendations (same input = same output)
- [ ] Multi-gap support (users with 2+ gaps)
- [ ] No invented metadata (unknown = neutral, not optimistic)
- [ ] Auditable scoring (each component transparent)
- [ ] Provider abstraction (ready for live APIs)
- [ ] Small prototype dataset (20-30 iGOT + 10-15 NSSTA)

### Must NOT Have ❌

- [ ] Engagement metrics (round 1 only uses 5 components)
- [ ] Fake completion rates or ratings
- [ ] Live API calls (prototype only)
- [ ] LLM-based ranking
- [ ] Breaking changes to existing systems
- [ ] Invented metadata (prerequisite, difficulty, target_roles)

### Deliverables

1. **Code:**
   - `app/learning_resources/models.py` → Schemas
   - `app/learning_resources/repository.py` → CRUD
   - `app/learning_resources/providers/base.py` → Abstract provider
   - `app/learning_resources/providers/igot_provider.py` → IGOT
   - `app/learning_resources/providers/nssta_provider.py` → NSSTA
   - `app/recommendations/engine.py` → Recommendation engine
   - `app/recommendations/router.py` → API endpoints
   - `app/recommendations/schemas.py` → Response schemas

2. **Data:**
   - 20-30 iGOT courses (learning_resources + mappings)
   - 10-15 NSSTA programmes (learning_resources + mappings)

3. **Tests:**
   - `tests/test_recommendations_engine.py` → Unit + integration
   - `tests/test_recommendations_api.py` → E2E
   - `tests/test_provider_factory.py` → Provider tests

4. **Documentation:**
   - Implementation decisions
   - Scoring formula justification
   - Example recommendations (Statistical Officer + Data Analyst)
   - Final verification report

---

## ARCHITECTURE FINALIZED ✅

Ready for Week 1 implementation.

**Next:** Begin collection creation and prototype data seeding.

