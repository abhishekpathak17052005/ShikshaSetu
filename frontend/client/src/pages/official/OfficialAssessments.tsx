import React, { useEffect, useState } from "react";
import {
  ClipboardCheck,
  Award,
  CheckCircle2,
  AlertCircle,
  ArrowRight,
  TrendingUp,
  RotateCcw,
  Sparkles,
  HelpCircle,
} from "lucide-react";
import {
  api,
  AssessmentAttempt,
  AssessmentSubmitResponse,
  CapabilityAssessment,
  CapabilityAssessmentSubmitResponse,
} from "@/lib/api";
import { toast } from "sonner";

interface OfficialAssessmentsProps {
  initialCompetencyCode?: string;
  onNavigate: (page: string) => void;
}

export function OfficialAssessments({
  initialCompetencyCode,
  onNavigate,
}: OfficialAssessmentsProps) {
  const [attempt, setAttempt] = useState<AssessmentAttempt | null>(null);
  const [capabilityAssessment, setCapabilityAssessment] = useState<CapabilityAssessment | null>(null);

  // Response state
  const [ratings, setRatings] = useState<Record<string, number>>({});
  const [answers, setAnswers] = useState<{ question_id: string; selected_answer: string }[]>([]);
  const [busy, setBusy] = useState(false);
  const [submittedResult, setSubmittedResult] = useState<any | null>(null);

  const startBaselineAssessment = async () => {
    try {
      setBusy(true);
      setSubmittedResult(null);
      const res = await api.assessments.start("initial-competency-v1");
      setAttempt(res);
      setCapabilityAssessment(null);
      setRatings({});
      setAnswers([]);
    } catch (err: any) {
      toast.error(err.message || "Failed to start assessment");
    } finally {
      setBusy(false);
    }
  };

  const startTargetedAssessment = async (code: string) => {
    try {
      setBusy(true);
      setSubmittedResult(null);
      const res = await api.capabilityAssessments.create({ competency_code: code });
      setCapabilityAssessment(res);
      setAttempt(null);
      setRatings({});
      setAnswers([]);
    } catch (err: any) {
      toast.error(err.message || "Failed to create capability assessment");
    } finally {
      setBusy(false);
    }
  };

  useEffect(() => {
    if (initialCompetencyCode) {
      startTargetedAssessment(initialCompetencyCode);
    }
  }, [initialCompetencyCode]);

  // Submit Baseline Assessment
  const handleSubmitBaseline = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!attempt) return;

    try {
      setBusy(true);
      const res = await api.assessments.submit(attempt.id, {
        self_ratings: ratings,
        answers: answers.map((a) => ({ question_id: a.question_id, answer: a.selected_answer })),
        training_evidence: [],
      });
      setSubmittedResult(res);
      setAttempt(null);
      toast.success("Assessment submitted! Authoritative evidence recorded and competency profile updated.");
    } catch (err: any) {
      toast.error(err.message || "Failed to submit assessment");
    } finally {
      setBusy(false);
    }
  };

  // Submit Capability Assessment
  const handleSubmitCapability = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!capabilityAssessment) return;

    try {
      setBusy(true);
      const res = await api.capabilityAssessments.submit(capabilityAssessment.id, {
        answers,
      });
      setSubmittedResult(res);
      setCapabilityAssessment(null);
      toast.success("Capability assessment verified! Competency level updated.");
    } catch (err: any) {
      toast.error(err.message || "Failed to submit capability assessment");
    } finally {
      setBusy(false);
    }
  };

  const currentQuestions = attempt?.questions || capabilityAssessment?.questions || [];
  const answeredCount = currentQuestions.filter((q) => {
    if (q.question_type === "SELF_RATING") {
      return ratings[q.competency_id || q.question_id] != null;
    }
    return answers.some((a) => a.question_id === q.question_id);
  }).length;

  const progressPct =
    currentQuestions.length > 0 ? Math.round((answeredCount / currentQuestions.length) * 100) : 0;

  return (
    <div className="space-y-6 animate-fadeIn max-w-4xl mx-auto">
      {/* Top Banner */}
      <div className="rounded-3xl border border-[#dfe7f0] bg-white p-6 sm:p-8 shadow-sm">
        <div className="flex items-center gap-3 text-teal-800">
          <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-teal-50 text-teal-700">
            <ClipboardCheck size={22} />
          </div>
          <div>
            <h1 className="text-2xl font-black text-[#123057]">
              Formal Capability Assessments
            </h1>
            <p className="text-xs text-slate-400 mt-0.5">
              Authoritative competency evaluation and validated evidence generation
            </p>
          </div>
        </div>

        {/* Start Assessment Prompt */}
        {!attempt && !capabilityAssessment && !submittedResult && (
          <div className="mt-8 space-y-6">
            <div className="rounded-2xl border border-teal-100 bg-teal-50/40 p-6 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
              <div>
                <span className="rounded-full bg-teal-100 px-3 py-0.5 text-[10px] font-bold text-teal-900 uppercase tracking-wider">
                  Baseline Evaluation
                </span>
                <h3 className="text-lg font-bold text-[#123057] mt-2">
                  Comprehensive Role Capability Baseline
                </h3>
                <p className="text-xs text-slate-600 mt-1 max-w-lg">
                  Establishes your initial competency benchmarks across statistical sampling, data analysis, and civil governance domains.
                </p>
              </div>
              <button
                onClick={startBaselineAssessment}
                disabled={busy}
                className="inline-flex items-center justify-center gap-2 rounded-xl bg-[#ef7e37] px-5 py-3 text-xs font-bold text-white shadow hover:bg-[#d96a27] transition-all transform active:scale-95 whitespace-nowrap"
              >
                <ClipboardCheck size={16} /> Start Full Assessment
              </button>
            </div>

            <div className="grid gap-4 sm:grid-cols-2 pt-2">
              {[
                { code: "STAT_SAMPLING", name: "Statistical Sampling Assessment" },
                { code: "TECH_PYTHON", name: "Python Data Analysis Assessment" },
                { code: "DATA_ANALYSIS", name: "Visual Analytics Assessment" },
                { code: "CIVIL_GOV", name: "Civil Governance Verification" },
              ].map((item) => (
                <div
                  key={item.code}
                  className="rounded-2xl border border-slate-100 bg-slate-50/50 p-5 flex flex-col justify-between hover:border-teal-200 transition-colors"
                >
                  <div>
                    <span className="text-[10px] font-bold text-teal-800 uppercase tracking-wider">
                      {item.code}
                    </span>
                    <h4 className="text-sm font-bold text-[#123057] mt-1">{item.name}</h4>
                    <p className="text-xs text-slate-400 mt-1">
                      Authoritative evaluation yielding 0.85+ confidence competency evidence.
                    </p>
                  </div>
                  <button
                    onClick={() => startTargetedAssessment(item.code)}
                    className="mt-4 inline-flex items-center gap-1 text-xs font-bold text-teal-700 hover:underline"
                  >
                    Launch Assessment <ArrowRight size={12} />
                  </button>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Live Assessment Form */}
      {(attempt || capabilityAssessment) && (
        <div className="space-y-6 animate-fadeIn">
          {/* Progress Tracker Strip */}
          <div className="rounded-2xl border border-[#dfe7f0] bg-white p-5 shadow-sm space-y-2">
            <div className="flex items-center justify-between text-xs">
              <span className="font-bold text-[#123057]">
                Assessment in Progress: {capabilityAssessment?.title || "National Capability Evaluation"}
              </span>
              <span className="text-slate-400">
                {answeredCount} of {currentQuestions.length} answered ({progressPct}%)
              </span>
            </div>
            <div className="h-2 w-full overflow-hidden rounded-full bg-slate-100">
              <div
                className="h-full rounded-full bg-[#087f76] transition-all duration-500"
                style={{ width: `${progressPct}%` }}
              />
            </div>
          </div>

          <form onSubmit={attempt ? handleSubmitBaseline : handleSubmitCapability} className="space-y-4">
            {currentQuestions.map((q: any, idx: number) => {
              const qid = q.question_id || q.id;
              const isSelfRating = q.question_type === "SELF_RATING";

              return (
                <div
                  key={qid || idx}
                  className="rounded-2xl border border-[#dfe7f0] bg-white p-6 shadow-sm space-y-4"
                >
                  <div className="flex items-center justify-between">
                    <span className="rounded-md bg-teal-50 px-2 py-0.5 text-[10px] font-extrabold uppercase tracking-wider text-teal-800">
                      {isSelfRating ? "Self-Evaluation" : "Domain Knowledge Check"}
                    </span>
                    <span className="text-xs font-bold text-slate-400">
                      Question #{idx + 1} of {currentQuestions.length}
                    </span>
                  </div>

                  <h3 className="text-base font-bold text-[#123057] leading-snug">
                    {q.scenario_context || q.question_text || q.question}
                  </h3>

                  {/* Options Renderer */}
                  {isSelfRating ? (
                    <div className="pt-2">
                      <div className="text-xs font-semibold text-slate-400 mb-2">
                        Rate your current operational readiness (1 = Basic Awareness, 5 = Expert Mastery):
                      </div>
                      <div className="flex flex-wrap gap-2">
                        {[1, 2, 3, 4, 5].map((val) => (
                          <button
                            type="button"
                            key={val}
                            onClick={() =>
                              setRatings((prev) => ({
                                ...prev,
                                [q.competency_id || qid]: val,
                              }))
                            }
                            className={`rounded-xl border px-5 py-2.5 text-xs font-black transition-all ${
                              ratings[q.competency_id || qid] === val
                                ? "border-[#087f76] bg-teal-50 text-teal-900 shadow-sm"
                                : "border-slate-200 bg-white text-slate-600 hover:bg-slate-50"
                            }`}
                          >
                            Level {val}
                          </button>
                        ))}
                      </div>
                    </div>
                  ) : (
                    <div className="space-y-2 pt-2">
                      {q.options &&
                        q.options.map((opt: string, optIdx: number) => {
                          const letter = String.fromCharCode(65 + optIdx);
                          const isSelected = answers.find((a) => a.question_id === qid)?.selected_answer === letter;

                          return (
                            <label
                              key={optIdx}
                              className={`flex items-center gap-3 rounded-xl border p-3 cursor-pointer text-xs transition-all ${
                                isSelected
                                  ? "border-teal-400 bg-teal-50/50 font-bold text-[#123057]"
                                  : "border-slate-200 bg-slate-50/50 hover:bg-slate-50 text-slate-700"
                              }`}
                            >
                              <input
                                type="radio"
                                name={qid}
                                checked={isSelected}
                                onChange={() => {
                                  setAnswers((prev) => [
                                    ...prev.filter((a) => a.question_id !== qid),
                                    { question_id: qid, selected_answer: letter },
                                  ]);
                                }}
                                className="accent-[#087f76]"
                              />
                              <span className="flex h-5 w-5 shrink-0 items-center justify-center rounded-lg bg-slate-200 text-[10px] font-black text-slate-700">
                                {letter}
                              </span>
                              <span>{opt}</span>
                            </label>
                          );
                        })}
                    </div>
                  )}
                </div>
              );
            })}

            {/* Form Submit Bar */}
            <div className="rounded-2xl bg-white p-5 border border-[#dfe7f0] flex items-center justify-between shadow-sm">
              <button
                type="button"
                onClick={() => {
                  setAttempt(null);
                  setCapabilityAssessment(null);
                }}
                className="rounded-xl border border-slate-200 px-4 py-2 text-xs font-bold text-slate-600 hover:bg-slate-50"
              >
                Cancel Assessment
              </button>

              <button
                type="submit"
                disabled={busy || answeredCount !== currentQuestions.length}
                className="inline-flex items-center gap-2 rounded-xl bg-[#ef7e37] px-6 py-2.5 text-xs font-bold text-white shadow hover:bg-[#d96a27] disabled:opacity-50 transition-all active:scale-95"
              >
                {busy ? "Submitting & Scoring..." : "Submit Assessment & Update Profile"}
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Submitted Results View */}
      {submittedResult && (
        <div className="rounded-3xl border border-emerald-200 bg-white p-6 sm:p-8 shadow-sm space-y-6 animate-fadeIn">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-emerald-100 pb-5">
            <div>
              <div className="inline-flex items-center gap-1.5 rounded-full bg-emerald-100 px-3 py-1 text-xs font-bold text-emerald-900">
                <CheckCircle2 size={14} /> Authoritative Assessment Verified
              </div>
              <h2 className="text-2xl font-black text-[#123057] mt-2">
                Competency Profile Successfully Updated
              </h2>
              <p className="text-xs text-slate-500 mt-0.5">
                Official evidence recorded with 0.85+ confidence. Skill gaps recalculated.
              </p>
            </div>

            <div className="rounded-2xl border border-emerald-200 bg-emerald-50/50 p-4 text-center">
              <div className="text-xs font-bold text-emerald-800 uppercase tracking-wider">
                Overall Score
              </div>
              <div className="text-3xl font-black text-[#123057] mt-1">
                {submittedResult.normalized_score != null
                  ? `${submittedResult.normalized_score.toFixed(1)} / 5.0`
                  : `${Math.round(submittedResult.percentage || 0)}%`}
              </div>
            </div>
          </div>

          {/* Competency Impact Cards */}
          <div className="grid gap-3 sm:grid-cols-2">
            {(submittedResult.competency_results || []).map((res: any, idx: number) => (
              <div
                key={idx}
                className="rounded-xl border border-slate-100 bg-[#f8fafc] p-4 flex items-center justify-between"
              >
                <div>
                  <span className="text-[10px] font-bold uppercase tracking-wider text-teal-800">
                    {res.competency_code || `Competency #${idx + 1}`}
                  </span>
                  <div className="text-base font-bold text-[#123057] mt-0.5">
                    Level {res.score?.toFixed(1) || res.level?.toFixed(1) || "4.0"} / 5.0
                  </div>
                </div>
                <span className="text-xs font-semibold text-slate-400">
                  {Math.round((res.confidence || 0.85) * 100)}% confidence
                </span>
              </div>
            ))}
          </div>

          {/* Action Hub */}
          <div className="flex flex-wrap items-center gap-3 pt-4 border-t border-slate-100">
            <button
              onClick={() => onNavigate("Skill Gaps")}
              className="inline-flex items-center gap-2 rounded-xl bg-[#ef7e37] px-5 py-2.5 text-xs font-bold text-white shadow hover:bg-[#d96a27] transition-all"
            >
              View Updated Skill Gaps <ArrowRight size={14} />
            </button>
            <button
              onClick={() => onNavigate("Recommendations")}
              className="inline-flex items-center gap-2 rounded-xl border border-slate-200 px-5 py-2.5 text-xs font-bold text-slate-700 hover:bg-slate-50 transition-colors"
            >
              View Targeted Recommendations
            </button>
            <button
              onClick={() => setSubmittedResult(null)}
              className="inline-flex items-center gap-1 text-xs font-bold text-slate-400 hover:text-slate-600 ml-auto"
            >
              <RotateCcw size={13} /> Retake / New Assessment
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

export default OfficialAssessments;
