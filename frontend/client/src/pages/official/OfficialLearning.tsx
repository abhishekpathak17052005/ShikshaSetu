import React, { useState } from "react";
import {
  BookOpen,
  CheckCircle2,
  Clock,
  Play,
  ArrowRight,
  TrendingUp,
  Award,
  AlertCircle,
  RotateCcw,
  Check,
  Sparkles,
  FileQuestion,
  BookMarked,
} from "lucide-react";
import { useLearningActivities } from "@/hooks/useLearningActivities";
import { LearningActivity } from "@/lib/api";
import { CourseViewerModal } from "@/components/CourseViewerModal";
import { getCourseCurriculum } from "@/lib/courseContent";
import { toast } from "sonner";

interface OfficialLearningProps {
  initialActivityId?: string;
  onNavigate: (page: string, context?: { competencyCode?: string }) => void;
}

export function OfficialLearning({
  initialActivityId,
  onNavigate,
}: OfficialLearningProps) {
  const { activities, currentActivity, loading, updateProgress, completeActivity } =
    useLearningActivities(true);

  const [activeTab, setActiveTab] = useState<"ACTIVE" | "COMPLETED">("ACTIVE");
  const [showCompleteModal, setShowCompleteModal] = useState(false);
  const [targetCompleteActivity, setTargetCompleteActivity] = useState<LearningActivity | null>(null);
  const [completionScore, setCompletionScore] = useState<number | undefined>(85);
  const [notes, setNotes] = useState("");

  // Course Reader Modal
  const [viewerOpen, setViewerOpen] = useState(false);
  const [viewingCurriculum, setViewingCurriculum] = useState<{
    competencyCode?: string;
    resourceTitle?: string;
  }>({});

  const activeActivities = activities.filter((a) => a.status === "in_progress" || a.status === "not_started");
  const completedActivities = activities.filter((a) => a.status === "completed");

  const selectedActivity =
    (initialActivityId && activities.find((a) => a.activity_id === initialActivityId)) ||
    currentActivity ||
    activeActivities[0];

  const handleUpdateProgress = async (activity: LearningActivity, delta: number) => {
    const newProgress = Math.min(100, (activity.progress_percent || 0) + delta);
    const newDuration = (activity.duration_minutes || 0) + 15;
    await updateProgress(activity.activity_id, newProgress, newDuration);
    toast.success(`Progress updated to ${newProgress}%`);
  };

  const handleOpenCompleteModal = (activity: LearningActivity) => {
    setTargetCompleteActivity(activity);
    setShowCompleteModal(true);
  };

  const handleLaunchReader = (activity: LearningActivity) => {
    setViewingCurriculum({
      competencyCode: activity.competency_id,
      resourceTitle: activity.resource_id,
    });
    setViewerOpen(true);
  };

  const handleConfirmComplete = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!targetCompleteActivity) return;

    const res = await completeActivity(
      targetCompleteActivity.activity_id,
      completionScore,
      notes || "Learning module completed successfully"
    );

    if (res) {
      setShowCompleteModal(false);
      setTargetCompleteActivity(null);
      toast.success(
        "Learning completed! Supporting evidence recorded. Next: Take a capability assessment to validate your improvement."
      );
    }
  };

  const selectedCurriculum = selectedActivity
    ? getCourseCurriculum(selectedActivity.competency_id, selectedActivity.resource_id)
    : null;

  return (
    <div className="space-y-6 animate-fadeIn">
      {/* Course Reader Modal */}
      <CourseViewerModal
        isOpen={viewerOpen}
        onClose={() => setViewerOpen(false)}
        competencyCode={viewingCurriculum.competencyCode}
        resourceTitle={viewingCurriculum.resourceTitle}
        onLaunchQuiz={(comp) => onNavigate("Quizzes", { competencyCode: comp })}
        onCompleteActivity={() => {
          if (selectedActivity) {
            handleUpdateProgress(selectedActivity, 100);
          }
        }}
      />

      {/* Top Header */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-black text-[#123057]">My Learning Workspace</h1>
          <p className="text-sm text-slate-500 mt-1">
            Track module completions, record supporting evidence, and prepare for capability validation.
          </p>
        </div>

        {/* Tab Toggle */}
        <div className="flex items-center gap-1 rounded-2xl border border-[#dfe7f0] bg-white p-1.5 shadow-sm">
          <button
            onClick={() => setActiveTab("ACTIVE")}
            className={`flex items-center gap-2 rounded-xl px-4 py-2 text-xs font-bold transition-all ${
              activeTab === "ACTIVE"
                ? "bg-[#087f76] text-white shadow-sm"
                : "text-slate-500 hover:text-slate-800"
            }`}
          >
            <Play size={13} /> Active Activities ({activeActivities.length})
          </button>
          <button
            onClick={() => setActiveTab("COMPLETED")}
            className={`flex items-center gap-2 rounded-xl px-4 py-2 text-xs font-bold transition-all ${
              activeTab === "COMPLETED"
                ? "bg-[#087f76] text-white shadow-sm"
                : "text-slate-500 hover:text-slate-800"
            }`}
          >
            <CheckCircle2 size={13} /> Completed ({completedActivities.length})
          </button>
        </div>
      </div>

      {/* Evidence & Ecosystem Note */}
      <div className="flex items-start gap-3 rounded-2xl border border-amber-100 bg-amber-50/70 p-4 text-xs text-amber-900">
        <Award size={18} className="text-amber-600 shrink-0 mt-0.5" />
        <div className="space-y-0.5">
          <div className="font-bold text-[#123057] flex items-center gap-2">
            <span>Learning ≠ Proven Competency Governance Architecture</span>
            <span className="rounded-md bg-amber-200/80 px-2 py-0.5 text-[10px] font-semibold text-amber-800">
              Supporting Evidence (0.30)
            </span>
          </div>
          <p className="text-slate-600 leading-relaxed">
            Completing self-paced modules records verifiable supporting evidence in your capability ledger. 
            Formal competency ratings and skill gap recalculations require authoritative validation through AI Quizzes or Proctored Assessments.
          </p>
        </div>
      </div>

      {/* ── ACTIVE TAB ── */}
      {activeTab === "ACTIVE" && (
        <div className="space-y-6">
          {loading ? (
            <div className="h-64 rounded-3xl bg-white animate-pulse border border-slate-200" />
          ) : activeActivities.length === 0 ? (
            <div className="rounded-3xl border border-dashed border-[#dfe7f0] bg-white p-12 text-center">
              <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-teal-50 text-teal-700">
                <BookOpen size={24} />
              </div>
              <h3 className="mt-4 text-base font-bold text-[#123057]">
                No active learning activities
              </h3>
              <p className="mt-1 text-sm text-slate-500 max-w-md mx-auto">
                Explore personalized iGOT/NSSTA curriculum recommendations to start closing capability deficits.
              </p>
              <button
                onClick={() => onNavigate("Recommendations")}
                className="mt-5 inline-flex items-center gap-2 rounded-xl bg-[#ef7e37] px-5 py-2.5 text-xs font-bold text-white hover:bg-[#d96a27]"
              >
                Browse Recommendations <ArrowRight size={13} />
              </button>
            </div>
          ) : (
            <div className="grid gap-6 lg:grid-cols-3">
              {/* Primary Active Card (2 cols) */}
              {selectedActivity && selectedCurriculum && (
                <div className="rounded-3xl border border-[#dfe7f0] bg-white p-6 sm:p-8 shadow-sm lg:col-span-2 space-y-6">
                  <div className="flex flex-wrap items-start justify-between gap-3 border-b border-slate-100 pb-4">
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="rounded-full bg-[#123057] px-2.5 py-0.5 text-[10px] font-extrabold uppercase text-white">
                          {selectedCurriculum.provider}
                        </span>
                        <span className="rounded-md bg-teal-50 px-2.5 py-0.5 text-[11px] font-extrabold uppercase text-teal-800">
                          {selectedActivity.competency_id}
                        </span>
                      </div>
                      <h2 className="text-xl font-bold text-[#123057] mt-2">
                        {selectedCurriculum.title}
                      </h2>
                    </div>

                    <div className="flex items-center gap-2 text-xs font-semibold text-slate-400">
                      <Clock size={14} />
                      <span>{selectedActivity.duration_minutes || 0} mins logged</span>
                    </div>
                  </div>

                  {/* Progress Bar */}
                  <div className="space-y-2">
                    <div className="flex justify-between text-xs font-bold">
                      <span className="text-slate-500">Learning Progress</span>
                      <span className="text-[#087f76]">{selectedActivity.progress_percent}% Completed</span>
                    </div>
                    <div className="h-3 w-full overflow-hidden rounded-full bg-slate-100">
                      <div
                        className="h-full rounded-full bg-[#087f76] transition-all duration-500"
                        style={{ width: `${selectedActivity.progress_percent}%` }}
                      />
                    </div>
                  </div>

                  {/* Objective & Context */}
                  <div className="rounded-2xl bg-[#f8fafc] p-4 text-xs leading-relaxed text-slate-600 border border-slate-100 space-y-1.5">
                    <div>
                      <strong className="text-[#123057] font-semibold">Curriculum Overview:</strong> {selectedCurriculum.overview}
                    </div>
                    <div className="text-[11px] text-slate-500">
                      <strong>Target Competency:</strong> {selectedCurriculum.competencyName} • <strong>Estimated Time:</strong> {selectedCurriculum.estimatedTime}
                    </div>
                  </div>

                  {/* Action Buttons */}
                  <div className="flex flex-wrap items-center gap-3 pt-2">
                    <button
                      onClick={() => handleLaunchReader(selectedActivity)}
                      className="inline-flex items-center gap-2 rounded-xl bg-[#087f76] px-5 py-2.5 text-xs font-bold text-white shadow hover:bg-[#06655e] transition-all"
                    >
                      <BookOpen size={14} /> Study Course Content ({selectedCurriculum.chapters.length} Chapters)
                    </button>

                    <button
                      onClick={() => handleUpdateProgress(selectedActivity, 25)}
                      disabled={selectedActivity.progress_percent >= 100}
                      className="inline-flex items-center gap-1.5 rounded-xl bg-teal-50 px-4 py-2.5 text-xs font-bold text-teal-800 hover:bg-teal-100 transition-colors"
                    >
                      +25% Progress
                    </button>

                    <button
                      onClick={() => handleOpenCompleteModal(selectedActivity)}
                      className="inline-flex items-center gap-2 rounded-xl border border-slate-200 bg-white px-4 py-2.5 text-xs font-bold text-slate-700 hover:bg-slate-50 transition-colors"
                    >
                      <CheckCircle2 size={14} /> Mark as Complete
                    </button>

                    <button
                      onClick={() => onNavigate("Quizzes", { competencyCode: selectedActivity.competency_id })}
                      className="inline-flex items-center gap-1 text-xs font-bold text-[#ef7e37] hover:underline ml-auto"
                    >
                      <FileQuestion size={14} /> Attempt Practice Quiz →
                    </button>
                  </div>
                </div>
              )}

              {/* Side: Next Steps & Evidence Notice */}
              <div className="rounded-3xl border border-[#dfe7f0] bg-white p-6 shadow-sm space-y-5">
                <div className="flex items-center gap-2 text-[#087f76]">
                  <Award size={20} />
                  <h3 className="text-sm font-extrabold text-[#123057]">Evidence Rules</h3>
                </div>

                <p className="text-xs text-slate-500 leading-relaxed">
                  Completing this module records <strong className="text-teal-800">Supporting Evidence (0.30 confidence)</strong>.
                </p>

                <div className="rounded-xl border border-amber-200 bg-amber-50/50 p-3.5 text-xs text-amber-900 leading-relaxed">
                  <strong>Important:</strong> Learning alone does not directly increase competency. Take a formal capability assessment afterwards to validate your growth.
                </div>

                <button
                  onClick={() => onNavigate("Assessments")}
                  className="w-full inline-flex items-center justify-center gap-2 rounded-xl bg-[#123057] py-2.5 text-xs font-bold text-white shadow hover:bg-[#1a3d6d] transition-colors"
                >
                  Capability Assessment <ArrowRight size={13} />
                </button>
              </div>
            </div>
          )}
        </div>
      )}

      {/* ── COMPLETED TAB ── */}
      {activeTab === "COMPLETED" && (
        <div className="space-y-4">
          {completedActivities.length === 0 ? (
            <div className="rounded-2xl border border-dashed border-[#dfe7f0] bg-white p-12 text-center text-xs text-slate-400">
              No completed activities yet.
            </div>
          ) : (
            completedActivities.map((act) => (
              <div
                key={act.activity_id}
                className="rounded-2xl border border-emerald-100 bg-white p-6 shadow-sm flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4"
              >
                <div>
                  <div className="flex items-center gap-2">
                    <span className="rounded bg-emerald-50 px-2 py-0.5 text-[10px] font-bold text-emerald-800">
                      COMPLETED
                    </span>
                    <span className="text-xs font-bold text-slate-400">
                      {act.competency_id}
                    </span>
                  </div>
                  <h3 className="text-base font-bold text-[#123057] mt-1">
                    {act.resource_id}
                  </h3>
                  <div className="text-xs text-slate-400 mt-1">
                    {act.completed_at ? new Date(act.completed_at).toLocaleDateString() : "Recently"} · {act.duration_minutes} minutes spent
                  </div>
                </div>

                <div className="flex items-center gap-3">
                  <span className="inline-flex items-center gap-1 rounded-full bg-teal-50 px-3 py-1 text-xs font-bold text-teal-800">
                    <Check size={12} /> Supporting Evidence Logged (0.30)
                  </span>

                  <button
                    onClick={() => onNavigate("Assessments", { competencyCode: act.competency_id })}
                    className="inline-flex items-center gap-1.5 rounded-xl bg-[#087f76] px-4 py-2 text-xs font-bold text-white shadow hover:bg-[#06655e]"
                  >
                    Validate via Assessment →
                  </button>
                </div>
              </div>
            ))
          )}
        </div>
      )}

      {/* ── Complete Modal ── */}
      {showCompleteModal && targetCompleteActivity && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4 backdrop-blur-sm animate-fadeIn">
          <div className="relative w-full max-w-md rounded-3xl bg-white p-6 shadow-2xl border border-[#dfe7f0]">
            <h3 className="text-lg font-extrabold text-[#123057]">
              Complete Learning Activity
            </h3>
            <p className="text-xs text-slate-400 mt-1">
              Resource: <strong>{targetCompleteActivity.resource_id}</strong>
            </p>

            <form onSubmit={handleConfirmComplete} className="mt-5 space-y-4">
              {/* Evidence explanation note */}
              <div className="rounded-xl border border-teal-200 bg-teal-50/50 p-4 text-xs text-teal-900 leading-relaxed">
                <strong className="block mb-1 font-bold">Evidence Confirmation:</strong>
                Marking this module as complete records <span className="font-bold">Supporting Evidence</span>. Your official competency score will not change until you pass a standardized capability assessment.
              </div>

              {/* Optional Score */}
              <div className="space-y-1.5">
                <label className="block text-xs font-bold text-slate-700">
                  Self-Assessment / Quiz Score % (Optional):
                </label>
                <input
                  type="number"
                  min="0"
                  max="100"
                  value={completionScore}
                  onChange={(e) => setCompletionScore(parseInt(e.target.value))}
                  className="w-full rounded-xl border border-slate-200 px-3 py-2 text-xs text-[#123057] focus:outline-none"
                  placeholder="e.g. 85"
                />
              </div>

              {/* Completion Notes */}
              <div className="space-y-1.5">
                <label className="block text-xs font-bold text-slate-700">
                  Learning Notes / Takeaways:
                </label>
                <textarea
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                  rows={2}
                  className="w-full rounded-xl border border-slate-200 p-2.5 text-xs text-slate-800 focus:outline-none"
                  placeholder="Key concepts covered..."
                />
              </div>

              {/* Actions */}
              <div className="border-t border-slate-100 pt-4 flex items-center justify-end gap-2">
                <button
                  type="button"
                  onClick={() => setShowCompleteModal(false)}
                  className="rounded-xl border border-slate-200 px-4 py-2 text-xs font-bold text-slate-600"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="rounded-xl bg-[#087f76] px-5 py-2 text-xs font-bold text-white shadow hover:bg-[#06655e]"
                >
                  Confirm & Log Evidence
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

export default OfficialLearning;
