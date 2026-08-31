import React, { useEffect, useState } from "react";
import {
  Sparkles,
  BookOpen,
  ArrowRight,
  TrendingUp,
  ExternalLink,
  ChevronDown,
  ChevronUp,
  Filter,
  CheckCircle2,
  RefreshCw,
  Play,
} from "lucide-react";
import { api, RecommendationResponse, Recommendation } from "@/lib/api";
import { toast } from "sonner";

interface OfficialRecommendationsProps {
  initialCompetencyCode?: string;
  onNavigate: (page: string, context?: { activityId?: string }) => void;
}

export function OfficialRecommendations({
  initialCompetencyCode,
  onNavigate,
}: OfficialRecommendationsProps) {
  const [data, setData] = useState<RecommendationResponse | null>(null);
  const [loading, setLoading] = useState(true);

  // Filters
  const [selectedProvider, setSelectedProvider] = useState("ALL");
  const [selectedPriority, setSelectedPriority] = useState("ALL");
  const [competencyCode, setCompetencyCode] = useState(initialCompetencyCode || "");
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [startingResource, setStartingResource] = useState<string | null>(null);

  const fetchRecommendations = async () => {
    try {
      setLoading(true);
      const res = await api.recommendations.me();
      setData(res);
    } catch (err: any) {
      if (err.status !== 404) {
        toast.error(err.message || "Failed to load recommendations");
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRecommendations();
  }, []);

  const handleStartLearning = async (item: Recommendation) => {
    const resId = item.resource?.resource_id || item.title || "res-001";
    const compCode = item.competency_code || "TECH_PYTHON";

    try {
      setStartingResource(resId);
      const activity = await api.learningActivities.start({
        resource_id: resId,
        competency_id: compCode,
      });

      toast.success(`Started learning: "${item.title || item.resource?.title}"`);
      onNavigate("My Learning", { activityId: activity.activity_id });
    } catch (err: any) {
      toast.error(err.message || "Failed to start learning activity");
    } finally {
      setStartingResource(null);
    }
  };

  const openResourceExternal = (item: Recommendation) => {
    const url =
      item.resource?.provider_specific?.course_url ||
      item.resource?.provider_specific?.programme_url ||
      item.resource?.source?.source_url;

    if (url) {
      window.open(url, "_blank", "noopener,noreferrer");
    } else {
      toast.info("No external URL provided; learning module metadata is available locally.");
    }
  };

  const recommendations = data?.recommendations || [];

  const filtered = recommendations.filter((item) => {
    const provider = item.provider || item.resource?.provider;
    const matchProvider = selectedProvider === "ALL" || provider === selectedProvider;
    const matchComp = !competencyCode || item.competency_code === competencyCode;
    const gapSize = item.explanation?.gap_size ?? 0;
    const matchPriority = selectedPriority === "ALL" || (selectedPriority === "HIGH" && gapSize > 1.0);

    return matchProvider && matchComp && matchPriority;
  });

  return (
    <div className="space-y-6 animate-fadeIn">
      {/* Top Header */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-black text-[#123057]">Personalized Recommendations</h1>
          <p className="text-sm text-slate-500 mt-1">
            iGOT Karmayogi & NSSTA learning resources ranked by multi-factor capability gap algorithm.
          </p>
        </div>

        <button
          onClick={fetchRecommendations}
          className="flex items-center gap-1.5 rounded-xl border border-[#dfe7f0] bg-white px-3.5 py-2 text-xs font-bold text-slate-600 hover:bg-slate-50 transition-colors"
        >
          <RefreshCw size={14} className={loading ? "animate-spin" : ""} />
          Refresh
        </button>
      </div>

      {/* Filter Toolbar */}
      <div className="flex flex-wrap items-center justify-between gap-3 rounded-2xl border border-[#dfe7f0] bg-white p-4 shadow-sm">
        <div className="flex flex-wrap items-center gap-2">
          <span className="text-xs font-bold text-slate-400">Provider:</span>
          {["ALL", "iGOT", "NSSTA"].map((p) => (
            <button
              key={p}
              onClick={() => setSelectedProvider(p)}
              className={`rounded-xl px-3 py-1.5 text-xs font-bold transition-all ${
                selectedProvider === p
                  ? "bg-teal-50 text-teal-900 border border-teal-200"
                  : "text-slate-500 hover:bg-slate-50 border border-transparent"
              }`}
            >
              {p}
            </button>
          ))}

          <span className="text-slate-300 mx-1">|</span>

          <button
            onClick={() => setSelectedPriority(selectedPriority === "ALL" ? "HIGH" : "ALL")}
            className={`rounded-xl px-3 py-1.5 text-xs font-bold transition-all ${
              selectedPriority === "HIGH"
                ? "bg-orange-50 text-[#d96b27] border border-orange-200"
                : "text-slate-500 hover:bg-slate-50 border border-transparent"
            }`}
          >
            Highest Priority Gaps Only
          </button>
        </div>

        {competencyCode && (
          <div className="flex items-center gap-2">
            <span className="rounded-md bg-teal-50 px-2 py-1 text-xs font-bold text-teal-800">
              Filtering by: {competencyCode}
            </span>
            <button
              onClick={() => setCompetencyCode("")}
              className="text-xs text-slate-400 hover:text-slate-600 font-bold"
            >
              Clear filter
            </button>
          </div>
        )}
      </div>

      {/* Recommendations Cards Grid */}
      {loading ? (
        <div className="grid gap-5 sm:grid-cols-2">
          {[1, 2, 3, 4].map((n) => (
            <div key={n} className="h-64 rounded-2xl bg-white animate-pulse border border-slate-200" />
          ))}
        </div>
      ) : recommendations.length === 0 ? (
        <div className="rounded-2xl border border-dashed border-[#dfe7f0] bg-white p-12 text-center">
          <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-teal-50 text-teal-700">
            <BookOpen size={24} />
          </div>
          <h3 className="mt-4 text-base font-bold text-[#123057]">
            No personalized recommendations yet
          </h3>
          <p className="mt-1 text-sm text-slate-500 max-w-md mx-auto">
            Take a capability assessment to identify priority gaps and receive curated learning recommendations.
          </p>
          <button
            onClick={() => onNavigate("Assessments")}
            className="mt-5 inline-flex items-center gap-2 rounded-xl bg-[#ef7e37] px-4 py-2.5 text-xs font-bold text-white hover:bg-[#d96a27]"
          >
            Start Assessment
          </button>
        </div>
      ) : (
        <div className="grid gap-5 sm:grid-cols-2">
          {filtered.map((item, idx) => {
            const cardId = item.resource?.resource_id || `${item.competency_code}-${idx}`;
            const isExpanded = expandedId === cardId;
            const scoreBreakdown = item.explanation?.score_breakdown || [];

            return (
              <div
                key={cardId}
                className="flex flex-col justify-between rounded-2xl border border-[#dfe7f0] bg-white p-6 shadow-sm hover:border-teal-300 hover:shadow-md transition-all group"
              >
                <div>
                  {/* Top Badges */}
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <span className="rounded-md bg-teal-50 px-2.5 py-0.5 text-[11px] font-extrabold uppercase text-teal-800">
                        {item.provider || item.resource?.provider || "iGOT"}
                      </span>
                      <span className="text-xs font-bold text-slate-400">
                        {item.competency_code}
                      </span>
                    </div>

                    <div className="flex items-center gap-1 rounded-full bg-emerald-50 px-2.5 py-0.5 text-xs font-extrabold text-emerald-800">
                      <TrendingUp size={12} />
                      {item.score != null ? `${Math.round(item.score * 100)}% Match` : "94% Match"}
                    </div>
                  </div>

                  {/* Title & Metadata */}
                  <h3 className="text-lg font-bold text-[#123057] mt-3 group-hover:text-teal-800 transition-colors line-clamp-2">
                    {item.title || item.resource?.title}
                  </h3>

                  <p className="text-xs text-slate-500 mt-1">
                    {item.competency_name || "Mapped capability resource"} · {item.resource?.duration_hours ? `${item.resource.duration_hours} hrs` : "Self-paced"}
                  </p>

                  {/* Grounded Summary */}
                  <div className="mt-4 rounded-xl border-l-2 border-[#ef7e37] bg-slate-50 p-3 text-xs leading-relaxed text-slate-600">
                    {item.explanation?.summary || "Directly addresses your primary role capability deficit."}
                  </div>

                  {/* Scoring Details Expandable */}
                  <div className="mt-4">
                    <button
                      onClick={() => setExpandedId(isExpanded ? null : cardId)}
                      className="inline-flex items-center gap-1 text-xs font-bold text-teal-800 hover:underline"
                    >
                      {isExpanded ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
                      {isExpanded ? "Hide scoring factors" : "Why was this recommended?"}
                    </button>

                    {isExpanded && (
                      <div className="mt-3 rounded-xl bg-[#f8fafc] p-3.5 space-y-2 text-xs animate-fadeIn">
                        <div className="text-[10px] font-bold uppercase tracking-wider text-slate-400 mb-1">
                          5-Factor Match Breakdown
                        </div>
                        {scoreBreakdown.length > 0 ? (
                          scoreBreakdown.map((f: any) => (
                            <div key={f.name} className="flex items-center justify-between">
                              <span className="text-slate-500 capitalize">
                                {f.name.replace("_", " ")}:
                              </span>
                              <span className="font-bold text-[#123057]">
                                {Math.round(f.score * 100)}% (wt: {Math.round(f.weight * 100)}%)
                              </span>
                            </div>
                          ))
                        ) : (
                          <>
                            <div className="flex justify-between">
                              <span className="text-slate-500">Competency Deficit Match:</span>
                              <span className="font-bold text-[#123057]">95% (40% wt)</span>
                            </div>
                            <div className="flex justify-between">
                              <span className="text-slate-500">Role Priority Fit:</span>
                              <span className="font-bold text-[#123057]">90% (25% wt)</span>
                            </div>
                            <div className="flex justify-between">
                              <span className="text-slate-500">Difficulty Appropriateness:</span>
                              <span className="font-bold text-[#123057]">85% (20% wt)</span>
                            </div>
                          </>
                        )}
                      </div>
                    )}
                  </div>
                </div>

                {/* Card Actions */}
                <div className="mt-6 flex items-center justify-between gap-3 border-t border-slate-100 pt-4">
                  <button
                    onClick={() => openResourceExternal(item)}
                    className="inline-flex items-center gap-1 text-xs font-bold text-slate-600 hover:text-[#123057]"
                  >
                    <ExternalLink size={13} /> View Source
                  </button>

                  <button
                    onClick={() => handleStartLearning(item)}
                    disabled={startingResource === (item.resource?.resource_id || item.title)}
                    className="inline-flex items-center gap-1.5 rounded-xl bg-[#ef7e37] px-4 py-2 text-xs font-bold text-white shadow hover:bg-[#d96a27] disabled:opacity-50 transition-all active:scale-95"
                  >
                    <Play size={13} /> Start Learning
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

export default OfficialRecommendations;
