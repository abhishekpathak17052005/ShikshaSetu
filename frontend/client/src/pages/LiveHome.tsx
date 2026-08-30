import { useEffect, useState } from "react";
import {
  ArrowRight,
  BookOpen,
  Check,
  ClipboardCheck,
  Gauge,
  LayoutDashboard,
  LogOut,
  Menu,
  Target,
  UserRound,
  X,
} from "lucide-react";
import { toast } from "sonner";
import {
  api,
  ApiError,
  type AssessmentAttempt,
  type Competency,
  type User,
} from "@/lib/api";

const nav = [
  ["Dashboard", LayoutDashboard],
  ["My Competencies", Gauge],
  ["Skill Gaps", Target],
  ["Recommendations", BookOpen],
  ["Learning", BookOpen],
  ["Assessments", ClipboardCheck],
  ["Profile", UserRound],
] as const;
const title = (page: string) =>
  page === "Dashboard" ? "Capability overview" : page;

function Shell({ user, page, setPage, children, logout }: any) {
  const [open, setOpen] = useState(false);
  return (
    <div className="min-h-screen bg-[#f4f7fb] text-ink">
      <aside
        className={`fixed inset-y-0 left-0 z-40 w-[264px] border-r border-[#dfe7f0] bg-white px-5 py-6 transition-transform lg:translate-x-0 ${open ? "translate-x-0" : "-translate-x-full"}`}
      >
        <div className="mb-10 flex items-center gap-3 px-2">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-navy text-white font-bold">
            S
          </div>
          <div>
            <div className="text-[17px] font-extrabold text-navy">
              ShikshaSetu
            </div>
            <div className="text-[9px] font-bold uppercase tracking-[.18em] text-slate-400">
              Capability Intelligence
            </div>
          </div>
        </div>
        <div className="mb-3 px-2 text-[10px] font-bold uppercase tracking-[.14em] text-slate-400">
          Learner workspace
        </div>
        {nav.map(([label, Icon]) => (
          <button
            key={label}
            onClick={() => {
              setPage(label);
              setOpen(false);
            }}
            className={`mb-1 flex w-full items-center gap-3 rounded-xl px-3 py-3 text-left text-sm font-bold ${page === label ? "bg-[#e8f6f3] text-teal" : "text-slate-500 hover:bg-slate-50"}`}
          >
            <Icon size={18} />
            {label}
          </button>
        ))}
        <button
          onClick={logout}
          className="mt-8 flex w-full items-center gap-3 px-3 py-3 text-sm font-bold text-slate-500"
        >
          <LogOut size={18} />
          Log out
        </button>
      </aside>
      <button
        className="fixed left-4 top-4 z-30 rounded-lg bg-white p-2 shadow lg:hidden"
        onClick={() => setOpen(!open)}
      >
        {open ? <X size={20} /> : <Menu size={20} />}
      </button>
      <main className="lg:ml-[264px]">
        <header className="flex h-[76px] items-center justify-between border-b border-[#dfe7f0] bg-white px-6 lg:px-9">
          <div>
            <div className="text-[10px] font-bold uppercase tracking-[.14em] text-slate-400">
              ShikshaSetu workspace
            </div>
            <h1 className="text-xl font-bold text-navy">{title(page)}</h1>
          </div>
          <div className="flex items-center gap-3">
            <span className="hidden text-xs font-bold text-slate-500 sm:block">
              {user.full_name}
            </span>
            <button
              onClick={logout}
              className="rounded-lg border border-slate-200 px-3 py-2 text-xs font-bold text-navy"
            >
              Logout
            </button>
          </div>
        </header>
        <div className="mx-auto max-w-[1240px] p-6 lg:p-9">{children}</div>
      </main>
    </div>
  );
}

