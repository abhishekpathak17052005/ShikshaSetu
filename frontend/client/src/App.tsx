import React, { useState, useEffect, useCallback, Suspense, lazy } from "react";
import { useLocation } from "wouter";
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
import { ShikshaSetuLogo } from "./components/brand/ShikshaSetuLogo";
import { usePrefetchRoutes } from "@/utils/routePrefetch";
import { registerServiceWorker } from "@/utils/serviceWorker";

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
const TrainerProfile = lazy(() =>
  import("./pages/trainer/TrainerProfile").then((m) => ({ default: m.TrainerProfile }))
);
const TrainerTalentPassport = lazy(() =>
  import("./pages/trainer/TrainerTalentPassport").then((m) => ({ default: m.TrainerTalentPassport }))
);

// Admin Pages
const AdminDashboard = lazy(() =>
  import("./pages/admin/AdminDashboard").then((m) => ({ default: m.AdminDashboard }))
);
const WorkforceIntelligence = lazy(() =>
  import("./pages/admin/WorkforceIntelligence").then((m) => ({ default: m.WorkforceIntelligence }))
);
const TalentDiscovery = lazy(() =>
  import("./pages/admin/TalentDiscovery").then((m) => ({ default: m.TalentDiscovery }))
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
const AdminTalentNetwork = lazy(() =>
  import("./pages/admin/AdminTalentNetwork").then((m) => ({ default: m.AdminTalentNetwork }))
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
const OfficialTalentPassport = lazy(() =>
  import("./pages/official/OfficialTalentPassport").then((m) => ({ default: m.OfficialTalentPassport }))
);
// ─── Loading screen ───────────────────────────────────────────────────────────

function LoadingScreen() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-[#eef4f8]">
      <div className="text-center animate-fadeIn">
        <div className="mx-auto mb-4 flex items-center justify-center">
          <ShikshaSetuLogo variant="full" size="md" priority />
        </div>
        <div className="text-sm font-bold text-[#123057]">Loading ShikshaSetu…</div>
        <div className="mt-2 text-xs text-slate-400">Optimizing capability intelligence</div>
      </div>
    </div>
  );
}

// ─── Routing Helpers ──────────────────────────────────────────────────────────

function toSlug(name: string): string {
  return name
    .toLowerCase()
    .trim()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/(^-|-$)/g, "");
}

function getRoleSlug(role?: string): "trainer" | "admin" | "official" {
  const r = (role || "").toUpperCase();
  if (r === "TRAINER") return "trainer";
  if (r === "ADMIN") return "admin";
  return "official";
}

// ─── Trainer Portal App ───────────────────────────────────────────────────────

const TRAINER_SLUG_MAP: Record<string, string> = {
  "dashboard": "Dashboard",
  "learning-materials": "Learning Materials",
  "upload-material": "Learning Materials",
  "ai-question-generator": "AI Question Generator",
  "question-review": "Question Review",
  "quiz-studio": "Quiz Studio",
  "published-quizzes": "Quiz Studio",
  "learner-results": "Learner Results",
  "trainer-talent-passport": "Trainer Talent Passport",
  "talent-passport": "Trainer Talent Passport",
  "profile": "Profile",
};

