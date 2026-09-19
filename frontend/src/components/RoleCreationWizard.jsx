import { useState } from "react";
import Icon from "./Icon.jsx";
import { api } from "../lib/api";

export default function RoleCreationWizard({ isOpen, onClose, onCreated }) {
  const [step, setStep] = useState(1);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  // Form State
  const [title, setTitle] = useState("ML Engineer");
  const [department, setDepartment] = useState("Data & AI");
  const [jdText, setJdText] = useState(
    `We are seeking a Machine Learning Engineer to design, deploy, and monitor scalable machine learning models and feature pipelines.
Requirements:
- 2+ years of professional experience in Python and Machine Learning
- Mandatory skills: Python, Machine Learning, SQL, Data Pipelines
- Preferred skills: MLOps, Model Deployment, System Design
- Experience training predictive models and deploying to production APIs
- Nice to have: TensorFlow Developer or Cloud ML certification`
  );
  const [domain, setDomain] = useState("AI/ML");
  const [minExp, setMinExp] = useState(2.0);
  const [mandatorySkills, setMandatorySkills] = useState(["Python", "Machine Learning", "SQL", "Data Pipelines"]);
  const [preferredSkills, setPreferredSkills] = useState(["MLOps", "Model Deployment", "System Design"]);
  const [headcount, setHeadcount] = useState(2);
  const [visibility, setVisibility] = useState("visible"); // visible | hidden
  const [newSkillInput, setNewSkillInput] = useState("");
  const [crawlingMarket, setCrawlingMarket] = useState(false);
  const [crawlStats, setCrawlStats] = useState(null);

  if (!isOpen) return null;

  async function handleMarketCrawl() {
    setCrawlingMarket(true);
    setError("");
    try {
      const res = await api("/crawler/market-skills", {
        method: "POST",
        body: { domain: domain || department, role_title: title, max_workers: 4 },
      });
      setCrawlStats(res);
      if (res.mandatory_skills?.length) {
        setMandatorySkills((prev) => Array.from(new Set([...prev, ...res.mandatory_skills.slice(0, 3)])));
      }
      if (res.preferred_skills?.length) {
        setPreferredSkills((prev) => Array.from(new Set([...prev, ...res.preferred_skills.slice(0, 3)])));
      }
    } catch (err) {
      setError(err.message || "Market skill crawl failed.");
    } finally {
      setCrawlingMarket(false);
    }
  }

  async function handleExtractAI() {
    if (!jdText.trim()) {
      setError("Please paste or write a Job Description first.");
      return;
    }
    setError("");
    setLoading(true);
    try {
      const res = await api("/roles/parse-jd", {
        method: "POST",
        body: { jd_text: jdText, title, department },
      });
      const parsed = res.parsed || {};
      if (parsed.title) setTitle(parsed.title);
      if (parsed.department) setDepartment(parsed.department);
      if (parsed.domain) setDomain(parsed.domain);
      if (parsed.minimum_experience) setMinExp(parsed.minimum_experience);
      if (parsed.mandatory_skills?.length) setMandatorySkills(parsed.mandatory_skills);
      if (parsed.preferred_skills?.length) setPreferredSkills(parsed.preferred_skills);
      setStep(4); // Advance to review requirements
    } catch (err) {
      setError(err.message || "AI extraction failed. You can fill requirements manually.");
      setStep(4);
    } finally {
      setLoading(false);
    }
  }

  async function handleFinalSubmit() {
    setError("");
    setLoading(true);
    try {
      const rolePayload = {
        title,
        department,
        domain,
        jd_text: jdText,
        description: jdText.slice(0, 200) + "...",
        minimum_experience: Number(minExp),
        mandatory_skills: mandatorySkills,
        preferred_skills: preferredSkills,
        headcount: Number(headcount),
        visibility,
      };

      const res = await api("/manager/roles", {
        method: "POST",
        body: rolePayload,
      });

      if (onCreated) {
        onCreated(res.role, res.match_run_id);
      }
      onClose();
    } catch (err) {
      setError(err.message || "Failed to create role.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-ink-950/80 p-4 backdrop-blur-md">
      <div className="relative w-full max-w-2xl overflow-hidden rounded-3xl border border-white/10 bg-ink-900 shadow-2xl">
        {/* Wizard Header */}
        <div className="flex items-center justify-between border-b border-white/10 px-6 py-5">
          <div>
            <div className="flex items-center gap-2">
              <span className="rounded-full bg-brand-500/20 px-2.5 py-0.5 text-xs font-semibold text-brand-300">
                Step {step} of 7
              </span>
              <h2 className="font-display text-lg font-bold text-white">Create New Role</h2>
            </div>
            <p className="mt-0.5 text-xs text-slate-400">
              {step === 1 && "Basic role details"}
              {step === 2 && "Paste or input Job Description"}
              {step === 3 && "Role Intelligence Agent extraction"}
              {step === 4 && "Review & edit requirements"}
              {step === 5 && "Target headcount"}
              {step === 6 && "Set role visibility"}
              {step === 7 && "Confirm and launch discovery"}
            </p>
          </div>
          <button
            onClick={onClose}
            className="grid size-8 place-items-center rounded-lg border border-white/10 text-slate-400 hover:text-white"
          >
            ✕
          </button>
        </div>

        {/* Wizard Progress Bar */}
        <div className="h-1 w-full bg-ink-800">
          <div
            className="h-full bg-gradient-to-r from-brand-500 to-accent-400 transition-all duration-300"
            style={{ width: `${(step / 7) * 100}%` }}
          />
        </div>

        {/* Body Steps */}
        <div className="max-h-[65vh] overflow-y-auto p-6 space-y-4">
          {error && (
            <p className="rounded-xl border border-rose-400/30 bg-rose-500/10 px-4 py-3 text-xs text-rose-300">
              {error}
            </p>
          )}

          {step === 1 && (
            <div className="space-y-4">
              <div>
                <label className="mb-1 block text-xs font-semibold text-slate-300">Role Title</label>
                <input
                  type="text"
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  className="w-full rounded-xl border border-white/10 bg-ink-950 px-4 py-2.5 text-sm text-white outline-none focus:border-brand-400"
                  placeholder="e.g. ML Engineer, Data Scientist"
                />
              </div>
              <div>
                <label className="mb-1 block text-xs font-semibold text-slate-300">Department</label>
                <input
                  type="text"
                  value={department}
                  onChange={(e) => setDepartment(e.target.value)}
                  className="w-full rounded-xl border border-white/10 bg-ink-950 px-4 py-2.5 text-sm text-white outline-none focus:border-brand-400"
                  placeholder="e.g. Data & AI, Engineering, Product"
                />
              </div>
            </div>
          )}

          {step === 2 && (
            <div className="space-y-3">
              <label className="mb-1 block text-xs font-semibold text-slate-300">
                Paste Job Description (JD)
              </label>
              <textarea
                rows={7}
                value={jdText}
                onChange={(e) => setJdText(e.target.value)}
                className="w-full rounded-xl border border-white/10 bg-ink-950 p-4 text-xs font-mono text-slate-200 outline-none focus:border-brand-400"
                placeholder="Paste the raw job description here..."
              />
              <p className="text-[11px] text-slate-400">
                The Role Intelligence Agent will extract mandatory skills, preferred skills, minimum experience, and domain.
              </p>
            </div>
          )}

          {step === 3 && (
            <div className="py-8 text-center space-y-4">
              <div className="mx-auto grid size-16 place-items-center rounded-2xl border border-brand-400/40 bg-brand-500/10 text-brand-300">
                <Icon name="sparkles" className="size-8 animate-pulse" />
              </div>
              <div>
                <h3 className="font-display text-base font-bold text-white">Role Intelligence Agent</h3>
                <p className="mx-auto mt-1 max-w-md text-xs text-slate-400">
                  Analyze JD structure and extract weighted requirements for {title}.
                </p>
              </div>
              <button
                onClick={handleExtractAI}
                disabled={loading}
                className="rounded-xl bg-brand-600 px-6 py-2.5 text-xs font-semibold text-white shadow-lg transition hover:bg-brand-500 disabled:opacity-50"
              >
                {loading ? "Agent Analyzing JD…" : "Run AI Extraction →"}
              </button>
            </div>
          )}

          {step === 4 && (
            <div className="space-y-4">
              <div className="rounded-xl border border-brand-400/20 bg-brand-500/5 p-3">
                <p className="text-[11px] font-semibold text-brand-300">
                  ✓ AI parsed criteria — Review and fine-tune below before matching.
                </p>
              </div>

              {/* Multi-Threaded Market Intelligence Crawl Box */}
              <div className="rounded-xl border border-accent-400/20 bg-accent-500/5 p-3.5 space-y-2">
                <div className="flex items-center justify-between">
                  <div>
                    <span className="inline-flex items-center gap-1.5 text-xs font-semibold text-accent-300">
                      🌐 Multi-Threaded Market Skill Crawler
                    </span>
                    <p className="text-[11px] text-slate-400">
                      Spawns parallel worker threads to harvest emerging industry benchmarks for {domain || "this domain"}.
                    </p>
                  </div>
                  <button
                    type="button"
                    onClick={handleMarketCrawl}
                    disabled={crawlingMarket}
                    className="inline-flex items-center gap-1.5 rounded-lg border border-accent-400/40 bg-accent-500/10 px-3 py-1.5 text-xs font-medium text-accent-200 hover:bg-accent-500/20 transition disabled:opacity-50"
                  >
                    {crawlingMarket ? "Crawling Market Threads…" : "Run Live Crawl ⚡"}
                  </button>
                </div>
                {crawlStats && (
                  <div className="rounded-lg bg-ink-950 p-2 text-[10px] text-accent-200 border border-accent-400/20">
                    ✓ Crawled across {crawlStats.threads_spawned} concurrent worker threads in {crawlStats.elapsed_ms}ms. Enriched skill requirements!
                  </div>
                )}
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="mb-1 block text-[11px] font-semibold text-slate-400">Domain</label>
                  <input
                    type="text"
                    value={domain}
                    onChange={(e) => setDomain(e.target.value)}
                    className="w-full rounded-lg border border-white/10 bg-ink-950 px-3 py-2 text-xs text-white"
                  />
                </div>
                <div>
                  <label className="mb-1 block text-[11px] font-semibold text-slate-400">Min Experience (Years)</label>
                  <input
                    type="number"
                    step="0.5"
                    value={minExp}
                    onChange={(e) => setMinExp(e.target.value)}
                    className="w-full rounded-lg border border-white/10 bg-ink-950 px-3 py-2 text-xs text-white"
                  />
                </div>
              </div>

              <div>
                <label className="mb-1.5 block text-xs font-semibold text-slate-300">Mandatory Skills (30% Fit weight)</label>
                <div className="flex flex-wrap gap-1.5">
                  {mandatorySkills.map((s) => (
                    <span
                      key={s}
                      className="inline-flex items-center gap-1.5 rounded-lg border border-brand-400/30 bg-brand-500/10 px-2.5 py-1 text-xs text-brand-200"
                    >
                      {s}
                      <button
                        type="button"
                        onClick={() => setMandatorySkills(mandatorySkills.filter((x) => x !== s))}
                        className="text-slate-400 hover:text-rose-400"
                      >
                        ×
                      </button>
                    </span>
                  ))}
                </div>
              </div>

              <div>
                <label className="mb-1.5 block text-xs font-semibold text-slate-300">Preferred Skills</label>
                <div className="flex flex-wrap gap-1.5">
                  {preferredSkills.map((s) => (
                    <span
                      key={s}
                      className="inline-flex items-center gap-1.5 rounded-lg border border-white/10 bg-ink-800 px-2.5 py-1 text-xs text-slate-300"
                    >
                      {s}
                      <button
                        type="button"
                        onClick={() => setPreferredSkills(preferredSkills.filter((x) => x !== s))}
                        className="text-slate-400 hover:text-rose-400"
                      >
                        ×
                      </button>
                    </span>
                  ))}
                </div>
              </div>

              <div className="flex gap-2">
                <input
                  type="text"
                  value={newSkillInput}
                  onChange={(e) => setNewSkillInput(e.target.value)}
                  placeholder="Add another requirement..."
                  className="flex-1 rounded-lg border border-white/10 bg-ink-950 px-3 py-1.5 text-xs text-white"
                />
                <button
                  type="button"
                  onClick={() => {
                    if (newSkillInput.trim()) {
                      setMandatorySkills([...mandatorySkills, newSkillInput.trim()]);
                      setNewSkillInput("");
                    }
                  }}
                  className="rounded-lg border border-white/10 bg-white/5 px-3 py-1.5 text-xs text-slate-300 hover:text-white"
                >
                  + Add Mandatory
                </button>
              </div>
            </div>
          )}

          {step === 5 && (
            <div className="space-y-4">
              <label className="mb-1 block text-xs font-semibold text-slate-300">Vacancies / Headcount</label>
              <input
                type="number"
                min="1"
                max="20"
                value={headcount}
                onChange={(e) => setHeadcount(e.target.value)}
                className="w-full rounded-xl border border-white/10 bg-ink-950 px-4 py-3 text-lg font-bold text-white outline-none focus:border-brand-400"
              />
              <p className="text-xs text-slate-400">
                Number of vacancies available to fill through internal mobility.
              </p>
            </div>
          )}

          {step === 6 && (
            <div className="space-y-4">
              <label className="mb-1 block text-xs font-semibold text-slate-300">Role Visibility (§18)</label>
              <div className="grid gap-3 sm:grid-cols-2">
                <div
                  onClick={() => setVisibility("visible")}
                  className={`cursor-pointer rounded-2xl border p-4 transition ${
                    visibility === "visible"
                      ? "border-brand-400 bg-brand-500/10"
                      : "border-white/10 bg-ink-950 hover:border-white/20"
                  }`}
                >
                  <div className="flex items-center gap-2">
                    <Icon name="eye" className="size-4 text-brand-300" />
                    <span className="text-sm font-semibold text-white">Visible</span>
                  </div>
                  <p className="mt-2 text-xs text-slate-400">
                    Shown to employees in internal opportunity feeds. Eligible employees can view matches and express interest.
                  </p>
                </div>

                <div
                  onClick={() => setVisibility("hidden")}
                  className={`cursor-pointer rounded-2xl border p-4 transition ${
                    visibility === "hidden"
                      ? "border-amber-400 bg-amber-500/10"
                      : "border-white/10 bg-ink-950 hover:border-white/20"
                  }`}
                >
                  <div className="flex items-center gap-2">
                    <Icon name="lock" className="size-4 text-amber-300" />
                    <span className="text-sm font-semibold text-white">Hidden</span>
                  </div>
                  <p className="mt-2 text-xs text-slate-400">
                    Confidential internal search. Visible only to managers and HR; never appears in employee portals.
                  </p>
                </div>
              </div>
            </div>
          )}

          {step === 7 && (
            <div className="space-y-4">
              <div className="rounded-2xl border border-white/10 bg-ink-950 p-4 space-y-2">
                <h4 className="font-display text-base font-bold text-white">{title}</h4>
                <p className="text-xs text-slate-400">{department} · {domain} · {headcount} vacancies · {visibility}</p>
                <div className="pt-2 border-t border-white/5 text-xs text-slate-300">
                  <span className="font-semibold text-brand-300">Mandatory Skills: </span>
                  {mandatorySkills.join(", ")}
                </div>
              </div>
              <p className="text-xs text-slate-400">
                Clicking <span className="text-white font-semibold">"Create Role & Launch Discovery"</span> will store the role in PostgreSQL and automatically queue the Celery + LangGraph discovery pipeline.
              </p>
            </div>
          )}
        </div>

        {/* Wizard Footer Controls */}
        <div className="flex items-center justify-between border-t border-white/10 px-6 py-4">
          <button
            type="button"
            onClick={() => setStep(Math.max(1, step - 1))}
            disabled={step === 1}
            className="rounded-lg border border-white/10 px-4 py-2 text-xs font-semibold text-slate-300 hover:text-white disabled:opacity-30"
          >
            Back
          </button>

          {step < 7 ? (
            <button
              type="button"
              onClick={() => {
                if (step === 2) {
                  setStep(3);
                } else {
                  setStep(step + 1);
                }
              }}
              className="rounded-lg bg-brand-600 px-5 py-2 text-xs font-semibold text-white shadow transition hover:bg-brand-500"
            >
              Continue →
            </button>
          ) : (
            <button
              type="button"
              onClick={handleFinalSubmit}
              disabled={loading}
              className="rounded-lg bg-gradient-to-r from-brand-600 to-accent-500 px-6 py-2.5 text-xs font-semibold text-white shadow-lg transition hover:opacity-90 disabled:opacity-50"
            >
              {loading ? "Creating & Queuing Discovery…" : "Create Role & Launch Discovery"}
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
