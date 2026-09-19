import { useState } from "react";

import Icon from "./Icon.jsx";
import Reveal from "./Reveal.jsx";
import { SectionHeading } from "./Pipeline.jsx";

const CANDIDATES = [
  { id: "EMP-1024", name: "Arjun M.", fit: 92, readiness: 81, note: "Data Analyst → ML Engineer (Python & SQL demonstrated in Customer Analytics)", quadrant: "ready" },
  { id: "EMP-1025", name: "Kavita R.", fit: 89, readiness: 85, note: "Software Engineer → Full Stack / ML APIs", quadrant: "ready" },
  { id: "EMP-1026", name: "Rohan V.", fit: 68, readiness: 84, note: "QA Automation → DevOps / Backend testing", quadrant: "grow" },
  { id: "EMP-0231", name: "Divya K.", fit: 91, readiness: 35, note: "Strong data modeling, active on critical project with 6 weeks remaining", quadrant: "skilled" },
  { id: "EMP-0487", name: "Rohan S.", fit: 62, readiness: 78, note: "Data engineering background, completing MLOps roadmap", quadrant: "grow" },
  { id: "EMP-0712", name: "Meera T.", fit: 41, readiness: 30, note: "Adjacent skill domain, low role alignment", quadrant: "low" },
  { id: "EMP-0344", name: "Farhan A.", fit: 88, readiness: 65, note: "Data pipeline lead, availability in 30d", quadrant: "ready" },
];

const QUADRANTS = [
  {
    key: "skilled",
    title: "Skilled, not interested",
    text: "High Fit, low Readiness — great capability but no signal of willingness.",
    corner: "top-right",
  },
  {
    key: "ready",
    title: "Ready Now",
    text: "High Fit and high Readiness — the top shortlist.",
    corner: "bottom-right",
  },
  {
    key: "low",
    title: "Not a fit",
    text: "Low on both axes — excluded gracefully with feedback.",
    corner: "top-left",
  },
  {
    key: "grow",
    title: "Grow & Coach",
    text: "Willing but needs upskilling — a roadmap closes the gap.",
    corner: "bottom-left",
  },
];

const COLORS = {
  ready: "bg-emerald-400",
  grow: "bg-amber-400",
  skilled: "bg-brand-400",
  low: "bg-slate-500",
};