function TrainerApp() {
  const [location, navigate] = useLocation();
  const [navContext, setNavContext] = useState<{ materialId?: string; quizId?: string }>({});

  const match = location.match(/^\/trainer\/?([^\/?#]+)?/i);
  const rawSlug = match && match[1] ? match[1].toLowerCase() : "";
  const activePage = TRAINER_SLUG_MAP[rawSlug] || "Dashboard";

  // Prefetch all trainer pages so section clicks are instantaneous
  usePrefetchRoutes([
    { loader: () => import("./pages/trainer/TrainerDashboard"), key: "trainer-dashboard" },
    { loader: () => import("./pages/trainer/TrainerMaterials"), key: "trainer-materials" },
    { loader: () => import("./pages/trainer/TrainerQuizStudio"), key: "trainer-quiz-studio" },
    { loader: () => import("./pages/trainer/TrainerQuestionGenerator"), key: "trainer-question-gen" },
    { loader: () => import("./pages/trainer/TrainerQuestionReview"), key: "trainer-question-review" },
    { loader: () => import("./pages/trainer/TrainerLearnerResults"), key: "trainer-learner-results" },
    { loader: () => import("./pages/trainer/TrainerTalentPassport"), key: "trainer-talent-passport" },
    { loader: () => import("./pages/trainer/TrainerProfile"), key: "trainer-profile" },
  ]);

  useEffect(() => {
    if (!rawSlug || !TRAINER_SLUG_MAP[rawSlug]) {
      navigate("/trainer/dashboard", { replace: true });
    }
  }, [rawSlug, navigate]);

  const handleNavigate = useCallback((page: string, context?: { materialId?: string; quizId?: string }) => {
    if (context) {
      setNavContext(context);
    }
    const raw = toSlug(page);
    const canonicalPage = TRAINER_SLUG_MAP[raw] || page;
    const slug = toSlug(canonicalPage);
    navigate(`/trainer/${slug}`);
  }, [navigate]);

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
      case "Trainer Talent Passport":
        return <TrainerTalentPassport />;
      case "Profile":
        return <TrainerProfile />;
      default:
        return <TrainerDashboard onNavigate={handleNavigate} />;
    }
  };

  return (
    <TrainerLayout activePage={activePage} onNavigate={handleNavigate}>
      <Suspense fallback={<PageSkeleton />}>
        {renderPage()}
      </Suspense>
    </TrainerLayout>
  );
}

// ─── Admin Portal App ─────────────────────────────────────────────────────────

const ADMIN_SLUG_MAP: Record<string, string> = {
  "dashboard": "Dashboard",
  "workforce-intelligence": "Workforce Intelligence",
  "workforce-overview": "Workforce Overview",
  "competency-analytics": "Competency Analytics",
  "skill-gap-analytics": "Skill Gap Analytics",
  "training-effectiveness": "Training Effectiveness",
  "emerging-skills": "Emerging Skills",
  "capacity-planning": "Capacity Planning",
  "opportunity-network": "Opportunity Network",
  "talent-network": "Opportunity Network",
  "talent-discovery": "Talent Discovery",
  "users": "Users",
  "reports": "Reports",
  "profile": "Profile",
};

function AdminApp() {
  const [location, navigate] = useLocation();

  const match = location.match(/^\/admin\/?([^\/?#]+)?/i);
  const rawSlug = match && match[1] ? match[1].toLowerCase() : "";
  const activePage = ADMIN_SLUG_MAP[rawSlug] || "Dashboard";

  // Prefetch all admin pages so section clicks are instantaneous
  usePrefetchRoutes([
    { loader: () => import("./pages/admin/AdminDashboard"), key: "admin-dashboard" },
    { loader: () => import("./pages/admin/WorkforceIntelligence"), key: "admin-workforce-intelligence" },
    { loader: () => import("./pages/admin/TalentDiscovery"), key: "admin-talent-discovery" },
    { loader: () => import("./pages/admin/WorkforceOverview"), key: "admin-workforce" },
    { loader: () => import("./pages/admin/CompetencyAnalytics"), key: "admin-competency" },
    { loader: () => import("./pages/admin/SkillGapAnalytics"), key: "admin-skill-gaps" },
    { loader: () => import("./pages/admin/TrainingEffectiveness"), key: "admin-training-eff" },
    { loader: () => import("./pages/admin/EmergingSkills"), key: "admin-emerging-skills" },
    { loader: () => import("./pages/admin/CapacityPlanning"), key: "admin-capacity-planning" },
    { loader: () => import("./pages/admin/AdminTalentNetwork"), key: "admin-talent-net" },
    { loader: () => import("./pages/admin/AdminUsers"), key: "admin-users" },
    { loader: () => import("./pages/admin/AdminReports"), key: "admin-reports" },
    { loader: () => import("./pages/admin/AdminProfile"), key: "admin-profile" },
  ]);

  useEffect(() => {
    if (!rawSlug || !ADMIN_SLUG_MAP[rawSlug]) {
      navigate("/admin/dashboard", { replace: true });
    }
  }, [rawSlug, navigate]);

  const handleNavigate = useCallback((page: string) => {
    const raw = toSlug(page);
    const canonicalPage = ADMIN_SLUG_MAP[raw] || page;
    const slug = toSlug(canonicalPage);
    navigate(`/admin/${slug}`);
  }, [navigate]);

  const renderPage = () => {
    switch (activePage) {
      case "Dashboard":
        return <AdminDashboard onNavigate={handleNavigate} />;
      case "Workforce Intelligence":
        return <WorkforceIntelligence />;
      case "Workforce Overview":
        return <WorkforceOverview onNavigate={handleNavigate} />;
      case "Competency Analytics":
        return <CompetencyAnalytics onNavigate={handleNavigate} />;
      case "Skill Gap Analytics":
        return <SkillGapAnalytics onNavigate={handleNavigate} />;
      case "Training Effectiveness":
        return <TrainingEffectiveness onNavigate={handleNavigate} />;
      case "Emerging Skills":
        return <EmergingSkills onNavigate={handleNavigate} />;
      case "Capacity Planning":
        return <CapacityPlanning onNavigate={handleNavigate} />;
      case "Opportunity Network":
        return <AdminTalentNetwork />;
      case "Talent Discovery":
        return <TalentDiscovery onNavigate={handleNavigate} />;
      case "Users":
        return <AdminUsers onNavigate={handleNavigate} />;
      case "Reports":
        return <AdminReports onNavigate={handleNavigate} />;
      case "Profile":
        return <AdminProfile />;
      default:
        return <AdminDashboard onNavigate={handleNavigate} />;
    }
  };

  return (
    <AdminLayout activePage={activePage} onNavigate={handleNavigate}>
      <Suspense fallback={<PageSkeleton />}>
        {renderPage()}
      </Suspense>
    </AdminLayout>
  );
}

// ─── Official / Employee app ──────────────────────────────────────────────────

const OFFICIAL_SLUG_MAP: Record<string, string> = {
  "dashboard": "Dashboard",
  "my-competencies": "My Competencies",
  "assessments": "Assessments",
  "skill-gaps": "Skill Gaps",
  "recommendations": "Recommendations",
  "my-learning": "My Learning",
  "quizzes": "Quizzes",
  "evidence": "Evidence",
  "progress": "Progress",
  "talent-passport": "Talent Passport",
  "profile": "Profile",
};

function OfficialApp() {
  const [location, navigate] = useLocation();
  const [navContext, setNavContext] = useState<{ competencyCode?: string; activityId?: string }>({});

  const match = location.match(/^\/(?:official|employee)\/?([^\/?#]+)?/i);
  const rawSlug = match && match[1] ? match[1].toLowerCase() : "";
  const activePage = OFFICIAL_SLUG_MAP[rawSlug] || "Dashboard";

  // Prefetch all official pages so section clicks are instantaneous
  usePrefetchRoutes([
    { loader: () => import("./pages/official/OfficialDashboard"), key: "official-dashboard" },
    { loader: () => import("./pages/official/OfficialCompetencies"), key: "official-competencies" },
    { loader: () => import("./pages/official/OfficialAssessments"), key: "official-assessments" },
    { loader: () => import("./pages/official/OfficialSkillGaps"), key: "official-skill-gaps" },
    { loader: () => import("./pages/official/OfficialRecommendations"), key: "official-recommendations" },
    { loader: () => import("./pages/official/OfficialLearning"), key: "official-learning" },
    { loader: () => import("./pages/official/OfficialQuizzes"), key: "official-quizzes" },
    { loader: () => import("./pages/official/OfficialEvidence"), key: "official-evidence" },
    { loader: () => import("./pages/official/OfficialProgress"), key: "official-progress" },
    { loader: () => import("./pages/official/OfficialTalentPassport"), key: "official-talent-passport" },
    { loader: () => import("./pages/official/OfficialProfile"), key: "official-profile" },
  ]);

  useEffect(() => {
    if (!rawSlug || !OFFICIAL_SLUG_MAP[rawSlug]) {
      navigate("/official/dashboard", { replace: true });
    }
  }, [rawSlug, navigate]);

  const handleNavigate = useCallback((page: string, context?: { competencyCode?: string; activityId?: string }) => {
    if (context) {
      setNavContext(context);
    }
    const raw = toSlug(page);
    const canonicalPage = OFFICIAL_SLUG_MAP[raw] || page;
    const slug = toSlug(canonicalPage);
    navigate(`/official/${slug}`);
  }, [navigate]);

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
      case "Talent Passport":
        return <OfficialTalentPassport onNavigate={handleNavigate} />;
      case "Profile":
        return <OfficialProfile />;
      default:
        return <OfficialDashboard onNavigate={handleNavigate} />;
    }
  };

  return (
    <OfficialLayout activePage={activePage} onNavigate={handleNavigate}>
      <Suspense fallback={<PageSkeleton />}>
        {renderPage()}
      </Suspense>
    </OfficialLayout>
  );
}

// ─── Role-based router ────────────────────────────────────────────────────────

function RoleRouter() {
  const { user, loading } = useAuth();
  const [location, navigate] = useLocation();

  const userRole = user ? getRoleSlug(user.access_role) : null;

  useEffect(() => {
    if (loading) return;

    if (!user) {
      // Unauthenticated: allow only /login and /register
      if (location !== "/login" && location !== "/register") {
        navigate("/login", { replace: true });
      }
    } else {
      // Authenticated: redirect away from auth routes or root
      const isAuthPage = location === "/login" || location === "/register" || location === "/";
      const isBareRole = location === `/${userRole}`;
      if (isAuthPage || isBareRole) {
        navigate(`/${userRole}/dashboard`, { replace: true });
        return;
      }

      // If user attempts to access a role section they do not belong to:
      const roleMatch = location.match(/^\/([^\/?#]+)/i);
      const requestedRole = roleMatch ? roleMatch[1].toLowerCase() : "";
      const allRoles = ["trainer", "admin", "official", "employee"];
      if (allRoles.includes(requestedRole)) {
        const canonicalRequested = requestedRole === "employee" ? "official" : requestedRole;
        if (canonicalRequested !== userRole) {
          navigate(`/${userRole}/dashboard`, { replace: true });
        }
      }
    }
  }, [loading, user, userRole, location, navigate]);

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
  // Register service worker for offline support and caching
  useEffect(() => {
    registerServiceWorker({
      onSuccess: () => console.log("[App] Service worker registered successfully"),
      onUpdate: () => console.log("[App] New app version available"),
      onError: (error) => console.error("[App] Service worker error:", error),
    });
  }, []);

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
