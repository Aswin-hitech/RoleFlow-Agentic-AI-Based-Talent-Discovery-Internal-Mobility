import { useState } from "react";
import { Link } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import Icon, { Logo } from "../components/Icon.jsx";
import { api } from "../lib/api";
import { useAuth } from "../hooks/useAuth.jsx";

export default function EmployeePortal() {
  const { user, logout } = useAuth();
  const queryClient = useQueryClient();
  const [activeTab, setActiveTab] = useState("opportunities"); // opportunities | profile | learning | preferences
  const [notice, setNotice] = useState("");
  const [prefRole1, setPrefRole1] = useState("");
  const [prefRole2, setPrefRole2] = useState("");

  // Query employee profile
  const profileQuery = useQuery({
    queryKey: ["employee-profile"],
    queryFn: () => api("/me/profile"),
  });

  // Query opportunities (strictly visible roles per §25)
  const oppsQuery = useQuery({
    queryKey: ["employee-opportunities"],
    queryFn: () => api("/me/opportunities"),
  });

  // Query learning roadmap
  const learningQuery = useQuery({
    queryKey: ["employee-learning"],
    queryFn: () => api("/me/learning"),
  });

  // Accept mutation (§26, §30)
  const acceptMutation = useMutation({
    mutationFn: (roleId) => api(`/me/opportunities/${roleId}/accept`, { method: "POST" }),
    onSuccess: (data) => {
      setNotice(data.message || "Opportunity accepted! Forwarded to HR for governance approval.");
      queryClient.invalidateQueries({ queryKey: ["employee-opportunities"] });
    },
    onError: (err) => setNotice(err.message || "Failed to accept opportunity."),
  });

  // Decline mutation (§28)
  const declineMutation = useMutation({
    mutationFn: (roleId) => api(`/me/opportunities/${roleId}/decline`, { method: "POST" }),
    onSuccess: (data) => {
      setNotice(data.message || "Opportunity declined. The role remains vacant for another candidate.");
      queryClient.invalidateQueries({ queryKey: ["employee-opportunities"] });
    },
    onError: (err) => setNotice(err.message || "Failed to decline opportunity."),
  });

  // Complete course mutation (§54)
  const completeLearningMutation = useMutation({
    mutationFn: ({ courseId, skillName }) =>
      api(`/me/learning/${courseId}/complete`, { method: "POST", body: { skill_name: skillName } }),
    onSuccess: (data) => {
      setNotice(data.message || "Course completed! Skill marked as verified on your profile.");
      queryClient.invalidateQueries({ queryKey: ["employee-profile"] });
      queryClient.invalidateQueries({ queryKey: ["employee-opportunities"] });
    },
  });

  // Save multiple role preference mutation (§27)
  const savePreferencesMutation = useMutation({
    mutationFn: (prefs) => api("/me/role-preferences", { method: "PUT", body: { preferences: prefs } }),
    onSuccess: (data) => {
      setNotice(data.message || "Preferences saved successfully.");
      queryClient.invalidateQueries({ queryKey: ["employee-opportunities"] });
    },
  });

  const profile = profileQuery.data?.profile || {};
  const opportunities = oppsQuery.data?.opportunities || [];
  const learningItems = learningQuery.data?.roadmap?.items || [];

  // Check if multiple roles exist for preference resolution (§27)
  const hasMultipleRoles = opportunities.length > 1;

  function handleSavePreferences() {
    if (!prefRole1) {
      setNotice("Please select at least your 1st preference.");
      return;
    }
    const prefs = [{ role_id: prefRole1, rank: 1 }];
    if (prefRole2 && prefRole2 !== prefRole1) {
      prefs.push({ role_id: prefRole2, rank: 2 });
    }
    savePreferencesMutation.mutate(prefs);
  }

  return (
    <div className="min-h-screen bg-ink-950 text-slate-100">
      {/* Navbar */}
      <header className="sticky top-0 z-40 border-b border-white/10 bg-ink-950/85 backdrop-blur-xl">
        <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-4 sm:px-6 lg:px-8">
          <Link to="/" className="flex items-center gap-3">
            <Logo className="size-8" />
            <span className="font-display text-base font-bold tracking-tight text-white">
              Role<span className="text-gradient">Flow</span>
            </span>
            <span className="ml-2 rounded-full border border-white/10 bg-white/5 px-2.5 py-0.5 text-[11px] font-semibold text-accent-300">
              EMPLOYEE PORTAL
            </span>
          </Link>

          <div className="flex items-center gap-3">
            <span className="hidden text-xs text-slate-400 sm:block">{profile.full_name || user?.name}</span>
            <Link to="/" className="rounded-lg border border-white/10 px-3.5 py-1.5 text-xs font-semibold text-slate-300 hover:text-white">
              Home
            </Link>
            <button
              onClick={logout}
              className="grid size-9 place-items-center rounded-lg border border-white/10 text-slate-400 hover:text-rose-300"
              title="Sign out"
            >
              <Icon name="logout" className="size-4" />
            </button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8 space-y-8">
        {notice && (
          <div className="flex items-center justify-between rounded-xl border border-brand-400/30 bg-brand-500/10 p-4 text-xs font-medium text-brand-200">
            <span>{notice}</span>
            <button onClick={() => setNotice("")} className="text-slate-400 hover:text-white">✕</button>
          </div>
        )}

        {/* Employee Summary Card */}
        <div className="flex flex-wrap items-center justify-between gap-4 rounded-3xl border border-white/10 bg-ink-900/60 p-6 sm:p-8">
          <div>
            <div className="flex items-center gap-2">
              <span className="rounded-full bg-accent-500/10 px-2.5 py-0.5 text-[10px] font-semibold text-accent-300">
                {profile.id || "EMP-1024"}
              </span>
              <h1 className="font-display text-2xl font-bold text-white">{profile.full_name || user?.name}</h1>
            </div>
            <p className="mt-1 text-sm text-slate-400">
              {profile.current_role} · {profile.department} · {profile.experience_years} yrs experience
            </p>
          </div>

          {/* Transfer Willingness & Notice */}
          <div className="flex items-center gap-4 text-xs">
            <div className="rounded-2xl border border-white/10 bg-ink-950/60 px-4 py-2.5">
              <span className="text-slate-400">Transfer Status: </span>
              <strong className="text-emerald-300 font-semibold">Open to Mobility</strong>
            </div>
            <div className="rounded-2xl border border-white/10 bg-ink-950/60 px-4 py-2.5">
              <span className="text-slate-400">Availability: </span>
              <strong className="text-white font-semibold">{profile.availability_days || 30} days</strong>
            </div>
          </div>
        </div>

        {/* Multiple Role Conflict Resolution Banner (§27) */}
        {hasMultipleRoles && (
          <div className="rounded-3xl border border-accent-400/30 bg-accent-500/10 p-6">
            <div className="flex items-start justify-between gap-4">
              <div>
                <h3 className="font-display text-base font-bold text-white flex items-center gap-2">
                  <Icon name="sparkles" className="size-4 text-accent-300" />
                  Multiple Role Opportunities Available (§27)
                </h3>
                <p className="mt-1 text-xs text-slate-300 max-w-xl">
                  You have been matched to multiple organizational roles. Choose your preferred opportunity order so managers and HR can prioritize your career choice.
                </p>
              </div>

              <div className="flex flex-wrap gap-3 items-center">
                <div>
                  <label className="block text-[10px] uppercase font-semibold text-slate-400 mb-1">1st Preference</label>
                  <select
                    value={prefRole1}
                    onChange={(e) => setPrefRole1(e.target.value)}
                    className="rounded-lg border border-white/20 bg-ink-950 px-3 py-1.5 text-xs text-white"
                  >
                    <option value="">Select 1st Role...</option>
                    {opportunities.map((o) => (
                      <option key={o.role_id} value={o.role_id}>{o.title} ({o.fit_score}% Fit)</option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-[10px] uppercase font-semibold text-slate-400 mb-1">2nd Preference</label>
                  <select
                    value={prefRole2}
                    onChange={(e) => setPrefRole2(e.target.value)}
                    className="rounded-lg border border-white/20 bg-ink-950 px-3 py-1.5 text-xs text-white"
                  >
                    <option value="">Select 2nd Role...</option>
                    {opportunities.filter((o) => o.role_id !== prefRole1).map((o) => (
                      <option key={o.role_id} value={o.role_id}>{o.title} ({o.fit_score}% Fit)</option>
                    ))}
                  </select>
                </div>

                <button
                  onClick={handleSavePreferences}
                  disabled={savePreferencesMutation.isPending}
                  className="mt-4 rounded-lg bg-accent-500 px-4 py-2 text-xs font-semibold text-ink-950 transition hover:bg-accent-400 disabled:opacity-50"
                >
                  {savePreferencesMutation.isPending ? "Saving…" : "Save Preferences"}
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Tab Navigation */}
        <div className="flex border-b border-white/10 pb-2 gap-2">
          {[
            { id: "opportunities", label: `Internal Opportunities (${opportunities.length})` },
            { id: "profile", label: "My Skills & Verified Projects" },
            { id: "learning", label: "Learning Roadmap & Skill Upgrade" },
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`rounded-xl px-4 py-2 text-xs font-semibold transition ${
                activeTab === tab.id
                  ? "bg-brand-600 text-white shadow-lg shadow-brand-600/25"
                  : "border border-white/10 bg-ink-900/60 text-slate-400 hover:text-white"
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {/* Opportunities Feed (§26) */}
        {activeTab === "opportunities" && (
          <div className="grid gap-6">
            {opportunities.map((opp) => (
              <div
                key={opp.role_id}
                className="overflow-hidden rounded-3xl border border-white/10 bg-ink-900/60 p-6 sm:p-8 space-y-6"
              >
                <div className="flex flex-wrap items-start justify-between gap-4">
                  <div>
                    <span className="rounded-full border border-brand-400/30 bg-brand-500/10 px-2.5 py-0.5 text-[10px] font-semibold text-brand-300">
                      {opp.department} · {opp.headcount} {opp.headcount === 1 ? "vacancy" : "vacancies"}
                    </span>
                    <h2 className="font-display mt-2 text-xl font-bold text-white">{opp.title}</h2>
                    <p className="mt-1 text-xs text-slate-400 max-w-xl">{opp.description}</p>
                  </div>

                  <div className="flex items-center gap-3">
                    <div className="rounded-xl border border-brand-400/30 bg-brand-500/10 px-4 py-2 text-center">
                      <p className="font-display text-xl font-bold text-brand-300">{opp.fit_score}%</p>
                      <p className="text-[10px] font-semibold uppercase tracking-wider text-slate-400">Fit</p>
                    </div>
                    <div className="rounded-xl border border-emerald-400/30 bg-emerald-500/10 px-4 py-2 text-center">
                      <p className="font-display text-xl font-bold text-emerald-300">{opp.readiness_score}%</p>
                      <p className="text-[10px] font-semibold uppercase tracking-wider text-slate-400">Readiness</p>
                    </div>
                  </div>
                </div>

                {/* Grounded Why You Match (§26) */}
                <div className="rounded-2xl border border-white/5 bg-ink-950/60 p-4 space-y-2">
                  <h4 className="text-xs font-bold text-emerald-300 flex items-center gap-1.5">
                    <span>✓</span> Why you match this role:
                  </h4>
                  <p className="text-xs text-slate-300 leading-relaxed">
                    {opp.ai_explanation}
                  </p>
                  <div className="mt-2 flex flex-wrap gap-2 pt-2 border-t border-white/5">
                    {opp.evidence_refs?.map((ev, i) => (
                      <span key={i} className="text-[11px] text-slate-400">
                        • {ev}
                      </span>
                    ))}
                  </div>
                </div>

                {/* Skill Gaps & Recommended Learning Row */}
                <div className="grid gap-4 sm:grid-cols-2 text-xs">
                  <div className="rounded-2xl border border-white/5 bg-ink-950/40 p-4">
                    <span className="font-semibold text-slate-400 uppercase text-[10px] tracking-wider">Skill Gaps to Address:</span>
                    <div className="mt-2 space-y-1">
                      {opp.missing_skills?.map((ms) => (
                        <p key={ms} className="text-rose-300">○ {ms} (Target required for day-to-day)</p>
                      ))}
                      {opp.partial_skills?.map((ps) => (
                        <p key={ps} className="text-amber-300">△ {ps} (Developing foundation)</p>
                      ))}
                    </div>
                  </div>

                  <div className="rounded-2xl border border-white/5 bg-ink-950/40 p-4">
                    <span className="font-semibold text-slate-400 uppercase text-[10px] tracking-wider">Recommended Learning:</span>
                    <div className="mt-2 space-y-1">
                      {opp.learning_items?.slice(0, 2).map((item, i) => (
                        <p key={i} className="text-slate-300">
                          {i + 1}. {item.course_title || item.resource} ({item.provider || "Curated"})
                        </p>
                      ))}
                    </div>
                  </div>
                </div>

                {/* Actions: Accept or Decline (§26, §28, §30) */}
                <div className="flex flex-wrap items-center justify-between border-t border-white/5 pt-4 text-xs">
                  <div className="text-slate-400">
                    Status:{" "}
                    <strong className="text-white capitalize">
                      {opp.decision_status === "pending_employee"
                        ? "Pending Your Decision"
                        : opp.decision_status === "pending_hr"
                        ? "Accepted · Pending HR Approval"
                        : opp.decision_status === "employee_declined"
                        ? "Declined"
                        : opp.decision_status === "approved"
                        ? "Transfer Approved ✓"
                        : "Discovered Opportunity"}
                    </strong>
                  </div>

                  <div className="flex gap-3">
                    <button
                      onClick={() => declineMutation.mutate(opp.role_id)}
                      disabled={declineMutation.isPending || opp.decision_status === "employee_declined"}
                      className="rounded-xl border border-white/10 bg-white/5 px-4 py-2 font-semibold text-slate-300 hover:border-rose-400/40 hover:text-rose-300 disabled:opacity-40"
                    >
                      {opp.decision_status === "employee_declined" ? "Declined" : "Decline"}
                    </button>

                    <button
                      onClick={() => acceptMutation.mutate(opp.role_id)}
                      disabled={acceptMutation.isPending || opp.decision_status === "pending_hr" || opp.decision_status === "approved"}
                      className="rounded-xl bg-gradient-to-r from-brand-600 to-accent-500 px-5 py-2 font-semibold text-white shadow-lg transition hover:opacity-95 disabled:opacity-50"
                    >
                      {opp.decision_status === "pending_hr"
                        ? "Accepted (Awaiting HR)"
                        : opp.decision_status === "approved"
                        ? "Approved by HR ✓"
                        : "Accept Opportunity →"}
                    </button>
                  </div>
                </div>
              </div>
            ))}

            {opportunities.length === 0 && (
              <div className="rounded-3xl border border-white/10 bg-ink-900/30 p-12 text-center text-slate-400">
                <Icon name="compass" className="mx-auto size-8 text-slate-500" />
                <p className="mt-3 text-sm font-semibold text-white">No active opportunities visible</p>
                <p className="mt-1 text-xs text-slate-500">Only roles with visible status appear in your portal (§25).</p>
              </div>
            )}
          </div>
        )}

        {/* Profile Tab */}
        {activeTab === "profile" && (
          <div className="space-y-6">
            <div className="rounded-3xl border border-white/10 bg-ink-900/60 p-6">
              <h3 className="text-sm font-semibold text-white uppercase tracking-wider">My Skills & Evidence Classification</h3>
              <div className="mt-4 grid gap-3 sm:grid-cols-2">
                {(profile.skills || []).map((sk) => (
                  <div key={sk.name} className="rounded-xl border border-white/5 bg-ink-950/60 p-3.5 text-xs">
                    <div className="flex items-center justify-between">
                      <span className="font-bold text-white">{sk.name}</span>
                      <span className={`rounded-full px-2 py-0.5 text-[10px] font-semibold uppercase ${
                        sk.status === "verified" ? "bg-emerald-500/10 text-emerald-300" : "bg-brand-500/10 text-brand-300"
                      }`}>
                        {sk.status}
                      </span>
                    </div>
                    <p className="mt-1 text-[11px] text-slate-400">
                      Proficiency: {sk.proficiency}/5 · Evidence: {sk.evidence_text || sk.evidence_id || "Profile"}
                    </p>
                  </div>
                ))}
              </div>
            </div>

            <div className="rounded-3xl border border-white/10 bg-ink-900/60 p-6">
              <h3 className="text-sm font-semibold text-white uppercase tracking-wider">Project Evidence Records (§14)</h3>
              <div className="mt-4 space-y-3">
                {(profile.projects || []).map((p) => (
                  <div key={p.id} className="rounded-xl border border-white/5 bg-ink-950/60 p-4 text-xs">
                    <div className="flex items-center justify-between">
                      <span className="font-bold text-white">{p.name}</span>
                      <span className="rounded-full bg-white/5 px-2 py-0.5 text-[10px] text-slate-300 capitalize">
                        {p.status} ({p.completion_percentage}%)
                      </span>
                    </div>
                    <p className="mt-1 text-slate-400">{p.description}</p>
                    <p className="mt-2 text-[11px] text-brand-300">
                      Skills Demonstrated: {(p.skills_used || []).join(", ")}
                    </p>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Learning Roadmap Tab (§54) */}
        {activeTab === "learning" && (
          <div className="rounded-3xl border border-white/10 bg-ink-900/60 p-6 sm:p-8 space-y-6">
            <div>
              <h3 className="font-display text-lg font-bold text-white">Continuous Upskilling Roadmap</h3>
              <p className="mt-1 text-xs text-slate-400">
                Complete curated modules to acquire verified skills and upgrade your match score for emerging roles.
              </p>
            </div>

            <div className="space-y-4">
              {learningItems.map((item, idx) => (
                <div
                  key={idx}
                  className="flex flex-wrap items-center justify-between gap-4 rounded-2xl border border-white/10 bg-ink-950/60 p-5 transition hover:border-brand-400/30"
                >
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="rounded-md bg-brand-500/10 px-2 py-0.5 text-[10px] font-semibold text-brand-300">
                        {item.provider || "Coursera"}
                      </span>
                      <h4 className="text-sm font-bold text-white">{item.course_title || item.resource}</h4>
                    </div>
                    <p className="mt-1 text-xs text-slate-400">
                      Target Skill: <strong className="text-slate-200">{item.skill}</strong> · Duration: {item.estimated_duration}
                    </p>
                    <p className="mt-1 text-[11px] text-slate-500">{item.reason}</p>
                  </div>

                  <button
                    onClick={() =>
                      completeLearningMutation.mutate({
                        courseId: `crs-${idx + 1}`,
                        skillName: item.skill,
                      })
                    }
                    disabled={completeLearningMutation.isPending}
                    className="rounded-xl border border-emerald-400/40 bg-emerald-500/10 px-4 py-2 text-xs font-semibold text-emerald-300 hover:bg-emerald-500/20"
                  >
                    Mark learning complete (§54) ✓
                  </button>
                </div>
              ))}
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
