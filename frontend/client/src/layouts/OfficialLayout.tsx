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
import { useTranslation } from "@/i18n";
import { LanguageToggle } from "@/components/LanguageToggle";

// ─── Props ────────────────────────────────────────────────────────────────────

interface OfficialLayoutProps {
  children: React.ReactNode;
  activePage: string;
  onNavigate: (page: string) => void;
}

// ─── Component ────────────────────────────────────────────────────────────────

export function OfficialLayout({ children, activePage, onNavigate }: OfficialLayoutProps) {
  const { user, logout } = useAuth();
  const { t, isHindi } = useTranslation();
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const navItems = [
    { id: "Dashboard", label: t("nav.dashboard"), icon: LayoutDashboard },
    { id: "My Competencies", label: t("nav.competencies"), icon: Gauge },
    { id: "Assessments", label: t("nav.assessments"), icon: ClipboardCheck },
    { id: "Skill Gaps", label: t("nav.skillGaps"), icon: Target },
    { id: "Recommendations", label: t("nav.recommendations"), icon: BookOpen },
    { id: "My Learning", label: t("nav.learning"), icon: Star },
    { id: "Quizzes", label: t("nav.quizzes"), icon: Award },
    { id: "Evidence", label: t("nav.evidence"), icon: FileText },
    { id: "Progress", label: t("nav.progress"), icon: TrendingUp },
    { id: "Profile", label: t("nav.profile"), icon: UserRound },
  ];

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
        <div className="flex items-center gap-3 px-5 py-5 border-b border-[#dfe7f0]">
          <img
            src="/shikshasetu-icon.svg"
            alt="ShikshaSetu"
            className="h-9 w-9 flex-shrink-0"
            aria-hidden="true"
            onError={(e) => {
              (e.currentTarget as HTMLElement).style.display = "none";
            }}
          />
          <div className="min-w-0">
            <div className="text-base font-bold text-[#123057] tracking-tight">ShikshaSetu</div>
            <div className="text-[10px] font-semibold uppercase tracking-wider text-slate-400 mt-0.5">
              {isHindi ? "क्षमता इंटेलिजेंस" : "Capability Intelligence"}
            </div>
          </div>
        </div>

        {/* Section label */}
        <div className="px-7 pt-5 pb-2 text-[10px] font-semibold uppercase tracking-wider text-slate-400">
          {isHindi ? "शिक्षार्थी कार्यक्षेत्र" : "Learner workspace"}
        </div>

        {/* Nav items */}
        <nav className="flex-1 px-4 overflow-y-auto pb-4">
          {navItems.map(({ id, label, icon: Icon }) => {
            const isActive = activePage === id;
            return (
              <button
                key={id}
                onClick={() => handleNav(id)}
                className={`mb-1 flex w-full items-center gap-3 rounded-xl px-3.5 py-2.5 text-left text-xs transition-all duration-180 active:scale-[0.98] group ${
                  isActive
                    ? "bg-[#e8f5f3] text-[#087f76] shadow-xs font-semibold nav-pill-active"
                    : "text-slate-600 font-medium hover:bg-slate-50 hover:text-[#123057]"
                }`}
                aria-current={isActive ? "page" : undefined}
              >
                <Icon size={17} className={`transition-transform duration-160 ${isActive ? "scale-105 text-[#087f76]" : "text-slate-400 group-hover:scale-110 group-hover:text-[#123057]"}`} />
                <span>{label}</span>
              </button>
            );
          })}
        </nav>

        {/* User footer */}
        <div className="border-t border-[#dfe7f0] px-5 py-4">
          <div className="mb-0.5 text-xs font-semibold text-[#123057] truncate">
            {user?.full_name ?? "—"}
          </div>
          <div className="text-[11px] font-normal text-slate-400 truncate mb-3">
            {user?.designation ?? user?.department ?? "—"}
          </div>
          <button
            onClick={logout}
            className="flex w-full items-center gap-2 rounded-lg px-3 py-2 text-xs font-medium text-slate-600 hover:bg-slate-50 transition-colors active:scale-[0.98]"
          >
            <LogOut size={15} aria-hidden="true" />
            {t("common.logout")}
          </button>
        </div>

        {/* Capability pathway strip */}
        <div className="border-t border-[#dfe7f0] px-4 py-3 bg-[#f8fafc]">
          <div className="text-[10px] font-semibold uppercase tracking-wider text-slate-400 mb-2">
            {isHindi ? "क्षमता विकास पथ" : "Capability pathway"}
          </div>
          <div className="flex flex-wrap gap-1">
            {PATHWAY_STEPS.map((step, idx) => (
              <React.Fragment key={step.id}>
                <span
                  className={`text-[9px] font-semibold px-2 py-0.5 rounded-md transition-all duration-200 ${
                    currentStep === step.id
                      ? "bg-[#0f9f92] text-white shadow-xs scale-105"
                      : "bg-[#e8f5f3] text-[#0f9f92]"
                  }`}
                >
                  {isHindi ? step.labelHi : step.labelEn}
                </span>
                {idx < PATHWAY_STEPS.length - 1 && (
                  <span className="text-[9px] text-slate-300 self-center font-mono">→</span>
                )}
              </React.Fragment>
            ))}
          </div>
        </div>
      </aside>

      {/* ── Mobile overlay ── */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 z-30 bg-black/20 backdrop-blur-xs transition-opacity lg:hidden"
          onClick={() => setSidebarOpen(false)}
          aria-hidden="true"
        />
      )}

      {/* ── Hamburger ── */}
      <button
        className="fixed left-4 top-4 z-50 rounded-lg bg-white p-2 shadow border border-[#dfe7f0] lg:hidden active:scale-95 transition-transform"
        onClick={() => setSidebarOpen(!sidebarOpen)}
        aria-label={sidebarOpen ? "Close sidebar" : "Open sidebar"}
      >
        {sidebarOpen ? <X size={20} /> : <Menu size={20} />}
      </button>

      {/* ── Main content ── */}
      <main className="lg:ml-[264px]">
        <header className="flex h-[68px] items-center justify-between border-b border-[#dfe7f0] bg-white px-6 lg:px-9 sticky top-0 z-20">
          <div>
            <div className="text-[10px] font-bold uppercase tracking-[.14em] text-slate-400">
              {isHindi ? "शिक्षासेतु कार्यक्षेत्र" : "ShikshaSetu workspace"}
            </div>
            <h1 className="text-lg font-bold text-[#123057]">
              {navItems.find((n) => n.id === activePage)?.label || activePage}
            </h1>
          </div>
          <div className="flex items-center gap-3">
            <LanguageToggle />
            <span className="hidden text-xs font-semibold text-slate-500 sm:block truncate max-w-[160px]">
              {user?.full_name}
            </span>
            <button
              onClick={logout}
              className="rounded-lg border border-slate-200 px-3 py-1.5 text-xs font-bold text-[#123057] hover:bg-slate-50 transition-all active:scale-95"
            >
              {t("common.logout")}
            </button>
          </div>
        </header>
        <div key={activePage} className="mx-auto max-w-[1240px] p-6 lg:p-9 anim-page-enter">{children}</div>
      </main>
    </div>
  );
}

export default OfficialLayout;
