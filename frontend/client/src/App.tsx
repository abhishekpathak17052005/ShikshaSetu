import React, { useState, Suspense, lazy } from "react";
import { Toaster } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import ErrorBoundary from "./components/ErrorBoundary";
import { ThemeProvider } from "./contexts/ThemeContext";
import { AuthProvider, useAuth } from "./contexts/AuthContext";
import { LanguageProvider } from "./i18n";
import { TrainerLayout } from "./layouts/TrainerLayout";
import { AdminLayout } from "./layouts/AdminLayout";
import { OfficialLayout } from "./layouts/OfficialLayout";
import { PageSkeleton } from "./components/PageSkeleton";

// ─── Lazy Loaded Pages ─────────────────────────────────────────────────────────

// Auth
const LoginPage = lazy(() => import("./pages/LoginPage"));

// Trainer Pages
const TrainerDashboard = lazy(() =>
  import("./pages/trainer/TrainerDashboard").then((m) => ({ default: m.TrainerDashboard }))
);
const TrainerMaterials = lazy(() =>
  import("./pages/trainer/TrainerMaterials").then((m) => ({ default: m.TrainerMaterials }))
);
const TrainerQuestionGenerator = lazy(() =>
  import("./pages/trainer/TrainerQuestionGenerator").then((m) => ({ default: m.TrainerQuestionGenerator }))
);
const TrainerQuestionReview = lazy(() =>
  import("./pages/trainer/TrainerQuestionReview").then((m) => ({ default: m.TrainerQuestionReview }))
);
const TrainerQuizStudio = lazy(() =>
  import("./pages/trainer/TrainerQuizStudio").then((m) => ({ default: m.TrainerQuizStudio }))
);
const TrainerLearnerResults = lazy(() =>
  import("./pages/trainer/TrainerLearnerResults").then((m) => ({ default: m.TrainerLearnerResults }))
);

// Admin Pages
const AdminDashboard = lazy(() =>
  import("./pages/admin/AdminDashboard").then((m) => ({ default: m.AdminDashboard }))
);
const WorkforceOverview = lazy(() =>
  import("./pages/admin/WorkforceOverview").then((m) => ({ default: m.WorkforceOverview }))
);
const CompetencyAnalytics = lazy(() =>
  import("./pages/admin/CompetencyAnalytics").then((m) => ({ default: m.CompetencyAnalytics }))
);
const SkillGapAnalytics = lazy(() =>
  import("./pages/admin/SkillGapAnalytics").then((m) => ({ default: m.SkillGapAnalytics }))
);
const TrainingEffectiveness = lazy(() =>
  import("./pages/admin/TrainingEffectiveness").then((m) => ({ default: m.TrainingEffectiveness }))
);
const EmergingSkills = lazy(() =>
  import("./pages/admin/EmergingSkills").then((m) => ({ default: m.EmergingSkills }))
);
const CapacityPlanning = lazy(() =>
  import("./pages/admin/CapacityPlanning").then((m) => ({ default: m.CapacityPlanning }))
);
const AdminUsers = lazy(() =>
  import("./pages/admin/AdminUsers").then((m) => ({ default: m.AdminUsers }))
);
const AdminReports = lazy(() =>
  import("./pages/admin/AdminReports").then((m) => ({ default: m.AdminReports }))
);
const AdminProfile = lazy(() =>
  import("./pages/admin/AdminProfile").then((m) => ({ default: m.AdminProfile }))
);

// Official Pages
const OfficialDashboard = lazy(() =>
  import("./pages/official/OfficialDashboard").then((m) => ({ default: m.OfficialDashboard }))
);
const OfficialCompetencies = lazy(() =>
  import("./pages/official/OfficialCompetencies").then((m) => ({ default: m.OfficialCompetencies }))
);
const OfficialAssessments = lazy(() =>
  import("./pages/official/OfficialAssessments").then((m) => ({ default: m.OfficialAssessments }))
);
const OfficialSkillGaps = lazy(() =>
  import("./pages/official/OfficialSkillGaps").then((m) => ({ default: m.OfficialSkillGaps }))
);
const OfficialRecommendations = lazy(() =>
  import("./pages/official/OfficialRecommendations").then((m) => ({ default: m.OfficialRecommendations }))
);
const OfficialLearning = lazy(() =>
  import("./pages/official/OfficialLearning").then((m) => ({ default: m.OfficialLearning }))
);
const OfficialQuizzes = lazy(() =>
  import("./pages/official/OfficialQuizzes").then((m) => ({ default: m.OfficialQuizzes }))
);
const OfficialEvidence = lazy(() =>
  import("./pages/official/OfficialEvidence").then((m) => ({ default: m.OfficialEvidence }))
);
const OfficialProgress = lazy(() =>
  import("./pages/official/OfficialProgress").then((m) => ({ default: m.OfficialProgress }))
);
const OfficialProfile = lazy(() =>
  import("./pages/official/OfficialProfile").then((m) => ({ default: m.OfficialProfile }))
);
const CapabilityAssistant = lazy(() =>
  import("./components/assistant/CapabilityAssistant").then((m) => ({ default: m.CapabilityAssistant }))
);

