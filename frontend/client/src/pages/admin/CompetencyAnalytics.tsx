import React, { useEffect, useState } from "react";
import {
  BarChart2,
  Filter,
  Layers,
  RefreshCw,
  Search,
  SlidersHorizontal,
  TrendingUp,
  AlertCircle,
} from "lucide-react";
import { api, clearApiCache, CompetencyAnalyticsResponse, CompetencyAnalyticsItem } from "@/lib/api";
import { toast } from "sonner";
import { NumberReveal } from "@/components/motion/MotionUtils";

interface CompetencyAnalyticsProps {
  onNavigate: (page: string) => void;
}

export function CompetencyAnalytics({ onNavigate }: CompetencyAnalyticsProps) {
  const [data, setData] = useState<CompetencyAnalyticsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [selectedDomain, setSelectedDomain] = useState("ALL");
  const [searchQuery, setSearchQuery] = useState("");

  const fetchCompetencies = async () => {
    clearApiCache();
    try {
      setLoading(true);
      const res = await api.admin.competencies();
      setData(res);
    } catch (err: any) {
      toast.error(err.message || "Failed to load competency analytics");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCompetencies();
  }, []);

  const domains = Array.from(
    new Set((data?.competencies || []).map((c) => c.domain).filter(Boolean))
  );

  const filteredCompetencies = (data?.competencies || []).filter((c) => {
    const matchDomain = selectedDomain === "ALL" || c.domain === selectedDomain;
    const matchSearch =
      !searchQuery ||
      c.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      c.code.toLowerCase().includes(searchQuery.toLowerCase());
    return matchDomain && matchSearch;
  });

  return (
    <div className="space-y-8 anim-page-enter max-w-6xl mx-auto">
      {/* Header */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between anim-fade-up">
        <div>
          <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-[#123057]">
            Competency Intelligence Matrix
          </h1>
          <p className="text-sm text-slate-500 mt-1">
            Organization-wide proficiency levels vs required baselines across all 42 competency taxonomy elements.
          </p>
        </div>

        <button
          onClick={fetchCompetencies}
          className="flex items-center gap-1.5 rounded-xl border border-[#e0daef] bg-white px-4 py-2 text-xs font-semibold text-[#4b36a8] shadow-sm hover:bg-purple-50 btn-interactive"
        >
          <RefreshCw size={14} className={loading ? "animate-spin" : ""} /> Refresh Matrix
        </button>
      </div>

      {/* Domain Breakdown Row */}
      <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
        <div className="rounded-2xl border border-[#e0daef] bg-white p-5 shadow-sm card-interactive anim-card-enter stagger-1">
          <div className="text-[10px] font-semibold uppercase tracking-wider text-slate-400">
            Total Framework Competencies
          </div>
          <div className="mt-2 text-3xl font-extrabold tracking-tight text-[#123057]">
            <NumberReveal value={data?.total_competencies ?? 42} />
          </div>
          <div className="mt-1 text-xs text-slate-400 font-medium">Standardized taxonomy</div>
        </div>

        <div className="rounded-2xl border border-[#e0daef] bg-white p-5 shadow-sm card-interactive anim-card-enter stagger-2">
          <div className="text-[10px] font-semibold uppercase tracking-wider text-slate-400">
            Core Domain
          </div>
          <div className="mt-2 text-3xl font-extrabold tracking-tight text-[#6d5bc3]">
            <NumberReveal value={data?.domain_breakdown?.find((d) => d.domain === "CORE")?.count ?? 12} />
          </div>
          <div className="mt-1 text-xs text-slate-400 font-medium">Foundational civil service skills</div>
        </div>

        <div className="rounded-2xl border border-[#e0daef] bg-white p-5 shadow-sm card-interactive anim-card-enter stagger-3">
          <div className="text-[10px] font-semibold uppercase tracking-wider text-slate-400">
            Domain-Specific
          </div>
          <div className="mt-2 text-3xl font-extrabold tracking-tight text-[#087f76]">
            <NumberReveal value={data?.domain_breakdown?.find((d) => d.domain === "DOMAIN")?.count ?? 18} />
          </div>
          <div className="mt-1 text-xs text-slate-400 font-medium">Technical & statistical capabilities</div>
        </div>

        <div className="rounded-2xl border border-[#e0daef] bg-white p-5 shadow-sm card-interactive anim-card-enter stagger-4">
          <div className="text-[10px] font-semibold uppercase tracking-wider text-slate-400">
            Behavioral
          </div>
          <div className="mt-2 text-3xl font-extrabold tracking-tight text-[#ef7e37]">
            <NumberReveal value={data?.domain_breakdown?.find((d) => d.domain === "BEHAVIORAL")?.count ?? 12} />
          </div>
          <div className="mt-1 text-xs text-slate-400 font-medium">Leadership & public service</div>
        </div>
      </div>

      {/* Filter Bar */}
      <div className="flex flex-col gap-3 rounded-2xl border border-[#e0daef] bg-white p-4 sm:flex-row sm:items-center">
        <div className="relative flex-1">
          <Search size={16} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400" />
          <input
            type="text"
            placeholder="Search competencies by name or code..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full rounded-xl border border-slate-200 bg-slate-50/50 py-2 pl-9 pr-4 text-xs font-semibold text-slate-800 placeholder-slate-400 focus:border-[#6d5bc3] focus:bg-white focus:outline-none"
          />
        </div>

        <div className="flex items-center gap-2">
          <Filter size={15} className="text-slate-400" />
          <select
            value={selectedDomain}
            onChange={(e) => setSelectedDomain(e.target.value)}
            className="rounded-xl border border-slate-200 bg-white px-3 py-2 text-xs font-semibold text-slate-700 focus:outline-none"
          >
            <option value="ALL">All Domains</option>
            {domains.map((d) => (
              <option key={d} value={d}>
                {d}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Table Container */}
      <div className="rounded-3xl border border-[#e0daef] bg-white shadow-sm overflow-hidden">
        <div className="px-6 py-4 border-b border-slate-100 flex items-center justify-between">
          <h3 className="text-sm font-bold text-[#123057]">
            Competency Performance Indicators ({filteredCompetencies.length})
          </h3>
          <span className="text-xs text-slate-400 font-medium">
            Aggregated official assessments
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-[#f8f6fd] text-[10px] font-semibold uppercase tracking-wider text-slate-500 border-b border-[#e0daef]">
              <tr>
                <th className="px-6 py-3.5">Competency</th>
                <th className="px-6 py-3.5">Domain</th>
                <th className="px-6 py-3.5">Required Lvl</th>
                <th className="px-6 py-3.5">Avg Current Lvl</th>
                <th className="px-6 py-3.5">Avg Deficit</th>
                <th className="px-6 py-3.5">% Meeting Target</th>
                <th className="px-6 py-3.5">Priority</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {filteredCompetencies.map((comp, cIdx) => {
                const staggerCls = `stagger-${Math.min((cIdx % 6) + 1, 8)}`;
                return (
                  <tr key={comp.competency_id} className={`hover:bg-purple-50/40 transition-colors anim-card-enter ${staggerCls}`}>
                    <td className="px-6 py-4">
                      <div className="font-bold text-[#123057]">{comp.name}</div>
                      <div className="font-mono text-[10px] font-medium tracking-tight text-slate-400 uppercase">{comp.code}</div>
                    </td>
                    <td className="px-6 py-4">
                      <span className="rounded-md bg-purple-50 px-2 py-0.5 text-[10px] font-semibold text-[#4b36a8] anim-badge-pop tracking-wider">
                        {comp.domain}
                      </span>
                    </td>
                    <td className="px-6 py-4 font-semibold text-slate-700">
                      {comp.average_required_level.toFixed(1)}
                    </td>
                    <td className="px-6 py-4 font-semibold text-[#087f76]">
                      {comp.average_current_level.toFixed(1)}
                    </td>
                    <td className="px-6 py-4 font-bold text-[#ef7e37]">
                      {comp.average_gap.toFixed(1)}
                    </td>
                    <td className="px-6 py-4 font-medium text-slate-600">
                      {comp.meeting_requirement_pct}%
                    </td>
                    <td className="px-6 py-4">
                      <span
                        className={`rounded-full px-2.5 py-0.5 text-[10px] font-semibold anim-badge-pop tracking-wider ${
                          comp.priority === "CRITICAL"
                            ? "bg-rose-100 text-rose-800"
                            : comp.priority === "HIGH"
                            ? "bg-orange-100 text-orange-800"
                            : "bg-teal-100 text-teal-800"
                        }`}
                      >
                        {comp.priority}
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

export default CompetencyAnalytics;
