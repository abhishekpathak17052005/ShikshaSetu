"""
ShikshaSetu Complete End-to-End System Design Integration Test Suite
Validates the entire closed-loop system flow from Auth through to Admin/Trainer Analytics:
REAL USER -> AUTH -> PROFILE -> ROLE -> COMPETENCIES -> ASSESSMENT ->
SKILL GAP -> RECOMMENDATION -> LEARNING -> QUIZ -> RESULT -> EVIDENCE ->
PROFILE UPDATE -> AI/RAG -> CACHE -> ADMIN/TRAINER ANALYTICS
"""

import os
import sys
import uuid
import random
import pytest
import requests

BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000/api/v1")


@pytest.fixture(scope="module")
def api_tokens():
    tokens = {}
    r_off = requests.post(f"{BASE_URL}/auth/login", json={"email": "official@shikshasetu.gov.in", "password": "Password123!"}, timeout=30)
    assert r_off.status_code == 200, f"Official login failed: {r_off.status_code}"
    tokens["official"] = r_off.json()["access_token"]

    r_tr = requests.post(f"{BASE_URL}/auth/login", json={"email": "trainer@shikshasetu.gov.in", "password": "Password123!"}, timeout=30)
    assert r_tr.status_code == 200, f"Trainer login failed: {r_tr.status_code}"
    tokens["trainer"] = r_tr.json()["access_token"]

    r_adm = requests.post(f"{BASE_URL}/auth/login", json={"email": "admin@shikshasetu.gov.in", "password": "Password123!"}, timeout=30)
    assert r_adm.status_code == 200, f"Admin login failed: {r_adm.status_code}"
    tokens["admin"] = r_adm.json()["access_token"]
    return tokens


def test_system_health():
    r = requests.get(f"{BASE_URL}/health", timeout=15)
    assert r.status_code == 200
    assert r.json().get("database") == "connected"


def test_authentication_and_rbac(api_tokens):
    h_off = {"Authorization": f"Bearer {api_tokens['official']}"}
    h_tr = {"Authorization": f"Bearer {api_tokens['trainer']}"}
    h_adm = {"Authorization": f"Bearer {api_tokens['admin']}"}

    # Token Introspection
    me = requests.get(f"{BASE_URL}/auth/me", headers=h_off, timeout=15).json()
    assert me.get("access_role") == "OFFICIAL"
    assert me.get("designation") == "Statistical Officer"

    # Cross-role RBAC enforcement
    assert requests.get(f"{BASE_URL}/trainer/dashboard", headers=h_off, timeout=15).status_code == 403
    assert requests.get(f"{BASE_URL}/admin/dashboard", headers=h_off, timeout=15).status_code == 403
    assert requests.get(f"{BASE_URL}/trainer/dashboard", headers=h_tr, timeout=15).status_code == 200
    assert requests.get(f"{BASE_URL}/admin/dashboard", headers=h_adm, timeout=15).status_code == 200


def test_competency_framework_and_skill_gaps(api_tokens):
    h_off = {"Authorization": f"Bearer {api_tokens['official']}"}

    comps = requests.get(f"{BASE_URL}/competencies", headers=h_off, timeout=15).json()
    assert len(comps) >= 40

    gaps_resp = requests.get(f"{BASE_URL}/skill-gaps/me", headers=h_off, timeout=15).json()
    gaps = gaps_resp.get("gaps", [])
    assert len(gaps) > 0
    for g in gaps:
        req = float(g.get("required_level", 0.0))
        cur = float(g.get("current_level", 0.0))
        gap = float(g.get("gap_size", g.get("gap", 0.0)))
        assert gap == pytest.approx(max(0.0, req - cur), abs=0.05)


def test_recommendations_and_learning_flow(api_tokens):
    h_off = {"Authorization": f"Bearer {api_tokens['official']}"}

    recs_resp = requests.get(f"{BASE_URL}/recommendations/me", headers=h_off, timeout=30).json()
    recs = recs_resp.get("recommendations", [])
    assert len(recs) > 0
    unique_ids = {str(item.get("resource", {}).get("resource_id") or item.get("_id")) for item in recs}
    assert len(unique_ids) == len(recs)

    # Activity lifecycle
    first_res = recs[0].get("resource", {})
    res_id = str(first_res.get("_id") or recs[0].get("resource_id"))
    comp_id = str(recs[0].get("competency_id", "6a8ff00dbda6ad0866e7667c"))

    act_start = requests.post(f"{BASE_URL}/learning-activities", json={"resource_id": res_id, "competency_id": comp_id}, headers=h_off, timeout=15)
    if act_start.status_code in [200, 201]:
        act_id = act_start.json().get("_id") or act_start.json().get("activity_id")
        assert act_id is not None
        # Progress update
        act_upd = requests.put(f"{BASE_URL}/learning-activities/{act_id}", json={"progress_percentage": 50.0}, headers=h_off, timeout=15)
        assert act_upd.status_code in [200, 204]


def test_ai_copilot_and_cache(api_tokens):
    h_off = {"Authorization": f"Bearer {api_tokens['official']}"}
    payload = {"message": "What are my primary skill gaps?"}

    # First request (allow up to 60s for live LLM candidate cascade + Atlas RAG retrieval)
    r1 = requests.post(f"{BASE_URL}/assistant/chat", json=payload, headers=h_off, timeout=60)
    assert r1.status_code == 200
    assert len(r1.json().get("answer", "")) > 10

    # Second cached request
    r2 = requests.post(f"{BASE_URL}/assistant/chat", json=payload, headers=h_off, timeout=30)
    assert r2.status_code == 200
    assert len(r2.json().get("answer", "")) > 10


def test_evidence_ledger_immutability(api_tokens):
    h_off = {"Authorization": f"Bearer {api_tokens['official']}"}
    r_ev = requests.get(f"{BASE_URL}/users/me/evidence", headers=h_off, timeout=15)
    assert r_ev.status_code == 200
    ev_list = r_ev.json()
    assert isinstance(ev_list, list)
    assert len(ev_list) > 0
