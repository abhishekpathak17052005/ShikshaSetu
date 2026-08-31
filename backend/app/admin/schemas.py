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
    urgency_score: float
    demand_index: int
    officials_in_deficit: int
    average_gap_size: float
    rationale: str
    recommended_focus: str


class EmergingSkillsResponse(BaseModel):
    strategic_focus_domains: List[str]
    emerging_capabilities: List[EmergingSkillItem]


# ─── Capacity Planning ───────────────────────────────────────────────────────

class CapacityInterventionItem(BaseModel):
    competency_code: str
    competency_name: str
    domain: str
    priority: str
    target_officials_count: int
    estimated_training_hours: float
    recommended_courses_count: int
    top_resource_title: Optional[str] = None
    top_resource_provider: Optional[str] = None
    suggested_cohort_size: int


class CapacityPlanningResponse(BaseModel):
    total_training_hours_required: float
    total_officials_requiring_intervention: int
    high_priority_initiatives_count: int
    interventions: List[CapacityInterventionItem]


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


# ─── Reports ─────────────────────────────────────────────────────────────────

class AdminReportsResponse(BaseModel):
    generated_at: datetime
    workforce_summary: Dict[str, Any]
    skill_gap_summary: Dict[str, Any]
    training_summary: Dict[str, Any]
    compliance_summary: Dict[str, Any]
