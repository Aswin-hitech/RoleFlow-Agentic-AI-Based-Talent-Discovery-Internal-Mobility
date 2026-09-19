const NODES = [
  { id: "python", label: "Python", x: 50, y: 14 },
  { id: "dataproc", label: "Data Processing", x: 18, y: 42 },
  { id: "sql", label: "SQL", x: 50, y: 46 },
  { id: "react", label: "React", x: 84, y: 40 },
  { id: "dataeng", label: "Data Eng", x: 26, y: 82 },
  { id: "ml", label: "ML Engineer", x: 74, y: 80 },
  { id: "fullstack", label: "Full Stack", x: 50, y: 68 },
];

const EDGES = [
  ["python", "dataproc", 0.9],
  ["dataproc", "ml", 0.85],
  ["python", "sql", 0.8],
  ["sql", "dataeng", 0.9],
  ["dataeng", "ml", 0.75],
  ["react", "fullstack", 0.88],
  ["python", "fullstack", 0.82],
  ["sql", "fullstack", 0.7],
];

function nodeById(id) {
  return NODES.find((node) => node.id === id);
}

export default function SkillGraphVisual() {
  return (
    <div className="relative">
      <div className="card-glow glass relative overflow-hidden rounded-3xl p-1 shadow-2xl shadow-brand-950/50">
        <div className="bg-grid rounded-[calc(1.5rem-4px)] p-5 sm:p-7">
          <div className="mb-4 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="size-3 rounded-full bg-rose-400/80" />
              <span className="size-3 rounded-full bg-amber-400/80" />
              <span className="size-3 rounded-full bg-emerald-400/80" />
            </div>
            <span className="rounded-full border border-brand-400/30 bg-brand-500/10 px-3 py-1 text-[11px] font-semibold tracking-wide text-brand-300">
              SKILL ONTOLOGY · LIVE
            </span>
          </div>

          <svg viewBox="0 0 100 100" className="h-auto w-full" role="img" aria-label="Skill ontology graph">
            <defs>
              <linearGradient id="edge-grad" x1="0" y1="0" x2="1" y2="1">
                <stop offset="0%" stopColor="#818cf8" stopOpacity="0.7" />
                <stop offset="100%" stopColor="#22d3ee" stopOpacity="0.5" />
              </linearGradient>
            </defs>
            {EDGES.map(([from, to, weight], index) => {
              const a = nodeById(from);
              const b = nodeById(to);
              return (
                <g key={`${from}-${to}`}>
                  <line
                    x1={a.x}
                    y1={a.y}
                    x2={b.x}
                    y2={b.y}
                    stroke="url(#edge-grad)"
                    strokeWidth={weight * 0.5}
                    strokeDasharray="1.2 1.6"
                    className="animate-blink"
                    style={{ animationDelay: `${index * 0.35}s` }}
                  />
                  <text
                    x={(a.x + b.x) / 2}
                    y={(a.y + b.y) / 2 - 1}
                    textAnchor="middle"
                    className="fill-slate-500"
                    fontSize="2.6"
                    fontFamily="Inter, sans-serif"
                  >
                    {weight.toFixed(1)}
                  </text>
                </g>
              );
            })}
            {NODES.map((node, index) => (
              <g key={node.id} className="animate-float" style={{ animationDelay: `${index * 0.8}s`, animationDuration: `${7 + index}s` }}>
                <circle cx={node.x} cy={node.y} r="6.4" fill="#101627" stroke="#818cf8" strokeWidth="0.5" />
                <circle cx={node.x} cy={node.y} r="2.6" fill={index % 2 ? "#22d3ee" : "#818cf8"} />
                <text
                  x={node.x}
                  y={node.y - 8.4}
                  textAnchor="middle"
                  className="fill-slate-300"
                  fontSize="3.4"
                  fontWeight="600"
                  fontFamily="Space Grotesk, Inter, sans-serif"
                >
                  {node.label}
                </text>
              </g>
            ))}
          </svg>

          <div className="mt-4 grid grid-cols-3 gap-3">
            {[
              { label: "Employees indexed", value: "10,000" },
              { label: "Skills mapped", value: "1,842" },
              { label: "Avg. shortlist", value: "< 8 s" },
            ].map((stat) => (
              <div key={stat.label} className="rounded-2xl border border-white/5 bg-ink-900/60 px-3 py-2.5 text-center">
                <p className="font-display text-sm font-bold text-white sm:text-base">{stat.value}</p>
                <p className="mt-0.5 text-[10px] font-medium uppercase tracking-wider text-slate-500">{stat.label}</p>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="glass animate-float absolute -left-6 top-8 hidden rounded-2xl px-4 py-3 shadow-xl sm:block">
        <p className="text-[10px] font-semibold uppercase tracking-wider text-slate-400">Transferable talent</p>
        <p className="mt-1 text-sm font-semibold text-white">
          Python <span className="text-accent-400">→</span> ML <span className="text-brand-300">0.85 related</span>
        </p>
      </div>
      <div className="glass animate-float-slow absolute -right-5 bottom-16 hidden rounded-2xl px-4 py-3 shadow-xl sm:block">
        <p className="text-[10px] font-semibold uppercase tracking-wider text-slate-400">Top match found</p>
        <p className="mt-1 text-sm font-semibold text-white">
          EMP-1024 · <span className="text-emerald-300">92% fit · 81% ready</span>
        </p>
      </div>
    </div>
  );
}
