"""Schemas for Admin organizational intelligence endpoints."""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


# ─── Dashboard ───────────────────────────────────────────────────────────────

class MetricCard(BaseModel):
    label: str
    value: Any
    change: Optional[str] = None
    subtext: Optional[str] = None
    trend: Optional[str] = None


class AdminDashboardResponse(BaseModel):
    total_officials: int
    total_trainers: int
    total_users: int
    active_users: int
    average_capability_level: float
    total_critical_gaps: int
    total_learning_hours: float
    assessment_coverage_pct: float
    total_quizzes_assigned: int
    total_quiz_attempts: int
    average_quiz_score_pct: float
    departments_count: int
    competencies_count: int
    department_distribution: List[Dict[str, Any]]
    domain_capability_breakdown: List[Dict[str, Any]]
    recent_activity: List[Dict[str, Any]]


# ─── Workforce Overview ──────────────────────────────────────────────────────

class WorkforceEmployeeItem(BaseModel):
    id: str
    full_name: str
    email: str
    employee_id: str
    department: str
    designation: str
    professional_role: str
    access_role: str
    status: str
    assessed_competencies: int
    average_proficiency: Optional[float] = None
    last_assessment_at: Optional[datetime] = None


class WorkforceOverviewResponse(BaseModel):
    total_workforce: int
    department_breakdown: List[Dict[str, Any]]
    role_breakdown: List[Dict[str, Any]]
    domain_proficiency_distribution: List[Dict[str, Any]]
    proficiency_tier_distribution: Dict[str, int]
    employees: List[WorkforceEmployeeItem]


# ─── Competency Analytics ────────────────────────────────────────────────────

class CompetencyAnalyticsItem(BaseModel):
    competency_id: str
    code: str
    name: str
    domain: str
    required_roles_count: int
    average_required_level: float
    average_current_level: float
    average_gap: float
    assessed_officials_count: int
    meeting_requirement_pct: float
    critical_deficits_count: int
    priority: str


class CompetencyAnalyticsResponse(BaseModel):
    total_competencies: int
    domain_breakdown: List[Dict[str, Any]]
    competencies: List[CompetencyAnalyticsItem]


# ─── Skill Gap Analytics ─────────────────────────────────────────────────────

class OrganizationGapItem(BaseModel):
    competency_id: str
    competency_code: str
    competency_name: str
    domain: str
    officials_affected: int
    critical_count: int
    high_count: int
    medium_count: int
    low_count: int
    average_gap: float
    priority: str


class SkillGapAnalyticsResponse(BaseModel):
    total_gaps_identified: int
    critical_gaps_count: int
    high_gaps_count: int
    medium_gaps_count: int
    low_gaps_count: int
    domain_gap_distribution: List[Dict[str, Any]]
    department_gap_distribution: List[Dict[str, Any]]
    top_organization_gaps: List[OrganizationGapItem]


# ─── Training Effectiveness ──────────────────────────────────────────────────

class TrainingEffectivenessResponse(BaseModel):
    total_enrolled_activities: int
    total_completed_activities: int
    overall_completion_rate_pct: float
    total_learning_minutes: int
    total_learning_hours: float
    supporting_evidence_count: int
    authoritative_evidence_count: int
    total_quizzes_created: int
    total_quizzes_assigned: int
    total_quiz_submissions: int
    average_quiz_score_pct: float
    completion_by_department: List[Dict[str, Any]]
    evidence_ledger_breakdown: Dict[str, int]
    training_to_assessment_funnel: Dict[str, Any]


# ─── Emerging Skills ─────────────────────────────────────────────────────────

class EmergingSkillItem(BaseModel):
    competency_id: str
    code: str
    name: str
    domain: str
    officials_in_deficit: int
    average_gap_size: Optional[float] = None
    average_current_level: Optional[float] = None
    average_required_level: Optional[float] = None
    rationale: str
    recommended_focus: str


class EmergingSkillsResponse(BaseModel):
    strategic_focus_domains: List[str]
    emerging_capabilities: List[EmergingSkillItem]
    historical_trend_available: bool
    data_basis: str


