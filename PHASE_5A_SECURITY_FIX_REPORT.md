# Phase 5A Security Fix Report: Closed Trainer Self-Registration

**Component:** ShikshaSetu Backend — Authentication, Registration & Admin Provisioning  
**Issue Priority:** P0 / Critical Security Remediation  
**Status:** Completed & Verified  
**Date:** 2026-09-06  

---

## 1. Vulnerability Found

Unauthenticated external callers could self-assign the privileged `TRAINER` access role during public registration by providing `"access_role": "TRAINER"` (or case/whitespace variants) in the `POST /api/v1/auth/register` payload. 

This granted unauthorized actors access to the Trainer Assessment Studio, AI Question Generation, Quiz Publication, and access to evaluate civil servant learners.

---

## 2. Root Cause

1. `app.auth.schemas.RegisterRequest` accepted `AccessRole` (an enum containing `OFFICIAL`, `TRAINER`, `ADMIN`, `EMPLOYEE`) with a default of `OFFICIAL`, but permitted callers to pass `TRAINER`.
2. `app.auth.router.register` explicitly blocked `ADMIN` with HTTP 403, but failed to block `TRAINER`. It subsequently assigned `access_role_value = payload.access_role.value`, persisting `"TRAINER"` in MongoDB.
3. `tests/test_rbac.py` had a legacy test `test_registration_as_trainer_allowed()` that codified this security gap.
4. The system lacked an explicit, protected administrative endpoint for authorized `ADMIN` users to promote verified accounts to the `TRAINER` role.

---

## 3. Files Changed

| File | Purpose of Modification |
| :--- | :--- |
| `backend/app/auth/schemas.py` | Added `@field_validator("access_role", mode="before")` to normalize role inputs (trim whitespace, uppercase enum parsing). |
| `backend/app/auth/router.py` | Hardened `/auth/register` to reject both `ADMIN` and `TRAINER` requests with HTTP 403 Forbidden, and hardcoded persistent registration role to `AccessRole.OFFICIAL.value`. |
| `backend/app/admin/router.py` | Added `POST /api/v1/admin/users/{user_id}/promote-to-trainer` under `require_admin_role` guard. |
| `backend/app/admin/service.py` | Added `promote_user_to_trainer()` business logic restricting role changes to authenticated administrators only. |
| `backend/tests/test_rbac.py` | Replaced insecure trainer self-registration test with parameterized regression tests for `TRAINER`/`ADMIN` rejection and added RBAC tests for Admin trainer promotion. |

---

## 4. Security Behavior Before vs. After

### Before
- `POST /auth/register` with `{"access_role": "TRAINER"}` returned HTTP 201 Created and persisted user with `access_role: "TRAINER"`.
- `POST /auth/register` with `{"access_role": "ADMIN"}` returned HTTP 403 Forbidden.
- Casing variations (e.g. `"trainer"`, `"admin"`) caused validation 422 errors rather than explicit security rejections.
- No administrative route existed to promote legitimate civil service instructors to `TRAINER`.

### After
- `POST /auth/register` with `{"access_role": "TRAINER"}` returns **HTTP 403 Forbidden** (*"Trainer registration is restricted and must be provisioned by an administrator"*), and creates NO record.
- `POST /auth/register` with `{"access_role": "ADMIN"}` returns **HTTP 403 Forbidden** (*"Admin registration is restricted and must be provisioned by an administrator"*), and creates NO record.
- Casing and whitespace variants (`"trainer"`, `" trainer "`, `"admin"`, `" admin "`, `"Trainer"`, `"Admin"`) are all normalized and rejected with **HTTP 403 Forbidden**.
- Public registrations without a role or requesting `OFFICIAL`/`EMPLOYEE` are created with `access_role = "OFFICIAL"`.
- Valid `OFFICIAL` $\rightarrow$ `TRAINER` promotion is strictly controlled via `POST /api/v1/admin/users/{user_id}/promote-to-trainer`, accessible only to authenticated `ADMIN` accounts.
- `TRAINER` and `OFFICIAL` callers attempting promotion receive **HTTP 403 Forbidden**. Unauthenticated callers receive **HTTP 401 Unauthorized**.

