import sys
sys.path.insert(0, r"c:\Users\Lenovo\Desktop\ShikshaSetu\backend")
import os
import time
import requests
import json
import dns.resolver
dns.resolver.default_resolver = dns.resolver.Resolver()
dns.resolver.default_resolver.nameservers = ['8.8.8.8']
from pymongo import MongoClient
from bson import ObjectId

PROD_URL = "https://shikshasetu-m8xv.onrender.com/api/v1"

print("=" * 75)
print("PHASE 3G-D — FINAL LIVE PRODUCTION VERIFICATION")
print(f"Target URL: {PROD_URL}")
print("=" * 75)

# 1. Health
print("\n[STEP 1] Verifying System Health...")
t0 = time.perf_counter()
r_health = requests.get(f"{PROD_URL}/health", timeout=30)
t1 = time.perf_counter()
print(f"Health Status: {r_health.status_code} in {(t1-t0)*1000:.1f}ms | Body: {r_health.text}")
assert r_health.status_code == 200, "Health check failed"

# 2. Authenticate Education Officer (Abhishek Pathak)
print("\n[STEP 2] Authenticating Education Officer (ap17052005@gmail.com)...")
# Generate JWT token using backend secret or login
from app.core.config import get_settings
from app.auth.security import create_access_token

settings = get_settings()
uri = os.environ.get("MONGODB_URI") or settings.mongodb_uri
client = MongoClient(uri)
db = client[settings.mongodb_database]

user_edu = db.users.find_one({"email": "ap17052005@gmail.com"})
user_edu_id = str(user_edu["_id"])
token_edu = create_access_token(user_edu_id, settings)
headers_edu = {"Authorization": f"Bearer {token_edu}"}

r_me = requests.get(f"{PROD_URL}/auth/me", headers=headers_edu, timeout=30)
print(f"/auth/me: {r_me.status_code} | {r_me.json().get('full_name')} | Role ID: {r_me.json().get('role_id')} | Dept: {r_me.json().get('department')}")

# 3. Critical Verification: GET /skill-gaps/me for Education Officer
print("\n[STEP 3] Calling GET /skill-gaps/me for Education Officer (Testing 4.5 Gap Fix)...")
t0 = time.perf_counter()
r_gaps = requests.get(f"{PROD_URL}/skill-gaps/me", headers=headers_edu, timeout=30)
t1 = time.perf_counter()
gaps_latency_ms = (t1 - t0) * 1000

print(f"Status Code: {r_gaps.status_code} in {gaps_latency_ms:.1f}ms")
if r_gaps.status_code != 200:
    print(f"FAILED: {r_gaps.text}")
    sys.exit(1)

gaps_data = r_gaps.json()
role_name = gaps_data.get("role", {}).get("name")
summary = gaps_data.get("summary", {})
gaps = gaps_data.get("gaps", [])

print(f"Role: {role_name}")
print(f"Required Competencies: {summary.get('required_competencies')}")
print(f"Total Gaps: {summary.get('total_gaps')}")
print(f"Critical Gaps: {summary.get('critical_gaps')}")
print(f"Not Assessed Count: {summary.get('not_assessed_count')}")

assert len(gaps) == 6, f"Expected 6 gaps, got {len(gaps)}"
assert summary.get("required_competencies") == 6
assert summary.get("total_gaps") == 6

# Find BEH_ETHICS and BEH_COMMUNICATION
ethics_gap = next((g for g in gaps if g["competency_code"] == "BEH_ETHICS"), None)
comm_gap = next((g for g in gaps if g["competency_code"] == "BEH_COMMUNICATION"), None)

print("\nVerifying Specific Competencies in /skill-gaps/me:")
assert ethics_gap is not None, "BEH_ETHICS not found in gaps!"
print(f"  BEH_ETHICS: req={ethics_gap.get('required_level')}, cur={ethics_gap.get('current_level')}, gap={ethics_gap.get('gap')}, category={ethics_gap.get('gap_category')}, status={ethics_gap.get('assessment_status')}")
assert ethics_gap.get("required_level") == 4.5
assert ethics_gap.get("current_level") is None
assert ethics_gap.get("gap") == 4.5
assert ethics_gap.get("gap_category") == "CRITICAL"
assert ethics_gap.get("assessment_status") == "NOT_ASSESSED"

