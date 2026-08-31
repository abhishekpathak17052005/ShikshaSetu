import React, { useEffect, useState } from "react";
import {
  PenTool,
  Plus,
  Layers,
  Users,
  CheckCircle2,
  Clock,
  Eye,
  Send,
  Search,
  Filter,
  X,
  AlertCircle,
  HelpCircle,
  BookOpen,
  ArrowRight,
  TrendingUp,
  Award,
} from "lucide-react";
import {
  api,
  TrainerQuiz,
  TrainerQuestion,
  User,
  TrainerMaterial,
  LearningMaterial,
} from "@/lib/api";
import { toast } from "sonner";

interface TrainerQuizStudioProps {
  onNavigate: (page: string, context?: { quizId?: string }) => void;
}

export function TrainerQuizStudio({ onNavigate }: TrainerQuizStudioProps) {
  const [quizzes, setQuizzes] = useState<TrainerQuiz[]>([]);
  const [approvedQuestions, setApprovedQuestions] = useState<TrainerQuestion[]>([]);
  const [materials, setMaterials] = useState<LearningMaterial[]>([]);
  const [learners, setLearners] = useState<User[]>([]);
  const [competencies, setCompetencies] = useState<{ code: string; name: string }[]>([
    { code: "STAT_SAMPLING", name: "Statistical Sampling & Survey Design" },
    { code: "STAT_DATA_QUALITY_FRAMEWORKS", name: "Data Quality Frameworks" },
    { code: "STAT_SURVEY_DESIGN", name: "Survey Design & Methodology" },
    { code: "STAT_NATIONAL_ACCOUNTS", name: "National Accounts Statistics" },
    { code: "TECH_PYTHON", name: "Python Programming for Public Service" },
    { code: "DATA_ANALYSIS", name: "Data Analysis & Visual Analytics" },
  ]);
  const [loading, setLoading] = useState(true);

  // Tab State
  const [activeTab, setActiveTab] = useState<"LIST" | "CREATE">("LIST");

  // Create Form State
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [competencyCode, setCompetencyCode] = useState("STAT_SAMPLING");
  const [selectedQuestionIds, setSelectedQuestionIds] = useState<string[]>([]);
  const [creatingQuiz, setCreatingQuiz] = useState(false);

  // Preview Modal State
  const [previewModalOpen, setPreviewModalOpen] = useState(false);
  const [previewingQuiz, setPreviewingQuiz] = useState<TrainerQuiz | null>(null);

  // Assign Modal State
  const [assignModalOpen, setAssignModalOpen] = useState(false);
  const [assigningQuiz, setAssigningQuiz] = useState<TrainerQuiz | null>(null);
  const [selectedLearnerIds, setSelectedLearnerIds] = useState<string[]>([]);
  const [learnerSearch, setLearnerSearch] = useState("");
  const [submittingAssign, setSubmittingAssign] = useState(false);

  const fetchStudioData = async () => {
    try {
      setLoading(true);
      const [quizList, mats, learnerList, compList] = await Promise.all([
        api.trainer.quizzes.list(),
        api.trainer.materials.list(),
        api.trainer.learners.list().catch(() => []),
        api.competencies.list().catch(() => []),
      ]);

      setQuizzes(quizList);
      setMaterials(mats);
      setLearners(learnerList);
      if (compList.length > 0) {
        setCompetencies(
          compList.map((c) => ({
            code: c.code,
            name: c.name || c.code.replace(/_/g, " "),
          }))
        );
      }

      // Fetch approved questions across all materials
      const allApproved: TrainerQuestion[] = [];
      for (const mat of mats) {
        const matId = mat.id || (mat as any)._id;
        try {
          const qs = await api.trainer.materials.getQuestions(matId, "APPROVED");
          allApproved.push(...qs);
        } catch {
          // Ignore
        }
      }
      setApprovedQuestions(allApproved);
    } catch (err: any) {
      toast.error(err.message || "Failed to load Quiz Studio data");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStudioData();
  }, []);

  // ── Handlers ──

  const handleToggleQuestion = (qid: string) => {
    setSelectedQuestionIds((prev) =>
      prev.includes(qid) ? prev.filter((id) => id !== qid) : [...prev, qid]
    );
  };

  const handleCreateQuiz = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim()) {
      toast.error("Please enter a quiz title.");
      return;
    }
    if (selectedQuestionIds.length === 0) {
      toast.error("Please select at least 1 approved question for this assessment.");
      return;
    }

    try {
      setCreatingQuiz(true);
      const created = await api.trainer.quizzes.create({
        title: title.trim(),
        description: description.trim() || undefined,
        competency_code: competencyCode,
        question_ids: selectedQuestionIds,
      });

      toast.success(`Assessment draft "${created.title}" created successfully!`);
      setTitle("");
      setDescription("");
      setSelectedQuestionIds([]);
      setActiveTab("LIST");
      fetchStudioData();
    } catch (err: any) {
      toast.error(err.message || "Failed to create quiz");
    } finally {
      setCreatingQuiz(false);
    }
  };

  const handlePublishQuiz = async (quizId: string) => {
    try {
      await api.trainer.quizzes.publish(quizId);
      toast.success("Assessment published! You can now assign it to civil servants.");
      setQuizzes((prev) =>
        prev.map((q) =>
          (q.id || q.quiz_id || (q as any)._id) === quizId
            ? { ...q, status: "PUBLISHED" as any, published_at: new Date().toISOString() }
            : q
        )
      );
    } catch (err: any) {
      toast.error(err.message || "Failed to publish quiz");
    }
  };

  const openAssignModal = (quiz: TrainerQuiz) => {
    setAssigningQuiz(quiz);
    setSelectedLearnerIds([]);
    setLearnerSearch("");
    setAssignModalOpen(true);
  };

  const handleToggleLearner = (userId: string) => {
    setSelectedLearnerIds((prev) =>
      prev.includes(userId) ? prev.filter((id) => id !== userId) : [...prev, userId]
    );
  };

  const handleSelectAllLearners = () => {
    if (selectedLearnerIds.length === filteredLearners.length) {
      setSelectedLearnerIds([]);
    } else {
      setSelectedLearnerIds(filteredLearners.map((l) => l.id || (l as any)._id));
    }
  };

  const handleConfirmAssign = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!assigningQuiz) return;
    const qid = assigningQuiz.id || assigningQuiz.quiz_id || (assigningQuiz as any)._id;

    if (selectedLearnerIds.length === 0) {
      toast.error("Please select at least 1 learner to assign.");
      return;
    }

    try {
      setSubmittingAssign(true);
      await api.trainer.quizzes.assign(qid, { learner_ids: selectedLearnerIds });
      toast.success(`Assigned quiz to ${selectedLearnerIds.length} civil servants!`);
      setAssignModalOpen(false);
      setAssigningQuiz(null);
      fetchStudioData();
    } catch (err: any) {
      toast.error(err.message || "Failed to assign quiz");
    } finally {
      setSubmittingAssign(false);
    }
  };

  const openPreviewModal = async (quiz: TrainerQuiz) => {
    const qid = quiz.id || quiz.quiz_id || (quiz as any)._id;
    try {
      const fullQuiz = await api.trainer.quizzes.get(qid);
      setPreviewingQuiz(fullQuiz);
      setPreviewModalOpen(true);
    } catch (err: any) {
      toast.error(err.message || "Failed to load quiz preview");
    }
  };

  const filteredApprovedQuestions = approvedQuestions.filter(
    (q) => q.competency_code === competencyCode
  );

  const filteredLearners = learners.filter((l) => {
    const term = learnerSearch.toLowerCase();
    return (
      l.full_name?.toLowerCase().includes(term) ||
      l.email?.toLowerCase().includes(term) ||
      l.department?.toLowerCase().includes(term) ||
      l.designation?.toLowerCase().includes(term) ||
      l.employee_id?.toLowerCase().includes(term)
    );
  });

  return (
    <div className="space-y-6 animate-fadeIn">
      {/* Top Header */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-black text-slate-800">Quiz & Assessment Studio</h1>
          <p className="text-sm text-slate-500 mt-1">
            Build formal competency quizzes exclusively from approved questions, publish, and assign to learner cohorts.
          </p>
        </div>

        {/* Tab Toggle */}
        <div className="flex items-center gap-1 rounded-2xl border border-[#f0ddd0] bg-white p-1.5 shadow-sm">
          <button
            onClick={() => setActiveTab("LIST")}
            className={`flex items-center gap-2 rounded-xl px-4 py-2 text-xs font-bold transition-all ${
              activeTab === "LIST"
                ? "bg-[#ef7e37] text-white shadow-sm"
                : "text-slate-500 hover:text-slate-800"
            }`}
          >
            <Layers size={14} /> All Assessments ({quizzes.length})
          </button>
          <button
            onClick={() => setActiveTab("CREATE")}
            className={`flex items-center gap-2 rounded-xl px-4 py-2 text-xs font-bold transition-all ${
              activeTab === "CREATE"
                ? "bg-[#ef7e37] text-white shadow-sm"
                : "text-slate-500 hover:text-slate-800"
            }`}
          >
            <Plus size={14} /> Create Assessment
          </button>
        </div>
      </div>

      {/* ── TAB 1: LIST QUIZZES ── */}
      {activeTab === "LIST" && (
        <div className="space-y-4">
          {loading ? (
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
              {[1, 2, 3].map((n) => (
                <div key={n} className="h-52 rounded-2xl border border-slate-200 bg-white p-6 animate-pulse" />
              ))}
            </div>
          ) : quizzes.length === 0 ? (
            <div className="rounded-2xl border border-dashed border-[#f0ddd0] bg-white p-12 text-center">
              <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-orange-50 text-[#ef7e37]">
                <PenTool size={24} />
              </div>
              <h3 className="mt-4 text-base font-bold text-slate-800">No assessments created yet</h3>
              <p className="mt-1 text-sm text-slate-500 max-w-md mx-auto">
                Assemble approved questions into standardized capability assessment quizzes for your department.
              </p>
              <button
                onClick={() => setActiveTab("CREATE")}
                className="mt-5 inline-flex items-center gap-2 rounded-xl bg-[#ef7e37] px-4 py-2.5 text-xs font-bold text-white hover:bg-[#d96a27] transition-colors"
              >
                <Plus size={14} /> Create First Quiz
              </button>
            </div>
          ) : (
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
              {quizzes.map((q) => {
                const qid = q.id || q.quiz_id || (q as any)._id;
                const isPublished = q.status === "PUBLISHED" || q.status === "ASSIGNED";
                const isDraft = q.status === "DRAFT";

                return (
                  <div
                    key={qid}
                    className="flex flex-col justify-between rounded-2xl border border-[#f0ddd0] bg-white p-6 shadow-sm hover:border-orange-300 hover:shadow-md transition-all group"
                  >
                    <div>
                      {/* Header Badge */}
                      <div className="flex items-center justify-between">
                        <span className="rounded-md bg-orange-50 px-2.5 py-1 text-[11px] font-bold text-[#c2510e]">
                          {q.competency_code}
                        </span>

                        {isPublished ? (
                          <span className="inline-flex items-center gap-1 rounded-full bg-emerald-100 px-2.5 py-0.5 text-[11px] font-bold text-emerald-800">
                            <CheckCircle2 size={12} /> PUBLISHED
                          </span>
                        ) : (
                          <span className="inline-flex items-center gap-1 rounded-full bg-amber-100 px-2.5 py-0.5 text-[11px] font-bold text-amber-800">
                            <Clock size={12} /> DRAFT
                          </span>
                        )}
                      </div>

                      {/* Title */}
                      <h3 className="mt-3 text-base font-bold text-slate-800 group-hover:text-[#c2510e] transition-colors line-clamp-2">
                        {q.title}
                      </h3>

                      {q.description && (
                        <p className="mt-1.5 text-xs text-slate-500 line-clamp-2">
                          {q.description}
                        </p>
                      )}

                      {/* Metrics */}
                      <div className="mt-4 grid grid-cols-2 gap-2 rounded-xl bg-slate-50 p-3 text-xs">
                        <div>
                          <div className="text-slate-400 font-semibold">Questions:</div>
                          <div className="font-bold text-slate-800">
                            {q.question_count || q.questions?.length || 0} items
                          </div>
                        </div>
                        <div>
                          <div className="text-slate-400 font-semibold">Assigned:</div>
                          <div className="font-bold text-slate-800">
                            {q.assigned_learners_count || 0} learners
                          </div>
                        </div>
                      </div>
                    </div>

                    {/* Actions Bar */}
                    <div className="mt-5 border-t border-slate-100 pt-4 flex flex-col gap-2">
                      <div className="flex items-center gap-2">
                        <button
                          onClick={() => openPreviewModal(q)}
                          className="flex-1 inline-flex items-center justify-center gap-1 rounded-xl border border-slate-200 py-2 text-xs font-bold text-slate-700 hover:bg-slate-50 transition-colors"
                        >
                          <Eye size={13} /> Preview
                        </button>

                        {isDraft && (
                          <button
                            onClick={() => handlePublishQuiz(qid)}
                            className="flex-1 inline-flex items-center justify-center gap-1 rounded-xl bg-emerald-600 py-2 text-xs font-bold text-white shadow hover:bg-emerald-700 transition-all active:scale-95"
                          >
                            <Send size={13} /> Publish
                          </button>
                        )}
                      </div>

                      {isPublished && (
                        <div className="flex items-center gap-2">
                          <button
                            onClick={() => openAssignModal(q)}
                            className="flex-1 inline-flex items-center justify-center gap-1 rounded-xl bg-[#ef7e37] py-2 text-xs font-bold text-white shadow hover:bg-[#d96a27] transition-all active:scale-95"
                          >
                            <Users size={13} /> Assign Learners
                          </button>
                          <button
                            onClick={() => onNavigate("Learner Results", { quizId: qid })}
                            className="inline-flex items-center justify-center rounded-xl border border-orange-200 bg-orange-50 px-3 py-2 text-xs font-bold text-[#c2510e] hover:bg-orange-100 transition-colors"
                            title="View learner submissions for this quiz"
                          >
                            <TrendingUp size={13} />
                          </button>
                        </div>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      )}

      {/* ── TAB 2: CREATE ASSESSMENT ── */}
      {activeTab === "CREATE" && (
        <div className="rounded-3xl border border-[#f0ddd0] bg-white p-6 sm:p-8 shadow-sm space-y-6">
          <div className="border-b border-slate-100 pb-4">
            <h2 className="text-xl font-black text-slate-800">Create New Capability Assessment</h2>
            <p className="text-xs text-slate-400 mt-0.5">
              Compose a verified quiz draft exclusively from questions with status APPROVED.
            </p>
          </div>

          <form onSubmit={handleCreateQuiz} className="space-y-6">
            <div className="grid gap-4 sm:grid-cols-2">
              {/* Quiz Title */}
              <div className="space-y-1.5 sm:col-span-2">
                <label className="block text-xs font-bold uppercase tracking-wider text-slate-600">
                  Assessment Title
                </label>
                <input
                  type="text"
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  placeholder="e.g. Statistical Sampling Core Verification 2026"
                  className="w-full rounded-xl border border-slate-200 px-4 py-3 text-sm text-slate-800 focus:border-[#ef7e37] focus:outline-none shadow-sm"
                  required
                />
              </div>

              {/* Target Competency */}
              <div className="space-y-1.5">
                <label className="block text-xs font-bold uppercase tracking-wider text-slate-600">
                  Target Competency
                </label>
                <select
                  value={competencyCode}
                  onChange={(e) => {
                    setCompetencyCode(e.target.value);
                    setSelectedQuestionIds([]);
                  }}
                  className="w-full rounded-xl border border-slate-200 bg-white px-4 py-3 text-sm font-semibold text-slate-800 focus:border-[#ef7e37] focus:outline-none shadow-sm"
                >
                  {competencies.map((c) => (
                    <option key={c.code} value={c.code}>
                      {c.code} — {c.name}
                    </option>
                  ))}
                </select>
              </div>

              {/* Description */}
              <div className="space-y-1.5 sm:col-span-2">
                <label className="block text-xs font-bold uppercase tracking-wider text-slate-600">
                  Instructions & Description (Optional)
                </label>
                <textarea
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  rows={2}
                  placeholder="e.g. Mandatory formal assessment for Statistical Officers..."
                  className="w-full rounded-xl border border-slate-200 p-3 text-xs text-slate-800 focus:border-[#ef7e37] focus:outline-none shadow-sm"
                />
              </div>
            </div>

            {/* Approved Questions Selector */}
            <div className="space-y-3 pt-4 border-t border-slate-100">
              <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
                <div>
                  <h3 className="text-sm font-extrabold text-slate-800">
                    Select Approved Questions ({selectedQuestionIds.length} Selected)
                  </h3>
                  <p className="text-xs text-slate-400">
                    Showing approved items matching competency <strong>{competencyCode}</strong>
                  </p>
                </div>

                {filteredApprovedQuestions.length > 0 && (
                  <button
                    type="button"
                    onClick={() => {
                      if (selectedQuestionIds.length === filteredApprovedQuestions.length) {
                        setSelectedQuestionIds([]);
                      } else {
                        setSelectedQuestionIds(
                          filteredApprovedQuestions.map(
                            (q) => q.id || q.question_id || (q as any)._id
                          )
                        );
                      }
                    }}
                    className="text-xs font-bold text-[#ef7e37] hover:underline"
                  >
                    {selectedQuestionIds.length === filteredApprovedQuestions.length
                      ? "Deselect All"
                      : "Select All Matching"}
                  </button>
                )}
              </div>

              {filteredApprovedQuestions.length === 0 ? (
                <div className="rounded-2xl border border-dashed border-amber-200 bg-amber-50/50 p-8 text-center">
                  <AlertCircle size={24} className="mx-auto text-amber-600" />
                  <h4 className="mt-2 text-sm font-bold text-amber-900">
                    No approved questions for {competencyCode}
                  </h4>
                  <p className="mt-1 text-xs text-amber-700 max-w-sm mx-auto">
                    Please go to Question Review Studio and approve questions before adding them to a quiz.
                  </p>
                  <button
                    type="button"
                    onClick={() => onNavigate("Question Review")}
                    className="mt-4 inline-flex items-center gap-1.5 rounded-xl bg-[#ef7e37] px-4 py-2 text-xs font-bold text-white"
                  >
                    Open Review Studio
                  </button>
                </div>
              ) : (
                <div className="space-y-3 max-h-[360px] overflow-y-auto pr-1">
                  {filteredApprovedQuestions.map((q, idx) => {
                    const qid = q.id || q.question_id || (q as any)._id;
                    const isChecked = selectedQuestionIds.includes(qid);

                    return (
                      <div
                        key={qid || idx}
                        onClick={() => handleToggleQuestion(qid)}
                        className={`flex items-start gap-3 rounded-2xl border p-4 cursor-pointer transition-all ${
                          isChecked
                            ? "border-emerald-500 bg-emerald-50/40 shadow-sm"
                            : "border-slate-200 bg-white hover:border-slate-300"
                        }`}
                      >
                        <input
                          type="checkbox"
                          checked={isChecked}
                          onChange={() => {}} // Handled by div onClick
                          className="mt-1 h-4 w-4 rounded border-slate-300 accent-[#ef7e37]"
                        />

                        <div className="flex-1 space-y-1">
                          <div className="flex items-center gap-2">
                            <span className="text-xs font-bold text-slate-400">
                              #{idx + 1}
                            </span>
                            <span className="rounded bg-emerald-100 px-2 py-0.5 text-[10px] font-bold text-emerald-800">
                              APPROVED
                            </span>
                            {q.difficulty && (
                              <span className="text-[10px] font-semibold text-slate-400">
                                · {q.difficulty}
                              </span>
                            )}
                          </div>
                          <p className="text-xs font-bold text-slate-800">{q.question}</p>
                          <div className="text-[11px] text-slate-500">
                            Key: Option {q.correct_answer} · {q.explanation}
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>

            {/* Submit Action */}
            <div className="flex items-center justify-end gap-3 border-t border-slate-100 pt-6">
              <button
                type="button"
                onClick={() => setActiveTab("LIST")}
                className="rounded-xl border border-slate-200 px-5 py-2.5 text-xs font-bold text-slate-600 hover:bg-slate-50"
              >
                Cancel
              </button>

              <button
                type="submit"
                disabled={creatingQuiz || selectedQuestionIds.length === 0}
                className="inline-flex items-center gap-2 rounded-xl bg-[#ef7e37] px-6 py-2.5 text-xs font-bold text-white shadow hover:bg-[#d96a27] disabled:opacity-50 transition-all active:scale-95"
              >
                {creatingQuiz ? "Creating Assessment..." : "Save Assessment Draft"}
              </button>
            </div>
          </form>
        </div>
      )}

      {/* ── Assign Learners Modal ── */}
      {assignModalOpen && assigningQuiz && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4 backdrop-blur-sm animate-fadeIn">
          <div className="relative w-full max-w-xl rounded-3xl bg-white p-6 shadow-2xl border border-[#f0ddd0] max-h-[90vh] flex flex-col">
            <div className="flex items-center justify-between border-b border-slate-100 pb-4">
              <div>
                <h3 className="text-lg font-extrabold text-slate-800">
                  Assign Assessment to Learners
                </h3>
                <p className="text-xs text-slate-400 mt-0.5">
                  Quiz: <strong>{assigningQuiz.title}</strong> ({assigningQuiz.competency_code})
                </p>
              </div>
              <button
                onClick={() => setAssignModalOpen(false)}
                className="rounded-full p-1 text-slate-400 hover:bg-slate-100"
              >
                <X size={18} />
              </button>
            </div>

            <form onSubmit={handleConfirmAssign} className="mt-4 flex-1 flex flex-col space-y-4 overflow-hidden">
              {/* Search & Select All */}
              <div className="flex items-center justify-between gap-3">
                <div className="flex flex-1 items-center gap-2 rounded-xl border border-slate-200 px-3 py-1.5 text-xs">
                  <Search size={14} className="text-slate-400" />
                  <input
                    type="text"
                    value={learnerSearch}
                    onChange={(e) => setLearnerSearch(e.target.value)}
                    placeholder="Search officials by name, email, department..."
                    className="w-full bg-transparent text-xs text-slate-800 focus:outline-none"
                  />
                </div>

                {filteredLearners.length > 0 && (
                  <button
                    type="button"
                    onClick={handleSelectAllLearners}
                    className="text-xs font-bold text-[#ef7e37] hover:underline whitespace-nowrap"
                  >
                    {selectedLearnerIds.length === filteredLearners.length
                      ? "Deselect All"
                      : "Select All"}
                  </button>
                )}
              </div>

              {/* Learners List */}
              <div className="flex-1 overflow-y-auto space-y-2 pr-1 min-h-[220px]">
                {filteredLearners.length === 0 ? (
                  <div className="p-8 text-center text-xs text-slate-400">
                    No eligible officials / learners found.
                  </div>
                ) : (
                  filteredLearners.map((learner) => {
                    const lid = learner.id || (learner as any)._id;
                    const isSelected = selectedLearnerIds.includes(lid);

                    return (
                      <div
                        key={lid}
                        onClick={() => handleToggleLearner(lid)}
                        className={`flex items-center justify-between rounded-xl border p-3 cursor-pointer transition-all ${
                          isSelected
                            ? "border-orange-300 bg-orange-50/50 shadow-sm"
                            : "border-slate-100 bg-slate-50/50 hover:bg-slate-50"
                        }`}
                      >
                        <div className="flex items-center gap-3">
                          <input
                            type="checkbox"
                            checked={isSelected}
                            onChange={() => {}}
                            className="h-4 w-4 rounded border-slate-300 accent-[#ef7e37]"
                          />
                          <div>
                            <div className="text-xs font-bold text-slate-800">
                              {learner.full_name}
                            </div>
                            <div className="text-[11px] text-slate-400">
                              {learner.email} · {learner.designation || learner.department || "Officer"}
                            </div>
                          </div>
                        </div>

                        <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 bg-white px-2 py-0.5 rounded border border-slate-200">
                          {learner.access_role || "OFFICIAL"}
                        </span>
                      </div>
                    );
                  })
                )}
              </div>

              {/* Actions */}
              <div className="border-t border-slate-100 pt-4 flex items-center justify-between">
                <span className="text-xs font-bold text-slate-600">
                  {selectedLearnerIds.length} learners selected
                </span>

                <div className="flex items-center gap-2">
                  <button
                    type="button"
                    onClick={() => setAssignModalOpen(false)}
                    className="rounded-xl border border-slate-200 px-4 py-2 text-xs font-bold text-slate-600"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={submittingAssign || selectedLearnerIds.length === 0}
                    className="rounded-xl bg-[#ef7e37] px-5 py-2 text-xs font-bold text-white shadow hover:bg-[#d96a27] disabled:opacity-50"
                  >
                    {submittingAssign ? "Assigning..." : "Confirm Assignment"}
                  </button>
                </div>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* ── Preview Modal ── */}
      {previewModalOpen && previewingQuiz && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4 backdrop-blur-sm animate-fadeIn">
          <div className="relative w-full max-w-2xl rounded-3xl bg-white p-6 shadow-2xl border border-[#f0ddd0] max-h-[90vh] overflow-y-auto space-y-6">
            <div className="flex items-center justify-between border-b border-slate-100 pb-4">
              <div>
                <span className="rounded bg-orange-50 px-2 py-0.5 text-[10px] font-bold text-[#c2510e]">
                  {previewingQuiz.competency_code}
                </span>
                <h3 className="text-lg font-extrabold text-slate-800 mt-1">
                  {previewingQuiz.title}
                </h3>
              </div>
              <button
                onClick={() => setPreviewModalOpen(false)}
                className="rounded-full p-1 text-slate-400 hover:bg-slate-100"
              >
                <X size={18} />
              </button>
            </div>

            {/* Questions List */}
            <div className="space-y-4">
              {previewingQuiz.questions && previewingQuiz.questions.length > 0 ? (
                previewingQuiz.questions.map((q, idx) => (
                  <div key={idx} className="rounded-2xl border border-slate-200 bg-slate-50/50 p-4 space-y-2">
                    <div className="text-xs font-bold text-slate-400 uppercase">
                      Question #{idx + 1}
                    </div>
                    <p className="text-xs font-bold text-slate-800">{q.question}</p>
                    <div className="grid gap-1.5 sm:grid-cols-2 pt-1">
                      {q.options &&
                        q.options.map((opt, optIdx) => {
                          const letter = String.fromCharCode(65 + optIdx);
                          const isCorrect = letter === q.correct_answer;
                          return (
                            <div
                              key={optIdx}
                              className={`rounded-lg border px-2.5 py-1.5 text-xs flex items-center gap-2 ${
                                isCorrect
                                  ? "border-emerald-300 bg-emerald-50 text-emerald-800 font-bold"
                                  : "border-slate-200 bg-white text-slate-600"
                              }`}
                            >
                              <span className="font-black">{letter}.</span> {opt}
                            </div>
                          );
                        })}
                    </div>
                  </div>
                ))
              ) : (
                <div className="text-center py-6 text-xs text-slate-400">
                  No questions loaded in preview.
                </div>
              )}
            </div>

            <div className="border-t border-slate-100 pt-4 flex justify-end">
              <button
                onClick={() => setPreviewModalOpen(false)}
                className="rounded-xl bg-slate-800 px-5 py-2 text-xs font-bold text-white"
              >
                Close Preview
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default TrainerQuizStudio;
