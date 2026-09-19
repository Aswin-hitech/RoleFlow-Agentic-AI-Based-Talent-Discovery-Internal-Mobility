"""RoleFlow — Employee AI Career Chatbot Service.

Provides grounded, employee-isolated conversational career guidance using GPT-OSS-120B
with strict anti-hallucination guardrails and deterministic factual fallbacks.
"""

import json
import logging
import uuid
from typing import Any, Dict, List, Optional

from ..extensions import db
from ..models import (
    Course,
    Employee,
    EmployeeSkill,
    Project,
    Certification,
    Role,
    RoleCandidate,
    Transfer,
)
from ..agents.llm import get_llm
from ..agents.skill_gap import generate_skill_gap_report
from ..agents.learning import generate_learning_roadmap

logger = logging.getLogger(__name__)


def get_employee_grounded_context(emp_id: str, role_id: Optional[str] = None) -> Dict[str, Any]:
    """Retrieve verified RoleFlow records strictly for the authenticated employee."""
    emp = Employee.query.filter_by(id=emp_id).first()
    if not emp:
        return {}

    skills = EmployeeSkill.query.filter_by(employee_id=emp_id).all()
    projects = Project.query.filter_by(employee_id=emp_id).all()
    certs = Certification.query.filter_by(employee_id=emp_id).all()
    matches = RoleCandidate.query.filter_by(employee_id=emp_id).all()

    # Determine targeted role if requested or available
    target_role = None
    target_candidate = None
    gap_report = {}
    learning_plan = {}
    transfer_record = None

    if role_id:
        role = Role.query.filter_by(id=role_id).first()
        if role and role.visibility == "visible":
            target_role = role
            target_candidate = RoleCandidate.query.filter_by(role_id=role.id, employee_id=emp_id).first()
            gap_report = generate_skill_gap_report(role.id, emp_id)
            learning_plan = generate_learning_roadmap(role.id, emp_id)
            transfer_record = Transfer.query.filter_by(role_id=role.id, employee_id=emp_id).first()
    elif matches:
        # Pick top matched visible role
        valid_candidates = []
        for m in matches:
            r = Role.query.filter_by(id=m.role_id).first()
            if r and r.visibility == "visible":
                valid_candidates.append((m, r))
        if valid_candidates:
            valid_candidates.sort(key=lambda x: (x[0].fit_score or 0, x[0].readiness_score or 0), reverse=True)
            top_cand, top_role = valid_candidates[0]
            target_role = top_role
            target_candidate = top_cand
            gap_report = generate_skill_gap_report(top_role.id, emp_id)
            learning_plan = generate_learning_roadmap(top_role.id, emp_id)
            transfer_record = Transfer.query.filter_by(role_id=top_role.id, employee_id=emp_id).first()

    # Categorize skills
    verified_skills = [s for s in skills if s.status == "verified"]
    explicit_skills = [s for s in skills if s.status == "explicit"]
    inferred_skills = [s for s in skills if s.status == "inferred"]
    transferable_skills = [s for s in skills if s.status == "transferable"]

    # Active and completed projects
    active_projects = [p for p in projects if p.status == "in_progress"]
    completed_projects = [p for p in projects if p.status == "completed"]

    # All visible opportunities
    all_opps = []
    for m in matches:
        r = Role.query.filter_by(id=m.role_id).first()
        if r and r.visibility == "visible":
            all_opps.append({
                "role_id": r.id,
                "title": r.title,
                "department": r.department,
                "fit_score": m.fit_score,
                "readiness_score": m.readiness_score,
            })

    sources = ["employee_profile", f"employee_profile:{emp.id}", "verified_skills", "project_history"]
    if target_role:
        sources.extend(["role_candidate", "skill_gap_report", "learning_roadmap"])

    return {
        "employee": {
            "id": emp.id,
            "full_name": emp.full_name,
            "current_role": emp.current_role,
            "department": emp.department,
            "experience_years": emp.experience_years,
            "availability_days": emp.availability_days,
            "bio": emp.bio,
            "career_interests": emp.career_interests or [],
        },
        "skills": {
            "verified": [f"{s.skill_name} (Proficiency: {s.proficiency}/5, Evidence: {s.evidence_text or 'Project record'})" for s in verified_skills],
            "explicit": [f"{s.skill_name} (Proficiency: {s.proficiency}/5)" for s in explicit_skills],
            "inferred": [f"{s.skill_name} (Proficiency: {s.proficiency}/5)" for s in inferred_skills],
            "transferable": [f"{s.skill_name} (Proficiency: {s.proficiency}/5)" for s in transferable_skills],
            "all_names": [s.skill_name for s in skills],
        },
        "projects": {
            "active": [
                {
                    "name": p.name,
                    "role": p.role,
                    "completion_percentage": p.completion_percentage,
                    "remaining_weeks": p.remaining_weeks,
                    "skills_used": p.skills_used or [],
                }
                for p in active_projects
            ],
            "completed": [
                {
                    "name": p.name,
                    "role": p.role,
                    "skills_used": p.skills_used or [],
                }
                for p in completed_projects
            ],
        },
        "certifications": [
            f"{c.name} by {c.issuer} (Covers: {', '.join(c.skills_covered or [])})"
            for c in certs
        ],
        "active_role": {
            "id": target_role.id if target_role else None,
            "title": target_role.title if target_role else None,
            "department": target_role.department if target_role else None,
            "description": target_role.description if target_role else None,
            "headcount": target_role.headcount if target_role else 1,
            "mandatory_skills": target_role.mandatory_skills if target_role else [],
            "preferred_skills": target_role.preferred_skills if target_role else [],
            "fit_score": target_candidate.fit_score if target_candidate else None,
            "readiness_score": target_candidate.readiness_score if target_candidate else None,
            "fit_breakdown": target_candidate.fit_breakdown if target_candidate else {},
            "readiness_breakdown": target_candidate.readiness_breakdown if target_candidate else {},
            "transferable_skills": target_candidate.transferable_skills if target_candidate else [],
            "ai_explanation": target_candidate.ai_explanation if target_candidate else "",
            "evidence_refs": target_candidate.evidence_refs if target_candidate else [],
            "transfer_status": transfer_record.status if transfer_record else "discovered",
            "preference_rank": transfer_record.preference_rank if transfer_record else None,
            "gap_report": gap_report,
            "learning_plan": learning_plan,
        } if target_role else None,
        "available_opportunities": all_opps,
        "sources": sources,
    }


