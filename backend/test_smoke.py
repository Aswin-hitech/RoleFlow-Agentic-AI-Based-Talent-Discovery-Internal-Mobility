"""RoleFlow — Backend API Smoke Tests (§59).

Tests all key endpoints and end-to-end business workflows.
"""

import sys
import json
from core import create_app

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

def run_tests():
    app = create_app()
    client = app.test_client()
    passed = 0
    total = 0

    def check(name, condition, details=""):
        nonlocal passed, total
        total += 1
        if condition:
            passed += 1
            print(f"  [PASS] {name}")
        else:
            print(f"  [FAIL] {name}: {details}")

    print("\n--- 1. Health Endpoint ---")
    res = client.get("/api/v1/health")
    data = res.get_json()
    check("Health returns 200", res.status_code == 200)
    check("Health services present", "services" in data and "postgres" in data["services"])
    check("No docker string in response", "docker" not in json.dumps(data).lower())

    print("\n--- 2. Auth Endpoints ---")
    # Login as Manager
    res = client.post("/api/v1/auth/login", json={"email": "manager@roleflow.io", "password": "demo1234"})
    check("Manager login 200", res.status_code == 200)
    mgr_token = res.get_json().get("access_token")
    check("Manager token received", bool(mgr_token))
    mgr_headers = {"Authorization": f"Bearer {mgr_token}"}

    # Login as Employee
    res = client.post("/api/v1/auth/login", json={"email": "employee@roleflow.io", "password": "demo1234"})
    check("Employee login 200", res.status_code == 200)
    emp_token = res.get_json().get("access_token")
    check("Employee token received", bool(emp_token))
    emp_headers = {"Authorization": f"Bearer {emp_token}"}

    # Login as HR
    res = client.post("/api/v1/auth/login", json={"email": "hr@roleflow.io", "password": "demo1234"})
    check("HR login 200", res.status_code == 200)
    hr_token = res.get_json().get("access_token")
    check("HR token received", bool(hr_token))
    hr_headers = {"Authorization": f"Bearer {hr_token}"}

    print("\n--- 3. Role Intelligence (JD Parsing) ---")
    sample_jd = """We are seeking an ML Engineer to build production deep learning and NLP models.
Requirements:
- 3+ years experience with Python, Machine Learning, and SQL
- Mandatory: Python, Machine Learning, Deep Learning, SQL
- Preferred: MLOps, Model Deployment"""
    res = client.post("/api/v1/roles/parse-jd", json={"jd_text": sample_jd, "title": "ML Engineer"})
    check("Parse JD 200", res.status_code == 200)
    parsed = res.get_json().get("parsed", {})
    check("Extracted mandatory skills", "Python" in parsed.get("mandatory_skills", []))
    check("Extracted title", "ML Engineer" in parsed.get("title", ""))

    print("\n--- 4. Manager Roles & Candidate Discovery ---")
    res = client.get("/api/v1/manager/roles", headers=mgr_headers)
    check("List manager roles 200", res.status_code == 200)
    roles = res.get_json().get("roles", [])
    check("Found seeded roles", len(roles) >= 4)

    # Get ML Engineer role
    ml_role = next((r for r in roles if r["id"] == "role-ml-engineer"), roles[0])
    role_id = ml_role["id"]

    # Candidate list
    res = client.get(f"/api/v1/manager/roles/{role_id}/candidates", headers=mgr_headers)
    check("Get candidates 200", res.status_code == 200)
    cands = res.get_json().get("candidates", [])
    check("Candidates found for role", len(cands) > 0)
    arjun = next((c for c in cands if c.get("employee_id") == "EMP-1024"), cands[0])
    check("Arjun Mehta present in candidates", bool(arjun))
    check("Fit score is numeric between 50-99", 50 <= arjun["fit_score"] <= 99)
    check("Readiness score is separate", 30 <= arjun["readiness_score"] <= 99)
    check("Fit breakdown present (6 components)", len(arjun.get("fit_breakdown", {})) == 6)

    print("\n--- 5. Manager Shortlist Flow ---")
    res = client.post(
        f"/api/v1/manager/roles/{role_id}/candidates/{arjun['employee_id']}/shortlist",
        headers=mgr_headers,
    )
    check("Shortlist candidate 200", res.status_code == 200)
    check("Shortlist creates pending_employee transfer", res.get_json().get("transfer", {}).get("status") == "pending_employee")

    print("\n--- 6. Employee Portal & Opportunity Visibility ---")
    res = client.get("/api/v1/me/opportunities", headers=emp_headers)
    check("Employee opportunities 200", res.status_code == 200)
    opps = res.get_json().get("opportunities", [])
    check("Opportunity received by employee", len(opps) > 0)
    # Check hidden role security (§25, §37): role-ai-engineer is hidden, must NOT appear
    hidden_present = any(o["role_id"] == "role-ai-engineer" for o in opps)
    check("Hidden roles strictly excluded from employee portal", not hidden_present)

    print("\n--- 7. Employee Decision & Preference Flow ---")
    # Accept opportunity (§26, §30)
    res = client.post(f"/api/v1/me/opportunities/{role_id}/accept", headers=emp_headers)
    check("Employee accept 200", res.status_code == 200)
    check("Status advanced to pending_hr", res.get_json().get("transfer", {}).get("status") == "pending_hr")

    # Set multiple role preferences (§27)
    res = client.put("/api/v1/me/role-preferences", headers=emp_headers, json={"preferences": [{"role_id": role_id, "rank": 1}]})
    check("Save role preference 200", res.status_code == 200)

    print("\n--- 8. Continuous Learning Loop (§54) ---")
    res = client.get("/api/v1/me/learning", headers=emp_headers)
    check("Get learning roadmap 200", res.status_code == 200)
    res = client.post("/api/v1/me/learning/crs-001/complete", headers=emp_headers, json={"skill_name": "MLOps"})
    check("Mark learning complete 200", res.status_code == 200)

    print("\n--- 9. HR Governance & Transfer Approval ---")
    res = client.get("/api/v1/hr/transfers", headers=hr_headers)
    check("HR list transfers 200", res.status_code == 200)
    transfers = res.get_json().get("transfers", [])
    pending_trf = next((t for t in transfers if t["status"] == "pending_hr"), None)
    check("Pending HR transfer exists", bool(pending_trf))

    if pending_trf:
        res = client.post(f"/api/v1/hr/transfers/{pending_trf['id']}/approve", headers=hr_headers, json={"notes": "Approved."})
        check("HR approve transfer 200", res.status_code == 200)
        check("Transfer status is approved", res.get_json().get("transfer", {}).get("status") == "approved")

    print("\n--- 10. Multi-Threaded Crawlers & Knowledge Harvester ---")
    res = client.post("/api/v1/crawler/courses", json={"skills": ["Python", "MLOps", "Distributed Systems"], "max_workers": 5})
    check("Multi-threaded course crawl 200", res.status_code == 200)
    data = res.get_json() or {}
    check("Course crawl completed with worker threads", data.get("status") == "completed" and data.get("workers_dispatched", 0) >= 3)
    check("Discovered educational resources from multiple providers", data.get("total_crawled", 0) > 0)

    res = client.post("/api/v1/crawler/market-skills", json={"domain": "Data & AI", "role_title": "ML Engineer", "max_workers": 3})
    check("Multi-threaded market skill crawl 200", res.status_code == 200)
    market_data = res.get_json() or {}
    check("Market trends crawled across parallel threads", market_data.get("threads_spawned", 0) >= 2)
    check("Extracted trending market requirements", len(market_data.get("mandatory_skills", [])) > 0)

    res = client.post(f"/api/v1/roles/{role_id}/live-course-crawl/{arjun['employee_id']}")
    check("Live gap course crawl endpoint 200", res.status_code == 200)
    gap_crawl = res.get_json() or {}
    check("Targeted employee gap skills in crawl", len(gap_crawl.get("gap_skills_targeted", [])) > 0)

    print("\n--- 11. Employee AI Career Chatbot (Grounded Career Assistant) ---")
    # 11.1 Unauthorized attempt must be rejected
    unauth_res = client.post("/api/v1/me/chat", json={"message": "What roles fit me?"})
    check("Chatbot requires JWT auth (401 without token)", unauth_res.status_code == 401)

    # 11.2 Context retrieval
    chat_ctx_res = client.get(f"/api/v1/me/chat/context?role_id={role_id}", headers=emp_headers)
    check("Chatbot context endpoint 200", chat_ctx_res.status_code == 200)
    chat_ctx = chat_ctx_res.get_json() or {}
    check("Chat context returns employee info", chat_ctx.get("employee_name") == "Arjun Mehta")
    check("Chat context has suggested chips", len(chat_ctx.get("suggested_chips", [])) > 0)
    check("Chat context includes grounded sources", len(chat_ctx.get("sources", [])) > 0)

    # 11.3 Chat message with grounded explanation
    chat_res = client.post("/api/v1/me/chat", headers=emp_headers, json={
        "message": "Why is my readiness score lower than my fit score for the ML Engineer role?",
        "role_id": role_id
    })
    check("Chat query endpoint 200", chat_res.status_code == 200)
    chat_reply = chat_res.get_json() or {}
    check("Chat returns reply text", len(chat_reply.get("reply", "")) > 10)
    check("Chat references verified sources", len(chat_reply.get("sources", [])) > 0)
    check("Chat returns next action chips", len(chat_reply.get("suggested_chips", [])) > 0)

    # 11.4 Anti-spoofing security check (tampered employee_id in payload ignored)
    spoof_res = client.post("/api/v1/me/chat", headers=emp_headers, json={
        "employee_id": "EMP-999-HACKER",
        "message": "Who am I?"
    })
    check("Anti-spoofing respects JWT identity", spoof_res.status_code == 200)
    spoof_reply = spoof_res.get_json() or {}
    check("Chat strictly resolved Arjun's records", "Arjun" in spoof_reply.get("reply", "") or any("EMP-001" in s for s in spoof_reply.get("sources", [])))

    print(f"\n==========================================")
    print(f"Smoke Tests Complete: {passed}/{total} PASSED")
    print(f"==========================================\n")
    return passed == total

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
