"""RoleFlow — Synthetic Data Generator and Demo Seeder.

Usage:
    python seed.py
    python seed.py --reset
"""

import sys
from datetime import datetime, timezone
import random
from werkzeug.security import generate_password_hash

from core import create_app
from core.extensions import db
from core.models import (
    User,
    Employee,
    Skill,
    SkillRelationship,
    EmployeeSkill,
    Project,
    Certification,
    Role,
    RoleCandidate,
    Transfer,
    Course,
    MatchRun,
)
from core.agents.embeddings import embed_texts


def seed_database(reset: bool = False):
    app = create_app()
    with app.app_context():
        if reset:
            print("Resetting database...")
            db.drop_all()

        db.create_all()
        print("Database schema created.")

        # Check if already seeded and not reset
        if not reset and User.query.filter_by(email="manager@roleflow.io").first():
            print("Database already contains demo data. Run with --reset to wipe and re-seed.")
            return

        print("Seeding demo users...")
        pwd_hash = generate_password_hash("demo1234")

        users = [
            User(
                id="usr-mgr-01",
                email="manager@roleflow.io",
                full_name="Priya Sharma",
                role="manager",
                password_hash=pwd_hash,
                employee_id="EMP-0001",
            ),
            User(
                id="usr-emp-01",
                email="employee@roleflow.io",
                full_name="Arjun Mehta",
                role="employee",
                password_hash=pwd_hash,
                employee_id="EMP-1024",
            ),
            User(
                id="usr-hr-01",
                email="hr@roleflow.io",
                full_name="Sneha Rao",
                role="hr",
                password_hash=pwd_hash,
                employee_id="EMP-0002",
            ),
        ]
        db.session.add_all(users)

        print("Seeding skills and ontology relationships...")
        skills_data = [
            ("Python", "Programming", "Core language"),
            ("Machine Learning", "AI/ML", "ML algorithms, models, and training"),
            ("Deep Learning", "AI/ML", "Neural networks, PyTorch, TensorFlow"),
            ("SQL", "Database", "Querying, schema design, relational DBs"),
            ("Data Pipelines", "Data Engineering", "ETL, Airflow, stream processing"),
            ("Data Engineering", "Data Engineering", "Data platform and warehouse architectures"),
            ("Data Processing", "Data", "Data wrangling, cleaning, transformations"),
            ("MLOps", "AI/ML", "Model deployment, monitoring, CI/CD for ML"),
            ("Model Deployment", "AI/ML", "Inference serving, Docker, API integration"),
            ("System Design", "Engineering", "Distributed systems, architectural scalability"),
            ("React", "Frontend", "UI architecture, state management, components"),
            ("Frontend Development", "Frontend", "Client-side development"),
            ("Full Stack Development", "Engineering", "End-to-end full stack architecture"),
            ("Statistics", "Data", "Hypothesis testing, probability, inferential stats"),
            ("Predictive Modeling", "AI/ML", "Regression, forecasting, classification"),
            ("Automation", "Testing", "Test automation frameworks, scripting"),
            ("Testing", "Engineering", "Unit, integration, and performance testing"),
            ("CI/CD", "DevOps", "Continuous integration and deployment pipelines"),
            ("APIs", "Engineering", "RESTful API development, GraphQL"),
            ("Database", "Database", "Relational and NoSQL data stores"),
        ]

        skill_objs = {}
        for s_name, s_domain, s_desc in skills_data:
            s = Skill(
                id=f"skl-{s_name.lower().replace(' ', '-')}",
                name=s_name,
                domain=s_domain,
                description=s_desc,
            )
            db.session.add(s)
            skill_objs[s_name] = s

        relationships = [
            ("Python", "Data Processing", "specialization_of", 0.90),
            ("Data Processing", "Machine Learning", "transferable_to", 0.85),
            ("Python", "Machine Learning", "transferable_to", 0.85),
            ("SQL", "Data Engineering", "transferable_to", 0.90),
            ("Data Engineering", "Data Platform", "specialization_of", 0.88),
            ("React", "Frontend Development", "specialization_of", 0.95),
            ("Frontend Development", "Full Stack Development", "transferable_to", 0.88),
            ("React", "Full Stack Development", "transferable_to", 0.85),
            ("Statistics", "Predictive Modeling", "transferable_to", 0.88),
            ("Statistics", "Machine Learning", "transferable_to", 0.82),
            ("Automation", "CI/CD", "transferable_to", 0.85),
            ("Testing", "Automation", "specialization_of", 0.86),
        ]
        for src, tgt, rel_type, strength in relationships:
            rel = SkillRelationship(
                source_skill=src,
                target_skill=tgt,
                relationship_type=rel_type,
                strength=strength,
            )
            db.session.add(rel)

        print("Seeding curated courses...")
        courses_data = [
            ("MLOps Fundamentals & Continuous Delivery", "Coursera", "End-to-end MLOps architectures, MLflow, model registry, monitoring", ["MLOps", "Model Deployment"], 25, "Intermediate"),
            ("Production Machine Learning System Design", "Internal Learning", "Scalable distributed model serving, feature stores, and reliability", ["System Design", "MLOps"], 20, "Advanced"),
            ("Practical Model Deployment with FastAPI & Docker", "Udemy", "Containerizing ML models, high-throughput REST APIs, async batching", ["Model Deployment", "APIs"], 18, "Intermediate"),
            ("Advanced Deep Learning & Transformer Architectures", "NPTEL", "Attention mechanisms, transformers, transfer learning with PyTorch", ["Deep Learning", "Machine Learning"], 30, "Advanced"),
            ("Modern Data Engineering with Python & Spark", "Coursera", "Building high-performance data processing pipelines and lakehouses", ["Data Engineering", "Data Pipelines"], 22, "Intermediate"),
            ("Enterprise Full Stack Development with React & Python", "Microsoft Learn", "Modern full-stack web applications, microservices, and state", ["Full Stack Development", "React"], 24, "Intermediate"),
            ("Continuous Integration & Automated Testing at Scale", "Internal Learning", "Test automation patterns, CI/CD GitHub Actions, resilience", ["Automation", "CI/CD", "Testing"], 16, "Intermediate"),
        ]
        for idx, (c_title, c_prov, c_desc, c_targets, c_dur, c_lvl) in enumerate(courses_data, 1):
            c = Course(
                id=f"crs-{idx:03d}",
                title=c_title,
                provider=c_prov,
                description=c_desc,
                target_skills=c_targets,
                duration_hours=c_dur,
                level=c_lvl,
            )
            db.session.add(c)

        print("Seeding mandatory and rich employee profiles (§43)...")

        # Employee A: Arjun Mehta (EMP-1024)
        emp_a = Employee(
            id="EMP-1024",
            user_id="usr-emp-01",
            full_name="Arjun Mehta",
            email="employee@roleflow.io",
            current_role="Data Analyst",
            department="Data & AI",
            experience_years=4.5,
            bio="Senior data analyst with deep expertise in Python, statistical modeling, and large-scale SQL query optimization. Actively building ML systems.",
            open_to_transfer=True,
            availability_days=30,
            career_interests=["ML / AI", "Machine Learning", "Data Science"],
            embedding=embed_texts(["Data Analyst Python SQL Statistics Machine Learning Predictive Modeling Data & AI"])[0],
        )
        db.session.add(emp_a)

        # Projects for Arjun Mehta
        p_a1 = Project(
            id="prj-1024-1",
            employee_id="EMP-1024",
            name="Customer Analytics Platform",
            description="Built multi-touch attribution models and high-throughput churn analysis data pipelines using Python and SQL.",
            role="Lead Analyst",
            skills_used=["Python", "SQL", "Statistics", "Data Processing"],
            status="in_progress",
            completion_percentage=75,
            remaining_weeks=3,
            start_date="2026-03-01",
            expected_end_date="2026-10-15",
        )
        p_a2 = Project(
            id="prj-1024-2",
            employee_id="EMP-1024",
            name="Predictive Churn Modeling",
            description="Trained gradient boosting classification models for 500k customer cohort predicting 90-day retention.",
            role="Specialist",
            skills_used=["Python", "Machine Learning", "Statistics"],
            status="completed",
            completion_percentage=100,
            remaining_weeks=0,
            start_date="2025-06-01",
            expected_end_date="2025-12-15",
        )
        db.session.add_all([p_a1, p_a2])

        # Skills for Arjun Mehta
        emp_skills_a = [
            ("Python", 4, "verified", "prj-1024-1", "Demonstrated in Customer Analytics Platform"),
            ("SQL", 4, "verified", "prj-1024-1", "Advanced queries and schema tuning"),
            ("Statistics", 4, "verified", "prj-1024-2", "Statistical modeling and hypothesis testing"),
            ("Machine Learning", 3, "inferred", "prj-1024-2", "Demonstrated scikit-learn models in completed project"),
        ]
        for sk_name, prof, status, evid_id, evid_text in emp_skills_a:
            es = EmployeeSkill(
                employee_id="EMP-1024",
                skill_name=sk_name,
                proficiency=prof,
                status=status,
                evidence_id=evid_id,
                evidence_text=evid_text,
            )
            db.session.add(es)

        cert_a = Certification(
            employee_id="EMP-1024",
            name="IBM Data Science Professional",
            issuer="IBM",
            issue_date="2025-02-10",
            skills_covered=["Python", "Statistics", "Machine Learning"],
        )
        db.session.add(cert_a)

        # Employee B: Kavita Raman (EMP-1025)
        emp_b = Employee(
            id="EMP-1025",
            full_name="Kavita Raman",
            email="kavita.raman@roleflow.io",
            current_role="Software Engineer",
            department="Engineering",
            experience_years=3.5,
            bio="Full-stack oriented software engineer proficient in Python APIs, React frontends, and relational database optimization.",
            open_to_transfer=True,
            availability_days=14,
            career_interests=["Full Stack Development", "AI / ML", "Backend Engineering"],
            embedding=embed_texts(["Software Engineer Python React APIs Database Full Stack Engineering"])[0],
        )
        db.session.add(emp_b)

        p_b = Project(
            id="prj-1025-1",
            employee_id="EMP-1025",
            name="Internal Developer Portal",
            description="Built microservices in Python and responsive dashboards in React, integrating team APIs.",
            role="Full Stack Engineer",
            skills_used=["Python", "React", "APIs", "Database"],
            status="completed",
            completion_percentage=100,
            remaining_weeks=0,
            start_date="2025-01-10",
            expected_end_date="2025-09-01",
        )
        db.session.add(p_b)

        for sk, prf, st in [("Python", 4, "verified"), ("React", 4, "verified"), ("APIs", 4, "verified"), ("Database", 3, "verified")]:
            db.session.add(EmployeeSkill(
                employee_id="EMP-1025",
                skill_name=sk,
                proficiency=prf,
                status=st,
                evidence_id="prj-1025-1",
                evidence_text="Enterprise portal implementation",
            ))

        # Employee C: Rohan Verma (EMP-1026)
        emp_c = Employee(
            id="EMP-1026",
            full_name="Rohan Verma",
            email="rohan.verma@roleflow.io",
            current_role="QA Engineer",
            department="Quality Engineering",
            experience_years=4.0,
            bio="QA automation specialist with robust Python testing frameworks, CI/CD pipeline integration, and test harness authoring.",
            open_to_transfer=True,
            availability_days=20,
            career_interests=["DevOps", "Backend Engineering", "Test Engineering"],
            embedding=embed_texts(["QA Engineer Automation Python Testing CI/CD Quality Engineering"])[0],
        )
        db.session.add(emp_c)

        p_c = Project(
            id="prj-1026-1",
            employee_id="EMP-1026",
            name="Continuous Automated Test Suite",
            description="Engineered distributed regression suite running thousands of tests on each GitHub pull request.",
            role="Lead QA Engineer",
            skills_used=["Automation", "Python", "Testing", "CI/CD"],
            status="completed",
            completion_percentage=100,
            remaining_weeks=0,
            start_date="2025-04-01",
            expected_end_date="2025-11-20",
        )
        db.session.add(p_c)

        for sk, prf, st in [("Automation", 4, "verified"), ("Python", 3, "verified"), ("Testing", 5, "verified"), ("CI/CD", 3, "verified")]:
            db.session.add(EmployeeSkill(
                employee_id="EMP-1026",
                skill_name=sk,
                proficiency=prf,
                status=st,
                evidence_id="prj-1026-1",
                evidence_text="Demonstrated in Continuous Automated Test Suite",
            ))

        # Add 30 additional detailed employee profiles across various domains
        roles_pool = [
            ("Data Scientist", "Data & AI", ["Python", "Machine Learning", "Deep Learning", "Statistics"]),
            ("Backend Engineer", "Engineering", ["Python", "APIs", "Database", "System Design"]),
            ("Frontend Engineer", "Engineering", ["React", "Frontend Development", "APIs"]),
            ("Product Analyst", "Product", ["SQL", "Statistics", "Data Processing"]),
            ("Data Platform Engineer", "Data & AI", ["Data Pipelines", "SQL", "Python", "Data Engineering"]),
            ("ML Research Associate", "Data & AI", ["Python", "Deep Learning", "Statistics", "Machine Learning"]),
        ]

        first_names = ["Ananya", "Vikram", "Tara", "Nikhil", "Deepa", "Siddharth", "Meera", "Karan", "Pooja", "Harsh", "Sneha", "Aditya", "Ritu", "Gaurav", "Simran", "Varun", "Isha", "Manish", "Divya", "Rahul", "Tanvi", "Amit", "Kritika", "Suresh", "Bhavna", "Jay", "Preeti", "Alok", "Pallavi", "Naveen"]
        last_names = ["Iyer", "Kapoor", "Nair", "Patel", "Reddy", "Choudhury", "Bose", "Menon", "Joshi", "Das", "Deshmukh", "Singhal", "Gupta", "Saxena", "Bhatia", "Sen", "Pillai", "Kulkarni", "Malhotra", "Shukla"]

        print("Generating 30 rich employee profiles...")
        for i in range(30):
            emp_id = f"EMP-{1030 + i}"
            fn = first_names[i % len(first_names)]
            ln = last_names[i % len(last_names)]
            full_name = f"{fn} {ln}"
            email = f"{fn.lower()}.{ln.lower()}@roleflow.io"
            base_role, dept, base_skills = roles_pool[i % len(roles_pool)]
            exp = round(random.uniform(1.8, 8.5), 1)

            e = Employee(
                id=emp_id,
                full_name=full_name,
                email=email,
                current_role=base_role,
                department=dept,
                experience_years=exp,
                bio=f"{base_role} with {exp} years of proven industry experience.",
                open_to_transfer=random.choice([True, True, True, False]),
                availability_days=random.choice([14, 21, 30, 45]),
                career_interests=[base_role, "AI / ML", "Engineering"],
                embedding=embed_texts([f"{base_role} {dept} {' '.join(base_skills)}"])[0],
            )
            db.session.add(e)

            # Add projects
            p = Project(
                id=f"prj-{emp_id}-1",
                employee_id=emp_id,
                name=f"{base_role} Core Initiative",
                description=f"Developed key modules using {', '.join(base_skills[:2])}.",
                role="Contributor",
                skills_used=base_skills[:3],
                status="completed" if i % 3 != 0 else "in_progress",
                completion_percentage=100 if i % 3 != 0 else 60,
                remaining_weeks=0 if i % 3 != 0 else 4,
            )
            db.session.add(p)

            for sk in base_skills:
                db.session.add(EmployeeSkill(
                    employee_id=emp_id,
                    skill_name=sk,
                    proficiency=random.randint(2, 5),
                    status=random.choice(["verified", "explicit"]),
                    evidence_id=f"prj-{emp_id}-1",
                    evidence_text=f"Demonstrated in {p.name}",
                ))

        print("Seeding sample roles (§44)...")
        roles_catalog = [
            (
                "role-ml-engineer",
                "ML Engineer",
                "Data & AI",
                "Design, build, and deploy production machine learning pipelines and real-time inference microservices.",
                """We are seeking a Machine Learning Engineer to design, deploy, and monitor scalable machine learning models and feature pipelines.
Requirements:
- 2+ years of professional experience in Python and Machine Learning
- Mandatory skills: Python, Machine Learning, SQL, Data Pipelines
- Preferred skills: MLOps, Model Deployment, System Design
- Experience training predictive models and deploying to production APIs
- Nice to have: TensorFlow Developer or Cloud ML certification""",
                2,
                2.0,
                ["Python", "Machine Learning", "SQL", "Data Pipelines"],
                ["MLOps", "Model Deployment", "System Design"],
                ["TensorFlow Developer Certificate"],
                [
                    "Train, evaluate, and fine-tune machine learning and predictive models",
                    "Build automated feature engineering and data processing pipelines",
                    "Deploy models with high-throughput REST APIs and monitor drift",
                ],
                "AI/ML",
                "visible",
            ),
            (
                "role-data-scientist",
                "Data Scientist",
                "Data & AI",
                "Develop predictive statistical and machine learning models for customer behavior and revenue forecasting.",
                """Seeking a Data Scientist to formulate predictive models, conduct exploratory statistical analysis, and drive decision intelligence.
Requirements:
- 2+ years experience with Python, SQL, Statistics, and Machine Learning
- Mandatory skills: Python, Statistics, Machine Learning, SQL
- Preferred skills: Predictive Modeling, Data Processing""",
                1,
                2.0,
                ["Python", "Statistics", "Machine Learning", "SQL"],
                ["Predictive Modeling", "Data Processing"],
                [],
                [
                    "Perform deep exploratory analysis and hypothesis testing",
                    "Develop statistical models for customer churn and demand forecasting",
                ],
                "AI/ML",
                "visible",
            ),
            (
                "role-data-analyst",
                "Data Analyst",
                "Data & AI",
                "Translate business questions into analytical dashboards and SQL aggregations.",
                "Seeking Data Analyst with SQL and Python.",
                2,
                1.5,
                ["SQL", "Python", "Data Processing"],
                ["Statistics"],
                [],
                ["Build analytics queries", "Deliver actionable metrics"],
                "Data",
                "visible",
            ),
            (
                "role-software-engineer",
                "Software Engineer",
                "Engineering",
                "Build scalable backend services and responsive full-stack interfaces.",
                "Full-stack software engineering with React and Python APIs.",
                3,
                2.0,
                ["Python", "React", "APIs"],
                ["Database", "Full Stack Development"],
                [],
                ["Develop clean APIs and web interfaces", "Maintain test coverage"],
                "Engineering",
                "visible",
            ),
            (
                "role-ai-engineer",
                "AI Engineer",
                "Data & AI",
                "Deploy agentic LLM workflows and neural search engines (Internal role).",
                "Internal strategic role for agentic architectures.",
                1,
                3.0,
                ["Python", "Machine Learning", "Deep Learning"],
                ["MLOps", "System Design"],
                [],
                ["Develop agentic LLM pipelines", "Build vector indexing"],
                "AI/ML",
                "hidden",  # Hidden role testing
            ),
        ]

        for r_id, title, dept, desc, jd, headcount, min_exp, mandatory, preferred, certs, resps, domain, vis in roles_catalog:
            r = Role(
                id=r_id,
                title=title,
                department=dept,
                description=desc,
                jd_text=jd,
                headcount=headcount,
                minimum_experience=min_exp,
                mandatory_skills=mandatory,
                preferred_skills=preferred,
                certifications=certs,
                responsibilities=resps,
                domain=domain,
                status="vacant",
                visibility=vis,
                last_discovered_at=datetime.now(timezone.utc),
                embedding=embed_texts([f"{title} {dept} {' '.join(mandatory)}"])[0],
            )
            db.session.add(r)

        db.session.commit()

        print("Populating high-volume synthetic records to reach ~10,000 employees (§42)...")
        # Generate lightweight synthetic records in bulk chunks
        CHUNK_SIZE = 2000
        TOTAL_SYNTHETIC = 10000
        current_count = Employee.query.count()
        needed = max(0, TOTAL_SYNTHETIC - current_count)

        if needed > 0:
            departments = ["Engineering", "Data & AI", "Product", "Quality Engineering", "Operations", "Information Security"]
            roles_list = [
                ("Associate Software Engineer", "Engineering"),
                ("Junior Data Analyst", "Data & AI"),
                ("QA Associate", "Quality Engineering"),
                ("Operations Specialist", "Operations"),
                ("Junior Developer", "Engineering"),
                ("Product Specialist", "Product"),
                ("Security Analyst", "Information Security"),
            ]
            
            for chunk_start in range(0, needed, CHUNK_SIZE):
                batch = []
                count = min(CHUNK_SIZE, needed - chunk_start)
                for j in range(count):
                    idx = current_count + chunk_start + j + 1
                    r_title, r_dept = random.choice(roles_list)
                    batch.append(Employee(
                        id=f"EMP-{10000 + idx}",
                        full_name=f"Employee {idx}",
                        email=f"employee.{idx}@roleflow.internal",
                        current_role=r_title,
                        department=r_dept,
                        experience_years=round(random.uniform(1.0, 7.0), 1),
                        bio="Internal team member.",
                        open_to_transfer=random.choice([True, False]),
                        availability_days=random.choice([15, 30, 60]),
                        career_interests=[r_title],
                    ))
                db.session.bulk_save_objects(batch)
                db.session.commit()
                print(f"  Indexed {chunk_start + count}/{needed} synthetic employees...")

        print("Pre-running initial discovery matching for demo roles...")
        from core.agents.matching import run_role_matching
        for r_id in ["role-ml-engineer", "role-data-scientist"]:
            candidates = run_role_matching(r_id, top_k=20)
            RoleCandidate.query.filter_by(role_id=r_id).delete()
            for cand in candidates:
                db.session.add(RoleCandidate(
                    role_id=r_id,
                    employee_id=cand["employee_id"],
                    fit_score=cand["fit_score"],
                    readiness_score=cand["readiness_score"],
                    fit_breakdown=cand["fit_breakdown"],
                    readiness_breakdown=cand["readiness_breakdown"],
                    top_skills=cand["top_skills"],
                    transferable_skills=cand["transferable_skills"],
                    ai_explanation=cand.get("ai_explanation", ""),
                    evidence_refs=cand.get("evidence_refs", []),
                    status="discovered",
                ))

        db.session.commit()
        print("RoleFlow seed complete! Total employees in DB:", Employee.query.count())


if __name__ == "__main__":
    reset_flag = "--reset" in sys.argv
    seed_database(reset=reset_flag)