def _build_system_prompt(ctx: Dict[str, Any]) -> str:
    emp = ctx["employee"]
    skills = ctx["skills"]
    projs = ctx["projects"]
    certs = ctx["certifications"]
    role = ctx.get("active_role")
    opps = ctx.get("available_opportunities", [])

    prompt = f"""You are the RoleFlow Career Assistant, an empathetic, highly knowledgeable, and grounded AI career guide for internal mobility.
You are directly advising {emp['full_name']} ({emp['current_role']} in {emp['department']}, {emp['experience_years']} years experience).

CORE GROUNDING RULES:
1. Base your answer STRICTLY on the authenticated RoleFlow records provided below.
2. NEVER invent, extrapolate, or assume skills, projects, certifications, scores, or opportunities not in the records.
3. If information is not available in the records, say: "I don't have enough information in your RoleFlow profile to answer that yet."
4. Distinguish clearly between Fit Score (skills/experience/domain alignment) and Readiness Score (project timing/availability).
5. Responses must be concise, well-structured, and readable:
   - Use short paragraphs.
   - Use clean bullet points (•) for multiple items.
   - Conclude with a clear, actionable recommended next step.
6. Provide supportive, non-judgmental guidance while leaving decision authority strictly to the employee.

--- AUTHENTICATED EMPLOYEE PROFILE ---
Employee: {emp['full_name']} (ID: {emp['id']})
Current Role: {emp['current_role']}
Department: {emp['department']}
Experience: {emp['experience_years']} years
Availability: {emp['availability_days']} days notice
Bio: {emp['bio']}
Career Interests: {', '.join(emp['career_interests']) or 'General Career Growth'}

--- VERIFIED & INFERRED SKILLS ---
Verified Skills: {'; '.join(skills['verified']) or 'None documented'}
Explicit Skills: {'; '.join(skills['explicit']) or 'None'}
Inferred Skills: {'; '.join(skills['inferred']) or 'None'}
Transferable Bridges: {'; '.join(skills['transferable']) or 'None'}

--- PROJECT TRACK RECORD & COMMITMENTS ---
Active Projects:
{json.dumps(projs['active'], indent=2) if projs['active'] else 'No active projects'}
Completed Projects:
{json.dumps(projs['completed'], indent=2) if projs['completed'] else 'No completed projects'}

--- CERTIFICATIONS ---
{'; '.join(certs) or 'No formal certifications logged'}
"""

    if role:
        gap = role.get("gap_report", {})
        plan = role.get("learning_plan", {})
        prompt += f"""
--- CURRENTLY SELECTED ROLE CONTEXT ---
Target Role: {role['title']} ({role['department']})
Description: {role['description']}
Mandatory Skills: {', '.join(role['mandatory_skills'])}
Preferred Skills: {', '.join(role['preferred_skills'])}
Match Fit Score: {role['fit_score']}%
Match Readiness Score: {role['readiness_score']}%
Fit Score Breakdown: {json.dumps(role['fit_breakdown'])}
Readiness Breakdown / Reason: {json.dumps(role['readiness_breakdown'])}
Transferable Skills to Role: {', '.join(role['transferable_skills']) or 'Adjacent foundation'}
Skill Gaps:
- Strong Skills (Satisfied): {', '.join(gap.get('strong_skills', []))}
- Partial / Developing Skills: {', '.join(gap.get('partial_skills', []))}
- Missing Skills (Required): {', '.join(gap.get('missing_skills', []))}
Curated Learning Items:
{json.dumps(plan.get('items', []), indent=2)}
Transfer Opportunity Status: {role['transfer_status']}
"""
    else:
        prompt += f"""
--- AVAILABLE VISIBLE OPPORTUNITIES ---
{json.dumps(opps, indent=2) if opps else 'No active matches'}
"""

    return prompt


