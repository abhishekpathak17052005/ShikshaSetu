import React, { useState } from "react";
import {
  BarChart2,
  BookOpen,
  CheckSquare,
  FileQuestion,
  FilePlus,
  Layers,
  LayoutDashboard,
  LogOut,
  Menu,
  PenTool,
  Users,
  UserRound,
  X,
} from "lucide-react";
import { useAuth } from "@/contexts/AuthContext";

// ─── Navigation items ─────────────────────────────────────────────────────────

const NAV_ITEMS = [
  { id: "Dashboard", label: "Dashboard", icon: LayoutDashboard },
  { id: "Learning Materials", label: "Learning Materials", icon: BookOpen },
  { id: "Upload Material", label: "Upload Material", icon: FilePlus },
  { id: "AI Question Generator", label: "AI Question Generator", icon: FileQuestion },
  { id: "Question Review", label: "Question Review", icon: CheckSquare },
  { id: "Quiz Studio", label: "Quiz Studio", icon: PenTool },
  { id: "Published Quizzes", label: "Published Quizzes", icon: Layers },
  { id: "Learner Results", label: "Learner Results", icon: BarChart2 },
  { id: "Profile", label: "Profile", icon: UserRound },
] as const;

// ─── Props ────────────────────────────────────────────────────────────────────

interface TrainerLayoutProps {
  children: React.ReactNode;
  activePage: string;
  onNavigate: (page: string) => void;
}

// ─── Component ────────────────────────────────────────────────────────────────

export function TrainerLayout({ children, activePage, onNavigate }: TrainerLayoutProps) {
  const { user, logout } = useAuth();
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const handleNav = (page: string) => {
    onNavigate(page);
    setSidebarOpen(false);
  };

  return (
    <div className="min-h-screen bg-[#fdf5ee] text-[#1a2744]">
      {/* ── Sidebar ── */}
      <aside
        className={`fixed inset-y-0 left-0 z-40 w-[264px] border-r border-[#f0ddd0] bg-white flex flex-col transition-transform lg:translate-x-0 ${
          sidebarOpen ? "translate-x-0" : "-translate-x-full"
        }`}
      >
        {/* Logo */}
        <div className="flex items-center gap-3 px-5 py-6">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-[#ef7e37] text-white text-lg font-extrabold select-none">
            T
          </div>
          <div>
            <div className="text-[17px] font-extrabold text-[#c2510e]">ShikshaSetu</div>
            <div className="text-[9px] font-bold uppercase tracking-[.18em] text-slate-400">
              Content Creator
            </div>
          </div>
        </div>

        {/* Section label */}
        <div className="px-7 mb-2 text-[10px] font-bold uppercase tracking-[.14em] text-slate-400">
          Trainer workspace
        </div>

        {/* Nav items */}
        <nav className="flex-1 px-4 overflow-y-auto">
          {NAV_ITEMS.map(({ id, label, icon: Icon }) => (
            <button
              key={id}
              onClick={() => handleNav(id)}
              className={`mb-1 flex w-full items-center gap-3 rounded-xl px-3 py-2.5 text-left text-sm font-semibold transition-colors ${
                activePage === id
                  ? "bg-[#fff2e8] text-[#ef7e37]"
                  : "text-slate-500 hover:bg-orange-50 hover:text-[#c2510e]"
              }`}
            >
              <Icon size={17} />
              {label}
            </button>
          ))}
        </nav>

        {/* User footer */}
        <div className="border-t border-[#f0ddd0] px-5 py-4">
          <div className="mb-1 text-sm font-bold text-[#c2510e] truncate">
            {user?.full_name ?? "—"}
          </div>
          <div className="text-xs text-slate-400 truncate mb-3">
            {user?.designation ?? user?.department ?? "Trainer"}
          </div>
          <button
            onClick={logout}
            className="flex w-full items-center gap-2 rounded-lg px-3 py-2 text-sm font-semibold text-slate-500 hover:bg-orange-50 transition-colors"
          >
            <LogOut size={16} />
            Log out
          </button>
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
        className="fixed left-4 top-4 z-50 rounded-lg bg-white p-2 shadow border border-[#f0ddd0] lg:hidden"
        onClick={() => setSidebarOpen(!sidebarOpen)}
        aria-label="Toggle sidebar"
      >
        {sidebarOpen ? <X size={20} /> : <Menu size={20} />}
      </button>

      {/* ── Main content ── */}
      <main className="lg:ml-[264px]">
        <header className="flex h-[68px] items-center justify-between border-b border-[#f0ddd0] bg-white px-6 lg:px-9">
          <div>
            <div className="text-[10px] font-bold uppercase tracking-[.14em] text-slate-400">
              Trainer workspace
            </div>
            <h1 className="text-lg font-bold text-[#c2510e]">{activePage}</h1>
          </div>
          <div className="flex items-center gap-3">
            <span className="hidden text-xs font-semibold text-slate-500 sm:block truncate max-w-[160px]">
              {user?.full_name}
            </span>
            <button
              onClick={logout}
              className="rounded-lg border border-[#f0ddd0] px-3 py-1.5 text-xs font-bold text-[#c2510e] hover:bg-orange-50 transition-colors"
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

export default TrainerLayout;