export default function Quadrant() {
  const [selected, setSelected] = useState(CANDIDATES[0]);

  return (
    <section id="matching" className="relative py-24 sm:py-32">
      <div className="pointer-events-none absolute right-0 top-24 h-72 w-72 rounded-full bg-accent-500/10 blur-[100px]" />
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <SectionHeading
          eyebrow="Two-axis ranking"
          title="Capability never hides behind willingness"
          description="Fit (can they do it?) and Readiness (are they willing and available?) are scored, displayed and filtered as separate axes — never silently blended."
        />

        <div className="mt-16 grid items-start gap-10 lg:grid-cols-[1.15fr_0.85fr]">
          <Reveal>
            <div className="card-glow glass rounded-3xl p-6 sm:p-8">
              <div className="relative">
                <span className="absolute -left-1 top-1/2 -translate-y-1/2 -rotate-90 text-[10px] font-semibold uppercase tracking-widest text-slate-500">
                  Readiness →
                </span>
                <span className="absolute -bottom-5 left-1/2 -translate-x-1/2 text-[10px] font-semibold uppercase tracking-widest text-slate-500">
                  Fit →
                </span>

                <div className="ml-6 grid aspect-square grid-cols-2 grid-rows-2 gap-1.5 overflow-hidden rounded-2xl border border-white/10">
                  {QUADRANTS.map((quadrant) => (
                    <div
                      key={quadrant.key}
                      className={`relative border border-white/5 ${
                        quadrant.corner === "top-left" ? "rounded-tl-2xl bg-slate-500/5" :
                        quadrant.corner === "top-right" ? "rounded-tr-2xl bg-brand-500/10" :
                        quadrant.corner === "bottom-left" ? "rounded-bl-2xl bg-amber-500/10" :
                        "rounded-br-2xl bg-emerald-500/10"
                      }`}
                    >
                      <p className="absolute left-3 top-2.5 text-[11px] font-semibold text-slate-300">{quadrant.title}</p>
                    </div>
                  ))}

                  {CANDIDATES.map((candidate) => (
                    <button
                      key={candidate.id}
                      onClick={() => setSelected(candidate)}
                      style={{
                        gridColumn: candidate.fit >= 50 ? 2 : 1,
                        gridRow: candidate.readiness >= 50 ? 2 : 1,
                        justifySelf: candidate.fit >= 84 ? "end" : candidate.fit <= 44 ? "start" : "center",
                        alignSelf: candidate.readiness >= 84 ? "end" : candidate.readiness <= 34 ? "start" : "center",
                      }}
                      className={`relative z-10 m-[12%] grid size-7 place-items-center rounded-full ring-2 ring-ink-950 transition-all duration-300 hover:scale-125 ${
                        COLORS[candidate.quadrant]
                      } ${selected.id === candidate.id ? "scale-125 ring-2 ring-white/70" : ""}`}
                      title={`${candidate.name} — Fit ${candidate.fit} / Readiness ${candidate.readiness}`}
                      aria-label={`${candidate.name}, fit ${candidate.fit}, readiness ${candidate.readiness}`}
                    >
                      <span className="text-[9px] font-bold text-ink-950">{candidate.fit}</span>
                    </button>
                  ))}
                </div>

                <div className="mt-7 flex flex-wrap items-center gap-x-5 gap-y-2">
                  {[
                    { key: "ready", label: "Ready Now" },
                    { key: "grow", label: "Grow & Coach" },
                    { key: "skilled", label: "Skilled, not interested" },
                    { key: "low", label: "Not a fit" },
                  ].map((legend) => (
                    <span key={legend.key} className="flex items-center gap-2 text-xs text-slate-400">
                      <span className={`size-2.5 rounded-full ${COLORS[legend.key]}`} />
                      {legend.label}
                    </span>
                  ))}
                </div>
              </div>
            </div>
          </Reveal>

          <div className="space-y-5">
            <Reveal delay={120}>
              <div className="rounded-3xl border border-white/10 bg-ink-900/60 p-6">
                <div className="flex items-start justify-between gap-4">
                  <div>
                    <p className="text-xs font-medium uppercase tracking-widest text-slate-500">Why this candidate?</p>
                    <h3 className="font-display mt-1.5 text-xl font-bold text-white">
                      {selected.name} <span className="text-sm font-medium text-slate-500">{selected.id}</span>
                    </h3>
                  </div>
                  <span className="rounded-full border border-emerald-400/30 bg-emerald-500/10 px-3 py-1 text-[11px] font-semibold text-emerald-300">
                    {selected.quadrant === "ready" ? "Top shortlist" : selected.quadrant === "grow" ? "Upskill first" : selected.quadrant === "skilled" ? "Approach carefully" : "Deprioritised"}
                  </span>
                </div>

                <div className="mt-5 space-y-4">
                  {[
                    { label: "Fit", value: selected.fit, bar: "from-brand-500 to-brand-400" },
                    { label: "Readiness", value: selected.readiness, bar: "from-accent-500 to-accent-400" },
                  ].map((metric) => (
                    <div key={metric.label}>
                      <div className="mb-1.5 flex items-center justify-between text-xs">
                        <span className="font-medium text-slate-300">{metric.label}</span>
                        <span className="font-display font-bold text-white">{metric.value}%</span>
                      </div>
                      <div className="h-2 overflow-hidden rounded-full bg-ink-700">
                        <div
                          className={`h-full rounded-full bg-gradient-to-r ${metric.bar} transition-all duration-700`}
                          style={{ width: `${metric.value}%` }}
                        />
                      </div>
                    </div>
                  ))}
                </div>

                <p className="mt-5 rounded-xl border border-white/5 bg-ink-950/60 p-3.5 text-[13px] leading-relaxed text-slate-400">
                  <Icon name="sparkles" className="mr-1.5 inline size-3.5 text-brand-300" />
                  {selected.note}
                </p>
              </div>
            </Reveal>

            <Reveal delay={220}>
              <div className="rounded-3xl border border-white/10 bg-ink-900/60 p-6">
                <p className="text-xs font-medium uppercase tracking-widest text-slate-500">Evidence chips</p>
                <div className="mt-3 flex flex-wrap gap-2">
                  {["prj_1024_1 · Customer Analytics", "cert_ibm · Data Science", "prj_1024_2 · Churn Modeling", "assess_04 · Python & ML Benchmark"].map(
                    (chip) => (
                      <span
                        key={chip}
                        className="rounded-full border border-brand-400/25 bg-brand-500/10 px-3 py-1.5 text-[11px] font-medium text-brand-200 transition hover:border-brand-300/50"
                      >
                        {chip}
                      </span>
                    ),
                  )}
                </div>
                <p className="mt-4 text-[13px] leading-relaxed text-slate-500">
                  A validator strips any claim whose evidence ID doesn't exist in the database — explanations stay
                  grounded.
                </p>
              </div>
            </Reveal>
          </div>
        </div>
      </div>
    </section>
  );
}
