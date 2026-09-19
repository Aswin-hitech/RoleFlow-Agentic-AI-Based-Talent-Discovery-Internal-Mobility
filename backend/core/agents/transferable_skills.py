"""Agent 3 — Transferable Skill Discovery Agent.

Identifies capability bridges between employee skills and target role requirements:
Python -> Data Processing -> Machine Learning
SQL -> Data Engineering -> Data Platform
React -> Frontend Development -> Full Stack Development

Classifies skills as:
- verified: Demonstrated directly in completed project or certification
- explicit: Explicitly declared on employee profile
- transferable: Connected through skill relationship ontology + evidence
- inferred: Related through semantic similarity / domain overlap
"""

from typing import Any, Dict, List
from ..models import SkillRelationship


# Base ontology transitions
ONTOLOGY_BRIDGES = {
    "Python": [
        {"capability": "Data Processing", "target": "Machine Learning", "strength": 0.85},
        {"capability": "Backend Scripting", "target": "Data Engineering", "strength": 0.80},
        {"capability": "Automation Testing", "target": "CI/CD Pipeline", "strength": 0.78},
    ],
    "SQL": [
        {"capability": "Data Engineering", "target": "Data Platform", "strength": 0.90},
        {"capability": "Analytics Querying", "target": "Machine Learning Feature Engineering", "strength": 0.82},
    ],
    "React": [
        {"capability": "Frontend Development", "target": "Full Stack Development", "strength": 0.88},
        {"capability": "UI State Architecture", "target": "Web Applications", "strength": 0.85},
    ],
    "Statistics": [
        {"capability": "Quantitative Analysis", "target": "Predictive Modeling", "strength": 0.88},
        {"capability": "Data Analytics", "target": "Machine Learning", "strength": 0.82},
    ],
    "Automation": [
        {"capability": "Test Automation", "target": "CI/CD Engineering", "strength": 0.84},
        {"capability": "Workflow Scripting", "target": "DevOps / Reliability", "strength": 0.79},
    ],
}


def discover_transferable_skills(
    employee_profile: Dict[str, Any],
    target_skills: List[str],
) -> List[Dict[str, Any]]:
    """Discover evidence-backed transferable skills bridging employee skills to target role skills."""
    emp_skills = {s["name"].lower(): s for s in employee_profile.get("skills", [])}
    projects = employee_profile.get("projects", [])
    transferable = []

    # Check DB relationships as well
    db_rels = SkillRelationship.query.all()
    relationship_map = {}
    for rel in db_rels:
        key = rel.source_skill.lower()
        if key not in relationship_map:
            relationship_map[key] = []
        relationship_map[key].append({
            "target": rel.target_skill,
            "strength": rel.strength,
            "type": rel.relationship_type,
        })

    for target_skill in target_skills:
        target_lower = target_skill.lower()

        # If already directly possessed, check if verified by project
        if target_lower in emp_skills:
            continue

        # Look for bridges
        for emp_skill_name, skill_info in emp_skills.items():
            # Check built-in bridges
            title_name = skill_info["name"]
            bridges = ONTOLOGY_BRIDGES.get(title_name, [])

            for b in bridges:
                if target_lower in b["target"].lower() or b["target"].lower() in target_lower:
                    # Find backing project evidence
                    evidence_project = None
                    for p in projects:
                        used = [u.lower() for u in p.get("skills_used", [])]
                        if emp_skill_name in used:
                            evidence_project = p
                            break

                    evidence_note = (
                        f"Demonstrated via {evidence_project['name']} ({evidence_project.get('role', 'Contributor')})"
                        if evidence_project
                        else f"Inferred from {title_name} proficiency level {skill_info.get('proficiency', 3)}"
                    )

                    transferable.append({
                        "source_skill": title_name,
                        "bridge_capability": b["capability"],
                        "target_skill": target_skill,
                        "strength": b["strength"],
                        "classification": "transferable" if evidence_project else "inferred",
                        "evidence": evidence_note,
                        "evidence_id": evidence_project["id"] if evidence_project else skill_info.get("evidence_id"),
                    })

            # Check DB relationships
            if emp_skill_name in relationship_map:
                for rel in relationship_map[emp_skill_name]:
                    if target_lower in rel["target"].lower() or rel["target"].lower() in target_lower:
                        if not any(t["target_skill"] == target_skill for t in transferable):
                            transferable.append({
                                "source_skill": skill_info["name"],
                                "bridge_capability": rel.get("type", "transferable_to"),
                                "target_skill": target_skill,
                                "strength": rel["strength"],
                                "classification": "transferable",
                                "evidence": f"Ontology mapped relatedness ({rel['strength']})",
                                "evidence_id": None,
                            })

    return transferable
