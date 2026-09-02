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
  ClipboardCheck,
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
  const [error, setError] = useState<string | null>(null);

  const fetchSkillGaps = async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await api.skillGaps.me();
      setSkillGaps(res);
    } catch (err: any) {
      const msg = err.message || "Unable to load skill-gap analysis. Please try again.";
      setError(msg);
      if (err.status !== 404) {
        toast.error(msg);
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

  if (error && !skillGaps) {
    return (
      <div className="space-y-6 animate-fadeIn">
        <div className="rounded-3xl border border-red-200 bg-red-50/50 p-8 text-center">
          <AlertCircle className="h-10 w-10 text-red-500 mx-auto mb-3" />
          <h2 className="text-lg font-bold text-red-950">Unable to load skill-gap analysis</h2>
          <p className="text-sm text-red-700 mt-1 max-w-md mx-auto">
            {error}
          </p>
          <button
            onClick={fetchSkillGaps}
            className="mt-4 inline-flex items-center gap-2 rounded-xl bg-red-600 px-4 py-2 text-sm font-semibold text-white shadow hover:bg-red-700 transition"
          >
            <RefreshCw className="h-4 w-4" /> Try Again
          </button>
        </div>
      </div>
    );
  }

  const summary = skillGaps?.summary;
  const gaps = skillGaps?.gaps || [];

  const assessedCount = gaps.filter((g) => g.current_level != null).length;
  const isUnassessed = assessedCount === 0;

  const overallStatus = isUnassessed
    ? "Assessment Required"
    : summary?.critical_gaps
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
            onClick={() => onNavigate(isUnassessed ? "Assessments" : "Recommendations")}
            className="flex items-center gap-2 rounded-xl bg-[#ef7e37] px-4 py-2 text-xs font-bold text-white shadow hover:bg-[#d96a27] transition-all"
          >
            {isUnassessed ? (
              <>
                <ClipboardCheck size={14} /> Start Assessment
              </>
            ) : (
              <>
                <BookOpen size={14} /> View Recommendations
              </>
            )}
          </button>
        </div>
      </div>

      {/* Unassessed Prompt Banner */}
      {isUnassessed && (
        <div className="rounded-2xl border border-amber-200 bg-amber-50/70 p-5 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="flex items-center gap-3.5">
            <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-amber-100 text-amber-800 font-bold">
              <ClipboardCheck size={20} />
            </div>
            <div>
              <h3 className="text-sm font-bold text-amber-900">Capability Assessment Required</h3>
              <p className="text-xs text-amber-700 mt-0.5">
                Complete your role capability assessment to establish verified proficiency benchmarks and identify active skill gaps.
              </p>
            </div>
          </div>
          <button
            onClick={() => onNavigate("Assessments")}
            className="shrink-0 rounded-xl bg-amber-600 px-4 py-2 text-xs font-bold text-white shadow hover:bg-amber-700 transition-colors"
          >
            Take Assessment
          </button>
        </div>
      )}

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

          <span className={`rounded-full px-3.5 py-1.5 text-xs font-bold ${
            isUnassessed
              ? "bg-amber-100 text-amber-800 border border-amber-200"
              : "bg-[#fff0e6] text-[#d96b27]"
          }`}>
            {overallStatus}
          </span>
        </div>

        {/* 4-Stat Metric Row */}
        <div className="mt-5 grid grid-cols-2 gap-3 sm:grid-cols-4">
          <div className="rounded-xl bg-[#f8fafc] p-4 border border-slate-100">
            <div className="text-[10px] font-bold uppercase tracking-wider text-slate-400">
              Skill Gaps
            </div>
            <div className={`mt-2 font-black ${isUnassessed ? "text-lg text-amber-600" : "text-2xl text-[#ef7e37]"}`}>
              {isUnassessed ? "Assessment Required" : (summary?.total_gaps ?? gaps.length)}
            </div>
          </div>

          <div className="rounded-xl bg-[#f8fafc] p-4 border border-slate-100">
            <div className="text-[10px] font-bold uppercase tracking-wider text-slate-400">
              Priority Gaps
            </div>
            <div className="mt-2 text-2xl font-black text-rose-600">
              {isUnassessed ? "—" : (summary?.high_gaps || 0) + (summary?.critical_gaps || 0)}
            </div>
          </div>

          <div className="rounded-xl bg-[#f8fafc] p-4 border border-slate-100">
            <div className="text-[10px] font-bold uppercase tracking-wider text-slate-400">
              Assessed Competencies
            </div>
            <div className="mt-2 text-2xl font-black text-teal-700">
              {assessedCount} / {gaps.length}
            </div>
          </div>

          <div className="rounded-xl bg-[#f8fafc] p-4 border border-slate-100">
            <div className="text-[10px] font-bold uppercase tracking-wider text-slate-400">
              Role Baseline
            </div>
            <div className="mt-2 text-2xl font-black text-[#123057]">
              {gaps.length} Active
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
