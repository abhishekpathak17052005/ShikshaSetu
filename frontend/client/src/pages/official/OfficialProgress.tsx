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
  Layers,
} from "lucide-react";
import {
  api,
  SkillGapResponse,
  LearningActivityListResponse,
} from "@/lib/api";
import { toast } from "sonner";

interface OfficialProgressProps {
  onNavigate: (page: string) => void;
}

export function OfficialProgress({ onNavigate }: OfficialProgressProps) {
  const [skillGaps, setSkillGaps] = useState<SkillGapResponse | null>(null);
  const [activities, setActivities] = useState<LearningActivityListResponse | null>(null);
  const [assessments, setAssessments] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchProgress = async () => {
    try {
      setLoading(true);
      const [gapsRes, actsRes, assessRes] = await Promise.allSettled([
        api.skillGaps.me(),
        api.learningActivities.list(),
        api.capabilityAssessments.list(undefined, "SUBMITTED"),
      ]);

      if (gapsRes.status === "fulfilled") setSkillGaps(gapsRes.value);
      if (actsRes.status === "fulfilled") setActivities(actsRes.value);
      if (assessRes.status === "fulfilled") setAssessments(assessRes.value);
    } catch (err: any) {
      toast.error(err.message || "Failed to load progress metrics");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchProgress();
  }, []);

  const totalMinutes = (activities?.activities || []).reduce(
    (acc, a) => acc + (a.duration_minutes || 0),
    0
  );
  const totalHours = (totalMinutes / 60).toFixed(1);

  const completedActivitiesCount = (activities?.activities || []).filter(
    (a) => a.status === "completed"
  ).length;

  const assessedGaps = (skillGaps?.gaps || []).filter((g) => g.current_level != null);
  const averageLevel =
    assessedGaps.length > 0
      ? (
          assessedGaps.reduce((acc, g) => acc + (g.current_level || 0), 0) /
          assessedGaps.length
        ).toFixed(1)
      : "—";

  return (
    <div className="space-y-6 animate-fadeIn max-w-4xl mx-auto">
      {/* Header */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-black text-[#123057]">Progress & Capability Growth</h1>
          <p className="text-sm text-slate-500 mt-1">
            Real longitudinal capability progress based exclusively on verified assessments and recorded learning time.
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
          <div className="mt-3 text-3xl font-black text-[#123057]">{assessments.length}</div>
          <div className="mt-1 text-[11px] text-slate-400 font-semibold">Authoritative examinations</div>
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

      {/* Capability Timeline */}
      <div className="rounded-3xl border border-[#dfe7f0] bg-white p-6 sm:p-8 shadow-sm space-y-6">
        <div className="border-b border-slate-100 pb-4">
          <h2 className="text-lg font-bold text-[#123057]">Validated Assessment History</h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Chronological audit of formal competency evaluations that modified your profile.
          </p>
        </div>

        {assessments.length === 0 ? (
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
            {assessments.map((ass, idx) => (
              <div
                key={ass.id || idx}
                className="rounded-2xl border border-slate-100 bg-[#f8fafc] p-4 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3"
              >
                <div>
                  <div className="flex items-center gap-2">
                    <span className="rounded bg-teal-50 px-2 py-0.5 text-[10px] font-bold text-teal-800">
                      {ass.competency_code}
                    </span>
                    <span className="text-xs font-bold text-[#123057]">
                      {ass.title || "Standardized Assessment"}
                    </span>
                  </div>
                  <div className="text-[11px] text-slate-400 mt-1">
                    Submitted on {ass.submitted_at ? new Date(ass.submitted_at).toLocaleDateString() : "Recent"}
                  </div>
                </div>

                <div className="flex items-center gap-3">
                  <span className="rounded-full bg-emerald-100 px-3 py-1 text-xs font-extrabold text-emerald-800">
                    Level {ass.score?.toFixed(1) || (ass.percentage ? (ass.percentage / 20).toFixed(1) : "4.0")} / 5.0
                  </span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

export default OfficialProgress;
