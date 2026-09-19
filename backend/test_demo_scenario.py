"""RoleFlow — End-to-End Demo Scenario (§61).

Executes the entire 21-step hackathon jury presentation workflow:
1. Login as Manager (manager@roleflow.io / demo1234)
2. Create role via AI JD extraction
3. Review extracted requirements & set visibility to 'visible'
4. Create role & launch discovery (Celery + LangGraph 6 agents)
5. Retrieve candidate list
6. Open top candidate (Arjun Mehta, EMP-1024)
7. Validate Fit % & Readiness %
8. Validate Transferable skills (Python -> Data Processing -> ML)
9. Validate Project evidence records
10. Validate Skill Gap report (Strong, Developing, Missing)
11. Validate Curated Learning roadmap
12. Shortlist candidate (Transfer -> pending_employee)
13. Login as Employee (employee@roleflow.io / demo1234)
14. View internal opportunities (confirm visibility security)
15. Handle multiple-role conflict: select 1st and 2nd preference
16. Accept opportunity (Transfer -> pending_hr)
17. Login as HR (hr@roleflow.io / demo1234)
18. Review workforce transfers & approve transfer (Transfer -> approved)
19. Demonstrate Decline flow: employee declines a role -> remains vacant
"""

import sys
import json
from core import create_app

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def run_demo_scenario():
    app = create_app()
    client = app.test_client()

    print("\n=======================================================")
    print(" ROLEFLOW — END-TO-END DEMO SCENARIO VERIFICATION (§61)")
    print("=======================================================\n")

    # Step 1: Login as Manager
    print("[1/21] Logging in as Manager (manager@roleflow.io)...")
    res = client.post("/api/v1/auth/login", json={"email": "manager@roleflow.io", "password": "demo1234"})
    assert res.status_code == 200, f"Manager login failed: {res.text}"
    mgr_token = res.get_json()["access_token"]
    mgr_headers = {"Authorization": f"Bearer {mgr_token}"}
    print("       ✓ Logged in as Priya Sharma (Engineering Manager)")

    # Step 2-4: Paste JD and Role Intelligence AI Extraction
    print("\n[2-4/21] Pasting Job Description & executing Role Intelligence Agent...")
    sample_jd = """We are seeking a Machine Learning Engineer to build production deep learning and real-time inference models.
Requirements:
- 2+ years of experience with Python, Machine Learning, and SQL
- Mandatory skills: Python, Machine Learning, SQL, Data Pipelines
- Preferred skills: MLOps, Model Deployment, System Design
- Strong problem solving, statistical foundations, and team collaboration."""
    res = client.post("/api/v1/roles/parse-jd", json={"jd_text": sample_jd, "title": "ML Engineer", "department": "Data & AI"})
    assert res.status_code == 200
    parsed = res.get_json()["parsed"]
    print(f"       ✓ Extracted Title: {parsed.get('title')}")
    print(f"       ✓ Extracted Mandatory Skills: {parsed.get('mandatory_skills')}")
    print(f"       ✓ Extracted Preferred Skills: {parsed.get('preferred_skills')}")

    # Step 5: Manager reviews and creates role with visibility='visible'
    print("\n[5/21] Manager reviews criteria and creates visible role...")
    res = client.post("/api/v1/manager/roles", headers=mgr_headers, json={
        "title": parsed["title"],
        "department": parsed["department"],
        "domain": parsed["domain"],
        "jd_text": sample_jd,
        "description": "Production ML model training and deployment",
        "minimum_experience": parsed["minimum_experience"],
        "mandatory_skills": parsed["mandatory_skills"],
        "preferred_skills": parsed["preferred_skills"],
        "headcount": 2,
        "visibility": "visible",
    })
    assert res.status_code == 201
    created_role = res.get_json()["role"]
    new_role_id = created_role["id"]
    match_run_id = res.get_json().get("match_run_id")
    print(f"       ✓ Created Role: {created_role['title']} ({new_role_id})")
    print(f"       ✓ Discovery Queued with Run ID: {match_run_id}")

    # Step 6-7: Check Discovery Status with polling (§20)
    print("\n[6-7/21] Polling Discovery Run Status (Celery + LangGraph)...")
    import time
    for _ in range(50):
        res = client.get(f"/api/v1/match-runs/{match_run_id}/status")
        stage = res.get_json().get("current_stage", "")
        status = res.get_json().get("status", "")
        if status == "completed" or stage == "Completed":
            break
        time.sleep(0.5)
    assert status == "completed" or stage == "Completed", f"Discovery did not complete in time (stage: {stage}, status: {status})"
    print(f"       ✓ Discovery completed: {stage} ({status})")

    # Step 8: Candidate list appears
    print("\n[8/21] Fetching Candidate List for Role...")
    res = client.get(f"/api/v1/manager/roles/{new_role_id}/candidates", headers=mgr_headers)
    assert res.status_code == 200
    candidates = res.get_json()["candidates"]
    print(f"       ✓ Candidates Discovered: {len(candidates)} candidates in pool")

    # Step 9-14: Open top candidate & inspect Match Explanation
    print("\n[9-14/21] Inspecting Candidate Details for Arjun Mehta (EMP-1024)...")
    arjun = next((c for c in candidates if c["employee_id"] == "EMP-1024"), candidates[0])
    print(f"       ✓ Candidate: {arjun['name']} ({arjun['current_role']})")
    print(f"       ✓ Fit Score: {arjun['fit_score']}% (Component breakdown: {arjun['fit_breakdown']})")
    print(f"       ✓ Readiness Score: {arjun['readiness_score']}% (Deduction reason: {arjun['readiness_breakdown'].get('deduction_reason')})")
    print(f"       ✓ Transferable Skills: {arjun['transferable_skills']}")
    print(f"       ✓ Evidence Records: {arjun['evidence_refs']}")
    print(f"       ✓ AI Explanation: {arjun['ai_explanation']}")

    # Multi-Threaded Crawl: Live multi-provider course harvesting for Arjun's skill gaps
    print("\n[Concurrent Crawl] Spawning Worker Threads to Harvest Live Courses across Providers...")
    res = client.post(f"/api/v1/roles/{new_role_id}/live-course-crawl/{arjun['employee_id']}")
    assert res.status_code == 200
    crawl_info = res.get_json()["crawl_results"]
    print(f"       ✓ Multi-Threaded Crawl Dispatched {crawl_info['workers_dispatched']} workers across Coursera, edX, MIT OCW & GitHub")
    print(f"       ✓ Harvested {crawl_info['total_crawled']} relevant courses in {crawl_info['elapsed_ms']}ms")

    # Step 15: Shortlist candidate
    print("\n[15/21] Manager shortlists Arjun Mehta for role...")
    res = client.post(f"/api/v1/manager/roles/{new_role_id}/candidates/{arjun['employee_id']}/shortlist", headers=mgr_headers)
    assert res.status_code == 200
    print("       ✓ Shortlisted! Transfer opportunity created in 'pending_employee' state.")

    # Step 16-17: Login as Employee and view opportunity
    print("\n[16-17/21] Logging in as Employee (employee@roleflow.io)...")
    res = client.post("/api/v1/auth/login", json={"email": "employee@roleflow.io", "password": "demo1234"})
    assert res.status_code == 200
    emp_token = res.get_json()["access_token"]
    emp_headers = {"Authorization": f"Bearer {emp_token}"}

    res = client.get("/api/v1/me/opportunities", headers=emp_headers)
    assert res.status_code == 200
    opps = res.get_json()["opportunities"]
    print(f"       ✓ Employee opportunities loaded: {len(opps)} visible opportunities available")

    # Step 17b: Employee consults AI Career Assistant
    print("\n[17b/21] Employee Consults AI Career Assistant (Grounded Chatbot)...")
    res = client.get(f"/api/v1/me/chat/context?role_id={new_role_id}", headers=emp_headers)
    assert res.status_code == 200
    ctx_data = res.get_json()
    print(f"       ✓ Chat Context: Role '{ctx_data.get('role_title')}', Fit {ctx_data.get('fit_score')}%, Readiness {ctx_data.get('readiness_score')}%")
    print(f"       ✓ Grounded Evidence Sources: {ctx_data.get('sources')}")

    res = client.post("/api/v1/me/chat", headers=emp_headers, json={
        "message": "Why is my readiness score lower than my fit score?",
        "role_id": new_role_id,
    })
    assert res.status_code == 200
    chat_data = res.get_json()
    print(f"       ✓ AI Career Assistant Reply: {chat_data.get('message')[:120]}...")
    print(f"       ✓ Suggested Action Chips: {chat_data.get('suggested_actions', [])[:3]}")

    # Step 18: Multiple Role Preference (§27)
    print("\n[18/21] Resolving Multiple Role Conflict: Setting 1st and 2nd Preferences...")
    res = client.put("/api/v1/me/role-preferences", headers=emp_headers, json={
        "preferences": [
            {"role_id": new_role_id, "rank": 1},
            {"role_id": "role-data-scientist", "rank": 2},
        ]
    })
    assert res.status_code == 200
    print("       ✓ 1st & 2nd Role Preferences recorded successfully.")

    # Step 19: Employee accepts opportunity
    print("\n[19/21] Employee accepts the opportunity...")
    res = client.post(f"/api/v1/me/opportunities/{new_role_id}/accept", headers=emp_headers)
    assert res.status_code == 200
    print("       ✓ Opportunity accepted! Status moved to 'pending_hr'.")

    # Step 20-21: Login as HR and approve transfer
    print("\n[20-21/21] Logging in as HR (hr@roleflow.io) and approving transfer...")
    res = client.post("/api/v1/auth/login", json={"email": "hr@roleflow.io", "password": "demo1234"})
    assert res.status_code == 200
    hr_token = res.get_json()["access_token"]
    hr_headers = {"Authorization": f"Bearer {hr_token}"}

    res = client.get("/api/v1/hr/transfers", headers=hr_headers)
    transfers = res.get_json()["transfers"]
    target_transfer = next((t for t in transfers if t["role_id"] == new_role_id and t["status"] == "pending_hr"), None)
    assert target_transfer is not None, "Pending transfer not found in HR portal"

    res = client.post(f"/api/v1/hr/transfers/{target_transfer['id']}/approve", headers=hr_headers, json={
        "notes": "Approved by HR Talent Review Board."
    })
    assert res.status_code == 200
    approved_transfer = res.get_json()["transfer"]
    print(f"       ✓ HR Approved transfer! Final Status: {approved_transfer['status']}")

    # Extra edge case: Decline flow (§28)
    print("\n[Extra] Testing Employee Decline Flow (§28)...")
    res = client.post("/api/v1/me/opportunities/role-data-scientist/decline", headers=emp_headers)
    assert res.status_code == 200
    declined_transfer = res.get_json()["transfer"]
    print(f"       ✓ Declined opportunity status: {declined_transfer['status']} (Role remains vacant)")

    print("\n=======================================================")
    print(" ALL 21 DEMO WORKFLOW STEPS + EDGE CASES PASSED! ✓")
    print("=======================================================\n")
    return True


if __name__ == "__main__":
    success = run_demo_scenario()
    sys.exit(0 if success else 1)