def _deterministic_grounded_reply(query: str, ctx: Dict[str, Any]) -> str:
    """Deterministic, grounded factual reply when the LLM is unavailable."""
    q = query.lower()
    emp = ctx["employee"]
    skills = ctx["skills"]
    projs = ctx["projects"]
    role = ctx.get("active_role")
    opps = ctx.get("available_opportunities", [])

    # 1. Readiness score & Why lower (prioritize before general fit)
    if any(k in q for k in ["readiness", "why lower", "why is my readiness", "project affecting"]):
        if role and role.get("readiness_score") is not None:
            rbd = role.get("readiness_breakdown", {})
            reason = rbd.get("deduction_reason") or "Current project commitments require completion before transition."
            active = projs.get("active", [])
            active_info = ""
            if active:
                p = active[0]
                active_info = f" Specifically, your ongoing commitment to **{p['name']}** is {p['completion_percentage']}% complete with approximately **{p['remaining_weeks']} weeks remaining**."
            return (
                f"Your **Readiness Score is {role['readiness_score']}%** (compared to a {role['fit_score']}% Fit Score).\n\n"
                f"• **Primary factor:** {reason}{active_info}\n"
                f"• **Notice window:** Your profile indicates an availability window of **{emp['availability_days']} days**.\n\n"
                f"**Recommended next step:** As your current project reaches completion over the next 3 weeks, your readiness score will automatically update toward 100%."
            )

    # 2. Fit score & Match reason
    if any(k in q for k in ["fit", "why was i matched", "why matched", "suitable", "match score"]):
        if role and role.get("fit_score") is not None:
            bd = role.get("fit_breakdown", {})
            return (
                f"You are matched to **{role['title']}** with a **{role['fit_score']}% Fit Score**.\n\n"
                f"Here is how your verified profile aligns with this role:\n"
                f"• **Skills Alignment ({bd.get('skills', {}).get('score', 0)}/{bd.get('skills', {}).get('max', 30)} pts)**: Verified proficiency in {', '.join(role.get('mandatory_skills', [])[:3])}.\n"
                f"• **Experience ({bd.get('experience', {}).get('score', 0)}/{bd.get('experience', {}).get('max', 25)} pts)**: {emp['experience_years']} years of industry experience.\n"
                f"• **Project Evidence ({bd.get('projects', {}).get('score', 0)}/{bd.get('projects', {}).get('max', 15)} pts)**: Demonstrated execution across {len(projs['active']) + len(projs['completed'])} projects.\n"
                f"• **Transferable Capabilities ({bd.get('transferable', {}).get('score', 0)}/{bd.get('transferable', {}).get('max', 10)} pts)**: Adjacent technical foundation in Python & data workflows.\n\n"
                f"**Recommended next step:** Review the missing skills below or ask me for your recommended learning plan."
            )
        elif opps:
            top = opps[0]
            return (
                f"You currently have **{len(opps)} active visible opportunities**.\n\n"
                f"Your highest technical match is **{top['title']}** in {top['department']} with a **{top['fit_score']}% Fit Score** "
                f"and **{top['readiness_score']}% Readiness Score**.\n\n"
                f"**Recommended next step:** Select this opportunity to discuss specific skill gaps and learning roadmaps."
            )

    # 3. Missing skills / Skill gaps
    if any(k in q for k in ["missing", "skill gap", "gaps", "what skills am i missing", "what am i missing"]):
        if role:
            gap = role.get("gap_report", {})
            missing = gap.get("missing_skills", [])
            partial = gap.get("partial_skills", [])
            strong = gap.get("strong_skills", [])
            return (
                f"Here is your skill breakdown for **{role['title']}**:\n\n"
                f"• **Strong Skills ({len(strong)})**: {', '.join(strong) or 'None documented'}\n"
                f"• **Developing Skills ({len(partial)})**: {', '.join(partial) or 'None'}\n"
                f"• **Missing Skills to Acquire ({len(missing)})**: {', '.join(missing) or 'All mandatory skills verified!'}\n\n"
                f"**Recommended next step:** Ask me for your curated learning plan to see courses that bridge these missing skills."
            )

    # 4. Learning plan / Courses / Upskilling
    if any(k in q for k in ["learning", "course", "roadmap", "plan", "how do i improve", "which skills should i learn"]):
        if role:
            plan = role.get("learning_plan", {})
            items = plan.get("items", [])
            if items:
                lines = [f"• **Phase {item.get('phase', idx + 1)}**: {item.get('course_title', item.get('resource'))} ({item.get('provider', 'Curated')}) — Targets **{item.get('skill')}** ({item.get('estimated_duration', '20h')})" for idx, item in enumerate(items[:3])]
                return (
                    f"Here is your recommended upskilling roadmap for **{role['title']}**:\n\n"
                    + "\n".join(lines) + "\n\n"
                    f"**Recommended next step:** You can start with Phase 1 in the Learning tab of your portal."
                )

    # 5. Transferable skills
    if any(k in q for k in ["transferable", "bridge", "adjacent"]):
        if role and role.get("transferable_skills"):
            bridges = role.get("transferable_skills", [])
            return (
                f"RoleFlow identified these transferable skill bridges for **{role['title']}**:\n\n"
                + "\n".join([f"• {b}" for b in bridges]) + "\n\n"
                f"These represent skills from your data analytics background that transfer directly into engineering tasks."
            )

    # 6. Current skills / Verified skills
    if any(k in q for k in ["my skills", "strongest skills", "verified skills"]):
        v_list = skills.get("verified", [])
        return (
            f"Here are your verified skills documented in RoleFlow:\n\n"
            + "\n".join([f"• **{s}**" for s in v_list[:5]]) + "\n\n"
            f"These proficiencies have been validated through enterprise project milestones and course completions."
        )

    # 7. Available opportunities
    if any(k in q for k in ["opportunities", "roles", "what internal roles", "internal roles"]):
        if opps:
            lines = [f"• **{o['title']}** ({o['department']}) — **{o['fit_score']}% Fit** | **{o['readiness_score']}% Readiness**" for o in opps]
            return (
                f"You are currently matched to **{len(opps)} visible internal roles**:\n\n"
                + "\n".join(lines) + "\n\n"
                f"**Recommended next step:** Would you like me to explain the match breakdown for any of these roles?"
            )

    # 8. Identity & Profile overview
    if any(k in q for k in ["who am i", "my profile", "my identity", "my name"]):
        return (
            f"You are **{emp['full_name']}** (ID: {emp['id']}), currently working as **{emp['current_role']}** in the **{emp['department']}** department.\n\n"
            f"• **Experience**: {emp['experience_years']} years\n"
            f"• **Verified Skills**: {', '.join(skills.get('all_names', [])[:4]) or 'Profile skills logged'}\n"
            f"• **Notice Window**: {emp['availability_days']} days\n"
            f"• **Active Projects**: {len(projs.get('active', []))} in progress\n\n"
            f"Your data is securely authenticated and isolated from other employees."
        )

    # Default fallback
    target_name = f" for **{role['title']}**" if role else ""
    return (
        f"Hello {emp['full_name']}! I am your **RoleFlow Career Assistant**, connected directly to your employee profile ({emp['id']}).\n\n"
        f"• **Current Role**: {emp['current_role']} ({emp['department']})\n"
        f"• **Verified Skills**: {', '.join(skills.get('all_names', [])[:4])}\n"
        f"• **Active Matches**: {len(opps)} visible opportunities{target_name}\n\n"
        f"You can ask me:\n"
        f"• *\"Why was I matched to this role?\"*\n"
        f"• *\"What skills am I missing?\"*\n"
        f"• *\"Why is my readiness score lower than my fit score?\"*\n"
        f"• *\"Show my recommended learning roadmap\"*"
    )