// ─── Loading screen ───────────────────────────────────────────────────────────

function LoadingScreen() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-[#eef4f8]">
      <div className="text-center animate-fadeIn">
        <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-[#123057] text-white text-2xl font-extrabold shadow-md">
          S
        </div>
        <div className="text-sm font-bold text-[#123057]">Loading ShikshaSetu…</div>
        <div className="mt-2 text-xs text-slate-400">Optimizing capability intelligence</div>
      </div>
    </div>
  );
}

// ─── Trainer Portal App ───────────────────────────────────────────────────────

function TrainerApp() {
  const [activePage, setActivePage] = useState("Dashboard");
  const [navContext, setNavContext] = useState<{ materialId?: string; quizId?: string }>({});
  const { user } = useAuth();

  const handleNavigate = (page: string, context?: { materialId?: string; quizId?: string }) => {
    setActivePage(page);
    if (context) {
      setNavContext(context);
    }
  };

  const renderPage = () => {
    switch (activePage) {
      case "Dashboard":
        return <TrainerDashboard onNavigate={handleNavigate} />;
      case "Learning Materials":
      case "Upload Material":
        return <TrainerMaterials onNavigate={handleNavigate} />;
      case "AI Question Generator":
        return (
          <TrainerQuestionGenerator
            initialMaterialId={navContext.materialId}
            onNavigate={handleNavigate}
          />
        );
      case "Question Review":
        return (
          <TrainerQuestionReview
            initialMaterialId={navContext.materialId}
            onNavigate={handleNavigate}
          />
        );
      case "Quiz Studio":
      case "Published Quizzes":
        return <TrainerQuizStudio onNavigate={handleNavigate} />;
      case "Learner Results":
        return (
          <TrainerLearnerResults
            initialQuizId={navContext.quizId}
            onNavigate={handleNavigate}
          />
        );
      case "Profile":
        return (
          <div className="max-w-2xl mx-auto rounded-3xl border border-[#f0ddd0] bg-white p-8 shadow-sm space-y-6 animate-fadeIn">
            <div className="flex items-center gap-4 border-b border-slate-100 pb-6">
              <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-[#ef7e37] text-white text-2xl font-black">
                {user?.full_name?.charAt(0) || "T"}
              </div>
              <div>
                <span className="rounded-full bg-orange-100 px-3 py-0.5 text-xs font-bold text-[#c2510e]">
                  TRAINER
                </span>
                <h2 className="text-xl font-extrabold text-slate-800 mt-1">
                  {user?.full_name}
                </h2>
                <p className="text-xs text-slate-400">{user?.email}</p>
              </div>
            </div>

            <div className="grid gap-4 sm:grid-cols-2 text-xs">
              <div className="rounded-2xl bg-slate-50 p-4 border border-slate-100">
                <div className="font-bold text-slate-400 uppercase tracking-wider text-[10px]">
                  Designation
                </div>
                <div className="text-sm font-black text-slate-800 mt-1">
                  {user?.designation || "Senior Curriculum Trainer"}
                </div>
              </div>

              <div className="rounded-2xl bg-slate-50 p-4 border border-slate-100">
                <div className="font-bold text-slate-400 uppercase tracking-wider text-[10px]">
                  Department
                </div>
                <div className="text-sm font-black text-slate-800 mt-1">
                  {user?.department || "Ministry of Statistics & PI"}
                </div>
              </div>

              <div className="rounded-2xl bg-slate-50 p-4 border border-slate-100">
                <div className="font-bold text-slate-400 uppercase tracking-wider text-[10px]">
                  Employee ID
                </div>
                <div className="text-sm font-black text-slate-800 mt-1">
                  {user?.employee_id || "TRN-001"}
                </div>
              </div>

              <div className="rounded-2xl bg-slate-50 p-4 border border-slate-100">
                <div className="font-bold text-slate-400 uppercase tracking-wider text-[10px]">
                  Access Role
                </div>
                <div className="text-sm font-black text-emerald-700 mt-1">
                  Verified Content Creator & Evaluator
                </div>
              </div>
            </div>
          </div>
        );
      default:
        return <TrainerDashboard onNavigate={handleNavigate} />;
    }
  };

  return (
    <TrainerLayout activePage={activePage} onNavigate={setActivePage}>
      <Suspense fallback={<PageSkeleton />}>
        {renderPage()}
      </Suspense>
    </TrainerLayout>
  );
}

// ─── Admin Portal App ─────────────────────────────────────────────────────────

function AdminApp() {
  const [activePage, setActivePage] = useState("Dashboard");

  const renderPage = () => {
    switch (activePage) {
      case "Dashboard":
        return <AdminDashboard onNavigate={setActivePage} />;
      case "Workforce Overview":
        return <WorkforceOverview onNavigate={setActivePage} />;
      case "Competency Analytics":
        return <CompetencyAnalytics onNavigate={setActivePage} />;
      case "Skill Gap Analytics":
        return <SkillGapAnalytics onNavigate={setActivePage} />;
      case "Training Effectiveness":
        return <TrainingEffectiveness onNavigate={setActivePage} />;
      case "Emerging Skills":
        return <EmergingSkills onNavigate={setActivePage} />;
      case "Capacity Planning":
        return <CapacityPlanning onNavigate={setActivePage} />;
      case "Users":
        return <AdminUsers onNavigate={setActivePage} />;
      case "Reports":
        return <AdminReports onNavigate={setActivePage} />;
      case "Profile":
        return <AdminProfile />;
      default:
        return <AdminDashboard onNavigate={setActivePage} />;
    }
  };

  return (
    <AdminLayout activePage={activePage} onNavigate={setActivePage}>
      <Suspense fallback={<PageSkeleton />}>
        {renderPage()}
      </Suspense>
    </AdminLayout>
  );
}

// ─── Official / Employee app ──────────────────────────────────────────────────

function OfficialApp() {
  const [activePage, setActivePage] = useState("Dashboard");
  const [navContext, setNavContext] = useState<{ competencyCode?: string; activityId?: string }>({});

  const handleNavigate = (page: string, context?: { competencyCode?: string; activityId?: string }) => {
    setActivePage(page);
    if (context) {
      setNavContext(context);
    }
  };

  const renderPage = () => {
    switch (activePage) {
      case "Dashboard":
        return <OfficialDashboard onNavigate={handleNavigate} />;
      case "My Competencies":
        return <OfficialCompetencies onNavigate={handleNavigate} />;
      case "Assessments":
        return (
          <OfficialAssessments
            initialCompetencyCode={navContext.competencyCode}
            onNavigate={handleNavigate}
          />
        );
      case "Skill Gaps":
        return <OfficialSkillGaps onNavigate={handleNavigate} />;
      case "Recommendations":
        return (
          <OfficialRecommendations
            initialCompetencyCode={navContext.competencyCode}
            onNavigate={handleNavigate}
          />
        );
      case "My Learning":
        return (
          <OfficialLearning
            initialActivityId={navContext.activityId}
            onNavigate={handleNavigate}
          />
        );
      case "Quizzes":
        return (
          <OfficialQuizzes
            initialCompetencyCode={navContext.competencyCode}
            onNavigate={handleNavigate}
          />
        );
      case "Evidence":
        return <OfficialEvidence onNavigate={handleNavigate} />;
      case "Progress":
        return <OfficialProgress onNavigate={handleNavigate} />;
      case "Profile":
        return <OfficialProfile />;
      default:
        return <OfficialDashboard onNavigate={handleNavigate} />;
    }
  };

  return (
    <OfficialLayout activePage={activePage} onNavigate={setActivePage}>
      <Suspense fallback={<PageSkeleton />}>
        {renderPage()}
      </Suspense>
      <Suspense fallback={null}>
        <CapabilityAssistant currentPage={activePage} onNavigate={handleNavigate} />
      </Suspense>
    </OfficialLayout>
  );
}

// ─── Role-based router ────────────────────────────────────────────────────────

function RoleRouter() {
  const { user, loading } = useAuth();

  if (loading) return <LoadingScreen />;
  if (!user) {
    return (
      <Suspense fallback={<LoadingScreen />}>
        <LoginPage />
      </Suspense>
    );
  }

  if (user.access_role === "TRAINER") return <TrainerApp />;
  if (user.access_role === "ADMIN") return <AdminApp />;

  // OFFICIAL + EMPLOYEE
  return <OfficialApp />;
}

// ─── Root ─────────────────────────────────────────────────────────────────────

function App() {
  return (
    <ErrorBoundary>
      <ThemeProvider defaultTheme="light">
        <TooltipProvider>
          <Toaster position="bottom-center" />
          <LanguageProvider>
            <AuthProvider>
              <RoleRouter />
            </AuthProvider>
          </LanguageProvider>
        </TooltipProvider>
      </ThemeProvider>
    </ErrorBoundary>
  );
}

export default App;
