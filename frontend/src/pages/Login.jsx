import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";

import Icon, { Logo } from "../components/Icon.jsx";
import { useAuth } from "../hooks/useAuth.jsx";

const DEMO_ACCOUNTS = [
  { email: "manager@roleflow.io", role: "Manager", name: "Priya Sharma", blurb: "Role creation, discovery & matching", icon: "target" },
  { email: "employee@roleflow.io", role: "Employee", name: "Arjun Mehta", blurb: "Opportunities & learning roadmap", icon: "compass" },
  { email: "hr@roleflow.io", role: "HR / Admin", name: "Sneha Rao", blurb: "Workforce mobility & transfer governance", icon: "barChart" },
];

export default function Login() {
  const { login } = useAuth();
  const navigate = useNavigate();

  const [email, setEmail] = useState("manager@roleflow.io");
  const [password, setPassword] = useState("demo1234");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(event) {
    event.preventDefault();
    setError("");
    setLoading(true);
    try {
      const authUser = await login(email, password);
      // Route based on role (§45)
      if (authUser?.role === "employee") {
        navigate("/employee");
      } else if (authUser?.role === "hr") {
        navigate("/hr");
      } else {
        navigate("/manager");
      }
    } catch (err) {
      setError(err.message || "Sign-in failed. Is the Flask API running on :5000?");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="grid min-h-screen lg:grid-cols-2">
      {/* Form side */}
      <div className="flex flex-col px-6 py-8 sm:px-12 lg:px-16">
        <Link to="/" className="group inline-flex items-center gap-3 self-start">
          <Logo className="size-9 transition-transform group-hover:rotate-6" />
          <span className="font-display text-lg font-bold tracking-tight text-white">
            Role<span className="text-gradient">Flow</span>
          </span>
        </Link>

        <div className="mx-auto flex w-full max-w-md flex-1 flex-col justify-center py-12">
          <h1 className="font-display text-3xl font-bold tracking-tight text-white">Welcome back</h1>
          <p className="mt-2 text-sm text-slate-400">
            Sign in with a demo account — every persona is pre-loaded with synthetic data.
          </p>

          <form onSubmit={handleSubmit} className="mt-8 space-y-5">
            <div>
              <label htmlFor="email" className="mb-1.5 block text-sm font-medium text-slate-300">
                Work email
              </label>
              <input
                id="email"
                type="email"
                required
                value={email}
                onChange={(event) => setEmail(event.target.value)}
                className="w-full rounded-xl border border-white/10 bg-ink-900/80 px-4 py-3 text-sm text-white placeholder-slate-500 outline-none transition focus:border-brand-400/60 focus:ring-2 focus:ring-brand-500/20"
                placeholder="you@company.com"
                autoComplete="email"
              />
            </div>
            <div>
              <label htmlFor="password" className="mb-1.5 block text-sm font-medium text-slate-300">
                Password
              </label>
              <input
                id="password"
                type="password"
                required
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                className="w-full rounded-xl border border-white/10 bg-ink-900/80 px-4 py-3 text-sm text-white placeholder-slate-500 outline-none transition focus:border-brand-400/60 focus:ring-2 focus:ring-brand-500/20"
                placeholder="••••••••"
                autoComplete="current-password"
              />
            </div>

            {error && (
              <p className="rounded-xl border border-rose-400/30 bg-rose-500/10 px-4 py-3 text-sm text-rose-300">
                {error}
              </p>
            )}

            <button
              type="submit"
              disabled={loading}
              className="group flex w-full items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-brand-600 to-brand-500 px-6 py-3.5 text-sm font-semibold text-white shadow-xl shadow-brand-600/30 transition hover:-translate-y-0.5 disabled:cursor-not-allowed disabled:opacity-60"
            >
              {loading ? (
                <span className="size-4 animate-spin rounded-full border-2 border-white/30 border-t-white" />
              ) : (
                <Icon name="zap" className="size-4" />
              )}
              {loading ? "Signing in…" : "Sign in with JWT"}
            </button>

            <div className="flex items-center gap-3">
              <span className="h-px flex-1 bg-white/10" />
              <span className="text-xs font-medium uppercase tracking-wider text-slate-500">or pick a persona</span>
              <span className="h-px flex-1 bg-white/10" />
            </div>

            <div className="grid gap-2.5">
              {DEMO_ACCOUNTS.map((account) => (
                <button
                  key={account.email}
                  type="button"
                  onClick={() => {
                    setEmail(account.email);
                    setPassword("demo1234");
                  }}
                  className={`flex items-center gap-3.5 rounded-xl border px-4 py-3 text-left transition ${
                    email === account.email
                      ? "border-brand-400/50 bg-brand-500/10"
                      : "border-white/10 bg-ink-900/50 hover:border-white/25"
                  }`}
                >
                  <span className="grid size-9 shrink-0 place-items-center rounded-lg border border-white/10 bg-ink-800 text-brand-300">
                    <Icon name={account.icon} className="size-4" />
                  </span>
                  <span className="min-w-0 flex-1">
                    <span className="block text-sm font-semibold text-white">
                      {account.role} <span className="font-normal text-slate-500">· {account.name}</span>
                    </span>
                    <span className="block truncate text-xs text-slate-500">{account.blurb}</span>
                  </span>
                  {email === account.email && <Icon name="check" className="size-4 shrink-0 text-brand-300" />}
                </button>
              ))}
            </div>
          </form>

          <p className="mt-8 text-center text-xs text-slate-500">
            OAuth (Google / GitHub) ready via env keys · JWT access + refresh tokens
          </p>
        </div>
      </div>

      {/* Visual side */}
      <div className="relative hidden overflow-hidden border-l border-white/10 bg-ink-900/40 lg:block">
        <div className="bg-grid absolute inset-0" />
        <div className="pointer-events-none absolute -left-20 top-1/4 h-96 w-96 rounded-full bg-brand-600/20 blur-[120px]" />
        <div className="pointer-events-none absolute -right-10 bottom-10 h-72 w-72 rounded-full bg-accent-500/15 blur-[100px]" />

        <div className="relative flex h-full flex-col justify-center px-14">
          <span className="w-fit rounded-full border border-accent-400/30 bg-accent-500/10 px-3.5 py-1.5 text-xs font-semibold text-accent-300">
            The core intelligence loop
          </span>
          <h2 className="font-display mt-6 max-w-md text-3xl font-bold leading-snug tracking-tight text-white">
            Employee Intelligence → Matching → Learning → <span className="text-gradient">Verified skill</span>
          </h2>
          <ol className="mt-10 space-y-0">
            {[
              "Profiles become evidence-backed skill graphs",
              "Roles become weighted requirement profiles",
              "Ontology bridges transferable skills",
              "Fit and Readiness ranked on separate axes",
              "Roadmaps close the gap, projects prove it",
            ].map((line, index) => (
              <li key={line} className="relative flex gap-5 pb-8 last:pb-0">
                {index !== 4 && <span className="absolute left-[17px] top-9 h-full w-px bg-gradient-to-b from-brand-400/40 to-transparent" />}
                <span className="font-display grid size-9 shrink-0 place-items-center rounded-full border border-brand-400/40 bg-brand-500/15 text-sm font-bold text-brand-300">
                  {index + 1}
                </span>
                <p className="pt-2 text-sm leading-relaxed text-slate-300">{line}</p>
              </li>
            ))}
          </ol>
        </div>
      </div>
    </div>
  );
}
