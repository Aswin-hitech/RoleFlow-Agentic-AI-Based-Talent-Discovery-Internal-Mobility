import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import Icon, { Logo } from "../components/Icon.jsx";
import { api } from "../lib/api";
import { useAuth } from "../hooks/useAuth.jsx";
import { useHealth } from "../hooks/useHealth.js";
import RoleCreationWizard from "../components/RoleCreationWizard.jsx";

function timeAgo(isoString) {
  if (!isoString) return "just now";
  const seconds = Math.max(0, (Date.now() - new Date(isoString).getTime()) / 1000);
  if (seconds < 60) return "just now";
  const minutes = Math.floor(seconds / 60);
  if (minutes < 60) return `${minutes} min ago`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours} h ago`;
  return `${Math.floor(hours / 24)} d ago`;
}

function ServiceBar() {
  const { data, isPending, isError } = useHealth();
  const services = [
    { name: "PostgreSQL", state: isPending ? "pending" : isError ? "Unavailable" : data.services?.postgres || "Connected", action: "Start PostgreSQL" },
    { name: "Redis", state: isPending ? "pending" : isError ? "Unavailable" : data.services?.redis || "Connected", action: "Start Redis" },
    { name: "MongoDB", state: isPending ? "pending" : isError ? "Unavailable" : data.services?.mongodb || "Connected", action: "Start MongoDB" },
    { name: "GPT-OSS-120B", state: isPending ? "pending" : isError ? "Configured" : data.services?.llm || "Configured", action: "Check LLM endpoint" },
  ];

  const tone = (state) =>
    state === "Connected" || state === "ok" || state === "configured" || state === "Configured"
      ? "border-emerald-400/30 bg-emerald-500/10 text-emerald-300"
      : state === "pending"
        ? "border-amber-400/30 bg-amber-500/10 text-amber-300"
        : "border-rose-400/30 bg-rose-500/10 text-rose-300";

  return (
    <div className="flex flex-wrap items-center gap-2">
      {services.map((service) => (
        <span
          key={service.name}
          title={service.state === "Connected" ? "Service Connected" : service.action}
          className={`rounded-full border px-3 py-1 text-[11px] font-semibold ${tone(service.state)}`}
        >
          {service.name}: {service.state}
        </span>
      ))}
    </div>
  );
}

function RoleCard({ role, onRefresh, refreshing, onOpen }) {
  return (
    <div className="group relative overflow-hidden rounded-3xl border border-white/10 bg-ink-900/60 p-6 transition-all duration-300 hover:-translate-y-1 hover:border-brand-400/30">
      <div className="pointer-events-none absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-brand-400/50 to-transparent opacity-0 transition-opacity group-hover:opacity-100" />
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h3 className="font-display text-lg font-bold text-white">{role.title}</h3>
          <p className="mt-0.5 text-sm text-slate-500">{role.department} · {role.headcount} {role.headcount === 1 ? "vacancy" : "vacancies"}</p>
        </div>
        <div className="flex items-center gap-2">
          <span
            className={`rounded-full border px-2.5 py-1 text-[11px] font-semibold capitalize ${
              role.status === "vacant"
                ? "border-emerald-400/30 bg-emerald-500/10 text-emerald-300"
                : "border-slate-400/30 bg-slate-500/10 text-slate-300"
            }`}
          >
            {role.status}
          </span>
          <span
            className={`inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-[11px] font-semibold ${
              role.visibility === "visible"
                ? "border-brand-400/30 bg-brand-500/10 text-brand-300"
                : "border-amber-400/30 bg-amber-500/10 text-amber-300"
            }`}
          >
            <Icon name={role.visibility === "visible" ? "eye" : "lock"} className="size-3" />
            {role.visibility}
          </span>
        </div>
      </div>

      <div className="mt-6 grid grid-cols-2 gap-3 sm:grid-cols-4">
        {[
          { label: "Candidates found", value: role.candidates_found || 0, tone: "text-white" },
          { label: "Ready now", value: role.ready_now || 0, tone: "text-emerald-300" },
          { label: "Shortlisted", value: role.self_nominated || 0, tone: "text-brand-300" },
          { label: "New in pool", value: role.new_candidates || 0, tone: (role.new_candidates || 0) > 0 ? "text-accent-300" : "text-slate-400" },
        ].map((stat) => (
          <div key={stat.label} className="rounded-2xl border border-white/5 bg-ink-950/60 px-3.5 py-3">
            <p className={`font-display text-xl font-bold ${stat.tone}`}>{stat.value}</p>
            <p className="mt-0.5 text-[10px] font-medium uppercase tracking-wide text-slate-500">{stat.label}</p>
          </div>
        ))}
      </div>

      <div className="mt-6 flex flex-wrap items-center justify-between gap-3">
        <p className="text-xs text-slate-500">
          Discovered {timeAgo(role.last_discovered_at)} · LangGraph pipeline
        </p>
        <div className="flex gap-2">
          <button
            onClick={() => onRefresh(role)}
            disabled={refreshing}
            className="inline-flex items-center gap-1.5 rounded-lg border border-white/10 bg-white/5 px-3.5 py-2 text-xs font-semibold text-slate-200 transition hover:border-brand-400/40 hover:text-white disabled:opacity-50"
          >
            <Icon name="refresh" className={`size-3.5 ${refreshing ? "animate-spin" : ""}`} />
            {refreshing ? "Queuing…" : "Refresh discovery"}
          </button>
          <button
            onClick={() => onOpen(role)}
            className="inline-flex items-center gap-1.5 rounded-lg bg-brand-600 px-3.5 py-2 text-xs font-semibold text-white shadow-lg shadow-brand-600/25 transition hover:bg-brand-500"
          >
            Open role
            <Icon name="arrowRight" className="size-3.5" />
          </button>
        </div>
      </div>
    </div>
  );
}

export default function Dashboard() {
  const { user, logout } = useAuth();
  const queryClient = useQueryClient();
  const navigate = useNavigate();
  const [notice, setNotice] = useState("");
  const [wizardOpen, setWizardOpen] = useState(false);

  const rolesQuery = useQuery({
    queryKey: ["manager-roles"],
    queryFn: () => api("/manager/roles"),
    retry: false,
  });

  const refreshMutation = useMutation({
    mutationFn: (role) => api(`/manager/roles/${role.id}/discovery`, { method: "POST" }),
    onSuccess: () => {
      setNotice("Candidate discovery dispatched across the 6 logical AI agents.");
      queryClient.invalidateQueries({ queryKey: ["manager-roles"] });
    },
    onError: (error) => setNotice(error.message || "Refresh failed."),
  });

  const roles = rolesQuery.data?.roles || [];
  const totals = roles.reduce(
    (acc, role) => ({
      candidates: acc.candidates + (role.candidates_found || 0),
      ready: acc.ready + (role.ready_now || 0),
      nominated: acc.nominated + (role.self_nominated || 0),
    }),
    { candidates: 0, ready: 0, nominated: 0 },
  );

  return (
    <div className="min-h-screen bg-ink-950 text-slate-100">
      <header className="sticky top-0 z-40 border-b border-white/10 bg-ink-950/85 backdrop-blur-xl">
        <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-4 sm:px-6 lg:px-8">
          <Link to="/" className="flex items-center gap-3">
            <Logo className="size-8" />
            <span className="font-display text-base font-bold tracking-tight text-white">
              Role<span className="text-gradient">Flow</span>
            </span>
            <span className="ml-2 hidden rounded-full border border-white/10 bg-white/5 px-2.5 py-0.5 text-[11px] font-semibold text-brand-300 sm:block">
              MANAGER PORTAL
            </span>
          </Link>
          <div className="flex items-center gap-3">
            <span className="hidden text-xs text-slate-400 sm:block">{user?.name}</span>
            <Link to="/" className="rounded-lg border border-white/10 px-3 py-1.5 text-xs font-semibold text-slate-300 transition hover:border-white/25 hover:text-white">
              Home
            </Link>
            <button
              onClick={logout}
              className="grid size-9 place-items-center rounded-lg border border-white/10 text-slate-400 transition hover:border-rose-400/40 hover:text-rose-300"
              title="Sign out"
            >
              <Icon name="logout" className="size-4" />
            </button>
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-7xl px-4 py-10 sm:px-6 lg:px-8">
        <div className="flex flex-wrap items-end justify-between gap-4">
          <div>
            <h1 className="font-display text-2xl font-bold tracking-tight text-white sm:text-3xl">Vacant Roles</h1>
            <p className="mt-1.5 text-sm text-slate-400">
              RoleFlow discovers suitable internal candidates automatically using deterministic scoring and evidence grounding.
            </p>
          </div>
          <ServiceBar />
        </div>

        {notice && (
          <p className="mt-6 rounded-xl border border-brand-400/30 bg-brand-500/10 px-4 py-3 text-sm text-brand-200">
            {notice}
          </p>
        )}

        {/* Dashboard calculated metrics (§49) */}
        <div className="mt-8 grid grid-cols-2 gap-4 sm:grid-cols-4">
          {[
            { label: "Active Roles", value: roles.length, icon: "target", tone: "text-brand-300" },
            { label: "Candidates Found", value: totals.candidates, icon: "users", tone: "text-white" },
            { label: "Ready Now (≥70%)", value: totals.ready, icon: "zap", tone: "text-emerald-300" },
            { label: "Shortlisted", value: totals.nominated, icon: "sparkles", tone: "text-accent-300" },
          ].map((stat) => (
            <div key={stat.label} className="card-glow rounded-2xl bg-ink-900/60 p-5">
              <div className="flex items-center justify-between">
                <p className="text-[11px] font-semibold uppercase tracking-widest text-slate-500">{stat.label}</p>
                <Icon name={stat.icon} className={`size-4 ${stat.tone}`} />
              </div>
              <p className={`font-display mt-2 text-3xl font-bold ${stat.tone}`}>
                {rolesQuery.isPending ? "—" : stat.value}
              </p>
            </div>
          ))}
        </div>

        {/* Role Cards List */}
        <div className="mt-8 grid gap-5 lg:grid-cols-2">
          {roles.map((role) => (
            <RoleCard
              key={role.id}
              role={role}
              onRefresh={(selected) => refreshMutation.mutate(selected)}
              refreshing={refreshMutation.isPending && refreshMutation.variables?.id === role.id}
              onOpen={(selected) => navigate(`/manager/roles/${selected.id}`)}
            />
          ))}
        </div>

        {/* Functional "Create New Role" Button (§18) */}
        <button
          onClick={() => setWizardOpen(true)}
          className="group mt-6 flex w-full items-center justify-center gap-2 rounded-3xl border border-dashed border-white/15 bg-ink-900/30 px-6 py-8 text-sm font-semibold text-slate-400 transition hover:border-brand-400/40 hover:bg-brand-500/5 hover:text-brand-200"
        >
          <span className="grid size-8 place-items-center rounded-full border border-white/15 transition group-hover:border-brand-400/50">+</span>
          Create New Role — paste JD, extract with Role Intelligence Agent, review criteria, launch discovery
        </button>
      </main>

      {/* Role Creation Wizard Modal (§18) */}
      <RoleCreationWizard
        isOpen={wizardOpen}
        onClose={() => setWizardOpen(false)}
        onCreated={(newRole) => {
          queryClient.invalidateQueries({ queryKey: ["manager-roles"] });
          setNotice(`Role '${newRole.title}' created! Discovery launched across the 6 logical agents.`);
        }}
      />
    </div>
  );
}
