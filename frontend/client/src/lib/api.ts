const API_BASE = import.meta.env.VITE_API_URL || "/api/v1";

export class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
  }
}

export type User = {
  id: string; email: string; full_name: string; role_id: string;
  designation: string; department: string; employee_id: string;
  status: string; access_role: "EMPLOYEE" | "ADMIN";
};

export type Competency = {
  id: string; code: string; name: string; domain: string;
  description: string; level_definitions: Record<string, string> | string[];
};

export type AssessmentQuestion = {
  question_id: string; competency_id: string; question_type: "SELF_RATING" | "MCQ" | "SCENARIO";
  question_text: string; options: string[]; scenario_context?: string | null;
};

export type AssessmentAttempt = {
  id: string; assessment_id: string; status: "IN_PROGRESS" | "SUBMITTED";
  questions: AssessmentQuestion[]; competency_results: { competency_id: string; score: number; confidence: number }[];
};

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const token = localStorage.getItem("shikshasetu_token");
  const isFormData = init.body instanceof FormData;
  const response = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: { ...(isFormData ? {} : { "Content-Type": "application/json" }), ...(token ? { Authorization: `Bearer ${token}` } : {}), ...(init.headers || {}) },
  });
  const body = await response.json().catch(() => ({}));
  if (!response.ok) {
    if (response.status === 401) localStorage.removeItem("shikshasetu_token");
    throw new ApiError(response.status, body.detail || "Request failed");
  }
  return body as T;
}

export const api = {
  login: (payload: { email: string; password: string }) => request<{ access_token: string; user: User }>("/auth/login", { method: "POST", body: JSON.stringify(payload) }),
  register: (payload: Record<string, unknown>) => request<User>("/auth/register", { method: "POST", body: JSON.stringify(payload) }),
  me: () => request<User>("/auth/me"),
  updateProfile: (payload: Record<string, string>) => request<User>("/users/me", { method: "PUT", body: JSON.stringify(payload) }),
  competencies: () => request<Competency[]>("/competencies"),
  roles: () => request<any[]>("/roles"),
  requirements: (roleId: string) => request<any[]>(`/roles/${roleId}/requirements`),
  skillGaps: () => request<any>("/skill-gaps/me"),
  recommendations: () => request<any>("/recommendations/me"),
  competencyResources: (competencyCode: string) => request<any>(`/recommendations/competencies/${encodeURIComponent(competencyCode)}/resources`),
  uploadMaterial: (file: File) => { const form = new FormData(); form.append("file", file); return request<any>("/learning-materials/upload", { method: "POST", body: form }); },
  material: (materialId: string) => request<any>(`/learning-materials/${materialId}`),
  generateQuestions: (materialId: string, payload: { competency_code: string; question_count: number; difficulty?: string }) => request<any>(`/learning-materials/${materialId}/generate-questions`, { method: "POST", body: JSON.stringify(payload) }),
  createQuiz: (payload: any) => request<any>("/quizzes", { method: "POST", body: JSON.stringify(payload) }),
  quiz: (quizId: string) => request<any>(`/quizzes/${quizId}`),
  submitQuiz: (quizId: string, answers: { question_id: string; selected_answer: string }[]) => request<any>(`/quizzes/${quizId}/submit`, { method: "POST", body: JSON.stringify({ answers }) }),
  startAssessment: (assessment_key = "initial-competency-v1") => request<AssessmentAttempt>("/assessments", { method: "POST", body: JSON.stringify({ assessment_key }) }),
  getAttempt: (id: string) => request<AssessmentAttempt>(`/assessments/${id}`),
  submitAssessment: (id: string, payload: unknown) => request<any>(`/assessments/${id}/submit`, { method: "POST", body: JSON.stringify(payload) }),
};