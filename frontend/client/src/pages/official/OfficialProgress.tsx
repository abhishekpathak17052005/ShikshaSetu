import React, { useEffect, useState } from "react";
import {
  TrendingUp,
  Award,
  Clock,
  ClipboardCheck,
  CheckCircle2,
  BookOpen,
  RefreshCw,
  ArrowRight,
  ShieldCheck,
  Sparkles,
} from "lucide-react";
import {
  api,
  SkillGapResponse,
  LearningActivityListResponse,
} from "@/lib/api";
import { PageSkeleton } from "@/components/PageSkeleton";
import { toast } from "sonner";

interface OfficialProgressProps {
  onNavigate: (page: string, context?: { competencyCode?: string }) => void;
}

export function OfficialProgress({ onNavigate }: OfficialProgressProps) {
  const [skillGaps, setSkillGaps] = useState<SkillGapResponse | null>(null);
  const [activities, setActivities] = useState<LearningActivityListResponse | null>(null);
  const [evidenceList, setEvidenceList] = useState<any[]>([]);
  const [adaptiveHistory, setAdaptiveHistory] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchProgress = async () => {
    try {
      setLoading(true);
      const [gapsRes, actsRes, evRes, adaptRes] = await Promise.allSettled([
        api.skillGaps.me(),
        api.learningActivities.list(),
        api.evidence.list(),
        api.adaptiveAssessments.history(),
      ]);

      if (gapsRes.status === "fulfilled") setSkillGaps(gapsRes.value);
      if (actsRes.status === "fulfilled") setActivities(actsRes.value);
      if (evRes.status === "fulfilled") setEvidenceList(evRes.value);
      if (adaptRes.status === "fulfilled") setAdaptiveHistory(adaptRes.value);
    } catch (err: any) {
      toast.error(err.message || "Failed to load progress metrics");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchProgress();
  }, []);

  if (loading && !skillGaps && evidenceList.length === 0 && adaptiveHistory.length === 0) {
    return <PageSkeleton />;
  }

  // Calculate total learning time
  const totalMinutes = (activities?.activities || []).reduce(
    (acc, a) => acc + (a.duration_minutes || 0),
    0
  );
  const totalHours = (totalMinutes / 60).toFixed(1);

  const completedActivitiesCount = (activities?.activities || []).filter(
    (a) => a.status === "completed"
  ).length;

  const normalizeScore = (rawScore: any, scoreType?: string): number => {
    const val = Number(rawScore);
    if (isNaN(val)) return 3.0;
    if (scoreType === "PERCENTAGE") {
      return Math.min(5.0, Math.max(1.0, Math.round((val / 100.0) * 5.0 * 10) / 10));
    }
    if (scoreType === "IRT_THETA" || scoreType === "PROFICIENCY_LEVEL") {
      return Math.min(5.0, Math.max(1.0, Math.round(val * 10) / 10));
    }
    if (val > 5.0) {
      return Math.min(5.0, Math.max(1.0, Math.round((val / 100.0) * 5.0 * 10) / 10));
    }
    return Math.min(5.0, Math.max(1.0, Math.round(val * 10) / 10));
  };

  // Combine authoritative records from adaptive history + evidence ledger
  const allAuthoritativeItems: any[] = [];
  const seenIds = new Set<string>();

  adaptiveHistory.forEach((item) => {
    const id = item.session_id || item.competency_code;
    seenIds.add(id);
    const norm = normalizeScore(item.final_score, "IRT_THETA");
    allAuthoritativeItems.push({
      id,
      type: "AUTHORITATIVE",
      score_type: "IRT_THETA",
      raw_score: item.final_score,
      competency_code: item.competency_code,
      competency_name: item.competency_name,
      title: `Adaptive Assessment: ${item.competency_name || item.competency_code}`,
      source: "Standardized IRT Adaptive Examination",
      score: norm,
      confidence: 0.85,
      date: item.completed_at,
    });
  });

  evidenceList.forEach((ev) => {
    if (!seenIds.has(ev.id) && !seenIds.has(ev.session_id)) {
      const sType = ev.score_type || (ev.source === "AI_QUIZ" ? "PERCENTAGE" : "PROFICIENCY_LEVEL");
      const raw = ev.raw_score !== undefined ? ev.raw_score : ev.score;
      const norm = ev.normalized_level !== undefined ? ev.normalized_level : normalizeScore(raw, sType);
      allAuthoritativeItems.push({
        ...ev,
        score_type: sType,
        raw_score: raw,
        score: norm,
      });
    }
  });

  const authoritativeCount = allAuthoritativeItems.filter(
    (e) => e.type === "AUTHORITATIVE" || (e.confidence && e.confidence >= 0.7)
  ).length;

  const assessedGaps = (skillGaps?.gaps || []).filter((g) => g.current_level != null);
  let averageLevel = "—";
  if (assessedGaps.length > 0) {
    const sum = assessedGaps.reduce((acc, g) => acc + (g.current_level || 0), 0);
    averageLevel = (sum / assessedGaps.length).toFixed(1);
  } else if (allAuthoritativeItems.length > 0) {
    const compScores = new Map<string, number>();
    allAuthoritativeItems.forEach((item) => {
      const code = item.competency_code || "GENERAL";
      if (!compScores.has(code)) {
        compScores.set(code, normalizeScore(item.score));
      }
    });
    const values: number[] = [];
    compScores.forEach((v) => values.push(v));
    const sum = values.reduce((acc, s) => acc + s, 0);
    averageLevel = (sum / Math.max(values.length, 1)).toFixed(1);
  }

  return (
    <div className="space-y-6 animate-fadeIn max-w-4xl mx-auto">
      {/* Header */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-black text-[#123057]">Progress & Capability Growth</h1>
          <p className="text-sm text-slate-500 mt-1">
            Real longitudinal capability progress based on verified assessments and recorded learning time.
          </p>
        </div>

        <button
          onClick={fetchProgress}
          className="flex items-center gap-1.5 rounded-xl border border-[#dfe7f0] bg-white px-3.5 py-2 text-xs font-bold text-slate-600 hover:bg-slate-50 transition-colors"
        >
          <RefreshCw size={14} className={loading ? "animate-spin" : ""} />
          Refresh Progress
        </button>
      </div>

      {/* 4-Card Summary */}
      <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
        <div className="rounded-2xl border border-[#dfe7f0] bg-white p-5 shadow-sm">
          <div className="flex items-center justify-between text-slate-400">
            <span className="text-xs font-bold uppercase">Learning Hours</span>
            <Clock size={18} className="text-purple-600" />
          </div>
          <div className="mt-3 text-3xl font-black text-[#123057]">{totalHours} hrs</div>
          <div className="mt-1 text-[11px] text-slate-400 font-semibold">{totalMinutes} minutes logged</div>
        </div>

        <div className="rounded-2xl border border-[#dfe7f0] bg-white p-5 shadow-sm">
          <div className="flex items-center justify-between text-slate-400">
            <span className="text-xs font-bold uppercase">Modules Completed</span>
            <BookOpen size={18} className="text-teal-600" />
          </div>
          <div className="mt-3 text-3xl font-black text-[#123057]">{completedActivitiesCount}</div>
          <div className="mt-1 text-[11px] text-slate-400 font-semibold">Supporting evidence logged</div>
        </div>

        <div className="rounded-2xl border border-[#dfe7f0] bg-white p-5 shadow-sm">
          <div className="flex items-center justify-between text-slate-400">
            <span className="text-xs font-bold uppercase">Assessments Taken</span>
            <ClipboardCheck size={18} className="text-emerald-600" />
          </div>
          <div className="mt-3 text-3xl font-black text-[#123057]">{authoritativeCount}</div>
          <div className="mt-1 text-[11px] text-slate-400 font-semibold">Authoritative records</div>
        </div>

        <div className="rounded-2xl border border-[#dfe7f0] bg-white p-5 shadow-sm">
          <div className="flex items-center justify-between text-slate-400">
            <span className="text-xs font-bold uppercase">Current Level</span>
            <Award size={18} className="text-[#ef7e37]" />
          </div>
          <div className="mt-3 text-3xl font-black text-[#ef7e37]">{averageLevel} / 5.0</div>
          <div className="mt-1 text-[11px] text-slate-400 font-semibold">Average capability index</div>
        </div>
      </div>

      {/* Validated Evidence Timeline */}
      <div className="rounded-3xl border border-[#dfe7f0] bg-white p-6 sm:p-8 shadow-sm space-y-6">
        <div className="border-b border-slate-100 pb-4 flex items-center justify-between">
          <div>
            <h2 className="text-lg font-bold text-[#123057]">Validated Assessment & Capability History</h2>
            <p className="text-xs text-slate-400 mt-0.5">
              Chronological audit of formal competency evaluations and validated learning milestones.
            </p>
          </div>
          <span className="inline-flex items-center gap-1 rounded-full bg-emerald-50 px-3 py-1 text-xs font-bold text-emerald-700">
            <ShieldCheck size={14} /> Immutable Ledger
          </span>
        </div>

        {allAuthoritativeItems.length === 0 ? (
          <div className="rounded-2xl border border-dashed border-[#dfe7f0] bg-slate-50/50 p-8 text-center">
            <TrendingUp size={24} className="mx-auto text-slate-400" />
            <h3 className="mt-2 text-sm font-bold text-[#123057]">No historical assessment data</h3>
            <p className="mt-1 text-xs text-slate-500 max-w-sm mx-auto">
              Your capability progress timeline will populate automatically as you complete standardized capability assessments.
            </p>
            <button
              onClick={() => onNavigate("Assessments")}
              className="mt-4 inline-flex items-center gap-1.5 rounded-xl bg-[#ef7e37] px-4 py-2 text-xs font-bold text-white shadow hover:bg-[#d96a27]"
            >
              Start First Assessment <ArrowRight size={12} />
            </button>
          </div>
        ) : (
          <div className="space-y-3">
            {allAuthoritativeItems.map((ev, idx) => {
              const isAuthoritative = ev.type === "AUTHORITATIVE" || (ev.confidence && ev.confidence >= 0.7);
              const scoreVal = normalizeScore(ev.score ?? ev.raw_score ?? 3.0, ev.score_type).toFixed(1);
              const dateStr = ev.date ? new Date(ev.date).toLocaleDateString(undefined, { year: "numeric", month: "short", day: "numeric" }) : "Recent";
              const rawLabel =
                ev.score_type === "PERCENTAGE" && ev.raw_score != null
                  ? `${Number(ev.raw_score).toFixed(0)}% quiz score`
                  : ev.raw_score != null
                  ? `Theta ${Number(ev.raw_score).toFixed(1)}`
                  : null;

              return (
                <div
                  key={ev.id || idx}
                  className="rounded-2xl border border-slate-100 bg-[#f8fafc] p-4 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 hover:border-slate-200 transition-colors"
                >
                  <div className="flex items-start gap-3">
                    <div className={`mt-0.5 flex h-9 w-9 shrink-0 items-center justify-center rounded-xl font-black text-xs ${
                      isAuthoritative ? "bg-emerald-100 text-emerald-800" : "bg-teal-100 text-teal-800"
                    }`}>
                      {isAuthoritative ? <ClipboardCheck size={18} /> : <BookOpen size={18} />}
                    </div>
                    <div>
                      <div className="flex flex-wrap items-center gap-2">
                        <span className="rounded bg-slate-200/80 px-2 py-0.5 text-[10px] font-bold text-slate-800">
                          {ev.competency_code || "COMPETENCY"}
                        </span>
                        <span className="text-xs font-bold text-[#123057]">
                          {ev.title || ev.source || "Competency Verification"}
                        </span>
                      </div>
                      <div className="text-[11px] text-slate-400 mt-1 flex items-center gap-2">
                        <span>Recorded on {dateStr}</span>
                        <span>·</span>
                        <span className="font-semibold text-slate-500">{ev.source || "System Verification"}</span>
                        {rawLabel && (
                          <>
                            <span>·</span>
                            <span className="text-slate-400 font-medium">{rawLabel}</span>
                          </>
                        )}
                      </div>
                    </div>
                  </div>

                  <div className="flex items-center gap-3 shrink-0">
                    <span className={`rounded-full px-3 py-1 text-xs font-extrabold ${
                      isAuthoritative ? "bg-emerald-100 text-emerald-800" : "bg-teal-100 text-teal-800"
                    }`}>
                      Level {scoreVal} / 5.0
                    </span>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}

export default OfficialProgress;
