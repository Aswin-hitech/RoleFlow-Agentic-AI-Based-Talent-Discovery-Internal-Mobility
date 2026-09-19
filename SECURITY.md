# Security Policy & Vulnerability Management

RoleFlow treats workforce data confidentiality, model integrity, and tenant isolation as mission-critical enterprise commitments. This document describes our security architecture, supported versions, vulnerability disclosure procedures, and compliance safeguards.

---

## 1. Supported Versions

Security updates and critical patches are actively provided for the following releases:

| Version | Supported | Security Maintenance Level |
| :--- | :---: | :--- |
| **1.2.x** | :white_check_mark: | Active support (Current Production Release) |
| **1.1.x** | :white_check_mark: | Critical security patches only |
| **< 1.1.0**| :x: | End of Life (Upgrade recommended) |

---

## 2. Reporting a Vulnerability

If you discover a security vulnerability, please do **NOT** file a public GitHub issue.

Please follow these responsible disclosure procedures:
1. **Email Disclosure**: Report all security findings to `security@roleflow.io` (or the project maintainers directly).
2. **Details to Include**:
   - Component / Endpoint affected (e.g. `/api/v1/me/chat`, `backend/core/security/rbac.py`)
   - Type of vulnerability (e.g. privilege escalation, broken access control, prompt injection, SSRF, SQLi)
   - Step-by-step reproduction steps or minimal proof-of-concept (PoC)
   - Potential impact on enterprise workforce records
3. **SLA & Response Commitment**:
   - Initial acknowledgement: within **24 hours**.
   - Severity triage & impact assessment: within **72 hours**.
   - Remediation patch & release: within **7 business days** (or 48 hours for critical severity).

---

## 3. Core Security Architecture & Threat Model

RoleFlow implements defense-in-depth principles across its application, data, and agent layers:

### 3.1 Zero-Trust Authentication & RBAC
- **Cryptographic Tokens**: JSON Web Tokens (JWT) signed via HMAC-SHA256 (`flask-jwt-extended`) with explicit role claims (`manager`, `employee`, `hr`, `admin`).
- **Endpoint Enforcement**: Every route is guarded with `@jwt_required()` and fine-grained `@roles_required(*roles)` decorators.
- **Strict Server-Side Identity**: Employee endpoints (`/api/v1/me/*`) derive the active employee ID solely from verified token claims via `_get_current_employee_id()`. Client-supplied `employee_id` parameters in request bodies are explicitly ignored and discarded to prevent identity spoofing.

### 3.2 Confidential Role & Candidate Isolation
- Hidden, draft, or inactive roles (`visibility="hidden"`) are strictly filtered at the database level and never exposed to the Employee Portal or Career Assistant contexts (§25, §37).
- Cross-employee data access is prohibited; an employee can only query their own verified skills, opportunities, learning roadmaps, and chat history.

### 3.3 Rate Limiting & DoS Protection
- High-performance, in-memory sliding-window rate limiters protect public and high-compute endpoints without introducing external broker dependencies:
  - Authentication (`/api/v1/auth/login`): **10 requests / minute**
  - AI Matching & Discovery: **20 requests / minute**
  - Web Crawlers (`/api/v1/crawler/*`): **30 requests / minute**
  - General API: **120 requests / minute**

### 3.4 Production Secrets & Demo Account Hardening
- In production (`FLASK_ENV=production`), application startup verifies that `JWT_SECRET_KEY` and `SECRET_KEY` are explicitly configured from environment variables. Insecure fallback strings trigger immediate warnings/errors.
- Default demo credentials (`demo1234`) are strictly disabled outside development unless explicitly permitted via `ALLOW_DEMO_USERS=true`.

### 3.5 AI & LLM Safety Guardrails
- **Prompt Sanitization**: Inbound conversational inputs are bounded to 4,000 characters; conversation history is capped at 6 turns to prevent memory bloat and context window exhaustion.
- **Zero-Hallucination Grounding**: Large Language Models never set numeric scores. Scoring is 100% deterministic in Python.
- **Anti-Prompt Injection**: The AI Career Assistant operates under a strict anti-hallucination system prompt that prohibits revealing system prompts, inventing skills, or accessing out-of-scope candidate records.

### 3.6 Data Privacy & Compliance
- **GDPR Article 22 Compliance**: Automated talent scoring provides full transparency (`fit_breakdown` and `readiness_breakdown`). Employees have the right to decline opportunities and request human review.
- **Audit Logging**: All transfer state transitions, shortlists, and score overrides are immutably logged with actor, timestamp, and justification notes to both MongoDB and relational audit tables.
- **PII Anonymization**: Vector embeddings are computed from technical roles, skills, and sanitized project competencies rather than sensitive demographic or personal identifiable information.
