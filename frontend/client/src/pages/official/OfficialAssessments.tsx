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
  Layers,
  Zap,
  Activity,
  Check,
  X as XIcon,
} from "lucide-react";
import {
  api,
  AssessmentAttempt,
  CapabilityAssessment,
  AdaptiveStartResponse,
  AdaptiveQuestionItem,
  AdaptiveFinalizeResponse,
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
  // Legacy / Baseline assessment state
  const [attempt, setAttempt] = useState<AssessmentAttempt | null>(null);
  const [capabilityAssessment, setCapabilityAssessment] = useState<CapabilityAssessment | null>(null);
  const [ratings, setRatings] = useState<Record<string, number>>({});
  const [answers, setAnswers] = useState<{ question_id: string; selected_answer: string }[]>([]);
  const [submittedResult, setSubmittedResult] = useState<any | null>(null);

  // ─── Phase 3C: Dynamic Adaptive Assessment State ───────────────────────────
  const [userCompetencies, setUserCompetencies] = useState<any[]>([]);
  const [adaptiveSession, setAdaptiveSession] = useState<AdaptiveStartResponse | null>(null);
  const [adaptiveCurrentQuestion, setAdaptiveCurrentQuestion] = useState<AdaptiveQuestionItem | null>(null);
  const [adaptiveCurrentNumber, setAdaptiveCurrentNumber] = useState(1);
  const [adaptiveTheta, setAdaptiveTheta] = useState(2.5);
  const [adaptiveDifficulty, setAdaptiveDifficulty] = useState("MEDIUM");
  const [selectedOption, setSelectedOption] = useState<string>("");
  const [adaptiveFeedback, setAdaptiveFeedback] = useState<{ isCorrect: boolean; explanation?: string | null } | null>(null);
  const [adaptiveFinalResult, setAdaptiveFinalResult] = useState<AdaptiveFinalizeResponse | null>(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    async function loadApplicableCompetencies() {
      try {
        const comps = await api.competencies.me();
        setUserCompetencies(comps || []);
      } catch {
        setUserCompetencies([]);
      }
    }
    loadApplicableCompetencies();
  }, []);

  // Start Adaptive Assessment
  const startAdaptiveAssessment = async (code: string) => {
    try {
      setBusy(true);
      setSubmittedResult(null);
      setAdaptiveFinalResult(null);
      setAttempt(null);
      setCapabilityAssessment(null);
      setSelectedOption("");
      setAdaptiveFeedback(null);

      const res = await api.adaptiveAssessments.start(code, 5);
      setAdaptiveSession(res);
      setAdaptiveCurrentQuestion(res.question || null);
      setAdaptiveCurrentNumber(1);
      setAdaptiveTheta(res.estimated_level);
      setAdaptiveDifficulty(res.difficulty);
      toast.success(`Adaptive assessment initialized for ${res.competency_name}`);
    } catch (err: any) {
      toast.error(err.message || "Failed to start adaptive assessment");
    } finally {
      setBusy(false);
    }
  };

  useEffect(() => {
    if (initialCompetencyCode) {
      startAdaptiveAssessment(initialCompetencyCode);
    }
  }, [initialCompetencyCode]);


  // Submit single adaptive answer
  const handleAdaptiveAnswerSubmit = async () => {
    if (!adaptiveSession || !adaptiveCurrentQuestion || !selectedOption || busy) return;

    try {
      setBusy(true);
      const res = await api.adaptiveAssessments.answer(
        adaptiveSession.session_id,
        adaptiveCurrentQuestion.question_id,
        selectedOption
      );

      setAdaptiveFeedback({
        isCorrect: res.is_correct,
        explanation: res.explanation,
      });

      setAdaptiveTheta(res.updated_estimated_level);
      setAdaptiveDifficulty(res.next_difficulty);

      if (res.is_complete || !res.next_question) {
        // Automatically finalize session
        const finalRes = await api.adaptiveAssessments.finalize(adaptiveSession.session_id);
        setAdaptiveFinalResult(finalRes);
        setAdaptiveSession(null);
        setAdaptiveCurrentQuestion(null);
        toast.success("Adaptive assessment finalized! Authoritative evidence recorded (0.85).");
      } else {
        // Move to next question after a brief feedback moment
        setTimeout(() => {
          setAdaptiveCurrentQuestion(res.next_question || null);
          setAdaptiveCurrentNumber((prev) => prev + 1);
          setSelectedOption("");
          setAdaptiveFeedback(null);
        }, 1200);
      }
    } catch (err: any) {
      toast.error(err.message || "Failed to process answer");
    } finally {
      setBusy(false);
    }
  };

  // Start Baseline Assessment
  const startBaselineAssessment = async () => {
    try {
      setBusy(true);
      setSubmittedResult(null);
      setAdaptiveSession(null);
      setAdaptiveFinalResult(null);
      const res = await api.assessments.start("initial-competency-v1");
      setAttempt(res);
      setCapabilityAssessment(null);
      setRatings({});
      setAnswers([]);
    } catch (err: any) {
      toast.error(err.message || "Failed to start baseline assessment");
    } finally {
      setBusy(false);
    }
  };

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
      toast.success("Assessment submitted! Competency profile updated.");
    } catch (err: any) {
      toast.error(err.message || "Failed to submit assessment");
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="space-y-6 animate-fadeIn max-w-4xl mx-auto">
      {/* Top Banner */}
      <div className="rounded-3xl border border-[#dfe7f0] bg-white p-6 sm:p-8 shadow-sm">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div className="flex items-center gap-3 text-teal-800">
            <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-gradient-to-br from-[#123057] to-[#087f76] text-white shadow-md">
              <Activity size={24} />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-2xl font-black text-[#123057]">
                  Adaptive Capability Assessments
                </h1>
                <span className="rounded-md bg-teal-100 px-2 py-0.5 text-[10px] font-extrabold text-teal-800 uppercase tracking-wider">
                  Phase 3C Active
                </span>
              </div>
              <p className="text-xs text-slate-500 mt-0.5">
                Dynamic Item Calibration Engine • Authoritative Evidence Verification (0.85 Confidence)
              </p>
            </div>
          </div>
        </div>

        {/* Start Assessment Prompt */}
        {!attempt && !capabilityAssessment && !adaptiveSession && !submittedResult && !adaptiveFinalResult && (
          <div className="mt-8 space-y-6">
            {/* Primary Hero: Launch Adaptive Assessment */}
            <div className="rounded-2xl border border-teal-200 bg-gradient-to-r from-teal-50/90 via-blue-50/60 to-purple-50/50 p-6 flex flex-col md:flex-row md:items-center md:justify-between gap-6 shadow-sm">
              <div className="space-y-2">
                <div className="inline-flex items-center gap-1.5 rounded-full bg-teal-100 px-3 py-0.5 text-[10px] font-extrabold text-teal-900 uppercase tracking-wider">
                  <Zap size={12} className="text-[#ef7e37]" /> Dynamic Step-Up / Step-Down Engine
                </div>
                <h3 className="text-lg font-black text-[#123057]">
                  Adaptive Competency Validation
                </h3>
                <p className="text-xs text-slate-600 max-w-lg leading-relaxed">
                  Questions dynamically calibrate in real time based on your demonstrated accuracy. 
                  Finalizing records <strong>Authoritative Evidence (0.85)</strong>, directly updating your official competency rating and closing skill gaps.
                </p>
              </div>

              {userCompetencies[0] && (
                <button
                  onClick={() => startAdaptiveAssessment(userCompetencies[0].code)}
                  disabled={busy}
                  className="inline-flex items-center justify-center gap-2 rounded-xl bg-[#ef7e37] px-6 py-3.5 text-xs font-black text-white shadow-md hover:bg-[#d96a27] hover:scale-105 transition-all whitespace-nowrap"
                >
                  <Zap size={15} /> Launch {userCompetencies[0].name.split(" ")[0]} Assessment
                </button>
              )}
            </div>

            {/* Targeted Competency Cards */}
            <div>
              <div className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-3">
                Select Competency for Adaptive Calibration (Mapped to Your Department):
              </div>
              <div className="grid gap-4 sm:grid-cols-2">
                {(userCompetencies.length > 0 ? userCompetencies : [
                  {
                    code: "TECH_PYTHON",
                    name: "Python for Official Data Analytics",
                    domain: "TECHNICAL",
                    description: "Pandas, NumPy, statistical modeling and automation.",
                    required_level: 4.0,
                  },
                ]).map((item: any) => (
                  <div
                    key={item.code}
                    className="rounded-2xl border border-slate-200 bg-white p-5 flex flex-col justify-between hover:border-teal-400 hover:shadow-md transition-all group"
                  >
                    <div>
                      <div className="flex items-center justify-between">
                        <span className="rounded-md bg-slate-100 px-2 py-0.5 text-[10px] font-extrabold text-slate-700 uppercase">
                          {item.domain}
                        </span>
                        <span className="text-[10px] font-bold text-teal-700">
                          {item.code}
                        </span>
                      </div>
                      <h4 className="text-sm font-black text-[#123057] mt-2 group-hover:text-teal-800 transition-colors">
                        {item.name}
                      </h4>
                      <p className="text-xs text-slate-500 mt-1 leading-relaxed line-clamp-2">
                        {item.description || item.desc}
                      </p>
                      <div className="mt-2 text-[11px] font-semibold text-slate-400">
                        Required Level: <strong className="text-slate-700">Level {item.required_level || 4.0}</strong>
                        {item.current_level != null && (
                          <span> · Current: <strong className="text-teal-700">Level {item.current_level.toFixed(1)}</strong></span>
                        )}
                      </div>
                    </div>

                    <button
                      onClick={() => startAdaptiveAssessment(item.code)}
                      className="mt-4 inline-flex items-center gap-1.5 text-xs font-bold text-teal-800 hover:text-teal-900 group-hover:translate-x-1 transition-all"
                    >
                      <span>Start Adaptive Evaluation</span>
                      <ArrowRight size={13} />
                    </button>
                  </div>
                ))}
              </div>
            </div>


            {/* Baseline Full Assessment Prompt */}
            <div className="pt-2 border-t border-slate-100 flex items-center justify-between text-xs text-slate-500">
              <span>Looking for standard baseline assessment?</span>
              <button
                onClick={startBaselineAssessment}
                className="font-bold text-teal-700 hover:underline inline-flex items-center gap-1"
              >
                Launch Role Baseline Survey <ArrowRight size={12} />
              </button>
            </div>
          </div>
        )}
      </div>

      {/* ─── LIVE ADAPTIVE ASSESSMENT STUDIO ──────────────────────────────── */}
      {adaptiveSession && adaptiveCurrentQuestion && (
        <div className="space-y-6 animate-fadeIn">
          {/* Dynamic Capability Meter Card */}
          <div className="rounded-3xl border border-teal-200 bg-white p-6 shadow-sm space-y-4">
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
              <div>
                <span className="text-[10px] font-extrabold uppercase tracking-wider text-teal-800 bg-teal-50 px-2.5 py-1 rounded-md">
                  Adaptive Calibration • {adaptiveSession.competency_name}
                </span>
                <h3 className="text-base font-black text-[#123057] mt-1">
                  Question #{adaptiveCurrentNumber} of {adaptiveSession.total_questions_planned}
                </h3>
              </div>

              <div className="flex items-center gap-3">
                <div className="text-right">
                  <div className="text-[10px] font-bold text-slate-400 uppercase">
                    Target Difficulty
                  </div>
                  <span
                    className={`inline-block rounded-lg px-2.5 py-0.5 text-xs font-black uppercase ${
                      adaptiveDifficulty === "HARD"
                        ? "bg-purple-100 text-purple-900"
                        : adaptiveDifficulty === "MEDIUM"
                        ? "bg-blue-100 text-blue-900"
                        : "bg-emerald-100 text-emerald-900"
                    }`}
                  >
                    {adaptiveDifficulty === "HARD"
                      ? "Advanced (L4-L5)"
                      : adaptiveDifficulty === "MEDIUM"
                      ? "Intermediate (L3)"
                      : "Foundation (L1-L2)"}
                  </span>
                </div>

                <div className="rounded-2xl bg-slate-50 border border-slate-100 p-2.5 text-center min-w-[90px]">
                  <div className="text-[10px] font-bold text-slate-400 uppercase">
                    Demonstrated
                  </div>
                  <div className="text-lg font-black text-[#123057]">
                    L {adaptiveTheta.toFixed(1)}
                  </div>
                </div>
              </div>
            </div>

            {/* 5-Level Progress Bar / Gauge */}
            <div className="space-y-1.5 pt-2">
              <div className="flex justify-between text-[10px] font-bold text-slate-400">
                <span>L1 Awareness</span>
                <span>L2 Working</span>
                <span>L3 Operational</span>
                <span>L4 Specialist</span>
                <span>L5 Authority</span>
              </div>
              <div className="relative h-3 w-full overflow-hidden rounded-full bg-slate-100">
                <div
                  className="h-full rounded-full bg-gradient-to-r from-emerald-400 via-teal-500 to-purple-600 transition-all duration-700"
                  style={{ width: `${Math.min(100, Math.max(10, ((adaptiveTheta - 1.0) / 4.0) * 100))}%` }}
                />
              </div>
              <p className="text-[11px] text-slate-400 text-center italic">
                Your assessment dynamically adapts difficulty based on your sequential answer performance.
              </p>
            </div>
          </div>

          {/* Active Question Card */}
          <div className="rounded-3xl border border-[#dfe7f0] bg-white p-6 sm:p-8 shadow-sm space-y-6">
            <div className="space-y-2">
              {adaptiveCurrentQuestion.scenario_context && (
                <div className="rounded-xl bg-slate-50 p-4 border border-slate-100 text-xs text-slate-700 leading-relaxed font-medium">
                  <strong>Scenario Context:</strong> {adaptiveCurrentQuestion.scenario_context}
                </div>
              )}

              <h2 className="text-lg sm:text-xl font-bold text-[#123057] leading-snug">
                {adaptiveCurrentQuestion.question_text}
              </h2>
            </div>

            {/* Options */}
            <div className="space-y-3">
              {adaptiveCurrentQuestion.options.map((opt, oIdx) => {
                const optLetter = chrFromIdx(oIdx);
                const isSelected = selectedOption === optLetter || selectedOption === opt;

                return (
                  <button
                    key={oIdx}
                    type="button"
                    onClick={() => !adaptiveFeedback && setSelectedOption(optLetter)}
                    disabled={busy || adaptiveFeedback != null}
                    className={`w-full text-left rounded-2xl p-4 text-xs font-semibold transition-all border flex items-center justify-between ${
                      isSelected
                        ? "bg-teal-50/80 border-teal-500 text-teal-950 shadow-sm"
                        : "bg-white border-slate-200 hover:bg-slate-50 text-slate-800"
                    }`}
                  >
                    <div className="flex items-center gap-3">
                      <span
                        className={`flex h-7 w-7 shrink-0 items-center justify-center rounded-xl font-black text-xs ${
                          isSelected
                            ? "bg-teal-600 text-white"
                            : "bg-slate-100 text-slate-600"
                        }`}
                      >
                        {optLetter}
                      </span>
                      <span>{opt}</span>
                    </div>

                    {isSelected && (
                      <CheckCircle2 size={16} className="text-teal-600 shrink-0" />
                    )}
                  </button>
                );
              })}
            </div>

            {/* Answer Feedback Alert */}
            {adaptiveFeedback && (
              <div
                className={`rounded-2xl p-4 text-xs border flex items-start gap-3 animate-fadeIn ${
                  adaptiveFeedback.isCorrect
                    ? "bg-emerald-50 border-emerald-200 text-emerald-900"
                    : "bg-amber-50 border-amber-200 text-amber-900"
                }`}
              >
                {adaptiveFeedback.isCorrect ? (
                  <Check size={18} className="text-emerald-600 shrink-0 mt-0.5" />
                ) : (
                  <XIcon size={18} className="text-amber-600 shrink-0 mt-0.5" />
                )}
                <div>
                  <strong className="font-bold">
                    {adaptiveFeedback.isCorrect
                      ? "Correct! Demonstrated capability stepped upward."
                      : "Incorrect. Calibrating foundation level..."}
                  </strong>
                  {adaptiveFeedback.explanation && (
                    <p className="mt-1 text-slate-600 leading-relaxed">
                      {adaptiveFeedback.explanation}
                    </p>
                  )}
                </div>
              </div>
            )}

            {/* Submit Action */}
            <div className="pt-4 border-t border-slate-100 flex items-center justify-between">
              <span className="text-[11px] text-slate-400">
                Authoritative item evaluation • Zero AI hallucination
              </span>

              <button
                type="button"
                onClick={handleAdaptiveAnswerSubmit}
                disabled={!selectedOption || busy || adaptiveFeedback != null}
                className="inline-flex items-center gap-2 rounded-xl bg-[#123057] px-6 py-3 text-xs font-bold text-white shadow hover:bg-[#087f76] transition-all disabled:opacity-40"
              >
                {busy ? "Calibrating..." : "Submit Answer & Calibrate"} <ArrowRight size={13} />
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ─── PHASE 3C COMPLETION SCREEN ───────────────────────────────────── */}
      {adaptiveFinalResult && (
        <div className="rounded-3xl border border-emerald-200 bg-white p-6 sm:p-8 shadow-sm space-y-6 animate-fadeIn">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-slate-100 pb-6">
            <div>
              <div className="inline-flex items-center gap-1.5 rounded-full bg-emerald-100 px-3 py-1 text-xs font-bold text-emerald-900">
                <CheckCircle2 size={14} /> Adaptive Capability Assessment Complete
              </div>
              <h2 className="text-2xl font-black text-[#123057] mt-2">
                Official Competency Validated
              </h2>
              <p className="text-xs text-slate-500 mt-0.5">
                Target Competency: <strong>{adaptiveFinalResult.competency_name}</strong> ({adaptiveFinalResult.competency_code})
              </p>
            </div>

            <div className="rounded-2xl border border-emerald-200 bg-emerald-50/60 p-4 text-center min-w-[140px]">
              <div className="text-[10px] font-bold text-emerald-800 uppercase tracking-wider">
                Validated Level
              </div>
              <div className="text-3xl font-black text-[#123057] mt-1">
                L {adaptiveFinalResult.final_demonstrated_level.toFixed(1)}
              </div>
              <div className="text-[10px] text-emerald-700 font-semibold mt-0.5">
                Scale 1.0 – 5.0
              </div>
            </div>
          </div>

          {/* Core Results Grid */}
          <div className="grid gap-4 sm:grid-cols-3">
            <div className="rounded-2xl bg-slate-50 p-4 border border-slate-100 space-y-1">
              <div className="text-[10px] font-bold uppercase text-slate-400">
                Competency Rating
              </div>
              <div className="text-lg font-black text-[#123057]">
                Level {adaptiveFinalResult.previous_competency_level.toFixed(1)} ➔{" "}
                <span className="text-emerald-700">
                  {adaptiveFinalResult.updated_competency_level.toFixed(1)}
                </span>
              </div>
              <p className="text-[11px] text-slate-500">
                {adaptiveFinalResult.proficiency_tier}
              </p>
            </div>

            <div className="rounded-2xl bg-slate-50 p-4 border border-slate-100 space-y-1">
              <div className="text-[10px] font-bold uppercase text-slate-400">
                Skill Gap Impact
              </div>
              <div className="text-lg font-black text-[#123057]">
                {adaptiveFinalResult.previous_skill_gap.toFixed(1)} ➔{" "}
                <span className="text-teal-700 font-black">
                  {adaptiveFinalResult.updated_skill_gap.toFixed(1)} Deficit
                </span>
              </div>
              <p className="text-[11px] text-slate-500">
                Recalculated against role baseline
              </p>
            </div>

            <div className="rounded-2xl bg-slate-50 p-4 border border-slate-100 space-y-1">
              <div className="text-[10px] font-bold uppercase text-slate-400">
                Evidence Confidence
              </div>
              <div className="text-lg font-black text-purple-900">
                85% (Authoritative)
              </div>
              <p className="text-[11px] text-slate-500 truncate" title={adaptiveFinalResult.evidence_record_id}>
                ID: {adaptiveFinalResult.evidence_record_id.slice(-8)}
              </p>
            </div>
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
              Browse Updated Recommendations
            </button>
            <button
              onClick={() => setAdaptiveFinalResult(null)}
              className="inline-flex items-center gap-1 text-xs font-bold text-slate-400 hover:text-slate-600 ml-auto"
            >
              <RotateCcw size={13} /> Assess Another Competency
            </button>
          </div>
        </div>
      )}

      {/* Legacy Baseline Form Support */}
      {attempt && (
        <div className="space-y-6 animate-fadeIn">
          <form onSubmit={handleSubmitBaseline} className="space-y-4">
            {(attempt.questions || []).map((q: any, idx: number) => {
              const qid = q.question_id || q.id;
              const isSelfRating = q.question_type === "SELF_RATING";

              return (
                <div
                  key={qid || idx}
                  className="rounded-2xl border border-[#dfe7f0] bg-white p-6 shadow-sm space-y-4"
                >
                  <div className="flex items-center justify-between">
                    <span className="rounded-md bg-teal-50 px-2 py-0.5 text-[10px] font-extrabold uppercase tracking-wider text-teal-800">
                      {isSelfRating ? "Self-Evaluation" : "Domain Knowledge"}
                    </span>
                    <span className="text-xs font-bold text-slate-400">
                      Question #{idx + 1}
                    </span>
                  </div>

                  <h3 className="text-base font-bold text-[#123057]">
                    {q.scenario_context || q.question_text || q.question}
                  </h3>

                  {isSelfRating ? (
                    <div className="flex gap-2">
                      {[1, 2, 3, 4, 5].map((lvl) => (
                        <button
                          key={lvl}
                          type="button"
                          onClick={() => setRatings((prev) => ({ ...prev, [qid]: lvl }))}
                          className={`flex-1 py-2 rounded-xl text-xs font-bold border transition-all ${
                            ratings[qid] === lvl
                              ? "bg-teal-700 text-white border-teal-700 shadow"
                              : "bg-slate-50 border-slate-200 text-slate-700 hover:bg-slate-100"
                          }`}
                        >
                          Level {lvl}
                        </button>
                      ))}
                    </div>
                  ) : (
                    <div className="space-y-2">
                      {(q.options || []).map((opt: string, oIdx: number) => (
                        <button
                          key={oIdx}
                          type="button"
                          onClick={() => {
                            setAnswers((prev) => [
                              ...prev.filter((a) => a.question_id !== qid),
                              { question_id: qid, selected_answer: opt },
                            ]);
                          }}
                          className={`w-full text-left p-3 rounded-xl text-xs border transition-all ${
                            answers.some((a) => a.question_id === qid && a.selected_answer === opt)
                              ? "bg-teal-50 border-teal-500 font-bold text-teal-900"
                              : "bg-slate-50 border-slate-200 text-slate-700 hover:bg-slate-100"
                          }`}
                        >
                          {opt}
                        </button>
                      ))}
                    </div>
                  )}
                </div>
              );
            })}

            <div className="flex justify-end pt-4">
              <button
                type="submit"
                disabled={busy}
                className="rounded-xl bg-[#123057] px-6 py-3 text-xs font-bold text-white hover:bg-[#087f76] transition-all"
              >
                Submit Baseline Assessment
              </button>
            </div>
          </form>
        </div>
      )}
    </div>
  );
}

function chrFromIdx(idx: number): string {
  return String.fromCharCode(65 + idx);
}

export default OfficialAssessments;
