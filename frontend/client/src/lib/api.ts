// Full unified API client for ShikshaSetu
// Token key: "shikshasetu_token"
// Base URL: import.meta.env.VITE_API_URL || "/api/v1"

const API_BASE = import.meta.env.VITE_API_URL || "/api/v1";

export class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
  }
}

// ─── User & Auth ────────────────────────────────────────────────────────────

export type User = {
  id: string;
  email: string;
  full_name: string;
  role_id: string;
  designation: string;
  department: string;
  employee_id: string;
  status: string;
  access_role: "OFFICIAL" | "TRAINER" | "ADMIN" | "EMPLOYEE";
};

export type Role = {
  id: string;
  role_name: string;
  role_code: string;
  department: string;
  level: string;
  description: string;
};

export type RoleRequirement = {
  id: string;
  role_id: string;
  competency_id: string;
  required_level: number;
  priority: "CRITICAL" | "HIGH" | "MEDIUM" | "LOW";
  competency?: Competency;
};

// ─── Competencies ───────────────────────────────────────────────────────────

export type Competency = {
  id: string;
  code: string;
  name: string;
  domain: string;
  description: string;
  level_definitions: Record<string, string> | string[];
};

// ─── Skill Gaps ─────────────────────────────────────────────────────────────

export type SkillGap = {
  competency_id: string;
  competency_code: string;
  competency_name: string;
  competency_domain: string;
  required_level: number;
  current_level: number | null;
  gap: number;
  gap_category: "CRITICAL" | "HIGH" | "MEDIUM" | "LOW" | "MET" | "UNKNOWN";
  priority: "CRITICAL" | "HIGH" | "MEDIUM" | "LOW";
  confidence: number | null;
  last_assessed: string | null;
};

export type SkillGapResponse = {
  gaps: SkillGap[];
  summary: {
    role: string;
    required_competencies: number;
    assessed_count: number;
    not_assessed_count: number;
    critical_gaps: number;
    high_gaps: number;
    medium_gaps: number;
    met_count: number;
  };
  role: string;
};

// ─── Recommendations ────────────────────────────────────────────────────────

export type Recommendation = {
  id: string;
  user_id: string;
  competency_id: string;
  competency_code: string;
  competency_name: string;
  resource_type: string;
  resource_title: string;
  resource_url: string;
  provider: string;
  duration_hours: number | null;
  relevance_score: number;
  reason: string;
  priority: "CRITICAL" | "HIGH" | "MEDIUM" | "LOW";
  status: string;
  created_at: string;
};

export type RecommendationResponse = {
  recommendations: Recommendation[];
  total: number;
  by_competency: Record<string, Recommendation[]>;
};

// ─── Assessments ────────────────────────────────────────────────────────────

export type AssessmentQuestion = {
  question_id: string;
  competency_id: string;
  question_type: "SELF_RATING" | "MCQ" | "SCENARIO";
  question_text: string;
  options: string[];
  scenario_context?: string | null;
};

export type AssessmentAttempt = {
  id: string;
  assessment_id: string;
  status: "IN_PROGRESS" | "SUBMITTED";
  questions: AssessmentQuestion[];
  competency_results: {
    competency_id: string;
    score: number;
    confidence: number;
  }[];
};

export type AssessmentSubmitResponse = {
  attempt_id: string;
  status: string;
  competency_results: {
    competency_id: string;
    competency_code: string;
    level: number;
    confidence: number;
  }[];
  gaps_updated: boolean;
  recommendations_generated: boolean;
};

export type CapabilityAssessmentQuestion = {
  question_id: string;
  question_type: string;
  question_text: string;
  options: string[];
  difficulty: string;
  weight?: number;
  scenario_context?: string | null;
};

export type CapabilityAssessment = {
  id: string;
  competency_code: string;
  assessment_type: string;
  title: string;
  questions: CapabilityAssessmentQuestion[];
  status: string;
  started_at: string;
  submitted_at?: string | null;
  score?: number | null;
  percentage?: number | null;
  normalized_score?: number | null;
  duration_seconds?: number | null;
};

export type CapabilityAssessmentSubmitResponse = {
  assessment_id: string;
  competency_code: string;
  status: string;
  score: number;
  percentage: number;
  normalized_score: number;
  competency_results: {
    competency_code: string;
    score: number;
    confidence: number;
  }[];
  submitted_at: string;
};

