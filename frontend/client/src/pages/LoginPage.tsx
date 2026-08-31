import { useEffect, useState } from "react";
import { toast } from "sonner";
import { Eye, EyeOff } from "lucide-react";
import { api } from "@/lib/api";
import { useAuth } from "@/contexts/AuthContext";
import type { Role } from "@/lib/api";

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
  const [designation, setDesignation] = useState("");
  const [department, setDepartment] = useState("");
  const [selectedRoleId, setSelectedRoleId] = useState("");

  // Shared fields
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  useEffect(() => {
    api.roles
      .list()
      .then(setRoles)
      .catch(() => undefined);
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setBusy(true);
    setError("");

    try {
      if (isRegister) {
        await api.auth.register({
          full_name: fullName,
          employee_id: employeeId,
          designation,
          department,
          role_id: selectedRoleId || roles[0]?.id,
          email,
          password,
        });
        toast.success("Account created. Please sign in.");
        setIsRegister(false);
        setPassword("");
      } else {
        await login(email, password);
        // AuthContext sets the user; Router in App.tsx redirects automatically
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
      <div className="hidden lg:flex flex-col justify-between bg-[#123057] text-white w-[420px] flex-shrink-0 p-12">
        <div>
          <div className="flex items-center gap-3 mb-12">
            <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-white/10 text-white text-2xl font-extrabold">
              S
            </div>
            <div>
              <div className="text-xl font-extrabold">ShikshaSetu</div>
              <div className="text-[10px] font-bold uppercase tracking-[.18em] text-blue-300">
                Capability Intelligence
              </div>
            </div>
          </div>

          <div className="space-y-6">
            <div>
              <div className="text-3xl font-extrabold leading-tight mb-4">
                Empowering India's Civil Services through capability intelligence
              </div>
              <p className="text-sm text-blue-200 leading-6">
                A unified platform for skill gap analysis, AI-driven learning, and measurable
                growth — built for Smart India Hackathon.
              </p>
            </div>

            <div className="space-y-3 pt-4">
              {[
                "Role-based competency mapping",
                "AI-powered skill gap analysis",
                "Personalised learning recommendations",
                "Evidence-based progress tracking",
              ].map(item => (
                <div key={item} className="flex items-center gap-3 text-sm text-blue-100">
                  <div className="h-1.5 w-1.5 rounded-full bg-[#0f9f92] flex-shrink-0" />
                  {item}
                </div>
              ))}
            </div>
          </div>
        </div>

        <div className="text-[10px] text-blue-300 font-medium">
          Smart India Hackathon · Ministry of Personnel, Public Grievances &amp; Pensions
        </div>
      </div>

      {/* ── Right panel (form) ── */}
      <div className="flex flex-1 items-center justify-center bg-[#eef4f8] px-5 py-12">
        <div className="w-full max-w-[440px]">
          {/* Mobile logo */}
          <div className="mb-8 flex items-center gap-2 lg:hidden">
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-[#123057] text-white font-extrabold">
              S
            </div>
            <span className="text-xl font-extrabold text-[#123057]">ShikshaSetu</span>
          </div>

          <div className="rounded-3xl border border-[#dfe7f0] bg-white p-8 shadow-xl">
            {/* Header */}
            <div className="mb-8">
              <div className="mb-3 inline-flex items-center gap-2 rounded-full border border-[#0f9f92]/20 bg-[#e8f6f3] px-3 py-1 text-[11px] font-bold text-[#0f9f92]">
                Smart India Hackathon · Capability Intelligence
              </div>
              <div className="text-2xl font-extrabold text-[#123057]">
                {isRegister ? "Create account" : "Welcome back"}
              </div>
              <p className="mt-1.5 text-sm text-slate-500">
                {isRegister
                  ? "Create your civil services employee account"
                  : "Sign in to your capability workspace"}
              </p>
            </div>

            {/* Error */}
            {error && (
              <div className="mb-4 rounded-lg bg-red-50 px-4 py-3 text-sm text-red-700 border border-red-100">
                {error}
              </div>
            )}

            {/* Form */}
            <form onSubmit={handleSubmit} className="space-y-3">
              {isRegister && (
                <>
                  <input
                    className="form-input"
                    placeholder="Full name"
                    value={fullName}
                    onChange={e => setFullName(e.target.value)}
                    required
                  />
                  <input
                    className="form-input"
                    placeholder="Employee ID"
                    value={employeeId}
                    onChange={e => setEmployeeId(e.target.value)}
                    required
                  />
                  <input
                    className="form-input"
                    placeholder="Designation"
                    value={designation}
                    onChange={e => setDesignation(e.target.value)}
                  />
                  <input
                    className="form-input"
                    placeholder="Department"
                    value={department}
                    onChange={e => setDepartment(e.target.value)}
                  />
                  <select
                    className="form-input"
                    value={selectedRoleId}
                    onChange={e => setSelectedRoleId(e.target.value)}
                  >
                    <option value="">Select professional role</option>
                    {roles.map(role => (
                      <option key={role.id} value={role.id}>
                        {role.role_name}
                      </option>
                    ))}
                  </select>
                </>
              )}

              <input
                className="form-input"
                type="email"
                placeholder="Email address"
                value={email}
                onChange={e => setEmail(e.target.value)}
                required
                autoComplete="email"
              />
              <div className="relative">
                <input
                  className="form-input pr-10"
                  type={showPassword ? "text" : "password"}
                  placeholder="Password"
                  value={password}
                  onChange={e => setPassword(e.target.value)}
                  required
                  autoComplete={isRegister ? "new-password" : "current-password"}
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 focus:outline-none transition-colors p-1"
                  aria-label={showPassword ? "Hide password" : "Show password"}
                >
                  {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
                </button>
              </div>

              <button
                type="submit"
                disabled={busy}
                className="w-full rounded-xl bg-[#ef7e37] px-4 py-3 text-sm font-bold text-white hover:bg-[#d96e2a] disabled:opacity-60 transition-colors"
              >
                {busy
                  ? "Please wait..."
                  : isRegister
                  ? "Create account"
                  : "Sign in"}
              </button>
            </form>

            {/* Toggle */}
            <button
              type="button"
              className="mt-5 w-full text-sm font-bold text-[#0f9f92] hover:underline"
              onClick={() => {
                setIsRegister(!isRegister);
                setError("");
              }}
            >
              {isRegister
                ? "Already registered? Sign in"
                : "New employee? Create an account"}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
