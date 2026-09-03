import React, { useState, useEffect } from "react";
import { Save, UserRound, Briefcase, GraduationCap, Award } from "lucide-react";
import { api } from "@/lib/api";
import { useAuth } from "@/contexts/AuthContext";
import { toast } from "sonner";

export function TrainerProfile() {
  const { user, updateUser } = useAuth();
  const [saving, setSaving] = useState(false);

  const [fullName, setFullName] = useState(user?.full_name || "");
  const [employeeId, setEmployeeId] = useState(user?.employee_id || "");
  const [designation, setDesignation] = useState(user?.designation || "");
  const [department, setDepartment] = useState(user?.department || "");
  const [organization, setOrganization] = useState(user?.organization || "");
  const [currentAssignment, setCurrentAssignment] = useState(user?.current_assignment || "");

  // Sync when user loads asynchronously
  useEffect(() => {
    if (!user) return;
    setFullName(user.full_name || "");
    setEmployeeId(user.employee_id || "");
    setDesignation(user.designation || "");
    setDepartment(user.department || "");
    setOrganization(user.organization || "");
    setCurrentAssignment(user.current_assignment || "");
  }, [user?.id]);

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!fullName.trim()) { toast.error("Full name is required."); return; }
    try {
      setSaving(true);
      const payload: Record<string, string> = {};
      if (fullName.trim()) payload.full_name = fullName.trim();
      if (employeeId.trim()) payload.employee_id = employeeId.trim();
      if (designation.trim()) payload.designation = designation.trim();
      if (department.trim()) payload.department = department.trim();
      if (organization.trim()) payload.organization = organization.trim();
      if (currentAssignment.trim()) payload.current_assignment = currentAssignment.trim();
      const updated = await api.auth.updateProfile(payload);
      updateUser(updated);
      toast.success("Profile saved.");
    } catch (err: any) {
      toast.error(err.message || "Failed to save profile.");
    } finally {
      setSaving(false);
    }
  };

  const inputCls = "w-full rounded-xl border border-slate-200 px-4 py-2.5 text-sm text-[#123057] focus:border-[#ef7e37] focus:outline-none transition-colors";
  const labelCls = "block text-[10px] font-bold uppercase tracking-wider text-slate-400 mb-1.5";

  return (
    <form onSubmit={handleSave} className="space-y-6 animate-fadeIn max-w-3xl mx-auto">
      {/* Header */}
      <div className="flex items-start justify-between gap-4 flex-wrap">
        <div>
          <h1 className="text-2xl font-black text-[#123057]">Trainer Profile</h1>
          <p className="text-sm text-slate-500 mt-1">
            Manage your curriculum creator credentials and professional details.
          </p>
        </div>
        <button
          type="submit"
          disabled={saving}
          className="inline-flex shrink-0 items-center gap-2 rounded-xl bg-[#ef7e37] px-6 py-2.5 text-xs font-bold text-white shadow hover:bg-[#d96a27] disabled:opacity-50 transition-all active:scale-95"
        >
          {saving ? (
            <>
              <svg className="animate-spin h-3.5 w-3.5" viewBox="0 0 24 24" fill="none">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"/>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z"/>
              </svg>
              Saving…
            </>
          ) : (<><Save size={14} /> Save Profile</>)}
        </button>
      </div>

      {/* Avatar card */}
      <div className="rounded-2xl border border-[#f0ddd0] bg-white p-6 shadow-sm">
        <div className="flex items-center gap-5">
          <div className="flex h-20 w-20 flex-shrink-0 items-center justify-center rounded-2xl bg-[#ef7e37] text-white text-3xl font-black select-none">
            {user?.full_name?.charAt(0)?.toUpperCase() || "T"}
          </div>
          <div className="min-w-0">
            <div className="flex items-center gap-2 flex-wrap">
              <span className="rounded-full bg-orange-100 px-3 py-0.5 text-xs font-extrabold text-[#c2510e]">
                TRAINER · CONTENT CREATOR
              </span>
            </div>
            <h2 className="text-xl font-extrabold text-[#123057] mt-1 truncate">{user?.full_name}</h2>
            <p className="text-xs text-slate-400 truncate">{user?.email}</p>
          </div>
        </div>
      </div>

      {/* Basic Information */}
      <div className="rounded-2xl border border-[#dfe7f0] bg-white p-6 shadow-sm space-y-4">
        <div className="flex items-center gap-2.5 pb-3 border-b border-slate-100">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-orange-50">
            <UserRound size={16} className="text-[#ef7e37]" />
          </div>
          <h2 className="text-sm font-bold text-[#123057]">Basic Information</h2>
        </div>
        <div className="grid gap-4 sm:grid-cols-2">
          <div>
            <label className={labelCls}>Full Name *</label>
            <input className={inputCls} value={fullName} onChange={e => setFullName(e.target.value)} placeholder="Full name" required />
          </div>
          <div>
            <label className={labelCls}>Employee ID</label>
            <input className={inputCls} value={employeeId} onChange={e => setEmployeeId(e.target.value)} placeholder="e.g. TRN-2024-001" />
          </div>
          <div>
            <label className={labelCls}>Official Email (Permanent)</label>
            <div className="rounded-xl border border-slate-100 bg-slate-50 px-4 py-2.5 text-sm text-slate-400 truncate">
              {user?.email || "—"}
            </div>
          </div>
          <div>
            <label className={labelCls}>Access Role</label>
            <div className="rounded-xl border border-slate-100 bg-slate-50 px-4 py-2.5 text-sm font-semibold text-[#c2510e]">
              Curriculum Trainer &amp; Evaluator
            </div>
          </div>
        </div>
      </div>

      {/* Employment Details */}
      <div className="rounded-2xl border border-[#dfe7f0] bg-white p-6 shadow-sm space-y-4">
        <div className="flex items-center gap-2.5 pb-3 border-b border-slate-100">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-orange-50">
            <Briefcase size={16} className="text-[#ef7e37]" />
          </div>
          <h2 className="text-sm font-bold text-[#123057]">Employment Details</h2>
        </div>
        <div className="grid gap-4 sm:grid-cols-2">
          <div>
            <label className={labelCls}>Designation</label>
            <input className={inputCls} value={designation} onChange={e => setDesignation(e.target.value)} placeholder="e.g. Senior Curriculum Developer" />
          </div>
          <div>
            <label className={labelCls}>Department / Ministry</label>
            <input className={inputCls} value={department} onChange={e => setDepartment(e.target.value)} placeholder="e.g. Ministry of Statistics & PI" />
          </div>
          <div>
            <label className={labelCls}>Organization / Office</label>
            <input className={inputCls} value={organization} onChange={e => setOrganization(e.target.value)} placeholder="e.g. NSSTA, New Delhi" />
          </div>
          <div>
            <label className={labelCls}>Current Assignment</label>
            <input className={inputCls} value={currentAssignment} onChange={e => setCurrentAssignment(e.target.value)} placeholder="e.g. Statistical Training Programme Lead" />
          </div>
        </div>
      </div>

      {/* Bottom save */}
      <div className="flex justify-end pb-8">
        <button
          type="submit"
          disabled={saving}
          className="inline-flex items-center gap-2 rounded-xl bg-[#ef7e37] px-8 py-3 text-sm font-bold text-white shadow hover:bg-[#d96a27] disabled:opacity-50 transition-all active:scale-95"
        >
          {saving ? "Saving changes…" : <><Save size={16} /> Save Profile Changes</>}
        </button>
      </div>
    </form>
  );
}

export default TrainerProfile;
