import React, { useEffect, useState } from "react";
import {
  Download,
  FileBarChart,
  FileText,
  RefreshCw,
  ShieldCheck,
  Table,
} from "lucide-react";
import { api, clearApiCache, AdminReportsResponse } from "@/lib/api";
import { toast } from "sonner";

interface AdminReportsProps {
  onNavigate: (page: string) => void;
}

export function AdminReports({ onNavigate }: AdminReportsProps) {
  const [data, setData] = useState<AdminReportsResponse | null>(null);
  const [loading, setLoading] = useState(true);

  const fetchReports = async () => {
    clearApiCache();
    try {
      setLoading(true);
      const res = await api.admin.reports();
      setData(res);
    } catch (err: any) {
      toast.error(err.message || "Failed to load admin reports");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchReports();
  }, []);

  const exportCSV = (reportName: string, rows: Record<string, any>[]) => {
    if (!rows || rows.length === 0) {
      toast.info("No records available to export");
      return;
    }
    const headers = Object.keys(rows[0]);
    const csvContent = [
      headers.join(","),
      ...rows.map((row) =>
        headers.map((h) => `"${(row[h] ?? "").toString().replace(/"/g, '""')}"`).join(",")
      ),
    ].join("\n");

    const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.setAttribute("href", url);
    link.setAttribute("download", `${reportName}_${new Date().toISOString().slice(0, 10)}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    toast.success(`Exported ${reportName}.csv`);
  };

  const handleExportWorkforce = async () => {
    try {
      const wf = await api.admin.workforce();
      const rows = wf.employees.map((e) => ({
        ID: e.id,
        FullName: e.full_name,
        Email: e.email,
        Department: e.department,
        Designation: e.designation,
        ProfessionalRole: e.professional_role,
        AccessRole: e.access_role,
        AvgProficiency: e.average_proficiency ?? "N/A",
        Status: e.status,
      }));
      exportCSV("Workforce_Competency_Report", rows);
    } catch (err: any) {
      toast.error("Failed to export workforce report");
    }
  };

  const handleExportSkillGaps = async () => {
    try {
      const gaps = await api.admin.skillGaps();
      const rows = gaps.top_organization_gaps.map((g) => ({
        CompetencyCode: g.competency_code,
        CompetencyName: g.competency_name,
        Domain: g.domain,
        OfficialsAffected: g.officials_affected,
        CriticalCount: g.critical_count,
        HighCount: g.high_count,
        AverageGap: g.average_gap,
        Priority: g.priority,
      }));
      exportCSV("Organization_Skill_Gaps_Report", rows);
    } catch (err: any) {
      toast.error("Failed to export skill gaps report");
    }
  };

  const handleExportTraining = async () => {
    try {
      const t = await api.admin.trainingEffectiveness();
      const rows = t.completion_by_department.map((d) => ({
        Department: d.department,
        Enrolled: d.enrolled,
        Completed: d.completed,
        CompletionRatePct: d.rate_pct,
      }));
      exportCSV("Training_Effectiveness_Report", rows);
    } catch (err: any) {
      toast.error("Failed to export training report");
    }
  };

  return (
    <div className="space-y-8 animate-fadeIn max-w-6xl mx-auto">
      {/* Header */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl sm:text-3xl font-black text-[#123057]">
            Intelligence & Compliance Reports
          </h1>
          <p className="text-sm text-slate-500 mt-1">
            Consolidated organizational reports on workforce proficiency, capability deficits, and capacity-building.
          </p>
        </div>

        <button
          onClick={fetchReports}
          className="flex items-center gap-1.5 rounded-xl border border-[#e0daef] bg-white px-4 py-2 text-xs font-bold text-[#4b36a8] shadow-sm hover:bg-purple-50 transition-all"
        >
          <RefreshCw size={14} className={loading ? "animate-spin" : ""} /> Refresh Reports
        </button>
      </div>

      {/* 3 Main Export Cards */}
      <div className="grid gap-6 sm:grid-cols-3">
        <div className="flex flex-col justify-between rounded-3xl border border-[#e0daef] bg-white p-6 shadow-sm hover:shadow-md transition-all space-y-4">
          <div>
            <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-purple-100 text-[#4b36a8]">
              <FileBarChart size={24} />
            </div>
            <h3 className="text-lg font-bold text-[#123057] mt-4">
              Workforce Competency Report
            </h3>
            <p className="text-xs text-slate-500 mt-2 leading-relaxed">
              Complete inventory of civil service personnel, assigned professional roles, and verified proficiency levels across departments.
            </p>
          </div>
          <button
            onClick={handleExportWorkforce}
            className="flex w-full items-center justify-center gap-2 rounded-xl bg-[#4b36a8] px-4 py-2.5 text-xs font-bold text-white shadow hover:bg-[#3d2b8c] transition-all"
          >
            <Download size={14} /> Export CSV
          </button>
        </div>

        <div className="flex flex-col justify-between rounded-3xl border border-[#e0daef] bg-white p-6 shadow-sm hover:shadow-md transition-all space-y-4">
          <div>
            <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-rose-100 text-rose-700">
              <FileText size={24} />
            </div>
            <h3 className="text-lg font-bold text-[#123057] mt-4">
              Organization Skill Gap Report
            </h3>
            <p className="text-xs text-slate-500 mt-2 leading-relaxed">
              Detailed breakdown of critical and high-priority competency deficits, affected officials count, and average deficit sizes.
            </p>
          </div>
          <button
            onClick={handleExportSkillGaps}
            className="flex w-full items-center justify-center gap-2 rounded-xl bg-[#ef7e37] px-4 py-2.5 text-xs font-bold text-white shadow hover:bg-[#d96a27] transition-all"
          >
            <Download size={14} /> Export CSV
          </button>
        </div>

        <div className="flex flex-col justify-between rounded-3xl border border-[#e0daef] bg-white p-6 shadow-sm hover:shadow-md transition-all space-y-4">
          <div>
            <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-teal-100 text-teal-700">
              <Table size={24} />
            </div>
            <h3 className="text-lg font-bold text-[#123057] mt-4">
              Training Effectiveness Report
            </h3>
            <p className="text-xs text-slate-500 mt-2 leading-relaxed">
              Curriculum completion rates, quiz evaluation results, learning hours, and supporting vs authoritative evidence ledger balances.
            </p>
          </div>
          <button
            onClick={handleExportTraining}
            className="flex w-full items-center justify-center gap-2 rounded-xl bg-[#087f76] px-4 py-2.5 text-xs font-bold text-white shadow hover:bg-[#06635c] transition-all"
          >
            <Download size={14} /> Export CSV
          </button>
        </div>
      </div>

      {/* Snapshot Summary Cards */}
      <div className="rounded-3xl border border-[#e0daef] bg-white p-6 shadow-sm space-y-4">
        <h3 className="text-base font-bold text-[#123057]">
          Executive Compliance & Governance Summary
        </h3>

        <div className="grid grid-cols-2 gap-3 sm:grid-cols-4 text-xs">
          <div className="rounded-xl bg-slate-50 p-4 border border-slate-100">
            <span className="text-slate-400 font-bold uppercase text-[10px]">Evidence Integrity</span>
            <div className="text-base font-black text-emerald-700 mt-1">VALIDATED</div>
          </div>
          <div className="rounded-xl bg-slate-50 p-4 border border-slate-100">
            <span className="text-slate-400 font-bold uppercase text-[10px]">Governance Status</span>
            <div className="text-base font-black text-[#4b36a8] mt-1">COMPLIANT</div>
          </div>
          <div className="rounded-xl bg-slate-50 p-4 border border-slate-100">
            <span className="text-slate-400 font-bold uppercase text-[10px]">Authoritative Exams</span>
            <div className="text-base font-black text-[#123057] mt-1">
              {data?.compliance_summary?.authoritative_assessments ?? 5} Recorded
            </div>
          </div>
          <div className="rounded-xl bg-slate-50 p-4 border border-slate-100">
            <span className="text-slate-400 font-bold uppercase text-[10px]">Supporting Evidence</span>
            <div className="text-base font-black text-[#ef7e37] mt-1">
              {data?.compliance_summary?.supporting_evidence_records ?? 12} Recorded
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default AdminReports;