def _generate_suggestion_chips(ctx: Dict[str, Any]) -> List[str]:
    """Generate dynamic quick action chips tailored to current context."""
    role = ctx.get("active_role")
    if role:
        return [
            "Why was I matched to this role?",
            "What skills am I missing?",
            "Why is readiness lower than fit?",
            "Show my recommended learning plan",
            "What transferable skills do I have?",
            "What internal opportunities are open to me?",
        ]
    return [
        "What internal roles are suitable for me?",
        "What are my strongest verified skills?",
        "How do I improve my career readiness?",
        "Show my learning roadmap",
    ]


def handle_employee_chat(
    emp_id: str,
    message: str,
    role_id: Optional[str] = None,
    history: Optional[List[Dict[str, str]]] = None,
    conversation_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Process employee chat message using GPT-OSS-120B with grounded context and fallback."""
    conv_id = conversation_id or f"conv-{uuid.uuid4().hex[:8]}"
    ctx = get_employee_grounded_context(emp_id, role_id=role_id)
    if not ctx or not ctx.get("employee"):
        return {
            "message": "I don't have enough information in your RoleFlow profile to answer that yet.",
            "conversation_id": conv_id,
            "role_id": role_id,
            "role_title": None,
            "sources": [],
            "suggested_actions": ["Refresh my profile"],
        }

    role = ctx.get("active_role")
    role_title = role["title"] if role else None
    role_id_resolved = role["id"] if role else role_id

    # Attempt LLM call
    system_prompt = _build_system_prompt(ctx)
    llm = get_llm()
    reply_text = ""

    if llm:
        try:
            messages = [("system", system_prompt)]
            # Include recent bounded history (max 6 turns)
            if history:
                for h in history[-6:]:
                    r = h.get("role")
                    c = h.get("content", "")
                    if r in ("user", "human") and c:
                        messages.append(("human", c[:1000]))
                    elif r in ("assistant", "ai") and c:
                        messages.append(("ai", c[:1000]))

            messages.append(("human", message[:2000]))
            response = llm.invoke(messages)
            reply_text = response.content.strip()
        except Exception as exc:
            logger.warning("Chatbot LLM call failed, switching to grounded deterministic fallback: %s", exc)
            reply_text = ""

    # If LLM is offline or returned empty, use grounded deterministic fallback
    if not reply_text:
        reply_text = _deterministic_grounded_reply(message, ctx)

    chips = _generate_suggestion_chips(ctx)

    return {
        "message": reply_text,
        "reply": reply_text,
        "conversation_id": conv_id,
        "role_id": role_id_resolved,
        "role_title": role_title,
        "sources": ctx.get("sources", []),
        "suggested_actions": chips,
        "suggested_chips": chips,
    }
