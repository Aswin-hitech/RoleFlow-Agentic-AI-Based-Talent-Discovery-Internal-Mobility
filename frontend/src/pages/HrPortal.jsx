import { useState } from "react";
import { Link } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import Icon, { Logo } from "../components/Icon.jsx";
import { api } from "../lib/api";
import { useAuth } from "../hooks/useAuth.jsx";

export default function HrPortal() {
  const { user, logout } = useAuth();
  const queryClient = useQueryClient();
  const [notice, setNotice] = useState("");

  const transfersQuery = useQuery({
    queryKey: ["hr-transfers"],
    queryFn: () => api("/hr/transfers"),
  });

  const approveMutation = useMutation({
    mutationFn: (transferId) => api(`/hr/transfers/${transferId}/approve`, { method: "POST" }),
    onSuccess: (data) => {
      setNotice(data.message || "Transfer successfully approved!");
      queryClient.invalidateQueries({ queryKey: ["hr-transfers"] });
    },
    onError: (err) => setNotice(err.message || "Failed to approve transfer."),
  });

  const rejectMutation = useMutation({
    mutationFn: (transferId) => api(`/hr/transfers/${transferId}/reject`, { method: "POST" }),
    onSuccess: (data) => {
      setNotice(data.message || "Transfer rejected.");
      queryClient.invalidateQueries({ queryKey: ["hr-transfers"] });
    },
    onError: (err) => setNotice(err.message || "Failed to reject transfer."),
  });

  const transfers = transfersQuery.data?.transfers || [];
  const metrics = transfersQuery.data?.metrics || {
    open_roles: 0,
    total_candidates: 0,
    ready_now: 0,
    shortlisted_candidates: 0,
    pending_employee_decisions: 0,
    pending_hr_approvals: 0,
    completed_transfers: 0,
  };

  return (
    <div className="min-h-screen bg-ink-950 text-slate-100">
      {/* Navbar */}
      <header className="sticky top-0 z-40 border-b border-white/10 bg-ink-950/85 backdrop-blur-xl">
        <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-4 sm:px-6 lg:px-8">
          <Link to="/" className="flex items-center gap-3">
            <Logo className="size-8" />
            <span className="font-display text-base font-bold tracking-tight text-white">
              Role<span className="text-gradient">Flow</span>
            </span>
            <span className="ml-2 rounded-full border border-white/10 bg-white/5 px-2.5 py-0.5 text-[11px] font-semibold text-violet-300">
              HR & GOVERNANCE PORTAL
            </span>
          </Link>

          <div className="flex items-center gap-3">
            <span className="hidden text-xs text-slate-400 sm:block">{user?.name}</span>
            <Link to="/" className="rounded-lg border border-white/10 px-3.5 py-1.5 text-xs font-semibold text-slate-300 hover:text-white">
              Home
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
        <div className="flex flex-wrap items-end justify-between gap-4">
          <div>
            <h1 className="font-display text-2xl font-bold tracking-tight text-white sm:text-3xl">
              Internal Mobility Governance
            </h1>
            <p className="mt-1.5 text-sm text-slate-400">
              Review shortlisted employee career transitions, evaluate readiness, and execute final governance approvals (§29, §30).
            </p>
          </div>
        </div>

        {notice && (
          <div className="flex items-center justify-between rounded-xl border border-brand-400/30 bg-brand-500/10 p-4 text-xs font-medium text-brand-200">
            <span>{notice}</span>
            <button onClick={() => setNotice("")} className="text-slate-400 hover:text-white">✕</button>
          </div>
        )}

        {/* HR Dashboard Metrics (§49) */}
        <div className="grid grid-cols-2 gap-4 sm:grid-cols-4 lg:grid-cols-5">
          {[
            { label: "Active Roles", value: metrics.open_roles, tone: "text-white" },
            { label: "Total Candidates", value: metrics.total_candidates, tone: "text-brand-300" },
            { label: "Pending Decisions", value: metrics.pending_employee_decisions, tone: "text-amber-300" },
            { label: "Pending Approvals", value: metrics.pending_hr_approvals, tone: "text-accent-300" },
            { label: "Approved Transfers", value: metrics.completed_transfers, tone: "text-emerald-300" },
          ].map((m) => (
            <div key={m.label} className="card-glow rounded-2xl bg-ink-900/60 p-5">
              <p className="text-[10px] font-semibold uppercase tracking-wider text-slate-500">{m.label}</p>
              <p className={`font-display mt-2 text-2xl font-bold ${m.tone}`}>{m.value}</p>
            </div>
          ))}
        </div>

        {/* Transfer Governance Pipeline (§30) */}
        <div className="rounded-3xl border border-white/10 bg-ink-900/60 p-6 sm:p-8 space-y-6">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="font-display text-lg font-bold text-white">Transfer Request Approvals</h2>
              <p className="text-xs text-slate-400">
                Human-in-the-loop stage: Manager shortlists → Employee decides → HR approves.
              </p>
            </div>
            <span className="rounded-full bg-white/5 px-3 py-1 text-xs font-semibold text-slate-300">
              {transfers.length} records tracked
            </span>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="border-b border-white/10 text-slate-500 uppercase text-[10px] tracking-wider">
                <tr>
                  <th className="pb-3 font-semibold">Employee</th>
                  <th className="pb-3 font-semibold">Target Role</th>
                  <th className="pb-3 font-semibold">Fit / Readiness</th>
                  <th className="pb-3 font-semibold">Preference</th>
                  <th className="pb-3 font-semibold">Status</th>
                  <th className="pb-3 font-semibold text-right">HR Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/5 text-slate-300">
                {transfers.map((t) => (
                  <tr key={t.id} className="hover:bg-white/[0.02]">
                    <td className="py-4">
                      <div className="font-bold text-white">{t.employee_name}</div>
                      <div className="text-[11px] text-slate-500">{t.current_role} · {t.source_department}</div>
                    </td>
                    <td className="py-4">
                      <div className="font-semibold text-white">{t.role_title}</div>
                      <div className="text-[11px] text-slate-500">{t.department}</div>
                    </td>
                    <td className="py-4">
                      <div className="flex items-center gap-2">
                        <span className="rounded-md bg-brand-500/10 px-2 py-0.5 font-bold text-brand-300">
                          {t.fit_score}% Fit
                        </span>
                        <span className="rounded-md bg-emerald-500/10 px-2 py-0.5 font-bold text-emerald-300">
                          {t.readiness_score}% Ready
                        </span>
                      </div>
                    </td>
                    <td className="py-4">
                      {t.preference_rank ? (
                        <span className="rounded-full bg-accent-500/10 px-2.5 py-0.5 font-semibold text-accent-300">
                          Preference #{t.preference_rank}
                        </span>
                      ) : (
                        <span className="text-slate-500">—</span>
                      )}
                    </td>
                    <td className="py-4">
                      <span className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-[11px] font-semibold capitalize ${
                        t.status === "approved"
                          ? "border border-emerald-400/30 bg-emerald-500/10 text-emerald-300"
                          : t.status === "rejected"
                          ? "border border-rose-400/30 bg-rose-500/10 text-rose-300"
                          : t.status === "pending_hr"
                          ? "border border-accent-400/30 bg-accent-500/10 text-accent-300"
                          : t.status === "employee_declined"
                          ? "border border-slate-500/30 bg-slate-500/10 text-slate-400"
                          : "border border-amber-400/30 bg-amber-500/10 text-amber-300"
                      }`}>
                        {t.status.replace("_", " ")}
                      </span>
                    </td>
                    <td className="py-4 text-right">
                      {t.status === "pending_hr" ? (
                        <div className="flex justify-end gap-2">
                          <button
                            onClick={() => approveMutation.mutate(t.id)}
                            disabled={approveMutation.isPending}
                            className="rounded-lg bg-emerald-600 px-3 py-1.5 text-xs font-semibold text-white hover:bg-emerald-500 disabled:opacity-50"
                          >
                            Approve
                          </button>
                          <button
                            onClick={() => rejectMutation.mutate(t.id)}
                            disabled={rejectMutation.isPending}
                            className="rounded-lg border border-white/10 bg-white/5 px-3 py-1.5 text-xs font-semibold text-rose-300 hover:border-rose-400/40 hover:bg-rose-500/10 disabled:opacity-50"
                          >
                            Reject
                          </button>
                        </div>
                      ) : (
                        <span className="text-slate-500 text-[11px]">
                          {t.status === "approved" ? "Approved ✓" : t.status === "rejected" ? "Rejected" : "Awaiting candidate"}
                        </span>
                      )}
                    </td>
                  </tr>
                ))}

                {transfers.length === 0 && (
                  <tr>
                    <td colSpan={6} className="py-8 text-center text-slate-500">
                      No transfer requests submitted yet. Managers can shortlist candidates to initiate the governance workflow.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      </main>
    </div>
  );
}
