# RoleFlow — Agentic Internal Talent Mobility Platform

> **RoleFlow — Discover internal talent. Match roles intelligently. Close skill gaps. Enable internal mobility.**

RoleFlow is an agentic AI-powered internal talent mobility platform that analyzes employee skills, experience, projects, and learning history to discover suitable internal candidates for organizational roles, identify skill gaps, and recommend personalized learning paths.

---

## Actual Technology Stack

| Layer | Technology |
|---|---|
| Frontend | React 19 · Tailwind CSS · Vite · TanStack React Query · React Router |
| Backend | Python · Flask · Pydantic · JWT (flask-jwt-extended) · OAuth-ready |
| Data | PostgreSQL + pgvector · MongoDB |
| Async | Redis · Celery |
| Agentic AI | LangGraph · LangChain |
| AI / ML | GPT-OSS-120B · BGE-base / Sentence-BERT |
| Auth | OAuth · JWT |

---

## Running the Application

### 1. Backend (Single Entry Point)

```bash
cd backend
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

pip install -r requirements.txt
python seed.py --reset
python app.py
```

The Flask API runs at `http://localhost:5000/api/v1`.

### 2. Celery Worker (Async Candidate Discovery)

In a separate terminal:

```bash
cd backend
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

celery -A app.celery_app worker --loglevel=info
```

### 3. Frontend

In a separate terminal:

```bash
cd frontend
npm install
npm run dev
```

The Vite frontend runs at `http://localhost:5173`.

---

## Demo Accounts

All accounts use password: `demo1234`

| Persona | Email | Responsibility |
|---|---|---|
| **Manager** | `manager@roleflow.io` | Role creation, JD requirement review, candidate shortlisting |
| **Employee** | `employee@roleflow.io` | Visible opportunities, accept/decline, role preference, learning completion |
| **HR / Admin** | `hr@roleflow.io` | Workforce mobility governance, transfer review and final approval |

---

## Six Logical AI Agents

1. **Role Intelligence Agent**: Converts pasted JDs into structured, manager-editable requirements (mandatory/preferred skills, domain, minimum experience).
2. **Employee Intelligence Agent**: Understands employees beyond job titles — skills, verified project history, certifications, and availability.
3. **Transferable Skill Discovery Agent**: Maps capability bridges across skill families (e.g. Python → Data Processing → Machine Learning) backed by real project evidence.
4. **Internal Role Matching Agent**: Performs semantic retrieval and deterministic scoring on two independent axes: **Fit** (30% skills, 25% experience, 15% projects, 10% certs, 10% transferable, 10% domain) and **Readiness** (transfer willingness, career interest, availability, active project commitments).
5. **Skill Gap Agent**: Details strong, developing, and missing skills for shortlisted candidates.
6. **Learning & Career Agent**: Generates sequenced learning roadmaps using curated learning resources (Coursera, Udemy, NPTEL, Microsoft Learn, Internal Learning).

---

## Actual Business Workflow

```text
Manager creates role
        ↓
Role Intelligence Agent
        ↓
Employee Intelligence Agent
        ↓
Transferable Skill Discovery Agent
        ↓
Internal Role Matching Agent
        ↓
Fit + Readiness
        ↓
Top Candidates
        ↓
Skill Gap Agent
        ↓
Learning & Career Agent
        ↓
Manager shortlists
        ↓
Employee receives opportunity
        ↓
Employee accepts / declines
        ↓
HR reviews / approves transfer
```
