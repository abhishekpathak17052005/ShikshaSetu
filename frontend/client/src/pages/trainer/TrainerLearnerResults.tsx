import React, { useEffect, useState } from "react";
import {
  BarChart2,
  CheckCircle2,
  Clock,
  MessageSquare,
  Search,
  Star,
  UserCheck,
  X,
  Send,
  RefreshCw,
  Award,
  Layers,
  HelpCircle,
  TrendingUp,
} from "lucide-react";
import {
  api,
  clearApiCache,
  TrainerQuiz,
  TrainerLearnerAttempt,
} from "@/lib/api";
import { toast } from "sonner";

interface TrainerLearnerResultsProps {
  initialQuizId?: string;
  onNavigate: (page: string) => void;
}

export function TrainerLearnerResults({
  initialQuizId,
  onNavigate,
}: TrainerLearnerResultsProps) {
  const [quizzes, setQuizzes] = useState<TrainerQuiz[]>([]);
  const [attempts, setAttempts] = useState<TrainerLearnerAttempt[]>([]);
  const [loading, setLoading] = useState(true);

  // Filters
  const [selectedQuizId, setSelectedQuizId] = useState(initialQuizId || "ALL");
  const [searchQuery, setSearchQuery] = useState("");

  // Feedback Modal State
  const [feedbackModalOpen, setFeedbackModalOpen] = useState(false);
  const [activeAttempt, setActiveAttempt] = useState<TrainerLearnerAttempt | null>(null);
  const [feedbackText, setFeedbackText] = useState("");
  const [strengthsInput, setStrengthsInput] = useState("");
  const [strengths, setStrengths] = useState<string[]>([]);
  const [areasInput, setAreasInput] = useState("");
  const [areasForImprovement, setAreasForImprovement] = useState<string[]>([]);
  const [rating, setRating] = useState<number>(4);
  const [submittingFeedback, setSubmittingFeedback] = useState(false);

  const fetchResults = async () => {
    clearApiCache();
    try {
      setLoading(true);
      const quizList = await api.trainer.quizzes.list();
      setQuizzes(quizList);

      const allAttempts: TrainerLearnerAttempt[] = [];

      if (selectedQuizId && selectedQuizId !== "ALL") {
        const list = await api.trainer.quizzes.getAttempts(selectedQuizId);
        allAttempts.push(...list);
      } else {
        for (const q of quizList) {
          const qid = q.id || q.quiz_id || (q as any)._id;
          try {
            const list = await api.trainer.quizzes.getAttempts(qid);
            allAttempts.push(...list);
          } catch {
            // Ignore
          }
        }
      }

      setAttempts(allAttempts);
    } catch (err: any) {
      toast.error(err.message || "Failed to load learner results");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchResults();
  }, [selectedQuizId]);

  const openFeedbackModal = (att: TrainerLearnerAttempt) => {
    setActiveAttempt(att);
    if (att.trainer_feedback) {
      setFeedbackText(att.trainer_feedback.feedback_text || "");
      setStrengths(att.trainer_feedback.strengths || []);
      setAreasForImprovement(att.trainer_feedback.areas_for_improvement || []);
      setRating(att.trainer_feedback.rating || 4);
    } else {
      setFeedbackText("");
      setStrengths(["Strong foundational understanding", "Accurate conceptual recall"]);
      setAreasForImprovement(["Review complex edge cases in regulations"]);
      setRating(4);
    }
    setFeedbackModalOpen(true);
  };

  const handleAddStrength = () => {
    if (strengthsInput.trim() && !strengths.includes(strengthsInput.trim())) {
      setStrengths([...strengths, strengthsInput.trim()]);
      setStrengthsInput("");
    }
  };

  const handleAddArea = () => {
    if (areasInput.trim() && !areasForImprovement.includes(areasInput.trim())) {
      setAreasForImprovement([...areasForImprovement, areasInput.trim()]);
      setAreasInput("");
    }
  };

  const handleSubmitFeedback = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!activeAttempt) return;
    const attId = activeAttempt.attempt_id || activeAttempt._id || (activeAttempt as any).id;

    if (!feedbackText.trim()) {
      toast.error("Please enter qualitative evaluation feedback remarks.");
      return;
    }

    try {
      setSubmittingFeedback(true);
      const res = await api.trainer.attempts.submitFeedback(attId, {
        feedback_text: feedbackText.trim(),
        strengths,
        areas_for_improvement: areasForImprovement,
        rating,
      });

      toast.success("Trainer evaluation feedback attached successfully!");
      setAttempts((prev) =>
        prev.map((item) =>
          (item.attempt_id || item._id || (item as any).id) === attId
            ? {
                ...item,
                has_trainer_feedback: true,
                trainer_feedback: res.trainer_feedback || {
                  feedback_text: feedbackText.trim(),
                  strengths,
                  areas_for_improvement: areasForImprovement,
                  rating,
                },
              }
            : item
        )
      );
      setFeedbackModalOpen(false);
      setActiveAttempt(null);
    } catch (err: any) {
      toast.error(err.message || "Failed to submit feedback");
    } finally {
      setSubmittingFeedback(false);
    }
  };

  const filteredAttempts = attempts.filter((att) => {
    const term = searchQuery.toLowerCase();
    return (
      att.learner_name?.toLowerCase().includes(term) ||
      att.learner_email?.toLowerCase().includes(term) ||
      att.quiz_title?.toLowerCase().includes(term) ||
      att.competency_code?.toLowerCase().includes(term)
    );
  });

  return (
    <div className="space-y-6 animate-fadeIn">
      {/* Top Header */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-black text-slate-800">Learner Assessment Results</h1>
          <p className="text-sm text-slate-500 mt-1">
            Review civil servant quiz attempts, inspect understanding gaps, and provide qualitative feedback.
          </p>
        </div>

        <button
          onClick={fetchResults}
          className="flex items-center gap-1.5 rounded-xl border border-[#f0ddd0] bg-white px-3.5 py-2 text-xs font-bold text-slate-600 hover:bg-orange-50 transition-colors"
        >
          <RefreshCw size={14} className={loading ? "animate-spin" : ""} />
          Refresh Results
        </button>
      </div>

      {/* Filter Toolbar */}
      <div className="flex flex-col gap-3 rounded-2xl border border-[#f0ddd0] bg-white p-4 shadow-sm sm:flex-row sm:items-center sm:justify-between">
        {/* Search Bar */}
        <div className="flex flex-1 items-center gap-2 rounded-xl border border-slate-200 px-3 py-2">
          <Search size={16} className="text-slate-400" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search by learner name, email, or quiz..."
            className="w-full bg-transparent text-xs text-slate-800 placeholder-slate-400 focus:outline-none"
          />
          {searchQuery && (
            <button onClick={() => setSearchQuery("")} className="text-xs text-slate-400">
              <X size={14} />
            </button>
          )}
        </div>

        {/* Quiz Filter */}
        <div className="flex items-center gap-2">
          <label className="text-xs font-bold text-slate-500 whitespace-nowrap">Filter Quiz:</label>
          <select
            value={selectedQuizId}
            onChange={(e) => setSelectedQuizId(e.target.value)}
            className="rounded-xl border border-slate-200 bg-white px-3 py-2 text-xs font-semibold text-slate-700 focus:border-[#ef7e37] focus:outline-none"
          >
            <option value="ALL">All Quizzes</option>
            {quizzes.map((q) => (
              <option key={q.id || q.quiz_id || (q as any)._id} value={q.id || q.quiz_id || (q as any)._id}>
                {q.title}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Results Table */}
      {loading ? (
        <div className="space-y-3">
          {[1, 2, 3, 4].map((n) => (
            <div key={n} className="h-16 rounded-2xl bg-white animate-pulse border border-slate-200" />
          ))}
        </div>
      ) : filteredAttempts.length === 0 ? (
        <div className="rounded-2xl border border-dashed border-[#f0ddd0] bg-white p-12 text-center">
          <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-orange-50 text-[#ef7e37]">
            <BarChart2 size={24} />
          </div>
          <h3 className="mt-4 text-base font-bold text-slate-800">No learner submissions yet</h3>
          <p className="mt-1 text-sm text-slate-500 max-w-md mx-auto">
            Once civil servants attempt assigned quizzes, their scores and responses will appear here for evaluation.
          </p>
        </div>
      ) : (
        <div className="overflow-hidden rounded-2xl border border-[#f0ddd0] bg-white shadow-sm">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs text-slate-600">
              <thead className="border-b border-slate-100 bg-slate-50/70 text-[11px] font-extrabold uppercase tracking-wider text-slate-400">
                <tr>
                  <th className="px-5 py-3.5">Learner</th>
                  <th className="px-5 py-3.5">Assessment</th>
                  <th className="px-5 py-3.5">Score</th>
                  <th className="px-5 py-3.5">Submitted</th>
                  <th className="px-5 py-3.5">Evaluation Feedback</th>
                  <th className="px-5 py-3.5 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 font-medium">
                {filteredAttempts.map((att, idx) => {
                  const hasFeedback = att.has_trainer_feedback;
                  const scorePct = Math.round(att.percentage || 0);

                  return (
                    <tr key={att.attempt_id || (att as any)._id || idx} className="hover:bg-slate-50/50 transition-colors">
                      <td className="px-5 py-4">
                        <div className="font-bold text-slate-800">{att.learner_name}</div>
                        <div className="text-[11px] text-slate-400">{att.learner_email}</div>
                      </td>

                      <td className="px-5 py-4">
                        <div className="font-bold text-slate-800">{att.quiz_title}</div>
                        <span className="rounded bg-orange-50 px-2 py-0.5 text-[10px] font-bold text-[#c2510e]">
                          {att.competency_code}
                        </span>
                      </td>

                      <td className="px-5 py-4">
                        <div className="flex items-center gap-2">
                          <span className={`text-sm font-black ${
                            scorePct >= 75 ? "text-emerald-700" : scorePct >= 50 ? "text-amber-700" : "text-rose-700"
                          }`}>
                            {scorePct}%
                          </span>
                          <span className="text-[11px] text-slate-400">
                            ({att.correct_count}/{att.total_questions})
                          </span>
                        </div>
                      </td>

                      <td className="px-5 py-4 text-slate-400 whitespace-nowrap">
                        {att.submitted_at ? new Date(att.submitted_at).toLocaleDateString() : "Recent"}
                      </td>

                      <td className="px-5 py-4">
                        {hasFeedback ? (
                          <span className="inline-flex items-center gap-1 rounded-full bg-emerald-100 px-2.5 py-0.5 text-[10px] font-bold text-emerald-800">
                            <CheckCircle2 size={12} /> Feedback Attached
                          </span>
                        ) : (
                          <span className="inline-flex items-center gap-1 rounded-full bg-amber-100 px-2.5 py-0.5 text-[10px] font-bold text-amber-800">
                            <Clock size={12} /> Pending Evaluation
                          </span>
                        )}
                      </td>

                      <td className="px-5 py-4 text-right">
                        <button
                          onClick={() => openFeedbackModal(att)}
                          className="inline-flex items-center gap-1 rounded-xl bg-orange-50 px-3 py-1.5 text-xs font-bold text-[#c2510e] hover:bg-orange-100 transition-colors"
                        >
                          <MessageSquare size={13} /> {hasFeedback ? "Edit Feedback" : "Give Feedback"}
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* ── Qualitative Feedback Modal ── */}
      {feedbackModalOpen && activeAttempt && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4 backdrop-blur-sm animate-fadeIn">
          <div className="relative w-full max-w-xl rounded-3xl bg-white p-6 shadow-2xl border border-[#f0ddd0] max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between border-b border-slate-100 pb-4">
              <div>
                <span className="rounded bg-orange-50 px-2 py-0.5 text-[10px] font-bold text-[#c2510e]">
                  {activeAttempt.competency_code}
                </span>
                <h3 className="text-lg font-extrabold text-slate-800 mt-1">
                  Qualitative Evaluation & Feedback
                </h3>
                <p className="text-xs text-slate-400">
                  Learner: <strong>{activeAttempt.learner_name}</strong> · Score:{" "}
                  <strong>{Math.round(activeAttempt.percentage)}%</strong>
                </p>
              </div>
              <button
                onClick={() => setFeedbackModalOpen(false)}
                className="rounded-full p-1 text-slate-400 hover:bg-slate-100"
              >
                <X size={18} />
              </button>
            </div>

            <form onSubmit={handleSubmitFeedback} className="mt-5 space-y-5">
              {/* Rating Scale */}
              <div className="space-y-1.5">
                <label className="block text-xs font-bold uppercase tracking-wider text-slate-600">
                  Competency Readiness Rating (1 - 5 Stars)
                </label>
                <div className="flex items-center gap-2">
                  {[1, 2, 3, 4, 5].map((starVal) => (
                    <button
                      type="button"
                      key={starVal}
                      onClick={() => setRating(starVal)}
                      className={`p-1.5 rounded-lg transition-transform hover:scale-110 ${
                        rating >= starVal ? "text-amber-500" : "text-slate-200"
                      }`}
                    >
                      <Star size={24} fill={rating >= starVal ? "currentColor" : "none"} />
                    </button>
                  ))}
                  <span className="ml-2 text-xs font-bold text-slate-700">
                    {rating === 5
                      ? "5/5 — Expert Mastery"
                      : rating === 4
                      ? "4/5 — Proficient Capability"
                      : rating === 3
                      ? "3/5 — Working Knowledge"
                      : rating === 2
                      ? "2/5 — Basic Awareness"
                      : "1/5 — Needs Guided Training"}
                  </span>
                </div>
              </div>

              {/* Feedback Remarks */}
              <div className="space-y-1.5">
                <label className="block text-xs font-bold uppercase tracking-wider text-slate-600">
                  Qualitative Evaluation Remarks
                </label>
                <textarea
                  value={feedbackText}
                  onChange={(e) => setFeedbackText(e.target.value)}
                  rows={4}
                  placeholder="Provide personalized mentorship feedback on the civil servant's performance, conceptual strengths, and application of policies..."
                  className="w-full rounded-xl border border-slate-200 p-3 text-xs text-slate-800 focus:border-[#ef7e37] focus:outline-none shadow-sm"
                  required
                />
              </div>

              {/* Strengths Pills */}
              <div className="space-y-2">
                <label className="block text-xs font-bold uppercase tracking-wider text-slate-600">
                  Key Demonstrated Strengths
                </label>
                <div className="flex gap-2">
                  <input
                    type="text"
                    value={strengthsInput}
                    onChange={(e) => setStrengthsInput(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === "Enter") {
                        e.preventDefault();
                        handleAddStrength();
                      }
                    }}
                    placeholder="Type a strength and click Add..."
                    className="flex-1 rounded-xl border border-slate-200 px-3 py-1.5 text-xs text-slate-800 focus:outline-none"
                  />
                  <button
                    type="button"
                    onClick={handleAddStrength}
                    className="rounded-xl bg-slate-100 px-3 py-1.5 text-xs font-bold text-slate-700 hover:bg-slate-200"
                  >
                    Add
                  </button>
                </div>
                <div className="flex flex-wrap gap-1.5">
                  {strengths.map((str, idx) => (
                    <span
                      key={idx}
                      className="inline-flex items-center gap-1 rounded-lg bg-emerald-50 px-2.5 py-1 text-xs font-semibold text-emerald-800 border border-emerald-200"
                    >
                      {str}
                      <button
                        type="button"
                        onClick={() => setStrengths(strengths.filter((_, i) => i !== idx))}
                        className="text-emerald-600 hover:text-emerald-900"
                      >
                        <X size={12} />
                      </button>
                    </span>
                  ))}
                </div>
              </div>

              {/* Areas for Improvement Pills */}
              <div className="space-y-2">
                <label className="block text-xs font-bold uppercase tracking-wider text-slate-600">
                  Areas for Improvement
                </label>
                <div className="flex gap-2">
                  <input
                    type="text"
                    value={areasInput}
                    onChange={(e) => setAreasInput(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === "Enter") {
                        e.preventDefault();
                        handleAddArea();
                      }
                    }}
                    placeholder="Type an area and click Add..."
                    className="flex-1 rounded-xl border border-slate-200 px-3 py-1.5 text-xs text-slate-800 focus:outline-none"
                  />
                  <button
                    type="button"
                    onClick={handleAddArea}
                    className="rounded-xl bg-slate-100 px-3 py-1.5 text-xs font-bold text-slate-700 hover:bg-slate-200"
                  >
                    Add
                  </button>
                </div>
                <div className="flex flex-wrap gap-1.5">
                  {areasForImprovement.map((area, idx) => (
                    <span
                      key={idx}
                      className="inline-flex items-center gap-1 rounded-lg bg-amber-50 px-2.5 py-1 text-xs font-semibold text-amber-800 border border-amber-200"
                    >
                      {area}
                      <button
                        type="button"
                        onClick={() =>
                          setAreasForImprovement(areasForImprovement.filter((_, i) => i !== idx))
                        }
                        className="text-amber-600 hover:text-amber-900"
                      >
                        <X size={12} />
                      </button>
                    </span>
                  ))}
                </div>
              </div>

              {/* Modal Actions */}
              <div className="border-t border-slate-100 pt-4 flex items-center justify-end gap-3">
                <button
                  type="button"
                  onClick={() => setFeedbackModalOpen(false)}
                  className="rounded-xl border border-slate-200 px-4 py-2 text-xs font-bold text-slate-600 hover:bg-slate-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submittingFeedback}
                  className="inline-flex items-center gap-2 rounded-xl bg-[#ef7e37] px-6 py-2 text-xs font-bold text-white shadow hover:bg-[#d96a27] disabled:opacity-50 transition-all active:scale-95"
                >
                  {submittingFeedback ? "Submitting..." : "Save Evaluation Feedback"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

export default TrainerLearnerResults;
