import React, { useEffect, useState } from "react";
import {
  CalendarRange,
  CheckCircle2,
  Clock,
  Layers,
  Play,
  RefreshCw,
  TrendingUp,
  Users,
} from "lucide-react";
import { api, clearApiCache, CapacityPlanningResponse, CapacityInterventionItem } from "@/lib/api";
import { toast } from "sonner";
import { NumberReveal } from "@/components/motion/MotionUtils";

interface CapacityPlanningProps {
  onNavigate: (page: string) => void;
}

export function CapacityPlanning({ onNavigate }: CapacityPlanningProps) {
  const [data, setData] = useState<CapacityPlanningResponse | null>(null);
  const [loading, setLoading] = useState(true);

  const fetchCapacity = async () => {
    clearApiCache();
    try {
      setLoading(true);
      const res = await api.admin.capacityPlanning();
      setData(res);
    } catch (err: any) {
      toast.error(err.message || "Failed to load capacity planning");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCapacity();
  }, []);

  return (
    <div className="space-y-8 anim-page-enter max-w-6xl mx-auto">
      {/* Header */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between anim-fade-up">
        <div>
          <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-[#123057]">
            Capacity Planning & Interventions
          </h1>
          <p className="text-sm text-slate-500 mt-1">
            Prioritized training initiatives and curriculum demand to systematically eliminate organizational skill gaps.
          </p>
        </div>

        <button
          onClick={fetchCapacity}
          className="flex items-center gap-1.5 rounded-xl border border-[#e0daef] bg-white px-4 py-2 text-xs font-semibold text-[#4b36a8] shadow-sm hover:bg-purple-50 transition-all btn-interactive"
        >
          <RefreshCw size={14} className={loading ? "animate-spin" : ""} /> Refresh Plan
        </button>
      </div>

      {/* Summary KPI Row */}
      <div className="grid grid-cols-2 gap-4 sm:grid-cols-3">
        <div className="rounded-2xl border border-[#e0daef] bg-white p-5 shadow-sm anim-card-enter stagger-1">
          <div className="text-[10px] font-semibold uppercase tracking-wider text-slate-400">
            Total Target Personnel
          </div>
          <div className="mt-2 text-3xl font-extrabold tracking-tight text-[#123057]">
            <NumberReveal value={data?.total_officials_requiring_intervention ?? 0} suffix=" Officials" />
          </div>
          <div className="mt-1 text-xs text-slate-400 font-medium">Across planned cohorts</div>
        </div>

        <div className="rounded-2xl border border-[#e0daef] bg-white p-5 shadow-sm anim-card-enter stagger-2">
          <div className="text-[10px] font-semibold uppercase tracking-wider text-slate-400">
            Estimated Training Hours
          </div>
          <div className="mt-2 text-3xl font-extrabold tracking-tight text-[#6d5bc3]">
            <NumberReveal value={data?.total_training_hours_required ?? 0} suffix=" Hours" />
          </div>
          <div className="mt-1 text-xs text-slate-400 font-medium">Curriculum commitment</div>
        </div>

        <div className="rounded-2xl border border-[#e0daef] bg-white p-5 shadow-sm anim-card-enter stagger-3">
          <div className="text-[10px] font-semibold uppercase tracking-wider text-slate-400">
            Priority Initiatives
          </div>
          <div className="mt-2 text-3xl font-extrabold tracking-tight text-[#087f76]">
            <NumberReveal value={data?.high_priority_initiatives_count ?? 0} />
          </div>
          <div className="mt-1 text-xs text-slate-400 font-medium">High-impact capability targets</div>
        </div>
      </div>

      {/* Intervention Matrix */}
      <div className="rounded-3xl border border-[#e0daef] bg-white shadow-sm overflow-hidden p-6 space-y-6 anim-card-enter stagger-4">
        <h3 className="text-base font-bold text-[#123057] tracking-tight">
          Recommended Capacity-Building Interventions
        </h3>

        <div className="space-y-4">
          {(data?.interventions || []).map((item, idx) => (
            <div
              key={item.competency_code}
              className={`rounded-2xl border border-[#dfe7f0] bg-white p-5 hover:border-[#6d5bc3] hover:shadow-md transition-all card-interactive anim-card-enter stagger-${Math.min(idx + 1, 6)}`}
            >
              <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 border-b border-slate-100 pb-3">
                <div>
                  <span className="rounded-md bg-purple-50 px-2 py-0.5 text-[10px] font-semibold uppercase text-[#4b36a8] tracking-wider">
                    {item.domain} · <span className="font-mono text-[10px] font-medium">{item.competency_code}</span>
                  </span>
                  <h4 className="text-base font-bold text-[#123057] mt-1 tracking-tight">
                    {item.competency_name}
                  </h4>
                </div>

                <span className="rounded-full bg-rose-100 px-3 py-0.5 text-[10px] font-extrabold text-rose-800 self-start sm:self-auto anim-badge-pop">
                  {item.priority} Priority
                </span>
              </div>

              <div className="mt-4 grid grid-cols-2 gap-3 sm:grid-cols-4 text-xs">
                <div>
                  <span className="text-slate-400 font-semibold">Target Officials:</span>
                  <div className="font-bold text-[#123057] mt-0.5">
                    <NumberReveal value={item.target_officials_count} suffix=" personnel" />
                  </div>
                </div>
                <div>
                  <span className="text-slate-400 font-semibold">Suggested Cohort Size:</span>
                  <div className="font-bold text-[#123057] mt-0.5">
                    <NumberReveal value={item.suggested_cohort_size} suffix=" per batch" />
                  </div>
                </div>
                <div>
                  <span className="text-slate-400 font-semibold">Estimated Hours:</span>
                  <div className="font-bold text-[#123057] mt-0.5">
                    <NumberReveal value={item.estimated_training_hours} suffix=" hrs" />
                  </div>
                </div>
                <div>
                  <span className="text-slate-400 font-semibold">Top Resource Provider:</span>
                  <div className="font-bold text-[#087f76] mt-0.5">{item.top_resource_provider || "iGOT"}</div>
                </div>
              </div>

              {item.top_resource_title && (
                <div className="mt-3 rounded-xl bg-slate-50 p-3 text-xs text-slate-600">
                  <span className="font-bold text-slate-700">Recommended Curriculum:</span> {item.top_resource_title}
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

export default CapacityPlanning;
