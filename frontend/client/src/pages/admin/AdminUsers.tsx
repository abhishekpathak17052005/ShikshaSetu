import React, { useEffect, useState } from "react";
import {
  Building2,
  Filter,
  RefreshCw,
  Search,
  ShieldCheck,
  UserCheck,
  Users,
} from "lucide-react";
import { api, clearApiCache, AdminUserListResponse, AdminUserItem } from "@/lib/api";
import { toast } from "sonner";

interface AdminUsersProps {
  onNavigate: (page: string) => void;
}

export function AdminUsers({ onNavigate }: AdminUsersProps) {
  const [data, setData] = useState<AdminUserListResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedRole, setSelectedRole] = useState("ALL");

  const fetchUsers = async () => {
    clearApiCache();
    try {
      setLoading(true);
      const res = await api.admin.users();
      setData(res);
    } catch (err: any) {
      toast.error(err.message || "Failed to load user directory");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchUsers();
  }, []);

  const filteredUsers = (data?.users || []).filter((u) => {
    const matchSearch =
      !searchQuery ||
      u.full_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      u.email.toLowerCase().includes(searchQuery.toLowerCase()) ||
      u.employee_id.toLowerCase().includes(searchQuery.toLowerCase());
    const matchRole = selectedRole === "ALL" || u.access_role === selectedRole;
    return matchSearch && matchRole;
  });

  return (
    <div className="space-y-8 anim-page-enter max-w-6xl mx-auto">
      {/* Header */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between anim-fade-up">
        <div>
          <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-[#123057]">
            User & Access Directory
          </h1>
          <p className="text-sm text-slate-500 mt-1">
            Active civil servants, curriculum trainers, and system administrators across the portal.
          </p>
        </div>

        <button
          onClick={fetchUsers}
          className="flex items-center gap-1.5 rounded-xl border border-[#e0daef] bg-white px-4 py-2 text-xs font-semibold text-[#4b36a8] shadow-sm hover:bg-purple-50 transition-all btn-interactive"
        >
          <RefreshCw size={14} className={loading ? "animate-spin" : ""} /> Refresh Users
        </button>
      </div>

      {/* Filter and Search */}
      <div className="flex flex-col gap-3 rounded-2xl border border-[#e0daef] bg-white p-4 sm:flex-row sm:items-center anim-card-enter stagger-1">
        <div className="relative flex-1">
          <Search size={16} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400" />
          <input
            type="text"
            placeholder="Search users by name, email, employee ID..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full rounded-xl border border-slate-200 bg-slate-50/50 py-2 pl-9 pr-4 text-xs font-semibold text-slate-800 placeholder-slate-400 focus:border-[#6d5bc3] focus:bg-white focus:outline-none transition-all"
          />
        </div>

        <div className="flex items-center gap-2">
          <Filter size={15} className="text-slate-400" />
          <select
            value={selectedRole}
            onChange={(e) => setSelectedRole(e.target.value)}
            className="rounded-xl border border-slate-200 bg-white px-3 py-2 text-xs font-semibold text-slate-700 focus:outline-none transition-all"
          >
            <option value="ALL">All Access Roles</option>
            <option value="OFFICIAL">Official / Employee</option>
            <option value="TRAINER">Trainer</option>
            <option value="ADMIN">Administrator</option>
          </select>
        </div>
      </div>

      {/* User Table */}
      <div className="rounded-3xl border border-[#e0daef] bg-white shadow-sm overflow-hidden anim-card-enter stagger-2">
        <div className="px-6 py-4 border-b border-slate-100 flex items-center justify-between">
          <h3 className="text-sm font-bold text-[#123057]">
            System Users Directory ({filteredUsers.length})
          </h3>
          <span className="text-xs text-slate-400 font-medium">
            Role-Based Access Control
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-[#f8f6fd] text-[10px] font-semibold uppercase tracking-wider text-slate-500 border-b border-[#e0daef]">
              <tr>
                <th className="px-6 py-3.5">User</th>
                <th className="px-6 py-3.5">Department</th>
                <th className="px-6 py-3.5">Professional Role</th>
                <th className="px-6 py-3.5">Access Role</th>
                <th className="px-6 py-3.5">Status</th>
                <th className="px-6 py-3.5">Registered</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {filteredUsers.map((user, idx) => (
                <tr
                  key={user.id}
                  className={`hover:bg-purple-50/40 transition-colors anim-card-enter stagger-${Math.min(idx + 1, 6)}`}
                >
                  <td className="px-6 py-4">
                    <div className="font-bold text-[#123057]">{user.full_name}</div>
                    <div className="text-[11px] text-slate-400">{user.email} · <span className="font-mono text-[10px] font-medium tracking-tight">{user.employee_id}</span></div>
                  </td>
                  <td className="px-6 py-4 font-semibold text-slate-600">
                    {user.department}
                  </td>
                  <td className="px-6 py-4">
                    <div className="font-bold text-[#4b36a8]">{user.professional_role}</div>
                    <div className="text-[11px] text-slate-400">{user.designation}</div>
                  </td>
                  <td className="px-6 py-4">
                    <span
                      className={`rounded-full px-2.5 py-0.5 text-[10px] font-extrabold anim-badge-pop ${
                        user.access_role === "ADMIN"
                          ? "bg-purple-100 text-[#4b36a8]"
                          : user.access_role === "TRAINER"
                          ? "bg-orange-100 text-orange-800"
                          : "bg-teal-100 text-teal-800"
                      }`}
                    >
                      {user.access_role}
                    </span>
                  </td>
                  <td className="px-6 py-4">
                    <span className="rounded-full bg-emerald-50 px-2.5 py-0.5 text-[10px] font-extrabold text-emerald-800 anim-badge-pop">
                      Active
                    </span>
                  </td>
                  <td className="px-6 py-4 text-slate-400 text-[11px]">
                    {new Date(user.created_at).toLocaleDateString()}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

export default AdminUsers;