# ─── Capacity Planning ───────────────────────────────────────────────────────

class CapacityInterventionItem(BaseModel):
    competency_code: str
    competency_name: str
    domain: str
    priority: str
    target_officials_count: int
    estimated_training_hours: Optional[float] = None
    recommended_courses_count: int
    top_resource_title: Optional[str] = None
    top_resource_provider: Optional[str] = None
    suggested_cohort_size: Optional[int] = None


class CapacityPlanningResponse(BaseModel):
    total_training_hours_required: Optional[float] = None
    total_officials_requiring_intervention: int
    high_priority_initiatives_count: int
    interventions: List[CapacityInterventionItem]
    data_basis: str


# ─── User Directory ──────────────────────────────────────────────────────────

class AdminUserItem(BaseModel):
    id: str
    email: str
    full_name: str
    employee_id: str
    department: str
    designation: str
    access_role: str
    professional_role: str
    status: str
    created_at: datetime
    last_login_at: Optional[datetime] = None


class AdminUserListResponse(BaseModel):
    total: int
    users: List[AdminUserItem]


class AdminCapabilityItem(BaseModel):
    competency_code: str
    competency_name: str
    domain: str
    current_level: Optional[float] = None
    required_level: float
    gap: float
    gap_category: str


class AdminLearningActivityItem(BaseModel):
    activity_id: str
    resource_id: str
    resource_title: Optional[str] = None
    provider: Optional[str] = None
    competency_id: str
    status: str
    progress_percent: float
    started_at: Optional[datetime] = None
    last_accessed_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_minutes: float = 0


class AdminAssessmentItem(BaseModel):
    assessment_id: str
    assessment_type: str
    competency_code: Optional[str] = None
    status: Optional[str] = None
    score: Optional[float] = None
    percentage: Optional[float] = None
    assessed_at: Optional[datetime] = None
    authoritative: bool = False


class AdminEvidenceItem(BaseModel):
    evidence_id: str
    evidence_type: str
    competency_code: Optional[str] = None
    confidence: Optional[float] = None
    source: Optional[str] = None
    recorded_at: Optional[datetime] = None


class AdminWorkforceProfileResponse(BaseModel):
    user: AdminUserItem
    capabilities: List[AdminCapabilityItem] = Field(default_factory=list)
    active_gaps: List[AdminCapabilityItem] = Field(default_factory=list)
    learning_summary: Dict[str, Any]
    learning_activities: List[AdminLearningActivityItem] = Field(default_factory=list)
    assessments: List[AdminAssessmentItem] = Field(default_factory=list)
    evidence_summary: Dict[str, Any]
    evidence: List[AdminEvidenceItem] = Field(default_factory=list)
    timeline: List[Dict[str, Any]] = Field(default_factory=list)


# ─── Reports ─────────────────────────────────────────────────────────────────

class AdminReportsResponse(BaseModel):
    generated_at: datetime
    workforce_summary: Dict[str, Any]
    skill_gap_summary: Dict[str, Any]
    training_summary: Dict[str, Any]
    compliance_summary: Dict[str, Any]


class AdminAssignRoleRequest(BaseModel):
    role_id: str
    department: Optional[str] = None
    designation: Optional[str] = None


# ─── Workforce Intelligence & Talent Discovery ──────────────────────────────

class WorkforceIntelligenceResponse(BaseModel):
    filters: Dict[str, Any] = Field(default_factory=dict)
    overview: Dict[str, Any] = Field(default_factory=dict)
    competency_intelligence: Dict[str, Any] = Field(default_factory=dict)
    department_analysis: List[Dict[str, Any]] = Field(default_factory=list)
    training_effectiveness: Dict[str, Any] = Field(default_factory=dict)
    trends: Dict[str, Any] = Field(default_factory=dict)


class TalentDiscoveryResponse(BaseModel):
    filters: Dict[str, Any] = Field(default_factory=dict)
    page: int
    limit: int
    total: int
    results: List[Dict[str, Any]] = Field(default_factory=list)
    data_basis: str
