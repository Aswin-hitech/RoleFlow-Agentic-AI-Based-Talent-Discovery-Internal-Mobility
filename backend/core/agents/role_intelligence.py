"""Agent 2 — Role Intelligence Agent.

Converts JD text into structured, manager-editable requirements.
"""

import json
import re
from typing import Any, Dict
from .llm import generate_structured


def parse_job_description(jd_text: str, default_title: str = "", default_dept: str = "") -> Dict[str, Any]:
    """Extract structured criteria from a job description."""
    schema_hint = """{
  "title": "ML Engineer",
  "department": "Data & AI",
  "domain": "AI/ML",
  "minimum_experience": 2.0,
  "mandatory_skills": ["Python", "Machine Learning", "SQL"],
  "preferred_skills": ["MLOps", "Model Deployment", "System Design"],
  "certifications": ["TensorFlow Developer" or similar],
  "responsibilities": ["Design and train models", "Deploy pipelines to production"],
  "headcount": 1
}"""

    prompt = f"""Analyze this Job Description and extract structured role requirements:

Job Description:
\"\"\"
{jd_text}
\"\"\"

Title hint: {default_title}
Department hint: {default_dept}
"""

    raw_json = generate_structured(prompt, schema_hint)
    if raw_json:
        try:
            data = json.loads(raw_json)
            if isinstance(data, dict) and "mandatory_skills" in data:
                return data
        except Exception:
            pass

    # Deterministic fallback parser
    return _deterministic_parse(jd_text, default_title, default_dept)


def _deterministic_parse(text: str, default_title: str, default_dept: str) -> Dict[str, Any]:
    lower = text.lower()

    # Detect title
    title = default_title
    if not title:
        for possible in [
            "ml engineer",
            "machine learning engineer",
            "data scientist",
            "data analyst",
            "software engineer",
            "backend engineer",
            "frontend engineer",
            "ai engineer",
            "product analyst",
            "cloud architect",
        ]:
            if possible in lower:
                title = possible.title()
                break
    if not title:
        title = "Software Engineer"

    # Detect department & domain
    dept = default_dept or ("Data & AI" if any(k in lower for k in ["ml", "data", "ai", "machine learning"]) else "Engineering")
    domain = "AI/ML" if any(k in lower for k in ["ml", "machine learning", "deep learning", "ai"]) else (
        "Data Engineering" if "data" in lower else "Software Engineering"
    )

    # Detect experience
    exp_match = re.search(r"(\d+)\+?\s*(?:to\s*\d+\s*)?(?:years?|yrs?)", lower)
    min_exp = float(exp_match.group(1)) if exp_match else 2.0

    # Skill extraction catalog
    catalog = {
        "Python": ["python", "pandas", "numpy"],
        "Machine Learning": ["machine learning", "ml", "scikit-learn", "sklearn"],
        "Deep Learning": ["deep learning", "pytorch", "tensorflow", "keras"],
        "SQL": ["sql", "postgres", "mysql", "queries"],
        "Data Pipelines": ["pipeline", "etl", "data pipeline", "airflow"],
        "Data Engineering": ["data engineering", "spark", "hadoop", "databricks"],
        "MLOps": ["mlops", "model monitoring", "mlflow", "feature store"],
        "Model Deployment": ["deployment", "serving", "docker", "fastapi", "inference"],
        "APIs": ["api", "rest", "graphql", "endpoints"],
        "React": ["react", "react.js", "frontend", "typescript"],
        "System Design": ["system design", "architecture", "distributed systems"],
        "Testing": ["testing", "unit test", "automation", "qa", "pytest"],
        "CI/CD": ["ci/cd", "ci", "cd", "continuous integration"],
        "Statistics": ["statistics", "statistical", "probability"],
    }

    found_skills = []
    for skill, aliases in catalog.items():
        if any(alias in lower for alias in aliases):
            found_skills.append(skill)

    if not found_skills:
        found_skills = ["Python", "Machine Learning", "SQL"]

    # Split into mandatory and preferred
    mandatory = found_skills[:max(2, len(found_skills) // 2 + 1)]
    preferred = [s for s in found_skills if s not in mandatory]
    if not preferred:
        preferred = ["System Design", "MLOps"]

    # Responsibilities
    responsibilities = []
    for line in text.split("\n"):
        clean = line.strip().lstrip("-*•0123456789. ")
        if len(clean) > 20 and any(kw in clean.lower() for kw in ["develop", "build", "lead", "design", "manage", "collaborate", "ensure", "deploy"]):
            responsibilities.append(clean)
            if len(responsibilities) >= 4:
                break

    if not responsibilities:
        responsibilities = [
            f"Build and maintain robust {title} solutions",
            "Collaborate with cross-functional product and engineering teams",
            "Ensure high test coverage, reliable deployments, and system scalability",
        ]

    # Certifications
    certs = []
    if "cert" in lower:
        if "aws" in lower:
            certs.append("AWS Certified Machine Learning Specialist")
        if "tensorflow" in lower:
            certs.append("TensorFlow Developer Certificate")
        if not certs:
            certs.append("Relevant Professional Certification")

    return {
        "title": title,
        "department": dept,
        "domain": domain,
        "minimum_experience": min_exp,
        "mandatory_skills": mandatory,
        "preferred_skills": preferred,
        "certifications": certs,
        "responsibilities": responsibilities,
        "headcount": 1,
        "visibility": "visible",
    }
