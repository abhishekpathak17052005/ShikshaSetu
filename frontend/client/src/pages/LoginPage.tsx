import { useEffect, useState, useMemo } from "react";
import { useLocation } from "wouter";
import { toast } from "sonner";
import { Eye, EyeOff, CheckCircle2 } from "lucide-react";
import { api } from "@/lib/api";
import { useAuth } from "@/contexts/AuthContext";
import type { Role } from "@/lib/api";
import { DEPARTMENT_TAXONOMY } from "@/lib/departments";
import { ShikshaSetuLogo } from "@/components/brand/ShikshaSetuLogo";
import {
  GovernmentLevel,
  GovernmentOrganization,
  CENTRAL_MINISTRIES,
} from "@/lib/governmentTaxonomy";
import { GovernmentTaxonomySelector } from "@/components/common/GovernmentTaxonomySelector";

export default function LoginPage() {
  const { login } = useAuth();
  const [location, navigate] = useLocation();
  const isRegister = location === "/register";
  const [showPassword, setShowPassword] = useState(false);
  const [roles, setRoles] = useState<Role[]>([]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  // Registration identity fields
  const [fullName, setFullName] = useState("");
  const [employeeId, setEmployeeId] = useState("");

  // Cascading Government Taxonomy fields
  const [level, setLevel] = useState<GovernmentLevel>("CENTRAL");
  const [stateCode, setStateCode] = useState("");
  const [selectedOrg, setSelectedOrg] = useState<GovernmentOrganization | null>(
    CENTRAL_MINISTRIES[0]
  );
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

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setBusy(true);
    setError("");

    try {
      if (isRegister) {
        const finalDesignation = isCustomDesignation
          ? customDesignation.trim()
          : designation.trim();

        if (!selectedOrg) {
          throw new Error("Please select your Department / Organization");
        }
        if (!finalDesignation) {
          throw new Error("Please select or enter your Official Designation");
        }

        // Determine matching backend role ID
        let resolvedRoleId = "";
        if (selectedOrg.default_role_code) {
          const matched = roles.find((r) => r.role_code === selectedOrg.default_role_code);
          if (matched) resolvedRoleId = matched.id;
        }
        if (!resolvedRoleId && roles.length > 0) {
          resolvedRoleId = roles[0].id;
        }

        await api.auth.register({
          full_name: fullName.trim(),
          employee_id: employeeId.trim(),
          designation: finalDesignation,
          department: selectedOrg.name,
          organization: selectedOrg.short_name,
          organization_id: selectedOrg.id,
          organization_type: selectedOrg.organization_type,
          government_level: level,
          state_ut: level !== "CENTRAL" ? stateCode : null,
          government_designation: finalDesignation,
          role_id: resolvedRoleId || "6a8ff00dbda6ad0866e7667c",
          email: email.trim(),
          password: password.trim(),
        });

        toast.success("Account created successfully. Please sign in.");
        navigate("/login");
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
    <div className="min-h-screen bg-[#f4f7fb] text-[#18304f] lg:h-screen lg:overflow-hidden">
      <header className="mx-auto flex max-w-[1380px] items-center justify-between px-6 py-5 lg:h-[88px] lg:px-12 lg:py-4">
        <ShikshaSetuLogo variant="full" size="md" href="/" priority />
        <div className="hidden items-center gap-7 text-xs font-bold text-slate-500 md:flex">
          <a href="#capabilities" className="transition-colors hover:text-[#0f9f92]">Capabilities</a>
          <a href="#ecosystem" className="transition-colors hover:text-[#0f9f92]">Learning ecosystem</a>
          <span className="flex items-center gap-2 text-[#123057]"><CheckCircle2 size={15} className="text-[#0f9f92]" /> Protected access</span>
        </div>
      </header>

      <main className="mx-auto grid min-h-[calc(100vh-80px)] max-w-[1380px] items-center gap-10 px-6 pb-10 pt-4 lg:h-[calc(100vh-88px)] lg:min-h-0 lg:-translate-y-6 lg:grid-cols-[1.08fr_.92fr] lg:gap-16 lg:px-12 lg:py-3">
      {/* ── Landing hero ── */}
      <div id="capabilities" className="relative overflow-hidden rounded-[2rem] bg-[#123057] p-8 text-white shadow-[0_24px_70px_rgba(18,48,87,.18)] md:p-12 lg:h-[calc(100vh-120px)] lg:min-h-0 lg:p-10">
        <div className="absolute -right-24 -top-24 h-80 w-80 rounded-full border border-white/10" />
        <div className="absolute -bottom-32 -left-20 h-72 w-72 rounded-full border border-[#38d9c0]/20" />
        <div>
          <div className="inline-flex items-center gap-2 rounded-full border border-[#38d9c0]/25 bg-white/10 px-3 py-1 text-[10px] font-bold uppercase tracking-[.12em] text-[#8ce9dc]">
            Smart India Hackathon · Public sector learning
          </div>
          <h1 className="mt-7 max-w-xl text-4xl font-extrabold leading-[0.98] tracking-[-.04em] md:text-6xl">
            Build the capability your role demands<span className="text-[#38d9c0]">.</span>
          </h1>
          <p className="mt-2 max-w-lg text-sm leading-6 text-blue-100 md:text-base">
            ShikshaSetu turns competency frameworks into a clear path from assessment to evidence-backed professional growth across India&apos;s civil services.
          </p>

          <div className="mt-4 grid max-w-lg grid-cols-3 gap-3 border-y border-white/10 py-5">
            <div><div className="text-2xl font-extrabold text-[#38d9c0]">01</div><div className="mt-1 text-[10px] font-bold uppercase tracking-wider text-blue-200">Assess</div></div>
            <div><div className="text-2xl font-extrabold text-[#38d9c0]">02</div><div className="mt-1 text-[10px] font-bold uppercase tracking-wider text-blue-200">Learn</div></div>
            <div><div className="text-2xl font-extrabold text-[#38d9c0]">03</div><div className="mt-1 text-[10px] font-bold uppercase tracking-wider text-blue-200">Evidence</div></div>
          </div>

          <div id="ecosystem" className="mt-10 grid gap-3 sm:grid-cols-2">
            {[
              "Role-aware competency frameworks",
              "Explainable AI skill-gap analysis",
              "iGOT Karmayogi & NSSTA pathways",
              "Continuous evidence and assessment",
            ].map((item) => (
              <div key={item} className="flex items-start gap-2 text-xs text-blue-100"><CheckCircle2 size={14} className="mt-0.5 shrink-0 text-[#38d9c0]" /><span>{item}</span></div>
            ))}
          </div>
        </div>
      </div>

      {/* ── Sign-in panel ── */}
      <div className="flex items-center justify-center py-4 anim-page-enter lg:py-3">
        <div className="w-full max-w-[480px]">
          {/* Mobile logo */}
          <div className="mb-6 flex items-center justify-center lg:hidden">
            <ShikshaSetuLogo variant="full" size="md" priority />
          </div>

          <div className="rounded-[2rem] border border-[#dfe7f0] bg-white p-7 shadow-[0_24px_70px_rgba(18,48,87,.12)] anim-card-enter md:p-9 lg:h-[calc(100vh-120px)] lg:overflow-hidden lg:p-6">
            {/* Header */}
            <div className="mb-6 lg:mb-4">
              <div className="mb-3 inline-flex items-center gap-2 rounded-full border border-[#0f9f92]/20 bg-[#e8f6f3] px-3 py-1 text-[11px] font-semibold text-[#0f9f92] anim-badge-pop">
                ShikshaSetu · Capability Intelligence Platform
              </div>
              <div className="text-2xl font-bold text-[#123057] tracking-tight">
                {isRegister ? "Create account" : "Welcome back"}
              </div>
              <p className="mt-1 text-xs text-slate-500 font-normal">
                {isRegister
                  ? "Select your department, role, and designation to initialize your tailored framework"
                  : "Sign in to your capability workspace"}
              </p>
            </div>

            {/* Error banner */}
            {error && (
              <div className="mb-4 rounded-xl bg-red-50 px-4 py-3 text-xs font-medium text-red-700 border border-red-100 anim-fade-up">
                {error}
              </div>
            )}

            {/* Form */}
            <form onSubmit={handleSubmit} className="space-y-3.5 lg:space-y-2.5">
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

                  {/* Cascading Government Organization & Designation Taxonomy Selector */}
                  <GovernmentTaxonomySelector
                    level={level}
                    setLevel={setLevel}
                    stateCode={stateCode}
                    setStateCode={setStateCode}
                    selectedOrg={selectedOrg}
                    setSelectedOrg={setSelectedOrg}
                    designation={designation}
                    setDesignation={setDesignation}
                    customDesignation={customDesignation}
                    setCustomDesignation={setCustomDesignation}
                    isCustomDesignation={isCustomDesignation}
                    setIsCustomDesignation={setIsCustomDesignation}
                    disabled={busy}
                    required
                  />
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
                className="w-full mt-2 rounded-xl bg-[#ef7e37] px-4 py-3 text-sm font-bold text-white hover:bg-[#d96e2a] disabled:opacity-60 transition-all shadow-md hover:shadow-lg btn-interactive lg:py-2.5"
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
              className="mt-5 w-full text-xs font-bold text-[#0f9f92] hover:underline btn-interactive lg:mt-3"
              onClick={() => {
                setError("");
                navigate(isRegister ? "/login" : "/register");
              }}
            >
              {isRegister
                ? "Already registered? Sign in"
                : "New civil services employee? Create an account"}
            </button>

            {/* Quick Demo Access Bar */}
            {!isRegister && (
              <div className="mt-6 border-t border-slate-100 pt-5 lg:mt-4 lg:pt-4">
                <div className="mb-2.5 flex items-center justify-between">
                  <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400">
                    QUICK DEMO ACCESS · SIH 2026
                  </span>
                  <span className="rounded bg-teal-50 px-1.5 py-0.5 text-[9px] font-bold text-teal-700">
                    One-Click
                  </span>
                </div>
                <div className="grid grid-cols-2 gap-2">
                  <button
                    type="button"
                    disabled={busy}
                    onClick={async () => {
                      setEmail("official@shikshasetu.gov.in");
                      setPassword("Password123!");
                      setBusy(true);
                      setError("");
                      try {
                        await login("official@shikshasetu.gov.in", "Password123!");
                      } catch (err: unknown) {
                        setError(err instanceof Error ? err.message : "Login failed");
                      } finally {
                        setBusy(false);
                      }
                    }}
                    className="flex flex-col items-start rounded-xl border border-teal-200/80 bg-teal-50/50 p-2.5 text-left transition hover:border-teal-400 hover:bg-teal-50 focus:outline-none"
                  >
                    <span className="text-[11px] font-bold text-teal-900">📊 Statistical Officer</span>
                    <span className="text-[10px] text-teal-700">MoSPI · Primary Demo</span>
                  </button>

                  <button
                    type="button"
                    disabled={busy}
                    onClick={async () => {
                      setEmail("trainer@shikshasetu.gov.in");
                      setPassword("Password123!");
                      setBusy(true);
                      setError("");
                      try {
                        await login("trainer@shikshasetu.gov.in", "Password123!");
                      } catch (err: unknown) {
                        setError(err instanceof Error ? err.message : "Login failed");
                      } finally {
                        setBusy(false);
                      }
                    }}
                    className="flex flex-col items-start rounded-xl border border-blue-200/80 bg-blue-50/50 p-2.5 text-left transition hover:border-blue-400 hover:bg-blue-50 focus:outline-none"
                  >
                    <span className="text-[11px] font-bold text-blue-900">🎓 NSSTA Trainer</span>
                    <span className="text-[10px] text-blue-700">Training · AI Question Generation</span>
                  </button>

                  <button
                    type="button"
                    disabled={busy}
                    onClick={async () => {
                      setEmail("admin@shikshasetu.gov.in");
                      setPassword("Password123!");
                      setBusy(true);
                      setError("");
                      try {
                        await login("admin@shikshasetu.gov.in", "Password123!");
                      } catch (err: unknown) {
                        setError(err instanceof Error ? err.message : "Login failed");
                      } finally {
                        setBusy(false);
                      }
                    }}
                    className="flex flex-col items-start rounded-xl border border-amber-200/80 bg-amber-50/50 p-2.5 text-left transition hover:border-amber-400 hover:bg-amber-50 focus:outline-none"
                  >
                    <span className="text-[11px] font-bold text-amber-900">🏛️ MoSPI Admin</span>
                    <span className="text-[10px] text-amber-700">Workforce · Department Overview</span>
                  </button>

                  <button
                    type="button"
                    disabled={busy}
                    onClick={async () => {
                      setEmail("edu.officer@shikshasetu.gov.in");
                      setPassword("Password123!");
                      setBusy(true);
                      setError("");
                      try {
                        await login("edu.officer@shikshasetu.gov.in", "Password123!");
                      } catch (err: unknown) {
                        setError(err instanceof Error ? err.message : "Login failed");
                      } finally {
                        setBusy(false);
                      }
                    }}
                    className="flex flex-col items-start rounded-xl border border-slate-200 bg-slate-50/50 p-2.5 text-left transition hover:border-slate-400 hover:bg-slate-100 focus:outline-none"
                  >
                    <span className="text-[11px] font-bold text-slate-800">📚 Education Officer</span>
                    <span className="text-[10px] text-slate-600">MoE · Multi-Dept Demo</span>
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
      </main>
    </div>
  );
}

