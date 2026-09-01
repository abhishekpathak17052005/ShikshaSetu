import React, { useState } from "react";
import {
  BookOpen,
  CheckCircle2,
  Clock,
  Award,
  ArrowRight,
  ArrowLeft,
  Sparkles,
  FileQuestion,
  Lightbulb,
  Building2,
  Bookmark,
  Share2,
  X,
  Play,
  Check,
} from "lucide-react";
import {
  getCourseCurriculum,
  CourseCurriculumData,
  CourseModuleChapter,
} from "@/lib/courseContent";
import { toast } from "sonner";

interface CourseViewerModalProps {
  isOpen: boolean;
  onClose: () => void;
  competencyCode?: string;
  resourceTitle?: string;
  onLaunchQuiz?: (competencyCode: string) => void;
  onCompleteActivity?: () => void;
}

export function CourseViewerModal({
  isOpen,
  onClose,
  competencyCode,
  resourceTitle,
  onLaunchQuiz,
  onCompleteActivity,
}: CourseViewerModalProps) {
  if (!isOpen) return null;

  const curriculum: CourseCurriculumData = getCourseCurriculum(
    competencyCode,
    resourceTitle
  );

  const [activeChapterIndex, setActiveChapterIndex] = useState(0);
  const [completedChapters, setCompletedChapters] = useState<number[]>([0]);
  const [userNotes, setUserNotes] = useState("");
  const [notesSaved, setNotesSaved] = useState(false);

  const currentChapter: CourseModuleChapter =
    curriculum.chapters[activeChapterIndex] || curriculum.chapters[0];

  const handleNextChapter = () => {
    if (activeChapterIndex < curriculum.chapters.length - 1) {
      const nextIdx = activeChapterIndex + 1;
      setActiveChapterIndex(nextIdx);
      if (!completedChapters.includes(nextIdx)) {
        setCompletedChapters([...completedChapters, nextIdx]);
      }
    }
  };

  const handlePrevChapter = () => {
    if (activeChapterIndex > 0) {
      setActiveChapterIndex(activeChapterIndex - 1);
    }
  };

  const handleSaveNotes = () => {
    if (!userNotes.trim()) return;
    setNotesSaved(true);
    toast.success("Study notes saved to your official learning journal.");
    setTimeout(() => setNotesSaved(false), 2500);
  };

  const progressPercent = Math.round(
    (completedChapters.length / curriculum.chapters.length) * 100
  );

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 p-4 backdrop-blur-sm animate-fadeIn">
      <div className="relative flex max-h-[92vh] w-full max-w-5xl flex-col overflow-hidden rounded-3xl border border-[#dfe7f0] bg-white shadow-2xl">
        {/* Top Header */}
        <div className="flex items-center justify-between border-b border-slate-100 bg-[#f7fafc] px-6 py-4">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-teal-50 text-[#087f76]">
              <BookOpen size={20} />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="rounded-full bg-[#123057] px-2.5 py-0.5 text-[10px] font-extrabold uppercase text-white">
                  {curriculum.provider}
                </span>
                <span className="rounded-md bg-teal-100/80 px-2 py-0.5 text-[10px] font-bold text-teal-800">
                  {curriculum.competencyCode}
                </span>
                <span className="flex items-center gap-1 text-[11px] font-medium text-slate-400">
                  <Clock size={12} /> {curriculum.estimatedTime}
                </span>
              </div>
              <h2 className="text-lg font-black text-[#123057] line-clamp-1 mt-0.5">
                {curriculum.title}
              </h2>
            </div>
          </div>

          <div className="flex items-center gap-3">
            {onLaunchQuiz && (
              <button
                onClick={() => {
                  onClose();
                  onLaunchQuiz(curriculum.competencyCode);
                }}
                className="hidden sm:inline-flex items-center gap-2 rounded-xl bg-[#ef7e37] px-3.5 py-2 text-xs font-bold text-white shadow-sm hover:bg-[#d96a27] transition"
              >
                <FileQuestion size={14} /> Attempt Practice Quiz
              </button>
            )}
            <button
              onClick={onClose}
              className="flex h-9 w-9 items-center justify-center rounded-xl text-slate-400 hover:bg-slate-200 hover:text-slate-700 transition"
            >
              <X size={18} />
            </button>
          </div>
        </div>

        {/* Learning Progress Bar */}
        <div className="h-1.5 w-full bg-slate-100">
          <div
            className="h-full bg-gradient-to-r from-teal-500 to-[#ef7e37] transition-all duration-300"
            style={{ width: `${progressPercent}%` }}
          />
        </div>

        {/* Main Content Layout */}
        <div className="grid flex-1 overflow-hidden md:grid-cols-[280px_1fr]">
          {/* Sidebar Navigation */}
          <div className="border-r border-slate-100 bg-slate-50/50 p-5 overflow-y-auto hidden md:block space-y-4">
            <div>
              <div className="text-[10px] font-black uppercase tracking-wider text-slate-400 mb-2">
                Course Curriculum ({curriculum.chapters.length} Chapters)
              </div>
              <div className="space-y-1.5">
                {curriculum.chapters.map((ch, idx) => {
                  const isActive = idx === activeChapterIndex;
                  const isDone = completedChapters.includes(idx);

                  return (
                    <button
                      key={ch.id}
                      onClick={() => setActiveChapterIndex(idx)}
                      className={`flex w-full items-start gap-2.5 rounded-xl p-3 text-left transition ${
                        isActive
                          ? "bg-white border border-[#dfe7f0] shadow-sm text-[#123057]"
                          : "text-slate-600 hover:bg-white/60 hover:text-slate-900"
                      }`}
                    >
                      <div
                        className={`mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded-full text-[10px] font-bold ${
                          isDone
                            ? "bg-teal-600 text-white"
                            : "bg-slate-200 text-slate-600"
                        }`}
                      >
                        {isDone ? <Check size={11} /> : idx + 1}
                      </div>
                      <div>
                        <div className="text-xs font-bold leading-snug line-clamp-2">
                          {ch.title}
                        </div>
                        <div className="text-[10px] text-slate-400 mt-0.5">
                          {ch.duration}
                        </div>
                      </div>
                    </button>
                  );
                })}
              </div>
            </div>

            {/* Quick Action Box */}
            <div className="rounded-2xl border border-teal-100 bg-teal-50/60 p-4 space-y-2">
              <div className="flex items-center gap-1.5 text-xs font-bold text-teal-800">
                <Sparkles size={14} className="text-[#ef7e37]" /> Practice Ready
              </div>
              <p className="text-[11px] text-slate-600 leading-relaxed">
                Test yourself with grounded MCQs to record supporting evidence.
              </p>
              {onLaunchQuiz && (
                <button
                  onClick={() => {
                    onClose();
                    onLaunchQuiz(curriculum.competencyCode);
                  }}
                  className="w-full mt-1 flex items-center justify-center gap-1.5 rounded-xl bg-[#087f76] py-2 text-xs font-bold text-white hover:bg-teal-700 transition"
                >
                  Start Quiz <ArrowRight size={13} />
                </button>
              )}
            </div>
          </div>

          {/* Chapter Content Reader */}
          <div className="overflow-y-auto p-6 sm:p-8 space-y-6">
            {/* Chapter Header */}
            <div className="border-b border-slate-100 pb-5">
              <div className="flex items-center gap-2 text-xs font-bold text-[#087f76]">
                <Clock size={13} /> Chapter {activeChapterIndex + 1} of{" "}
                {curriculum.chapters.length} ({currentChapter.duration})
              </div>
              <h1 className="text-2xl font-black text-[#123057] mt-1">
                {currentChapter.title}
              </h1>
              <p className="text-sm font-medium text-slate-500 mt-2 leading-relaxed">
                {currentChapter.summary}
              </p>
            </div>

            {/* Lesson Body */}
            <div className="space-y-4">
              <h3 className="text-xs font-black uppercase tracking-wider text-slate-400">
                Core Lesson & Policy Framework
              </h3>
              <div className="space-y-3">
                {currentChapter.content.map((paragraph, pIdx) => (
                  <p
                    key={pIdx}
                    className="text-sm text-slate-700 leading-relaxed rounded-xl bg-slate-50/70 p-4 border border-slate-100"
                  >
                    {paragraph}
                  </p>
                ))}
              </div>
            </div>

            {/* Key Takeaways Card */}
            <div className="rounded-2xl border border-amber-200/80 bg-amber-50/60 p-5 space-y-3">
              <div className="flex items-center gap-2 text-xs font-bold text-amber-900">
                <Lightbulb size={16} className="text-amber-600" /> Key Governance Takeaways
              </div>
              <ul className="space-y-2">
                {currentChapter.keyTakeaways.map((takeaway, tIdx) => (
                  <li
                    key={tIdx}
                    className="flex items-start gap-2 text-xs text-amber-950 leading-relaxed font-medium"
                  >
                    <CheckCircle2 size={14} className="text-teal-600 shrink-0 mt-0.5" />
                    <span>{takeaway}</span>
                  </li>
                ))}
              </ul>
            </div>

            {/* Practical Case Study (if present) */}
            {currentChapter.practicalCaseStudy && (
              <div className="rounded-2xl border border-blue-100 bg-blue-50/50 p-5 space-y-3">
                <div className="flex items-center gap-2 text-xs font-bold text-[#123057]">
                  <Building2 size={16} className="text-[#087f76]" /> Practical Public Service Case Study: {currentChapter.practicalCaseStudy.title}
                </div>
                <div className="grid gap-3 text-xs sm:grid-cols-3">
                  <div className="rounded-xl bg-white p-3 border border-slate-100">
                    <div className="font-bold text-slate-400 uppercase text-[10px]">Scenario</div>
                    <div className="text-slate-700 mt-1">{currentChapter.practicalCaseStudy.scenario}</div>
                  </div>
                  <div className="rounded-xl bg-white p-3 border border-slate-100">
                    <div className="font-bold text-slate-400 uppercase text-[10px]">Action Taken</div>
                    <div className="text-slate-700 mt-1">{currentChapter.practicalCaseStudy.actionTaken}</div>
                  </div>
                  <div className="rounded-xl bg-white p-3 border border-slate-100">
                    <div className="font-bold text-teal-700 uppercase text-[10px]">Impact</div>
                    <div className="text-slate-700 mt-1 font-semibold">{currentChapter.practicalCaseStudy.impact}</div>
                  </div>
                </div>
              </div>
            )}

            {/* Study Notes Input */}
            <div className="rounded-2xl border border-slate-200 bg-white p-4 space-y-2.5">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-1.5 text-xs font-bold text-slate-700">
                  <Bookmark size={14} className="text-teal-600" /> Personal Learning Notes
                </div>
                <button
                  onClick={handleSaveNotes}
                  className="text-xs font-bold text-[#087f76] hover:underline"
                >
                  {notesSaved ? "✓ Notes Saved" : "Save Notes"}
                </button>
              </div>
              <textarea
                value={userNotes}
                onChange={(e) => setUserNotes(e.target.value)}
                placeholder="Write key learnings or questions for review..."
                rows={2}
                className="w-full rounded-xl border border-slate-200 p-3 text-xs text-slate-800 placeholder-slate-400 focus:border-[#087f76] focus:outline-none"
              />
            </div>
          </div>
        </div>

        {/* Footer Navigation */}
        <div className="flex items-center justify-between border-t border-slate-100 bg-[#f7fafc] px-6 py-4">
          <button
            onClick={handlePrevChapter}
            disabled={activeChapterIndex === 0}
            className="flex items-center gap-1.5 rounded-xl border border-slate-200 bg-white px-4 py-2 text-xs font-bold text-slate-700 hover:bg-slate-50 disabled:opacity-40 transition"
          >
            <ArrowLeft size={14} /> Previous Chapter
          </button>

          <div className="flex items-center gap-3">
            {activeChapterIndex < curriculum.chapters.length - 1 ? (
              <button
                onClick={handleNextChapter}
                className="flex items-center gap-1.5 rounded-xl bg-[#087f76] px-5 py-2.5 text-xs font-bold text-white shadow-sm hover:bg-teal-700 transition"
              >
                Next Chapter <ArrowRight size={14} />
              </button>
            ) : (
              <div className="flex items-center gap-2">
                {onCompleteActivity && (
                  <button
                    onClick={() => {
                      onCompleteActivity();
                      onClose();
                    }}
                    className="flex items-center gap-1.5 rounded-xl bg-emerald-600 px-4 py-2.5 text-xs font-bold text-white shadow-sm hover:bg-emerald-700 transition"
                  >
                    <CheckCircle2 size={14} /> Complete Module (+100%)
                  </button>
                )}
                {onLaunchQuiz && (
                  <button
                    onClick={() => {
                      onClose();
                      onLaunchQuiz(curriculum.competencyCode);
                    }}
                    className="flex items-center gap-1.5 rounded-xl bg-[#ef7e37] px-5 py-2.5 text-xs font-bold text-white shadow-sm hover:bg-[#d96a27] transition"
                  >
                    <FileQuestion size={14} /> Launch Practice Quiz <ArrowRight size={14} />
                  </button>
                )}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
