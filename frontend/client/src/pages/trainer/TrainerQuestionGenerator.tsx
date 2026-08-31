import React, { useEffect, useState } from "react";
import {
  BookOpen,
  Sparkles,
  Sliders,
  CheckCircle2,
  FileQuestion,
  HelpCircle,
  ArrowRight,
  RefreshCw,
  Layers,
  Award,
} from "lucide-react";
import { api, LearningMaterial, TrainerQuestion } from "@/lib/api";
import { toast } from "sonner";

interface TrainerQuestionGeneratorProps {
  initialMaterialId?: string;
  onNavigate: (page: string, context?: { materialId?: string }) => void;
}

const COMPETENCIES = [
  { code: "STAT_SAMPLING", name: "Statistical Sampling & Survey Design" },
  { code: "TECH_PYTHON", name: "Python Programming for Public Service" },
  { code: "DATA_ANALYSIS", name: "Data Analysis & Visual Analytics" },
  { code: "CYBER_SEC", name: "Cybersecurity & Information Security" },
  { code: "CIVIL_GOV", name: "Civil Governance & Regulatory Frameworks" },
  { code: "PUBLIC_PROCUREMENT", name: "Government e-Marketplace (GeM) & Procurement" },
];

export function TrainerQuestionGenerator({
  initialMaterialId,
  onNavigate,
}: TrainerQuestionGeneratorProps) {
  const [materials, setMaterials] = useState<LearningMaterial[]>([]);
  const [loadingMaterials, setLoadingMaterials] = useState(true);

  // Form state
  const [selectedMaterialId, setSelectedMaterialId] = useState(initialMaterialId || "");
  const [competencyCode, setCompetencyCode] = useState("STAT_SAMPLING");
  const [questionCount, setQuestionCount] = useState(3);
  const [difficulty, setDifficulty] = useState("MEDIUM");

  // Generation state
  const [generating, setGenerating] = useState(false);
  const [generationStep, setGenerationStep] = useState(0);
  const [generatedQuestions, setGeneratedQuestions] = useState<TrainerQuestion[]>([]);

  useEffect(() => {
    async function loadMaterials() {
      try {
        setLoadingMaterials(true);
        const list = await api.trainer.materials.list();
        const readyMaterials = list.filter((m) => m.status === "READY");
        setMaterials(readyMaterials);

        if (!selectedMaterialId && readyMaterials.length > 0) {
          setSelectedMaterialId(readyMaterials[0].id || (readyMaterials[0] as any)._id);
        }
      } catch (err: any) {
        toast.error(err.message || "Failed to load materials");
      } finally {
        setLoadingMaterials(false);
      }
    }
    loadMaterials();
  }, []);

  const handleGenerate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedMaterialId) {
      toast.error("Please select a learning material.");
      return;
    }

    try {
      setGenerating(true);
      setGeneratedQuestions([]);
      setGenerationStep(1);

      // Visual progress simulator for multi-step RAG
      const stepTimer1 = setTimeout(() => setGenerationStep(2), 700);
      const stepTimer2 = setTimeout(() => setGenerationStep(3), 1500);

      const result = await api.trainer.materials.generateQuestions(selectedMaterialId, {
        competency_code: competencyCode,
        question_count: questionCount,
        difficulty,
      });

      clearTimeout(stepTimer1);
      clearTimeout(stepTimer2);
      setGenerationStep(4);
      setGeneratedQuestions(result);
      toast.success(`Successfully generated ${result.length} questions! Ready for review.`);
    } catch (err: any) {
      toast.error(err.message || "Question generation failed");
      setGenerationStep(0);
    } finally {
      setGenerating(false);
    }
  };

  const selectedMaterial = materials.find(
    (m) => (m.id || (m as any)._id) === selectedMaterialId
  );

  return (
    <div className="space-y-8 animate-fadeIn max-w-4xl mx-auto">
      {/* Top Title Banner */}
      <div className="rounded-3xl border border-[#f0ddd0] bg-white p-6 sm:p-8 shadow-sm">
        <div className="flex items-center gap-3 text-[#ef7e37]">
          <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-orange-50 text-[#ef7e37]">
            <Sparkles size={22} />
          </div>
          <div>
            <h1 className="text-2xl font-black text-slate-800">
              AI Assessment Question Generator
            </h1>
            <p className="text-xs text-slate-400 mt-0.5">
              RAG-grounded question synthesis from uploaded curriculum documents
            </p>
          </div>
        </div>

        {/* Generator Form */}
        <form onSubmit={handleGenerate} className="mt-8 space-y-6">
          <div className="grid gap-6 sm:grid-cols-2">
            {/* 1. Material Selector */}
            <div className="sm:col-span-2 space-y-2">
              <label className="block text-xs font-bold uppercase tracking-wider text-slate-500">
                1. Select Source Material
              </label>
              {loadingMaterials ? (
                <div className="h-12 rounded-xl bg-slate-100 animate-pulse" />
              ) : materials.length === 0 ? (
                <div className="rounded-xl border border-dashed border-amber-200 bg-amber-50/50 p-4 text-xs text-amber-800">
                  No processed materials available.{" "}
                  <button
                    type="button"
                    onClick={() => onNavigate("Upload Material")}
                    className="font-bold underline text-[#ef7e37]"
                  >
                    Upload a curriculum document first
                  </button>
                  .
                </div>
              ) : (
                <select
                  value={selectedMaterialId}
                  onChange={(e) => setSelectedMaterialId(e.target.value)}
                  className="w-full rounded-xl border border-[#f0ddd0] bg-white px-4 py-3 text-sm font-semibold text-slate-800 focus:border-[#ef7e37] focus:outline-none shadow-sm"
                >
                  {materials.map((m) => (
                    <option key={m.id || (m as any)._id} value={m.id || (m as any)._id}>
                      {m.original_filename || m.filename} ({m.chunk_count || 0} chunks)
                    </option>
                  ))}
                </select>
              )}
              {selectedMaterial && (
                <div className="text-[11px] text-slate-400 flex items-center gap-2 mt-1">
                  <BookOpen size={12} />
                  <span>
                    Indexed document with {selectedMaterial.chunk_count || 0} semantic chunks ready for retrieval.
                  </span>
                </div>
              )}
            </div>

            {/* 2. Target Competency */}
            <div className="space-y-2">
              <label className="block text-xs font-bold uppercase tracking-wider text-slate-500">
                2. Target Competency
              </label>
              <select
                value={competencyCode}
                onChange={(e) => setCompetencyCode(e.target.value)}
                className="w-full rounded-xl border border-[#f0ddd0] bg-white px-4 py-3 text-sm font-semibold text-slate-800 focus:border-[#ef7e37] focus:outline-none shadow-sm"
              >
                {COMPETENCIES.map((c) => (
                  <option key={c.code} value={c.code}>
                    {c.code} — {c.name}
                  </option>
                ))}
              </select>
            </div>

            {/* 3. Difficulty Level */}
            <div className="space-y-2">
              <label className="block text-xs font-bold uppercase tracking-wider text-slate-500">
                3. Difficulty Level
              </label>
              <div className="grid grid-cols-3 gap-2">
                {["EASY", "MEDIUM", "HARD"].map((diff) => (
                  <button
                    type="button"
                    key={diff}
                    onClick={() => setDifficulty(diff)}
                    className={`rounded-xl border py-2.5 text-xs font-bold transition-all ${
                      difficulty === diff
                        ? "border-[#ef7e37] bg-[#fff2e8] text-[#c2510e] shadow-sm"
                        : "border-[#f0ddd0] bg-white text-slate-500 hover:bg-orange-50"
                    }`}
                  >
                    {diff}
                  </button>
                ))}
              </div>
            </div>

            {/* 4. Question Count */}
            <div className="sm:col-span-2 space-y-2">
              <div className="flex items-center justify-between">
                <label className="block text-xs font-bold uppercase tracking-wider text-slate-500">
                  4. Number of Questions
                </label>
                <span className="text-sm font-black text-[#c2510e]">
                  {questionCount} Questions
                </span>
              </div>
              <input
                type="range"
                min="1"
                max="10"
                value={questionCount}
                onChange={(e) => setQuestionCount(parseInt(e.target.value))}
                className="w-full accent-[#ef7e37] cursor-pointer"
              />
              <div className="flex justify-between text-[10px] font-bold text-slate-400">
                <span>1 item (Rapid test)</span>
                <span>5 items (Standard)</span>
                <span>10 items (Comprehensive)</span>
              </div>
            </div>
          </div>

          {/* Trigger Button */}
          <div className="border-t border-slate-100 pt-6">
            <button
              type="submit"
              disabled={generating || materials.length === 0}
              className="w-full flex items-center justify-center gap-2 rounded-2xl bg-[#ef7e37] py-3.5 text-sm font-bold text-white shadow-md hover:bg-[#d96a27] disabled:opacity-50 transition-all transform active:scale-98"
            >
              {generating ? (
                <>
                  <RefreshCw size={18} className="animate-spin" />
                  Generating Grounded MCQs ({generationStep}/3)...
                </>
              ) : (
                <>
                  <Sparkles size={18} /> Generate Questions with AI
                </>
              )}
            </button>
          </div>
        </form>
      </div>

      {/* Generation Status Visualizer */}
      {generating && (
        <div className="rounded-3xl border border-orange-200 bg-orange-50/40 p-6 animate-fadeIn">
          <h3 className="text-sm font-bold text-slate-800 mb-4 flex items-center gap-2">
            <RefreshCw size={16} className="animate-spin text-[#ef7e37]" />
            RAG Pipeline Execution in Progress
          </h3>
          <div className="space-y-3">
            <div className={`flex items-center gap-3 text-xs ${generationStep >= 1 ? "text-emerald-700 font-bold" : "text-slate-400"}`}>
              <CheckCircle2 size={16} className={generationStep >= 1 ? "text-emerald-600" : "text-slate-300"} />
              1. Retrieving semantic chunks from vector index
            </div>
            <div className={`flex items-center gap-3 text-xs ${generationStep >= 2 ? "text-emerald-700 font-bold" : "text-slate-400"}`}>
              <CheckCircle2 size={16} className={generationStep >= 2 ? "text-emerald-600" : "text-slate-300"} />
              2. Prompting generative LLM with strict grounding constraints
            </div>
            <div className={`flex items-center gap-3 text-xs ${generationStep >= 3 ? "text-emerald-700 font-bold" : "text-slate-400"}`}>
              <CheckCircle2 size={16} className={generationStep >= 3 ? "text-emerald-600" : "text-slate-300"} />
              3. Running automated grounding validation & persisting to review pool
            </div>
          </div>
        </div>
      )}

      {/* Generated Questions Results Container */}
      {generatedQuestions.length > 0 && (
        <div className="rounded-3xl border border-emerald-200 bg-emerald-50/40 p-6 sm:p-8 animate-fadeIn space-y-6">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-emerald-200/60 pb-4">
            <div>
              <div className="inline-flex items-center gap-1.5 rounded-full bg-emerald-100 px-3 py-1 text-xs font-bold text-emerald-800">
                <CheckCircle2 size={14} /> Batch Generation Complete
              </div>
              <h2 className="text-xl font-extrabold text-slate-800 mt-2">
                {generatedQuestions.length} Questions Generated (Status: GENERATED)
              </h2>
              <p className="text-xs text-slate-500 mt-0.5">
                Questions have been added to your Review Studio. Audit and approve them before adding to quizzes.
              </p>
            </div>
            <button
              onClick={() => onNavigate("Question Review", { materialId: selectedMaterialId })}
              className="inline-flex items-center gap-2 rounded-xl bg-emerald-600 px-5 py-2.5 text-xs font-bold text-white shadow hover:bg-emerald-700 transition-all"
            >
              Open Question Review Studio <ArrowRight size={14} />
            </button>
          </div>

          {/* Quick List Preview */}
          <div className="space-y-4">
            {generatedQuestions.map((q, idx) => (
              <div
                key={q.id || (q as any)._id || idx}
                className="rounded-2xl border border-emerald-100 bg-white p-5 shadow-sm space-y-3"
              >
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-slate-400 uppercase tracking-wider">
                    Question #{idx + 1}
                  </span>
                  <span className="rounded-full bg-amber-100 px-2.5 py-0.5 text-[10px] font-bold text-amber-800">
                    GENERATED (Pending Review)
                  </span>
                </div>
                <p className="text-sm font-bold text-slate-800">{q.question}</p>

                <div className="grid gap-2 sm:grid-cols-2 pt-2">
                  {q.options.map((opt, optIdx) => {
                    const optLetter = String.fromCharCode(65 + optIdx);
                    const isCorrect = optLetter === q.correct_answer;
                    return (
                      <div
                        key={optIdx}
                        className={`rounded-xl border px-3 py-2 text-xs flex items-center gap-2 ${
                          isCorrect
                            ? "border-emerald-300 bg-emerald-50/50 font-bold text-emerald-800"
                            : "border-slate-100 bg-slate-50 text-slate-600"
                        }`}
                      >
                        <span className={`flex h-5 w-5 items-center justify-center rounded-full text-[10px] font-bold ${
                          isCorrect ? "bg-emerald-600 text-white" : "bg-slate-200 text-slate-600"
                        }`}>
                          {optLetter}
                        </span>
                        <span>{opt}</span>
                      </div>
                    );
                  })}
                </div>

                <div className="text-xs text-slate-500 bg-slate-50 p-3 rounded-xl border border-slate-100">
                  <strong className="text-slate-700">Explanation:</strong> {q.explanation}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

export default TrainerQuestionGenerator;
