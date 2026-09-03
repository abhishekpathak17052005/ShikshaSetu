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
    <div className="space-y-8 animate-fadeIn max-w-6xl mx-auto">
      {/* Header */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl sm:text-3xl font-black text-[#123057]">
            Capacity Planning & Interventions
          </h1>
          <p className="text-sm text-slate-500 mt-1">
            Prioritized training initiatives and curriculum demand to systematically eliminate organizational skill gaps.
          </p>
        </div>

        <button
          onClick={fetchCapacity}
          className="flex items-center gap-1.5 rounded-xl border border-[#e0daef] bg-white px-4 py-2 text-xs font-bold text-[#4b36a8] shadow-sm hover:bg-purple-50 transition-all"
        >
          <RefreshCw size={14} className={loading ? "animate-spin" : ""} /> Refresh Plan
        </button>
      </div>

      {/* Summary KPI Row */}
      <div className="grid grid-cols-2 gap-4 sm:grid-cols-3">
        <div className="rounded-2xl border border-[#e0daef] bg-white p-5 shadow-sm">
          <div className="text-[10px] font-extrabold uppercase tracking-wider text-slate-400">
            Total Target Personnel
          </div>
          <div className="mt-2 text-3xl font-black text-[#123057]">
            {data?.total_officials_requiring_intervention ?? 0} Officials
          </div>
          <div className="mt-1 text-xs text-slate-400 font-semibold">Across planned cohorts</div>
        </div>

        <div className="rounded-2xl border border-[#e0daef] bg-white p-5 shadow-sm">
          <div className="text-[10px] font-extrabold uppercase tracking-wider text-slate-400">
            Estimated Training Hours
          </div>
          <div className="mt-2 text-3xl font-black text-[#6d5bc3]">
            {data?.total_training_hours_required ?? 0} Hours
          </div>
          <div className="mt-1 text-xs text-slate-400 font-semibold">Curriculum commitment</div>
        </div>

        <div className="rounded-2xl border border-[#e0daef] bg-white p-5 shadow-sm">
          <div className="text-[10px] font-extrabold uppercase tracking-wider text-slate-400">
            Priority Initiatives
          </div>
          <div className="mt-2 text-3xl font-black text-[#087f76]">
            {data?.high_priority_initiatives_count ?? 0}
          </div>
          <div className="mt-1 text-xs text-slate-400 font-semibold">High-impact capability targets</div>
        </div>
      </div>

      {/* Intervention Matrix */}
      <div className="rounded-3xl border border-[#e0daef] bg-white shadow-sm overflow-hidden p-6 space-y-6">
        <h3 className="text-base font-bold text-[#123057]">
          Recommended Capacity-Building Interventions
        </h3>

        <div className="space-y-4">
          {(data?.interventions || []).map((item) => (
            <div
              key={item.competency_code}
              className="rounded-2xl border border-[#dfe7f0] bg-white p-5 hover:border-[#6d5bc3] hover:shadow-md transition-all"
            >
              <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 border-b border-slate-100 pb-3">
                <div>
                  <span className="rounded-md bg-purple-50 px-2 py-0.5 text-[10px] font-extrabold uppercase text-[#4b36a8]">
                    {item.domain} · {item.competency_code}
                  </span>
                  <h4 className="text-base font-bold text-[#123057] mt-1">
                    {item.competency_name}
                  </h4>
                </div>

                <span className="rounded-full bg-rose-100 px-3 py-0.5 text-[10px] font-extrabold text-rose-800 self-start sm:self-auto">
                  {item.priority} Priority
                </span>
              </div>

              <div className="mt-4 grid grid-cols-2 gap-3 sm:grid-cols-4 text-xs">
                <div>
                  <span className="text-slate-400 font-semibold">Target Officials:</span>
                  <div className="font-bold text-[#123057] mt-0.5">{item.target_officials_count} personnel</div>
                </div>
                <div>
                  <span className="text-slate-400 font-semibold">Suggested Cohort Size:</span>
                  <div className="font-bold text-[#123057] mt-0.5">{item.suggested_cohort_size} per batch</div>
                </div>
                <div>
                  <span className="text-slate-400 font-semibold">Estimated Hours:</span>
                  <div className="font-bold text-[#123057] mt-0.5">{item.estimated_training_hours} hrs</div>
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
