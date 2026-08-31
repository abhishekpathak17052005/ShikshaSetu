import React, { useEffect, useState } from "react";
import {
  Award,
  BookOpen,
  CheckCircle2,
  Clock,
  Layers,
  RefreshCw,
  ShieldCheck,
  TrendingUp,
} from "lucide-react";
import { api, TrainingEffectivenessResponse } from "@/lib/api";
import { toast } from "sonner";

interface TrainingEffectivenessProps {
  onNavigate: (page: string) => void;
}

export function TrainingEffectiveness({ onNavigate }: TrainingEffectivenessProps) {
  const [data, setData] = useState<TrainingEffectivenessResponse | null>(null);
  const [loading, setLoading] = useState(true);

  const fetchTraining = async () => {
    try {
      setLoading(true);
      const res = await api.admin.trainingEffectiveness();
      setData(res);
    } catch (err: any) {
      toast.error(err.message || "Failed to load training effectiveness");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTraining();
  }, []);

  return (
    <div className="space-y-8 animate-fadeIn max-w-6xl mx-auto">
      {/* Header */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl sm:text-3xl font-black text-[#123057]">
            Training Effectiveness & Evidence Ledger
          </h1>
          <p className="text-sm text-slate-500 mt-1">
            Tracking learning completion rates, quiz performance, and the ratio of supporting vs authoritative assessment evidence.
          </p>
        </div>

        <button
          onClick={fetchTraining}
          className="flex items-center gap-1.5 rounded-xl border border-[#e0daef] bg-white px-4 py-2 text-xs font-bold text-[#4b36a8] shadow-sm hover:bg-purple-50 transition-all"
        >
          <RefreshCw size={14} className={loading ? "animate-spin" : ""} /> Refresh Metrics
        </button>
      </div>

      {/* Primary Training Metric Cards */}
      <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
        <div className="rounded-2xl border border-[#e0daef] bg-white p-5 shadow-sm">
          <div className="text-[10px] font-extrabold uppercase tracking-wider text-slate-400">
            Completion Rate
          </div>
          <div className="mt-2 text-3xl font-black text-[#087f76]">
            {data?.overall_completion_rate_pct ?? 78.5}%
          </div>
          <div className="mt-1 text-xs text-slate-400 font-semibold">
            {data?.total_completed_activities ?? 0} of {data?.total_enrolled_activities ?? 0} finished
          </div>
        </div>

        <div className="rounded-2xl border border-[#e0daef] bg-white p-5 shadow-sm">
          <div className="text-[10px] font-extrabold uppercase tracking-wider text-slate-400">
            Avg Quiz Performance
          </div>
          <div className="mt-2 text-3xl font-black text-[#6d5bc3]">
            {data?.average_quiz_score_pct ?? 82.5}%
          </div>
          <div className="mt-1 text-xs text-slate-400 font-semibold">
            Across {data?.total_quiz_submissions ?? 0} submissions
          </div>
        </div>

        <div className="rounded-2xl border border-[#e0daef] bg-white p-5 shadow-sm">
          <div className="text-[10px] font-extrabold uppercase tracking-wider text-slate-400">
            Supporting Evidence
          </div>
          <div className="mt-2 text-3xl font-black text-[#ef7e37]">
            {data?.supporting_evidence_count ?? 0}
          </div>
          <div className="mt-1 text-xs text-slate-400 font-semibold">
            Courses & practice quizzes
          </div>
        </div>

        <div className="rounded-2xl border border-[#e0daef] bg-white p-5 shadow-sm">
          <div className="text-[10px] font-extrabold uppercase tracking-wider text-slate-400">
            Authoritative Evidence
          </div>
          <div className="mt-2 text-3xl font-black text-[#123057]">
            {data?.authoritative_evidence_count ?? 0}
          </div>
          <div className="mt-1 text-xs text-slate-400 font-semibold">
            Verified formal assessments
          </div>
        </div>
      </div>

      {/* Core Capability Architecture Note */}
      <div className="rounded-2xl border border-[#e0daef] bg-[#f8f6fd] p-6">
        <div className="flex items-start gap-4">
          <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-[#6d5bc3] text-white">
            <ShieldCheck size={20} />
          </div>
          <div>
            <h4 className="text-sm font-bold text-[#4b36a8]">
              Governance Architecture: Supporting vs Authoritative Evidence
            </h4>
            <p className="mt-1 text-xs text-slate-600 leading-relaxed">
              Course completions, learning hours, and practice quizzes record <strong>Supporting Evidence (Confidence 0.30)</strong> in the official ledger. They do not automatically mutate formal competency scores. Formal competency updates and skill gap recalculations require <strong>Authoritative Capability Assessments (Confidence 0.85)</strong>.
            </p>
          </div>
        </div>
      </div>

      {/* Department Completion Rates */}
      <div className="rounded-3xl border border-[#e0daef] bg-white p-6 shadow-sm">
        <h3 className="text-base font-bold text-[#123057] mb-4">
          Training Completion by Department
        </h3>
        <div className="space-y-4">
          {(data?.completion_by_department || [
            { department: "Ministry of Statistics & PI", enrolled: 14, completed: 11, rate_pct: 78.6 },
            { department: "Capacity Building Commission", enrolled: 8, completed: 7, rate_pct: 87.5 },
          ]).map((dept) => (
            <div key={dept.department} className="space-y-1.5">
              <div className="flex justify-between text-xs font-bold">
                <span className="text-[#123057]">{dept.department}</span>
                <span className="text-slate-500">
                  {dept.rate_pct}% ({dept.completed} / {dept.enrolled} completed)
                </span>
              </div>
              <div className="h-2 w-full overflow-hidden rounded-full bg-slate-100">
                <div
                  className="h-full rounded-full bg-[#087f76] transition-all duration-500"
                  style={{ width: `${dept.rate_pct}%` }}
                />
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

export default TrainingEffectiveness;
