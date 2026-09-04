/**
 * OfficialAssessments — Adaptive Capability Assessment Engine
 * Phase 3C Active: Dynamic Step-Up / Step-Down Calibration
 *
 * State machine:
 *   IDLE → STARTING → IN_PROGRESS → SUBMITTING → FEEDBACK → COMPLETING → COMPLETED
 *          ↓                                                        ↓
 *        ERROR                                                    ERROR
 *          ↓
 *        RESUMING (if session exists in localStorage)
 *
 * Root cause fixed: BEH_ETHICS returned question:null → blank screen.
 * Fix: backend now validates question bank before creating session;
 *      frontend has explicit ERROR state with user-friendly message.
 */

import React, { useCallback, useEffect, useRef, useState } from "react";
import {
  Activity,
  AlertCircle,
  ArrowRight,
  Award,
  BarChart2,
  BookOpen,
  Check,
  CheckCircle2,
  ChevronRight,
  ClipboardCheck,
  History,
  Info,
  Layers,
  Loader2,
  RefreshCw,
  RotateCcw,
  Sparkles,
  Target,
  TrendingDown,
  TrendingUp,
  X as XIcon,
  Zap,
} from "lucide-react";
import {
  api,
  clearApiCache,
  type AdaptiveFinalizeResponse,
  type AdaptiveQuestionItem,
  type AdaptiveStartResponse,
  type UserApplicableCompetency,
} from "@/lib/api";
import { toast } from "sonner";

// ─── Props ────────────────────────────────────────────────────────────────────

interface OfficialAssessmentsProps {
  initialCompetencyCode?: string;
  onNavigate: (page: string, context?: { competencyCode?: string }) => void;
}

// ─── State machine ────────────────────────────────────────────────────────────

type AssessmentPhase =
  | "IDLE"
  | "LOADING_COMPETENCIES"
  | "STARTING"
  | "RESUMING"
  | "IN_PROGRESS"
  | "SUBMITTING"
  | "FEEDBACK"
  | "COMPLETING"
  | "COMPLETED"
  | "ERROR"
  | "NOT_CONFIGURED";

// ─── Storage key for in-progress session resume ────────────────────────────────

const SESSION_STORAGE_KEY = "shikshasetu_adaptive_session";

function saveSessionToStorage(sessionId: string, code: string) {
  try {
    sessionStorage.setItem(SESSION_STORAGE_KEY, JSON.stringify({ sessionId, code, ts: Date.now() }));
  } catch {/* ignore */}
}

function clearSessionFromStorage() {
  try { sessionStorage.removeItem(SESSION_STORAGE_KEY); } catch {/* ignore */}
}

function getStoredSession(): { sessionId: string; code: string } | null {
  try {
    const raw = sessionStorage.getItem(SESSION_STORAGE_KEY);
    if (!raw) return null;
    const parsed = JSON.parse(raw);
    // Expire stored sessions after 2 hours
    if (Date.now() - parsed.ts > 2 * 60 * 60 * 1000) {
      clearSessionFromStorage();
      return null;
    }
    return parsed;
  } catch { return null; }
}

// ─── Domain → color ───────────────────────────────────────────────────────────

const DOMAIN_META: Record<string, { color: string; bg: string; label: string }> = {
  STATISTICAL:  { color: "text-blue-800",   bg: "bg-blue-50 border-blue-200",   label: "Statistical" },
  TECHNICAL:    { color: "text-teal-800",   bg: "bg-teal-50 border-teal-200",   label: "Technical" },
  GOVERNANCE:   { color: "text-purple-800", bg: "bg-purple-50 border-purple-200", label: "Governance" },
  BEHAVIORAL:   { color: "text-orange-800", bg: "bg-orange-50 border-orange-200", label: "Behavioural" },
  MANAGERIAL:   { color: "text-rose-800",   bg: "bg-rose-50 border-rose-200",   label: "Managerial" },
};

function domainMeta(domain: string) {
  const key = (domain || "").toUpperCase().replace(/\s+/g, "_");
  return DOMAIN_META[key] ?? { color: "text-slate-700", bg: "bg-slate-50 border-slate-200", label: domain };
}

// ─── Gap classification ────────────────────────────────────────────────────────

function classifyGap(gap: number): { label: string; color: string } {
  if (gap <= 0) return { label: "Competency Met", color: "text-emerald-700" };
  if (gap <= 0.5) return { label: "Near Target", color: "text-teal-700" };
  if (gap <= 1.5) return { label: "Moderate Gap", color: "text-amber-700" };
  return { label: "Critical Gap", color: "text-red-700" };
}

// ─── Theta bar ────────────────────────────────────────────────────────────────

function ThetaBar({ theta, maxTheta = 5 }: { theta: number; maxTheta?: number }) {
  const pct = Math.min(100, Math.max(4, ((theta - 1) / (maxTheta - 1)) * 100));
  const color =
    pct >= 80 ? "bg-emerald-500" :
    pct >= 60 ? "bg-teal-500" :
    pct >= 40 ? "bg-amber-400" : "bg-slate-400";
  return (
    <div className="h-2 w-full rounded-full bg-slate-100 overflow-hidden">
      <div
        className={`h-full rounded-full transition-all duration-500 ${color}`}
        style={{ width: `${pct}%` }}
      />
    </div>
  );
}

