import React, { useEffect, useState } from "react";
import {
  CheckCircle2,
  XCircle,
  Edit3,
  Filter,
  Search,
  BookOpen,
  HelpCircle,
  Clock,
  Layers,
  ArrowRight,
  Sparkles,
  RefreshCw,
  X,
  Check,
  AlertTriangle,
} from "lucide-react";
import { api, clearApiCache, TrainerQuestion, QuestionReviewStatus, LearningMaterial } from "@/lib/api";
import { toast } from "sonner";

interface TrainerQuestionReviewProps {
  initialMaterialId?: string;
  onNavigate: (page: string, context?: { materialId?: string }) => void;
}

export function TrainerQuestionReview({
  initialMaterialId,
  onNavigate,
}: TrainerQuestionReviewProps) {
  const [questions, setQuestions] = useState<TrainerQuestion[]>([]);
  const [materials, setMaterials] = useState<LearningMaterial[]>([]);
  const [loading, setLoading] = useState(true);

  // Filters
  const [selectedMaterialId, setSelectedMaterialId] = useState(initialMaterialId || "ALL");
  const [statusFilter, setStatusFilter] = useState<string>("ALL");
  const [searchQuery, setSearchQuery] = useState("");

  // Edit Modal State
  const [editModalOpen, setEditModalOpen] = useState(false);
  const [editingQuestion, setEditingQuestion] = useState<TrainerQuestion | null>(null);
  const [editForm, setEditForm] = useState({
    question: "",
    options: ["", "", "", ""],
    correct_answer: "A",
    explanation: "",
  });
  const [savingEdit, setSavingEdit] = useState(false);

  // Reject Modal State
  const [rejectModalOpen, setRejectModalOpen] = useState(false);
  const [rejectingQuestion, setRejectingQuestion] = useState<TrainerQuestion | null>(null);
  const [rejectNotes, setRejectNotes] = useState("");
  const [submittingReject, setSubmittingReject] = useState(false);

  const fetchQuestionsAndMaterials = async () => {
    clearApiCache();
    try {
      setLoading(true);
      const mats = await api.trainer.materials.list();
      setMaterials(mats);

      // Fetch questions based on material selection
      if (selectedMaterialId && selectedMaterialId !== "ALL") {
        const qList = await api.trainer.materials.getQuestions(
          selectedMaterialId,
          statusFilter !== "ALL" ? statusFilter : undefined
        );
        setQuestions(qList);
      } else {
        // Collect questions across all materials in a single fast call
        try {
          const allQuestions = await api.trainer.questions.list(
            statusFilter !== "ALL" ? statusFilter : undefined
          );
          setQuestions(allQuestions);
        } catch {
          // Fallback if needed
          const fallbackList: TrainerQuestion[] = [];
          for (const mat of mats) {
            const matId = mat.id || (mat as any)._id;
            try {
              const qList = await api.trainer.materials.getQuestions(
                matId,
                statusFilter !== "ALL" ? statusFilter : undefined
              );
              fallbackList.push(...qList);
            } catch {
              // Ignore single material fetch error
            }
          }
          setQuestions(fallbackList);
        }
      }
    } catch (err: any) {
      toast.error(err.message || "Failed to load questions");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchQuestionsAndMaterials();
  }, [selectedMaterialId, statusFilter]);

  // ── Actions ──

  const handleApprove = async (q: TrainerQuestion) => {
    const qid = q.id || q.question_id || (q as any)._id;
    try {
      await api.trainer.questions.approve(qid);
      toast.success("Question approved! It can now be used in published quizzes.");
      setQuestions((prev) =>
        prev.map((item) =>
          (item.id || item.question_id || (item as any)._id) === qid
            ? { ...item, status: "APPROVED" as QuestionReviewStatus }
            : item
        )
      );
    } catch (err: any) {
      toast.error(err.message || "Failed to approve question");
    }
  };

  const openEditModal = (q: TrainerQuestion) => {
    setEditingQuestion(q);
    setEditForm({
      question: q.question,
      options: q.options && q.options.length === 4 ? [...q.options] : ["", "", "", ""],
      correct_answer: q.correct_answer || "A",
      explanation: q.explanation || "",
    });
    setEditModalOpen(true);
  };

  const handleSaveEdit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editingQuestion) return;
    const qid = editingQuestion.id || editingQuestion.question_id || (editingQuestion as any)._id;

    if (!editForm.question.trim()) {
      toast.error("Question text cannot be empty.");
      return;
    }
    if (editForm.options.some((opt) => !opt.trim())) {
      toast.error("All 4 options must be provided.");
      return;
    }

    try {
      setSavingEdit(true);
      const updated = await api.trainer.questions.update(qid, {
        question: editForm.question,
        options: editForm.options,
        correct_answer: editForm.correct_answer,
        explanation: editForm.explanation,
      });

      toast.success("Question edited successfully! Status set to EDITED.");
      setQuestions((prev) =>
        prev.map((item) =>
          (item.id || item.question_id || (item as any)._id) === qid
            ? {
                ...item,
                ...updated,
                question: editForm.question,
                options: editForm.options,
                correct_answer: editForm.correct_answer,
                explanation: editForm.explanation,
                status: "EDITED" as QuestionReviewStatus,
              }
            : item
        )
      );
      setEditModalOpen(false);
      setEditingQuestion(null);
    } catch (err: any) {
      toast.error(err.message || "Failed to edit question");
    } finally {
      setSavingEdit(false);
    }
  };

  const openRejectModal = (q: TrainerQuestion) => {
    setRejectingQuestion(q);
    setRejectNotes(q.review_notes || "");
    setRejectModalOpen(true);
  };

  const handleConfirmReject = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!rejectingQuestion) return;
    const qid = rejectingQuestion.id || rejectingQuestion.question_id || (rejectingQuestion as any)._id;

    if (!rejectNotes.trim()) {
      toast.error("Please provide a reason for rejecting this question.");
      return;
    }

    try {
      setSubmittingReject(true);
      await api.trainer.questions.reject(qid, {
        action: "REJECT",
        review_notes: rejectNotes.trim(),
      });

      toast.success("Question rejected.");
      setQuestions((prev) =>
        prev.map((item) =>
          (item.id || item.question_id || (item as any)._id) === qid
            ? {
                ...item,
                status: "REJECTED" as QuestionReviewStatus,
                review_notes: rejectNotes.trim(),
              }
            : item
        )
      );
      setRejectModalOpen(false);
      setRejectingQuestion(null);
    } catch (err: any) {
      toast.error(err.message || "Failed to reject question");
    } finally {
      setSubmittingReject(false);
    }
  };

  const filteredQuestions = questions.filter((q) => {
    const term = searchQuery.toLowerCase();
    const matchesSearch =
      q.question.toLowerCase().includes(term) ||
      (q.explanation && q.explanation.toLowerCase().includes(term)) ||
      q.competency_code.toLowerCase().includes(term);

    const matchesStatus = statusFilter === "ALL" || q.status === statusFilter;
    return matchesSearch && matchesStatus;
  });

  return (
    <div className="space-y-6 animate-fadeIn">
      {/* Top Header */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-black text-slate-800">Question Review Studio</h1>
          <p className="text-sm text-slate-500 mt-1">
            Audit AI-generated MCQs, edit inaccuracies, and approve questions for authorized assessments.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={fetchQuestionsAndMaterials}
            className="flex items-center gap-1.5 rounded-xl border border-[#f0ddd0] bg-white px-3.5 py-2.5 text-xs font-bold text-slate-600 hover:bg-orange-50 transition-colors"
          >
            <RefreshCw size={14} className={loading ? "animate-spin" : ""} />
            Refresh Pool
          </button>

          <button
            onClick={() => onNavigate("Quiz Studio")}
            className="flex items-center gap-2 rounded-xl bg-[#ef7e37] px-4 py-2.5 text-xs font-bold text-white shadow hover:bg-[#d96a27] transition-all"
          >
            Open Quiz Studio <ArrowRight size={14} />
          </button>
        </div>
      </div>

      {/* Filter Toolbar */}
      <div className="flex flex-col gap-3 rounded-2xl border border-[#f0ddd0] bg-white p-4 shadow-sm md:flex-row md:items-center md:justify-between">
        {/* Search */}
        <div className="flex flex-1 items-center gap-2 rounded-xl border border-slate-200 px-3 py-2">
          <Search size={16} className="text-slate-400" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search questions by keyword or competency..."
            className="w-full bg-transparent text-xs text-slate-800 placeholder-slate-400 focus:outline-none"
          />
          {searchQuery && (
            <button onClick={() => setSearchQuery("")} className="text-xs text-slate-400 hover:text-slate-600">
              <X size={14} />
            </button>
          )}
        </div>

        {/* Material Filter */}
        <div className="flex items-center gap-2">
          <label className="text-xs font-bold text-slate-500 whitespace-nowrap">Material:</label>
          <select
            value={selectedMaterialId}
            onChange={(e) => setSelectedMaterialId(e.target.value)}
            className="rounded-xl border border-slate-200 bg-white px-3 py-2 text-xs font-semibold text-slate-700 focus:border-[#ef7e37] focus:outline-none"
          >
            <option value="ALL">All Materials</option>
            {materials.map((m) => (
              <option key={m.id || (m as any)._id} value={m.id || (m as any)._id}>
                {m.original_filename || m.filename}
              </option>
            ))}
          </select>
        </div>

        {/* Status Filter Tabs */}
        <div className="flex items-center gap-1 overflow-x-auto rounded-xl bg-slate-100 p-1">
          {["ALL", "GENERATED", "EDITED", "APPROVED", "REJECTED"].map((st) => (
            <button
              key={st}
              onClick={() => setStatusFilter(st)}
              className={`rounded-lg px-2.5 py-1 text-[11px] font-bold uppercase transition-all whitespace-nowrap ${
                statusFilter === st
                  ? "bg-white text-slate-800 shadow-sm"
                  : "text-slate-500 hover:text-slate-800"
              }`}
            >
              {st}
            </button>
          ))}
        </div>
      </div>

      {/* Question Cards List */}
      {loading ? (
        <div className="space-y-4">
          {[1, 2, 3].map((n) => (
            <div key={n} className="h-48 rounded-2xl border border-slate-200 bg-white p-6 animate-pulse" />
          ))}
        </div>
      ) : filteredQuestions.length === 0 ? (
        <div className="rounded-2xl border border-dashed border-[#f0ddd0] bg-white p-12 text-center">
          <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-orange-50 text-[#ef7e37]">
            <HelpCircle size={24} />
          </div>
          <h3 className="mt-4 text-base font-bold text-slate-800">No questions found</h3>
          <p className="mt-1 text-sm text-slate-500 max-w-md mx-auto">
            {searchQuery || statusFilter !== "ALL"
              ? "Try adjusting your filters or search terms."
              : "Generate questions from your uploaded materials to start reviewing."}
          </p>
          <button
            onClick={() => onNavigate("AI Question Generator")}
            className="mt-5 inline-flex items-center gap-2 rounded-xl bg-[#ef7e37] px-4 py-2.5 text-xs font-bold text-white hover:bg-[#d96a27] transition-colors"
          >
            <Sparkles size={14} /> Generate Questions
          </button>
        </div>
      ) : (
        <div className="space-y-4">
          {filteredQuestions.map((q, idx) => {
            const qid = q.id || q.question_id || (q as any)._id;
            const isApproved = q.status === "APPROVED";
            const isRejected = q.status === "REJECTED";
            const isEdited = q.status === "EDITED";
            const isGenerated = q.status === "GENERATED";

            return (
              <div
                key={qid || idx}
                className={`rounded-2xl border bg-white p-6 shadow-sm transition-all hover:shadow-md ${
                  isApproved
                    ? "border-emerald-200 bg-emerald-50/10"
                    : isRejected
                    ? "border-rose-200 bg-rose-50/10"
                    : isEdited
                    ? "border-blue-200 bg-blue-50/10"
                    : "border-[#f0ddd0]"
                }`}
              >
                {/* Header row */}
                <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-100 pb-3">
                  <div className="flex items-center gap-2.5">
                    <span className="rounded-lg bg-slate-100 px-2 py-0.5 text-xs font-black text-slate-600">
                      #{idx + 1}
                    </span>
                    <span className="rounded-md bg-orange-50 px-2 py-0.5 text-[11px] font-bold text-[#c2510e]">
                      {q.competency_code}
                    </span>
                    {q.difficulty && (
                      <span className="text-[11px] font-semibold text-slate-400">
                        · {q.difficulty}
                      </span>
                    )}
                  </div>

                  {/* Status Badge */}
                  <div>
                    {isApproved ? (
                      <span className="inline-flex items-center gap-1 rounded-full bg-emerald-100 px-3 py-1 text-xs font-bold text-emerald-800">
                        <CheckCircle2 size={13} /> APPROVED
                      </span>
                    ) : isEdited ? (
                      <span className="inline-flex items-center gap-1 rounded-full bg-blue-100 px-3 py-1 text-xs font-bold text-blue-800">
                        <Edit3 size={13} /> EDITED
                      </span>
                    ) : isRejected ? (
                      <span className="inline-flex items-center gap-1 rounded-full bg-rose-100 px-3 py-1 text-xs font-bold text-rose-800">
                        <XCircle size={13} /> REJECTED
                      </span>
                    ) : (
                      <span className="inline-flex items-center gap-1 rounded-full bg-amber-100 px-3 py-1 text-xs font-bold text-amber-800">
                        <Clock size={13} /> GENERATED
                      </span>
                    )}
                  </div>
                </div>

                {/* Question Stem */}
                <div className="mt-4">
                  <h3 className="text-base font-bold text-slate-800 leading-snug">
                    {q.question}
                  </h3>
                </div>

                {/* Options Grid */}
                <div className="mt-4 grid gap-2 sm:grid-cols-2">
                  {q.options &&
                    q.options.map((opt, optIdx) => {
                      const letter = String.fromCharCode(65 + optIdx);
                      const isCorrect = letter === q.correct_answer;

                      return (
                        <div
                          key={optIdx}
                          className={`flex items-center gap-3 rounded-xl border p-3 text-xs transition-all ${
                            isCorrect
                              ? "border-emerald-300 bg-emerald-50/70 font-bold text-emerald-900 shadow-sm"
                              : "border-slate-100 bg-slate-50/60 text-slate-700"
                          }`}
                        >
                          <span
                            className={`flex h-6 w-6 shrink-0 items-center justify-center rounded-lg text-xs font-black ${
                              isCorrect ? "bg-emerald-600 text-white" : "bg-slate-200 text-slate-600"
                            }`}
                          >
                            {letter}
                          </span>
                          <span className="flex-1">{opt}</span>
                          {isCorrect && (
                            <span className="text-[10px] font-extrabold uppercase text-emerald-700">
                              Correct Key
                            </span>
                          )}
                        </div>
                      );
                    })}
                </div>

                {/* Explanation / Grounding */}
                {q.explanation && (
                  <div className="mt-4 rounded-xl border border-slate-200/60 bg-slate-50 p-3.5 text-xs text-slate-600 leading-relaxed">
                    <strong className="text-slate-800 font-semibold">Grounded Explanation:</strong>{" "}
                    {q.explanation}
                  </div>
                )}

                {/* Rejection Notes (if any) */}
                {isRejected && q.review_notes && (
                  <div className="mt-3 rounded-xl border border-rose-200 bg-rose-50 p-3 text-xs text-rose-800 flex items-start gap-2">
                    <AlertTriangle size={15} className="text-rose-600 mt-0.5 shrink-0" />
                    <div>
                      <strong>Reviewer Rejection Reason:</strong> {q.review_notes}
                    </div>
                  </div>
                )}

                {/* Action Bar */}
                <div className="mt-5 flex flex-wrap items-center justify-between gap-3 border-t border-slate-100 pt-4">
                  <div className="text-[11px] font-semibold text-slate-400">
                    ID: {qid}
                  </div>

                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => openEditModal(q)}
                      className="inline-flex items-center gap-1.5 rounded-xl border border-slate-200 px-3 py-1.5 text-xs font-bold text-slate-700 hover:bg-slate-50 transition-colors"
                    >
                      <Edit3 size={13} /> Edit Question
                    </button>

                    {!isRejected && (
                      <button
                        onClick={() => openRejectModal(q)}
                        className="inline-flex items-center gap-1.5 rounded-xl border border-rose-200 bg-white px-3 py-1.5 text-xs font-bold text-rose-700 hover:bg-rose-50 transition-colors"
                      >
                        <XCircle size={13} /> Reject
                      </button>
                    )}

                    {!isApproved && (
                      <button
                        onClick={() => handleApprove(q)}
                        className="inline-flex items-center gap-1.5 rounded-xl bg-emerald-600 px-4 py-1.5 text-xs font-bold text-white shadow hover:bg-emerald-700 transition-all active:scale-95"
                      >
                        <CheckCircle2 size={13} /> Approve Question
                      </button>
                    )}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* ── Edit Modal ── */}
      {editModalOpen && editingQuestion && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4 backdrop-blur-sm animate-fadeIn">
          <div className="relative w-full max-w-2xl rounded-3xl bg-white p-6 shadow-2xl border border-[#f0ddd0] max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between border-b border-slate-100 pb-4">
              <div>
                <h3 className="text-lg font-extrabold text-slate-800">
                  Edit Assessment Question
                </h3>
                <p className="text-xs text-slate-400 mt-0.5">
                  Refine question phrasing, options, or explanation
                </p>
              </div>
              <button
                onClick={() => setEditModalOpen(false)}
                className="rounded-full p-1 text-slate-400 hover:bg-slate-100 transition-colors"
              >
                <X size={18} />
              </button>
            </div>

            <form onSubmit={handleSaveEdit} className="mt-5 space-y-4">
              {/* Question Text */}
              <div className="space-y-1.5">
                <label className="block text-xs font-bold uppercase tracking-wider text-slate-600">
                  Question Stem
                </label>
                <textarea
                  value={editForm.question}
                  onChange={(e) => setEditForm({ ...editForm, question: e.target.value })}
                  rows={3}
                  className="w-full rounded-xl border border-slate-200 p-3 text-sm text-slate-800 focus:border-[#ef7e37] focus:outline-none shadow-sm"
                  required
                />
              </div>

              {/* Options */}
              <div className="space-y-3">
                <label className="block text-xs font-bold uppercase tracking-wider text-slate-600">
                  Multiple Choice Options
                </label>
                {editForm.options.map((opt, optIdx) => {
                  const letter = String.fromCharCode(65 + optIdx);
                  return (
                    <div key={optIdx} className="flex items-center gap-2">
                      <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-slate-100 text-xs font-black text-slate-700">
                        {letter}
                      </span>
                      <input
                        type="text"
                        value={opt}
                        onChange={(e) => {
                          const newOpts = [...editForm.options];
                          newOpts[optIdx] = e.target.value;
                          setEditForm({ ...editForm, options: newOpts });
                        }}
                        className="w-full rounded-xl border border-slate-200 px-3 py-2 text-xs text-slate-800 focus:border-[#ef7e37] focus:outline-none"
                        placeholder={`Option ${letter}`}
                        required
                      />
                    </div>
                  );
                })}
              </div>

              {/* Correct Answer Selector */}
              <div className="space-y-1.5">
                <label className="block text-xs font-bold uppercase tracking-wider text-slate-600">
                  Correct Answer Key
                </label>
                <div className="grid grid-cols-4 gap-2">
                  {["A", "B", "C", "D"].map((letter) => (
                    <button
                      type="button"
                      key={letter}
                      onClick={() => setEditForm({ ...editForm, correct_answer: letter })}
                      className={`rounded-xl border py-2 text-xs font-black transition-all ${
                        editForm.correct_answer === letter
                          ? "border-emerald-500 bg-emerald-50 text-emerald-800 shadow-sm"
                          : "border-slate-200 bg-white text-slate-600 hover:bg-slate-50"
                      }`}
                    >
                      Option {letter}
                    </button>
                  ))}
                </div>
              </div>

              {/* Explanation */}
              <div className="space-y-1.5">
                <label className="block text-xs font-bold uppercase tracking-wider text-slate-600">
                  Explanation & Grounding Context
                </label>
                <textarea
                  value={editForm.explanation}
                  onChange={(e) => setEditForm({ ...editForm, explanation: e.target.value })}
                  rows={3}
                  className="w-full rounded-xl border border-slate-200 p-3 text-xs text-slate-800 focus:border-[#ef7e37] focus:outline-none shadow-sm"
                  placeholder="Provide educational justification..."
                  required
                />
              </div>

              {/* Modal Actions */}
              <div className="mt-6 flex items-center justify-end gap-3 border-t border-slate-100 pt-4">
                <button
                  type="button"
                  onClick={() => setEditModalOpen(false)}
                  className="rounded-xl border border-slate-200 px-4 py-2 text-xs font-bold text-slate-600 hover:bg-slate-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={savingEdit}
                  className="inline-flex items-center gap-2 rounded-xl bg-blue-600 px-5 py-2 text-xs font-bold text-white shadow hover:bg-blue-700 disabled:opacity-50"
                >
                  {savingEdit ? "Saving..." : "Save Modifications"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* ── Reject Modal ── */}
      {rejectModalOpen && rejectingQuestion && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4 backdrop-blur-sm animate-fadeIn">
          <div className="relative w-full max-w-md rounded-3xl bg-white p-6 shadow-2xl border border-rose-200">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <h3 className="text-base font-extrabold text-rose-800 flex items-center gap-2">
                <XCircle size={18} /> Reject Question
              </h3>
              <button
                onClick={() => setRejectModalOpen(false)}
                className="rounded-full p-1 text-slate-400 hover:bg-slate-100"
              >
                <X size={16} />
              </button>
            </div>

            <form onSubmit={handleConfirmReject} className="mt-4 space-y-4">
              <p className="text-xs text-slate-600 leading-relaxed">
                Provide feedback or reason why this question is being rejected (e.g. hallucinated content, ambiguous options, or lack of grounding).
              </p>

              <div className="space-y-1.5">
                <label className="block text-xs font-bold text-slate-700">
                  Rejection Reason / Notes:
                </label>
                <textarea
                  value={rejectNotes}
                  onChange={(e) => setRejectNotes(e.target.value)}
                  rows={3}
                  className="w-full rounded-xl border border-rose-200 p-3 text-xs text-slate-800 focus:border-rose-500 focus:outline-none"
                  placeholder="e.g., Option B is ambiguous, and source text does not support this definition..."
                  required
                />
              </div>

              <div className="flex items-center justify-end gap-2 border-t border-slate-100 pt-3">
                <button
                  type="button"
                  onClick={() => setRejectModalOpen(false)}
                  className="rounded-xl border border-slate-200 px-3.5 py-1.5 text-xs font-bold text-slate-600"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submittingReject}
                  className="rounded-xl bg-rose-600 px-4 py-1.5 text-xs font-bold text-white shadow hover:bg-rose-700 disabled:opacity-50"
                >
                  {submittingReject ? "Rejecting..." : "Confirm Rejection"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

export default TrainerQuestionReview;