function Auth({ onLogin }: { onLogin: (user: User) => void }) {
  const [register, setRegister] = useState(false);
  const [form, setForm] = useState<any>({});
  const [roles, setRoles] = useState<any[]>([]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  useEffect(() => {
    api
      .roles()
      .then(setRoles)
      .catch(() => undefined);
  }, []);
  const update = (key: string, value: string) =>
    setForm((old: any) => ({ ...old, [key]: value }));
  const submit = async () => {
    setBusy(true);
    setError("");
    try {
      if (register) {
        await api.register({ ...form, role_id: form.role_id || roles[0]?.id });
        toast("Account created. Please sign in.");
        setRegister(false);
      } else {
        const result = await api.login(form);
        localStorage.setItem("shikshasetu_token", result.access_token);
        onLogin(result.user);
      }
    } catch (e: any) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  };
  return (
    <div className="flex min-h-screen items-center justify-center bg-[#eef4f8] px-5">
      <div className="w-full max-w-[480px] rounded-3xl border border-[#dfe7f0] bg-white p-8 shadow-xl">
        <div className="mb-8">
          <div className="mb-3 inline-flex items-center gap-2 rounded-full border border-teal/20 bg-[#e8f6f3] px-3 py-1 text-[11px] font-bold text-teal">
            Smart India Hackathon · Capability Intelligence
          </div>
          <div className="text-2xl font-extrabold text-navy">ShikshaSetu</div>
          <p className="mt-2 text-sm text-slate-500">
            {register
              ? "Create your civil services employee account"
              : "Sign in to your capability workspace"}
          </p>
        </div>
        {error && (
          <div className="mb-4 rounded-lg bg-red-50 p-3 text-sm text-red-700">
            {error}
          </div>
        )}
        <div className="space-y-3">
          {register && (
            <>
              <input
                className="form-input"
                placeholder="Full name"
                onChange={e => update("full_name", e.target.value)}
              />
              <input
                className="form-input"
                placeholder="Employee ID"
                onChange={e => update("employee_id", e.target.value)}
              />
              <input
                className="form-input"
                placeholder="Designation"
                onChange={e => update("designation", e.target.value)}
              />
              <input
                className="form-input"
                placeholder="Department"
                onChange={e => update("department", e.target.value)}
              />
              <select
                className="form-input"
                onChange={e => update("role_id", e.target.value)}
              >
                <option value="">Select professional role</option>
                {roles.map(role => (
                  <option value={role.id} key={role.id}>
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
            onChange={e => update("email", e.target.value)}
          />
          <input
            className="form-input"
            type="password"
            placeholder="Password"
            onChange={e => update("password", e.target.value)}
          />
          <button
            disabled={busy}
            onClick={submit}
            className="w-full rounded-xl bg-orange px-4 py-3 text-sm font-bold text-white disabled:opacity-60"
          >
            {busy ? "Please wait..." : register ? "Create account" : "Sign in"}
          </button>
        </div>
        <button
          className="mt-5 w-full text-sm font-bold text-teal"
          onClick={() => setRegister(!register)}
        >
          {register
            ? "Already registered? Sign in"
            : "New employee? Create an account"}
        </button>
      </div>
    </div>
  );
}

function Card({ children }: any) {
  return (
    <section className="rounded-2xl border border-[#dfe7f0] bg-white p-6 shadow-sm">
      {children}
    </section>
  );
}
function Heading({ eyebrow, children }: any) {
  return (
    <div className="mb-6">
      <div className="mb-2 text-[10px] font-bold uppercase tracking-[.14em] text-slate-400">
        {eyebrow}
      </div>
      <h2 className="text-2xl font-bold text-navy">{children}</h2>
    </div>
  );
}
function Dashboard({ gaps, competencies, loading, gapError, go }: any) {
  if (loading)
    return (
      <Card>
        <div className="text-sm font-bold text-navy">Loading your capability overview...</div>
      </Card>
    );

  if (gapError?.status === 404 || !gaps?.gaps?.length)
    return (
      <>
        <Heading eyebrow="Your capability overview">Welcome back</Heading>
        <Card>
          <div className="text-lg font-bold text-navy">Your capability profile is ready to build.</div>
          <p className="mt-3 text-sm leading-6 text-slate-500">
            Complete your capability assessment to see your competency profile and skill gaps.
          </p>
          <button
            onClick={() => go("Assessments")}
            className="mt-6 inline-flex items-center gap-2 rounded-xl bg-orange px-4 py-3 text-sm font-bold text-white"
          >
            Start assessment <ArrowRight size={16} />
          </button>
        </Card>
      </>
    );

  const assessed = gaps.gaps.filter((gap: any) => gap.current_level != null);
  const priorityGaps = gaps.gaps.filter((gap: any) => gap.gap_category === "CRITICAL" || gap.gap_category === "HIGH");
  const averageLevel = assessed.length
    ? assessed.reduce((total: number, gap: any) => total + gap.current_level, 0) / assessed.length
    : null;
  const averageConfidence = assessed.length
    ? assessed.reduce((total: number, gap: any) => total + (gap.confidence || 0), 0) / assessed.length
    : null;
  const nextGap = gaps.gaps.find((gap: any) => gap.gap > 0) || gaps.gaps[0];

  return (
    <>
      <div className="mb-6 flex flex-wrap items-center justify-between gap-3 rounded-2xl border border-[#dfe7f0] bg-white p-4 shadow-sm">
        <div>
          <div className="text-[10px] font-extrabold uppercase tracking-wider text-slate-400">National Capability Lifecycle</div>
          <div className="text-xs font-bold text-navy">Closed-Loop Competency Development</div>
        </div>
        <div className="flex flex-wrap items-center gap-1.5 text-[10px] font-extrabold">
          <span className="rounded-lg bg-[#e8f6f3] px-2.5 py-1 text-teal">1. Baseline Assessment</span>
          <span className="text-slate-300">→</span>
          <span className="rounded-lg bg-[#e8f6f3] px-2.5 py-1 text-teal">2. Skill Gap Engine</span>
          <span className="text-slate-300">→</span>
          <span className="rounded-lg bg-[#e8f6f3] px-2.5 py-1 text-teal">3. 5-Factor Recommendations</span>
          <span className="text-slate-300">→</span>
          <span className="rounded-lg bg-[#fff0e6] px-2.5 py-1 text-orange">4. AI Learning & Quiz</span>
          <span className="text-slate-300">→</span>
          <span className="rounded-lg bg-[#f0ecfc] px-2.5 py-1 text-violet">5. Measured Growth</span>
        </div>
      </div>
      <Heading eyebrow="Your capability overview">Welcome back</Heading>
      <div className="mb-6 grid gap-4 sm:grid-cols-3">
        <Card>
          <div className="text-xs font-bold text-slate-400">
            Competencies mapped
          </div>
          <div className="mt-4 text-4xl font-extrabold text-navy">
            {gaps.summary.required_competencies}
          </div>
        </Card>
        <Card>
          <div className="text-xs font-bold text-slate-400">
            Priority skill gaps
          </div>
          <div className="mt-4 text-4xl font-extrabold text-orange">
            {priorityGaps.length}
          </div>
        </Card>
        <Card>
          <div className="text-xs font-bold text-slate-400">Not assessed</div>
          <div className="mt-4 text-4xl font-extrabold text-teal">
            {gaps.summary.not_assessed_count}
          </div>
        </Card>
      </div>
      <Card>
        <Heading eyebrow="Your capability summary">
          {gaps.role?.name || gaps.summary.role_name}
        </Heading>
        <p className="text-sm leading-6 text-slate-500">
          {averageLevel == null
            ? "Complete your capability assessment to establish your current level."
            : `Average capability is ${averageLevel.toFixed(1)} / 5 with ${((averageConfidence ?? 0) * 100).toFixed(0)}% evidence confidence across assessed competencies.`}
        </p>
        <button
          onClick={() => go(nextGap ? "Skill Gaps" : "Assessments")}
          className="mt-6 inline-flex items-center gap-2 rounded-xl bg-orange px-4 py-3 text-sm font-bold text-white"
        >
          {nextGap ? `Next: improve ${nextGap.competency_name}` : "Start assessment"} <ArrowRight size={16} />
        </button>
        <button
          onClick={() => go("Recommendations")}
          className="ml-3 mt-6 inline-flex items-center gap-2 rounded-xl border border-slate-200 px-4 py-3 text-sm font-bold text-navy"
        >
          View recommendations <ArrowRight size={16} />
        </button>
      </Card>
    </>
  );
}
function CompetenciesPage({ competencies, gaps, loading, error }: any) {
  const [search, setSearch] = useState("");
  const [domain, setDomain] = useState("All domains");
  const [status, setStatus] = useState("All statuses");
  const gapById = new Map((gaps?.gaps || []).map((item: any) => [item.competency_id, item]));
  const rows = competencies.map((item: Competency) => {
    const profile: any = gapById.get(item.id);
    const indicator = !profile || profile.assessment_status === "NOT_ASSESSED"
      ? "Not Assessed"
      : profile.gap_category === "NO_GAP"
        ? "Strong"
        : profile.gap_category === "LOW" || profile.gap_category === "MEDIUM"
          ? "Developing"
          : "Needs Attention";
    return { ...item, profile, indicator };
  });
  const filteredRows = rows.filter((item: any) =>
    `${item.name} ${item.code}`.toLowerCase().includes(search.toLowerCase()) &&
    (domain === "All domains" || item.domain === domain) &&
    (status === "All statuses" || item.indicator === status)
  );
  const domains = ["All domains"].concat(rows.map((item: any) => item.domain).filter((item: any, index: number, values: any[]) => values.indexOf(item) === index));
  if (loading)
    return <Card><div className="text-sm font-bold text-navy">Loading your competencies...</div></Card>;
  if (error)
    return <Card><div className="text-sm font-bold text-red-700">Unable to load competencies.</div><p className="mt-2 text-sm text-slate-500">{error.message}</p></Card>;
  if (!competencies.length)
    return <Card><div className="text-sm font-bold text-navy">No competency data is available.</div><p className="mt-2 text-sm text-slate-500">Complete your capability assessment to see your competency profile.</p></Card>;
  return (
    <>
      <Heading eyebrow="Capability framework">My Competencies</Heading>
      <Card>
        <div className="mb-5 grid gap-3 md:grid-cols-[1fr_auto_auto]">
          <input className="form-input" placeholder="Search competencies" value={search} onChange={e => setSearch(e.target.value)} />
          <select className="form-input" value={domain} onChange={e => setDomain(e.target.value)}>{domains.map(item => <option key={String(item)}>{item}</option>)}</select>
          <select className="form-input" value={status} onChange={e => setStatus(e.target.value)}><option>All statuses</option><option>Strong</option><option>Developing</option><option>Needs Attention</option><option>Not Assessed</option></select>
        </div>
        {!filteredRows.length ? <p className="py-8 text-center text-sm text-slate-500">No competencies match your filters.</p> : <div className="space-y-3">{filteredRows.map((item: any) => <div className="rounded-xl border border-slate-100 p-4" key={item.id}><div className="flex flex-wrap items-start justify-between gap-3"><div><div className="text-[10px] font-bold uppercase tracking-wider text-teal">{item.domain}</div><h3 className="mt-1 text-lg font-bold text-navy">{item.name}</h3><div className="mt-1 text-xs font-semibold text-slate-400">{item.code}</div></div><span className={`rounded-full px-3 py-1 text-[10px] font-bold ${item.indicator === "Strong" ? "bg-[#e8f6f3] text-teal" : item.indicator === "Needs Attention" ? "bg-[#fff0e6] text-[#d96b27]" : item.indicator === "Developing" ? "bg-[#fff8e8] text-[#a66b00]" : "bg-slate-100 text-slate-500"}`}>{item.indicator}</span></div><p className="mt-3 text-sm leading-6 text-slate-500">{item.description}</p><div className="mt-4 grid gap-3 text-xs sm:grid-cols-4"><div><div className="font-bold text-slate-400">Current level</div><div className="mt-1 font-bold text-navy">{item.profile?.current_level ?? "Not assessed"}</div></div><div><div className="font-bold text-slate-400">Required level</div><div className="mt-1 font-bold text-navy">{item.profile?.required_level ?? "Not available"}</div></div><div><div className="font-bold text-slate-400">Gap</div><div className="mt-1 font-bold text-orange">{item.profile?.gap != null ? item.profile.gap.toFixed(1) : "Not available"}</div></div><div><div className="font-bold text-slate-400">Confidence</div><div className="mt-1 font-bold text-navy">{item.profile?.confidence != null ? `${Math.round(item.profile.confidence * 100)}%` : "Not available"}</div></div></div></div>)}</div>}
      </Card>
    </>
  );
}
function GapsPage({ data, loading, error, go }: any) {
  if (loading)
    return <Card><div className="text-sm font-bold text-navy">Loading your skill gaps...</div></Card>;
  if (error?.status === 404)
    return <Card><div className="text-lg font-bold text-navy">Complete your capability assessment to identify your skill gaps.</div><button onClick={() => go("Assessments")} className="mt-5 rounded-xl bg-orange px-4 py-3 text-sm font-bold text-white">Start assessment</button></Card>;
  if (error)
    return <Card><div className="text-sm font-bold text-red-700">Unable to load skill gaps.</div><p className="mt-2 text-sm text-slate-500">{error.message}</p></Card>;
  if (!data?.gaps?.length)
    return <Card><div className="text-lg font-bold text-navy">Your current profile has no identified skill gaps.</div><p className="mt-2 text-sm text-slate-500">You are currently meeting the configured requirements for your role.</p></Card>;
  const summary = data.summary;
  const overallStatus = summary.critical_gaps ? "Needs Attention" : summary.high_gaps ? "High Priority" : summary.medium_gaps ? "Developing" : "On Track";
  return (
    <>
      <Heading eyebrow="Role comparison">Skill Gaps</Heading>
      <Card>
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div><div className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Role requirements</div><h2 className="mt-1 text-xl font-bold text-navy">{data.role?.name || summary.role_name}</h2></div>
          <div className="rounded-full bg-[#fff0e6] px-3 py-2 text-xs font-bold text-[#d96b27]">{overallStatus}</div>
        </div>
        <div className="mt-6 grid gap-3 sm:grid-cols-4">
          {[['Total skill gaps', summary.total_gaps, 'text-orange'], ['High priority gaps', summary.high_gaps + summary.critical_gaps, 'text-red-600'], ['Moderate gaps', summary.medium_gaps, 'text-[#a66b00]'], ['Low gaps', summary.low_gaps, 'text-teal']].map(([label, value, color]) => <div className="rounded-xl bg-[#f7fafc] p-4" key={String(label)}><div className="text-[10px] font-bold uppercase tracking-wider text-slate-400">{label}</div><div className={`mt-2 text-2xl font-extrabold ${color}`}>{value}</div></div>)}
        </div>
      </Card>
      <Card>
        <div className="mb-5 flex items-center justify-between"><div className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Skill gap engine</div><div className="text-xs text-slate-400">Sorted by backend priority</div></div>
        {(data.gaps || []).map((gap: any) => (
          <div
            className="mb-4 rounded-xl border border-slate-100 p-5 last:mb-0"
            key={gap.competency_id}
          >
            <div className="flex flex-wrap items-start justify-between gap-3">
              <div><div className="text-[10px] font-bold uppercase tracking-wider text-teal">{gap.competency_code} · {gap.domain}</div><span className="mt-1 block text-lg font-bold text-navy">{gap.competency_name}</span></div>
              <span className="rounded-full bg-[#fff0e6] px-3 py-1 text-[10px] font-bold text-[#d96b27]">{gap.gap_category}</span>
            </div>
            <div className="mt-5 grid gap-4 sm:grid-cols-3">
              <div><div className="text-xs font-bold text-slate-400">Required level</div><div className="mt-1 text-lg font-extrabold text-navy">{gap.required_level.toFixed(1)}</div></div>
              <div><div className="text-xs font-bold text-slate-400">Current level</div><div className="mt-1 text-lg font-extrabold text-navy">{gap.current_level == null ? "Not assessed" : gap.current_level.toFixed(1)}</div></div>
              <div><div className="text-xs font-bold text-slate-400">Gap</div><div className="mt-1 text-lg font-extrabold text-orange">{gap.gap.toFixed(1)}</div></div>
            </div>
            <div className="mt-5 flex flex-wrap items-center justify-between gap-3 border-t border-slate-100 pt-4 text-xs"><span className="font-semibold text-slate-500">Priority {gap.priority} · Confidence {Math.round(gap.confidence * 100)}% · {gap.assessment_status.replace("_", " ")}</span><button onClick={() => go("Recommendations", gap.competency_code)} className="inline-flex items-center gap-2 rounded-xl bg-orange px-4 py-2.5 font-bold text-white">View Recommendations <ArrowRight size={14} /></button></div>
            <div className="mt-3 h-2 rounded bg-slate-100"><div className="h-2 rounded bg-teal" style={{ width: `${(gap.current_level || 0) * 20}%` }} />
            </div>
          </div>
        ))}
      </Card>
    </>
  );
}
function RecommendationsPage({ data, loading, error, competencyCode }: any) {
  const [provider, setProvider] = useState("All");
  const [priority, setPriority] = useState("All");
  const [expanded, setExpanded] = useState<string | null>(null);
  if (loading)
    return <Card><div className="text-sm font-bold text-navy">Loading personalized recommendations...</div></Card>;
  if (error)
    return <Card><div className="text-sm font-bold text-red-700">Unable to load recommendations.</div><p className="mt-2 text-sm text-slate-500">{error.message}</p></Card>;
  const recommendations = data?.recommendations || data?.resources || [];
  const filtered = recommendations.filter((item: any) => {
    const itemProvider = item.provider || item.resource?.provider;
    const itemPriority = item.explanation?.gap_size ?? item.gap ?? 0;
    return (!competencyCode || item.competency_code === competencyCode) && (provider === "All" || itemProvider === provider) && (priority === "All" || (priority === "Highest Priority" && itemPriority > 1));
  });
  const openResource = (item: any) => {
    const url = item.resource?.provider_specific?.course_url || item.resource?.provider_specific?.programme_url || item.resource?.source?.source_url;
    if (url) window.open(url, "_blank", "noopener,noreferrer");
    else toast("No resource URL is available. Review the resource metadata instead.");
  };
  return (
    <>
      <Heading eyebrow="Ranked for your gaps">Recommendations</Heading>
      <Card>
        <div className="flex flex-wrap gap-2"><span className="self-center text-xs font-bold text-slate-400">Provider</span>{["All", "iGOT", "NSSTA"].map(item => <button key={item} onClick={() => setProvider(item)} className={`rounded-lg px-3 py-2 text-xs font-bold ${provider === item ? "bg-[#e8f6f3] text-teal" : "text-slate-500 hover:bg-slate-50"}`}>{item}</button>)}<button onClick={() => setPriority(priority === "All" ? "Highest Priority" : "All")} className={`rounded-lg px-3 py-2 text-xs font-bold ${priority === "Highest Priority" ? "bg-[#fff0e6] text-[#d96b27]" : "text-slate-500 hover:bg-slate-50"}`}>Highest Priority</button></div>
      </Card>
      {!recommendations.length ? <Card><div className="text-lg font-bold text-navy">No recommendations yet.</div><p className="mt-3 text-sm leading-6 text-slate-500">Complete your capability assessment to identify skill gaps and receive personalized learning recommendations.</p></Card> : !filtered.length ? <Card><p className="text-sm text-slate-500">No recommendations match these filters.</p></Card> : <div className="grid gap-4 md:grid-cols-2">{filtered.map((item: any, index: number) => { const resource = item.resource || item; const id = resource.resource_id || `${item.competency_code}-${index}`; const factors = item.explanation?.score_breakdown || []; return <Card key={id}><div className="flex items-start justify-between gap-3"><div><div className="text-xs font-bold text-teal">{item.provider || resource.provider}</div><h3 className="mt-2 text-lg font-bold text-navy">{resource.title}</h3><p className="mt-2 text-xs text-slate-500">{item.competency_name || item.competency_code || "Mapped learning resource"}</p></div><div className="rounded-xl bg-[#e8f6f3] px-3 py-2 text-center"><div className="text-lg font-extrabold text-teal">{item.score != null ? item.score.toFixed(3) : "-"}</div><div className="text-[9px] font-bold uppercase tracking-wider text-slate-400">Match score</div></div></div><div className="mt-5 border-l-2 border-orange pl-3 text-sm leading-6 text-slate-500">{item.explanation?.summary || "Matched to your role and current capability gaps."}</div><button onClick={() => setExpanded(expanded === id ? null : id)} className="mt-5 text-xs font-bold text-teal">{expanded === id ? "Hide scoring details" : "Why was this recommended?"}</button>{expanded === id && <div className="mt-4 space-y-3 rounded-xl bg-[#f7fafc] p-4"><div className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Why this resource?</div>{factors.map((factor: any) => <div className="flex items-center justify-between text-xs" key={factor.name}><span className="text-slate-500">{factor.name.replaceAll("_", " ")}</span><span className="font-bold text-navy">{(factor.score * 100).toFixed(0)}% <span className="font-normal text-slate-400">({(factor.weight * 100).toFixed(0)}% weight)</span></span></div>)}</div>}<div className="mt-5 flex flex-wrap items-center gap-3"><button onClick={() => openResource(item)} className="rounded-xl bg-orange px-4 py-2.5 text-xs font-bold text-white">View Resource <ArrowRight className="ml-1 inline" size={14} /></button>{!resource.provider_specific?.course_url && !resource.provider_specific?.programme_url && !resource.source?.source_url && <span className="text-[11px] text-slate-400">No URL; metadata available</span>}</div></Card>; })}</div>}
    </>
  );
}
function LearningFlow({ recommendations, gaps, competencies, loading, error, go }: any) {
  const [file, setFile] = useState<File | null>(null);
  const [material, setMaterial] = useState<any>(null);
  const [generated, setGenerated] = useState<any>(null);
  const [quiz, setQuiz] = useState<any>(null);
  const [quizResult, setQuizResult] = useState<any>(null);
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [busy, setBusy] = useState("");
  const [errorMessage, setErrorMessage] = useState("");
  const resources = recommendations?.recommendations || [];
  const selected = resources[0];
  const competencyCode = selected?.competency_code || gaps?.gaps?.[0]?.competency_code || competencies?.[0]?.code;
  const upload = async () => {
    if (!file) { setErrorMessage("Select a PDF, DOCX, or PPTX file first."); return; }
    setBusy("uploading"); setErrorMessage("");
    try { const uploaded = await api.uploadMaterial(file); setMaterial(await api.material(uploaded.material_id)); }
    catch (e: any) { setErrorMessage(e.message); } finally { setBusy(""); }
  };
  const generate = async () => {
    if (!material?.id || !competencyCode) { setErrorMessage("A learning material and competency are required."); return; }
    setBusy("generating"); setErrorMessage("");
    try { setGenerated(await api.generateQuestions(material.id, { competency_code: competencyCode, question_count: 5 })); }
    catch (e: any) { setErrorMessage(e.message); } finally { setBusy(""); }
  };
  const createQuiz = async () => {
    if (!generated?.questions?.length) return;
    setBusy("creating"); setErrorMessage("");
    try { setQuiz(await api.createQuiz({ material_id: material.id, competency_code: generated.competency_code, questions: generated.questions.map((question: any, index: number) => ({ ...question, question_id: `${material.id}-${index + 1}` })) })); }
    catch (e: any) { setErrorMessage(e.message); } finally { setBusy(""); }
  };
  const submitQuiz = async () => {
    if (!quiz || Object.keys(answers).length !== quiz.questions.length) { setErrorMessage("Answer every quiz question before submitting."); return; }
    setBusy("submitting"); setErrorMessage("");
    try { setQuizResult(await api.submitQuiz(quiz.quiz_id, quiz.questions.map((question: any) => ({ question_id: question.question_id, selected_answer: answers[question.question_id] })))); }
    catch (e: any) { setErrorMessage(e.message); } finally { setBusy(""); }
  };
  if (loading) return <Card><div className="text-sm font-bold text-navy">Loading learning resources...</div></Card>;
  if (error) return <Card><div className="text-sm font-bold text-red-700">Unable to load learning resources.</div><p className="mt-2 text-sm text-slate-500">{error.message}</p></Card>;
  if (quizResult)
    return (
      <>
        <Heading eyebrow="Quiz result">Learning evidence created</Heading>
        <Card>
          <div className="flex flex-wrap items-center justify-between gap-4">
            <div>
              <div className="text-[10px] font-extrabold uppercase tracking-wider text-teal">Quiz Completed & Verified</div>
              <div className="mt-2 text-4xl font-extrabold text-navy">{quizResult.percentage}%</div>
              <p className="mt-2 text-sm text-slate-500">{quizResult.correct_count} of {quizResult.total_questions} answers correct.</p>
            </div>
            <div className="rounded-2xl border border-teal/30 bg-[#f4fbf9] p-4 text-center">
              <div className="text-xs font-bold text-teal">Evidence Logged</div>
              <div className="mt-1 text-sm font-extrabold text-navy">Source: AI_QUIZ</div>
            </div>
          </div>
          <div className="mt-6 grid gap-4 rounded-xl bg-[#f7fafc] p-4 sm:grid-cols-3">
            <div>
              <div className="text-xs font-bold text-slate-400">Competency</div>
              <div className="mt-1 font-bold text-navy">{quizResult.competency?.competency_code}</div>
            </div>
            <div>
              <div className="text-xs font-bold text-slate-400">Updated Level</div>
              <div className="mt-1 font-bold text-teal">{quizResult.competency?.competency_level_after} / 5.0</div>
            </div>
            <div>
              <div className="text-xs font-bold text-slate-400">Skill Gap After</div>
              <div className="mt-1 font-bold text-orange">{quizResult.skill_gap?.gap_after}</div>
            </div>
          </div>
          <div className="mt-6 flex flex-wrap gap-3">
            <button onClick={() => go("My Competencies")} className="rounded-xl bg-orange px-4 py-3 text-sm font-bold text-white shadow-sm">
              View My Competencies
            </button>
            <button onClick={() => go("Skill Gaps")} className="rounded-xl border border-slate-200 px-4 py-3 text-sm font-bold text-navy">
              View Skill Gaps
            </button>
          </div>
        </Card>
      </>
    );

  return (
    <>
      <Heading eyebrow="Learning workspace">Learn from your material</Heading>
      {errorMessage && <div role="alert" className="mb-5 rounded-lg bg-red-50 p-3 text-sm text-red-700">{errorMessage}</div>}
      <Card>
        <div className="flex flex-wrap items-center justify-between gap-2">
          <div className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Selected learning resource</div>
          <span className="rounded-full bg-slate-100 px-2.5 py-0.5 text-[10px] font-bold text-slate-600">PDF · DOCX · PPTX</span>
        </div>
        <h2 className="mt-2 text-xl font-bold text-navy">{selected?.resource?.title || "Upload learning material"}</h2>
        <p className="mt-2 text-sm text-slate-500">
          {selected
            ? `${selected.provider} · ${selected.competency_name} · Match Score: ${selected.score}`
            : "Select or upload learning materials to generate source-grounded practice questions for your targeted competencies."}
        </p>
        <div className="mt-5 rounded-xl border border-dashed border-[#dfe7f0] bg-[#fafcfe] p-5 text-center">
          <input className="block w-full text-sm text-slate-500 file:mr-4 file:rounded-lg file:border-0 file:bg-teal/10 file:px-4 file:py-2 file:text-xs file:font-bold file:text-teal hover:file:bg-teal/20" type="file" accept=".pdf,.docx,.pptx" onChange={event => setFile(event.target.files?.[0] || null)} />
        </div>
        <button disabled={busy === "uploading"} onClick={upload} className="mt-5 rounded-xl bg-orange px-5 py-3 text-sm font-bold text-white shadow-sm disabled:opacity-60">
          {busy === "uploading" ? "Ingesting & Chunking..." : "Upload & Ingest Material"}
        </button>
        {material && (
          <div className="mt-5 rounded-xl border border-teal/20 bg-[#f4fbf9] p-4 text-sm font-bold text-teal">
            ✓ {material.original_filename} · Status: {material.status} · {material.chunk_count || 0} text chunks indexed
          </div>
        )}
      </Card>
      {material && !generated && (
        <Card>
          <Heading eyebrow="AI question generation">Generate practice questions</Heading>
          <p className="text-sm text-slate-500">
            Source-grounded multiple choice questions will be synthesized from the indexed material chunks for <b>{competencyCode}</b>.
          </p>
          <button disabled={busy === "generating"} onClick={generate} className="mt-5 rounded-xl bg-orange px-5 py-3 text-sm font-bold text-white shadow-sm disabled:opacity-60">
            {busy === "generating" ? "Generating Questions with AI..." : "Generate Practice Questions"}
          </button>
        </Card>
      )}
      {generated && !quiz && (
        <Card>
          <Heading eyebrow="Generated questions">Review before quiz</Heading>
          <div className="space-y-4">
            {generated.questions.map((question: any, index: number) => (
              <div className="rounded-xl border border-slate-100 bg-[#f8fafc] p-4" key={index}>
                <div className="text-xs font-bold text-teal">Question {index + 1} · {question.difficulty}</div>
                <div className="mt-2 text-sm font-bold text-navy">{question.question}</div>
                <div className="mt-2 text-xs text-slate-500">{question.options.join(" · ")}</div>
              </div>
            ))}
          </div>
          <button disabled={busy === "creating"} onClick={createQuiz} className="mt-5 rounded-xl bg-orange px-5 py-3 text-sm font-bold text-white shadow-sm disabled:opacity-60">
            {busy === "creating" ? "Preparing Quiz Session..." : "Start Practice Quiz"}
          </button>
        </Card>
      )}
      {quiz && (
        <Card>
          <Heading eyebrow="Interactive Quiz">{quiz.title || "Competency Assessment Quiz"}</Heading>
          <div className="mb-5 text-sm text-slate-500">
            {Object.keys(answers).length} answered · {quiz.questions.length - Object.keys(answers).length} remaining
          </div>
          <div className="space-y-5">
            {quiz.questions.map((question: any, index: number) => (
              <div key={question.question_id} className="rounded-xl border border-slate-100 p-4">
                <div className="text-xs font-bold text-teal">Question {index + 1} of {quiz.questions.length}</div>
                <div className="mt-2 text-sm font-bold text-navy">{question.question}</div>
                <div className="mt-3 space-y-2">
                  {question.options.map((option: string, optionIndex: number) => {
                    const letter = String.fromCharCode(65 + optionIndex);
                    return (
                      <label className="flex cursor-pointer items-start gap-2.5 text-sm text-slate-700 hover:bg-slate-50 p-1.5 rounded" key={option}>
                        <input type="radio" className="mt-0.5" name={question.question_id} checked={answers[question.question_id] === letter} onChange={() => setAnswers(old => ({ ...old, [question.question_id]: letter }))} />
                        <span>{option}</span>
                      </label>
                    );
                  })}
                </div>
              </div>
            ))}
          </div>
          <button disabled={busy === "submitting"} onClick={submitQuiz} className="mt-6 rounded-xl bg-orange px-6 py-3.5 text-sm font-bold text-white shadow-md disabled:opacity-60">
            {busy === "submitting" ? "Evaluating Answers & Updating Competency..." : "Submit Quiz & Log Evidence"}
          </button>
        </Card>
      )}
    </>
  );
}
function AssessmentPage({ attempt, setAttempt, onResult }: any) {
  const [answers, setAnswers] = useState<any[]>([]);
  const [ratings, setRatings] = useState<any>({});
  const [busy, setBusy] = useState(false);
  const start = async () => {
    try {
      const started = await api.startAssessment();
      setAttempt(started);
      localStorage.setItem("shikshasetu_attempt_id", started.id);
    } catch (e: any) {
      toast(e.message);
    }
  };
  const submit = async () => {
    setBusy(true);
    try {
      const result = await api.submitAssessment(attempt.id, {
        self_ratings: ratings,
        answers,
      });
      localStorage.removeItem("shikshasetu_attempt_id");
      onResult(result);
      toast("Assessment submitted");
    } catch (e: any) {
      toast(e.message);
    } finally {
      setBusy(false);
    }
  };
  if (!attempt)
    return (
      <Card>
        <Heading eyebrow="Assessment">Ready to measure capability?</Heading>
        <p className="text-sm text-slate-500">
          Questions and scoring come directly from the backend.
        </p>
        <button
          onClick={start}
          className="mt-5 rounded-xl bg-orange px-4 py-3 text-sm font-bold text-white"
        >
          Start assessment
        </button>
      </Card>
    );
  return (
    <>
      <Heading eyebrow="Live assessment">Answer every question</Heading>
      <div className="space-y-4">
        {attempt.questions.map((q: any) => (
          <Card key={q.question_id}>
            <div className="text-xs font-bold text-teal">{q.question_type}</div>
            <h3 className="mt-2 font-bold text-navy">{q.question_text}</h3>
            {q.question_type === "SELF_RATING" ? (
              <div className="mt-4 flex gap-2">
                {[1, 2, 3, 4, 5].map(value => (
                  <button
                    key={value}
                    onClick={() =>
                      setRatings((old: any) => ({
                        ...old,
                        [q.competency_id]: value,
                      }))
                    }
                    className={`rounded-lg border px-4 py-2 font-bold ${ratings[q.competency_id] === value ? "border-teal bg-[#e8f6f3] text-teal" : "border-slate-200"}`}
                  >
                    {value}
                  </button>
                ))}
              </div>
            ) : (
              <div className="mt-4 space-y-2">
                {q.options.map((option: string) => (
                  <label
                    className="flex gap-2 text-sm text-slate-600"
                    key={option}
                  >
                    <input
                      type="radio"
                      name={q.question_id}
                      onChange={() =>
                        setAnswers((old: any[]) => [
                          ...old.filter(a => a.question_id !== q.question_id),
                          { question_id: q.question_id, answer: option },
                        ])
                      }
                    />
                    {option}
                  </label>
                ))}
              </div>
            )}
          </Card>
        ))}
      </div>
      <button
        disabled={busy}
        onClick={submit}
        className="mt-6 rounded-xl bg-orange px-4 py-3 text-sm font-bold text-white"
      >
        {busy ? "Submitting..." : "Submit assessment"}
      </button>
    </>
  );
}
function AssessmentExperience({ attempt, setAttempt, gaps, go, onResult, onAuthExpired }: any) {
  const [answers, setAnswers] = useState<any[]>([]);
  const [ratings, setRatings] = useState<any>({});
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [submitted, setSubmitted] = useState<any>(attempt?.status === "SUBMITTED" ? attempt : null);
  const questions = attempt?.questions || [];
  const answeredCount = questions.filter((question: any) => question.question_type === "SELF_RATING" ? ratings[question.competency_id] != null : answers.some(answer => answer.question_id === question.question_id)).length;
  const start = async () => {
    setBusy(true); setError("");
    try { const started = await api.startAssessment(); setAttempt(started); localStorage.setItem("shikshasetu_attempt_id", started.id); }
    catch (e: any) { if (e.status === 401) onAuthExpired(); setError(e.message); }
    finally { setBusy(false); }
  };
  const submit = async () => {
    if (answeredCount !== questions.length) { setError(`Please answer all questions. ${questions.length - answeredCount} remaining.`); return; }
    setBusy(true); setError("");
    try {
      const result = await api.submitAssessment(attempt.id, { self_ratings: ratings, answers, training_evidence: [] });
      localStorage.removeItem("shikshasetu_attempt_id"); setSubmitted(result); onResult(result); toast("Assessment completed and competency profile updated");
    } catch (e: any) { if (e.status === 401) onAuthExpired(); setError(e.message); }
    finally { setBusy(false); }
  };
  if (!attempt)
    return <Card><Heading eyebrow="Assessment">Ready to measure your capability?</Heading><p className="text-sm text-slate-500">The backend will calculate your competency level and update your profile.</p>{error && <p className="mt-3 text-sm text-red-700">{error}</p>}<button disabled={busy} onClick={start} className="mt-5 rounded-xl bg-orange px-4 py-3 text-sm font-bold text-white disabled:opacity-60">{busy ? "Loading assessment..." : "Start assessment"}</button></Card>;
  if (submitted)
    return <><Heading eyebrow="Assessment completed">Competency updated</Heading><div className="mb-5 rounded-xl border border-[#b9e1dc] bg-[#f4fbf9] p-4 text-sm text-teal">Your answers were scored by the backend and your competency profile was updated.</div><div className="grid gap-4 md:grid-cols-2">{(submitted.competency_results || []).map((item: any) => { const previous = gaps?.gaps?.find((gap: any) => gap.competency_id === item.competency_id); const nextGap = previous ? Math.max(0, previous.required_level - item.score) : null; return <Card key={item.competency_id}><div className="text-xs font-bold text-slate-400">Competency {item.competency_id}</div><div className="mt-3 flex items-end justify-between"><div><div className="text-3xl font-extrabold text-navy">{item.score.toFixed(1)} / 5</div><div className="text-xs text-slate-500">Current level · {Math.round(item.confidence * 100)}% confidence</div></div>{nextGap != null && <div className="text-right"><div className="text-lg font-extrabold text-orange">{nextGap.toFixed(1)}</div><div className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Updated gap</div></div>}</div></Card>; })}</div><div className="mt-6 flex flex-wrap gap-3"><button onClick={() => go("Skill Gaps")} className="rounded-xl bg-orange px-4 py-3 text-sm font-bold text-white">View Skill Gaps <ArrowRight size={15} className="ml-1 inline" /></button><button onClick={() => go("Recommendations")} className="rounded-xl border border-slate-200 px-4 py-3 text-sm font-bold text-navy">View Recommendations <ArrowRight size={15} className="ml-1 inline" /></button></div></>;
  return (
    <>
      <Heading eyebrow="Live assessment">Answer every question</Heading>
      <div className="mb-5 flex flex-wrap items-center justify-between gap-3 rounded-xl bg-white p-4 text-sm shadow-sm">
        <span className="font-bold text-navy">Assessment Progress</span>
        <span className="text-slate-500">{answeredCount} answered · {questions.length - answeredCount} remaining of {questions.length}</span>
        <div className="h-2 w-full rounded bg-slate-100">
          <div className="h-2 rounded bg-teal transition-all" style={{ width: `${questions.length ? (answeredCount / questions.length) * 100 : 0}%` }} />
        </div>
      </div>
      {error && <div role="alert" className="mb-5 rounded-lg bg-red-50 p-3 text-sm text-red-700">{error}</div>}
      <div className="space-y-4">
        {questions.map((question: any, index: number) => {
          const typeLabel = question.question_type === "SELF_RATING" ? "Self-Evaluation (Level 1–5)" : question.question_type === "MCQ" ? "Domain Knowledge Check" : "Situational Judgment Scenario";
          const typeColor = question.question_type === "SELF_RATING" ? "bg-[#e8f6f3] text-teal" : question.question_type === "MCQ" ? "bg-[#fff0e6] text-[#d96b27]" : "bg-[#f0ecfc] text-[#6d5bc3]";
          return (
            <Card key={question.question_id}>
              <div className="flex flex-wrap items-center justify-between gap-2">
                <span className={`rounded-full px-3 py-1 text-[10px] font-extrabold uppercase tracking-wider ${typeColor}`}>{typeLabel}</span>
                <span className="text-xs font-bold text-slate-400">Question {index + 1} of {questions.length}</span>
              </div>
              <h3 className="mt-3 text-base font-bold text-navy">{question.scenario_context || question.question_text}</h3>
              {question.question_type === "SELF_RATING" ? (
                <div className="mt-4 flex flex-wrap gap-2">
                  {[1, 2, 3, 4, 5].map(value => (
                    <button
                      key={value}
                      onClick={() => setRatings((old: any) => ({ ...old, [question.competency_id]: value }))}
                      className={`rounded-lg border px-4 py-2 font-bold transition-colors ${ratings[question.competency_id] === value ? "border-teal bg-[#e8f6f3] text-teal" : "border-slate-200 text-slate-600 hover:bg-slate-50"}`}
                    >
                      {value}
                    </button>
                  ))}
                </div>
              ) : (
                <div className="mt-4 space-y-2">
                  {question.options.map((option: string) => (
                    <label className="flex cursor-pointer items-start gap-3 rounded-lg border border-transparent p-2 text-sm text-slate-700 hover:bg-slate-50" key={option}>
                      <input
                        type="radio"
                        className="mt-0.5"
                        name={question.question_id}
                        checked={answers.find(answer => answer.question_id === question.question_id)?.answer === option}
                        onChange={() => setAnswers(old => [...old.filter(answer => answer.question_id !== question.question_id), { question_id: question.question_id, answer: option }])}
                      />
                      <span>{option}</span>
                    </label>
                  ))}
                </div>
              )}
            </Card>
          );
        })}
      </div>
      <button
        disabled={busy || answeredCount !== questions.length}
        onClick={submit}
        className="mt-6 rounded-xl bg-orange px-6 py-3.5 text-sm font-bold text-white shadow-md disabled:cursor-not-allowed disabled:opacity-50"
      >
        {busy ? "Submitting & Scoring..." : "Submit Assessment & Update Profile"}
      </button>
    </>
  );
}
function ProfilePage({ user, setUser }: any) {
  const [form, setForm] = useState(user);
  const save = async () => {
    try {
      setUser(
        await api.updateProfile({
          full_name: form.full_name,
          designation: form.designation,
          department: form.department,
          employee_id: form.employee_id,
        })
      );
      toast("Profile updated");
    } catch (e: any) {
      toast(e.message);
    }
  };
  return (
    <Card>
      <Heading eyebrow="Employee profile">Your details</Heading>
      <div className="grid gap-4 sm:grid-cols-2">
        {["email", "full_name", "employee_id", "designation", "department"].map(
          key => (
            <label className="text-xs font-bold text-slate-500" key={key}>
              {key.replace("_", " ")}
              <input
                className="form-input mt-2"
                disabled={key === "email"}
                value={form[key] || ""}
                onChange={e => setForm({ ...form, [key]: e.target.value })}
              />
            </label>
          )
        )}
      </div>
      <button
        onClick={save}
        className="mt-6 rounded-xl bg-orange px-4 py-3 text-sm font-bold text-white"
      >
        Save profile
      </button>
    </Card>
  );
}

export default function LiveHome() {
  const [user, setUser] = useState<User | null>(null);
  const [page, setPage] = useState("Dashboard");
  const [competencies, setCompetencies] = useState<Competency[]>([]);
  const [gaps, setGaps] = useState<any>(null);
  const [recommendations, setRecommendations] = useState<any>(null);
  const [attempt, setAttempt] = useState<AssessmentAttempt | null>(null);
  const [result, setResult] = useState<any>(null);
  const [recommendationCompetency, setRecommendationCompetency] = useState("");
  const [loading, setLoading] = useState(true);
  const [dataLoading, setDataLoading] = useState(false);
  const [loadError, setLoadError] = useState("");
  const [gapError, setGapError] = useState<ApiError | null>(null);
  const [competencyError, setCompetencyError] = useState<ApiError | null>(null);
  const [recommendationError, setRecommendationError] = useState<ApiError | null>(null);
  useEffect(() => {
    if (localStorage.getItem("shikshasetu_token"))
      api
        .me()
        .then(setUser)
        .catch(() => localStorage.removeItem("shikshasetu_token"))
        .finally(() => setLoading(false));
    else setLoading(false);
  }, []);
  useEffect(() => {
    if (user) {
      setDataLoading(true);
      setLoadError("");
      setGapError(null);
      setCompetencyError(null);
      setRecommendationError(null);
      Promise.allSettled([api.competencies(), api.skillGaps(), api.recommendations()])
        .then(([competencyResult, gapResult, recommendationResult]) => {
          if (competencyResult.status === "fulfilled") setCompetencies(competencyResult.value);
          else {
            setCompetencyError(competencyResult.reason);
            if (competencyResult.reason.status === 401) setUser(null);
            setLoadError(competencyResult.reason.message);
          }
          if (gapResult.status === "fulfilled") setGaps(gapResult.value);
          else {
            setGapError(gapResult.reason);
            if (gapResult.reason.status === 401) setUser(null);
            if (gapResult.reason.status !== 404) setLoadError(gapResult.reason.message);
          }
          if (recommendationResult.status === "fulfilled") setRecommendations(recommendationResult.value);
          else {
            setRecommendationError(recommendationResult.reason);
            if (recommendationResult.reason.status === 401) setUser(null);
            if (recommendationResult.reason.status !== 404) setLoadError(recommendationResult.reason.message);
          }
        })
        .finally(() => setDataLoading(false));
      const attemptId = localStorage.getItem("shikshasetu_attempt_id");
      if (attemptId) api.getAttempt(attemptId).then(setAttempt).catch(() => localStorage.removeItem("shikshasetu_attempt_id"));
    }
  }, [user]);
  if (loading) return <div className="flex min-h-screen items-center justify-center bg-[#eef4f8] text-sm font-bold text-navy">Loading workspace...</div>;
  if (!user) return <Auth onLogin={setUser} />;
  const logout = () => {
    localStorage.removeItem("shikshasetu_token");
    setUser(null);
  };
  const navigate = (nextPage: string, competencyCode?: string) => {
    setPage(nextPage);
    setRecommendationCompetency(competencyCode || "");
  };
  const assessmentComplete = async (assessmentResult: any) => {
    setResult(assessmentResult);
    try { setGaps(await api.skillGaps()); } catch (e: any) { if (e.status !== 404) setLoadError(e.message); }
  };
  const content =
    page === "Dashboard" ? (
      <Dashboard gaps={gaps} competencies={competencies} loading={dataLoading} gapError={gapError} go={navigate} />
    ) : page === "My Competencies" ? (
      <CompetenciesPage competencies={competencies} gaps={gaps} loading={dataLoading} error={competencyError} />
    ) : page === "Skill Gaps" ? (
      <GapsPage data={gaps} loading={dataLoading} error={gapError} go={navigate} />
    ) : page === "Recommendations" ? (
      <RecommendationsPage data={recommendations} loading={dataLoading} error={recommendationError} competencyCode={recommendationCompetency} />
    ) : page === "Learning" ? (
      <LearningFlow recommendations={recommendations} gaps={gaps} competencies={competencies} loading={dataLoading} error={recommendationError} go={navigate} />
    ) : page === "Assessments" ? (
      <AssessmentExperience
        attempt={attempt}
        setAttempt={setAttempt}
        gaps={gaps}
        go={navigate}
        onResult={assessmentComplete}
        onAuthExpired={logout}
      />
    ) : page === "Profile" ? (
      <ProfilePage user={user} setUser={setUser} />
    ) : (
      <Card>
        <Heading eyebrow="Results">Assessment results</Heading>
        {result ? (
          <pre className="overflow-auto text-xs">
            {JSON.stringify(result, null, 2)}
          </pre>
        ) : (
          <p className="text-sm text-slate-500">
            Complete an assessment to see live results.
          </p>
        )}
      </Card>
    );
  return (
    <Shell user={user} page={page} setPage={setPage} logout={logout}>
      {loadError && <div className="mb-5 rounded-lg bg-red-50 p-3 text-sm text-red-700">{loadError}</div>}
      {content}
    </Shell>
  );
}
