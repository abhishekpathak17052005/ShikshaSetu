import { useState } from "react";
import { Toaster } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import ErrorBoundary from "./components/ErrorBoundary";
import { ThemeProvider } from "./contexts/ThemeContext";
import { AuthProvider, useAuth } from "./contexts/AuthContext";
import { TrainerLayout } from "./layouts/TrainerLayout";
import { AdminLayout } from "./layouts/AdminLayout";
import LoginPage from "./pages/LoginPage";

import { TrainerDashboard } from "./pages/trainer/TrainerDashboard";
import { TrainerMaterials } from "./pages/trainer/TrainerMaterials";
import { TrainerQuestionGenerator } from "./pages/trainer/TrainerQuestionGenerator";
import { TrainerQuestionReview } from "./pages/trainer/TrainerQuestionReview";
import { TrainerQuizStudio } from "./pages/trainer/TrainerQuizStudio";
import { TrainerLearnerResults } from "./pages/trainer/TrainerLearnerResults";

// ─── Loading screen ───────────────────────────────────────────────────────────

function LoadingScreen() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-[#eef4f8]">
      <div className="text-center">
        <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-[#123057] text-white text-2xl font-extrabold">
          S
        </div>
        <div className="text-sm font-bold text-[#123057]">Loading ShikshaSetu…</div>
        <div className="mt-2 text-xs text-slate-400">Checking your session</div>
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
      {renderPage()}
    </TrainerLayout>
  );
}

// ─── Admin stub ───────────────────────────────────────────────────────────────

import { AdminDashboard } from "./pages/admin/AdminDashboard";
import { WorkforceOverview } from "./pages/admin/WorkforceOverview";
import { CompetencyAnalytics } from "./pages/admin/CompetencyAnalytics";
import { SkillGapAnalytics } from "./pages/admin/SkillGapAnalytics";
import { TrainingEffectiveness } from "./pages/admin/TrainingEffectiveness";
import { EmergingSkills } from "./pages/admin/EmergingSkills";
import { CapacityPlanning } from "./pages/admin/CapacityPlanning";
import { AdminUsers } from "./pages/admin/AdminUsers";
import { AdminReports } from "./pages/admin/AdminReports";
import { AdminProfile } from "./pages/admin/AdminProfile";

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
      {renderPage()}
    </AdminLayout>
  );
}

import { OfficialLayout } from "./layouts/OfficialLayout";
import { OfficialDashboard } from "./pages/official/OfficialDashboard";
import { OfficialCompetencies } from "./pages/official/OfficialCompetencies";
import { OfficialAssessments } from "./pages/official/OfficialAssessments";
import { OfficialSkillGaps } from "./pages/official/OfficialSkillGaps";
import { OfficialRecommendations } from "./pages/official/OfficialRecommendations";
import { OfficialLearning } from "./pages/official/OfficialLearning";
import { OfficialQuizzes } from "./pages/official/OfficialQuizzes";
import { OfficialEvidence } from "./pages/official/OfficialEvidence";
import { OfficialProgress } from "./pages/official/OfficialProgress";
import { OfficialProfile } from "./pages/official/OfficialProfile";

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
        return <OfficialQuizzes onNavigate={handleNavigate} />;
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
      {renderPage()}
    </OfficialLayout>
  );
}

// ─── Role-based router ────────────────────────────────────────────────────────

function RoleRouter() {
  const { user, loading } = useAuth();

  if (loading) return <LoadingScreen />;
  if (!user) return <LoginPage />;

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
          <Toaster />
          <AuthProvider>
            <RoleRouter />
          </AuthProvider>
        </TooltipProvider>
      </ThemeProvider>
    </ErrorBoundary>
  );
}

export default App;
