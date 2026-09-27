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
  TalentProfile,
} from "@/lib/api";
import { useAuth } from "@/contexts/AuthContext";
import { useTranslation } from "@/i18n";
import { toast } from "sonner";
import { NumberReveal, ProgressBarFill, AnimatedSection } from "@/components/motion/MotionUtils";

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
  const [talentProfile, setTalentProfile] = useState<TalentProfile | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let active = true;
    setLoading(true);

    // 1. Primary data needed to render Dashboard KPIs and skill gaps immediately:
    api.skillGaps.me()
      .then((res) => {
        if (active) {
          setSkillGaps(res);
          setLoading(false);
        }
      })
      .catch(() => {
        if (active) setLoading(false);
      });

    // 2. Secondary framework items
    api.competencies.me()
      .then((res) => {
        if (active) {
          setCompetencies(res as any);
          setLoading(false);
        }
      })
      .catch(() => { });

    // 3. Asynchronous non-blocking background loads:
    api.learningActivities.list()
      .then((res) => { if (active) setActivities(res); })
      .catch(() => { });

    api.recommendations.me()
      .then((res) => { if (active) setRecommendations(res); })
      .catch(() => { });

    api.talent.getProfile()
      .then((res) => { if (active) setTalentProfile(res); })
      .catch(() => { });

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

  return (
    <div className="space-y-8 anim-page-enter">

      {/* ── Welcome & Capability Header ── */}
      <div className="relative overflow-hidden rounded-3xl bg-gradient-to-br from-[#123057] via-[#1a3d6d] to-[#087f76] p-7 sm:p-8 text-white shadow-lg anim-fade-up">
        <div className="relative z-10 flex flex-col justify-between gap-6 md:flex-row md:items-center">
          <div>
            <div className="inline-flex items-center gap-2 rounded-full bg-white/10 px-2.5 py-1 text-[11px] font-bold uppercase tracking-wider backdrop-blur-md anim-badge-pop text-[#38d9c0]">
              <Sparkles size={12} className="text-[#38d9c0]" />
              Official Capability Intelligence Platform
            </div>
            <h1 className="mt-2.5 text-2xl font-extrabold tracking-tight sm:text-[32px] leading-tight">
              Good morning, {user?.full_name || "Officer"}
            </h1>
            <div className="mt-1.5 flex flex-wrap items-center gap-3 text-[11px] text-slate-200">
              <span className="flex items-center gap-1">
                <Briefcase size={13} className="text-[#38d9c0]" />
                {user?.designation || "Statistical Officer"}
              </span>
              <span>·</span>
              <span className="flex items-center gap-1">
                <Building size={13} className="text-[#38d9c0]" />
                {user?.department || "Ministry of Statistics & PI"}
              </span>
            </div>
          </div>

          <div className="flex flex-wrap gap-2.5 md:ml-auto md:flex-nowrap md:justify-end">
            <button
              onClick={() => onNavigate("Assessments")}
              className="inline-flex shrink-0 items-center gap-1.5 whitespace-nowrap rounded-xl bg-[#ef7e37] px-4.5 py-2.5 text-[13px] font-bold text-white shadow-md hover:bg-[#d96a27] btn-interactive"
            >
              <ClipboardCheck size={15} />
              Take Assessment
            </button>
            <button
              onClick={() => onNavigate("Recommendations")}
              className="inline-flex shrink-0 items-center gap-1.5 whitespace-nowrap rounded-xl border border-white/20 bg-white/10 px-4.5 py-2.5 text-[13px] font-bold text-white backdrop-blur-md hover:bg-white/20 btn-interactive"
            >
              <BookOpen size={15} />
              View Recommendations
            </button>
          </div>
        </div>
      </div>

      {/* ── KPI Stat Cards ── */}
      <div className="grid grid-cols-2 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {/* Overall Capability */}
        <div className="rounded-2xl border border-[#dfe7f0] bg-white p-5 shadow-sm hover:shadow-md card-interactive anim-card-enter stagger-1 group">
          <div className="flex items-center justify-between">
            <span className="text-[11px] font-semibold uppercase tracking-wider text-slate-400">
              Overall Capability
            </span>
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-teal-50 text-teal-700 icon-interactive">
              <Gauge size={18} />
            </div>
          </div>
          <div className="mt-4 flex items-baseline gap-2">
            {loading ? (
              <div className="h-8 w-24 rounded bg-slate-200 animate-pulse" />
            ) : averageLevel != null ? (
              <span className="text-2xl sm:text-3xl font-bold tracking-tight text-[#123057]">
                <NumberReveal value={averageLevel} decimals={1} suffix=" / 5.0" />
              </span>
            ) : (
              <span className="text-lg font-bold text-amber-600 anim-fade-in">
                Not assessed
              </span>
            )}
          </div>
          <div className="mt-2 text-[11px] text-slate-400 font-medium">
            {loading ? (
              <div className="h-3.5 w-32 rounded bg-slate-100 animate-pulse" />
            ) : averageConfidence != null ? (
              `${Math.round(averageConfidence * 100)}% evidence confidence`
            ) : (
              "Complete capability assessment"
            )}
          </div>
        </div>

        {/* Competencies Mapped */}
        <div className="rounded-2xl border border-[#dfe7f0] bg-white p-5 shadow-sm hover:shadow-md card-interactive anim-card-enter stagger-2 group">
          <div className="flex items-center justify-between">
            <span className="text-[11px] font-semibold uppercase tracking-wider text-slate-400">
              Competencies Mapped
            </span>
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-blue-50 text-blue-700 icon-interactive">
              <Layers size={18} />
            </div>
          </div>
          <div className="mt-4 flex items-baseline gap-2">
            {loading ? (
              <div className="h-8 w-16 rounded bg-slate-200 animate-pulse" />
            ) : (
              <>
                <span className="text-2xl sm:text-3xl font-bold tracking-tight text-[#123057]">
                  <NumberReveal value={skillGaps?.summary?.required_competencies ?? competencies.length ?? 0} />
                </span>
                <span className="text-xs font-medium text-slate-400">framework items</span>
              </>
            )}
          </div>
          <button
            onClick={() => onNavigate("My Competencies")}
            className="mt-3 flex items-center gap-1 text-xs font-semibold text-teal-700 hover:underline btn-interactive"
          >
            View framework <ArrowRight size={12} />
          </button>
        </div>

        {/* Priority Skill Gaps */}
        <div className="rounded-2xl border border-[#dfe7f0] bg-white p-5 shadow-sm hover:shadow-md card-interactive anim-card-enter stagger-3 group">
          <div className="flex items-center justify-between">
            <span className="text-[11px] font-semibold uppercase tracking-wider text-slate-400">
              Skill Gaps
            </span>
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-orange-50 text-orange-600 icon-interactive">
              <Target size={18} />
            </div>
          </div>
          <div className="mt-4 flex items-baseline gap-2">
            {loading ? (
              <div className="h-8 w-20 rounded bg-slate-200 animate-pulse" />
            ) : averageLevel == null ? (
              <span className="text-xl font-black text-amber-600 anim-fade-in">
                Assessment required
              </span>
            ) : (
              <>
                <span className="text-3xl font-black text-[#ef7e37]">
                  <NumberReveal value={priorityGaps.length} />
                </span>
                <span className="text-xs font-semibold text-slate-400">priority gaps</span>
              </>
            )}
          </div>
          <button
            onClick={() => onNavigate(averageLevel == null ? "Assessments" : "Skill Gaps")}
            className="mt-3 flex items-center gap-1 text-xs font-bold text-[#ef7e37] hover:underline btn-interactive"
          >
            {averageLevel == null ? "Take assessment" : "View gap analysis"} <ArrowRight size={12} />
          </button>
        </div>

        {/* Learning Activities */}
        <div className="rounded-2xl border border-[#dfe7f0] bg-white p-5 shadow-sm hover:shadow-md card-interactive anim-card-enter stagger-4 group">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold uppercase tracking-wider text-slate-400">
              Learning Progress
            </span>
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-purple-50 text-purple-700 icon-interactive">
              <GraduationCap size={18} />
            </div>
          </div>
          <div className="mt-4 flex items-baseline gap-2">
            {loading ? (
              <div className="h-8 w-16 rounded bg-slate-200 animate-pulse" />
            ) : (
              <>
                <span className="text-3xl font-black text-[#123057]">
                  <NumberReveal value={completedActivities.length} />
                </span>
                <span className="text-xs font-semibold text-slate-400">
                  completed ({inProgressActivities.length} active)
                </span>
              </>
            )}
          </div>
          <button
            onClick={() => onNavigate("My Learning")}
            className="mt-3 flex items-center gap-1 text-xs font-bold text-purple-700 hover:underline btn-interactive"
          >
            My learning tracker <ArrowRight size={12} />
          </button>
        </div>
      </div>

      {/* ── Middle Row: Priority Gaps & Next Best Action ── */}
      <AnimatedSection className="grid gap-6 lg:grid-cols-3 items-stretch">
        {/* Priority Skill Gaps (2 cols) */}
        <div className="rounded-2xl border border-[#dfe7f0] bg-white p-6 shadow-sm lg:col-span-2 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between pb-4 border-b border-slate-100">
              <div>
                <h2 className="text-lg font-bold text-[#123057]">Priority Skill Gaps</h2>
                <p className="text-xs text-slate-400 mt-0.5">
                  Targeted capability deficits ranked by official role requirement priority.
                </p>
              </div>
              <button
                onClick={() => onNavigate("Skill Gaps")}
                className="inline-flex items-center justify-center rounded-full bg-[#eef9f8] border border-[#c6ece8] px-3.5 py-1 text-xs font-semibold text-[#087f76] hover:bg-[#e0f5f3] transition-colors shrink-0"
              >
                Full Analysis
              </button>
            </div>

            <div className="mt-5 space-y-3.5">
              {loading ? (
                <div className="h-40 rounded-xl bg-slate-50 animate-pulse" />
              ) : priorityGaps.length === 0 ? (
                <div className="rounded-xl border border-dashed border-emerald-200 bg-emerald-50/40 p-8 text-center anim-fade-in">
                  <CheckCircle2 size={24} className="mx-auto text-emerald-600 anim-badge-pop" />
                  <h3 className="mt-2 text-sm font-bold text-emerald-900">
                    No active skill gaps identified
                  </h3>
                  <p className="mt-1 text-xs text-emerald-700">
                    You are currently meeting all configured proficiency benchmarks for your role.
                  </p>
                </div>
              ) : (
                priorityGaps.slice(0, 3).map((gap, idx) => {
                  const current = gap.current_level || 0;
                  const required = gap.required_level || 4.0;
                  const pct = Math.min(100, Math.round((current / required) * 100));
                  const domainName = (gap.competency_domain || gap.domain || "STATISTICAL").toUpperCase();
                  const codeName = (gap.competency_code || "COMP").toUpperCase();

                  return (
                    <div
                      key={gap.competency_id || idx}
                      className={`rounded-2xl border ${
                        idx === 1 ? "border-[#2dd4bf]/40" : "border-[#e2e8f0]/70"
                      } bg-[#f8fafc] p-4 sm:p-5 transition-all hover:border-[#087f76]/40`}
                    >
                      <div className="flex items-center justify-between gap-2">
                        <span className="text-[10px] font-bold uppercase tracking-wider text-[#087f76]">
                          {codeName} · {domainName}
                        </span>
                        <span className="inline-flex items-center rounded-full bg-[#fff1e7] px-2.5 py-0.5 text-[11px] font-bold text-[#c2551a]">
                          Gap: {gap.gap != null ? <NumberReveal value={gap.gap} decimals={1} /> : "—"}
                        </span>
                      </div>

                      <h4 className="mt-1 text-base font-bold text-[#123057]">
                        {gap.competency_name}
                      </h4>

                      {/* Level Bar */}
                      <div className="mt-2.5">
                        <div className="flex justify-between text-xs text-slate-500 mb-1.5 font-normal">
                          <span>Current: <strong className="text-[#123057] font-bold"><NumberReveal value={current} decimals={1} /></strong></span>
                          <span>Required: <strong className="text-[#123057] font-bold"><NumberReveal value={required} decimals={1} /></strong></span>
                        </div>
                        <ProgressBarFill
                          percent={pct}
                          className="h-2 w-full rounded-full bg-[#e2e8f0] overflow-hidden"
                          fillClassName="h-full rounded-full bg-[#0a6c67]"
                          durationMs={800}
                        />
                      </div>

                      <div className="mt-3.5 flex items-center justify-between text-xs pt-1">
                        <span className="text-slate-400 font-normal">
                          Priority {gap.priority || idx + 1} · <NumberReveal value={Math.round((gap.confidence ?? 0.85) * 100)} suffix="%" /> confidence
                        </span>
                        <button
                          onClick={() =>
                            onNavigate("Recommendations", { competencyCode: gap.competency_code })
                          }
                          className="font-semibold text-[#ef7e37] hover:text-[#d96a27] inline-flex items-center gap-1 transition-colors"
                        >
                          View Learning <ArrowRight size={12} />
                        </button>
                      </div>
                    </div>
                  );
                })
              )}
            </div>
          </div>
        </div>

        {/* Next Best Action Card (1 col, aligned height) */}
        <div className="flex flex-col justify-between rounded-2xl bg-[#123057] p-6 text-white shadow-sm relative overflow-hidden">
          <div className="relative z-10">
            <div className="inline-flex items-center gap-1.5 rounded-full bg-white/10 px-2.5 py-0.5 text-[10px] font-bold uppercase tracking-wider text-[#38d9c0] anim-badge-pop">
              <TrendingUp size={12} /> Next Best Action
            </div>

            <h3 className="mt-3 text-lg font-bold">
              {topGap ? `Close your ${topGap.competency_name} gap` : "Verify Core Competencies"}
            </h3>

            <p className="mt-2 text-xs text-slate-200 leading-relaxed">
              {topRec
                ? `Recommended curriculum: "${
                    topRec.resource_title ||
                    topRec.title ||
                    (typeof topRec.resource === "object" && topRec.resource
                      ? (topRec.resource as any).title || (topRec.resource as any).name || (topRec.resource as any).course_title
                      : topRec.resource) ||
                    "Targeted Capability Curriculum"
                  }" from ${topRec.provider || "NSSTA"}. Matched to your role responsibilities.`
                : "Engage in recommended learning resources from iGOT/NSSTA and complete capability assessments."}
            </p>

            {topGap && (
              <div className="mt-5 rounded-xl bg-white/10 p-3.5 backdrop-blur-sm border border-white/10 anim-fade-up">
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

          <div className="relative z-10 mt-6 pt-4 border-t border-white/10">
            <button
              onClick={() => onNavigate("Recommendations")}
              className="w-full inline-flex items-center justify-center gap-2 rounded-xl bg-[#ef7e37] hover:bg-[#d96a27] py-3 text-sm font-semibold text-white shadow-sm transition-all active:scale-[0.98] btn-interactive"
            >
              View Learning <ArrowRight size={14} />
            </button>
          </div>
        </div>
      </AnimatedSection>

      {/* ── Bottom Notice: Learning ≠ Proven Competency ── */}
      <AnimatedSection className="rounded-2xl border border-teal-100 bg-teal-50/40 p-5 flex items-start gap-4">
        <div className="mt-0.5 text-teal-800">
          <Award size={20} />
        </div>
        <div className="text-xs text-slate-600 leading-relaxed">
          <strong className="text-[#123057] font-semibold">
            Civic Capability Integrity Principle:
          </strong>{" "}
          Completing learning resources and practice quizzes logs <span className="font-bold text-teal-800">Supporting Evidence (0.30 confidence)</span>. To formally validate mastery and update your official competency profile, complete a standardized <span className="font-bold text-[#123057]">Capability Assessment</span>.
        </div>
      </AnimatedSection>
    </div>
  );
}

export default OfficialDashboard;