export type CapabilityAssessmentResultsResponse = {
  assessment_id: string;
  competency_code: string;
  status: string;
  score: number;
  percentage: number;
  normalized_score: number;
  duration_seconds?: number | null;
  correct_answers: number;
  total_questions: number;
  competency_results: {
    competency_code: string;
    score: number;
    confidence: number;
  }[];
  submitted_at: string;
  started_at: string;
};

export type CapabilityAssessmentListItem = {
  id: string;
  competency_code: string;
  title: string;
  status: string;
  score?: number | null;
  percentage?: number | null;
  started_at: string;
  submitted_at?: string | null;
};

export type CompetencyEvidence = {
  id: string;
  _id?: string;
  user_id?: string;
  evidence_type: "LEARNING_ACTIVITY" | "CAPABILITY_ASSESSMENT" | "AI_QUIZ" | string;
  confidence: number;
  competency_code: string;
  score?: number;
  created_at: string;
  source_id?: string;
  details?: any;
  notes?: string;
};

// ─── Learning Activities ─────────────────────────────────────────────────────

export type LearningActivity = {
  activity_id: string;
  user_id: string;
  resource_id: string;
  competency_id: string;
  status: "not_started" | "in_progress" | "completed" | "abandoned";
  progress_percent: number;
  duration_minutes: number;
  started_at: string | null;
  completed_at: string | null;
  last_accessed_at: string | null;
  notes: string | null;
};

export type LearningActivityListResponse = {
  activities: LearningActivity[];
  total_count: number;
};

export type LearningActivityCompleteResponse = {
  activity: LearningActivity;
  evidence_created: boolean;
  evidence_id: string | null;
  evidence_type: string | null;
  evidence_confidence: number | null;
  note: string;
  current_competency_level: number | null;
  current_skill_gap: number | null;
  next_step: string | null;
};

// ─── Learning Materials ──────────────────────────────────────────────────────

export type LearningMaterial = {
  id: string;
  original_filename: string;
  filename: string;
  status: string;
  chunk_count: number;
  embedding_count: number;
  extraction_status: string;
  created_at: string;
};

// ─── Trainer Types ───────────────────────────────────────────────────────────

export type QuestionReviewStatus = "GENERATED" | "EDITED" | "APPROVED" | "REJECTED";
export type TrainerQuizStatus = "DRAFT" | "PUBLISHED" | "ASSIGNED" | "CLOSED" | "ARCHIVED";

export type TrainerQuestion = {
  id: string;
  _id?: string;
  question_id?: string;
  trainer_id?: string;
  material_id?: string;
  question: string;
  options: string[];
  correct_answer: string;
  explanation: string;
  difficulty?: string;
  competency_code: string;
  status: QuestionReviewStatus;
  review_notes?: string | null;
  source_chunks?: string[];
  created_at?: string;
  updated_at?: string;
};

export type TrainerQuiz = {
  id: string;
  _id?: string;
  quiz_id?: string;
  trainer_id?: string;
  title: string;
  description?: string;
  material_id?: string;
  competency_code: string;
  questions?: TrainerQuestion[];
  question_count?: number;
  assigned_learners_count?: number;
  attempts_count?: number;
  average_score?: number | null;
  status: TrainerQuizStatus | "DRAFT" | "PUBLISHED";
  created_at?: string;
  published_at?: string | null;
};

export type TrainerDashboard = {
  materials_count: number;
  questions_count?: number;
  generated_questions_count?: number;
  pending_review_count?: number;
  pending_questions_count?: number;
  approved_questions_count: number;
  rejected_questions_count?: number;
  quizzes_count?: number;
  published_quizzes_count: number;
  assigned_quizzes_count?: number;
  total_assigned_learners?: number;
  total_attempts_evaluated?: number;
  learner_attempts_count?: number;
  average_score_all_quizzes?: number | null;
};

export type QuizAssignment = {
  assignment_id?: string;
  quiz_id: string;
  assigned_to?: string[];
  assigned_learners_count?: number;
  status?: string;
  message?: string;
  assigned_at?: string;
};

export type AssignedQuiz = {
  quiz_id: string;
  title: string;
  description: string;
  question_count: number;
  status: "NOT_STARTED" | "IN_PROGRESS" | "COMPLETED";
  assigned_at: string;
  trainer_name: string;
};

