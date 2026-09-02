import React, { useEffect, useState } from "react";
import {
  ArrowRight,
  BookOpen,
  CheckCircle2,
  ClipboardCheck,
  Gauge,
  GraduationCap,
  Layers,
  Sparkles,
  Target,
  TrendingUp,
  Award,
  AlertCircle,
  Briefcase,
  Building,
} from "lucide-react";
import {
  api,
  SkillGapResponse,
  Competency,
  RecommendationResponse,
  LearningActivityListResponse,
} from "@/lib/api";
import { useAuth } from "@/contexts/AuthContext";
import { useTranslation } from "@/i18n";
import { toast } from "sonner";

interface OfficialDashboardProps {
  onNavigate: (page: string, context?: { competencyCode?: string }) => void;
}

export function OfficialDashboard({ onNavigate }: OfficialDashboardProps) {
  const { user } = useAuth();
  const { t, isHindi } = useTranslation();
  const [skillGaps, setSkillGaps] = useState<SkillGapResponse | null>(null);
  const [competencies, setCompetencies] = useState<Competency[]>([]);
  const [recommendations, setRecommendations] = useState<RecommendationResponse | null>(null);
  const [activities, setActivities] = useState<LearningActivityListResponse | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let active = true;
    setLoading(true);

    api.skillGaps.me()
      .then((res) => { if (active) setSkillGaps(res); })
      .catch(() => {});

    api.competencies.me()
      .then((res) => { if (active) setCompetencies(res as any); })
      .catch(() => {});

    api.learningActivities.list()
      .then((res) => { if (active) setActivities(res); })
      .catch(() => {});

    api.recommendations.me()
      .then((res) => { if (active) setRecommendations(res); })
      .catch(() => {})
      .finally(() => { if (active) setLoading(false); });

    return () => { active = false; };
  }, []);

  const assessedGaps = skillGaps?.gaps?.filter((g) => g.current_level != null) || [];
  const priorityGaps =
    skillGaps?.gaps?.filter(
      (g) => g.gap_category === "CRITICAL" || g.gap_category === "HIGH" || g.gap > 0
    ) || [];

  const averageLevel =
    assessedGaps.length > 0
      ? assessedGaps.reduce((acc, g) => acc + (g.current_level || 0), 0) / assessedGaps.length
      : null;

  const averageConfidence =
    assessedGaps.length > 0
      ? assessedGaps.reduce((acc, g) => acc + (g.confidence || 0), 0) / assessedGaps.length
      : null;

  const topGap = priorityGaps[0] || skillGaps?.gaps?.[0];
  const topRec = recommendations?.recommendations?.[0];

  const completedActivities = activities?.activities?.filter((a) => a.status === "completed") || [];
  const inProgressActivities = activities?.activities?.filter((a) => a.status === "in_progress") || [];

  if (loading && !skillGaps && !competencies.length) {
    return (
      <div className="space-y-8 animate-fadeIn">
        <div className="relative overflow-hidden rounded-3xl bg-gradient-to-br from-[#123057] via-[#1a3d6d] to-[#087f76] p-8 text-white shadow-lg">
          <div className="h-6 w-48 rounded bg-white/20 animate-pulse" />
          <div className="mt-3 h-10 w-72 rounded bg-white/30 animate-pulse" />
        </div>
        <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
          <div className="h-28 rounded-3xl bg-slate-200/60 animate-pulse" />
          <div className="h-28 rounded-3xl bg-slate-200/60 animate-pulse" />
          <div className="h-28 rounded-3xl bg-slate-200/60 animate-pulse" />
          <div className="h-28 rounded-3xl bg-slate-200/60 animate-pulse" />
        </div>
        <div className="grid gap-6 lg:grid-cols-2">
          <div className="h-64 rounded-3xl bg-slate-200/50 animate-pulse" />
          <div className="h-64 rounded-3xl bg-slate-200/50 animate-pulse" />
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-8 animate-fadeIn">

      {/* ── Welcome & Capability Header ── */}
      <div className="relative overflow-hidden rounded-3xl bg-gradient-to-br from-[#123057] via-[#1a3d6d] to-[#087f76] p-8 text-white shadow-lg">
        <div className="relative z-10 flex flex-col justify-between gap-6 md:flex-row md:items-center">
          <div>
            <div className="inline-flex items-center gap-2 rounded-full bg-white/10 px-3 py-1 text-xs font-bold uppercase tracking-wider backdrop-blur-md">
              <Sparkles size={14} className="text-[#38d9c0]" />
              Official Statistical System Capability Platform
            </div>
            <h1 className="mt-3 text-3xl font-extrabold tracking-tight sm:text-4xl">
              Good morning, {user?.full_name?.split(" ")[0] || "Officer"}
            </h1>
            <div className="mt-2 flex flex-wrap items-center gap-4 text-xs text-slate-200">
              <span className="flex items-center gap-1">
                <Briefcase size={14} className="text-[#38d9c0]" />
                {user?.designation || "Statistical Officer"}
              </span>
              <span>·</span>
              <span className="flex items-center gap-1">
                <Building size={14} className="text-[#38d9c0]" />
                {user?.department || "Ministry of Statistics & PI"}
              </span>
            </div>
          </div>

          <div className="flex flex-wrap gap-3">
            <button
              onClick={() => onNavigate("Assessments")}
              className="inline-flex items-center gap-2 rounded-xl bg-[#ef7e37] px-5 py-3 text-sm font-bold text-white shadow-md hover:bg-[#d96a27] transition-all transform active:scale-95"
            >
              <ClipboardCheck size={16} />
              Take Assessment
            </button>
            <button
              onClick={() => onNavigate("Recommendations")}
              className="inline-flex items-center gap-2 rounded-xl bg-white/10 backdrop-blur-md border border-white/20 px-5 py-3 text-sm font-bold text-white hover:bg-white/20 transition-all"
            >
              <BookOpen size={16} />
              View Recommendations
            </button>
          </div>
        </div>
      </div>

      {/* ── KPI Stat Cards ── */}
      <div className="grid grid-cols-2 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {/* Overall Capability */}
        <div className="rounded-2xl border border-[#dfe7f0] bg-white p-5 shadow-sm hover:shadow-md transition-shadow">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold uppercase tracking-wider text-slate-400">
              Overall Capability
            </span>
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-teal-50 text-teal-700">
              <Gauge size={18} />
            </div>
          </div>
          <div className="mt-4 flex items-baseline gap-2">
            <span className="text-3xl font-black text-[#123057]">
              {averageLevel != null ? `${averageLevel.toFixed(1)} / 5.0` : "—"}
            </span>
          </div>
          <div className="mt-2 text-[11px] text-slate-400 font-semibold">
            {averageConfidence != null
              ? `${Math.round(averageConfidence * 100)}% evidence confidence`
              : "Awaiting initial assessment"}
          </div>
        </div>

        {/* Competencies Mapped */}
        <div className="rounded-2xl border border-[#dfe7f0] bg-white p-5 shadow-sm hover:shadow-md transition-shadow">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold uppercase tracking-wider text-slate-400">
              Competencies Mapped
            </span>
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-blue-50 text-blue-700">
              <Layers size={18} />
            </div>
          </div>
          <div className="mt-4 flex items-baseline gap-2">
            <span className="text-3xl font-black text-[#123057]">
              {skillGaps?.summary?.required_competencies ?? competencies.length ?? 0}
            </span>
            <span className="text-xs font-semibold text-slate-400">framework items</span>
          </div>
          <button
            onClick={() => onNavigate("My Competencies")}
            className="mt-3 flex items-center gap-1 text-xs font-bold text-teal-700 hover:underline"
          >
            View framework <ArrowRight size={12} />
          </button>
        </div>

        {/* Priority Skill Gaps */}
        <div className="rounded-2xl border border-[#dfe7f0] bg-white p-5 shadow-sm hover:shadow-md transition-shadow">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold uppercase tracking-wider text-slate-400">
              Priority Skill Gaps
            </span>
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-orange-50 text-orange-600">
              <Target size={18} />
            </div>
          </div>
          <div className="mt-4 flex items-baseline gap-2">
            <span className="text-3xl font-black text-[#ef7e37]">
              {priorityGaps.length}
            </span>
            <span className="text-xs font-semibold text-slate-400">areas for growth</span>
          </div>
          <button
            onClick={() => onNavigate("Skill Gaps")}
            className="mt-3 flex items-center gap-1 text-xs font-bold text-[#ef7e37] hover:underline"
          >
            View gap analysis <ArrowRight size={12} />
          </button>
        </div>

        {/* Learning Activities */}
        <div className="rounded-2xl border border-[#dfe7f0] bg-white p-5 shadow-sm hover:shadow-md transition-shadow">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold uppercase tracking-wider text-slate-400">
              Learning Progress
            </span>
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-purple-50 text-purple-700">
              <GraduationCap size={18} />
            </div>
          </div>
          <div className="mt-4 flex items-baseline gap-2">
            <span className="text-3xl font-black text-[#123057]">
              {completedActivities.length}
            </span>
            <span className="text-xs font-semibold text-slate-400">
              completed ({inProgressActivities.length} active)
            </span>
          </div>
          <button
            onClick={() => onNavigate("My Learning")}
            className="mt-3 flex items-center gap-1 text-xs font-bold text-purple-700 hover:underline"
          >
            My learning tracker <ArrowRight size={12} />
          </button>
        </div>
      </div>

      {/* ── Middle Row: Priority Gaps & Next Best Action ── */}
      <div className="grid gap-6 lg:grid-cols-3">
        {/* Priority Skill Gaps (2 cols) */}
        <div className="rounded-2xl border border-[#dfe7f0] bg-white p-6 shadow-sm lg:col-span-2">
          <div className="flex items-center justify-between border-b border-slate-100 pb-4">
            <div>
              <h2 className="text-lg font-bold text-[#123057]">Priority Skill Gaps</h2>
              <p className="text-xs text-slate-400 mt-0.5">
                Targeted capability deficits ranked by official role requirement priority.
              </p>
            </div>
            <button
              onClick={() => onNavigate("Skill Gaps")}
              className="rounded-lg bg-teal-50 px-3 py-1.5 text-xs font-bold text-teal-800 hover:bg-teal-100 transition-colors"
            >
              Full Analysis
            </button>
          </div>

          <div className="mt-5 space-y-4">
            {loading ? (
              <div className="h-40 rounded-xl bg-slate-50 animate-pulse" />
            ) : priorityGaps.length === 0 ? (
              <div className="rounded-xl border border-dashed border-emerald-200 bg-emerald-50/40 p-8 text-center">
                <CheckCircle2 size={24} className="mx-auto text-emerald-600" />
                <h3 className="mt-2 text-sm font-bold text-emerald-900">
                  No active skill gaps identified
                </h3>
                <p className="mt-1 text-xs text-emerald-700">
                  You are currently meeting all configured proficiency benchmarks for your role.
                </p>
              </div>
            ) : (
              priorityGaps.slice(0, 3).map((gap) => {
                const current = gap.current_level || 0;
                const required = gap.required_level || 4.0;
                const pct = Math.min(100, Math.round((current / required) * 100));

                return (
                  <div
                    key={gap.competency_id}
                    className="rounded-xl border border-slate-100 bg-[#f8fafc] p-4 transition-all hover:border-teal-200"
                  >
                    <div className="flex items-center justify-between">
                      <div>
                        <div className="text-[10px] font-extrabold uppercase tracking-wider text-teal-700">
                          {gap.competency_code} · {gap.competency_domain || gap.domain || "Domain"}
                        </div>
                        <h4 className="text-sm font-bold text-[#123057] mt-0.5">
                          {gap.competency_name}
                        </h4>
                      </div>
                      <span className="rounded-full bg-orange-100 px-2.5 py-0.5 text-[10px] font-bold text-orange-800">
                        Gap: {gap.gap.toFixed(1)}
                      </span>
                    </div>

                    {/* Level Bar */}
                    <div className="mt-3">
                      <div className="flex justify-between text-[11px] font-semibold text-slate-500 mb-1">
                        <span>Current: <strong>{current.toFixed(1)}</strong></span>
                        <span>Required: <strong>{required.toFixed(1)}</strong></span>
                      </div>
                      <div className="h-2 w-full overflow-hidden rounded-full bg-slate-200">
                        <div
                          className="h-full rounded-full bg-[#087f76] transition-all duration-500"
                          style={{ width: `${pct}%` }}
                        />
                      </div>
                    </div>

                    <div className="mt-3 flex items-center justify-between border-t border-slate-200/50 pt-2.5 text-xs">
                      <span className="text-[11px] text-slate-400">
                        Priority {gap.priority} · {Math.round((gap.confidence ?? 0.8) * 100)}% confidence
                      </span>
                      <button
                        onClick={() =>
                          onNavigate("Recommendations", { competencyCode: gap.competency_code })
                        }
                        className="font-bold text-[#ef7e37] hover:underline inline-flex items-center gap-1"
                      >
                        View Learning <ArrowRight size={11} />
                      </button>
                    </div>
                  </div>
                );
              })
            )}
          </div>
        </div>

        {/* Next Best Action Card (1 col) */}
        <div className="flex flex-col justify-between rounded-2xl bg-[#123057] p-6 text-white shadow-sm relative overflow-hidden">
          <div className="relative z-10">
            <div className="inline-flex items-center gap-1.5 rounded-full bg-white/10 px-2.5 py-0.5 text-[10px] font-bold uppercase tracking-wider text-[#38d9c0]">
              <TrendingUp size={12} /> Next Best Action
            </div>

            <h3 className="mt-3 text-lg font-bold">
              {topGap ? `Close your ${topGap.competency_name} gap` : "Verify Core Competencies"}
            </h3>

            <p className="mt-2 text-xs text-slate-200 leading-relaxed">
              {topRec
                ? `Recommended curriculum: "${topRec.resource_title || topRec.title || topRec.resource || 'Course'}" from ${topRec.provider || "iGOT"}. Matched to your role responsibilities.`
                : "Engage in recommended learning resources from iGOT/NSSTA and complete capability assessments."}
            </p>

            {topGap && (
              <div className="mt-5 rounded-xl bg-white/10 p-3.5 backdrop-blur-sm border border-white/10">
                <div className="flex justify-between text-xs font-semibold">
                  <span className="text-slate-300">Target Proficiency:</span>
                  <span className="text-[#38d9c0] font-bold">Level {topGap.required_level.toFixed(1)} / 5.0</span>
                </div>
                <div className="mt-1 text-[11px] text-slate-300">
                  Priority deficit: {topGap.gap.toFixed(1)} points
                </div>
              </div>
            )}
          </div>

          <div className="relative z-10 mt-6 pt-4 border-t border-white/10 flex flex-col gap-2">
            <button
              onClick={() => onNavigate("Recommendations")}
              className="w-full inline-flex items-center justify-center gap-2 rounded-xl bg-[#ef7e37] py-2.5 text-xs font-bold text-white shadow hover:bg-[#d96a27] transition-colors"
            >
              Start Recommended Learning <ArrowRight size={13} />
            </button>
            <button
              onClick={() => onNavigate("Assessments")}
              className="w-full inline-flex items-center justify-center gap-1 rounded-xl bg-white/10 py-2 text-xs font-bold text-white hover:bg-white/20 transition-colors"
            >
              Take Capability Assessment
            </button>
          </div>
        </div>
      </div>

      {/* ── Bottom Notice: Learning ≠ Proven Competency ── */}
      <div className="rounded-2xl border border-teal-100 bg-teal-50/40 p-5 flex items-start gap-4">
        <div className="mt-0.5 text-teal-800">
          <Award size={20} />
        </div>
        <div className="text-xs text-slate-600 leading-relaxed">
          <strong className="text-[#123057] font-semibold">
            Civic Capability Integrity Principle:
          </strong>{" "}
          Completing learning resources and practice quizzes logs <span className="font-bold text-teal-800">Supporting Evidence (0.30 confidence)</span>. To formally validate mastery and update your official competency profile, complete a standardized <span className="font-bold text-[#123057]">Capability Assessment</span>.
        </div>
      </div>
    </div>
  );
}

export default OfficialDashboard;