// ─── History panel ────────────────────────────────────────────────────────────

function AssessmentHistoryPanel({ onStart }: { onStart: (code: string) => void }) {
  const [history, setHistory] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    clearApiCache();
    api.adaptiveAssessments.history()
      .then(setHistory)
      .catch(() => setHistory([]))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return (
    <div className="flex items-center gap-2 text-xs text-slate-400 py-4">
      <Loader2 size={14} className="animate-spin" /> Loading history…
    </div>
  );
  if (!history.length) return null;

  return (
    <div className="rounded-2xl border border-[#dfe7f0] bg-white p-5 shadow-sm space-y-3">
      <div className="flex items-center gap-2">
        <History size={14} className="text-slate-400" />
        <span className="text-xs font-bold text-slate-500 uppercase tracking-wider">Past Assessments</span>
      </div>
      <div className="space-y-2">
        {history.slice(0, 5).map((h) => (
          <div key={h.session_id} className="flex items-center justify-between text-xs">
            <div>
              <span className="font-semibold text-[#123057]">{h.competency_name || h.competency_code}</span>
              <span className="ml-2 text-slate-400">
                L{Number(h.final_score).toFixed(1)} · {Number(h.accuracy_pct).toFixed(0)}% acc
              </span>
            </div>
            <button
              onClick={() => onStart(h.competency_code)}
              className="text-teal-700 font-bold hover:underline"
            >
              Retake
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}

// ─── Main Component ───────────────────────────────────────────────────────────

export function OfficialAssessments({ initialCompetencyCode, onNavigate }: OfficialAssessmentsProps) {
  // ── Phase ────────────────────────────────────────────────────────────────
  const [phase, setPhase] = useState<AssessmentPhase>("LOADING_COMPETENCIES");

  // ── Competency list ───────────────────────────────────────────────────────
  const [competencies, setCompetencies] = useState<UserApplicableCompetency[]>([]);
  const [selectedCode, setSelectedCode] = useState<string>("");

  // ── Session / question ───────────────────────────────────────────────────
  const [session, setSession] = useState<AdaptiveStartResponse | null>(null);
  const [currentQuestion, setCurrentQuestion] = useState<AdaptiveQuestionItem | null>(null);
  const [currentQNumber, setCurrentQNumber] = useState(1);
  const [totalQPlanned, setTotalQPlanned] = useState(5);
  const [theta, setTheta] = useState(2.5);
  const [difficulty, setDifficulty] = useState("MEDIUM");
  const [selectedOption, setSelectedOption] = useState<string>("");

  // ── Feedback ─────────────────────────────────────────────────────────────
  const [feedback, setFeedback] = useState<{
    isCorrect: boolean;
    explanation: string | null;
    prevTheta: number;
    newTheta: number;
  } | null>(null);

  // ── Result ───────────────────────────────────────────────────────────────
  const [finalResult, setFinalResult] = useState<AdaptiveFinalizeResponse | null>(null);

  // ── Error ────────────────────────────────────────────────────────────────
  const [errorMsg, setErrorMsg] = useState<string>("");

  // ── Resume banner ─────────────────────────────────────────────────────────
  const [resumeSession, setResumeSession] = useState<{ sessionId: string; code: string } | null>(null);

  const feedbackTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  // ── Load competencies ─────────────────────────────────────────────────────

  useEffect(() => {
    let cancelled = false;
    clearApiCache();
    api.competencies.me()
      .then((comps) => {
        if (cancelled) return;
        setCompetencies(comps || []);
        // Check for stored in-progress session
        const stored = getStoredSession();
        if (stored) setResumeSession(stored);
        setPhase("IDLE");
      })
      .catch(() => {
        if (!cancelled) setPhase("IDLE");
      });
    return () => { cancelled = true; };
  }, []);

  // ── Auto-start from navigation context ───────────────────────────────────

  useEffect(() => {
    if (initialCompetencyCode && phase === "IDLE") {
      startAssessment(initialCompetencyCode);
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [initialCompetencyCode, phase]);

  // ── Cleanup timer on unmount ─────────────────────────────────────────────

  useEffect(() => () => {
    if (feedbackTimerRef.current) clearTimeout(feedbackTimerRef.current);
  }, []);

  // ── Start ─────────────────────────────────────────────────────────────────

  const startAssessment = useCallback(async (code: string) => {
    setPhase("STARTING");
    setSelectedCode(code);
    setSelectedOption("");
    setFeedback(null);
    setFinalResult(null);
    setErrorMsg("");
    clearSessionFromStorage();

    try {
      const res = await api.adaptiveAssessments.start(code, 5);

      if (!res.question) {
        // Should not happen after backend fix, but guard defensively
        setErrorMsg(`No questions are available for "${res.competency_name}". This competency is not yet configured for adaptive evaluation.`);
        setPhase("NOT_CONFIGURED");
        return;
      }

      setSession(res);
      setCurrentQuestion(res.question);
      setCurrentQNumber(1);
      setTotalQPlanned(res.total_questions_planned);
      setTheta(res.estimated_level);
      setDifficulty(res.difficulty);
      saveSessionToStorage(res.session_id, code);
      setPhase("IN_PROGRESS");
    } catch (err: any) {
      const msg: string = err?.message || "Failed to start assessment.";
      if (err?.status === 422 || msg.toLowerCase().includes("no assessment questions")) {
        setErrorMsg(msg);
        setPhase("NOT_CONFIGURED");
      } else {
        setErrorMsg(msg);
        setPhase("ERROR");
      }
    }
  }, []);

  // ── Resume ────────────────────────────────────────────────────────────────

  const resumeAssessment = useCallback(async () => {
    if (!resumeSession) return;
    setPhase("RESUMING");
    setResumeSession(null);
    try {
      const status = await api.adaptiveAssessments.sessionStatus(resumeSession.sessionId);
      if (status.status === "COMPLETED") {
        clearSessionFromStorage();
        setPhase("IDLE");
        return;
      }
      if (!status.current_question) {
        // Session exists but no question — just start fresh
        clearSessionFromStorage();
        startAssessment(resumeSession.code);
        return;
      }
      setSelectedCode(resumeSession.code);
      setSession({
        session_id: status.session_id,
        competency_code: status.competency_code,
        competency_name: status.competency_name,
        estimated_level: status.estimated_level,
        difficulty: status.difficulty,
        proficiency_tier: status.proficiency_tier,
        current_question_number: status.current_question_number,
        total_questions_planned: status.total_questions_planned,
        question: status.current_question,
        status: "IN_PROGRESS",
      });
      setCurrentQuestion(status.current_question);
      setCurrentQNumber(status.current_question_number);
      setTotalQPlanned(status.total_questions_planned);
      setTheta(status.estimated_level);
      setDifficulty(status.difficulty);
      setSelectedOption("");
      setFeedback(null);
      setPhase("IN_PROGRESS");
      toast.info("Assessment resumed from where you left off.");
    } catch {
      clearSessionFromStorage();
      startAssessment(resumeSession.code);
    }
  }, [resumeSession, startAssessment]);

  // ── Submit answer ─────────────────────────────────────────────────────────

  const submitAnswer = useCallback(async () => {
    if (!session || !currentQuestion || !selectedOption || phase !== "IN_PROGRESS") return;

    setPhase("SUBMITTING");
    const prevTheta = theta;

    try {
      const res = await api.adaptiveAssessments.answer(
        session.session_id,
        currentQuestion.question_id,
        selectedOption,
      );

      setTheta(res.updated_estimated_level);
      setDifficulty(res.next_difficulty);
      setFeedback({
        isCorrect: res.is_correct,
        explanation: res.explanation ?? null,
        prevTheta,
        newTheta: res.updated_estimated_level,
      });
      setPhase("FEEDBACK");

      if (res.is_complete || !res.next_question) {
        // Auto-finalize after brief feedback display
        feedbackTimerRef.current = setTimeout(async () => {
          setPhase("COMPLETING");
          try {
            const finalRes = await api.adaptiveAssessments.finalize(session.session_id);
            clearSessionFromStorage();
            setFinalResult(finalRes);
            setPhase("COMPLETED");
            toast.success("Assessment complete — authoritative evidence recorded (0.85 confidence).");
          } catch (err: any) {
            setErrorMsg(err?.message || "Failed to finalize assessment.");
            setPhase("ERROR");
          }
        }, 2200);
      } else {
        feedbackTimerRef.current = setTimeout(() => {
          setCurrentQuestion(res.next_question!);
          setCurrentQNumber((n) => n + 1);
          setSelectedOption("");
          setFeedback(null);
          setPhase("IN_PROGRESS");
        }, 2200);
      }
    } catch (err: any) {
      setErrorMsg(err?.message || "Failed to submit answer.");
      setPhase("ERROR");
    }
  }, [session, currentQuestion, selectedOption, phase, theta]);

  // ── Reset ─────────────────────────────────────────────────────────────────

  const resetToIdle = useCallback(() => {
    if (feedbackTimerRef.current) clearTimeout(feedbackTimerRef.current);
    clearSessionFromStorage();
    setPhase("IDLE");
    setSession(null);
    setCurrentQuestion(null);
    setFinalResult(null);
    setFeedback(null);
    setSelectedOption("");
    setErrorMsg("");
  }, []);

  // ── Render helpers ────────────────────────────────────────────────────────

  const progressPct = totalQPlanned > 0
    ? Math.round(((currentQNumber - 1) / totalQPlanned) * 100)
    : 0;

  const difficultyLabel =
    difficulty === "HARD"   ? "Advanced (L4–L5)"  :
    difficulty === "MEDIUM" ? "Intermediate (L3)" : "Foundation (L1–L2)";

  const difficultyColor =
    difficulty === "HARD"   ? "bg-purple-100 text-purple-900 border-purple-200" :
    difficulty === "MEDIUM" ? "bg-blue-100 text-blue-800 border-blue-200"       :
                              "bg-emerald-100 text-emerald-900 border-emerald-200";

  // ============================================================
  // RENDER — LOADING COMPETENCIES
  // ============================================================

  if (phase === "LOADING_COMPETENCIES") {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] gap-4">
        <Loader2 size={32} className="animate-spin text-[#087f76]" />
        <p className="text-sm font-semibold text-slate-500">Loading your capability profile…</p>
      </div>
    );
  }

  // ============================================================
  // RENDER — STARTING / RESUMING
  // ============================================================

  if (phase === "STARTING" || phase === "RESUMING") {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] gap-4">
        <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-gradient-to-br from-[#123057] to-[#087f76] shadow-md">
          <Activity size={28} className="text-white animate-pulse" />
        </div>
        <p className="text-base font-bold text-[#123057]">
          {phase === "RESUMING" ? "Resuming your assessment…" : "Initializing adaptive assessment…"}
        </p>
        <p className="text-xs text-slate-400">Calibrating to your competency profile</p>
      </div>
    );
  }

  // ============================================================
  // RENDER — ERROR
  // ============================================================

  if (phase === "ERROR") {
    return (
      <div className="max-w-xl mx-auto mt-8">
        <div className="rounded-2xl border border-red-200 bg-red-50 p-6 space-y-4">
          <div className="flex items-start gap-3">
            <AlertCircle size={20} className="text-red-600 shrink-0 mt-0.5" />
            <div>
              <h3 className="text-sm font-bold text-red-800">Assessment Error</h3>
              <p className="text-xs text-red-700 mt-1 leading-relaxed">{errorMsg}</p>
            </div>
          </div>
          <div className="flex gap-3 pt-2">
            <button
              onClick={() => selectedCode ? startAssessment(selectedCode) : resetToIdle()}
              className="inline-flex items-center gap-1.5 rounded-xl bg-red-700 px-4 py-2 text-xs font-bold text-white hover:bg-red-800 transition-all"
            >
              <RefreshCw size={13} /> Retry
            </button>
            <button
              onClick={resetToIdle}
              className="rounded-xl border border-slate-200 px-4 py-2 text-xs font-bold text-slate-600 hover:bg-slate-50 transition-all"
            >
              Back to Assessments
            </button>
          </div>
        </div>
      </div>
    );
  }

  // ============================================================
  // RENDER — NOT CONFIGURED
  // ============================================================

  if (phase === "NOT_CONFIGURED") {
    return (
      <div className="max-w-xl mx-auto mt-8">
        <div className="rounded-2xl border border-amber-200 bg-amber-50 p-6 space-y-4">
          <div className="flex items-start gap-3">
            <Info size={20} className="text-amber-600 shrink-0 mt-0.5" />
            <div>
              <h3 className="text-sm font-bold text-amber-800">Assessment Not Yet Available</h3>
              <p className="text-xs text-amber-700 mt-1 leading-relaxed">{errorMsg}</p>
            </div>
          </div>
          <button
            onClick={resetToIdle}
            className="inline-flex items-center gap-1.5 rounded-xl border border-slate-200 bg-white px-4 py-2 text-xs font-bold text-slate-600 hover:bg-slate-50 transition-all"
          >
            ← Back to Assessments
          </button>
        </div>
      </div>
    );
  }

  // ============================================================
  // RENDER — COMPLETED (Result Screen)
  // ============================================================

  if (phase === "COMPLETED" && finalResult) {
    const improvement = finalResult.updated_competency_level - finalResult.previous_competency_level;
    const gap = finalResult.updated_skill_gap;
    const gapInfo = classifyGap(gap);
    const ImpIcon = improvement > 0.01 ? TrendingUp : improvement < -0.01 ? TrendingDown : null;

    return (
      <div className="space-y-5 animate-fadeIn max-w-3xl mx-auto">

        {/* Result header */}
        <div className="rounded-3xl border border-emerald-200 bg-white p-6 sm:p-8 shadow-sm">
          <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-4 pb-5 border-b border-slate-100">
            <div>
              <div className="inline-flex items-center gap-1.5 rounded-full bg-emerald-100 px-3 py-1 text-xs font-bold text-emerald-900">
                <CheckCircle2 size={13} /> Adaptive Assessment Complete
              </div>
              <h2 className="text-2xl font-black text-[#123057] mt-2 tracking-tight">
                {finalResult.competency_name}
              </h2>
              <p className="text-xs text-slate-500 mt-0.5">
                <span className="font-mono text-[11px] font-medium text-teal-700">{finalResult.competency_code}</span>
                {" · "}Authoritative Evidence (0.85 confidence) recorded
              </p>
            </div>
            {/* Validated level */}
            <div className="rounded-2xl border border-emerald-200 bg-emerald-50/60 px-6 py-4 text-center shrink-0">
              <div className="text-[10px] font-bold text-emerald-800 uppercase tracking-wider">Final Level</div>
              <div className="text-4xl font-black text-[#123057] mt-1 tracking-tight">
                {finalResult.final_demonstrated_level.toFixed(1)}
              </div>
              <div className="text-[10px] text-emerald-700 font-medium mt-0.5">/ 5.0</div>
            </div>
          </div>

          {/* KPI grid */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mt-5">
            <div className="rounded-xl bg-slate-50 border border-slate-100 p-3 text-center">
              <div className="text-[10px] font-bold text-slate-400 uppercase">Questions</div>
              <div className="text-xl font-black text-[#123057] mt-0.5">
                {finalResult.total_questions}
              </div>
            </div>
            <div className="rounded-xl bg-slate-50 border border-slate-100 p-3 text-center">
              <div className="text-[10px] font-bold text-slate-400 uppercase">Accuracy</div>
              <div className="text-xl font-black text-[#123057] mt-0.5">
                {finalResult.accuracy_pct.toFixed(0)}%
              </div>
            </div>
            <div className={`rounded-xl border p-3 text-center ${improvement >= 0 ? "bg-emerald-50 border-emerald-100" : "bg-red-50 border-red-100"}`}>
              <div className="text-[10px] font-bold text-slate-400 uppercase">Change</div>
              <div className={`text-xl font-black mt-0.5 flex items-center justify-center gap-1 ${improvement >= 0 ? "text-emerald-700" : "text-red-600"}`}>
                {ImpIcon && <ImpIcon size={16} />}
                {improvement >= 0 ? "+" : ""}{improvement.toFixed(2)}
              </div>
            </div>
            <div className={`rounded-xl border p-3 text-center ${gap <= 0 ? "bg-emerald-50 border-emerald-100" : "bg-amber-50 border-amber-100"}`}>
              <div className="text-[10px] font-bold text-slate-400 uppercase">Skill Gap</div>
              <div className={`text-xl font-black mt-0.5 ${gapInfo.color}`}>
                {gap <= 0 ? "✓ Met" : gap.toFixed(2)}
              </div>
            </div>
          </div>
        </div>

        {/* Competency timeline */}
        <div className="rounded-2xl border border-[#dfe7f0] bg-white p-6 shadow-sm space-y-4">
          <h3 className="text-sm font-bold text-[#123057]">Competency Rating Update</h3>
          <div className="space-y-2">
            <div className="flex items-center justify-between text-xs text-slate-500">
              <span>Previous</span>
              <span className="font-bold">{finalResult.previous_competency_level.toFixed(1)}</span>
            </div>
            <ThetaBar theta={finalResult.previous_competency_level} />
            <div className="flex items-center justify-between text-xs text-slate-500">
              <span>Validated</span>
              <span className="font-bold text-[#123057]">{finalResult.updated_competency_level.toFixed(1)}</span>
            </div>
            <ThetaBar theta={finalResult.updated_competency_level} />
          </div>
          <div className="rounded-xl bg-slate-50 border border-slate-100 p-3 text-xs text-slate-600 leading-relaxed">
            <strong>Proficiency Tier:</strong> {finalResult.proficiency_tier}
            <br />
            <strong>Skill Gap Status:</strong>{" "}
            <span className={gapInfo.color}>{gapInfo.label}</span>
            {gap > 0 && (
              <span className="text-slate-400"> (gap: {gap.toFixed(2)} levels below role requirement)</span>
            )}
          </div>
          <div className="rounded-xl bg-teal-50/60 border border-teal-100 p-3 text-xs text-teal-900">
            <strong>Authoritative Evidence ({(finalResult.evidence_confidence * 100).toFixed(0)}% confidence)</strong> has been recorded in your competency ledger.
            Evidence ID: <span className="font-mono text-[11px]">{finalResult.evidence_record_id.slice(-12)}</span>
          </div>
        </div>

        {/* Actions */}
        <div className="flex flex-wrap items-center gap-3 pb-6">
          <button
            onClick={() => onNavigate("Skill Gaps")}
            className="inline-flex items-center gap-2 rounded-xl bg-[#ef7e37] px-5 py-2.5 text-xs font-bold text-white shadow hover:bg-[#d96a27] transition-all"
          >
            <Target size={13} /> View Updated Skill Gaps
          </button>
          <button
            onClick={() => onNavigate("Recommendations")}
            className="inline-flex items-center gap-2 rounded-xl border border-[#dfe7f0] bg-white px-4 py-2.5 text-xs font-bold text-slate-700 hover:bg-slate-50 transition-all"
          >
            <BookOpen size={13} /> Learning Recommendations
          </button>
          <button
            onClick={resetToIdle}
            className="inline-flex items-center gap-1.5 text-xs font-bold text-slate-400 hover:text-slate-600 ml-auto transition-all"
          >
            <RotateCcw size={13} /> Assess Another Competency
          </button>
        </div>
      </div>
    );
  }

  // ============================================================
  // RENDER — COMPLETING
  // ============================================================

  if (phase === "COMPLETING") {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] gap-4">
        <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-gradient-to-br from-[#123057] to-[#087f76] shadow-md">
          <Loader2 size={28} className="text-white animate-spin" />
        </div>
        <p className="text-base font-bold text-[#123057]">Finalising assessment…</p>
        <p className="text-xs text-slate-400">Recording authoritative evidence (0.85 confidence)</p>
      </div>
    );
  }

  // ============================================================
  // RENDER — IN_PROGRESS / SUBMITTING / FEEDBACK
  // ============================================================

  if ((phase === "IN_PROGRESS" || phase === "SUBMITTING" || phase === "FEEDBACK") && session && currentQuestion) {
    const isSubmitting = phase === "SUBMITTING";
    const isFeedback = phase === "FEEDBACK";
    const canSubmit = !!selectedOption && !isSubmitting && !isFeedback;

    return (
      <div className="space-y-4 max-w-3xl mx-auto animate-fadeIn">

        {/* Assessment header */}
        <div className="rounded-2xl border border-[#dfe7f0] bg-white p-5 shadow-sm">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
            <div className="min-w-0">
              <div className="flex items-center gap-2 flex-wrap">
                <span className="rounded-md bg-teal-50 border border-teal-200 px-2 py-0.5 text-[10px] font-extrabold uppercase text-teal-800">
                  {session.competency_code}
                </span>
                <span className={`rounded-md border px-2 py-0.5 text-[10px] font-bold ${difficultyColor}`}>
                  {difficultyLabel}
                </span>
              </div>
              <h2 className="text-lg font-black text-[#123057] mt-1.5 leading-tight">
                {session.competency_name}
              </h2>
            </div>
            <div className="text-right shrink-0">
              <div className="text-[10px] font-bold text-slate-400 uppercase">Estimated Level</div>
              <div className="text-2xl font-black text-[#123057]">{theta.toFixed(1)}</div>
            </div>
          </div>

          {/* Progress */}
          <div className="mt-4 space-y-1.5">
            <div className="flex justify-between text-[10px] font-bold text-slate-400">
              <span>Question {currentQNumber} of {totalQPlanned}</span>
              <span>{progressPct}% complete</span>
            </div>
            <div className="h-2 w-full rounded-full bg-slate-100 overflow-hidden">
              <div
                className="h-full rounded-full bg-gradient-to-r from-teal-400 to-teal-600 transition-all duration-500"
                style={{ width: `${Math.max(4, progressPct)}%` }}
              />
            </div>
            <div className="flex justify-between text-[10px] text-slate-300">
              <span>L1</span><span>L2</span><span>L3</span><span>L4</span><span>L5</span>
            </div>
            <ThetaBar theta={theta} />
          </div>
        </div>

        {/* Question card */}
        <div className="rounded-2xl border border-[#dfe7f0] bg-white p-6 shadow-sm space-y-5">
          {currentQuestion.scenario_context && (
            <div className="rounded-xl bg-blue-50 border border-blue-100 p-4 text-xs text-blue-900 leading-relaxed">
              <span className="font-bold">Scenario: </span>{currentQuestion.scenario_context}
            </div>
          )}

          <h3 className="text-base font-bold text-[#123057] leading-snug">
            {currentQuestion.question_text}
          </h3>

          {/* Options */}
          <div className="space-y-2.5">
            {currentQuestion.options.map((opt, idx) => {
              const letter = String.fromCharCode(65 + idx);
              const isSelected = selectedOption === letter;
              const isFeedbackSelected = isFeedback && isSelected;
              const bgClass = isFeedbackSelected
                ? feedback?.isCorrect
                  ? "border-emerald-400 bg-emerald-50 shadow-sm"
                  : "border-red-300 bg-red-50"
                : isSelected
                ? "border-teal-400 bg-teal-50/70 shadow-sm"
                : "border-slate-200 bg-slate-50/50 hover:border-teal-300 hover:bg-teal-50/30";

              return (
                <button
                  key={idx}
                  type="button"
                  disabled={isFeedback || isSubmitting}
                  onClick={() => !isFeedback && !isSubmitting && setSelectedOption(letter)}
                  className={`w-full flex items-center gap-3 rounded-xl border p-4 text-left text-sm transition-all duration-150 ${bgClass}`}
                >
                  <span className={`flex h-7 w-7 shrink-0 items-center justify-center rounded-lg text-[11px] font-black transition-colors ${
                    isSelected ? "bg-teal-500 text-white" : "bg-slate-200 text-slate-600"
                  }`}>
                    {letter}
                  </span>
                  <span className="font-medium text-slate-800 leading-snug">{opt}</span>
                  {isFeedbackSelected && (
                    feedback?.isCorrect
                      ? <Check size={15} className="text-emerald-600 ml-auto shrink-0" />
                      : <XIcon size={15} className="text-red-500 ml-auto shrink-0" />
                  )}
                </button>
              );
            })}
          </div>

          {/* Feedback panel */}
          {isFeedback && feedback && (
            <div className={`rounded-xl border p-4 text-xs space-y-1.5 ${
              feedback.isCorrect
                ? "bg-emerald-50 border-emerald-200 text-emerald-900"
                : "bg-amber-50 border-amber-200 text-amber-900"
            }`}>
              <div className="flex items-center gap-2 font-bold">
                {feedback.isCorrect
                  ? <><Check size={15} className="text-emerald-600" /> Correct — demonstrated capability stepped up</>
                  : <><XIcon size={15} className="text-amber-600" /> Incorrect — recalibrating to foundation level</>
                }
              </div>
              {feedback.explanation && (
                <p className="text-slate-600 leading-relaxed">{feedback.explanation}</p>
              )}
              <div className="text-[11px] font-semibold text-slate-500 pt-1">
                Level: {feedback.prevTheta.toFixed(2)} → {feedback.newTheta.toFixed(2)}
                <span className={feedback.newTheta >= feedback.prevTheta ? " text-emerald-600" : " text-amber-600"}>
                  {" "}({feedback.newTheta >= feedback.prevTheta ? "+" : ""}{(feedback.newTheta - feedback.prevTheta).toFixed(2)})
                </span>
              </div>
            </div>
          )}

          {/* Action row */}
          <div className="flex items-center justify-between border-t border-slate-100 pt-4">
            <button
              type="button"
              onClick={resetToIdle}
              className="text-xs font-bold text-slate-400 hover:text-slate-600 transition-colors"
            >
              Exit Assessment
            </button>

            <button
              type="button"
              onClick={submitAnswer}
              disabled={!canSubmit}
              className="inline-flex items-center gap-2 rounded-xl bg-[#123057] px-6 py-3 text-xs font-bold text-white shadow hover:bg-[#087f76] disabled:opacity-40 transition-all active:scale-95"
            >
              {isSubmitting ? (
                <><Loader2 size={13} className="animate-spin" /> Evaluating…</>
              ) : isFeedback ? (
                <><Loader2 size={13} className="animate-spin" /> Next question…</>
              ) : (
                <>Submit Answer &amp; Calibrate <ArrowRight size={13} /></>
              )}
            </button>
          </div>
        </div>

        {/* Adaptive status bar */}
        <div className="rounded-xl border border-[#dfe7f0] bg-white px-5 py-3 flex items-center justify-between text-xs text-slate-500">
          <div className="flex items-center gap-3">
            <Zap size={13} className="text-[#ef7e37]" />
            <span>Adaptive difficulty: <strong className="text-slate-700">{difficultyLabel}</strong></span>
          </div>
          <div className="flex items-center gap-1 font-semibold text-teal-700">
            <Activity size={13} />
            Estimated L{theta.toFixed(2)}
          </div>
        </div>
      </div>
    );
  }

  // ============================================================
  // RENDER — IDLE (Dashboard)
  // ============================================================

  return (
    <div className="space-y-6 animate-fadeIn max-w-4xl mx-auto">

      {/* Page header */}
      <div className="rounded-3xl border border-[#dfe7f0] bg-white p-6 sm:p-8 shadow-sm">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-gradient-to-br from-[#123057] to-[#087f76] text-white shadow-md">
              <Activity size={22} />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-2xl font-black text-[#123057]">Adaptive Capability Assessments</h1>
                <span className="rounded-md bg-teal-100 px-2 py-0.5 text-[10px] font-extrabold text-teal-800 uppercase tracking-wider">
                  Phase 3C Active
                </span>
              </div>
              <p className="text-xs text-slate-500 mt-0.5">
                Dynamic Step-Up / Step-Down Engine · Authoritative Evidence (0.85 Confidence)
              </p>
            </div>
          </div>
        </div>

        {/* Resume banner */}
        {resumeSession && (
          <div className="mt-5 flex items-center justify-between gap-4 rounded-xl border border-amber-200 bg-amber-50 px-4 py-3">
            <div className="flex items-center gap-2 text-xs text-amber-900">
              <Info size={14} className="shrink-0" />
              <span>
                You have an in-progress <strong>{resumeSession.code}</strong> assessment.
              </span>
            </div>
            <div className="flex gap-2 shrink-0">
              <button
                onClick={resumeAssessment}
                className="rounded-lg bg-amber-600 px-3 py-1.5 text-xs font-bold text-white hover:bg-amber-700 transition-all"
              >
                Resume
              </button>
              <button
                onClick={() => { clearSessionFromStorage(); setResumeSession(null); }}
                className="rounded-lg border border-amber-300 px-3 py-1.5 text-xs font-bold text-amber-800 hover:bg-amber-100 transition-all"
              >
                Dismiss
              </button>
            </div>
          </div>
        )}

        {/* Hero CTA */}
        {competencies.length > 0 && (
          <div className="mt-6 rounded-2xl border border-teal-200 bg-gradient-to-r from-teal-50/90 via-blue-50/60 to-purple-50/50 p-6 flex flex-col md:flex-row md:items-center md:justify-between gap-5 shadow-sm">
            <div className="space-y-2">
              <div className="inline-flex items-center gap-1.5 rounded-full bg-teal-100 px-3 py-0.5 text-[10px] font-extrabold text-teal-900 uppercase tracking-wider">
                <Zap size={11} className="text-[#ef7e37]" /> Dynamic Step-Up / Step-Down Engine
              </div>
              <h3 className="text-base font-black text-[#123057]">Adaptive Competency Validation</h3>
              <p className="text-xs text-slate-600 max-w-lg leading-relaxed">
                Questions dynamically calibrate in real time based on your demonstrated accuracy.
                Completing an assessment records <strong>Authoritative Evidence (0.85)</strong>, directly
                updating your official competency rating.
              </p>
            </div>
            <button
              onClick={() => startAssessment(competencies[0].code)}
              className="inline-flex items-center justify-center gap-2 rounded-xl bg-[#ef7e37] px-6 py-3.5 text-xs font-black text-white shadow-md hover:bg-[#d96a27] transition-all whitespace-nowrap"
            >
              <Zap size={14} /> Start {competencies[0]?.name?.split(" ")[0] ?? "Target"} Assessment
            </button>
          </div>
        )}
      </div>

      {/* Competency cards */}
      {competencies.length > 0 ? (
        <div>
          <div className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-3">
            Your Mapped Competencies — Select for Adaptive Evaluation
          </div>
          <div className="grid gap-4 sm:grid-cols-2">
            {competencies.map((comp) => {
              const dm = domainMeta(comp.domain);
              const gap = comp.gap ?? 0;
              const gapInfo = classifyGap(gap);
              return (
                <div
                  key={comp.code}
                  className="rounded-2xl border border-slate-200 bg-white p-5 flex flex-col justify-between hover:border-teal-300 hover:shadow-md transition-all group"
                >
                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <span className={`rounded-md border px-2 py-0.5 text-[10px] font-bold ${dm.bg} ${dm.color}`}>
                        {dm.label}
                      </span>
                      <span className="font-mono text-[11px] font-medium text-teal-700">{comp.code}</span>
                    </div>
                    <h4 className="text-sm font-bold text-[#123057] group-hover:text-teal-800 transition-colors leading-tight">
                      {comp.name}
                    </h4>
                    {comp.description && (
                      <p className="text-xs text-slate-500 leading-relaxed line-clamp-2">{comp.description}</p>
                    )}
                    <div className="grid grid-cols-3 gap-2 pt-1">
                      <div>
                        <div className="text-[10px] font-bold text-slate-400 uppercase">Required</div>
                        <div className="text-sm font-black text-slate-700">L{comp.required_level.toFixed(1)}</div>
                      </div>
                      <div>
                        <div className="text-[10px] font-bold text-slate-400 uppercase">Current</div>
                        <div className="text-sm font-black text-teal-700">
                          {comp.current_level != null ? `L${comp.current_level.toFixed(1)}` : "—"}
                        </div>
                      </div>
                      <div>
                        <div className="text-[10px] font-bold text-slate-400 uppercase">Gap</div>
                        <div className={`text-sm font-black ${gapInfo.color}`}>
                          {comp.current_level != null ? (gap <= 0 ? "✓ Met" : gap.toFixed(1)) : "—"}
                        </div>
                      </div>
                    </div>
                    {comp.current_level != null && (
                      <ThetaBar theta={comp.current_level} />
                    )}
                    <div className="flex items-center justify-between text-[10px] text-slate-400 pt-0.5">
                      <span className={`font-bold ${gapInfo.color}`}>
                        {comp.current_level != null ? gapInfo.label : "Not Assessed"}
                      </span>
                      {comp.confidence > 0 && (
                        <span>Confidence: {Math.round(comp.confidence * 100)}%</span>
                      )}
                    </div>
                  </div>

                  <button
                    onClick={() => startAssessment(comp.code)}
                    className="mt-4 inline-flex items-center gap-1.5 rounded-xl border border-teal-200 bg-teal-50 px-4 py-2 text-xs font-bold text-teal-800 hover:bg-teal-100 transition-all"
                  >
                    <ClipboardCheck size={13} />
                    Start Adaptive Evaluation
                    <ChevronRight size={13} className="ml-auto" />
                  </button>
                </div>
              );
            })}
          </div>
        </div>
      ) : (
        <div className="rounded-2xl border border-dashed border-[#dfe7f0] bg-white p-10 text-center">
          <Layers size={28} className="mx-auto text-slate-300 mb-3" />
          <h3 className="text-sm font-bold text-[#123057]">No competencies mapped yet</h3>
          <p className="text-xs text-slate-500 mt-1 max-w-sm mx-auto">
            Your role's competency requirements will appear here once configured. You can still start a standard baseline assessment.
          </p>
        </div>
      )}

      {/* Assessment history */}
      <AssessmentHistoryPanel onStart={startAssessment} />

      {/* Footer note */}
      <p className="text-[11px] text-slate-400 text-center pb-4">
        Adaptive assessments update your official competency profile with Authoritative Evidence (0.85 confidence).
        Completing a learning module records Supporting Evidence (0.30 confidence).
      </p>
    </div>
  );
}

export default OfficialAssessments;
