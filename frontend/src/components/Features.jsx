import Icon from "./Icon.jsx";
import Reveal from "./Reveal.jsx";
import { SectionHeading } from "./Pipeline.jsx";

const FEATURES = [
  {
    icon: "zap",
    title: "Always-on candidate discovery",
    text: "Open the dashboard and candidates are already there — event-driven, versioned and cached with stale-while-revalidate.",
    span: "lg:col-span-2",
    highlight: true,
  },
  {
    icon: "lock",
    title: "Hidden roles, guaranteed",
    text: "Row-Level Security keeps confidential backfills invisible to employees — enforced in the database, not just the UI.",
  },
  {
    icon: "gitFork",
    title: "Skill ontology with relatedness",
    text: "Curated graph edges (Azure ↔ AWS at 0.8) power real transferable-skill discovery, not keyword matching.",
  },
  {
    icon: "eye",
    title: "Explanations with receipts",
    text: "Every strength, gap and risk cites a verifiable evidence record. Claims without receipts are stripped.",
    span: "lg:col-span-2",
    highlight: true,
  },
  {
    icon: "graduation",
    title: "Verification ladder",
    text: "Course → quiz → hands-on project → certification. Each rung lifts skill confidence with linked evidence.",
  },
  {
    icon: "shieldCheck",
    title: "Fairness by design",
    text: "No protected attributes in features, prompts or embeddings — plus adverse-impact audits for HR.",
  },
];

export default function Features() {
  return (
    <section id="features" className="relative py-24 sm:py-32">
      <div className="pointer-events-none absolute left-0 top-1/3 h-80 w-80 rounded-full bg-brand-600/10 blur-[110px]" />
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <SectionHeading
          eyebrow="What makes it different"
          title="Details that turn an AI demo into an enterprise platform"
        />
        <div className="mt-16 grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
          {FEATURES.map((feature, index) => (
            <Reveal key={feature.title} delay={index * 80} className={feature.span || ""}>
              <div
                className={`group h-full rounded-3xl border p-6 transition-all duration-300 hover:-translate-y-1.5 ${
                  feature.highlight
                    ? "border-brand-400/25 bg-gradient-to-br from-brand-500/15 via-ink-900/70 to-ink-900/70 hover:border-brand-300/40"
                    : "border-white/10 bg-ink-900/50 hover:border-white/20"
                }`}
              >
                <span
                  className={`grid size-11 place-items-center rounded-xl border transition-colors ${
                    feature.highlight
                      ? "border-brand-400/30 bg-brand-500/15 text-brand-300"
                      : "border-white/10 bg-ink-800 text-accent-300"
                  }`}
                >
                  <Icon name={feature.icon} className="size-5" />
                </span>
                <h3 className="mt-4 text-base font-semibold text-white">{feature.title}</h3>
                <p className="mt-2 text-[13px] leading-relaxed text-slate-400">{feature.text}</p>
              </div>
            </Reveal>
          ))}
        </div>
      </div>
    </section>
  );
}
