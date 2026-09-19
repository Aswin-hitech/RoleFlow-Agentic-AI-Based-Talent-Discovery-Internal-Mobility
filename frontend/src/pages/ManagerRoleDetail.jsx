import { useState } from "react";
import { useParams, Link } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import Icon, { Logo } from "../components/Icon.jsx";
import { api } from "../lib/api";
import { useAuth } from "../hooks/useAuth.jsx";
import CandidateDetailDrawer from "../components/CandidateDetailDrawer.jsx";

export default function ManagerRoleDetail() {
  const { roleId } = useParams();
  const { user, logout } = useAuth();
  const queryClient = useQueryClient();

  const [activeTab, setActiveTab] = useState("all");
  const [minFit, setMinFit] = useState(0);
  const [minReadiness, setMinReadiness] = useState(0);
  const [selectedCandidate, setSelectedCandidate] = useState(null);
  const [notice, setNotice] = useState("");

  // Role details query
  const roleQuery = useQuery({
    queryKey: ["manager-role", roleId],
    queryFn: () => api(`/manager/roles/${roleId}`),
    retry: false,
  });

  // Candidates query
  const candidatesQuery = useQuery({
    queryKey: ["manager-candidates", roleId, activeTab, minFit, minReadiness],
    queryFn: () =>
      api(`/manager/roles/${roleId}/candidates?tab=${activeTab}&min_fit=${minFit}&min_readiness=${minReadiness}`),
    retry: false,
    refetchInterval: 3000, // Poll discovery status updates
  });

  // Refresh discovery mutation (§19, §20)
  const discoveryMutation = useMutation({
    mutationFn: () => api(`/manager/roles/${roleId}/discovery`, { method: "POST" }),
    onSuccess: (data) => {
      setNotice("Role candidate discovery initiated across the 6 logical agents.");
      queryClient.invalidateQueries({ queryKey: ["manager-candidates", roleId] });
      queryClient.invalidateQueries({ queryKey: ["manager-role", roleId] });
    },
    onError: (err) => setNotice(err.message || "Failed to trigger discovery."),
  });

  const role = roleQuery.data?.role;
  const candidates = candidatesQuery.data?.candidates || [];

  return (
    <div className="min-h-screen bg-ink-950 text-slate-100">
      {/* Top Navbar */}
      <header className="sticky top-0 z-40 border-b border-white/10 bg-ink-950/85 backdrop-blur-xl">
        <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-4 sm:px-6 lg:px-8">
          <Link to="/manager" className="flex items-center gap-3">
            <Logo className="size-8" />
            <span className="font-display text-base font-bold tracking-tight text-white">
              Role<span className="text-gradient">Flow</span>
            </span>
            <span className="ml-2 rounded-full border border-white/10 bg-white/5 px-2.5 py-0.5 text-[11px] font-semibold text-brand-300">
              ROLE INTELLIGENCE
            </span>
          </Link>

          <div className="flex items-center gap-3">
            <Link
              to="/manager"
              className="rounded-lg border border-white/10 px-3.5 py-1.5 text-xs font-semibold text-slate-300 transition hover:border-white/30 hover:text-white"
            >
              ← Back to Vacant Roles
            </Link>
            <button
              onClick={logout}
              className="grid size-9 place-items-center rounded-lg border border-white/10 text-slate-400 hover:text-rose-300"
              title="Sign out"
            >
              <Icon name="logout" className="size-4" />
            </button>
          </div>
        </div>
      </header>

      {/* Main Container */}
      <main className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8 space-y-8">
        {notice && (
          <div className="flex items-center justify-between rounded-xl border border-brand-400/30 bg-brand-500/10 p-4 text-xs font-medium text-brand-200">
            <span>{notice}</span>
            <button onClick={() => setNotice("")} className="text-slate-400 hover:text-white">✕</button>
          </div>
        )}

        {/* Role Header Banner (§46) */}
        {role ? (
          <div className="relative overflow-hidden rounded-3xl border border-white/10 bg-ink-900/60 p-6 sm:p-8">
            <div className="flex flex-wrap items-start justify-between gap-4">
              <div>
                <div className="flex items-center gap-3">
                  <h1 className="font-display text-3xl font-bold tracking-tight text-white">{role.title}</h1>
                  <span className="rounded-full border border-emerald-400/30 bg-emerald-500/10 px-2.5 py-0.5 text-[11px] font-semibold text-emerald-300 capitalize">
                    {role.status}
                  </span>
                  <span
                    className={`inline-flex items-center gap-1 rounded-full border px-2.5 py-0.5 text-[11px] font-semibold ${
                      role.visibility === "visible"
                        ? "border-brand-400/30 bg-brand-500/10 text-brand-300"
                        : "border-amber-400/30 bg-amber-500/10 text-amber-300"
                    }`}
                  >
                    <Icon name={role.visibility === "visible" ? "eye" : "lock"} className="size-3" />
                    {role.visibility}
                  </span>
                </div>
                <p className="mt-1 text-sm text-slate-400">
                  {role.department} · {role.domain} · {role.headcount} Vacancies · Min {role.minimum_experience} yrs exp
                </p>
              </div>

              <div className="flex gap-2">
                <button
                  onClick={() => discoveryMutation.mutate()}
                  disabled={discoveryMutation.isPending}
                  className="inline-flex items-center gap-1.5 rounded-xl border border-white/10 bg-white/5 px-4 py-2.5 text-xs font-semibold text-slate-200 hover:border-brand-400/40 hover:text-white disabled:opacity-50"
                >
                  <Icon name="refresh" className={`size-3.5 ${discoveryMutation.isPending ? "animate-spin" : ""}`} />
                  {discoveryMutation.isPending ? "Discovering…" : "Refresh Discovery"}
                </button>
              </div>
            </div>

            {/* Requirements Chips */}
            <div className="mt-6 flex flex-wrap items-center gap-2 border-t border-white/5 pt-6">
              <span className="text-xs font-semibold text-slate-400">Mandatory Requirements:</span>
              {(role.mandatory_skills || []).map((s) => (
                <span
                  key={s}
                  className="rounded-lg border border-brand-400/25 bg-brand-500/10 px-2.5 py-1 text-xs font-semibold text-brand-200"
                >
                  {s}
                </span>
              ))}
              {(role.preferred_skills || []).map((s) => (
                <span
                  key={s}
                  className="rounded-lg border border-white/10 bg-ink-800 px-2.5 py-1 text-xs text-slate-400"
                >
                  {s}
                </span>
              ))}
            </div>
          </div>
        ) : (
          <div className="h-44 animate-pulse rounded-3xl border border-white/10 bg-ink-900/40" />
        )}

        {/* Discovery Status Banner (§20) */}
        <div className="flex items-center justify-between rounded-2xl border border-white/10 bg-ink-900/40 p-4">
          <div className="flex items-center gap-3">
            <span className="relative flex size-3">
              <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-brand-400 opacity-75" />
              <span className="relative inline-flex size-3 rounded-full bg-brand-500" />
            </span>
            <div>
              <p className="text-xs font-bold text-white">Agentic Discovery Status</p>
              <p className="text-[11px] text-slate-400">
                Found {candidates.length} matching candidate profiles from database.
              </p>
            </div>
          </div>

          <div className="flex gap-4 text-xs font-medium text-slate-400">
            <span>High Fit (≥80%): <strong className="text-white">{candidates.filter((c) => c.fit_score >= 80).length}</strong></span>
            <span>Ready Now (≥70%): <strong className="text-emerald-300">{candidates.filter((c) => c.readiness_score >= 70).length}</strong></span>
          </div>
        </div>

        {/* Tabs and Filters (§46) */}
        <div className="flex flex-wrap items-center justify-between gap-4 border-b border-white/10 pb-4">
          <div className="flex gap-2">
            {[
              { id: "all", label: "All Candidates" },
              { id: "high_fit", label: "High Fit (≥80%)" },
              { id: "high_readiness", label: "High Readiness (≥70%)" },
              { id: "shortlisted", label: "Shortlisted" },
            ].map((t) => (
              <button
                key={t.id}
                onClick={() => setActiveTab(t.id)}
                className={`rounded-xl px-4 py-2 text-xs font-semibold transition ${
                  activeTab === t.id
                    ? "bg-brand-600 text-white shadow-lg shadow-brand-600/25"
                    : "border border-white/10 bg-ink-900/60 text-slate-400 hover:text-white"
                }`}
              >
                {t.label}
              </button>
            ))}
          </div>

          <div className="flex items-center gap-4 text-xs text-slate-400">
            <div className="flex items-center gap-2">
              <span>Min Fit:</span>
              <input
                type="range"
                min="0"
                max="90"
                step="10"
                value={minFit}
                onChange={(e) => setMinFit(Number(e.target.value))}
                className="w-20 accent-brand-500"
              />
              <span className="font-bold text-white">{minFit}%</span>
            </div>

            <div className="flex items-center gap-2">
              <span>Min Readiness:</span>
              <input
                type="range"
                min="0"
                max="90"
                step="10"
                value={minReadiness}
                onChange={(e) => setMinReadiness(Number(e.target.value))}
                className="w-20 accent-emerald-500"
              />
              <span className="font-bold text-white">{minReadiness}%</span>
            </div>
          </div>
        </div>

        {/* Candidate List (§22) */}
        <div className="grid gap-4">
          {candidates.map((cand) => (
            <div
              key={cand.id}
              className="group relative overflow-hidden rounded-2xl border border-white/10 bg-ink-900/50 p-6 transition hover:border-brand-400/40 hover:bg-ink-900/80"
            >
              <div className="flex flex-wrap items-start justify-between gap-4">
                <div>
                  <div className="flex items-center gap-2.5">
                    <h3 className="font-display text-lg font-bold text-white">{cand.name || cand.full_name}</h3>
                    <span className="rounded-full bg-white/5 px-2 py-0.5 text-[10px] font-semibold text-slate-400">
                      {cand.employee_id}
                    </span>
                    {cand.status === "shortlisted" && (
                      <span className="rounded-full border border-accent-400/40 bg-accent-500/10 px-2.5 py-0.5 text-[11px] font-semibold text-accent-300">
                        Shortlisted ✓
                      </span>
                    )}
                  </div>
                  <p className="mt-0.5 text-xs text-slate-400">
                    Current: <strong className="text-slate-200">{cand.current_role}</strong> · {cand.department}
                  </p>
                </div>

                {/* Score Badges */}
                <div className="flex items-center gap-3">
                  <div className="rounded-xl border border-brand-400/30 bg-brand-500/10 px-3.5 py-1.5 text-center">
                    <p className="font-display text-lg font-bold text-brand-300">{cand.fit_score}%</p>
                    <p className="text-[10px] font-semibold uppercase tracking-wider text-slate-400">Fit</p>
                  </div>

                  <div className="rounded-xl border border-emerald-400/30 bg-emerald-500/10 px-3.5 py-1.5 text-center">
                    <p className="font-display text-lg font-bold text-emerald-300">{cand.readiness_score}%</p>
                    <p className="text-[10px] font-semibold uppercase tracking-wider text-slate-400">Readiness</p>
                  </div>
                </div>
              </div>

              {/* Skills & Transferable capability row */}
              <div className="mt-4 grid gap-3 sm:grid-cols-2">
                <div>
                  <p className="text-[11px] font-semibold uppercase tracking-wider text-slate-500">Verified Skills</p>
                  <div className="mt-1.5 flex flex-wrap gap-1.5">
                    {(cand.top_skills || []).map((s) => (
                      <span key={s} className="rounded-md border border-white/5 bg-ink-950 px-2 py-0.5 text-xs text-slate-300">
                        {s}
                      </span>
                    ))}
                  </div>
                </div>

                <div>
                  <p className="text-[11px] font-semibold uppercase tracking-wider text-slate-500">Transferable Bridges</p>
                  <div className="mt-1.5 flex flex-wrap gap-1.5">
                    {(cand.transferable_skills || []).map((t, idx) => (
                      <span key={idx} className="rounded-md border border-accent-400/20 bg-accent-500/5 px-2 py-0.5 text-xs text-accent-300">
                        {t}
                      </span>
                    ))}
                  </div>
                </div>
              </div>

              {/* Current Project & Availability (§14, §22) */}
              <div className="mt-4 flex flex-wrap items-center justify-between border-t border-white/5 pt-4 text-xs">
                <div className="text-slate-400">
                  {cand.current_project ? (
                    <span>
                      Active: <strong className="text-white">{cand.current_project.name}</strong> ({cand.current_project.completion_percentage}% done · {cand.current_project.remaining_weeks}w left)
                    </span>
                  ) : (
                    <span>Available immediately</span>
                  )}
                </div>

                <div className="flex gap-2">
                  <button
                    onClick={() => setSelectedCandidate(cand)}
                    className="rounded-lg border border-white/10 bg-white/5 px-3.5 py-1.5 text-xs font-semibold text-slate-200 hover:border-brand-400/40 hover:text-white"
                  >
                    View Match Explanation →
                  </button>
                  <button
                    onClick={() => {
                      setSelectedCandidate(cand);
                    }}
                    className="rounded-lg bg-brand-600 px-3.5 py-1.5 text-xs font-semibold text-white hover:bg-brand-500"
                  >
                    {cand.status === "shortlisted" ? "Shortlisted" : "Shortlist"}
                  </button>
                </div>
              </div>
            </div>
          ))}

          {candidates.length === 0 && (
            <div className="rounded-3xl border border-white/10 bg-ink-900/30 p-12 text-center text-slate-400">
              <Icon name="users" className="mx-auto size-8 text-slate-500" />
              <p className="mt-3 text-sm font-semibold text-white">No candidates found for selected filters</p>
              <p className="mt-1 text-xs text-slate-500">Try adjusting the Fit or Readiness sliders or running a fresh discovery.</p>
            </div>
          )}
        </div>
      </main>

      {/* Candidate Detail / Match Explanation Drawer (§47) */}
      <CandidateDetailDrawer
        candidate={selectedCandidate}
        roleId={roleId}
        roleTitle={role?.title || "Role"}
        isOpen={Boolean(selectedCandidate)}
        onClose={() => setSelectedCandidate(null)}
        onShortlisted={(empId) => {
          queryClient.invalidateQueries({ queryKey: ["manager-candidates", roleId] });
        }}
      />
    </div>
  );
}
