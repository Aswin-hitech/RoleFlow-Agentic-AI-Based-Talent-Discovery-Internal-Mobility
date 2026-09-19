import Icon from "./Icon.jsx";
import Reveal from "./Reveal.jsx";

export function SectionHeading({ eyebrow, title, description }) {
  return (
    <div className="mx-auto max-w-2xl text-center">
      <Reveal>
        <span className="inline-block rounded-full border border-accent-400/30 bg-accent-500/10 px-3.5 py-1 text-xs font-semibold uppercase tracking-widest text-accent-300">
          {eyebrow}
        </span>
      </Reveal>
      <Reveal delay={80}>
        <h2 className="font-display mt-4 text-3xl font-bold tracking-tight text-white sm:text-4xl">{title}</h2>
      </Reveal>
      {description && (
        <Reveal delay={160}>
          <p className="mt-4 text-base leading-relaxed text-slate-400">{description}</p>
        </Reveal>
      )}
    </div>
  );
}

const STEPS = [
  {
    icon: "users",
    title: "Employee Intelligence",
    text: "Profiles become skill graphs — proficiency, confidence, evidence and decay for every skill.",
    color: "text-brand-300",
    ring: "group-hover:ring-brand-400/40",
  },
  {
    icon: "target",
    title: "Role Intelligence",
    text: "Paste or upload a JD; the LLM returns a structured, manager-editable requirement profile.",
    color: "text-accent-300",
    ring: "group-hover:ring-accent-400/40",
  },
  {
    icon: "gitFork",
    title: "Transferable Discovery",
    text: "The skill ontology bridges families — Python & SQL experience earns ML and Data Engineering credit, backed by project evidence.",
    color: "text-brand-300",
    ring: "group-hover:ring-brand-400/40",
  },
  {
    icon: "search",
    title: "Two-Axis Matching",
    text: "Hard eligibility → pgvector retrieval → ontology scoring → LLM review → Fit & Readiness ranking.",
    color: "text-accent-300",
    ring: "group-hover:ring-accent-400/40",
  },
  {
    icon: "shieldCheck",
    title: "Explainability",
    text: "Every claim cites a real project, cert or assessment — hallucinated evidence is rejected.",
    color: "text-brand-300",
    ring: "group-hover:ring-brand-400/40",
  },
  {
    icon: "graduation",
    title: "Learning & Verification",
    text: "Time-boxed roadmaps, hands-on projects and rubric grading update the skill graph automatically.",
    color: "text-accent-300",
    ring: "group-hover:ring-accent-400/40",
  },
  {
    icon: "refresh",
    title: "Continuous Re-match",
    text: "Course completed, cert earned, role changed — the profile updates and matches refresh via events.",
    color: "text-brand-300",
    ring: "group-hover:ring-brand-400/40",
  },
  {
    icon: "barChart",
    title: "Workforce Intelligence",
    text: "Skill heatmaps, demand forecasts and reskilling pools give HR a forward view of capability.",
    color: "text-accent-300",
    ring: "group-hover:ring-accent-400/40",
  },
];

export default function Pipeline() {
  return (
    <section id="pipeline" className="relative py-24 sm:py-32">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <SectionHeading
          eyebrow="Core intelligence loop"
          title="Nine stages from hidden talent to verified skill"
          description="Deterministic scoring keeps the rank reproducible and auditable; the LLM is reserved for extraction, review and narration — it never invents the rank."
        />
        <div className="mt-16 grid gap-5 sm:grid-cols-2 lg:grid-cols-4">
          {STEPS.map((step, index) => (
            <Reveal key={step.title} delay={index * 70}>
              <div
                className={`group relative h-full rounded-2xl border border-white/8 bg-ink-900/50 p-5 ring-1 ring-transparent transition-all duration-300 hover:-translate-y-1.5 hover:border-white/15 hover:bg-ink-800/60 ${step.ring}`}
              >
                <span className="font-display absolute right-4 top-3 text-4xl font-bold text-white/5 transition-colors group-hover:text-white/10">
                  {String(index + 1).padStart(2, "0")}
                </span>
                <span className="grid size-11 place-items-center rounded-xl border border-white/10 bg-ink-800">
                  <Icon name={step.icon} className={`size-5 ${step.color}`} />
                </span>
                <h3 className="mt-4 text-sm font-semibold text-white">{step.title}</h3>
                <p className="mt-2 text-[13px] leading-relaxed text-slate-400">{step.text}</p>
              </div>
            </Reveal>
          ))}
        </div>
      </div>
    </section>
  );
}