export type TrainerLearnerAttempt = {
  attempt_id: string;
  _id?: string;
  quiz_id: string;
  quiz_title: string;
  learner_id: string;
  learner_name: string;
  learner_email: string;
  score: number;
  percentage: number;
  correct_count: number;
  total_questions: number;
  competency_code: string;
  submitted_at: string;
  has_trainer_feedback: boolean;
  trainer_feedback?: {
    feedback_text: string;
    strengths?: string[];
    areas_for_improvement?: string[];
    rating?: number | null;
    evaluated_at?: string;
  } | null;
};

export type QuizAttemptResult = {
  attempt_id: string;
  quiz_id: string;
  score: number;
  correct_count: number;
  total_questions: number;
  percentage: number;
  completed_at: string;
  questions_with_feedback: {
    question_id: string;
    question: string;
    selected_answer: string;
    correct_answer: string;
    is_correct: boolean;
    explanation: string;
  }[];
};

// ─── HTTP helper ─────────────────────────────────────────────────────────────

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const token = localStorage.getItem("shikshasetu_token");
  const isFormData = init.body instanceof FormData;

  const response = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: {
      ...(isFormData ? {} : { "Content-Type": "application/json" }),
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...(init.headers || {}),
    },
  });

  const body = await response.json().catch(() => ({}));

  if (!response.ok) {
    if (response.status === 401) {
      localStorage.removeItem("shikshasetu_token");
    }
    throw new ApiError(response.status, body.detail || "Request failed");
  }

  return body as T;
}

// ─── API surface ──────────────────────────────────────────────────────────────

