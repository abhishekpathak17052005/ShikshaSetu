import React, { useState } from "react";
import {
  Award,
  BarChart2,
  BookOpen,
  ClipboardCheck,
  FileText,
  Gauge,
  LayoutDashboard,
  LogOut,
  Menu,
  Star,
  Target,
  TrendingUp,
  UserRound,
  X,
} from "lucide-react";
import { useAuth } from "@/contexts/AuthContext";

// ─── Navigation items ─────────────────────────────────────────────────────────

const NAV_ITEMS = [
  { id: "Dashboard", label: "Dashboard", icon: LayoutDashboard },
  { id: "My Competencies", label: "My Competencies", icon: Gauge },
  { id: "Assessments", label: "Assessments", icon: ClipboardCheck },
  { id: "Skill Gaps", label: "Skill Gaps", icon: Target },
  { id: "Recommendations", label: "Recommendations", icon: BookOpen },
  { id: "My Learning", label: "My Learning", icon: Star },
  { id: "Quizzes", label: "Quizzes", icon: Award },
  { id: "Evidence", label: "Evidence", icon: FileText },
  { id: "Progress", label: "Progress", icon: TrendingUp },
  { id: "Profile", label: "Profile", icon: UserRound },
] as const;

// Capability pathway steps shown at the bottom of the sidebar
const PATHWAY_STEPS = [
  { id: "role", label: "Role" },
  { id: "assess", label: "Assess" },
  { id: "gap", label: "Gap" },
  { id: "learn", label: "Learn" },
  { id: "practice", label: "Practice" },
  { id: "validate", label: "Validate" },
];

// Map active page → current pathway step
function getPathwayStep(activePage: string): string {
  if (activePage === "Assessments") return "assess";
  if (activePage === "Skill Gaps") return "gap";
  if (activePage === "My Learning" || activePage === "Recommendations") return "learn";
  if (activePage === "Quizzes") return "practice";
  if (activePage === "Evidence" || activePage === "Progress") return "validate";
  return "role";
}

// ─── Props ────────────────────────────────────────────────────────────────────

interface OfficialLayoutProps {
  children: React.ReactNode;
  activePage: string;
  onNavigate: (page: string) => void;
}

// ─── Component ────────────────────────────────────────────────────────────────

export function OfficialLayout({ children, activePage, onNavigate }: OfficialLayoutProps) {
  const { user, logout } = useAuth();
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const currentStep = getPathwayStep(activePage);

  const handleNav = (page: string) => {
    onNavigate(page);
    setSidebarOpen(false);
  };

  return (
    <div className="min-h-screen bg-[#f4f7fb] text-[#1a2744]">
      {/* ── Sidebar ── */}
      <aside
        className={`fixed inset-y-0 left-0 z-40 w-[264px] border-r border-[#dfe7f0] bg-white flex flex-col transition-transform lg:translate-x-0 ${
          sidebarOpen ? "translate-x-0" : "-translate-x-full"
        }`}
      >
        {/* Logo */}
        <div className="flex items-center gap-3 px-5 py-6">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-[#123057] text-white text-lg font-extrabold select-none">
            S
          </div>
          <div>
            <div className="text-[17px] font-extrabold text-[#123057]">ShikshaSetu</div>
            <div className="text-[9px] font-bold uppercase tracking-[.18em] text-slate-400">
              Capability Intelligence
            </div>
          </div>
        </div>

        {/* Section label */}
        <div className="px-7 mb-2 text-[10px] font-bold uppercase tracking-[.14em] text-slate-400">
          Learner workspace
        </div>

        {/* Nav items */}
        <nav className="flex-1 px-4 overflow-y-auto">
          {NAV_ITEMS.map(({ id, label, icon: Icon }) => (
            <button
              key={id}
              onClick={() => handleNav(id)}
              className={`mb-1 flex w-full items-center gap-3 rounded-xl px-3 py-2.5 text-left text-sm font-semibold transition-colors ${
                activePage === id
                  ? "bg-[#e8f5f3] text-[#087f76]"
                  : "text-slate-500 hover:bg-slate-50 hover:text-[#123057]"
              }`}
            >
              <Icon size={17} />
              {label}
            </button>
          ))}
        </nav>

        {/* User footer */}
        <div className="border-t border-[#dfe7f0] px-5 py-4">
          <div className="mb-1 text-sm font-bold text-[#123057] truncate">
            {user?.full_name ?? "—"}
          </div>
          <div className="text-xs text-slate-400 truncate mb-3">
            {user?.designation ?? user?.department ?? "—"}
          </div>
          <button
            onClick={logout}
            className="flex w-full items-center gap-2 rounded-lg px-3 py-2 text-sm font-semibold text-slate-500 hover:bg-slate-50 transition-colors"
          >
            <LogOut size={16} />
            Log out
          </button>
        </div>

        {/* Capability pathway strip */}
        <div className="border-t border-[#dfe7f0] px-4 py-3 bg-[#f8fafc]">
          <div className="text-[9px] font-bold uppercase tracking-wider text-slate-400 mb-2">
            Capability pathway
          </div>
          <div className="flex flex-wrap gap-1">
            {PATHWAY_STEPS.map((step, idx) => (
              <React.Fragment key={step.id}>
                <span
                  className={`text-[9px] font-bold px-2 py-0.5 rounded-md transition-colors ${
                    currentStep === step.id
                      ? "bg-[#0f9f92] text-white"
                      : "bg-[#e8f5f3] text-[#0f9f92]"
                  }`}
                >
                  {step.label}
                </span>
                {idx < PATHWAY_STEPS.length - 1 && (
                  <span className="text-[9px] text-slate-300 self-center">→</span>
                )}
              </React.Fragment>
            ))}
          </div>
        </div>
      </aside>

      {/* ── Mobile overlay ── */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 z-30 bg-black/20 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* ── Hamburger ── */}
      <button
        className="fixed left-4 top-4 z-50 rounded-lg bg-white p-2 shadow border border-[#dfe7f0] lg:hidden"
        onClick={() => setSidebarOpen(!sidebarOpen)}
        aria-label="Toggle sidebar"
      >
        {sidebarOpen ? <X size={20} /> : <Menu size={20} />}
      </button>

      {/* ── Main content ── */}
      <main className="lg:ml-[264px]">
        <header className="flex h-[68px] items-center justify-between border-b border-[#dfe7f0] bg-white px-6 lg:px-9">
          <div>
            <div className="text-[10px] font-bold uppercase tracking-[.14em] text-slate-400">
              ShikshaSetu workspace
            </div>
            <h1 className="text-lg font-bold text-[#123057]">{activePage}</h1>
          </div>
          <div className="flex items-center gap-3">
            <span className="hidden text-xs font-semibold text-slate-500 sm:block truncate max-w-[160px]">
              {user?.full_name}
            </span>
            <button
              onClick={logout}
              className="rounded-lg border border-slate-200 px-3 py-1.5 text-xs font-bold text-[#123057] hover:bg-slate-50 transition-colors"
            >
              Logout
            </button>
          </div>
        </header>
        <div className="mx-auto max-w-[1240px] p-6 lg:p-9">{children}</div>
      </main>
    </div>
  );
}

export default OfficialLayout;
