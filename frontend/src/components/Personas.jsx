import Icon from "./Icon.jsx";
import Reveal from "./Reveal.jsx";
import { SectionHeading } from "./Pipeline.jsx";

const PERSONAS = [
  {
    icon: "target",
    accent: "from-brand-500/20 to-transparent text-brand-300 border-brand-400/30",
    name: "Manager",
    goal: "Fill an open role from inside — before posting externally.",
    points: [
      "Vacant Roles dashboard: candidate counts already computed",
      "Upload a JD → AI-parsed criteria you edit before activation",
      "Weight tuner with presets and live what-if re-ranking",
      "Hidden / visible roles with database-level RLS enforcement",
    ],
  },
  {
    icon: "compass",
    accent: "from-accent-500/20 to-transparent text-accent-300 border-accent-400/30",
    name: "Employee",
    goal: "See where you could go next — and exactly what's missing.",
    points: [
      "Opportunities feed with your own match %, gaps and roadmap",
      "Express interest — confidential by default",
      "Personalised, time-boxed learning roadmaps",
      "Skills verified through projects, not self-reporting",
    ],
  },
  {
    icon: "barChart",
    accent: "from-violet-500/20 to-transparent text-violet-300 border-violet-400/30",
    name: "HR / Admin",
    goal: "Plan workforce capability instead of reacting to vacancies.",
    points: [
      "Skill heatmaps and demand forecasts by initiative",
      "Reskilling pools from adjacent-skill analysis",
      "Fairness dashboard and adverse-impact checks",
      "Full audit log: every visibility change and decision",
    ],
  },
];

export default function Personas() {
  return (
    <section id="personas" className="relative py-24 sm:py-32">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <SectionHeading
          eyebrow="Three portals, one platform"
          title="Built for the whole mobility loop"
          description="AI recommends; humans decide. Every persona stays in the loop with transparent, auditable tools."
        />
        <div className="mt-16 grid gap-6 lg:grid-cols-3">
          {PERSONAS.map((persona, index) => (
            <Reveal key={persona.name} delay={index * 100}>
              <div className="group relative h-full overflow-hidden rounded-3xl border border-white/10 bg-ink-900/50 p-7 transition-all duration-300 hover:-translate-y-2 hover:border-white/20">
                <div className={`pointer-events-none absolute inset-x-0 top-0 h-40 bg-gradient-to-b ${persona.accent.split(" ").slice(0, 2).join(" ")} opacity-60`} />
                <div className="relative">
                  <span className={`grid size-12 place-items-center rounded-2xl border bg-ink-900 ${persona.accent.split(" ").slice(2).join(" ")}`}>
                    <Icon name={persona.icon} className="size-6" />
                  </span>
                  <h3 className="font-display mt-5 text-xl font-bold text-white">{persona.name}</h3>
                  <p className="mt-1.5 text-sm font-medium text-slate-400">{persona.goal}</p>
                  <ul className="mt-6 space-y-3">
                    {persona.points.map((point) => (
                      <li key={point} className="flex items-start gap-2.5 text-[13px] leading-relaxed text-slate-300">
                        <Icon name="check" className="mt-0.5 size-4 shrink-0 text-emerald-400" />
                        {point}
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            </Reveal>
          ))}
        </div>
      </div>
    </section>
  );
}
