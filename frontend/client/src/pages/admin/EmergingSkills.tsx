import React, { useEffect, useState } from "react";
import {
  Brain,
  Lightbulb,
  RefreshCw,
  Sparkles,
  TrendingUp,
  Zap,
  ArrowRight,
} from "lucide-react";
import { api, clearApiCache, EmergingSkillsResponse, EmergingSkillItem } from "@/lib/api";
import { toast } from "sonner";
import { NumberReveal } from "@/components/motion/MotionUtils";

interface EmergingSkillsProps {
  onNavigate: (page: string) => void;
}

export function EmergingSkills({ onNavigate }: EmergingSkillsProps) {
  const [data, setData] = useState<EmergingSkillsResponse | null>(null);
  const [loading, setLoading] = useState(true);

  const fetchEmerging = async () => {
    clearApiCache();
    try {
      setLoading(true);
      const res = await api.admin.emergingSkills();
      setData(res);
    } catch (err: any) {
      toast.error(err.message || "Failed to load emerging skills");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchEmerging();
  }, []);

  return (
    <div className="space-y-8 anim-page-enter max-w-6xl mx-auto">
      {/* Header */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between anim-fade-up">
        <div>
          <div className="inline-flex items-center gap-1.5 rounded-full bg-amber-100 px-3 py-1 text-xs font-semibold uppercase tracking-wider text-amber-900 anim-badge-pop">
            <Zap size={13} /> Emerging Capability Needs
          </div>
          <h1 className="mt-2 text-2xl sm:text-3xl font-bold tracking-tight text-[#123057]">
            Strategic & Emerging Capabilities
          </h1>
          <p className="text-sm text-slate-500 mt-1">
            Data science, analytical modernization, and high-deficit domain requirements prioritized for administrative focus.
          </p>
        </div>

        <button
          onClick={fetchEmerging}
          className="flex items-center gap-1.5 rounded-xl border border-[#e0daef] bg-white px-4 py-2 text-xs font-semibold text-[#4b36a8] shadow-sm hover:bg-purple-50 transition-all btn-interactive"
        >
          <RefreshCw size={14} className={loading ? "animate-spin" : ""} /> Refresh Emerging
        </button>
      </div>

      {/* Strategic Focus Domains Banner */}
      <div className="rounded-3xl bg-gradient-to-r from-[#123057] to-[#1e4976] p-6 text-white shadow-sm flex flex-wrap items-center justify-between gap-4 anim-card-enter stagger-1">
        <div>
          <h3 className="text-base font-bold tracking-tight">Priority Modernization Domains</h3>
          <p className="text-xs text-slate-300 mt-1">
            Focus areas identified across civil service capacity building guidelines.
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          {(data?.strategic_focus_domains || ["TECHNOLOGY", "DATA", "DOMAIN", "BEHAVIORAL", "GOVERNANCE"]).map((dom, idx) => (
            <span key={dom} className={`rounded-xl bg-white/10 px-3 py-1.5 text-xs font-semibold text-teal-300 border border-white/10 anim-card-enter stagger-${Math.min(idx + 1, 6)} tracking-wider`}>
              {dom}
            </span>
          ))}
        </div>
      </div>

      {/* Emerging Capabilities Grid */}
      <div className="grid gap-5 md:grid-cols-2">
        {(data?.emerging_capabilities || []).map((skill, idx) => (
          <div
            key={skill.competency_id}
            className={`flex flex-col justify-between rounded-3xl border border-[#e0daef] bg-white p-6 shadow-sm hover:border-[#6d5bc3] hover:shadow-md transition-all space-y-4 card-interactive anim-card-enter stagger-${Math.min(idx + 1, 6)}`}
          >
            <div>
              <div className="flex items-center justify-between">
                <span className="rounded-md bg-purple-50 px-2.5 py-0.5 text-[10px] font-semibold uppercase text-[#4b36a8] tracking-wider">
                  {skill.domain} · <span className="font-mono text-[10px] font-medium">{skill.code}</span>
                </span>
                <span className="flex items-center gap-1 rounded-full bg-amber-50 px-2.5 py-0.5 text-xs font-semibold text-amber-800 anim-badge-pop">
                  <Sparkles size={12} /> Urgency: <NumberReveal value={skill.urgency_score} decimals={1} />
                </span>
              </div>

              <h3 className="text-lg font-bold tracking-tight text-[#123057] mt-3">
                {skill.name}
              </h3>

              <div className="mt-3 rounded-xl bg-slate-50 p-3 text-xs leading-relaxed text-slate-600">
                {skill.rationale}
              </div>

              <div className="mt-4 grid grid-cols-2 gap-2 text-xs">
                <div className="rounded-lg border border-slate-100 p-2.5">
                  <span className="text-[10px] uppercase font-semibold text-slate-400 tracking-wider">Demand Index</span>
                  <div className="text-sm font-extrabold text-[#123057] mt-0.5">
                    <NumberReveal value={skill.demand_index} suffix=" pts" />
                  </div>
                </div>
                <div className="rounded-lg border border-slate-100 p-2.5">
                  <span className="text-[10px] uppercase font-semibold text-slate-400 tracking-wider">Avg Deficit</span>
                  <div className="text-sm font-extrabold text-rose-600 mt-0.5">
                    <NumberReveal value={skill.average_gap_size} suffix=" pts" decimals={2} />
                  </div>
                </div>
              </div>
            </div>

            <div className="border-t border-slate-100 pt-3 flex items-center justify-between text-xs">
              <span className="text-slate-400 font-semibold truncate max-w-[240px]">
                {skill.recommended_focus}
              </span>
              <button
                onClick={() => onNavigate("Capacity Planning")}
                className="font-bold text-[#6d5bc3] hover:underline inline-flex items-center gap-1 shrink-0 btn-interactive"
              >
                Plan Interventions <ArrowRight size={11} />
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

export default EmergingSkills;
