import React, { useEffect, useState, useRef } from "react";
import {
  BookOpen,
  FilePlus,
  FileText,
  FileQuestion,
  Search,
  CheckCircle,
  AlertCircle,
  Clock,
  ArrowRight,
  Upload,
  X,
  RefreshCw,
  Layers,
} from "lucide-react";
import { api, clearApiCache, LearningMaterial } from "@/lib/api";
import { toast } from "sonner";

interface TrainerMaterialsProps {
  onNavigate: (page: string, context?: { materialId?: string }) => void;
}

export function TrainerMaterials({ onNavigate }: TrainerMaterialsProps) {
  const [materials, setMaterials] = useState<LearningMaterial[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");
  const [uploadModalOpen, setUploadModalOpen] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const fetchMaterials = async () => {
    clearApiCache();
    try {
      setLoading(true);
      const list = await api.trainer.materials.list();
      setMaterials(list);
    } catch (err: any) {
      toast.error(err.message || "Failed to load materials");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchMaterials();
  }, []);

  const handleFileDrop = (e: React.DragEvent) => {
    e.preventDefault();
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      validateAndSetFile(e.dataTransfer.files[0]);
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      validateAndSetFile(e.target.files[0]);
    }
  };

  const validateAndSetFile = (file: File) => {
    const validTypes = [
      "application/pdf",
      "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
      "text/plain",
    ];
    const validExts = [".pdf", ".docx", ".txt"];
    const ext = file.name.substring(file.name.lastIndexOf(".")).toLowerCase();

    if (!validTypes.includes(file.type) && !validExts.includes(ext)) {
      toast.error("Invalid file format. Please upload PDF, DOCX, or TXT documents.");
      return;
    }

    if (file.size > 25 * 1024 * 1024) {
      toast.error("File size exceeds 25MB limit.");
      return;
    }

    setSelectedFile(file);
  };

  const handleUploadSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedFile) {
      toast.error("Please select a file to upload.");
      return;
    }

    try {
      setUploading(true);
      await api.trainer.materials.upload(selectedFile);
      toast.success(`"${selectedFile.name}" uploaded successfully! Chunks extracted.`);
      setSelectedFile(null);
      setUploadModalOpen(false);
      fetchMaterials();
    } catch (err: any) {
      toast.error(err.message || "Upload failed");
    } finally {
      setUploading(false);
    }
  };

  const filteredMaterials = materials.filter((m) => {
    const term = searchQuery.toLowerCase();
    return (
      (m.original_filename && m.original_filename.toLowerCase().includes(term)) ||
      (m.filename && m.filename.toLowerCase().includes(term))
    );
  });

  return (
    <div className="space-y-6 animate-fadeIn">
      {/* Top action header */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-black text-slate-800">Learning Materials Library</h1>
          <p className="text-sm text-slate-500 mt-1">
            Curriculum content repositories used for grounded AI question generation.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={fetchMaterials}
            className="flex items-center gap-1.5 rounded-xl border border-[#f0ddd0] bg-white px-3.5 py-2.5 text-xs font-bold text-slate-600 hover:bg-orange-50 transition-colors"
            title="Refresh list"
          >
            <RefreshCw size={14} className={loading ? "animate-spin" : ""} />
            Refresh
          </button>
          <button
            onClick={() => setUploadModalOpen(true)}
            className="flex items-center gap-2 rounded-xl bg-[#ef7e37] px-4 py-2.5 text-sm font-bold text-white shadow-md hover:bg-[#d96a27] transition-all transform active:scale-95"
          >
            <FilePlus size={16} />
            Upload New Material
          </button>
        </div>
      </div>

      {/* Search & Filters */}
      <div className="flex items-center gap-3 rounded-2xl border border-[#f0ddd0] bg-white p-3 shadow-sm">
        <Search size={18} className="text-slate-400 ml-2" />
        <input
          type="text"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          placeholder="Search materials by title or filename..."
          className="w-full bg-transparent text-sm text-slate-800 placeholder-slate-400 focus:outline-none"
        />
        {searchQuery && (
          <button
            onClick={() => setSearchQuery("")}
            className="text-xs text-slate-400 hover:text-slate-600 mr-2"
          >
            Clear
          </button>
        )}
      </div>

      {/* Materials Grid / Table */}
      {loading ? (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {[1, 2, 3].map((n) => (
            <div
              key={n}
              className="h-44 rounded-2xl border border-slate-200 bg-white p-5 animate-pulse"
            />
          ))}
        </div>
      ) : filteredMaterials.length === 0 ? (
        <div className="rounded-2xl border border-dashed border-[#f0ddd0] bg-white p-12 text-center">
          <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-orange-50 text-[#ef7e37]">
            <BookOpen size={24} />
          </div>
          <h3 className="mt-4 text-base font-bold text-slate-800">No learning materials found</h3>
          <p className="mt-1 text-sm text-slate-500 max-w-md mx-auto">
            {searchQuery
              ? "No materials matched your search query."
              : "Upload government curriculum documents (PDF, DOCX, TXT) to start generating AI assessments."}
          </p>
          <button
            onClick={() => setUploadModalOpen(true)}
            className="mt-5 inline-flex items-center gap-2 rounded-xl bg-[#ef7e37] px-4 py-2.5 text-xs font-bold text-white hover:bg-[#d96a27] transition-colors"
          >
            <Upload size={14} /> Upload First Document
          </button>
        </div>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {filteredMaterials.map((mat) => {
            const isReady = mat.status === "READY";
            const isProcessing = mat.status === "PROCESSING" || mat.status === "UPLOADED";

            return (
              <div
                key={mat.id || (mat as any)._id}
                className="flex flex-col justify-between rounded-2xl border border-[#f0ddd0] bg-white p-5 shadow-sm hover:border-orange-300 hover:shadow-md transition-all group"
              >
                <div>
                  {/* Status & Type */}
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-orange-50 text-[#ef7e37]">
                        <FileText size={16} />
                      </div>
                      <span className="text-xs font-bold text-slate-400 uppercase tracking-wider">
                        Document
                      </span>
                    </div>

                    {isReady ? (
                      <span className="inline-flex items-center gap-1 rounded-full bg-emerald-50 px-2.5 py-0.5 text-[11px] font-bold text-emerald-700">
                        <CheckCircle size={12} /> Ready
                      </span>
                    ) : isProcessing ? (
                      <span className="inline-flex items-center gap-1 rounded-full bg-amber-50 px-2.5 py-0.5 text-[11px] font-bold text-amber-700">
                        <Clock size={12} className="animate-spin" /> Processing
                      </span>
                    ) : (
                      <span className="inline-flex items-center gap-1 rounded-full bg-rose-50 px-2.5 py-0.5 text-[11px] font-bold text-rose-700">
                        <AlertCircle size={12} /> Failed
                      </span>
                    )}
                  </div>

                  {/* Title & info */}
                  <h3
                    className="mt-3 text-base font-bold text-slate-800 line-clamp-2 group-hover:text-[#c2510e] transition-colors"
                    title={mat.original_filename || mat.filename}
                  >
                    {mat.original_filename || mat.filename}
                  </h3>

                  <div className="mt-4 flex items-center gap-4 text-xs font-semibold text-slate-400">
                    <span className="flex items-center gap-1">
                      <Layers size={13} className="text-slate-400" />
                      {mat.chunk_count || 0} chunks
                    </span>
                    <span>·</span>
                    <span>
                      {mat.created_at
                        ? new Date(mat.created_at).toLocaleDateString()
                        : "Recent"}
                    </span>
                  </div>
                </div>

                {/* Card actions */}
                <div className="mt-5 border-t border-slate-100 pt-4 flex items-center justify-between gap-2">
                  <button
                    onClick={() =>
                      onNavigate("AI Question Generator", { materialId: mat.id || (mat as any)._id })
                    }
                    disabled={!isReady}
                    className="flex-1 inline-flex items-center justify-center gap-1.5 rounded-xl bg-orange-50 px-3 py-2 text-xs font-bold text-[#c2510e] hover:bg-orange-100 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                  >
                    <FileQuestion size={14} /> Generate MCQs
                  </button>

                  <button
                    onClick={() =>
                      onNavigate("Question Review", { materialId: mat.id || (mat as any)._id })
                    }
                    className="inline-flex items-center justify-center rounded-xl border border-slate-200 px-3 py-2 text-xs font-bold text-slate-600 hover:bg-slate-50 transition-colors"
                    title="View all questions generated from this material"
                  >
                    Questions →
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* ── Upload Modal ── */}
      {uploadModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4 backdrop-blur-sm animate-fadeIn">
          <div className="relative w-full max-w-lg rounded-3xl bg-white p-6 shadow-2xl border border-[#f0ddd0]">
            <div className="flex items-center justify-between border-b border-slate-100 pb-4">
              <div>
                <h3 className="text-lg font-extrabold text-slate-800">
                  Upload Learning Content
                </h3>
                <p className="text-xs text-slate-400 mt-0.5">
                  Upload official public-service curriculum documents
                </p>
              </div>
              <button
                onClick={() => {
                  setUploadModalOpen(false);
                  setSelectedFile(null);
                }}
                className="rounded-full p-1 text-slate-400 hover:bg-slate-100 transition-colors"
              >
                <X size={18} />
              </button>
            </div>

            <form onSubmit={handleUploadSubmit} className="mt-5 space-y-4">
              {/* Dropzone */}
              <div
                onDragOver={(e) => e.preventDefault()}
                onDrop={handleFileDrop}
                onClick={() => fileInputRef.current?.click()}
                className={`flex flex-col items-center justify-center rounded-2xl border-2 border-dashed p-8 text-center cursor-pointer transition-all ${
                  selectedFile
                    ? "border-emerald-300 bg-emerald-50/30"
                    : "border-orange-200 bg-orange-50/20 hover:bg-orange-50/40"
                }`}
              >
                <input
                  type="file"
                  ref={fileInputRef}
                  onChange={handleFileChange}
                  accept=".pdf,.docx,.txt"
                  className="hidden"
                />

                <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-white text-[#ef7e37] shadow-sm border border-[#f0ddd0]">
                  <Upload size={22} />
                </div>

                {selectedFile ? (
                  <div className="mt-3">
                    <p className="text-sm font-bold text-emerald-800">
                      {selectedFile.name}
                    </p>
                    <p className="text-xs text-emerald-600 mt-0.5">
                      {(selectedFile.size / (1024 * 1024)).toFixed(2)} MB · Ready for upload
                    </p>
                  </div>
                ) : (
                  <div className="mt-3">
                    <p className="text-sm font-bold text-slate-700">
                      Drag and drop your file here, or{" "}
                      <span className="text-[#ef7e37]">browse</span>
                    </p>
                    <p className="text-xs text-slate-400 mt-1">
                      Supports PDF, DOCX, and TXT up to 25MB
                    </p>
                  </div>
                )}
              </div>

              {/* Supported notice */}
              <div className="rounded-xl bg-slate-50 p-3 text-xs text-slate-500 leading-relaxed border border-slate-200/50">
                Uploaded documents are extracted into deterministic semantic chunks and embedded for grounded AI question generation.
              </div>

              {/* Modal buttons */}
              <div className="mt-6 flex items-center justify-end gap-3 border-t border-slate-100 pt-4">
                <button
                  type="button"
                  onClick={() => {
                    setUploadModalOpen(false);
                    setSelectedFile(null);
                  }}
                  className="rounded-xl border border-slate-200 px-4 py-2 text-xs font-bold text-slate-600 hover:bg-slate-50 transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={!selectedFile || uploading}
                  className="inline-flex items-center gap-2 rounded-xl bg-[#ef7e37] px-5 py-2.5 text-xs font-bold text-white shadow-md hover:bg-[#d96a27] disabled:opacity-50 transition-all active:scale-95"
                >
                  {uploading ? (
                    <>
                      <RefreshCw size={14} className="animate-spin" /> Uploading & Chunking...
                    </>
                  ) : (
                    <>
                      <Upload size={14} /> Start Upload
                    </>
                  )}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

export default TrainerMaterials;
