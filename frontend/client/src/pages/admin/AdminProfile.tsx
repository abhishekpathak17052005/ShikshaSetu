import React from "react";
import { ShieldCheck, UserRound, Building2, Briefcase, Mail } from "lucide-react";
import { useAuth } from "@/contexts/AuthContext";

export function AdminProfile() {
  const { user } = useAuth();

  return (
    <div className="max-w-2xl mx-auto rounded-3xl border border-[#e0daef] bg-white p-8 shadow-sm space-y-6 animate-fadeIn">
      <div className="flex items-center gap-4 border-b border-slate-100 pb-6">
        <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-[#4b36a8] text-white text-2xl font-black">
          {user?.full_name?.charAt(0) || "A"}
        </div>
        <div>
          <span className="rounded-full bg-purple-100 px-3 py-0.5 text-xs font-bold text-[#4b36a8]">
            ADMINISTRATOR
          </span>
          <h2 className="text-xl font-extrabold text-[#123057] mt-1">
            {user?.full_name}
          </h2>
          <p className="text-xs text-slate-400">{user?.email}</p>
        </div>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 text-xs">
        <div className="rounded-2xl bg-slate-50 p-4 border border-slate-100">
          <div className="font-bold text-slate-400 uppercase tracking-wider text-[10px]">
            Designation
          </div>
          <div className="text-sm font-black text-[#123057] mt-1">
            {user?.designation || "Director (Admin & Governance)"}
          </div>
        </div>

        <div className="rounded-2xl bg-slate-50 p-4 border border-slate-100">
          <div className="font-bold text-slate-400 uppercase tracking-wider text-[10px]">
            Department
          </div>
          <div className="text-sm font-black text-[#123057] mt-1">
            {user?.department || "Department of Personnel and Training (DoPT)"}
          </div>
        </div>

        <div className="rounded-2xl bg-slate-50 p-4 border border-slate-100">
          <div className="font-bold text-slate-400 uppercase tracking-wider text-[10px]">
            Employee ID
          </div>
          <div className="text-sm font-black text-[#123057] mt-1">
            {user?.employee_id || "ADM-001"}
          </div>
        </div>

        <div className="rounded-2xl bg-slate-50 p-4 border border-slate-100">
          <div className="font-bold text-slate-400 uppercase tracking-wider text-[10px]">
            Governance Clearance
          </div>
          <div className="text-sm font-black text-emerald-700 mt-1">
            Full Organizational Intelligence Access
          </div>
        </div>
      </div>
    </div>
  );
}

export default AdminProfile;
