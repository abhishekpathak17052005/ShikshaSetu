import { useEffect, useState, useMemo } from "react";
import { toast } from "sonner";
import { Eye, EyeOff, Building2, Briefcase, Award, CheckCircle2 } from "lucide-react";
import { api } from "@/lib/api";
import { useAuth } from "@/contexts/AuthContext";
import type { Role } from "@/lib/api";
import { DEPARTMENT_TAXONOMY } from "@/lib/departments";

export default function LoginPage() {
  const { login } = useAuth();
  const [isRegister, setIsRegister] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [roles, setRoles] = useState<Role[]>([]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  // Registration fields
  const [fullName, setFullName] = useState("");
  const [employeeId, setEmployeeId] = useState("");
  const [department, setDepartment] = useState("");
  const [selectedRoleCode, setSelectedRoleCode] = useState("");
  const [selectedRoleId, setSelectedRoleId] = useState("");
  const [designation, setDesignation] = useState("");
  const [customDesignation, setCustomDesignation] = useState("");
  const [isCustomDesignation, setIsCustomDesignation] = useState(false);

  // Shared fields
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  useEffect(() => {
    api.roles
      .list()
      .then((data) => {
        setRoles(data || []);
      })
      .catch(() => undefined);
  }, []);

  // Department-filtered available roles
  const availableRoles = useMemo(() => {
    if (!department) return [];
    const deptObj = DEPARTMENT_TAXONOMY.find((d) => d.department_name === department);
    if (!deptObj) return [];
    return deptObj.roles;
  }, [department]);

  // Selected role configuration & description
  const selectedRoleConfig = useMemo(() => {
    return availableRoles.find((r) => r.role_code === selectedRoleCode);
  }, [availableRoles, selectedRoleCode]);

  // Role-filtered available designations
  const availableDesignations = useMemo(() => {
    return selectedRoleConfig ? selectedRoleConfig.designations : [];
  }, [selectedRoleConfig]);

  // Handle Department Change
  const handleDepartmentChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const nextDept = e.target.value;
    setDepartment(nextDept);
    // Reset cascading fields
    setSelectedRoleCode("");
    setSelectedRoleId("");
    setDesignation("");
    setCustomDesignation("");
    setIsCustomDesignation(false);
  };

  // Handle Role Change
  const handleRoleChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const nextRoleCode = e.target.value;
    setSelectedRoleCode(nextRoleCode);

    // Match backend role ID if available
    const matchedBackendRole = roles.find(
      (r) => r.role_code === nextRoleCode || r.role_name === nextRoleCode
    );
    if (matchedBackendRole) {
      setSelectedRoleId(matchedBackendRole.id);
    } else if (roles.length > 0) {
      setSelectedRoleId(roles[0].id);
    }

    // Reset designation
    setDesignation("");
    setCustomDesignation("");
    setIsCustomDesignation(false);
  };

  // Handle Designation Change
  const handleDesignationChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const val = e.target.value;
    if (val === "__custom__") {
      setIsCustomDesignation(true);
      setDesignation("");
    } else {
      setIsCustomDesignation(false);
      setDesignation(val);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setBusy(true);
    setError("");

    try {
      if (isRegister) {
        const finalDesignation = isCustomDesignation
          ? customDesignation.trim()
          : designation.trim();

        if (!department) {
          throw new Error("Please select your Department / Ministry");
        }
        if (!selectedRoleCode) {
          throw new Error("Please select your Professional Role");
        }
        if (!finalDesignation) {
          throw new Error("Please select or enter your Designation");
        }

        // Resolve active role ID for backend registration
        let resolvedRoleId = selectedRoleId;
        if (!resolvedRoleId) {
          const matched = roles.find(
            (r) => r.role_code === selectedRoleCode || r.role_name === selectedRoleCode
          );
          resolvedRoleId = matched ? matched.id : roles[0]?.id;
        }

        await api.auth.register({
          full_name: fullName.trim(),
          employee_id: employeeId.trim(),
          designation: finalDesignation,
          department: department.trim(),
          role_id: resolvedRoleId || "6a8ff00dbda6ad0866e7667c",
          email: email.trim(),
          password: password.trim(),
        });

        toast.success("Account created successfully. Please sign in.");
        setIsRegister(false);
        setPassword("");
      } else {
        await login(email.trim(), password.trim());
      }
    } catch (err: unknown) {
      const message =
        err instanceof Error ? err.message : "Something went wrong. Please try again.";
      setError(message);
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="flex min-h-screen">
      {/* ── Left panel (decorative) ── */}
      <div className="hidden lg:flex flex-col justify-between bg-[#123057] text-white w-[440px] flex-shrink-0 p-12">
        <div>
          <div className="flex items-center gap-3 mb-12">
            <img
              src="/shikshasetu-icon.svg"
              alt=""
              aria-hidden="true"
              className="h-12 w-12 brightness-0 invert opacity-90"
            />
            <div>
              <div className="text-xl font-extrabold tracking-tight">ShikshaSetu</div>
              <div className="text-[10px] font-bold uppercase tracking-[.18em] text-blue-300">
                Capability Intelligence
              </div>
            </div>
          </div>

          <div className="space-y-6">
            <div>
              <div className="text-3xl font-extrabold leading-tight mb-4 tracking-tight">
                Empowering India's Civil Services through capability intelligence
              </div>
              <p className="text-sm text-blue-200 leading-6">
                A unified platform for department-specific skill gap analysis, AI-driven learning,
                and verifiable professional growth — built for Smart India Hackathon.
              </p>
            </div>

            <div className="space-y-3 pt-4">
              {[
                "Ministry & Department-specific competency frameworks",
                "Role-targeted AI skill gap calculation",
                "Curated iGOT Karmayogi & NSSTA learning tracks",
                "Continuous competency evidence & assessment",
              ].map((item) => (
                <div key={item} className="flex items-start gap-3 text-sm text-blue-100">
                  <div className="h-1.5 w-1.5 rounded-full bg-[#0f9f92] flex-shrink-0 mt-2" />
                  <span>{item}</span>
                </div>
              ))}
            </div>
          </div>
        </div>

        <div className="rounded-2xl bg-white/5 p-4 border border-white/10 text-[11px] text-blue-200">
          <div className="font-bold text-white mb-1 flex items-center gap-1.5">
            <CheckCircle2 size={13} className="text-[#0f9f92]" />
            Multi-Department Architecture
          </div>
          <div>
            Supports Ministry of Education, MoSPI, MeitY, DoPT, Finance, Health, Rural Development &amp; more.
          </div>
        </div>
      </div>

      {/* ── Right panel (form) ── */}
      <div className="flex flex-1 items-center justify-center bg-[#eef4f8] px-5 py-10">
        <div className="w-full max-w-[480px]">
          {/* Mobile logo */}
          <div className="mb-6 flex items-center gap-2 lg:hidden">
            <img
              src="/shikshasetu-icon.svg"
              alt="ShikshaSetu"
              className="h-9 w-9"
            />
            <span className="text-xl font-extrabold text-[#123057]">ShikshaSetu</span>
          </div>

          <div className="rounded-3xl border border-[#dfe7f0] bg-white p-8 shadow-xl">
            {/* Header */}
            <div className="mb-6">
              <div className="mb-3 inline-flex items-center gap-2 rounded-full border border-[#0f9f92]/20 bg-[#e8f6f3] px-3 py-1 text-[11px] font-bold text-[#0f9f92]">
                Smart India Hackathon · Capability Intelligence
              </div>
              <div className="text-2xl font-extrabold text-[#123057]">
                {isRegister ? "Create account" : "Welcome back"}
              </div>
              <p className="mt-1 text-xs text-slate-500">
                {isRegister
                  ? "Select your department, role, and designation to initialize your tailored framework"
                  : "Sign in to your capability workspace"}
              </p>
            </div>

            {/* Error banner */}
            {error && (
              <div className="mb-4 rounded-xl bg-red-50 px-4 py-3 text-xs font-semibold text-red-700 border border-red-100 animate-fadeIn">
                {error}
              </div>
            )}

            {/* Form */}
            <form onSubmit={handleSubmit} className="space-y-3.5">
              {isRegister && (
                <>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                    <div>
                      <label className="text-[10px] font-bold uppercase tracking-wider text-slate-500">
                        Full Name *
                      </label>
                      <input
                        className="form-input !mt-1"
                        placeholder="e.g. Abhishek Pathak"
                        value={fullName}
                        onChange={(e) => setFullName(e.target.value)}
                        required
                      />
                    </div>

                    <div>
                      <label className="text-[10px] font-bold uppercase tracking-wider text-slate-500">
                        Employee ID *
                      </label>
                      <input
                        className="form-input !mt-1"
                        placeholder="e.g. EDU-TEACH-2024"
                        value={employeeId}
                        onChange={(e) => setEmployeeId(e.target.value)}
                        required
                      />
                    </div>
                  </div>

                  {/* 1. Department Selector */}
                  <div>
                    <label className="text-[10px] font-bold uppercase tracking-wider text-slate-500 flex items-center gap-1.5">
                      <Building2 size={12} className="text-[#0f9f92]" />
                      Department / Ministry *
                    </label>
                    <select
                      className="form-input !mt-1 bg-slate-50/50 cursor-pointer font-bold text-[#123057]"
                      value={department}
                      onChange={handleDepartmentChange}
                      required
                    >
                      <option value="">Select Department / Ministry</option>
                      {DEPARTMENT_TAXONOMY.map((dept) => (
                        <option key={dept.department_code} value={dept.department_name}>
                          {dept.department_name}
                        </option>
                      ))}
                    </select>
                  </div>

                  {/* 2. Professional Role Selector (Filtered by Department) */}
                  <div>
                    <label className="text-[10px] font-bold uppercase tracking-wider text-slate-500 flex items-center gap-1.5">
                      <Briefcase size={12} className="text-[#ef7e37]" />
                      Professional Role *
                    </label>
                    <select
                      className={`form-input !mt-1 cursor-pointer font-bold ${
                        !department ? "bg-slate-100 text-slate-400 cursor-not-allowed" : "text-[#123057]"
                      }`}
                      value={selectedRoleCode}
                      onChange={handleRoleChange}
                      disabled={!department}
                      required
                    >
                      <option value="">
                        {!department ? "← Select department above first" : "Select professional role"}
                      </option>
                      {availableRoles.map((role) => (
                        <option key={role.role_code} value={role.role_code}>
                          {role.role_name}
                        </option>
                      ))}
                    </select>
                    {selectedRoleConfig && (
                      <p className="mt-1 text-[11px] text-slate-500 leading-tight">
                        <span className="font-semibold text-teal-800">Domain:</span> {selectedRoleConfig.domain} · {selectedRoleConfig.description}
                      </p>
                    )}
                  </div>

                  {/* 3. Designation Selector (Filtered by Role) */}
                  <div>
                    <label className="text-[10px] font-bold uppercase tracking-wider text-slate-500 flex items-center gap-1.5">
                      <Award size={12} className="text-[#6d5bc3]" />
                      Designation *
                    </label>
                    <select
                      className={`form-input !mt-1 cursor-pointer font-bold ${
                        !selectedRoleCode ? "bg-slate-100 text-slate-400 cursor-not-allowed" : "text-[#123057]"
                      }`}
                      value={isCustomDesignation ? "__custom__" : designation}
                      onChange={handleDesignationChange}
                      disabled={!selectedRoleCode}
                      required={!isCustomDesignation}
                    >
                      <option value="">
                        {!selectedRoleCode
                          ? "← Select professional role above first"
                          : "Select your designation"}
                      </option>
                      {availableDesignations.map((des) => (
                        <option key={des} value={des}>
                          {des}
                        </option>
                      ))}
                      {selectedRoleCode && (
                        <option value="__custom__">+ Other (Specify Custom Designation)</option>
                      )}
                    </select>

                    {isCustomDesignation && (
                      <input
                        className="form-input !mt-1.5 border-teal-300 focus:border-teal-500 animate-fadeIn"
                        placeholder="Type your official designation"
                        value={customDesignation}
                        onChange={(e) => setCustomDesignation(e.target.value)}
                        required
                        autoFocus
                      />
                    )}
                  </div>
                </>
              )}

              <div>
                <label className="text-[10px] font-bold uppercase tracking-wider text-slate-500">
                  Email address *
                </label>
                <input
                  className="form-input !mt-1"
                  type="email"
                  placeholder="name@example.gov.in"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                  autoComplete="email"
                />
              </div>

              <div>
                <label className="text-[10px] font-bold uppercase tracking-wider text-slate-500">
                  Password *
                </label>
                <div className="relative !mt-1">
                  <input
                    className="form-input pr-10 !mt-0"
                    type={showPassword ? "text" : "password"}
                    placeholder="Enter secure password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    required
                    autoComplete={isRegister ? "new-password" : "current-password"}
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 focus:outline-none transition-colors p-1"
                    aria-label={showPassword ? "Hide password" : "Show password"}
                  >
                    {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
                  </button>
                </div>
              </div>

              <button
                type="submit"
                disabled={busy}
                className="w-full mt-2 rounded-xl bg-[#ef7e37] px-4 py-3 text-sm font-bold text-white hover:bg-[#d96e2a] disabled:opacity-60 transition-all shadow-md hover:shadow-lg"
              >
                {busy
                  ? "Please wait..."
                  : isRegister
                  ? "Create account"
                  : "Sign in"}
              </button>
            </form>

            {/* Toggle login / register */}
            <button
              type="button"
              className="mt-5 w-full text-xs font-bold text-[#0f9f92] hover:underline"
              onClick={() => {
                setIsRegister(!isRegister);
                setError("");
              }}
            >
              {isRegister
                ? "Already registered? Sign in"
                : "New civil services employee? Create an account"}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

