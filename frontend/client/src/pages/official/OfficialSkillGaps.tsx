import React, { useEffect, useState } from "react";
import {
  Target,
  ArrowRight,
  Sparkles,
  TrendingUp,
  AlertCircle,
  CheckCircle2,
  RefreshCw,
  BookOpen,
} from "lucide-react";
import { api, SkillGapResponse } from "@/lib/api";
import { useAuth } from "@/contexts/AuthContext";
import { PageSkeleton } from "@/components/PageSkeleton";
import { toast } from "sonner";

interface OfficialSkillGapsProps {
  onNavigate: (page: string, context?: { competencyCode?: string }) => void;
}

export function OfficialSkillGaps({ onNavigate }: OfficialSkillGapsProps) {
  const { user } = useAuth();
  const [skillGaps, setSkillGaps] = useState<SkillGapResponse | null>(null);
  const [loading, setLoading] = useState(true);

  const fetchSkillGaps = async () => {
    try {
      setLoading(true);
      const res = await api.skillGaps.me();
      setSkillGaps(res);
    } catch (err: any) {
      if (err.status !== 404) {
        toast.error(err.message || "Failed to load skill gaps");
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSkillGaps();
  }, []);

  if (loading && !skillGaps) {
    return <PageSkeleton />;
  }

  const summary = skillGaps?.summary;
  const gaps = skillGaps?.gaps || [];

  const overallStatus = summary?.critical_gaps
    ? "Needs Attention"
    : summary?.high_gaps
    ? "High Priority"
    : summary?.medium_gaps
    ? "Developing"
    : "On Track";

  const displayedRoleName =
    summary?.role_name ||
    skillGaps?.role ||
    (user?.designation ? `${user.designation} Framework` : "Role Capability Framework");

  return (
    <div className="space-y-6 animate-fadeIn">
      {/* Top Header */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-black text-[#123057]">Skill Gap Intelligence</h1>
          <p className="text-sm text-slate-500 mt-1">
            Automated capability gap calculation comparing current levels against official role requirements.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={fetchSkillGaps}
            className="flex items-center gap-1.5 rounded-xl border border-[#dfe7f0] bg-white px-3.5 py-2 text-xs font-bold text-slate-600 hover:bg-slate-50 transition-colors"
          >
            <RefreshCw size={14} className={loading ? "animate-spin" : ""} />
            Refresh
          </button>
          <button
            onClick={() => onNavigate("Recommendations")}
            className="flex items-center gap-2 rounded-xl bg-[#ef7e37] px-4 py-2 text-xs font-bold text-white shadow hover:bg-[#d96a27] transition-all"
          >
            <BookOpen size={14} /> View All Recommendations
          </button>
        </div>
      </div>

      {/* Role Requirement Summary Card */}
      <div className="rounded-2xl border border-[#dfe7f0] bg-white p-6 shadow-sm">
        <div className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-100 pb-4">
          <div>
            <div className="text-[10px] font-extrabold uppercase tracking-wider text-slate-400">
              Role Requirements Matrix
            </div>
            <h2 className="text-xl font-bold text-[#123057] mt-1">
              {displayedRoleName}
            </h2>
          </div>

          <span className="rounded-full bg-[#fff0e6] px-3.5 py-1.5 text-xs font-bold text-[#d96b27]">
            {overallStatus}
          </span>
        </div>

        {/* 4-Stat Metric Row */}
        <div className="mt-5 grid grid-cols-2 gap-3 sm:grid-cols-4">
          <div className="rounded-xl bg-[#f8fafc] p-4 border border-slate-100">
            <div className="text-[10px] font-bold uppercase tracking-wider text-slate-400">
              Total Skill Gaps
            </div>
            <div className="mt-2 text-2xl font-black text-[#ef7e37]">
              {summary?.total_gaps ?? gaps.length}
            </div>
          </div>

          <div className="rounded-xl bg-[#f8fafc] p-4 border border-slate-100">
            <div className="text-[10px] font-bold uppercase tracking-wider text-slate-400">
              High Priority Gaps
            </div>
            <div className="mt-2 text-2xl font-black text-rose-600">
              {(summary?.high_gaps || 0) + (summary?.critical_gaps || 0)}
            </div>
          </div>

          <div className="rounded-xl bg-[#f8fafc] p-4 border border-slate-100">
            <div className="text-[10px] font-bold uppercase tracking-wider text-slate-400">
              Moderate Gaps
            </div>
            <div className="mt-2 text-2xl font-black text-amber-600">
              {summary?.medium_gaps || 0}
            </div>
          </div>

          <div className="rounded-xl bg-[#f8fafc] p-4 border border-slate-100">
            <div className="text-[10px] font-bold uppercase tracking-wider text-slate-400">
              Low / On Track
            </div>
            <div className="mt-2 text-2xl font-black text-[#087f76]">
              {summary?.low_gaps ?? (summary?.met_count || 0)}
            </div>
          </div>
        </div>
      </div>

      {/* Gap Cards List */}
      {loading ? (
        <div className="space-y-4">
          {[1, 2, 3].map((n) => (
            <div key={n} className="h-44 rounded-2xl bg-white animate-pulse border border-slate-200" />
          ))}
        </div>
      ) : gaps.length === 0 ? (
        <div className="rounded-2xl border border-dashed border-[#dfe7f0] bg-white p-12 text-center">
          <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-teal-50 text-teal-700">
            <CheckCircle2 size={24} />
          </div>
          <h3 className="mt-4 text-base font-bold text-[#123057]">
            No skill gaps found in your profile
          </h3>
          <p className="mt-1 text-sm text-slate-500 max-w-md mx-auto">
            Take a capability assessment to measure current levels and uncover tailored learning paths.
          </p>
          <button
            onClick={() => onNavigate("Assessments")}
            className="mt-5 inline-flex items-center gap-2 rounded-xl bg-[#ef7e37] px-4 py-2.5 text-xs font-bold text-white hover:bg-[#d96a27]"
          >
            Start Assessment
          </button>
        </div>
      ) : (
        <div className="space-y-4">
          {gaps.map((gap) => {
            const current = gap.current_level || 0;
            const required = gap.required_level || 4.0;
            const pct = Math.min(100, Math.round((current / required) * 100));

            return (
              <div
                key={gap.competency_id}
                className="rounded-2xl border border-[#dfe7f0] bg-white p-6 shadow-sm hover:border-orange-300 hover:shadow-md transition-all"
              >
                <div className="flex flex-wrap items-start justify-between gap-3 border-b border-slate-100 pb-3">
                  <div>
                    <div className="text-[10px] font-extrabold uppercase tracking-wider text-teal-800">
                      {gap.competency_code} · {gap.competency_domain || gap.domain || "Domain"}
                    </div>
                    <h3 className="text-lg font-bold text-[#123057] mt-0.5">
                      {gap.competency_name}
                    </h3>
                  </div>

                  <span className="rounded-full bg-[#fff0e6] px-3 py-1 text-xs font-bold text-[#d96b27]">
                    {gap.gap_category}
                  </span>
                </div>

                {/* Grid Comparison */}
                <div className="mt-4 grid grid-cols-3 gap-4 rounded-xl bg-slate-50 p-4 text-center">
                  <div>
                    <div className="text-xs font-bold text-slate-400 uppercase">Required Level</div>
                    <div className="mt-1 text-xl font-black text-[#123057]">{required.toFixed(1)}</div>
                  </div>
                  <div>
                    <div className="text-xs font-bold text-slate-400 uppercase">Current Level</div>
                    <div className="mt-1 text-xl font-black text-[#123057]">
                      {gap.current_level != null ? gap.current_level.toFixed(1) : "Not Assessed"}
                    </div>
                  </div>
                  <div>
                    <div className="text-xs font-bold text-slate-400 uppercase">Deficit Gap</div>
                    <div className="mt-1 text-xl font-black text-[#ef7e37]">{gap.gap.toFixed(1)}</div>
                  </div>
                </div>

                {/* Signal Bar */}
                <div className="mt-4">
                  <div className="h-2.5 w-full overflow-hidden rounded-full bg-slate-100">
                    <div
                      className="h-full rounded-full bg-[#087f76] transition-all duration-500"
                      style={{ width: `${pct}%` }}
                    />
                  </div>
                </div>

                {/* Footer Action */}
                <div className="mt-4 flex flex-wrap items-center justify-between gap-3 border-t border-slate-100 pt-3 text-xs">
                  <span className="text-slate-400 font-semibold">
                    Priority {gap.priority} · {Math.round((gap.confidence ?? 0.8) * 100)}% confidence · {gap.gap_category}
                  </span>

                  <button
                    onClick={() => onNavigate("Recommendations", { competencyCode: gap.competency_code })}
                    className="inline-flex items-center gap-1.5 rounded-xl bg-[#ef7e37] px-4 py-2 text-xs font-bold text-white shadow hover:bg-[#d96a27] transition-all"
                  >
                    View Targeted Recommendations <ArrowRight size={13} />
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

export default OfficialSkillGaps;
