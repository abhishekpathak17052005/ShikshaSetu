#!/usr/bin/env python3
"""
Live Cloud Deployment Smoke Test Suite for ShikshaSetu.

Usage:
  python backend/scripts/verify_deployed_system.py --backend-url https://shikshasetu-backend.onrender.com
"""

import argparse
import sys
import requests


def run_smoke_test(backend_url: str) -> bool:
    api_base = backend_url.rstrip("/")
    if not api_base.endswith("/api/v1"):
        api_base = f"{api_base}/api/v1"

    print("=" * 70)
    print(f"SHIKSHASETU: LIVE CLOUD DEPLOYMENT SMOKE TEST")
    print(f"Target API Base: {api_base}")
    print("=" * 70)

    passed = 0
    total = 0

    # 1. Healthcheck
    total += 1
    print("\n[TEST 1] Testing System Health (/health)...")
    try:
        res = requests.get(f"{api_base}/health", timeout=15)
        if res.status_code == 200 and res.json().get("status") in ("healthy", "ok"):
            print(f"  ✓ PASS: System is healthy ({res.json()})")
            passed += 1
        else:
            print(f"  ✗ FAIL: Status code {res.status_code}, response: {res.text}")
    except Exception as e:
        print(f"  ✗ ERROR: {e}")

    # 2. Authentication for 3 Demo Accounts
    tokens = {}
    demo_accounts = [
        ("OFFICIAL", "officer@shikshasetu.gov.in", "Password@123"),
        ("TRAINER", "trainer@shikshasetu.gov.in", "Password@123"),
        ("ADMIN", "admin@shikshasetu.gov.in", "Password@123"),
    ]

    for role, email, password in demo_accounts:
        total += 1
        print(f"\n[TEST] Authenticating {role} ({email})...")
        try:
            res = requests.post(
                f"{api_base}/auth/login",
                data={"username": email, "password": password},
                timeout=15,
            )
            if res.status_code == 200:
                data = res.json()
                token = data.get("access_token")
                tokens[role] = token
                print(f"  ✓ PASS: Authenticated {role} successfully (token acquired)")
                passed += 1
            else:
                print(f"  ✗ FAIL: Status code {res.status_code}, response: {res.text}")
        except Exception as e:
            print(f"  ✗ ERROR: {e}")

    # 3. Official Role Operations
    if "OFFICIAL" in tokens:
        official_headers = {"Authorization": f"Bearer {tokens['OFFICIAL']}"}
        
        # Skill Gaps
        total += 1
        print("\n[TEST] Official: Fetching Skill Gaps (/skill-gaps/me)...")
        try:
            res = requests.get(f"{api_base}/skill-gaps/me", headers=official_headers, timeout=15)
            if res.status_code == 200 and "gaps" in res.json():
                print(f"  ✓ PASS: Retrieved {len(res.json()['gaps'])} skill gaps")
                passed += 1
            else:
                print(f"  ✗ FAIL: Status code {res.status_code}, response: {res.text}")
        except Exception as e:
            print(f"  ✗ ERROR: {e}")

        # Assistant Chat
        total += 1
        print("\n[TEST] Official: Testing Karmayogi AI Co-Pilot (/assistant/chat)...")
        try:
            res = requests.post(
                f"{api_base}/assistant/chat",
                headers=official_headers,
                json={"message": "What are my highest priority capability deficits?", "context_page": "Dashboard"},
                timeout=25,
            )
            if res.status_code == 200 and "answer" in res.json():
                print(f"  ✓ PASS: Co-Pilot responded with {len(res.json()['sources'])} sources")
                passed += 1
            else:
                print(f"  ✗ FAIL: Status code {res.status_code}, response: {res.text}")
        except Exception as e:
            print(f"  ✗ ERROR: {e}")

    # 4. Trainer Role Operations
    if "TRAINER" in tokens:
        trainer_headers = {"Authorization": f"Bearer {tokens['TRAINER']}"}
        
        total += 1
        print("\n[TEST] Trainer: Fetching Materials (/trainer/materials)...")
        try:
            res = requests.get(f"{api_base}/trainer/materials", headers=trainer_headers, timeout=15)
            if res.status_code == 200:
                print(f"  ✓ PASS: Retrieved trainer materials list")
                passed += 1
            else:
                print(f"  ✗ FAIL: Status code {res.status_code}, response: {res.text}")
        except Exception as e:
            print(f"  ✗ ERROR: {e}")

    # 5. Admin Role Operations
    if "ADMIN" in tokens:
        admin_headers = {"Authorization": f"Bearer {tokens['ADMIN']}"}
        
        total += 1
        print("\n[TEST] Admin: Fetching Dashboard Analytics (/admin/dashboard)...")
        try:
            res = requests.get(f"{api_base}/admin/dashboard", headers=admin_headers, timeout=15)
            if res.status_code == 200 and "total_users" in res.json():
                print(f"  ✓ PASS: Retrieved admin dashboard (Total users: {res.json()['total_users']}, Avg level: {res.json()['average_capability_level']})")
                passed += 1
            else:
                print(f"  ✗ FAIL: Status code {res.status_code}, response: {res.text}")
        except Exception as e:
            print(f"  ✗ ERROR: {e}")

    # 6. Security, RBAC Role Guards & Isolation Verification
    print("\n[SECURITY & RBAC ISOLATION CHECKS]")
    print("-" * 60)

    # 6a. Unauthenticated Access -> 401
    total += 1
    print("\n[TEST] Security: Unauthenticated request to /admin/dashboard...")
    try:
        res = requests.get(f"{api_base}/admin/dashboard", timeout=15)
        if res.status_code == 401:
            print(f"  ✓ PASS: Correctly rejected with HTTP 401 Unauthorized")
            passed += 1
        else:
            print(f"  ✗ FAIL: Expected 401, got {res.status_code}")
    except Exception as e:
        print(f"  ✗ ERROR: {e}")

    # 6b. Official accessing Admin API -> 403
    if "OFFICIAL" in tokens:
        total += 1
        print("\n[TEST] Security: Official role attempting to access /admin/dashboard...")
        try:
            res = requests.get(f"{api_base}/admin/dashboard", headers={"Authorization": f"Bearer {tokens['OFFICIAL']}"}, timeout=15)
            if res.status_code == 403:
                print(f"  ✓ PASS: Correctly blocked with HTTP 403 Forbidden")
                passed += 1
            else:
                print(f"  ✗ FAIL: Expected 403, got {res.status_code}")
        except Exception as e:
            print(f"  ✗ ERROR: {e}")

    # 6c. Trainer accessing Admin API -> 403
    if "TRAINER" in tokens:
        total += 1
        print("\n[TEST] Security: Trainer role attempting to access /admin/dashboard...")
        try:
            res = requests.get(f"{api_base}/admin/dashboard", headers={"Authorization": f"Bearer {tokens['TRAINER']}"}, timeout=15)
            if res.status_code == 403:
                print(f"  ✓ PASS: Correctly blocked with HTTP 403 Forbidden")
                passed += 1
            else:
                print(f"  ✗ FAIL: Expected 403, got {res.status_code}")
        except Exception as e:
            print(f"  ✗ ERROR: {e}")

    # 6d. Invalid credentials -> 401
    total += 1
    print("\n[TEST] Security: Authentication with invalid password...")
    try:
        res = requests.post(f"{api_base}/auth/login", data={"username": "officer@shikshasetu.gov.in", "password": "WrongPassword999!"}, timeout=15)
        if res.status_code == 401:
            print(f"  ✓ PASS: Correctly rejected invalid credentials with HTTP 401")
            passed += 1
        else:
            print(f"  ✗ FAIL: Expected 401, got {res.status_code}")
    except Exception as e:
        print(f"  ✗ ERROR: {e}")

    print("\n" + "=" * 70)
    print(f"SMOKE TEST SUMMARY: {passed}/{total} Passed")
    print("=" * 70)
    return passed == total


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Live Deployed Smoke Test for ShikshaSetu")
    parser.add_argument(
        "--backend-url",
        default="https://shikshasetu-backend.onrender.com",
        help="Base URL of the deployed backend service",
    )
    args = parser.parse_args()
    success = run_smoke_test(args.backend_url)
    sys.exit(0 if success else 1)
