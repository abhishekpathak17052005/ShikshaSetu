import React, { useEffect, useState } from "react";
import { AlertTriangle, Building2, CheckCircle2, Gauge, RefreshCw, Users } from "lucide-react";
import { api, WorkforceIntelligenceResponse } from "@/lib/api";
import { toast } from "sonner";

const KPI_ITEMS = [
  [Users, "Total officials", "bg-blue-50 text-blue-700"],
  [Building2, "Departments", "bg-amber-50 text-amber-700"],
  [Gauge, "Avg proficiency", "bg-teal-50 text-[#087f76]"],
  [AlertTriangle, "Active skill gaps", "bg-rose-50 text-rose-700"],
  [CheckCircle2, "Training completion", "bg-emerald-50 text-emerald-700"],
] as const;

const emptyFilters = { department: "", role: "", designation: "", competency_domain: "", gap_severity: "", training_status: "" };

export function WorkforceIntelligence() {
  const [filters, setFilters] = useState(emptyFilters);
  const [data, setData] = useState<WorkforceIntelligenceResponse | null>(null);
  const [loading, setLoading] = useState(true);

  const load = async (active = filters) => {
    try {
      setLoading(true);
      const params = Object.fromEntries(Object.entries(active).filter(([, value]) => value));
      setData(await api.admin.workforceIntelligence(params));
    } catch (error: any) {
      toast.error(error?.message || "Failed to load workforce intelligence");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []);

  const update = (key: keyof typeof filters, value: string) => setFilters((current) => ({ ...current, [key]: value }));
  const overview = data?.overview || {};
  const training = data?.training_effectiveness || {};

  return (
    <div className="space-y-6 anim-page-enter">
      <div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-end">
        <div>
          <div className="text-[10px] font-bold uppercase tracking-[0.14em] text-[#7c3aed]">Government Workforce Monitoring</div>
          <h1 className="mt-1 text-2xl font-extrabold tracking-tight text-[#123057]">Workforce Intelligence</h1>
          <p className="mt-1 text-sm text-slate-500">Understand the capability health of the government workforce using persisted assessment, learning and evidence data.</p>
        </div>
        <button onClick={() => load()} className="inline-flex items-center justify-center gap-2 rounded-xl border border-slate-200 bg-white px-3 py-2 text-xs font-bold text-slate-600 hover:bg-slate-50"><RefreshCw size={14} className={loading ? "animate-spin" : ""} /> Refresh</button>
      </div>

      <div className="grid gap-3 rounded-2xl border border-[#dfe7f0] bg-white p-4 shadow-xs sm:grid-cols-2 lg:grid-cols-3">
        {([ ["department", "Ministry / Department"], ["role", "Role"], ["designation", "Designation"], ["competency_domain", "Competency domain"] ] as const).map(([key, label]) => (
          <label key={key} className="text-[10px] font-bold uppercase tracking-wider text-slate-500">{label}<input value={filters[key]} onChange={(event) => update(key, event.target.value)} className="form-input !mt-1" placeholder={`Filter by ${label.toLowerCase()}`} /></label>
        ))}
        <label className="text-[10px] font-bold uppercase tracking-wider text-slate-500">Gap severity<select value={filters.gap_severity} onChange={(event) => update("gap_severity", event.target.value)} className="form-input !mt-1"><option value="">All severities</option><option>CRITICAL</option><option>HIGH</option><option>MEDIUM</option><option>LOW</option></select></label>
        <label className="text-[10px] font-bold uppercase tracking-wider text-slate-500">Training status<select value={filters.training_status} onChange={(event) => update("training_status", event.target.value)} className="form-input !mt-1"><option value="">All statuses</option><option value="assigned">Assigned</option><option value="in_progress">In progress</option><option value="completed">Completed</option></select></label>
        <button onClick={() => load()} className="self-end rounded-xl bg-[#123057] px-4 py-3 text-xs font-bold text-white hover:bg-[#1a416f]">Apply filters</button>
      </div>

      {loading && !data ? <div className="rounded-2xl border border-[#dfe7f0] bg-white p-8 text-sm text-slate-500">Loading workforce intelligence...</div> : data && <>
        <div className="grid grid-cols-2 gap-4 lg:grid-cols-5">
          {KPI_ITEMS.map(([Icon, label, tone]) => {
            const value = label === "Total officials" ? overview.total_officials ?? 0 : label === "Departments" ? overview.departments ?? 0 : label === "Avg proficiency" ? overview.average_proficiency == null ? "No data" : `${overview.average_proficiency}/5` : label === "Active skill gaps" ? overview.officials_with_active_skill_gaps ?? 0 : training.completion_rate_pct == null ? "No data" : `${training.completion_rate_pct}%`;
            return <div key={label} className="rounded-2xl border border-[#dfe7f0] bg-white p-4 shadow-xs"><div className={`flex h-9 w-9 items-center justify-center rounded-xl ${tone}`}><Icon size={17} /></div><div className="mt-3 text-2xl font-bold text-[#123057]">{value}</div><div className="mt-1 text-[10px] font-bold uppercase tracking-wider text-slate-400">{label}</div></div>;
          })}
        </div>

        <div className="grid gap-6 lg:grid-cols-2">
          <section className="rounded-2xl border border-[#dfe7f0] bg-white p-5 shadow-xs"><h2 className="text-base font-bold text-[#123057]">Competency intelligence</h2><p className="mt-1 text-xs text-slate-500">Persisted profiles and supporting evidence by competency.</p><div className="mt-4 space-y-3">{(data.competency_intelligence.competencies || []).slice(0, 10).map((item) => <div key={item.code} className="border-b border-slate-100 pb-3 last:border-0"><div className="flex justify-between gap-3 text-xs"><span className="font-semibold text-slate-700">{item.name} <span className="text-slate-400">{item.code}</span></span><span className="font-bold text-[#087f76]">{item.average_proficiency == null ? "No assessment" : `${item.average_proficiency}/5`}</span></div><div className="mt-1 flex justify-between text-[10px] text-slate-400"><span>{item.domain}</span><span>{item.supporting_evidence_count} supporting records</span></div></div>)}{!(data.competency_intelligence.competencies || []).length && <p className="text-xs text-slate-500">No competency profile data matches these filters.</p>}</div></section>
          <section className="rounded-2xl border border-[#dfe7f0] bg-white p-5 shadow-xs"><h2 className="text-base font-bold text-[#123057]">Department capability</h2><div className="mt-4 overflow-x-auto"><table className="w-full text-left text-xs"><thead className="text-[10px] uppercase tracking-wider text-slate-400"><tr><th className="pb-3">Department</th><th className="pb-3">Officials</th><th className="pb-3">Avg.</th><th className="pb-3">Critical gaps</th></tr></thead><tbody>{data.department_analysis.map((item) => <tr key={item.department} className="border-t border-slate-100"><td className="py-3 pr-3 font-semibold text-slate-700">{item.department}</td><td className="py-3">{item.officials}</td><td className="py-3">{item.average_proficiency == null ? "No data" : item.average_proficiency}</td><td className="py-3 font-bold text-rose-600">{item.critical_gaps}</td></tr>)}</tbody></table>{!data.department_analysis.length && <p className="py-4 text-xs text-slate-500">No department data matches these filters.</p>}</div></section>
        </div>
        <section className="rounded-2xl border border-[#dfe7f0] bg-white p-5 shadow-xs"><h2 className="text-base font-bold text-[#123057]">Workforce trends</h2><p className="mt-2 text-xs text-slate-500">{data.trends.message}. Trends are shown only when historical records exist.</p></section>
      </>}
    </div>
  );
}

export default WorkforceIntelligence;