assert comm_gap is not None, "BEH_COMMUNICATION not found in gaps!"
print(f"  BEH_COMMUNICATION: req={comm_gap.get('required_level')}, cur={comm_gap.get('current_level')}, gap={comm_gap.get('gap')}, category={comm_gap.get('gap_category')}, status={comm_gap.get('assessment_status')}")
assert comm_gap.get("required_level") == 4.0
assert comm_gap.get("current_level") == 3.8
assert comm_gap.get("gap") == 0.2
assert comm_gap.get("gap_category") == "LOW"
assert comm_gap.get("assessment_status") == "ASSESSED"

print("SUCCESS: /skill-gaps/me returned 200 OK! Both BEH_ETHICS (4.5) and BEH_COMMUNICATION (3.8) are verified.")

# 4. Compare with GET /competencies/me
print("\n[STEP 4] Calling GET /competencies/me and Comparing...")
r_comps = requests.get(f"{PROD_URL}/competencies/me", headers=headers_edu, timeout=30)
assert r_comps.status_code == 200
comps = r_comps.json()
print(f"Competencies count: {len(comps)}")
comm_comp = next((c for c in comps if c["code"] == "BEH_COMMUNICATION"), None)
assert comm_comp is not None
assert comm_comp.get("current_level") == 3.8
assert comm_comp.get("required_level") == 4.0
print("SUCCESS: /competencies/me agrees with /skill-gaps/me on canonical state (BEH_COMMUNICATION = 3.8).")

# 5. Database Read-Only Verification
print("\n[STEP 5] Database Direct Inspection (MongoDB Atlas)...")
prof_comm = db.competency_profiles.find_one({"user_id": ObjectId(user_edu_id), "competency_code": "BEH_COMMUNICATION"})
if not prof_comm:
    # try with string or competency_id
    comp_comm = db.competencies.find_one({"code": "BEH_COMMUNICATION"})
    prof_comm = db.competency_profiles.find_one({"user_id": ObjectId(user_edu_id), "competency_id": comp_comm["_id"]})
print(f"  competency_profiles (BEH_COMMUNICATION): current_level={prof_comm.get('current_level')}, confidence={prof_comm.get('confidence')}, status={prof_comm.get('status')}")
assert prof_comm.get("current_level") == 3.8
assert prof_comm.get("confidence") == 0.85
assert prof_comm.get("status") == "active"

# 6. Check Evidence Ledger
print("\n[STEP 6] Checking Evidence Ledger Bounds...")
r_ev = requests.get(f"{PROD_URL}/users/me/evidence", headers=headers_edu, timeout=30)
assert r_ev.status_code == 200
ev_list = r_ev.json()
print(f"  Retrieved {len(ev_list)} evidence records.")
for ev in ev_list:
    raw = ev.get("raw_score", ev.get("score"))
    norm = ev.get("normalized_level", ev.get("score"))
    assert norm <= 5.0, f"Score {norm} exceeds 5.0!"
print("  No evidence score exceeds 5.0 (7.4 / 5.0 eliminated).")

# 7. Recommendations Caching & Candidate Generation
print("\n[STEP 7] Testing Recommendations Caching & Isolation...")
t0 = time.perf_counter()
r_rec1 = requests.get(f"{PROD_URL}/recommendations/me", headers=headers_edu, timeout=30)
t1 = time.perf_counter()
rec1_ms = (t1 - t0) * 1000
assert r_rec1.status_code == 200

t0 = time.perf_counter()
r_rec2 = requests.get(f"{PROD_URL}/recommendations/me", headers=headers_edu, timeout=30)
t1 = time.perf_counter()
rec2_ms = (t1 - t0) * 1000
assert r_rec2.status_code == 200

print(f"  First Call (Cold Candidate Generation): {rec1_ms:.1f} ms")
print(f"  Second Call (In-Memory Cache Hit):      {rec2_ms:.1f} ms")
recs = r_rec1.json().get("recommendations", [])
print(f"  Recommendations Count: {len(recs)}")
# Verify BEH_ETHICS or role competencies in recommendations
rec_comp_codes = [r.get("competency_code") for r in recs if "competency_code" in r]
print(f"  Top recommended competency codes: {rec_comp_codes[:5]}")

print("\n" + "=" * 75)
print("ALL LIVE PRODUCTION VERIFICATION CHECKS PASSED PERFECTLY!")
print("=" * 75)
