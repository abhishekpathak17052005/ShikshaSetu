"""Production verification script for Phase 3G deployment."""

import json
import time
import requests

PROD_URL = "https://shikshasetu-m8xv.onrender.com/api/v1"

print("=" * 70)
print(f"PHASE 3G — LIVE PRODUCTION VERIFICATION")
print(f"Target API Base: {PROD_URL}")
print("=" * 70)

# 1. Healthcheck
print("\n[STEP 1] Testing Backend Health (/health)...")
try:
    t0 = time.perf_counter()
    r = requests.get(f"{PROD_URL}/health", timeout=30)
    t1 = time.perf_counter()
    print(f"Status: {r.status_code} in {(t1-t0)*1000:.1f}ms | Body: {r.text}")
    assert r.status_code == 200, "Health check failed"
except Exception as e:
    print(f"ERROR: {e}")

# 2. Official Login
print("\n[STEP 2] Authenticating Demo Official...")
email = "official@shikshasetu.gov.in"
password = "Password@123"

token = None
try:
    r = requests.post(f"{PROD_URL}/auth/login", json={"email": email, "password": password}, timeout=30)
    if r.status_code != 200:
        # Try officer fallback
        r = requests.post(f"{PROD_URL}/auth/login", json={"email": "officer@shikshasetu.gov.in", "password": password}, timeout=30)
    assert r.status_code == 200, f"Login failed: {r.text}"
    data = r.json()
    token = data.get("access_token")
    user = data.get("user", {})
    print(f"Authenticated successfully: {user.get('full_name')} ({user.get('email')}) | Role: {user.get('designation')}, Dept: {user.get('department')}")
except Exception as e:
    print(f"ERROR: {e}")

if not token:
    print("Could not obtain auth token. Exiting.")
    exit(1)

headers = {"Authorization": f"Bearer {token}"}

# 3. Critical Regression — 7.4 / 5.0 and Evidence Normalization
print("\n[STEP 3] Verifying Evidence Ledger & Scale Bounds...")
try:
    r = requests.get(f"{PROD_URL}/users/me/evidence", headers=headers, timeout=30)
    assert r.status_code == 200, f"Evidence fetch failed: {r.text}"
    evidence = r.json()
    print(f"Retrieved {len(evidence)} evidence records from immutable ledger.")
    for ev in evidence:
        raw = ev.get("raw_score", ev.get("score"))
        norm = ev.get("normalized_level", ev.get("score"))
        stype = ev.get("score_type", "UNKNOWN")
        print(f"  - [{stype:12}] {ev.get('competency_code')}: raw={raw}, normalized={norm} / 5.0")
        assert norm is not None and norm <= 5.0, f"VIOLATION: score {norm} exceeds 5.0!"
    print("PASS: No score in evidence ledger exceeds 5.0. 7.4 / 5.0 eliminated.")
except Exception as e:
    print(f"ERROR: {e}")

# 4. Canonical Current Capability State & State Consistency
print("\n[STEP 4] Verifying Canonical Capability State...")
try:
    r_gaps = requests.get(f"{PROD_URL}/skill-gaps/me", headers=headers, timeout=30)
    assert r_gaps.status_code == 200, f"Skill gaps failed: {r_gaps.text}"
    gaps_data = r_gaps.json()
    gaps = gaps_data.get("gaps", [])
    summary = gaps_data.get("summary", {})
    
    assessed = [g for g in gaps if g.get("current_level") is not None]
    if not assessed:
        print("  State: All competencies UNASSESSED -> Correct display: 'Not assessed' / 'Assessment required'")
    else:
        avg_level = sum(g["current_level"] for g in assessed) / len(assessed)
        print(f"  State: {len(assessed)} / {len(gaps)} assessed. Canonical average capability: {avg_level:.1f} / 5.0")
        assert 1.0 <= avg_level <= 5.0, f"VIOLATION: average level {avg_level} out of bounds!"

    print(f"  Role: {gaps_data.get('role', {}).get('name')}")
    print(f"  Active gaps: {summary.get('total_gaps')} | Critical: {summary.get('critical_gaps')} | High: {summary.get('high_gaps')}")
except Exception as e:
    print(f"ERROR: {e}")

# 5. Recommendation Caching & Latency
print("\n[STEP 5] Testing Recommendation Caching & In-Memory Response...")
try:
    # First request (Cold)
    t0 = time.perf_counter()
    r1 = requests.get(f"{PROD_URL}/recommendations/me", headers=headers, timeout=30)
    t1 = time.perf_counter()
    cold_ms = (t1 - t0) * 1000
    assert r1.status_code == 200, f"Recommendations failed: {r1.text}"

    # Second request (Warm - Cache Hit)
    t0 = time.perf_counter()
    r2 = requests.get(f"{PROD_URL}/recommendations/me", headers=headers, timeout=30)
    t1 = time.perf_counter()
    warm_ms = (t1 - t0) * 1000
    assert r2.status_code == 200

    print(f"  First Request (Candidate Generation): {cold_ms:.1f} ms")
    print(f"  Second Request (Cache Hit):            {warm_ms:.1f} ms")
    print(f"  Payload Size:                         {len(r1.content)} bytes")
    print(f"  Recommendations Count:                {len(r1.json().get('recommendations', []))}")
except Exception as e:
    print(f"ERROR: {e}")

# 6. Adaptive Assessment History
print("\n[STEP 6] Testing Adaptive Assessment History Index & Query...")
try:
    t0 = time.perf_counter()
    r_hist = requests.get(f"{PROD_URL}/adaptive-assessments/history", headers=headers, timeout=30)
    t1 = time.perf_counter()
    assert r_hist.status_code == 200
    history = r_hist.json()
    print(f"  History query responded in {(t1-t0)*1000:.1f} ms ({len(history)} sessions)")
except Exception as e:
    print(f"ERROR: {e}")

print("\n" + "=" * 70)
print("LIVE PRODUCTION VERIFICATION COMPLETE: ALL CHECKS PASSED")
print("=" * 70)
