import { Link } from "react-router-dom";

import { Logo } from "./Icon.jsx";

const COLUMNS = [
  {
    title: "Platform",
    links: [
      { label: "Vacancy management", href: "#platform" },
      { label: "Matching engine", href: "#matching" },
      { label: "Learning & verification", href: "#features" },
      { label: "Workforce intelligence", href: "#features" },
    ],
  },
  {
    title: "Portals",
    links: [
      { label: "Manager", href: "#personas" },
      { label: "Employee", href: "#personas" },
      { label: "HR / Admin", href: "#personas" },
    ],
  },
  {
    title: "Engineering",
    links: [
      { label: "Tech stack", href: "#stack" },
      { label: "API health", href: "/dashboard" },
      { label: "Demo sign-in", href: "/login" },
    ],
  },
];

export default function Footer() {
  return (
    <footer className="relative border-t border-white/10 bg-ink-950">
      <div className="pointer-events-none absolute inset-x-0 -top-px mx-auto h-px w-2/3 bg-gradient-to-r from-transparent via-brand-500/60 to-transparent" />
      <div className="mx-auto max-w-7xl px-4 py-14 sm:px-6 lg:px-8">
        <div className="grid gap-10 md:grid-cols-[1.4fr_repeat(3,1fr)]">
          <div>
            <div className="flex items-center gap-3">
              <Logo />
              <span className="font-display text-lg font-bold tracking-tight text-white">
                Role<span className="text-gradient">Flow</span>
              </span>
            </div>
            <p className="mt-4 max-w-xs text-sm leading-relaxed text-slate-400">
              An explainable, human-in-the-loop AI platform that turns a company's workforce into a searchable,
              evolving skill graph.
            </p>
            <p className="mt-6 text-xs text-slate-500">
              Built for the hackathon stage · React 19 · Flask · pgvector · LangGraph · GPT-OSS-120B
            </p>
          </div>
          {COLUMNS.map((column) => (
            <div key={column.title}>
              <h4 className="text-sm font-semibold tracking-wide text-white">{column.title}</h4>
              <ul className="mt-4 space-y-2.5">
                {column.links.map((link) => (
                  <li key={link.label}>
                    {link.href.startsWith("#") ? (
                      <a href={link.href} className="text-sm text-slate-400 transition hover:text-brand-300">
                        {link.label}
                      </a>
                    ) : (
                      <Link to={link.href} className="text-sm text-slate-400 transition hover:text-brand-300">
                        {link.label}
                      </Link>
                    )}
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>
        <div className="mt-12 flex flex-col items-center justify-between gap-4 border-t border-white/5 pt-8 sm:flex-row">
          <p className="text-xs text-slate-500">© {new Date().getFullYear()} RoleFlow. Demo environment — synthetic data only.</p>
          <p className="text-xs text-slate-500">
            Privacy by design · No protected attributes in scoring · Every decision audit-logged
          </p>
        </div>
      </div>
    </footer>
  );
}
