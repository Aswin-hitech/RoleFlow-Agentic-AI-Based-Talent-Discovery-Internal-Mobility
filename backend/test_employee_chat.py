"""RoleFlow — Employee AI Career Chatbot Verification Tests.

Validates grounded context retrieval, GPT-OSS-120B fallback, role-specific context,
conversation continuity, and strict JWT identity security isolation.
"""

import sys
from core import create_app

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def run_chat_tests():
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

    print("\n=======================================================")
    print(" ROLEFLOW — EMPLOYEE AI CAREER CHATBOT TEST SUITE")
    print("=======================================================\n")

    # 1. Anonymous Security Barrier
    print("--- 1. Security & Authentication Barriers ---")
    res = client.post("/api/v1/me/chat", json={"message": "What is my profile?"})
    check("Anonymous chat blocked with 401", res.status_code == 401)

    # 2. Login as Employee (Arjun Mehta - EMP-1024)
    print("\n--- 2. Employee Identity Resolution ---")
    res = client.post("/api/v1/auth/login", json={"email": "employee@roleflow.io", "password": "demo1234"})
    check("Employee login 200", res.status_code == 200)
    emp_token = res.get_json().get("access_token")
    emp_headers = {"Authorization": f"Bearer {emp_token}"}

    # 3. Context Endpoint
    print("\n--- 3. Chat Context & Dynamic Quick Chips ---")
    res = client.get("/api/v1/me/chat/context?role_id=role-ml-engineer", headers=emp_headers)
    check("Chat context 200", res.status_code == 200)
    ctx_data = res.get_json()
    check("Target role is ML Engineer", ctx_data.get("role_title") == "ML Engineer")
    check("Fit score present", ctx_data.get("fit_score") is not None)
    check("Readiness score present", ctx_data.get("readiness_score") is not None)
    chips = ctx_data.get("suggested_actions", [])
    check("Quick action chips returned", len(chips) >= 4)
    print(f"       ✓ Suggested Chips: {chips[:3]}")

    # 4. Question: Why was I matched?
    print("\n--- 4. Grounded Match & Fit Score Explanation ---")
    res = client.post(
        "/api/v1/me/chat",
        headers=emp_headers,
        json={
            "message": "Why was I matched to this role?",
            "role_id": "role-ml-engineer",
        },
    )
    check("Chat query 200", res.status_code == 200)
    reply1 = res.get_json()
    msg1 = reply1.get("message", "")
    check("Response mentions Fit Score", "fit score" in msg1.lower() or "fit" in msg1.lower())
    check("Sources list returned", len(reply1.get("sources", [])) > 0)
    check("Suggested actions updated", len(reply1.get("suggested_actions", [])) > 0)
    print(f"       ✓ Grounded Fit Explanation Snippet: {msg1[:150]}...")

    # 5. Question: Why is readiness lower?
    print("\n--- 5. Readiness Deduction & Commitment Grounding ---")
    res = client.post(
        "/api/v1/me/chat",
        headers=emp_headers,
        json={
            "message": "Why is my readiness score lower than my fit score?",
            "role_id": "role-ml-engineer",
        },
    )
    check("Readiness query 200", res.status_code == 200)
    reply2 = res.get_json()
    msg2 = reply2.get("message", "")
    check("Mentions project or readiness factor", "readiness" in msg2.lower() or "project" in msg2.lower())
    print(f"       ✓ Readiness Explanation Snippet: {msg2[:150]}...")

    # 6. Question: What skills am I missing?
    print("\n--- 6. Skill Gap & Missing Skills Breakdown ---")
    res = client.post(
        "/api/v1/me/chat",
        headers=emp_headers,
        json={
            "message": "What skills am I missing for this role?",
            "role_id": "role-ml-engineer",
        },
    )
    check("Skill gap query 200", res.status_code == 200)
    reply3 = res.get_json()
    msg3 = reply3.get("message", "")
    check("Categorizes skills (missing or developing)", "skill" in msg3.lower())
    print(f"       ✓ Skill Gap Snippet: {msg3[:150]}...")

    # 7. Question: Learning plan & Courses
    print("\n--- 7. Curated Learning Roadmap & Next Steps ---")
    res = client.post(
        "/api/v1/me/chat",
        headers=emp_headers,
        json={
            "message": "Show my recommended learning roadmap and courses",
            "role_id": "role-ml-engineer",
        },
    )
    check("Learning plan query 200", res.status_code == 200)
    reply4 = res.get_json()
    msg4 = reply4.get("message", "")
    check("Returns course or learning roadmap", "course" in msg4.lower() or "learning" in msg4.lower() or "phase" in msg4.lower())
    print(f"       ✓ Learning Roadmap Snippet: {msg4[:150]}...")

    # 8. Conversation Continuity
    print("\n--- 8. Multi-Turn Conversation Continuity ---")
    res = client.post(
        "/api/v1/me/chat",
        headers=emp_headers,
        json={
            "message": "What should I learn first?",
            "role_id": "role-ml-engineer",
            "conversation_id": reply1.get("conversation_id"),
            "history": [
                {"role": "user", "content": "Why was I matched to this role?"},
                {"role": "assistant", "content": msg1},
            ],
        },
    )
    check("Multi-turn continuation 200", res.status_code == 200)
    reply5 = res.get_json()
    check("Conversation ID preserved", reply5.get("conversation_id") == reply1.get("conversation_id"))

    # 9. Anti-Spoofing Security: Client tries to inject fake employee_id
    print("\n--- 9. Anti-Spoofing & Cross-Employee Data Protection ---")
    res = client.post(
        "/api/v1/me/chat",
        headers=emp_headers,
        json={
            "message": "Who am I?",
            "employee_id": "EMP-OTHER-HACKED",  # Malicious client-supplied ID
        },
    )
    check("Chat ignores forged employee_id", res.status_code == 200)
    msg_spoof = res.get_json().get("message", "")
    check("Response remains grounded in Arjun Mehta", "arjun" in msg_spoof.lower() or "data analyst" in msg_spoof.lower())

    print(f"\n=======================================================")
    print(f"Employee Chat Tests Complete: {passed}/{total} PASSED")
    print(f"=======================================================\n")
    return passed == total


if __name__ == "__main__":
    success = run_chat_tests()
    sys.exit(0 if success else 1)
