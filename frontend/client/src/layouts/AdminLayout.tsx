import React, { useState } from "react";
import {
  BarChart2,
  Brain,
  BriefcaseBusiness,
  Building2,
  CalendarRange,
  FileBarChart,
  LayoutDashboard,
  LogOut,
  Menu,
  TrendingUp,
  Users,
  UserRound,
  Zap,
  X,
} from "lucide-react";
import { useAuth } from "@/contexts/AuthContext";

// ─── Navigation items ─────────────────────────────────────────────────────────

const NAV_ITEMS = [
  { id: "Dashboard", label: "Dashboard", icon: LayoutDashboard },
  { id: "Workforce Overview", label: "Workforce Overview", icon: Building2 },
  { id: "Competency Analytics", label: "Competency Analytics", icon: BarChart2 },
  { id: "Skill Gap Analytics", label: "Skill Gap Analytics", icon: Brain },
  { id: "Training Effectiveness", label: "Training Effectiveness", icon: TrendingUp },
  { id: "Emerging Skills", label: "Emerging Skills", icon: Zap },
  { id: "Capacity Planning", label: "Capacity Planning", icon: CalendarRange },
  { id: "Users", label: "Users", icon: Users },
  { id: "Reports", label: "Reports", icon: FileBarChart },
  { id: "Profile", label: "Profile", icon: UserRound },
] as const;

// ─── Props ────────────────────────────────────────────────────────────────────

interface AdminLayoutProps {
  children: React.ReactNode;
  activePage: string;
  onNavigate: (page: string) => void;
}

// ─── Component ────────────────────────────────────────────────────────────────

export function AdminLayout({ children, activePage, onNavigate }: AdminLayoutProps) {
  const { user, logout } = useAuth();
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const handleNav = (page: string) => {
    onNavigate(page);
    setSidebarOpen(false);
  };

  return (
    <div className="min-h-screen bg-[#f3f1fb] text-[#1a2744]">
      {/* ── Sidebar ── */}
      <aside
        className={`fixed inset-y-0 left-0 z-40 w-[264px] border-r border-[#e0daef] bg-white flex flex-col transition-transform lg:translate-x-0 ${
          sidebarOpen ? "translate-x-0" : "-translate-x-full"
        }`}
      >
        {/* Logo */}
        <div className="flex items-center gap-3 px-5 py-6">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-[#6d5bc3] text-white text-lg font-extrabold select-none">
            A
          </div>
          <div>
            <div className="text-[17px] font-extrabold text-[#4b36a8]">ShikshaSetu</div>
            <div className="text-[9px] font-bold uppercase tracking-[.18em] text-slate-400">
              Intelligence Console
            </div>
          </div>
        </div>

        {/* Section label */}
        <div className="px-7 mb-2 text-[10px] font-bold uppercase tracking-[.14em] text-slate-400">
          Admin workspace
        </div>

        {/* Nav items */}
        <nav className="flex-1 px-4 overflow-y-auto">
          {NAV_ITEMS.map(({ id, label, icon: Icon }) => (
            <button
              key={id}
              onClick={() => handleNav(id)}
              className={`mb-1 flex w-full items-center gap-3 rounded-xl px-3 py-2.5 text-left text-sm font-semibold transition-colors ${
                activePage === id
                  ? "bg-[#f0edfc] text-[#6d5bc3]"
                  : "text-slate-500 hover:bg-purple-50 hover:text-[#4b36a8]"
              }`}
            >
              <Icon size={17} />
              {label}
            </button>
          ))}
        </nav>

        {/* User footer */}
        <div className="border-t border-[#e0daef] px-5 py-4">
          <div className="mb-1 text-sm font-bold text-[#4b36a8] truncate">
            {user?.full_name ?? "—"}
          </div>
          <div className="text-xs text-slate-400 truncate mb-3">
            {user?.designation ?? user?.department ?? "Administrator"}
          </div>
          <button
            onClick={logout}
            className="flex w-full items-center gap-2 rounded-lg px-3 py-2 text-sm font-semibold text-slate-500 hover:bg-purple-50 transition-colors"
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
        className="fixed left-4 top-4 z-50 rounded-lg bg-white p-2 shadow border border-[#e0daef] lg:hidden"
        onClick={() => setSidebarOpen(!sidebarOpen)}
        aria-label="Toggle sidebar"
      >
        {sidebarOpen ? <X size={20} /> : <Menu size={20} />}
      </button>

      {/* ── Main content ── */}
      <main className="lg:ml-[264px]">
        <header className="flex h-[68px] items-center justify-between border-b border-[#e0daef] bg-white px-6 lg:px-9">
          <div>
            <div className="text-[10px] font-bold uppercase tracking-[.14em] text-slate-400">
              Admin workspace
            </div>
            <h1 className="text-lg font-bold text-[#4b36a8]">{activePage}</h1>
          </div>
          <div className="flex items-center gap-3">
            <span className="hidden text-xs font-semibold text-slate-500 sm:block truncate max-w-[160px]">
              {user?.full_name}
            </span>
            <button
              onClick={logout}
              className="rounded-lg border border-[#e0daef] px-3 py-1.5 text-xs font-bold text-[#4b36a8] hover:bg-purple-50 transition-colors"
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

export default AdminLayout;
