import React, { useState } from "react";
import {
  UserRound,
  Briefcase,
  Building,
  Mail,
  Shield,
  Save,
  CheckCircle2,
} from "lucide-react";
import { api, User } from "@/lib/api";
import { useAuth } from "@/contexts/AuthContext";
import { toast } from "sonner";

export function OfficialProfile() {
  const { user, updateUser } = useAuth();
  const [form, setForm] = useState({
    full_name: user?.full_name || "",
    employee_id: user?.employee_id || "",
    designation: user?.designation || "",
    department: user?.department || "",
  });
  const [saving, setSaving] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setSaving(true);
      const updated = await api.auth.updateProfile(form);
      updateUser(updated);
      toast.success("Profile details updated successfully!");
    } catch (err: any) {
      toast.error(err.message || "Failed to update profile");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="space-y-6 animate-fadeIn max-w-2xl mx-auto">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-black text-[#123057]">Employee Profile</h1>
        <p className="text-sm text-slate-500 mt-1">
          Civil service registration credentials and capability framework mapping.
        </p>
      </div>

      {/* Profile Overview Card */}
      <div className="rounded-3xl border border-[#dfe7f0] bg-white p-6 sm:p-8 shadow-sm space-y-6">
        <div className="flex items-center gap-4 border-b border-slate-100 pb-6">
          <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-[#123057] text-white text-2xl font-black">
            {user?.full_name?.charAt(0) || "O"}
          </div>
          <div>
            <span className="rounded-full bg-teal-100 px-3 py-0.5 text-xs font-extrabold text-teal-900">
              OFFICIAL / LEARNER
            </span>
            <h2 className="text-xl font-extrabold text-[#123057] mt-1">
              {user?.full_name}
            </h2>
            <p className="text-xs text-slate-400">{user?.email}</p>
          </div>
        </div>

        {/* Profile Edit Form */}
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid gap-4 sm:grid-cols-2">
            <div className="space-y-1.5 sm:col-span-2">
              <label className="block text-xs font-bold uppercase tracking-wider text-slate-500">
                Full Name
              </label>
              <input
                type="text"
                value={form.full_name}
                onChange={(e) => setForm({ ...form, full_name: e.target.value })}
                className="w-full rounded-xl border border-slate-200 px-4 py-2.5 text-sm text-[#123057] focus:border-[#087f76] focus:outline-none"
                required
              />
            </div>

            <div className="space-y-1.5">
              <label className="block text-xs font-bold uppercase tracking-wider text-slate-500">
                Employee ID
              </label>
              <input
                type="text"
                value={form.employee_id}
                onChange={(e) => setForm({ ...form, employee_id: e.target.value })}
                className="w-full rounded-xl border border-slate-200 px-4 py-2.5 text-sm text-[#123057] focus:border-[#087f76] focus:outline-none"
              />
            </div>

            <div className="space-y-1.5">
              <label className="block text-xs font-bold uppercase tracking-wider text-slate-500">
                Email Address (Permanent)
              </label>
              <input
                type="email"
                value={user?.email || ""}
                disabled
                className="w-full rounded-xl border border-slate-200 bg-slate-50 px-4 py-2.5 text-sm text-slate-400 cursor-not-allowed"
              />
            </div>

            <div className="space-y-1.5">
              <label className="block text-xs font-bold uppercase tracking-wider text-slate-500">
                Designation
              </label>
              <input
                type="text"
                value={form.designation}
                onChange={(e) => setForm({ ...form, designation: e.target.value })}
                className="w-full rounded-xl border border-slate-200 px-4 py-2.5 text-sm text-[#123057] focus:border-[#087f76] focus:outline-none"
              />
            </div>

            <div className="space-y-1.5">
              <label className="block text-xs font-bold uppercase tracking-wider text-slate-500">
                Department / Ministry
              </label>
              <input
                type="text"
                value={form.department}
                onChange={(e) => setForm({ ...form, department: e.target.value })}
                className="w-full rounded-xl border border-slate-200 px-4 py-2.5 text-sm text-[#123057] focus:border-[#087f76] focus:outline-none"
              />
            </div>
          </div>

          <div className="flex justify-end pt-4 border-t border-slate-100">
            <button
              type="submit"
              disabled={saving}
              className="inline-flex items-center gap-2 rounded-xl bg-[#087f76] px-6 py-2.5 text-xs font-bold text-white shadow hover:bg-[#06655e] disabled:opacity-50 transition-all active:scale-95"
            >
              <Save size={14} /> {saving ? "Saving Changes..." : "Save Profile Details"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

export default OfficialProfile;
