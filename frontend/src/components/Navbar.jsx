import { useEffect, useState } from "react";
import { Link, useLocation } from "react-router-dom";

import Icon, { Logo } from "./Icon.jsx";
import { useAuth } from "../hooks/useAuth.jsx";
import { useHealth } from "../hooks/useHealth.js";

const LINKS = [
  { href: "#platform", label: "Platform" },
  { href: "#pipeline", label: "Pipeline" },
  { href: "#matching", label: "Matching" },
  { href: "#features", label: "Features" },
  { href: "#stack", label: "Stack" },
];

function ApiStatusPill() {
  const { data, isPending, isError } = useHealth();
  const [justLoaded, setJustLoaded] = useState(false);

  useEffect(() => {
    if (!isPending) {
      setJustLoaded(true);
      const timer = setTimeout(() => setJustLoaded(false), 900);
      return () => clearTimeout(timer);
    }
  }, [isPending]);

  const state = isPending
    ? { label: "Checking API…", dot: "bg-slate-400", pulse: "bg-slate-400" }
    : isError
      ? { label: "API offline", dot: "bg-rose-400", pulse: "bg-rose-400" }
      : { label: "API online", dot: "bg-emerald-400", pulse: "bg-emerald-300" };

  return (
    <span className="hidden items-center gap-2 rounded-full border border-white/10 bg-white/5 px-3 py-1.5 text-xs font-medium text-slate-300 md:inline-flex">
      <span className="relative grid size-2 place-items-center">
        <span className={`absolute size-2 rounded-full ${state.pulse} ${justLoaded ? "animate-pulse-ring" : ""}`} />
        <span className={`size-2 rounded-full ${state.dot} ${isPending ? "animate-blink" : ""}`} />
      </span>
      {state.label}
    </span>
  );
}

export default function Navbar() {
  const { isAuthenticated, user, logout } = useAuth();
  const location = useLocation();
  const [scrolled, setScrolled] = useState(false);
  const [open, setOpen] = useState(false);

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 12);
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  useEffect(() => setOpen(false), [location]);

  return (
    <header
      className={`fixed inset-x-0 top-0 z-50 transition-all duration-300 ${
        scrolled ? "border-b border-white/10 bg-ink-950/80 backdrop-blur-xl" : "bg-transparent"
      }`}
    >
      <nav className="mx-auto flex h-16 max-w-7xl items-center justify-between px-4 sm:px-6 lg:px-8">
        <Link to="/" className="group flex items-center gap-3">
          <Logo className="size-9 transition-transform duration-300 group-hover:rotate-6 group-hover:scale-105" />
          <span className="font-display text-lg font-bold tracking-tight text-white">
            Role<span className="text-gradient">Flow</span>
          </span>
        </Link>

        <div className="hidden items-center gap-1 lg:flex">
          {LINKS.map((link) => (
            <a
              key={link.href}
              href={link.href}
              className="rounded-lg px-3 py-2 text-sm font-medium text-slate-300 transition-colors hover:bg-white/5 hover:text-white"
            >
              {link.label}
            </a>
          ))}
        </div>

        <div className="flex items-center gap-3">
          <ApiStatusPill />
          {isAuthenticated ? (
            <div className="hidden items-center gap-3 sm:flex">
              <span className="flex items-center gap-2 rounded-full border border-white/10 bg-white/5 py-1 pl-1 pr-3">
                <span className="grid size-7 place-items-center rounded-full bg-gradient-to-br from-brand-500 to-accent-400 text-xs font-bold text-white">
                  {user?.name?.split(" ").map((part) => part[0]).slice(0, 2).join("")}
                </span>
                <span className="text-xs font-medium text-slate-200">{user?.name?.split(" ")[0]}</span>
              </span>
              <Link
                to={user?.role === "employee" ? "/employee" : user?.role === "hr" ? "/hr" : "/manager"}
                className="rounded-lg bg-brand-600 px-4 py-2 text-sm font-semibold text-white shadow-lg shadow-brand-600/25 transition hover:bg-brand-500 hover:shadow-brand-500/40"
              >
                Portal
              </Link>
              <button
                onClick={logout}
                title="Sign out"
                className="grid size-9 place-items-center rounded-lg border border-white/10 text-slate-400 transition hover:border-rose-400/40 hover:text-rose-300"
              >
                <Icon name="logout" className="size-4" />
              </button>
            </div>
          ) : (
            <Link
              to="/login"
              className="hidden rounded-lg bg-brand-600 px-4 py-2 text-sm font-semibold text-white shadow-lg shadow-brand-600/25 transition hover:-translate-y-px hover:bg-brand-500 hover:shadow-brand-500/40 sm:block"
            >
              Sign in
            </Link>
          )}
          <button
            onClick={() => setOpen((value) => !value)}
            className="grid size-9 place-items-center rounded-lg border border-white/10 text-slate-300 lg:hidden"
            aria-label="Toggle menu"
          >
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" className="size-5">
              {open ? <path d="M6 6l12 12M18 6 6 18" /> : <path d="M4 7h16M4 12h16M4 17h16" />}
            </svg>
          </button>
        </div>
      </nav>

      {open && (
        <div className="border-t border-white/10 bg-ink-950/95 px-4 py-4 backdrop-blur-xl lg:hidden">
          <div className="flex flex-col gap-1">
            {LINKS.map((link) => (
              <a
                key={link.href}
                href={link.href}
                className="rounded-lg px-3 py-2.5 text-sm font-medium text-slate-300 transition hover:bg-white/5 hover:text-white"
              >
                {link.label}
              </a>
            ))}
            <Link
              to={isAuthenticated ? (user?.role === "employee" ? "/employee" : user?.role === "hr" ? "/hr" : "/manager") : "/login"}
              className="mt-2 rounded-lg bg-brand-600 px-3 py-2.5 text-center text-sm font-semibold text-white"
            >
              {isAuthenticated ? "Open portal" : "Sign in"}
            </Link>
          </div>
        </div>
      )}
    </header>
  );
}
