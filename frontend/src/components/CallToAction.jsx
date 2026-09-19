import { Link } from "react-router-dom";

import Icon from "./Icon.jsx";
import Reveal from "./Reveal.jsx";

export default function CallToAction() {
  return (
    <section className="relative pb-24 pt-8 sm:pb-32">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <Reveal>
          <div className="card-glow relative overflow-hidden rounded-[2rem] bg-gradient-to-br from-brand-600/25 via-ink-900 to-ink-950 px-6 py-16 text-center sm:px-16 sm:py-20">
            <div className="bg-grid pointer-events-none absolute inset-0 opacity-60 [mask-image:radial-gradient(ellipse_60%_70%_at_50%_50%,black,transparent)]" />
            <div className="pointer-events-none absolute -top-24 left-1/2 h-64 w-[560px] -translate-x-1/2 rounded-full bg-brand-500/25 blur-[100px]" />

            <div className="relative">
              <span className="inline-flex items-center gap-2 rounded-full border border-white/15 bg-white/5 px-3.5 py-1.5 text-xs font-semibold text-slate-200">
                <Icon name="sparkles" className="size-3.5 text-accent-300" />
                Demo accounts pre-loaded · synthetic data only
              </span>
              <h2 className="font-display mx-auto mt-6 max-w-2xl text-3xl font-bold leading-tight tracking-tight text-white sm:text-5xl">
                Stop hiring for skills you <span className="text-gradient">already have</span>.
              </h2>
              <p className="mx-auto mt-5 max-w-xl text-base leading-relaxed text-slate-300">
                Sign in as a manager, an employee, or HR and explore the full loop — from vacancy to verified skill.
              </p>
              <div className="mt-9 flex flex-wrap items-center justify-center gap-4">
                <Link
                  to="/login"
                  className="group inline-flex items-center gap-2 rounded-xl bg-white px-7 py-3.5 text-sm font-bold text-ink-950 shadow-2xl shadow-white/20 transition hover:-translate-y-0.5 hover:shadow-white/30"
                >
                  Launch the demo
                  <Icon name="arrowRight" className="size-4 transition-transform group-hover:translate-x-1" />
                </Link>
                <a
                  href="#pipeline"
                  className="inline-flex items-center gap-2 rounded-xl border border-white/20 bg-white/5 px-7 py-3.5 text-sm font-semibold text-white backdrop-blur transition hover:border-white/40"
                >
                  Revisit the architecture
                </a>
              </div>
            </div>
          </div>
        </Reveal>
      </div>
    </section>
  );
}
