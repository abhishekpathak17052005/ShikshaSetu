import React, { useEffect, useState } from "react";
import {
  AlertTriangle,
  Brain,
  CheckCircle2,
  Filter,
  Layers,
  RefreshCw,
  TrendingDown,
  TrendingUp,
} from "lucide-react";
import { api, clearApiCache, SkillGapAnalyticsResponse, OrganizationGapItem } from "@/lib/api";
import { DEPARTMENT_TAXONOMY } from "@/lib/departments";
import { toast } from "sonner";
import { NumberReveal } from "@/components/motion/MotionUtils";

interface SkillGapAnalyticsProps {
  onNavigate: (page: string) => void;
}

export function SkillGapAnalytics({ onNavigate }: SkillGapAnalyticsProps) {
  const [data, setData] = useState<SkillGapAnalyticsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [selectedPriority, setSelectedPriority] = useState("ALL");
  const [selectedDepartment, setSelectedDepartment] = useState("ALL");

  const fetchGaps = async (dept?: string) => {
    clearApiCache();
    try {
      setLoading(true);
      const targetDept = dept !== undefined ? dept : selectedDepartment;
      const res = await api.admin.skillGaps(targetDept === "ALL" ? undefined : targetDept);
      setData(res);
    } catch (err: any) {
      toast.error(err.message || "Failed to load skill gap analytics");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchGaps(selectedDepartment);
  }, [selectedDepartment]);

  const filteredGaps = (data?.top_organization_gaps || []).filter((g) => {
    if (selectedPriority === "ALL") return true;
    return g.priority === selectedPriority;
  });

  return (
    <div className="space-y-8 anim-page-enter max-w-6xl mx-auto">
      {/* Header */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between anim-fade-up">
        <div>
          <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-[#123057]">
            Organization-Wide Skill Gap Analytics
          </h1>
          <p className="text-sm text-slate-500 mt-1">
            Aggregated capability deficits prioritized by administrative role impact and deficit size.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2">
            <label className="text-xs font-semibold text-slate-500 whitespace-nowrap">Department:</label>
            <select
              value={selectedDepartment}
              onChange={(e) => setSelectedDepartment(e.target.value)}
              className="rounded-xl border border-purple-200 bg-white px-3 py-2 text-xs font-semibold text-[#4b36a8] focus:border-[#4b36a8] focus:outline-none shadow-sm"
            >
              <option value="ALL">All Ministries & Departments</option>
              {DEPARTMENT_TAXONOMY.map((d) => (
                <option key={d.department_code} value={d.department_name}>
                  {d.department_name}
                </option>
              ))}
            </select>
          </div>

          <button
            onClick={() => fetchGaps()}
            className="flex items-center gap-1.5 rounded-xl border border-[#e0daef] bg-white px-4 py-2 text-xs font-semibold text-[#4b36a8] shadow-sm hover:bg-purple-50 btn-interactive"
          >
            <RefreshCw size={14} className={loading ? "animate-spin" : ""} /> Refresh
          </button>
        </div>
      </div>


      {/* 4 Priority Counters */}
      <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
        <div className="rounded-2xl border border-[#e0daef] bg-white p-5 shadow-sm card-interactive anim-card-enter stagger-1">
          <div className="flex items-center justify-between text-slate-400">
            <span className="text-[10px] font-semibold uppercase tracking-wider">Critical Priority</span>
            <AlertTriangle size={16} className="text-rose-600" />
          </div>
          <div className="mt-2 text-3xl font-extrabold tracking-tight text-rose-600">
            <NumberReveal value={data?.critical_gaps_count ?? 0} />
          </div>
          <div className="mt-1 text-xs text-slate-400 font-medium">Immediate intervention required</div>
        </div>

        <div className="rounded-2xl border border-[#e0daef] bg-white p-5 shadow-sm card-interactive anim-card-enter stagger-2">
          <div className="flex items-center justify-between text-slate-400">
            <span className="text-[10px] font-semibold uppercase tracking-wider">High Priority</span>
            <TrendingDown size={16} className="text-orange-600" />
          </div>
          <div className="mt-2 text-3xl font-extrabold tracking-tight text-[#ef7e37]">
            <NumberReveal value={data?.high_gaps_count ?? 0} />
          </div>
          <div className="mt-1 text-xs text-slate-400 font-medium">Deficit &gt; 1.0 points</div>
        </div>

        <div className="rounded-2xl border border-[#e0daef] bg-white p-5 shadow-sm card-interactive anim-card-enter stagger-3">
          <div className="flex items-center justify-between text-slate-400">
            <span className="text-[10px] font-semibold uppercase tracking-wider">Medium Priority</span>
            <Layers size={16} className="text-amber-600" />
          </div>
          <div className="mt-2 text-3xl font-extrabold tracking-tight text-amber-600">
            <NumberReveal value={data?.medium_gaps_count ?? 0} />
          </div>
          <div className="mt-1 text-xs text-slate-400 font-medium">Moderate proficiency gaps</div>
        </div>

        <div className="rounded-2xl border border-[#e0daef] bg-white p-5 shadow-sm card-interactive anim-card-enter stagger-4">
          <div className="flex items-center justify-between text-slate-400">
            <span className="text-[10px] font-semibold uppercase tracking-wider">On Track / Met</span>
            <CheckCircle2 size={16} className="text-[#087f76]" />
          </div>
          <div className="mt-2 text-3xl font-extrabold tracking-tight text-[#087f76]">
            <NumberReveal value={data?.low_gaps_count ?? 0} />
          </div>
          <div className="mt-1 text-xs text-slate-400 font-medium">Meeting role expectations</div>
        </div>
      </div>

      {/* Filter and Top Gaps List */}
      <div className="rounded-3xl border border-[#e0daef] bg-white shadow-sm overflow-hidden p-6 space-y-6 anim-card-enter stagger-5">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between border-b border-slate-100 pb-4">
          <div>
            <h3 className="text-base font-bold text-[#123057] tracking-tight">
              Priority Capability Deficit Ledger ({filteredGaps.length})
            </h3>
            <p className="text-xs text-slate-400 mt-0.5">
              Ranked by organizational prevalence and administrative criticality.
            </p>
          </div>

          <div className="flex items-center gap-2">
            <Filter size={15} className="text-slate-400" />
            <select
              value={selectedPriority}
              onChange={(e) => setSelectedPriority(e.target.value)}
              className="rounded-xl border border-slate-200 bg-white px-3 py-1.5 text-xs font-semibold text-slate-700 focus:outline-none"
            >
              <option value="ALL">All Priorities</option>
              <option value="CRITICAL">Critical Only</option>
              <option value="HIGH">High Priority</option>
              <option value="MEDIUM">Medium Priority</option>
            </select>
          </div>
        </div>

        <div className="grid gap-4 sm:grid-cols-2">
          {filteredGaps.map((gap, gIdx) => {
            const staggerCls = `stagger-${Math.min((gIdx % 6) + 1, 8)}`;
            return (
              <div
                key={gap.competency_id}
                className={`rounded-2xl border border-[#dfe7f0] bg-[#fdfcff] p-5 hover:border-[#6d5bc3] card-interactive anim-card-enter ${staggerCls} transition-all space-y-3`}
              >
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <span className="rounded-md bg-purple-100 px-2 py-0.5 text-[10px] font-semibold uppercase text-[#4b36a8] anim-badge-pop tracking-wider">
                      {gap.domain} · <span className="font-mono text-[10px] font-medium">{gap.competency_code}</span>
                    </span>
                    <h4 className="text-base font-bold text-[#123057] mt-1.5 tracking-tight">
                      {gap.competency_name}
                    </h4>
                  </div>

                  <span
                    className={`rounded-full px-2.5 py-0.5 text-[10px] font-semibold anim-badge-pop tracking-wider ${
                      gap.priority === "CRITICAL"
                        ? "bg-rose-100 text-rose-800"
                        : gap.priority === "HIGH"
                        ? "bg-orange-100 text-orange-800"
                        : "bg-amber-100 text-amber-800"
                    }`}
                  >
                    {gap.priority}
                  </span>
                </div>

                <div className="grid grid-cols-2 gap-2 rounded-xl bg-slate-50 p-3 text-xs">
                  <div>
                    <span className="text-slate-400 font-medium">Officials Affected:</span>
                    <div className="font-bold text-[#123057] mt-0.5">{gap.officials_affected} personnel</div>
                  </div>
                  <div>
                    <span className="text-slate-400 font-medium">Average Deficit:</span>
                    <div className="font-bold text-rose-600 mt-0.5">{gap.average_gap.toFixed(1)} points</div>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}

export default SkillGapAnalytics;
