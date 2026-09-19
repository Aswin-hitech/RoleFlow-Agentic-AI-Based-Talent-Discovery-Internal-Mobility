from datetime import datetime, timezone
import uuid

from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Text, JSON
from ..extensions import db


def _utcnow():
    return datetime.now(timezone.utc)


def _gen_id(prefix=""):
    uid = uuid.uuid4().hex[:12]
    return f"{prefix}{uid}" if prefix else uid


class User(db.Model):
    __tablename__ = "users"

    id = Column(String(64), primary_key=True, default=lambda: _gen_id("usr-"))
    email = Column(String(255), unique=True, nullable=False, index=True)
    full_name = Column(String(255), nullable=False)
    role = Column(String(32), nullable=False, default="employee")  # employee | manager | hr | admin
    password_hash = Column(String(255), nullable=True)
    employee_id = Column(String(64), nullable=True, index=True)
    created_at = Column(DateTime(timezone=True), default=_utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "email": self.email,
            "name": self.full_name,
            "full_name": self.full_name,
            "role": self.role,
            "employee_id": self.employee_id,
        }


class Employee(db.Model):
    __tablename__ = "employees"

    id = Column(String(64), primary_key=True)  # EMP-1024
    user_id = Column(String(64), nullable=True)
    full_name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    current_role = Column(String(255), nullable=False)
    department = Column(String(255), nullable=False)
    experience_years = Column(Float, default=3.0)
    bio = Column(Text, nullable=True)
    open_to_transfer = Column(Boolean, default=True)
    availability_days = Column(Integer, default=30)
    career_interests = Column(JSON, default=list)  # ["ML / AI", "Data Science"]
    embedding = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), default=_utcnow)

    skills = db.relationship("EmployeeSkill", backref="employee", cascade="all, delete-orphan", lazy=True)
    projects = db.relationship("Project", backref="employee", cascade="all, delete-orphan", lazy=True)
    certifications = db.relationship("Certification", backref="employee", cascade="all, delete-orphan", lazy=True)

    def to_dict(self):
        return {
            "id": self.id,
            "full_name": self.full_name,
            "email": self.email,
            "current_role": self.current_role,
            "department": self.department,
            "experience_years": self.experience_years,
            "bio": self.bio,
            "open_to_transfer": self.open_to_transfer,
            "availability_days": self.availability_days,
            "career_interests": self.career_interests or [],
        }


class Skill(db.Model):
    __tablename__ = "skills"

    id = Column(String(64), primary_key=True)
    name = Column(String(128), unique=True, nullable=False, index=True)
    domain = Column(String(128), nullable=False)
    category = Column(String(128), nullable=True)
    description = Column(Text, nullable=True)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "domain": self.domain,
            "category": self.category,
            "description": self.description,
        }


class SkillRelationship(db.Model):
    __tablename__ = "skill_relationships"

    id = Column(String(64), primary_key=True, default=lambda: _gen_id("rel-"))
    source_skill = Column(String(128), nullable=False, index=True)
    target_skill = Column(String(128), nullable=False, index=True)
    relationship_type = Column(String(64), default="transferable_to")
    strength = Column(Float, default=0.8)  # 0.0 - 1.0

    def to_dict(self):
        return {
            "id": self.id,
            "source_skill": self.source_skill,
            "target_skill": self.target_skill,
            "relationship_type": self.relationship_type,
            "strength": self.strength,
        }


class EmployeeSkill(db.Model):
    __tablename__ = "employee_skills"

    id = Column(String(64), primary_key=True, default=lambda: _gen_id("esk-"))
    employee_id = Column(String(64), ForeignKey("employees.id"), nullable=False, index=True)
    skill_name = Column(String(128), nullable=False, index=True)
    proficiency = Column(Integer, default=3)  # 1 - 5
    status = Column(String(32), default="explicit")  # explicit | inferred | transferable | verified
    evidence_id = Column(String(128), nullable=True)
    evidence_text = Column(Text, nullable=True)

    def to_dict(self):
        return {
            "id": self.id,
            "employee_id": self.employee_id,
            "skill_name": self.skill_name,
            "proficiency": self.proficiency,
            "status": self.status,
            "evidence_id": self.evidence_id,
            "evidence_text": self.evidence_text,
        }