export const api = {
  // Auth
  auth: {
    login: (payload: { email: string; password: string }) =>
      request<{ access_token: string; user: User }>("/auth/login", {
        method: "POST",
        body: JSON.stringify(payload),
      }),
    register: (payload: Record<string, unknown>) =>
      request<User>("/auth/register", {
        method: "POST",
        body: JSON.stringify(payload),
      }),
    me: () => request<User>("/auth/me"),
    updateProfile: (payload: Record<string, string>) =>
      request<User>("/users/me", {
        method: "PUT",
        body: JSON.stringify(payload),
      }),
  },

  // Competencies
  competencies: {
    list: () => request<Competency[]>("/competencies"),
    get: (id: string) => request<Competency>(`/competencies/${id}`),
  },

  // Roles
  roles: {
    list: () => request<Role[]>("/roles"),
    getRequirements: (roleId: string) =>
      request<RoleRequirement[]>(`/roles/${roleId}/requirements`),
  },

  // Skill Gaps
  skillGaps: {
    me: () => request<SkillGapResponse>("/skill-gaps/me"),
  },

  // Recommendations
  recommendations: {
    me: () => request<RecommendationResponse>("/recommendations/me"),
    byCompetency: (competencyCode: string) =>
      request<Recommendation[]>(
        `/recommendations/competencies/${encodeURIComponent(competencyCode)}/resources`
      ),
  },

  // Learning Activities
  learningActivities: {
    start: (payload: {
      resource_id: string;
      competency_id: string;
    }) =>
      request<LearningActivity>("/learning-activities", {
        method: "POST",
        body: JSON.stringify(payload),
      }),
    list: (status?: string) =>
      request<LearningActivityListResponse>(
        `/learning-activities${status ? `?status=${status}` : ""}`
      ),
    get: (activityId: string) =>
      request<LearningActivity>(`/learning-activities/${activityId}`),
    update: (
      activityId: string,
      payload: {
        progress_percent?: number;
        duration_minutes?: number;
        notes?: string;
      }
    ) =>
      request<LearningActivity>(`/learning-activities/${activityId}`, {
        method: "PUT",
        body: JSON.stringify(payload),
      }),
    complete: (
      activityId: string,
      payload?: { final_score?: number; notes?: string }
    ) =>
      request<LearningActivityCompleteResponse>(
        `/learning-activities/${activityId}/complete`,
        {
          method: "POST",
          body: JSON.stringify(payload || {}),
        }
      ),
  },

  // Learning Materials
  learningMaterials: {
    upload: (file: File) => {
      const form = new FormData();
      form.append("file", file);
      return request<LearningMaterial>("/learning-materials/upload", {
        method: "POST",
        body: form,
      });
    },
    get: (materialId: string) =>
      request<LearningMaterial>(`/learning-materials/${materialId}`),
  },

  // Assessments (Baseline / General)
  assessments: {
    start: (assessment_key = "initial-competency-v1") =>
      request<AssessmentAttempt>("/assessments", {
        method: "POST",
        body: JSON.stringify({ assessment_key }),
      }),
    get: (id: string) => request<AssessmentAttempt>(`/assessments/${id}`),
    submit: (id: string, payload: unknown) =>
      request<AssessmentSubmitResponse>(`/assessments/${id}/submit`, {
        method: "POST",
        body: JSON.stringify(payload),
      }),
  },

  // Capability Assessments (Authoritative Competency Evidence)
  capabilityAssessments: {
    create: (payload: { competency_code: string }) =>
      request<CapabilityAssessment>(
        "/assessments/capability",
        { method: "POST", body: JSON.stringify(payload) }
      ),
    get: (id: string) =>
      request<CapabilityAssessment>(`/assessments/capability/${id}`),
    submit: (
      id: string,
      payload: { answers: { question_id: string; selected_answer: string }[] }
    ) =>
      request<CapabilityAssessmentSubmitResponse>(
        `/assessments/capability/${id}/submit`,
        {
          method: "POST",
          body: JSON.stringify(payload),
        }
      ),
    getResults: (id: string) =>
      request<CapabilityAssessmentResultsResponse>(
        `/assessments/capability/${id}/results`
      ),
    list: (competency_code?: string, status_filter?: string) => {
      const params = new URLSearchParams();
      if (competency_code) params.append("competency_code", competency_code);
      if (status_filter) params.append("status_filter", status_filter);
      const q = params.toString();
      return request<CapabilityAssessmentListItem[]>(
        `/assessments/capability${q ? `?${q}` : ""}`
      );
    },
  },

  // Quizzes (official/learner side)
  quizzes: {
    assigned: () => request<AssignedQuiz[]>("/quizzes/assigned"),
    get: (quizId: string) => request<TrainerQuiz>(`/quizzes/${quizId}`),
    submit: (
      quizId: string,
      answers: { question_id: string; selected_answer: string }[]
    ) =>
      request<QuizAttemptResult>(`/quizzes/${quizId}/submit`, {
        method: "POST",
        body: JSON.stringify({ answers }),
      }),
  },

  // Trainer namespace
  trainer: {
    dashboard: () => request<TrainerDashboard>("/trainer/dashboard"),

    materials: {
      list: () => request<LearningMaterial[]>("/trainer/materials"),
      get: (materialId: string) =>
        request<LearningMaterial>(`/learning-materials/${materialId}`),
      upload: async (file: File) => {
        const token = localStorage.getItem("shikshasetu_token");
        const headers: Record<string, string> = {};
        if (token) headers["Authorization"] = `Bearer ${token}`;
        const formData = new FormData();
        formData.append("file", file);
        const res = await fetch(`${API_BASE}/learning-materials/upload`, {
          method: "POST",
          headers,
          body: formData,
        });
        if (!res.ok) {
          const err = await res.json().catch(() => ({ detail: res.statusText }));
          throw new ApiError(res.status, err.detail || "Upload failed");
        }
        return res.json() as Promise<LearningMaterial>;
      },
      generateQuestions: (
        materialId: string,
        payload: {
          competency_code: string;
          question_count: number;
          difficulty?: string;
        }
      ) =>
        request<TrainerQuestion[]>(
          `/trainer/materials/${materialId}/generate`,
          { method: "POST", body: JSON.stringify(payload) }
        ),
      getQuestions: (materialId: string, status?: string) =>
        request<TrainerQuestion[]>(
          `/trainer/materials/${materialId}/questions${status ? `?status=${status}` : ""}`
        ),
    },

    questions: {
      get: (questionId: string) =>
        request<TrainerQuestion>(`/trainer/questions/${questionId}`),
      update: (
        questionId: string,
        payload: {
          question?: string;
          options?: string[];
          correct_answer?: string;
          explanation?: string;
        }
      ) =>
        request<TrainerQuestion>(`/trainer/questions/${questionId}`, {
          method: "PUT",
          body: JSON.stringify(payload),
        }),
      approve: (questionId: string) =>
        request<TrainerQuestion>(`/trainer/questions/${questionId}/approve`, {
          method: "POST",
        }),
      reject: (
        questionId: string,
        payload: { action?: string; review_notes: string }
      ) =>
        request<TrainerQuestion>(`/trainer/questions/${questionId}/reject`, {
          method: "POST",
          body: JSON.stringify({ action: "REJECT", review_notes: payload.review_notes }),
        }),
    },

    quizzes: {
      create: (payload: {
        title: string;
        description?: string;
        material_id?: string;
        competency_code: string;
        question_ids: string[];
      }) =>
        request<TrainerQuiz>("/trainer/quizzes", {
          method: "POST",
          body: JSON.stringify(payload),
        }),
      list: () => request<TrainerQuiz[]>("/trainer/quizzes"),
      get: (quizId: string) =>
        request<TrainerQuiz>(`/trainer/quizzes/${quizId}`),
      publish: (quizId: string) =>
        request<TrainerQuiz>(`/trainer/quizzes/${quizId}/publish`, {
          method: "POST",
        }),
      assign: (quizId: string, payload: { learner_ids: string[] }) =>
        request<QuizAssignment>(`/trainer/quizzes/${quizId}/assign`, {
          method: "POST",
          body: JSON.stringify(payload),
        }),
      getAttempts: (quizId: string) =>
        request<TrainerLearnerAttempt[]>(`/trainer/quizzes/${quizId}/attempts`),
    },

    attempts: {
      submitFeedback: (
        attemptId: string,
        payload: {
          feedback_text: string;
          strengths?: string[];
          areas_for_improvement?: string[];
          rating?: number;
        }
      ) =>
        request<{ attempt_id: string; message: string; trainer_feedback: any }>(
          `/trainer/attempts/${attemptId}/feedback`,
          {
            method: "POST",
            body: JSON.stringify(payload),
          }
        ),
    },

    learners: {
      list: () => request<User[]>("/trainer/learners"),
    },
  },

  // ── Legacy flat aliases kept for backwards-compat with LiveHome.tsx ──────
  /** @deprecated use api.auth.login */
  login: (payload: { email: string; password: string }) =>
    request<{ access_token: string; user: User }>("/auth/login", {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  /** @deprecated use api.auth.register */
  register: (payload: Record<string, unknown>) =>
    request<User>("/auth/register", {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  /** @deprecated use api.auth.me */
  me: () => request<User>("/auth/me"),
  /** @deprecated use api.auth.updateProfile */
  updateProfile: (payload: Record<string, string>) =>
    request<User>("/users/me", { method: "PUT", body: JSON.stringify(payload) }),
  /** @deprecated use api.roles.getRequirements */
  requirements: (roleId: string) =>
    request<RoleRequirement[]>(`/roles/${roleId}/requirements`),
  /** @deprecated use api.recommendations.byCompetency */
  competencyResources: (competencyCode: string) =>
    request<Recommendation[]>(
      `/recommendations/competencies/${encodeURIComponent(competencyCode)}/resources`
    ),
  /** @deprecated use api.learningMaterials.upload */
  uploadMaterial: (file: File) => {
    const form = new FormData();
    form.append("file", file);
    return request<LearningMaterial>("/learning-materials/upload", {
      method: "POST",
      body: form,
    });
  },
  /** @deprecated use api.learningMaterials.get */
  material: (materialId: string) =>
    request<LearningMaterial>(`/learning-materials/${materialId}`),
  /** @deprecated use api.trainer.quizzes.create */
  createQuiz: (payload: any) =>
    request<TrainerQuiz>("/trainer/quizzes", {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  /** @deprecated use api.quizzes.get */
  quiz: (quizId: string) => request<TrainerQuiz>(`/quizzes/${quizId}`),
  /** @deprecated use api.quizzes.submit */
  submitQuiz: (
    quizId: string,
    answers: { question_id: string; selected_answer: string }[]
  ) =>
    request<QuizAttemptResult>(`/quizzes/${quizId}/submit`, {
      method: "POST",
      body: JSON.stringify({ answers }),
    }),
  /** @deprecated use api.assessments.start */
  startAssessment: (assessment_key = "initial-competency-v1") =>
    request<AssessmentAttempt>("/assessments", {
      method: "POST",
      body: JSON.stringify({ assessment_key }),
    }),
  /** @deprecated use api.assessments.get */
  getAttempt: (id: string) =>
    request<AssessmentAttempt>(`/assessments/${id}`),
  /** @deprecated use api.assessments.submit */
  submitAssessment: (id: string, payload: unknown) =>
    request<AssessmentSubmitResponse>(`/assessments/${id}/submit`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
};
