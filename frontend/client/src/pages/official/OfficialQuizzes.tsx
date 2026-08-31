import React, { useEffect, useState } from "react";
import {
  Award,
  CheckCircle2,
  Clock,
  Play,
  ArrowRight,
  AlertCircle,
  HelpCircle,
  RefreshCw,
  TrendingUp,
  XCircle,
  RotateCcw,
} from "lucide-react";
import {
  api,
  AssignedQuiz,
  TrainerQuiz,
  QuizAttemptResult,
} from "@/lib/api";
import { toast } from "sonner";

interface OfficialQuizzesProps {
  onNavigate: (page: string, context?: { competencyCode?: string }) => void;
}

export function OfficialQuizzes({ onNavigate }: OfficialQuizzesProps) {
  const [assignedQuizzes, setAssignedQuizzes] = useState<AssignedQuiz[]>([]);
  const [loading, setLoading] = useState(true);

  // Active Quiz State
  const [activeQuiz, setActiveQuiz] = useState<TrainerQuiz | null>(null);
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [submitting, setSubmitting] = useState(false);
  const [quizResult, setQuizResult] = useState<QuizAttemptResult | null>(null);

  const fetchAssignedQuizzes = async () => {
    try {
      setLoading(true);
      const list = await api.quizzes.assigned();
      setAssignedQuizzes(list);
    } catch (err: any) {
      toast.error(err.message || "Failed to load assigned quizzes");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAssignedQuizzes();
  }, []);

  const startQuizSession = async (quizId: string) => {
    try {
      setLoading(true);
      setQuizResult(null);
      const fullQuiz = await api.quizzes.get(quizId);
      setActiveQuiz(fullQuiz);
      setAnswers({});
    } catch (err: any) {
      toast.error(err.message || "Failed to load quiz questions");
    } finally {
      setLoading(false);
    }
  };

  const handleSubmitQuiz = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!activeQuiz) return;
    const qid = activeQuiz.id || activeQuiz.quiz_id || (activeQuiz as any)._id;

    const answerPayload = (activeQuiz.questions || []).map((q, idx) => ({
      question_id: q.id || q.question_id || (q as any)._id || `${qid}-${idx + 1}`,
      selected_answer: answers[q.id || q.question_id || (q as any)._id || `${qid}-${idx + 1}`] || "A",
    }));

    try {
      setSubmitting(true);
      const result = await api.quizzes.submit(qid, answerPayload);
      setQuizResult(result);
      setActiveQuiz(null);
      toast.success("Quiz completed! Supporting evidence recorded.");
      fetchAssignedQuizzes();
    } catch (err: any) {
      toast.error(err.message || "Failed to submit quiz");
    } finally {
      setSubmitting(false);
    }
  };

  const answeredCount = Object.keys(answers).length;
  const totalQuestions = activeQuiz?.questions?.length || 0;

  return (
    <div className="space-y-6 animate-fadeIn max-w-4xl mx-auto">
      {/* Top Header */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-black text-[#123057]">Assigned Quizzes</h1>
          <p className="text-sm text-slate-500 mt-1">
            Course practice quizzes assigned by curriculum trainers to test domain knowledge.
          </p>
        </div>

        <button
          onClick={fetchAssignedQuizzes}
          className="flex items-center gap-1.5 rounded-xl border border-[#dfe7f0] bg-white px-3.5 py-2 text-xs font-bold text-slate-600 hover:bg-slate-50 transition-colors"
        >
          <RefreshCw size={14} className={loading ? "animate-spin" : ""} />
          Refresh Quizzes
        </button>
      </div>

      {/* ── Active Quiz Session ── */}
      {activeQuiz && (
        <div className="space-y-6 animate-fadeIn">
          <div className="rounded-3xl border border-teal-200 bg-white p-6 sm:p-8 shadow-sm space-y-6">
            <div className="flex items-center justify-between border-b border-slate-100 pb-4">
              <div>
                <span className="rounded-md bg-teal-50 px-2.5 py-0.5 text-[10px] font-extrabold uppercase text-teal-800">
                  {activeQuiz.competency_code}
                </span>
                <h2 className="text-xl font-bold text-[#123057] mt-1">
                  {activeQuiz.title}
                </h2>
              </div>

              <span className="text-xs font-bold text-slate-400">
                {answeredCount} of {totalQuestions} answered
              </span>
            </div>

            <form onSubmit={handleSubmitQuiz} className="space-y-5">
              {(activeQuiz.questions || []).map((q, idx) => {
                const qid = q.id || q.question_id || (q as any)._id || `${activeQuiz.id}-${idx + 1}`;

                return (
                  <div
                    key={qid}
                    className="rounded-2xl border border-slate-200 bg-slate-50/50 p-5 space-y-3"
                  >
                    <div className="flex items-center justify-between text-xs font-bold text-slate-400">
                      <span>Question #{idx + 1} of {totalQuestions}</span>
                    </div>

                    <h3 className="text-sm font-bold text-[#123057]">{q.question}</h3>

                    <div className="space-y-2 pt-1">
                      {q.options &&
                        q.options.map((opt, optIdx) => {
                          const letter = String.fromCharCode(65 + optIdx);
                          const isSelected = answers[qid] === letter;

                          return (
                            <label
                              key={optIdx}
                              className={`flex items-center gap-3 rounded-xl border p-3 cursor-pointer text-xs transition-all ${
                                isSelected
                                  ? "border-teal-400 bg-teal-50/70 font-bold text-[#123057]"
                                  : "border-slate-200 bg-white hover:bg-slate-50 text-slate-700"
                              }`}
                            >
                              <input
                                type="radio"
                                name={qid}
                                checked={isSelected}
                                onChange={() => setAnswers({ ...answers, [qid]: letter })}
                                className="accent-[#087f76]"
                              />
                              <span className="flex h-5 w-5 shrink-0 items-center justify-center rounded-lg bg-slate-100 text-[10px] font-black text-slate-700">
                                {letter}
                              </span>
                              <span>{opt}</span>
                            </label>
                          );
                        })}
                    </div>
                  </div>
                );
              })}

              <div className="flex items-center justify-between border-t border-slate-100 pt-5">
                <button
                  type="button"
                  onClick={() => setActiveQuiz(null)}
                  className="rounded-xl border border-slate-200 px-4 py-2 text-xs font-bold text-slate-600"
                >
                  Exit Quiz
                </button>

                <button
                  type="submit"
                  disabled={submitting || answeredCount !== totalQuestions}
                  className="inline-flex items-center gap-2 rounded-xl bg-[#ef7e37] px-6 py-2.5 text-xs font-bold text-white shadow hover:bg-[#d96a27] disabled:opacity-50 transition-all active:scale-95"
                >
                  {submitting ? "Scoring Quiz..." : "Submit Quiz"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* ── Quiz Result View ── */}
      {quizResult && (
        <div className="rounded-3xl border border-teal-200 bg-white p-6 sm:p-8 shadow-sm space-y-6 animate-fadeIn">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-slate-100 pb-5">
            <div>
              <div className="inline-flex items-center gap-1.5 rounded-full bg-emerald-100 px-3 py-1 text-xs font-bold text-emerald-900">
                <CheckCircle2 size={14} /> Practice Quiz Completed
              </div>
              <h2 className="text-2xl font-black text-[#123057] mt-2">
                Quiz Evaluation Results
              </h2>
              <p className="text-xs text-slate-500 mt-0.5">
                Score: {quizResult.score} / {quizResult.total_questions} ({Math.round(quizResult.percentage)}%) · Supporting evidence logged.
              </p>
            </div>

            <div className="rounded-2xl border border-teal-200 bg-teal-50/50 p-4 text-center">
              <div className="text-xs font-bold text-teal-800 uppercase tracking-wider">
                Accuracy
              </div>
              <div className="text-3xl font-black text-[#123057] mt-1">
                {Math.round(quizResult.percentage)}%
              </div>
            </div>
          </div>

          {/* Feedback & Questions Breakdown */}
          <div className="space-y-4">
            <h3 className="text-sm font-extrabold text-[#123057]">
              Detailed Question Analysis & Explanations
            </h3>

            {(quizResult.questions_with_feedback || []).map((qf, idx) => (
              <div
                key={idx}
                className={`rounded-2xl border p-4 text-xs space-y-2 ${
                  qf.is_correct
                    ? "border-emerald-200 bg-emerald-50/30"
                    : "border-rose-200 bg-rose-50/30"
                }`}
              >
                <div className="flex items-center justify-between">
                  <span className="font-bold text-slate-600">Question #{idx + 1}</span>
                  {qf.is_correct ? (
                    <span className="inline-flex items-center gap-1 font-bold text-emerald-700">
                      <CheckCircle2 size={13} /> Correct (+1)
                    </span>
                  ) : (
                    <span className="inline-flex items-center gap-1 font-bold text-rose-700">
                      <XCircle size={13} /> Incorrect (Key: Option {qf.correct_answer})
                    </span>
                  )}
                </div>

                <p className="font-bold text-[#123057]">{qf.question}</p>

                <div className="text-slate-600 bg-white/70 p-2.5 rounded-lg border border-slate-200/50">
                  <strong>Explanation:</strong> {qf.explanation}
                </div>
              </div>
            ))}
          </div>

          {/* Core Principle Notice */}
          <div className="rounded-2xl bg-teal-50/60 border border-teal-100 p-4 text-xs text-teal-900 leading-relaxed">
            <strong>Supporting Evidence Recorded:</strong> Completing this practice quiz proves engagement and knowledge recall. To formally increase your official competency rating, please take a standardized <strong>Capability Assessment</strong>.
          </div>

          <div className="flex flex-wrap items-center gap-3 pt-4 border-t border-slate-100">
            <button
              onClick={() => onNavigate("Assessments")}
              className="inline-flex items-center gap-2 rounded-xl bg-[#087f76] px-5 py-2.5 text-xs font-bold text-white shadow hover:bg-[#06655e]"
            >
              Take Capability Assessment <ArrowRight size={13} />
            </button>
            <button
              onClick={() => setQuizResult(null)}
              className="rounded-xl border border-slate-200 px-4 py-2.5 text-xs font-bold text-slate-700 hover:bg-slate-50"
            >
              Back to Assigned Quizzes
            </button>
          </div>
        </div>
      )}

      {/* ── Assigned Quizzes List ── */}
      {!activeQuiz && !quizResult && (
        <div className="space-y-4">
          {loading ? (
            <div className="space-y-3">
              {[1, 2, 3].map((n) => (
                <div key={n} className="h-28 rounded-2xl bg-white animate-pulse border border-slate-200" />
              ))}
            </div>
          ) : assignedQuizzes.length === 0 ? (
            <div className="rounded-2xl border border-dashed border-[#dfe7f0] bg-white p-12 text-center">
              <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-teal-50 text-teal-700">
                <Award size={24} />
              </div>
              <h3 className="mt-4 text-base font-bold text-[#123057]">
                No quizzes currently assigned
              </h3>
              <p className="mt-1 text-sm text-slate-500 max-w-md mx-auto">
                When trainers assign tailored quizzes to your cohort, they will appear here.
              </p>
            </div>
          ) : (
            <div className="grid gap-4 sm:grid-cols-2">
              {assignedQuizzes.map((q) => {
                const isCompleted = q.status === "COMPLETED";

                return (
                  <div
                    key={q.quiz_id}
                    className="flex flex-col justify-between rounded-2xl border border-[#dfe7f0] bg-white p-6 shadow-sm hover:border-teal-300 hover:shadow-md transition-all group"
                  >
                    <div>
                      <div className="flex items-center justify-between">
                        <span className="rounded bg-teal-50 px-2 py-0.5 text-[10px] font-extrabold text-teal-800">
                          {q.question_count} Questions
                        </span>

                        {isCompleted ? (
                          <span className="rounded-full bg-emerald-100 px-2.5 py-0.5 text-[10px] font-bold text-emerald-800">
                            Completed
                          </span>
                        ) : (
                          <span className="rounded-full bg-amber-100 px-2.5 py-0.5 text-[10px] font-bold text-amber-800">
                            Assigned
                          </span>
                        )}
                      </div>

                      <h3 className="text-base font-bold text-[#123057] mt-3 group-hover:text-teal-800 transition-colors">
                        {q.title}
                      </h3>

                      {q.description && (
                        <p className="text-xs text-slate-500 mt-1 line-clamp-2">
                          {q.description}
                        </p>
                      )}

                      <div className="mt-4 text-[11px] text-slate-400">
                        Assigned by Trainer {q.trainer_name || "Staff"} · {q.assigned_at ? new Date(q.assigned_at).toLocaleDateString() : "Recent"}
                      </div>
                    </div>

                    <div className="mt-5 border-t border-slate-100 pt-4">
                      <button
                        onClick={() => startQuizSession(q.quiz_id)}
                        className="w-full inline-flex items-center justify-center gap-2 rounded-xl bg-[#ef7e37] py-2 text-xs font-bold text-white shadow hover:bg-[#d96a27] transition-all active:scale-95"
                      >
                        <Play size={12} /> {isCompleted ? "Retake Practice Quiz" : "Attempt Quiz"}
                      </button>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default OfficialQuizzes;
