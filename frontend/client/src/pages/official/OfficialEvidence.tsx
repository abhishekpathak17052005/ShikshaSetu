import React, { useEffect, useState } from "react";
import {
  Award,
  BookOpen,
  CheckCircle2,
  ClipboardCheck,
  Filter,
  Layers,
  RefreshCw,
  ShieldCheck,
  Sparkles,
  TrendingUp,
  Clock,
} from "lucide-react";
import { api, CompetencyEvidence, LearningActivity } from "@/lib/api";
import { toast } from "sonner";

interface OfficialEvidenceProps {
  onNavigate: (page: string) => void;
}

export function OfficialEvidence({ onNavigate }: OfficialEvidenceProps) {
  const [evidenceItems, setEvidenceItems] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [filterType, setFilterType] = useState<"ALL" | "AUTHORITATIVE" | "SUPPORTING">("ALL");

  const fetchEvidence = async () => {
    try {
      setLoading(true);
      const [evidenceRes, activitiesRes, assessmentsRes] = await Promise.allSettled([
        api.evidence.list(),
        api.learningActivities.list("completed"),
        api.capabilityAssessments.list(undefined, "SUBMITTED"),
      ]);

      const items: any[] = [];
      const seenIds = new Set<string>();

      // Primary source: dedicated competency evidence ledger API
      if (evidenceRes.status === "fulfilled" && Array.isArray(evidenceRes.value)) {
        evidenceRes.value.forEach((ev: any) => {
          if (!seenIds.has(ev.id)) {
            seenIds.add(ev.id);
            items.push(ev);
          }
        });
      }

      // Add completed learning activities as SUPPORTING evidence
      if (activitiesRes.status === "fulfilled" && (activitiesRes.value as any)?.activities) {
        ((activitiesRes.value as any).activities || []).forEach((act: LearningActivity) => {
          if (!seenIds.has(act.activity_id)) {
            seenIds.add(act.activity_id);
            items.push({
              id: act.activity_id,
              type: "SUPPORTING",
              source: "Learning Module Completion",
              title: act.resource_id,
              competency_code: act.competency_id,
              confidence: 0.3,
              date: act.completed_at || act.last_accessed_at,
              notes: act.notes || "Completed structured self-paced learning curriculum.",
            });
          }
        });
      }

      // Add submitted capability assessments as AUTHORITATIVE evidence
      if (assessmentsRes.status === "fulfilled" && Array.isArray(assessmentsRes.value)) {
        assessmentsRes.value.forEach((ass: any) => {
          if (!seenIds.has(ass.id)) {
            seenIds.add(ass.id);
            items.push({
              id: ass.id,
              type: "AUTHORITATIVE",
              source: "Standardized Capability Assessment",
              title: ass.title || `Formal Assessment (${ass.competency_code})`,
              competency_code: ass.competency_code,
              confidence: 0.85,
              score: ass.score || (ass.percentage ? ass.percentage / 20 : 4.0),
              date: ass.submitted_at || ass.started_at,
              notes: "Authoritative server-side scored examination. Verified competency profile update.",
            });
          }
        });
      }

      // Sort by date descending
      items.sort((a, b) => new Date(b.date || 0).getTime() - new Date(a.date || 0).getTime());
      setEvidenceItems(items);
    } catch (err: any) {
      toast.error(err.message || "Failed to load evidence records");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchEvidence();
  }, []);

  const filteredItems = evidenceItems.filter((item) => {
    if (filterType === "ALL") return true;
    return item.type === filterType;
  });

  const authoritativeCount = evidenceItems.filter((i) => i.type === "AUTHORITATIVE").length;
  const supportingCount = evidenceItems.filter((i) => i.type === "SUPPORTING").length;

  return (
    <div className="space-y-6 animate-fadeIn max-w-4xl mx-auto">
      {/* Header */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-black text-[#123057]">Competency Evidence Ledger</h1>
          <p className="text-sm text-slate-500 mt-1">
            Immutable timeline of authoritative assessment outcomes and supporting learning records.
          </p>
        </div>

        <button
          onClick={fetchEvidence}
          className="flex items-center gap-1.5 rounded-xl border border-[#dfe7f0] bg-white px-3.5 py-2 text-xs font-bold text-slate-600 hover:bg-slate-50 transition-colors"
        >
          <RefreshCw size={14} className={loading ? "animate-spin" : ""} />
          Refresh Ledger
        </button>
      </div>

      {/* Dual Evidence Rule Banners */}
      <div className="grid gap-4 sm:grid-cols-2">
        {/* Authoritative Card */}
        <div className="rounded-2xl border border-emerald-200 bg-emerald-50/40 p-5 space-y-2">
          <div className="flex items-center gap-2 text-emerald-800 font-extrabold text-sm">
            <ShieldCheck size={18} />
            Authoritative Evidence (Confidence 0.85 – 1.0)
          </div>
          <p className="text-xs text-emerald-950 leading-relaxed">
            Generated exclusively by formal capability assessments. Directly modifies your official competency profile score and recalculates national skill gaps.
          </p>
          <div className="text-xs font-bold text-emerald-800 pt-1">
            {authoritativeCount} records logged
          </div>
        </div>

        {/* Supporting Card */}
        <div className="rounded-2xl border border-teal-200 bg-teal-50/40 p-5 space-y-2">
          <div className="flex items-center gap-2 text-teal-900 font-extrabold text-sm">
            <BookOpen size={18} />
            Supporting Evidence (Confidence 0.30)
          </div>
          <p className="text-xs text-teal-950 leading-relaxed">
            Generated by completing iGOT/NSSTA courses and practice quizzes. Verifies learning engagement but does not alter authoritative competency scores without assessment.
          </p>
          <div className="text-xs font-bold text-teal-900 pt-1">
            {supportingCount} records logged
          </div>
        </div>
      </div>

      {/* Filter Tabs */}
      <div className="flex items-center gap-1 rounded-2xl border border-[#dfe7f0] bg-white p-1.5 shadow-sm">
        <button
          onClick={() => setFilterType("ALL")}
          className={`flex-1 rounded-xl py-2 text-xs font-bold transition-all ${
            filterType === "ALL"
              ? "bg-[#123057] text-white shadow-sm"
              : "text-slate-500 hover:text-slate-800"
          }`}
        >
          All Records ({evidenceItems.length})
        </button>
        <button
          onClick={() => setFilterType("AUTHORITATIVE")}
          className={`flex-1 rounded-xl py-2 text-xs font-bold transition-all ${
            filterType === "AUTHORITATIVE"
              ? "bg-emerald-700 text-white shadow-sm"
              : "text-slate-500 hover:text-slate-800"
          }`}
        >
          Authoritative ({authoritativeCount})
        </button>
        <button
          onClick={() => setFilterType("SUPPORTING")}
          className={`flex-1 rounded-xl py-2 text-xs font-bold transition-all ${
            filterType === "SUPPORTING"
              ? "bg-[#087f76] text-white shadow-sm"
              : "text-slate-500 hover:text-slate-800"
          }`}
        >
          Supporting ({supportingCount})
        </button>
      </div>

      {/* Evidence Timeline List */}
      {loading ? (
        <div className="space-y-4">
          {[1, 2, 3].map((n) => (
            <div key={n} className="h-32 rounded-2xl bg-white animate-pulse border border-slate-200" />
          ))}
        </div>
      ) : filteredItems.length === 0 ? (
        <div className="rounded-2xl border border-dashed border-[#dfe7f0] bg-white p-12 text-center">
          <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-teal-50 text-teal-700">
            <Award size={24} />
          </div>
          <h3 className="mt-4 text-base font-bold text-[#123057]">
            No evidence records found
          </h3>
          <p className="mt-1 text-sm text-slate-500 max-w-md mx-auto">
            Complete learning modules or take a capability assessment to start building your verified capability ledger.
          </p>
          <div className="mt-5 flex justify-center gap-3">
            <button
              onClick={() => onNavigate("Assessments")}
              className="rounded-xl bg-[#ef7e37] px-4 py-2 text-xs font-bold text-white hover:bg-[#d96a27]"
            >
              Take Assessment
            </button>
            <button
              onClick={() => onNavigate("Recommendations")}
              className="rounded-xl border border-slate-200 px-4 py-2 text-xs font-bold text-slate-700 hover:bg-slate-50"
            >
              Start Learning
            </button>
          </div>
        </div>
      ) : (
        <div className="space-y-4">
          {filteredItems.map((item, idx) => {
            const isAuth = item.type === "AUTHORITATIVE";

            return (
              <div
                key={item.id || idx}
                className={`rounded-2xl border bg-white p-6 shadow-sm transition-all ${
                  isAuth
                    ? "border-emerald-200 hover:border-emerald-400"
                    : "border-teal-100 hover:border-teal-300"
                }`}
              >
                <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-100 pb-3">
                  <div className="flex items-center gap-2">
                    <span
                      className={`rounded-full px-2.5 py-0.5 text-[10px] font-extrabold uppercase ${
                        isAuth
                          ? "bg-emerald-100 text-emerald-800"
                          : "bg-teal-100 text-teal-800"
                      }`}
                    >
                      {item.type} EVIDENCE
                    </span>

                    <span className="rounded bg-slate-100 px-2 py-0.5 text-[10px] font-bold text-slate-600">
                      {item.competency_code}
                    </span>
                  </div>

                  <span className="text-xs font-bold text-slate-400">
                    Confidence: {(item.confidence * 100).toFixed(0)}%
                  </span>
                </div>

                <div className="mt-3">
                  <h3 className="text-base font-bold text-[#123057]">{item.title}</h3>
                  <div className="text-xs text-slate-400 mt-0.5">
                    Source: {item.source} · {item.date ? new Date(item.date).toLocaleDateString() : "Recent"}
                  </div>
                </div>

                <p className="mt-3 text-xs leading-relaxed text-slate-600 bg-slate-50 p-3 rounded-xl border border-slate-100">
                  {item.notes}
                </p>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

export default OfficialEvidence;