---

## 5. Security Invariant Verification

```
┌────────────────────────────────────────────────────────┐
│ PUBLIC REGISTRATION                                    │
│ → Exclusively creates OFFICIAL accounts                │
│ → Requesting TRAINER or ADMIN returns HTTP 403         │
└────────────────────────────────────────────────────────┘
                           │
                           ▼
┌────────────────────────────────────────────────────────┐
│ TRAINER PROVISIONING                                   │
│ → Authenticated ADMIN calls                            │
│   POST /api/v1/admin/users/{user_id}/promote-to-trainer│
│ → OFFICIAL / TRAINER / Anonymous blocked (401 / 403)   │
└────────────────────────────────────────────────────────┘
                           │
                           ▼
┌────────────────────────────────────────────────────────┐
│ ADMIN PROVISIONING                                     │
│ → Secure CLI bootstrap / database seed only            │
│ → Public registration & promotion cannot create ADMIN  │
└────────────────────────────────────────────────────────┘
```

---

## 6. Tests Added & Execution Results

### 6.1 Test Suite Breakdown
In `backend/tests/test_rbac.py`:
1. `test_registration_defaults_to_official`: Confirms default registration yields `OFFICIAL` both in API response and in MongoDB.
2. `test_registration_as_trainer_rejected` (Parameterized across `"TRAINER"`, `"trainer"`, `" TRAINER "`, `" trainer "`, `"Trainer"`): Confirms 403 Forbidden and zero database persistence.
3. `test_registration_as_admin_rejected` (Parameterized across `"ADMIN"`, `"admin"`, `" ADMIN "`, `" admin "`, `"Admin"`): Confirms 403 Forbidden and zero database persistence.
4. `test_registration_with_invalid_role_rejected`: Confirms invalid roles (e.g. `"SUPERUSER"`) return 422.
5. `test_admin_can_promote_official_to_trainer`: Confirms ADMIN token can promote an OFFICIAL to TRAINER and updates DB.
6. `test_trainer_cannot_promote_another_trainer`: Confirms TRAINER token receives 403 Forbidden on promotion endpoint.
7. `test_official_cannot_promote_to_trainer`: Confirms OFFICIAL token receives 403 Forbidden on promotion endpoint.
8. `test_unauthenticated_cannot_access_trainer_provisioning`: Confirms missing token receives 401 Unauthorized.

### 6.2 Test Command & Execution Output
Command:
```powershell
..\.venv\Scripts\pytest tests/test_auth.py tests/test_rbac.py tests/test_admin.py tests/test_trainer.py tests/test_e2e_3role_lifecycle.py
```
Output:
```
====================== 79 passed, 26 warnings in 24.59s =======================
```

### 6.3 Frontend Verification
- **TypeScript Type Check:** `npm run check` $\rightarrow$ Passed (Exit code 0, no type errors).
- **Vite Production Build:** `npm run build` $\rightarrow$ Built 1904 modules successfully in 5.88s (Exit code 0).

---

## 7. Follow-Up Issues Discovered During Audit

1. **Deprecated Pydantic V1 Config / Validators in AI Module (`app/ai/models.py`, `app/ai/schemas.py`):**
   - Class-based `Config` and `@validator` triggers deprecation warnings in Pydantic V2. To be migrated to `ConfigDict` and `@field_validator` in a future cycle.
2. **Legacy `test_quizzes.py` Mock Schema Mismatches:**
   - Pre-existing Phase 1 test file `test_quizzes.py` has 10 test failures due to legacy assumption of quiz retrieval schemas superseded by Phase 2B Trainer Studio quizzes. The active Phase 2B/3E lifecycle tests (`test_trainer.py`, `test_e2e_3role_lifecycle.py`) passed 100%.
