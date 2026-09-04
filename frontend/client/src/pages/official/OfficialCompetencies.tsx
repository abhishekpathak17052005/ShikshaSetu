import React, { useEffect, useState } from "react";
import {
  Gauge,
  Search,
  SlidersHorizontal,
  ClipboardCheck,
  CheckCircle2,
  AlertCircle,
  HelpCircle,
  TrendingUp,
  ArrowRight,
  RefreshCw,
  X,
  Layers,
} from "lucide-react";
import { api, clearApiCache, UserApplicableCompetency, SkillGapResponse } from "@/lib/api";
import { useAuth } from "@/contexts/AuthContext";
import { useTranslation } from "@/i18n";
import { toast } from "sonner";
import { NumberReveal, ProgressBarFill } from "@/components/motion/MotionUtils";

interface OfficialCompetenciesProps {
  onNavigate: (page: string, context?: { competencyCode?: string }) => void;
}

export function OfficialCompetencies({ onNavigate }: OfficialCompetenciesProps) {
  const { user } = useAuth();
  const { t, isHindi } = useTranslation();
  const [competencies, setCompetencies] = useState<UserApplicableCompetency[]>([]);
  const [skillGaps, setSkillGaps] = useState<SkillGapResponse | null>(null);
  const [loading, setLoading] = useState(true);

  // Filters
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedDomain, setSelectedDomain] = useState("ALL");
  const [selectedStatus, setSelectedStatus] = useState("ALL");

  const fetchData = async () => {
    clearApiCache();
    try {
      setLoading(true);
      const [comps, gaps] = await Promise.all([
        api.competencies.me().catch(async () => {
          // Fallback if me endpoint errors
          return api.competencies.list() as any;
        }),
        api.skillGaps.me().catch(() => null),
      ]);
      setCompetencies(comps || []);
      setSkillGaps(gaps);
    } catch (err: any) {
      toast.error(err.message || "Failed to load competency framework");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const rows = competencies.map((comp) => {
    let indicator = comp.indicator || "Not Assessed";
    if (!comp.indicator) {
      if (comp.current_level != null) {
        if (comp.gap <= 0) indicator = "Strong";
        else if (comp.gap <= 1.0) indicator = "Developing";
        else indicator = "Needs Attention";
      }
    }
    return { ...comp, indicator };
  });


  const domains = ["ALL", ...Array.from(new Set(competencies.map((c) => c.domain)))];

  const filteredRows = rows.filter((item) => {
    const term = searchQuery.toLowerCase();
    const matchSearch =
      item.name.toLowerCase().includes(term) ||
      item.code.toLowerCase().includes(term) ||
      (item.description && item.description.toLowerCase().includes(term));

    const matchDomain = selectedDomain === "ALL" || item.domain === selectedDomain;
    const matchStatus = selectedStatus === "ALL" || item.indicator === selectedStatus;

    return matchSearch && matchDomain && matchStatus;
  });

  return (
    <div className="space-y-6 anim-page-enter">
      {/* Header */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between anim-fade-up">
        <div>
          <h1 className="text-2xl font-black text-[#123057]">My Competency Profile</h1>
          <p className="text-sm text-slate-500 mt-1">
            Civil service capability framework benchmarks and your assessed proficiency levels.
          </p>
          {user && (
            <div className="mt-2 flex flex-wrap items-center gap-2 text-xs font-semibold text-slate-600">
              <span className="rounded-md bg-teal-50 px-2 py-0.5 text-teal-800 font-bold">{user.department}</span>
              <span>·</span>
              <span className="text-slate-700">{user.designation}</span>
              <span>·</span>
              <span className="text-teal-700 font-bold">{competencies.length} Applicable Competencies</span>
            </div>
          )}
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={fetchData}
            className="flex items-center gap-1.5 rounded-xl border border-[#dfe7f0] bg-white px-3.5 py-2.5 text-xs font-bold text-slate-600 hover:bg-slate-50 btn-interactive"
          >
            <RefreshCw size={14} className={loading ? "animate-spin" : ""} />
            Refresh
          </button>
          <button
            onClick={() => onNavigate("Assessments")}
            className="flex items-center gap-2 rounded-xl bg-[#ef7e37] px-4 py-2.5 text-xs font-bold text-white shadow-md hover:bg-[#d96a27] btn-interactive"
          >
            <ClipboardCheck size={16} />
            Take Assessment
          </button>
        </div>
      </div>

      {/* Filter Toolbar */}
      <div className="flex flex-col gap-3 rounded-2xl border border-[#dfe7f0] bg-white p-4 shadow-sm md:flex-row md:items-center md:justify-between anim-fade-up stagger-1">
        {/* Search */}
        <div className="flex flex-1 items-center gap-2 rounded-xl border border-slate-200 px-3 py-2">
          <Search size={16} className="text-slate-400" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search competencies by code, title, or keyword..."
            className="w-full bg-transparent text-xs text-slate-800 placeholder-slate-400 focus:outline-none"
          />
          {searchQuery && (
            <button onClick={() => setSearchQuery("")} className="text-xs text-slate-400 hover:text-slate-600">
              <X size={14} />
            </button>
          )}
        </div>

        {/* Domain Filter */}
        <div className="flex items-center gap-2">
          <label className="text-xs font-bold text-slate-500 whitespace-nowrap">Domain:</label>
          <select
            value={selectedDomain}
            onChange={(e) => setSelectedDomain(e.target.value)}
            className="rounded-xl border border-slate-200 bg-white px-3 py-2 text-xs font-semibold text-slate-700 focus:border-[#087f76] focus:outline-none"
          >
            {domains.map((dom) => (
              <option key={dom} value={dom}>
                {dom === "ALL" ? "All Domains" : dom}
              </option>
            ))}
          </select>
        </div>

        {/* Status Filter */}
        <div className="flex items-center gap-1 overflow-x-auto rounded-xl bg-slate-100 p-1">
          {["ALL", "Strong", "Developing", "Needs Attention", "Not Assessed"].map((st) => (
            <button
              key={st}
              onClick={() => setSelectedStatus(st)}
              className={`rounded-lg px-2.5 py-1 text-[11px] font-bold transition-all whitespace-nowrap btn-interactive ${
                selectedStatus === st
                  ? "bg-white text-[#123057] shadow-sm"
                  : "text-slate-500 hover:text-slate-800"
              }`}
            >
              {st}
            </button>
          ))}
        </div>
      </div>

      {/* Competency Cards List */}
      {loading ? (
        <div className="space-y-4">
          {[1, 2, 3].map((n) => (
            <div key={n} className="h-48 rounded-2xl bg-white animate-pulse border border-slate-200" />
          ))}
        </div>
      ) : filteredRows.length === 0 ? (
        <div className="rounded-2xl border border-dashed border-[#dfe7f0] bg-white p-12 text-center anim-fade-in">
          <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-teal-50 text-teal-700 anim-badge-pop">
            <Layers size={24} />
          </div>
          <h3 className="mt-4 text-base font-bold text-[#123057]">No matching competencies</h3>
          <p className="mt-1 text-sm text-slate-500">
            Try adjusting your search query or domain/status filters.
          </p>
        </div>
      ) : (
        <div className="space-y-4 matrix-grid">
          {filteredRows.map((item, idx) => {
            const current = item.current_level;
            const required = item.required_level || 4.0;
            const gap = item.gap;
            const confidencePct = item.confidence != null ? Math.round(item.confidence * 100) : null;
            const hasScore = current != null;
            const staggerClass = idx < 8 ? `stagger-${idx + 1}` : "";

            return (
              <div
                key={item.id || item.code}
                className={`rounded-2xl border border-[#dfe7f0] bg-white p-6 shadow-sm hover:border-teal-400 card-interactive matrix-item anim-card-enter ${staggerClass} group`}
              >
                <div className="flex flex-wrap items-start justify-between gap-4 border-b border-slate-100 pb-4">
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="rounded-md bg-teal-50 px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wider text-teal-800">
                        {item.domain}
                      </span>
                      <span className="font-mono text-[11px] font-medium tracking-tight text-slate-400">{item.code}</span>
                    </div>
                    <h3 className="text-lg font-bold text-[#123057] mt-1 group-hover:text-teal-800 transition-colors">
                      {item.name}
                    </h3>
                  </div>

                  {/* Status Indicator */}
                  <div>
                    {item.indicator === "Strong" ? (
                      <span className="inline-flex items-center gap-1 rounded-full bg-emerald-100 px-3 py-1 text-xs font-semibold text-emerald-800 anim-badge-pop">
                        <CheckCircle2 size={13} /> Strong (Proficient)
                      </span>
                    ) : item.indicator === "Developing" ? (
                      <span className="inline-flex items-center gap-1 rounded-full bg-amber-100 px-3 py-1 text-xs font-semibold text-amber-800 anim-badge-pop">
                        <TrendingUp size={13} /> Developing
                      </span>
                    ) : item.indicator === "Needs Attention" ? (
                      <span className="inline-flex items-center gap-1 rounded-full bg-rose-100 px-3 py-1 text-xs font-semibold text-rose-800 anim-badge-pop">
                        <AlertCircle size={13} /> Needs Attention
                      </span>
                    ) : (
                      <span className="inline-flex items-center gap-1 rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-600 anim-fade-in">
                        <HelpCircle size={13} /> Not Assessed
                      </span>
                    )}
                  </div>
                </div>

                <p className="mt-3 text-xs leading-relaxed text-slate-600 font-normal">{item.description}</p>

                {/* Score Breakdown Grid */}
                <div className="mt-5 grid grid-cols-2 gap-3 sm:grid-cols-4 rounded-xl bg-slate-50 p-3.5 text-xs">
                  <div>
                    <div className="text-slate-400 font-medium text-[11px]">Current Level:</div>
                    <div className="text-sm font-bold text-[#123057] mt-0.5">
                      {hasScore ? (
                        <NumberReveal value={current} decimals={1} suffix=" / 5.0" />
                      ) : (
                        <span className="text-slate-400 font-normal">Not Assessed</span>
                      )}
                    </div>
                  </div>

                  <div>
                    <div className="text-slate-400 font-medium text-[11px]">Required Level:</div>
                    <div className="text-sm font-bold text-[#123057] mt-0.5">
                      {required.toFixed(1)} / 5.0
                    </div>
                  </div>

                  <div>
                    <div className="text-slate-400 font-medium text-[11px]">Skill Gap:</div>
                    <div
                      className={`text-sm font-bold mt-0.5 ${
                        gap != null && gap > 0 ? "text-[#ef7e37]" : "text-emerald-700"
                      }`}
                    >
                      {gap != null ? <NumberReveal value={gap} decimals={1} /> : "—"}
                    </div>
                  </div>

                  <div>
                    <div className="text-slate-400 font-medium text-[11px]">Evidence Confidence:</div>
                    <div className="text-sm font-bold text-teal-800 mt-0.5">
                      {confidencePct != null ? <NumberReveal value={confidencePct} suffix="%" /> : "—"}
                    </div>
                  </div>
                </div>

                {/* Progressive Proficiency Level Track (if assessed) */}
                {hasScore && (
                  <div className="mt-3.5 px-1">
                    <div className="flex justify-between items-center text-[10px] text-slate-400 font-bold mb-1">
                      <span>L1</span>
                      <span>L2</span>
                      <span>L3</span>
                      <span>L4</span>
                      <span>L5 (Mastery)</span>
                    </div>
                    <ProgressBarFill
                      percent={Math.min(100, Math.round((current / 5.0) * 100))}
                      className="h-2 w-full rounded-full bg-slate-200 overflow-hidden"
                      fillClassName={`h-full rounded-full ${
                        gap != null && gap > 0 ? "bg-[#ef7e37]" : "bg-[#087f76]"
                      }`}
                      durationMs={650}
                    />
                  </div>
                )}

                {/* Actions */}
                <div className="mt-5 flex flex-wrap items-center justify-between gap-3 border-t border-slate-100 pt-4">
                  <div className="text-[11px] text-slate-400">
                    Authoritative baseline required for national competency registration.
                  </div>

                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => onNavigate("Recommendations", { competencyCode: item.code })}
                      className="rounded-xl border border-slate-200 px-3.5 py-1.5 text-xs font-bold text-slate-700 hover:bg-slate-50 btn-interactive"
                    >
                      View Learning
                    </button>
                    <button
                      onClick={() => onNavigate("Assessments", { competencyCode: item.code })}
                      className="rounded-xl bg-[#087f76] px-4 py-1.5 text-xs font-bold text-white shadow hover:bg-[#06655e] btn-interactive"
                    >
                      Assess Competency →
                    </button>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

export default OfficialCompetencies;
