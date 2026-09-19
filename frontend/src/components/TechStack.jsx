import Reveal from "./Reveal.jsx";
import { SectionHeading } from "./Pipeline.jsx";

const STACK = [
  { name: "React 19", tone: "text-cyan-300 border-cyan-400/30 bg-cyan-500/10" },
  { name: "Tailwind CSS", tone: "text-sky-300 border-sky-400/30 bg-sky-500/10" },
  { name: "Vite", tone: "text-violet-300 border-violet-400/30 bg-violet-500/10" },
  { name: "React Query", tone: "text-rose-300 border-rose-400/30 bg-rose-500/10" },
  { name: "Flask", tone: "text-amber-300 border-amber-400/30 bg-amber-500/10" },
  { name: "PostgreSQL + pgvector", tone: "text-blue-300 border-blue-400/30 bg-blue-500/10" },
  { name: "MongoDB", tone: "text-emerald-300 border-emerald-400/30 bg-emerald-500/10" },
  { name: "Redis", tone: "text-red-300 border-red-400/30 bg-red-500/10" },
  { name: "Celery", tone: "text-green-300 border-green-400/30 bg-green-500/10" },
  { name: "LangGraph", tone: "text-lime-300 border-lime-400/30 bg-lime-500/10" },
  { name: "LangChain", tone: "text-teal-300 border-teal-400/30 bg-teal-500/10" },
  { name: "GPT-OSS-120B", tone: "text-indigo-300 border-indigo-400/30 bg-indigo-500/10" },
  { name: "BGE-base", tone: "text-fuchsia-300 border-fuchsia-400/30 bg-fuchsia-500/10" },
  { name: "Sentence-BERT", tone: "text-pink-300 border-pink-400/30 bg-pink-500/10" },
  { name: "OAuth / JWT", tone: "text-orange-300 border-orange-400/30 bg-orange-500/10" },
];

function MarqueeRow({ items, reverse = false }) {
  const doubled = [...items, ...items];
  return (
    <div className="mask-fade-x overflow-hidden">
      <div
        className="flex w-max items-center gap-3 py-1.5"
        style={{ animation: `marquee 38s linear infinite ${reverse ? "reverse" : ""}` }}
      >
        {doubled.map((item, index) => (
          <span
            key={`${item.name}-${index}`}
            className={`whitespace-nowrap rounded-xl border px-4 py-2.5 text-sm font-semibold ${item.tone}`}
          >
            {item.name}
          </span>
        ))}
      </div>
    </div>
  );
}

export default function TechStack() {
  return (
    <section id="stack" className="relative py-24 sm:py-32">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <SectionHeading
          eyebrow="Under the hood"
          title="A modern, production-shaped stack"
          description="Every component of the requested architecture — wired with sensible defaults and ready for the real thing."
        />
      </div>
      <div className="mt-14 space-y-3">
        <MarqueeRow items={STACK.slice(0, 8)} />
        <MarqueeRow items={STACK.slice(7)} reverse />
      </div>

      <div className="mx-auto mt-16 max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="grid gap-4 sm:grid-cols-3">
          {[
            { label: "Frontend", value: "React 19 · Tailwind · Vite · React Query" },
            { label: "Backend & agents", value: "Flask · Celery · LangGraph · GPT-OSS-120B" },
            { label: "Data layer", value: "PostgreSQL/pgvector · MongoDB · Redis" },
          ].map((row, index) => (
            <Reveal key={row.label} delay={index * 90}>
              <div className="rounded-2xl border border-white/10 bg-ink-900/50 p-5">
                <p className="text-[11px] font-semibold uppercase tracking-widest text-slate-500">{row.label}</p>
                <p className="mt-2 text-sm font-medium leading-relaxed text-slate-200">{row.value}</p>
              </div>
            </Reveal>
          ))}
        </div>
      </div>
    </section>
  );
}