class Project(db.Model):
    __tablename__ = "projects"

    id = Column(String(64), primary_key=True, default=lambda: _gen_id("prj-"))
    employee_id = Column(String(64), ForeignKey("employees.id"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    role = Column(String(128), nullable=True)
    skills_used = Column(JSON, default=list)
    status = Column(String(32), default="completed")  # in_progress | completed | on_hold
    completion_percentage = Column(Integer, default=100)
    start_date = Column(String(32), nullable=True)
    expected_end_date = Column(String(32), nullable=True)
    remaining_weeks = Column(Integer, default=0)

    def to_dict(self):
        return {
            "id": self.id,
            "employee_id": self.employee_id,
            "name": self.name,
            "description": self.description,
            "role": self.role,
            "skills_used": self.skills_used or [],
            "status": self.status,
            "completion_percentage": self.completion_percentage,
            "start_date": self.start_date,
            "expected_end_date": self.expected_end_date,
            "remaining_weeks": self.remaining_weeks,
        }


class Certification(db.Model):
    __tablename__ = "certifications"

    id = Column(String(64), primary_key=True, default=lambda: _gen_id("crt-"))
    employee_id = Column(String(64), ForeignKey("employees.id"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    issuer = Column(String(128), nullable=False)
    issue_date = Column(String(32), nullable=True)
    skills_covered = Column(JSON, default=list)

    def to_dict(self):
        return {
            "id": self.id,
            "employee_id": self.employee_id,
            "name": self.name,
            "issuer": self.issuer,
            "issue_date": self.issue_date,
            "skills_covered": self.skills_covered or [],
        }


class Role(db.Model):
    __tablename__ = "roles"

    id = Column(String(64), primary_key=True, default=lambda: _gen_id("role-"))
    title = Column(String(255), nullable=False)
    department = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    jd_text = Column(Text, nullable=True)
    headcount = Column(Integer, default=1)
    minimum_experience = Column(Float, default=2.0)
    mandatory_skills = Column(JSON, default=list)
    preferred_skills = Column(JSON, default=list)
    certifications = Column(JSON, default=list)
    responsibilities = Column(JSON, default=list)
    domain = Column(String(128), default="Engineering")
    status = Column(String(32), default="vacant")  # vacant | filled | closed
    visibility = Column(String(32), default="visible")  # visible | hidden
    created_by_id = Column(String(64), nullable=True)
    created_at = Column(DateTime(timezone=True), default=_utcnow)
    last_discovered_at = Column(DateTime(timezone=True), nullable=True)
    embedding = Column(JSON, nullable=True)

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "department": self.department,
            "description": self.description,
            "jd_text": self.jd_text,
            "headcount": self.headcount,
            "minimum_experience": self.minimum_experience,
            "mandatory_skills": self.mandatory_skills or [],
            "preferred_skills": self.preferred_skills or [],
            "certifications": self.certifications or [],
            "responsibilities": self.responsibilities or [],
            "domain": self.domain,
            "status": self.status,
            "visibility": self.visibility,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "last_discovered_at": self.last_discovered_at.isoformat() if self.last_discovered_at else None,
        }


class RoleCandidate(db.Model):
    __tablename__ = "role_candidates"

    id = Column(String(64), primary_key=True, default=lambda: _gen_id("cand-"))
    role_id = Column(String(64), ForeignKey("roles.id"), nullable=False, index=True)
    employee_id = Column(String(64), ForeignKey("employees.id"), nullable=False, index=True)
    fit_score = Column(Integer, default=0)
    readiness_score = Column(Integer, default=0)
    fit_breakdown = Column(JSON, default=dict)
    readiness_breakdown = Column(JSON, default=dict)
    top_skills = Column(JSON, default=list)
    transferable_skills = Column(JSON, default=list)
    ai_explanation = Column(Text, nullable=True)
    evidence_refs = Column(JSON, default=list)
    status = Column(String(32), default="discovered")  # discovered | shortlisted | declined | transferred
    match_run_id = Column(String(64), nullable=True)
    created_at = Column(DateTime(timezone=True), default=_utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "role_id": self.role_id,
            "employee_id": self.employee_id,
            "fit_score": self.fit_score,
            "readiness_score": self.readiness_score,
            "fit_breakdown": self.fit_breakdown or {},
            "readiness_breakdown": self.readiness_breakdown or {},
            "top_skills": self.top_skills or [],
            "transferable_skills": self.transferable_skills or [],
            "ai_explanation": self.ai_explanation or "",
            "evidence_refs": self.evidence_refs or [],
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class Transfer(db.Model):
    __tablename__ = "transfers"

    id = Column(String(64), primary_key=True, default=lambda: _gen_id("trf-"))
    role_id = Column(String(64), ForeignKey("roles.id"), nullable=False, index=True)
    employee_id = Column(String(64), ForeignKey("employees.id"), nullable=False, index=True)
    candidate_id = Column(String(64), ForeignKey("role_candidates.id"), nullable=True)
    status = Column(
        String(32), default="pending_employee"
    )  # pending_employee | employee_accepted | employee_declined | pending_hr | approved | rejected | completed
    preference_rank = Column(Integer, default=1)
    manager_id = Column(String(64), nullable=True)
    hr_id = Column(String(64), nullable=True)
    hr_notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=_utcnow)
    updated_at = Column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "role_id": self.role_id,
            "employee_id": self.employee_id,
            "candidate_id": self.candidate_id,
            "status": self.status,
            "preference_rank": self.preference_rank,
            "manager_id": self.manager_id,
            "hr_id": self.hr_id,
            "hr_notes": self.hr_notes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class SkillGapRecord(db.Model):
    __tablename__ = "skill_gap_records"

    id = Column(String(64), primary_key=True, default=lambda: _gen_id("gap-"))
    role_id = Column(String(64), ForeignKey("roles.id"), nullable=False, index=True)
    employee_id = Column(String(64), ForeignKey("employees.id"), nullable=False, index=True)
    strong_skills = Column(JSON, default=list)
    partial_skills = Column(JSON, default=list)
    missing_skills = Column(JSON, default=list)
    gap_details = Column(JSON, default=list)
    created_at = Column(DateTime(timezone=True), default=_utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "role_id": self.role_id,
            "employee_id": self.employee_id,
            "strong_skills": self.strong_skills or [],
            "partial_skills": self.partial_skills or [],
            "missing_skills": self.missing_skills or [],
            "gap_details": self.gap_details or [],
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class Course(db.Model):
    __tablename__ = "courses"

    id = Column(String(64), primary_key=True)
    title = Column(String(255), nullable=False)
    provider = Column(String(64), nullable=False)  # Coursera | Udemy | NPTEL | Microsoft Learn | Internal Learning
    description = Column(Text, nullable=True)
    target_skills = Column(JSON, default=list)
    duration_hours = Column(Integer, default=20)
    level = Column(String(32), default="Intermediate")

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "provider": self.provider,
            "description": self.description,
            "target_skills": self.target_skills or [],
            "duration_hours": self.duration_hours,
            "level": self.level,
        }


class LearningPlanRecord(db.Model):
    __tablename__ = "learning_plans"

    id = Column(String(64), primary_key=True, default=lambda: _gen_id("lrn-"))
    role_id = Column(String(64), ForeignKey("roles.id"), nullable=False, index=True)
    employee_id = Column(String(64), ForeignKey("employees.id"), nullable=False, index=True)
    items = Column(JSON, default=list)
    roadmap_explanation = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=_utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "role_id": self.role_id,
            "employee_id": self.employee_id,
            "items": self.items or [],
            "roadmap_explanation": self.roadmap_explanation,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class MatchRun(db.Model):
    __tablename__ = "match_runs"

    id = Column(String(64), primary_key=True, default=lambda: _gen_id("run-"))
    role_id = Column(String(64), ForeignKey("roles.id"), nullable=False, index=True)
    status = Column(String(64), default="queued")  # queued | analyzing | transferable_skills | scoring | explaining | completed | failed
    current_stage = Column(String(128), default="Discovery queued")
    progress = Column(Integer, default=0)
    candidates_count = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), default=_utcnow)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    def to_dict(self):
        return {
            "id": self.id,
            "role_id": self.role_id,
            "status": self.status,
            "current_stage": self.current_stage,
            "progress": self.progress,
            "candidates_count": self.candidates_count,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }
