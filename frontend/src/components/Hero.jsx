import { Link } from "react-router-dom";

import Icon from "./Icon.jsx";
import Reveal from "./Reveal.jsx";
import SkillGraphVisual from "./SkillGraphVisual.jsx";

const STATS = [
  { value: "10k", label: "Employees as a skill graph" },
  { value: "≥30%", label: "Cross-family talent discovered" },
  { value: "2-axis", label: "Fit vs. Readiness ranking" },
  { value: "100%", label: "Evidence-backed explanations" },
];

export default function Hero() {
  return (
    <section className="relative overflow-hidden pt-16">
      <div className="bg-grid pointer-events-none absolute inset-0 [mask-image:radial-gradient(ellipse_75%_60%_at_50%_35%,black,transparent)]" />
      <div className="pointer-events-none absolute -top-32 left-1/2 h-[420px] w-[820px] -translate-x-1/2 rounded-full bg-brand-600/20 blur-[130px]" />

      <div className="relative mx-auto max-w-7xl px-4 pb-20 pt-16 sm:px-6 sm:pt-24 lg:px-8 lg:pb-28">
        <div className="grid items-center gap-14 lg:grid-cols-[1.05fr_0.95fr]">
          <div>
            <Reveal>
              <span className="inline-flex items-center gap-2 rounded-full border border-brand-400/30 bg-brand-500/10 px-3.5 py-1.5 text-xs font-semibold text-brand-300">
                <Icon name="sparkles" className="size-3.5" />
                Agentic AI · GPT-OSS-120B · LangGraph
              </span>
            </Reveal>

            <Reveal delay={90}>
              <h1 className="font-display mt-6 text-4xl font-bold leading-[1.08] tracking-tight text-white sm:text-5xl lg:text-6xl">
                The talent you're hiring for is{" "}
                <span className="shimmer-text">already inside</span>{" "}
                your company.
              </h1>
            </Reveal>

            <Reveal delay={180}>
              <p className="mt-6 max-w-xl text-base leading-relaxed text-slate-400 sm:text-lg">
                RoleFlow is an agentic AI-powered internal talent mobility platform that analyzes employee skills,
                experience, projects, and learning history to discover suitable internal candidates for organizational
                roles, identify skill gaps, and recommend personalized learning paths.
              </p>
            </Reveal>

            <Reveal delay={270}>
              <div className="mt-9 flex flex-wrap items-center gap-4">
                <Link
                  to="/login"
                  className="group inline-flex items-center gap-2 rounded-xl bg-gradient-to-r from-brand-600 to-brand-500 px-6 py-3.5 text-sm font-semibold text-white shadow-xl shadow-brand-600/30 transition hover:-translate-y-0.5 hover:shadow-brand-500/50"
                >
                  Try the live demo
                  <Icon name="arrowRight" className="size-4 transition-transform group-hover:translate-x-1" />
                </Link>
                <a
                  href="#pipeline"
                  className="inline-flex items-center gap-2 rounded-xl border border-white/15 bg-white/5 px-6 py-3.5 text-sm font-semibold text-slate-200 backdrop-blur transition hover:border-brand-400/40 hover:text-white"
                >
                  <Icon name="compass" className="size-4 text-accent-400" />
                  See how it works
                </a>
              </div>
            </Reveal>

            <Reveal delay={360}>
              <dl className="mt-12 grid grid-cols-2 gap-x-6 gap-y-6 sm:grid-cols-4">
                {STATS.map((stat) => (
                  <div key={stat.label} className="border-l border-white/10 pl-4">
                    <dt className="font-display text-2xl font-bold text-white sm:text-3xl">{stat.value}</dt>
                    <dd className="mt-1 text-xs leading-snug text-slate-500">{stat.label}</dd>
                  </div>
                ))}
              </dl>
            </Reveal>
          </div>

          <Reveal delay={200} className="lg:pl-4">
            <SkillGraphVisual />
          </Reveal>
        </div>
      </div>
    </section>
  );
}
