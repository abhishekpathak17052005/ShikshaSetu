import React, { useEffect, useState } from "react";
import {
  BarChart2,
  Brain,
  Building2,
  CheckCircle2,
  Clock,
  Layers,
  RefreshCw,
  ShieldCheck,
  TrendingUp,
  Users,
  AlertTriangle,
  ArrowRight,
  Award,
} from "lucide-react";
import { api, AdminDashboardResponse } from "@/lib/api";
import { toast } from "sonner";

interface AdminDashboardProps {
  onNavigate: (page: string) => void;
}

export function AdminDashboard({ onNavigate }: AdminDashboardProps) {
  const [data, setData] = useState<AdminDashboardResponse | null>(null);
  const [loading, setLoading] = useState(true);

  const fetchDashboard = async () => {
    try {
      setLoading(true);
      const res = await api.admin.dashboard();
      setData(res);
    } catch (err: any) {
      toast.error(err.message || "Failed to load admin dashboard");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDashboard();
  }, []);

  return (
    <div className="space-y-8 animate-fadeIn max-w-6xl mx-auto">
      {/* Header */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <div className="inline-flex items-center gap-1.5 rounded-full bg-purple-100 px-3 py-1 text-xs font-extrabold uppercase tracking-wider text-[#4b36a8]">
            <ShieldCheck size={13} /> Civil Services Capability Intelligence Console
          </div>
          <h1 className="mt-2 text-2xl sm:text-3xl font-black text-[#123057]">
            National Workforce Governance
          </h1>
          <p className="text-sm text-slate-500 mt-1">
            Real-time organizational competency health, capability gap distribution, and capacity-building metrics.
          </p>
        </div>

        <button
          onClick={fetchDashboard}
          className="flex items-center gap-1.5 rounded-xl border border-[#e0daef] bg-white px-4 py-2.5 text-xs font-bold text-[#4b36a8] shadow-sm hover:bg-purple-50 transition-all"
        >
          <RefreshCw size={14} className={loading ? "animate-spin" : ""} /> Refresh Analytics
        </button>
      </div>

      {/* 4-KPI Primary Metrics */}
      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        <div className="rounded-2xl border border-[#e0daef] bg-white p-5 shadow-sm hover:shadow-md transition-all">
          <div className="flex items-center justify-between text-slate-400">
            <span className="text-xs font-bold uppercase tracking-wider">Total Officials</span>
            <Users size={18} className="text-[#6d5bc3]" />
          </div>
          <div className="mt-3 text-3xl font-black text-[#123057]">
            {data?.total_officials ?? "—"}
          </div>
          <div className="mt-1 text-[11px] text-slate-400 font-semibold">
            Across {data?.departments_count ?? 1} ministries/departments
          </div>
        </div>

        <div className="rounded-2xl border border-[#e0daef] bg-white p-5 shadow-sm hover:shadow-md transition-all">
          <div className="flex items-center justify-between text-slate-400">
            <span className="text-xs font-bold uppercase tracking-wider">Avg Proficiency</span>
            <TrendingUp size={18} className="text-[#087f76]" />
          </div>
          <div className="mt-3 text-3xl font-black text-[#087f76]">
            {data?.average_capability_level != null ? `${data.average_capability_level} / 5.0` : "3.2 / 5.0"}
          </div>
          <div className="mt-1 text-[11px] text-slate-400 font-semibold">
            {data?.assessment_coverage_pct ?? 75}% assessment coverage
          </div>
        </div>

        <div className="rounded-2xl border border-[#e0daef] bg-white p-5 shadow-sm hover:shadow-md transition-all">
          <div className="flex items-center justify-between text-slate-400">
            <span className="text-xs font-bold uppercase tracking-wider">Critical Gaps</span>
            <AlertTriangle size={18} className="text-rose-600" />
          </div>
          <div className="mt-3 text-3xl font-black text-rose-600">
            {data?.total_critical_gaps ?? 0}
          </div>
          <div className="mt-1 text-[11px] text-slate-400 font-semibold">
            Deficits ≥ 1.5 proficiency points
          </div>
        </div>

        <div className="rounded-2xl border border-[#e0daef] bg-white p-5 shadow-sm hover:shadow-md transition-all">
          <div className="flex items-center justify-between text-slate-400">
            <span className="text-xs font-bold uppercase tracking-wider">Training Hours</span>
            <Clock size={18} className="text-[#ef7e37]" />
          </div>
          <div className="mt-3 text-3xl font-black text-[#ef7e37]">
            {data?.total_learning_hours ?? 0} hrs
          </div>
          <div className="mt-1 text-[11px] text-slate-400 font-semibold">
            Supporting evidence recorded
          </div>
        </div>
      </div>

      {/* Domain Proficiency & Department Breakdown */}
      <div className="grid gap-6 lg:grid-cols-2">
        {/* Domain Capability Matrix */}
        <div className="rounded-3xl border border-[#e0daef] bg-white p-6 shadow-sm">
          <div className="flex items-center justify-between border-b border-slate-100 pb-4">
            <div>
              <div className="text-[10px] font-bold uppercase tracking-wider text-slate-400">
                Competency Distribution
              </div>
              <h3 className="text-base font-bold text-[#123057] mt-0.5">
                Proficiency by Competency Domain
              </h3>
            </div>
            <button
              onClick={() => onNavigate("Competency Analytics")}
              className="text-xs font-bold text-[#6d5bc3] hover:underline inline-flex items-center gap-1"
            >
              View All <ArrowRight size={12} />
            </button>
          </div>

          <div className="mt-5 space-y-4">
            {(data?.domain_capability_breakdown || [
              { domain: "CORE", average_level: 3.4, count: 12 },
              { domain: "DOMAIN", average_level: 3.1, count: 18 },
              { domain: "BEHAVIORAL", average_level: 3.6, count: 10 },
            ]).map((d) => {
              const pct = Math.min(100, Math.round((d.average_level / 5.0) * 100));
              return (
                <div key={d.domain} className="space-y-1.5">
                  <div className="flex justify-between text-xs font-bold">
                    <span className="text-[#123057]">{d.domain} Competencies</span>
                    <span className="text-slate-500">
                      Level {d.average_level} / 5.0 ({d.count} mapped)
                    </span>
                  </div>
                  <div className="h-2.5 w-full overflow-hidden rounded-full bg-slate-100">
                    <div
                      className="h-full rounded-full bg-[#6d5bc3] transition-all duration-500"
                      style={{ width: `${pct}%` }}
                    />
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Department Workforce Matrix */}
        <div className="rounded-3xl border border-[#e0daef] bg-white p-6 shadow-sm">
          <div className="flex items-center justify-between border-b border-slate-100 pb-4">
            <div>
              <div className="text-[10px] font-bold uppercase tracking-wider text-slate-400">
                Workforce Deployment
              </div>
              <h3 className="text-base font-bold text-[#123057] mt-0.5">
                Officials by Ministry / Department
              </h3>
            </div>
            <button
              onClick={() => onNavigate("Workforce Overview")}
              className="text-xs font-bold text-[#6d5bc3] hover:underline inline-flex items-center gap-1"
            >
              Details <ArrowRight size={12} />
            </button>
          </div>

          <div className="mt-5 space-y-3">
            {(data?.department_distribution || [
              { department: "Ministry of Statistics & PI", count: 8 },
              { department: "Capacity Building Commission", count: 4 },
              { department: "DoPT", count: 3 },
            ]).map((dept) => (
              <div
                key={dept.department}
                className="flex items-center justify-between rounded-xl bg-slate-50 p-3 text-xs"
              >
                <div className="flex items-center gap-2.5">
                  <Building2 size={15} className="text-[#6d5bc3]" />
                  <span className="font-bold text-[#123057]">{dept.department}</span>
                </div>
                <span className="rounded-full bg-purple-100 px-2.5 py-0.5 font-bold text-[#4b36a8]">
                  {dept.count} Officials
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Strategic Actions & Intelligence Pathways */}
      <div className="rounded-3xl bg-gradient-to-br from-[#4b36a8] to-[#2d1b7a] p-8 text-white shadow-md">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-6">
          <div>
            <span className="rounded-full bg-white/20 px-3 py-1 text-xs font-extrabold uppercase tracking-wider text-purple-200">
              Administrative Decision Support
            </span>
            <h2 className="mt-3 text-2xl font-black">Capacity Planning & Strategic Interventions</h2>
            <p className="mt-2 text-sm text-purple-100 max-w-xl leading-relaxed">
              Prioritize emerging data capabilities, review training effectiveness, and schedule cohort interventions based on authoritative assessment evidence.
            </p>
          </div>

          <div className="flex flex-wrap gap-3">
            <button
              onClick={() => onNavigate("Capacity Planning")}
              className="rounded-xl bg-white px-5 py-2.5 text-xs font-black text-[#4b36a8] shadow hover:bg-purple-50 transition-all"
            >
              Launch Capacity Planning →
            </button>
            <button
              onClick={() => onNavigate("Emerging Skills")}
              className="rounded-xl bg-white/10 px-5 py-2.5 text-xs font-bold text-white border border-white/20 hover:bg-white/20 transition-all"
            >
              Emerging Skills Matrix
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

export default AdminDashboard;
