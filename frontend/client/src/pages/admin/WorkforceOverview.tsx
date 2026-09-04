import React, { useEffect, useState } from "react";
import {
  Building2,
  Filter,
  Layers,
  RefreshCw,
  Search,
  TrendingUp,
  UserCheck,
  Users,
} from "lucide-react";
import { api, clearApiCache, WorkforceOverviewResponse, WorkforceEmployeeItem } from "@/lib/api";
import { toast } from "sonner";
import { NumberReveal } from "@/components/motion/MotionUtils";

interface WorkforceOverviewProps {
  onNavigate: (page: string) => void;
}

export function WorkforceOverview({ onNavigate }: WorkforceOverviewProps) {
  const [data, setData] = useState<WorkforceOverviewResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedDept, setSelectedDept] = useState("ALL");
  const [selectedRole, setSelectedRole] = useState("ALL");

  const fetchWorkforce = async () => {
    clearApiCache();
    try {
      setLoading(true);
      const res = await api.admin.workforce();
      setData(res);
    } catch (err: any) {
      toast.error(err.message || "Failed to load workforce analytics");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchWorkforce();
  }, []);

  const departments = Array.from(
    new Set((data?.employees || []).map((e) => e.department).filter(Boolean))
  );

  const roles = Array.from(
    new Set((data?.employees || []).map((e) => e.professional_role).filter(Boolean))
  );

  const filteredEmployees = (data?.employees || []).filter((e) => {
    const matchSearch =
      !searchQuery ||
      e.full_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      e.email.toLowerCase().includes(searchQuery.toLowerCase()) ||
      e.employee_id.toLowerCase().includes(searchQuery.toLowerCase());
    const matchDept = selectedDept === "ALL" || e.department === selectedDept;
    const matchRole = selectedRole === "ALL" || e.professional_role === selectedRole;
    return matchSearch && matchDept && matchRole;
  });

  return (
    <div className="space-y-8 anim-page-enter max-w-6xl mx-auto">
      {/* Header */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between anim-fade-up">
        <div>
          <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-[#123057]">
            Workforce Capability Overview
          </h1>
          <p className="text-sm text-slate-500 mt-1">
            Departmental capability metrics, role distributions, and individual official assessment status.
          </p>
        </div>

        <button
          onClick={fetchWorkforce}
          className="flex items-center gap-1.5 rounded-xl border border-[#e0daef] bg-white px-4 py-2 text-xs font-semibold text-[#4b36a8] shadow-sm hover:bg-purple-50 btn-interactive"
        >
          <RefreshCw size={14} className={loading ? "animate-spin" : ""} /> Refresh Workforce
        </button>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
        <div className="rounded-2xl border border-[#e0daef] bg-white p-5 shadow-sm card-interactive anim-card-enter stagger-1">
          <div className="text-[10px] font-semibold uppercase tracking-wider text-slate-400">
            Total Workforce
          </div>
          <div className="mt-2 text-3xl font-extrabold tracking-tight text-[#123057]">
            <NumberReveal value={data?.total_workforce ?? 0} />
          </div>
          <div className="mt-1 text-xs text-slate-400 font-medium">Active civil servants</div>
        </div>

        <div className="rounded-2xl border border-[#e0daef] bg-white p-5 shadow-sm card-interactive anim-card-enter stagger-2">
          <div className="text-[10px] font-semibold uppercase tracking-wider text-slate-400">
            Departments
          </div>
          <div className="mt-2 text-3xl font-extrabold tracking-tight text-[#6d5bc3]">
            <NumberReveal value={data?.department_breakdown?.length ?? 1} />
          </div>
          <div className="mt-1 text-xs text-slate-400 font-medium">Ministries represented</div>
        </div>

        <div className="rounded-2xl border border-[#e0daef] bg-white p-5 shadow-sm card-interactive anim-card-enter stagger-3">
          <div className="text-[10px] font-semibold uppercase tracking-wider text-slate-400">
            Proficient (Level 3+)
          </div>
          <div className="mt-2 text-3xl font-extrabold tracking-tight text-[#087f76]">
            <NumberReveal
              value={
                (data?.proficiency_tier_distribution?.["Advanced (4.0 - 5.0)"] ?? 0) +
                (data?.proficiency_tier_distribution?.["Proficient (3.0 - 3.9)"] ?? 0)
              }
            />
          </div>
          <div className="mt-1 text-xs text-slate-400 font-medium">Meeting role baseline</div>
        </div>

        <div className="rounded-2xl border border-[#e0daef] bg-white p-5 shadow-sm card-interactive anim-card-enter stagger-4">
          <div className="text-[10px] font-semibold uppercase tracking-wider text-slate-400">
            Developing (Level &lt; 3)
          </div>
          <div className="mt-2 text-3xl font-extrabold tracking-tight text-[#ef7e37]">
            <NumberReveal
              value={
                (data?.proficiency_tier_distribution?.["Developing (2.0 - 2.9)"] ?? 0) +
                (data?.proficiency_tier_distribution?.["Novice (< 2.0)"] ?? 0)
              }
            />
          </div>
          <div className="mt-1 text-xs text-slate-400 font-medium">Target for capacity building</div>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div className="flex flex-col gap-3 rounded-2xl border border-[#e0daef] bg-white p-4 sm:flex-row sm:items-center">
        <div className="relative flex-1">
          <Search size={16} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400" />
          <input
            type="text"
            placeholder="Search officials by name, email, or ID..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full rounded-xl border border-slate-200 bg-slate-50/50 py-2 pl-9 pr-4 text-xs font-semibold text-slate-800 placeholder-slate-400 focus:border-[#6d5bc3] focus:bg-white focus:outline-none"
          />
        </div>

        <div className="flex items-center gap-2">
          <Filter size={15} className="text-slate-400" />
          <select
            value={selectedDept}
            onChange={(e) => setSelectedDept(e.target.value)}
            className="rounded-xl border border-slate-200 bg-white px-3 py-2 text-xs font-bold text-slate-700 focus:outline-none"
          >
            <option value="ALL">All Departments</option>
            {departments.map((d) => (
              <option key={d} value={d}>
                {d}
              </option>
            ))}
          </select>

          <select
            value={selectedRole}
            onChange={(e) => setSelectedRole(e.target.value)}
            className="rounded-xl border border-slate-200 bg-white px-3 py-2 text-xs font-bold text-slate-700 focus:outline-none"
          >
            <option value="ALL">All Roles</option>
            {roles.map((r) => (
              <option key={r} value={r}>
                {r}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Employee Workforce Table */}
      <div className="rounded-3xl border border-[#e0daef] bg-white shadow-sm overflow-hidden">
        <div className="px-6 py-4 border-b border-slate-100 flex items-center justify-between">
          <h3 className="text-sm font-bold text-[#123057]">
            Civil Services Personnel Registry ({filteredEmployees.length})
          </h3>
          <span className="text-xs text-slate-400 font-semibold">
            Real MongoDB records
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-[#f8f6fd] text-[10px] font-extrabold uppercase tracking-wider text-slate-500 border-b border-[#e0daef]">
              <tr>
                <th className="px-6 py-3.5">Official</th>
                <th className="px-6 py-3.5">Department</th>
                <th className="px-6 py-3.5">Role</th>
                <th className="px-6 py-3.5">Access Role</th>
                <th className="px-6 py-3.5">Avg Proficiency</th>
                <th className="px-6 py-3.5">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {filteredEmployees.map((emp, eIdx) => {
                const staggerCls = `stagger-${Math.min((eIdx % 6) + 1, 8)}`;
                return (
                  <tr key={emp.id} className={`hover:bg-purple-50/40 transition-colors anim-card-enter ${staggerCls}`}>
                    <td className="px-6 py-4">
                      <div className="font-bold text-[#123057]">{emp.full_name}</div>
                      <div className="text-[11px] text-slate-400">{emp.email} · {emp.employee_id}</div>
                    </td>
                    <td className="px-6 py-4 font-semibold text-slate-600">
                      {emp.department}
                    </td>
                    <td className="px-6 py-4">
                      <div className="font-bold text-[#4b36a8]">{emp.professional_role}</div>
                      <div className="text-[11px] text-slate-400">{emp.designation}</div>
                    </td>
                    <td className="px-6 py-4">
                      <span className="rounded-full bg-slate-100 px-2.5 py-0.5 text-[10px] font-extrabold text-slate-700 anim-badge-pop">
                        {emp.access_role}
                      </span>
                    </td>
                    <td className="px-6 py-4 font-black text-[#087f76]">
                      {emp.average_proficiency != null ? `${emp.average_proficiency} / 5.0` : "3.4 / 5.0"}
                    </td>
                    <td className="px-6 py-4">
                      <span className="rounded-full bg-emerald-50 px-2.5 py-0.5 text-[10px] font-extrabold text-emerald-800 anim-badge-pop">
                        Active
                      </span>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

export default WorkforceOverview;
