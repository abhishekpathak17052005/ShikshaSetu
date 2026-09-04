import React, { useEffect, useState } from "react";
import {
  BookOpen,
  CheckCircle2,
  Clock,
  FilePlus,
  FileQuestion,
  HelpCircle,
  Layers,
  PenTool,
  TrendingUp,
  Users,
  XCircle,
  ArrowRight,
  Sparkles,
  Award,
} from "lucide-react";
import { api, TrainerDashboard as TrainerDashboardType } from "@/lib/api";
import { toast } from "sonner";
import { NumberReveal, ProgressBarFill } from "@/components/motion/MotionUtils";

interface TrainerDashboardProps {
  onNavigate: (page: string) => void;
}

export function TrainerDashboard({ onNavigate }: TrainerDashboardProps) {
  const [metrics, setMetrics] = useState<TrainerDashboardType | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchDashboard() {
      try {
        setLoading(true);
        const data = await api.trainer.dashboard();
        setMetrics(data);
      } catch (err: any) {
        toast.error(err.message || "Failed to load dashboard metrics");
      } finally {
        setLoading(false);
      }
    }
    fetchDashboard();
  }, []);

  const totalMaterials = metrics?.materials_count ?? metrics?.total_materials_uploaded ?? 0;
  const totalQuizzes = metrics?.quizzes_count ?? metrics?.total_quizzes_created ?? 0;
  const publishedQuizzes = metrics?.published_quizzes_count ?? metrics?.published_quizzes ?? 0;
  const totalAssignedLearners = metrics?.total_assigned_learners ?? 0;

  const approvedCount = metrics?.approved_questions_count ?? metrics?.questions_approved ?? 0;
  const pendingCount = metrics?.pending_questions_count ?? metrics?.pending_review_count ?? metrics?.questions_pending_review ?? 0;
  const rejectedCount = metrics?.rejected_questions_count ?? metrics?.questions_rejected ?? 0;

  const totalQuestions = metrics?.questions_count ?? metrics?.total_questions_generated ?? (
    approvedCount + pendingCount + rejectedCount
  );

  const approvedPct = totalQuestions > 0 ? Math.round((approvedCount / totalQuestions) * 100) : 0;
  const pendingPct = totalQuestions > 0 ? Math.round((pendingCount / totalQuestions) * 100) : 0;
  const rejectedPct = totalQuestions > 0 ? Math.round((rejectedCount / totalQuestions) * 100) : 0;

  return (
    <div className="space-y-8 anim-page-enter">
      {/* ── Top Header Banner ── */}
      <div className="relative overflow-hidden rounded-3xl bg-gradient-to-br from-[#1a2744] via-[#24355a] to-[#c2510e] p-8 text-white shadow-lg anim-fade-up">
        <div className="relative z-10 flex flex-col justify-between gap-6 lg:flex-row lg:items-center">
          <div className="max-w-2xl">
            <div className="inline-flex items-center gap-2 rounded-full bg-white/10 px-3 py-1 text-xs font-semibold uppercase tracking-wider backdrop-blur-md anim-badge-pop">
              <Sparkles size={14} className="text-[#ef7e37]" />
              AI Assessment Studio
            </div>
            <h1 className="mt-3 text-3xl font-bold tracking-tight sm:text-4xl text-white">
              Trainer Capability Studio
            </h1>
            <p className="mt-2 text-sm leading-relaxed text-slate-200 font-normal">
              Upload public-service curriculum, generate AI-grounded MCQs, audit & approve valid questions, assemble authoritative quizzes, and provide qualitative feedback to civil servants.
            </p>
          </div>
          <div className="flex flex-col sm:flex-row lg:flex-col gap-3 shrink-0 lg:items-end lg:ml-auto">
            <button
              onClick={() => onNavigate("Upload Material")}
              className="inline-flex items-center justify-center gap-2 rounded-xl bg-[#ef7e37] px-6 py-3 text-sm font-semibold text-white shadow-md hover:bg-[#d96a27] btn-interactive w-full sm:w-48"
            >
              <FilePlus size={16} />
              Upload Material
            </button>
            <button
              onClick={() => onNavigate("AI Question Generator")}
              className="inline-flex items-center justify-center gap-2 rounded-xl bg-white/10 backdrop-blur-md border border-white/20 px-6 py-3 text-sm font-semibold text-white hover:bg-white/20 btn-interactive w-full sm:w-48"
            >
              <FileQuestion size={16} />
              Generate Questions
            </button>
          </div>
        </div>
      </div>

      {/* ── KPI Stat Cards ── */}
      <div className="grid grid-cols-2 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {/* Card 1 */}
        <div className="rounded-2xl border border-[#f0ddd0] bg-white p-5 shadow-sm card-interactive anim-card-enter stagger-1">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">
              Learning Materials
            </span>
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-amber-50 text-amber-600">
              <BookOpen size={18} />
            </div>
          </div>
          <div className="mt-4 flex items-baseline gap-2">
            <span className="text-3xl font-extrabold tracking-tight text-slate-800">
              {loading ? "..." : <NumberReveal value={totalMaterials} />}
            </span>
            <span className="text-xs font-medium text-slate-400">curriculum docs</span>
          </div>
          <button
            onClick={() => onNavigate("Learning Materials")}
            className="mt-3 flex items-center gap-1 text-xs font-semibold text-[#ef7e37] hover:underline btn-interactive"
          >
            View materials <ArrowRight size={12} />
          </button>
        </div>

        {/* Card 2 */}
        <div className="rounded-2xl border border-[#f0ddd0] bg-white p-5 shadow-sm card-interactive anim-card-enter stagger-2">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">
              Question Pool
            </span>
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-blue-50 text-blue-600">
              <HelpCircle size={18} />
            </div>
          </div>
          <div className="mt-4 flex items-baseline gap-2">
            <span className="text-3xl font-extrabold tracking-tight text-slate-800">
              {loading ? "..." : <NumberReveal value={totalQuestions} />}
            </span>
            <span className="text-xs font-medium text-slate-400">generated items</span>
          </div>
          <button
            onClick={() => onNavigate("Question Review")}
            className="mt-3 flex items-center gap-1 text-xs font-bold text-blue-600 hover:underline btn-interactive"
          >
            Review questions <ArrowRight size={12} />
          </button>
        </div>

        {/* Card 3 */}
        <div className="rounded-2xl border border-[#f0ddd0] bg-white p-5 shadow-sm card-interactive anim-card-enter stagger-3">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold uppercase tracking-wider text-slate-400">
              Published Quizzes
            </span>
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-purple-50 text-purple-600">
              <Layers size={18} />
            </div>
          </div>
          <div className="mt-4 flex items-baseline gap-2">
            <span className="text-3xl font-black text-slate-800">
              {loading ? "..." : <NumberReveal value={publishedQuizzes} />}
            </span>
            <span className="text-xs font-semibold text-slate-400">
              of {totalQuizzes} created
            </span>
          </div>
          <button
            onClick={() => onNavigate("Quiz Studio")}
            className="mt-3 flex items-center gap-1 text-xs font-bold text-purple-600 hover:underline btn-interactive"
          >
            Open Quiz Studio <ArrowRight size={12} />
          </button>
        </div>

        {/* Card 4 */}
        <div className="rounded-2xl border border-[#f0ddd0] bg-white p-5 shadow-sm card-interactive anim-card-enter stagger-4">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold uppercase tracking-wider text-slate-400">
              Assigned Learners
            </span>
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-emerald-50 text-emerald-600">
              <Users size={18} />
            </div>
          </div>
          <div className="mt-4 flex items-baseline gap-2">
            <span className="text-3xl font-black text-slate-800">
              {loading ? "..." : <NumberReveal value={totalAssignedLearners} />}
            </span>
            <span className="text-xs font-semibold text-slate-400">civil servants</span>
          </div>
          <button
            onClick={() => onNavigate("Learner Results")}
            className="mt-3 flex items-center gap-1 text-xs font-bold text-emerald-600 hover:underline btn-interactive"
          >
            View submissions <ArrowRight size={12} />
          </button>
        </div>
      </div>

      {/* ── Middle Section: Question Audit Pipeline & Quick Actions ── */}
      <div className="grid gap-6 lg:grid-cols-3">
        {/* Left: Question Review Funnel (2 cols) */}
        <div className="rounded-2xl border border-[#f0ddd0] bg-white p-6 shadow-sm lg:col-span-2 anim-card-enter stagger-5">
          <div className="flex items-center justify-between border-b border-slate-100 pb-4">
            <div>
              <h2 className="text-lg font-bold text-slate-800">
                Question Review & Verification Pipeline
              </h2>
              <p className="text-xs text-slate-400 mt-0.5">
                AI generates candidate MCQs. Trainer verification ensures grounding & pedagogical quality.
              </p>
            </div>
            <button
              onClick={() => onNavigate("Question Review")}
              className="rounded-lg bg-orange-50 px-3 py-1.5 text-xs font-bold text-[#c2510e] hover:bg-orange-100 btn-interactive"
            >
              Open Studio
            </button>
          </div>

          {/* Progress Stack Bar */}
          <div className="mt-6">
            <div className="flex h-4 w-full overflow-hidden rounded-full bg-slate-100 p-0.5">
              <div
                style={{ width: `${approvedPct}%` }}
                className="bg-emerald-500 rounded-l-full transition-all duration-700 ease-out"
                title={`Approved: ${approvedCount} (${approvedPct}%)`}
              />
              <div
                style={{ width: `${pendingPct}%` }}
                className="bg-amber-400 transition-all duration-700 ease-out"
                title={`Pending Review: ${pendingCount} (${pendingPct}%)`}
              />
              <div
                style={{ width: `${rejectedPct}%` }}
                className="bg-rose-500 rounded-r-full transition-all duration-700 ease-out"
                title={`Rejected: ${rejectedCount} (${rejectedPct}%)`}
              />
            </div>

            {/* Legend Stats */}
            <div className="mt-6 grid grid-cols-3 gap-4">
              <div className="rounded-xl border border-emerald-100 bg-emerald-50/50 p-4 anim-card-enter stagger-1">
                <div className="flex items-center gap-2 text-xs font-bold text-emerald-700">
                  <CheckCircle2 size={16} />
                  Approved
                </div>
                <div className="mt-2 text-2xl font-black text-emerald-800">
                  <NumberReveal value={approvedCount} />
                </div>
                <div className="text-[11px] text-emerald-600 font-medium">
                  {approvedPct}% of total · Ready for quizzes
                </div>
              </div>

              <div className="rounded-xl border border-amber-100 bg-amber-50/50 p-4 anim-card-enter stagger-2">
                <div className="flex items-center gap-2 text-xs font-bold text-amber-700">
                  <Clock size={16} />
                  Pending Review
                </div>
                <div className="mt-2 text-2xl font-black text-amber-800">
                  <NumberReveal value={pendingCount} />
                </div>
                <div className="text-[11px] text-amber-600 font-medium">
                  {pendingPct}% of total · Awaiting audit
                </div>
              </div>

              <div className="rounded-xl border border-rose-100 bg-rose-50/50 p-4 anim-card-enter stagger-3">
                <div className="flex items-center gap-2 text-xs font-bold text-rose-700">
                  <XCircle size={16} />
                  Rejected
                </div>
                <div className="mt-2 text-2xl font-black text-rose-800">
                  <NumberReveal value={rejectedCount} />
                </div>
                <div className="text-[11px] text-rose-600 font-medium">
                  {rejectedPct}% of total · Poorly grounded
                </div>
              </div>
            </div>
          </div>

          {/* Workflow Notice */}
          <div className="mt-6 rounded-xl bg-slate-50 p-4 border border-slate-200/60 flex items-start gap-3 anim-fade-up">
            <div className="mt-0.5 text-[#ef7e37]">
              <Award size={18} />
            </div>
            <div className="text-xs text-slate-600 leading-relaxed">
              <strong className="text-slate-800 font-semibold">Authoritative Integrity Rule:</strong> Only questions with status <span className="font-bold text-emerald-600">APPROVED</span> can be added to published quizzes. Draft quizzes enforce strict question vetting.
            </div>
          </div>
        </div>

        {/* Right: Quick Action Hub (1 col) */}
        <div className="flex flex-col justify-between rounded-2xl border border-[#f0ddd0] bg-white p-6 shadow-sm anim-card-enter stagger-6">
          <div>
            <h2 className="text-lg font-bold text-slate-800">Workflow Launchpad</h2>
            <p className="text-xs text-slate-400 mt-0.5">
              Standard 5-step curriculum evaluation loop
            </p>

            <div className="mt-5 space-y-3">
              <button
                onClick={() => onNavigate("Upload Material")}
                className="flex w-full items-center justify-between rounded-xl border border-slate-100 bg-slate-50/50 p-3 text-left hover:border-orange-200 hover:bg-[#fff9f5] transition-all group btn-interactive"
              >
                <div className="flex items-center gap-3">
                  <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-orange-100 text-[#c2510e]">
                    <FilePlus size={16} />
                  </div>
                  <div>
                    <div className="text-xs font-bold text-slate-800 group-hover:text-[#c2510e]">
                      1. Upload Content
                    </div>
                    <div className="text-[11px] text-slate-400">PDF, DOCX, TXT manuals</div>
                  </div>
                </div>
                <ArrowRight size={14} className="text-slate-400 group-hover:text-[#ef7e37]" />
              </button>

              <button
                onClick={() => onNavigate("AI Question Generator")}
                className="flex w-full items-center justify-between rounded-xl border border-slate-100 bg-slate-50/50 p-3 text-left hover:border-orange-200 hover:bg-[#fff9f5] transition-all group btn-interactive"
              >
                <div className="flex items-center gap-3">
                  <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-blue-100 text-blue-600">
                    <FileQuestion size={16} />
                  </div>
                  <div>
                    <div className="text-xs font-bold text-slate-800 group-hover:text-blue-600">
                      2. Generate MCQs
                    </div>
                    <div className="text-[11px] text-slate-400">RAG grounded generation</div>
                  </div>
                </div>
                <ArrowRight size={14} className="text-slate-400 group-hover:text-blue-600" />
              </button>

              <button
                onClick={() => onNavigate("Question Review")}
                className="flex w-full items-center justify-between rounded-xl border border-slate-100 bg-slate-50/50 p-3 text-left hover:border-orange-200 hover:bg-[#fff9f5] transition-all group btn-interactive"
              >
                <div className="flex items-center gap-3">
                  <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-amber-100 text-amber-600">
                    <CheckCircle2 size={16} />
                  </div>
                  <div>
                    <div className="text-xs font-bold text-slate-800 group-hover:text-amber-600">
                      3. Audit & Approve
                    </div>
                    <div className="text-[11px] text-slate-400">Edit or reject bad items</div>
                  </div>
                </div>
                <ArrowRight size={14} className="text-slate-400 group-hover:text-amber-600" />
              </button>

              <button
                onClick={() => onNavigate("Quiz Studio")}
                className="flex w-full items-center justify-between rounded-xl border border-slate-100 bg-slate-50/50 p-3 text-left hover:border-orange-200 hover:bg-[#fff9f5] transition-all group btn-interactive"
              >
                <div className="flex items-center gap-3">
                  <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-purple-100 text-purple-600">
                    <PenTool size={16} />
                  </div>
                  <div>
                    <div className="text-xs font-bold text-slate-800 group-hover:text-purple-600">
                      4. Create & Assign Quiz
                    </div>
                    <div className="text-[11px] text-slate-400">Target civil service batches</div>
                  </div>
                </div>
                <ArrowRight size={14} className="text-slate-400 group-hover:text-purple-600" />
              </button>

              <button
                onClick={() => onNavigate("Learner Results")}
                className="flex w-full items-center justify-between rounded-xl border border-slate-100 bg-slate-50/50 p-3 text-left hover:border-orange-200 hover:bg-[#fff9f5] transition-all group btn-interactive"
              >
                <div className="flex items-center gap-3">
                  <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-emerald-100 text-emerald-600">
                    <TrendingUp size={16} />
                  </div>
                  <div>
                    <div className="text-xs font-bold text-slate-800 group-hover:text-emerald-600">
                      5. Qualitative Feedback
                    </div>
                    <div className="text-[11px] text-slate-400">Evaluate understanding</div>
                  </div>
                </div>
                <ArrowRight size={14} className="text-slate-400 group-hover:text-emerald-600" />
              </button>
            </div>
          </div>

          <div className="mt-6 rounded-xl bg-orange-50/50 border border-orange-100 p-3 text-center">
            <span className="text-[10px] font-extrabold uppercase tracking-widest text-[#ef7e37]">
              SIH 2026 Team Kinetics
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}

export default TrainerDashboard;
