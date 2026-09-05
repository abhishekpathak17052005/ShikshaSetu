# Phase 5A Security Audit: Trainer Self-Registration Vulnerability

**Target Subsystem:** ShikshaSetu Authentication & RBAC Layer  
**Severity:** P0 / Critical Security Defect  
**Audit Scope:** Public Registration, Role Assignment, Admin Provisioning, RBAC Boundaries  
**Date:** 2026-09-06  

---

## 1. Executive Summary

An independent product security audit revealed that the public self-service registration endpoint allowed untrusted external clients to create accounts with the privileged `TRAINER` access role. 

This document details the architectural audit, exact root cause, threat vector, data flows, and required security hardening to enforce the invariant that **public registration can NEVER create TRAINER or ADMIN accounts**.

---

## 2. Current Registration & Role Assignment Flow

### 2.1 Request Lifecycle
1. **Request Ingestion (`POST /api/v1/auth/register`):**
   - The endpoint receives a JSON payload matching `app.auth.schemas.RegisterRequest`.
   - `RegisterRequest` defines:
     ```python
     access_role: AccessRole = Field(default=AccessRole.OFFICIAL)
     ```
   - `AccessRole` is a `StrEnum` comprising `OFFICIAL`, `TRAINER`, `ADMIN`, `EMPLOYEE`.

2. **Route Handler (`app.auth.router.register`):**
   - Validates existence of `role_id` or resolves professional role from `(department, designation)`.
   - Checks if user email already exists.
   - Evaluates:
     ```python
     if payload.access_role == AccessRole.ADMIN:
         raise HTTPException(
             status_code=status.HTTP_403_FORBIDDEN,
             detail="Admin registration is restricted and must be provisioned by an administrator",
         )

     access_role_value = (
         AccessRole.OFFICIAL.value
         if payload.access_role in (AccessRole.OFFICIAL, AccessRole.EMPLOYEE)
         else payload.access_role.value
     )
     ```
   - Assembles the MongoDB document with `"access_role": access_role_value`.
   - Inserts the document into the `users` collection via `app.users.repository.insert_user`.
   - Reconciles initial competency profile and returns `UserResponse` with HTTP 201.

3. **Authentication & Role Claims (`POST /api/v1/auth/login` & `app.auth.dependencies`):**
   - When the user logs in, a JWT access token is signed with `sub = str(user["_id"])`.
   - On subsequent requests, `get_current_user` loads the user record from MongoDB.
   - RBAC dependency `require_trainer` (`require_role(AccessRole.TRAINER, AccessRole.ADMIN)`) inspects `current_user.get("access_role")`.
   - Because `access_role` was saved as `"TRAINER"`, the user receives full privileged access to:
     - Learning Material upload (`/api/v1/learning-materials/upload`)
     - AI Question Generation (`/api/v1/learning-materials/{id}/generate-questions`)
     - Trainer Assessment Studio (`/api/v1/trainer/*`)
     - Quiz creation, publication, and assignment across civil service learners

---

## 3. Exact Vulnerability & Root Cause Analysis

### 3.1 Vulnerability Mechanism
The route handler in `app/auth/router.py` only checked for `payload.access_role == AccessRole.ADMIN`. If a client supplied `"access_role": "TRAINER"`, the check was bypassed and `access_role_value` evaluated to `"TRAINER"`.

Furthermore, in `tests/test_rbac.py`, test `test_registration_as_trainer_allowed()` explicitly codified this insecure behavior as expected functionality.

### 3.2 Threat Vector & Impact
- **Threat Vector:** Any unauthenticated public user or script can execute:
  ```http
  POST /api/v1/auth/register
  Content-Type: application/json

  {
    "email": "attacker@gov.in",
    "password": "Password123!",
    "full_name": "Unauthorized Trainer",
    "role_id": "6a8ff00dbda6ad0866e7667c",
    "designation": "External Consultant",
    "department": "Public",
    "employee_id": "EXP-9999",
    "access_role": "TRAINER"
  }
  ```
- **Impact:** Privilege escalation to `TRAINER`. Attackers gain unauthorized access to publish training assessments, view employee capability records, generate official exam questions, and grade civil servants.

---

## 4. Code Artifacts & Functions Involved

| File | Function / Symbol | Role in Vulnerability |
| :--- | :--- | :--- |
| `backend/app/auth/schemas.py` | `RegisterRequest`, `AccessRole` | Accepted `AccessRole.TRAINER` in public schema without sanitization/rejection. |
| `backend/app/auth/router.py` | `register()` | Blocked `ADMIN` with 403, but permitted `TRAINER` through to DB insertion. |
| `backend/app/admin/router.py` | `router` | Lacked an explicit administrative endpoint for provisioning/promoting trainers. |
| `backend/app/admin/service.py` | `service` | Lacked `promote_user_to_trainer` service method. |
| `backend/tests/test_rbac.py` | `test_registration_as_trainer_allowed` | Erroneous legacy test asserting trainer self-registration succeeded. |

---

## 5. Existing Protections (What is Already Secure)

1. **Profile Updates (`PUT /api/v1/users/me`):**
   - Uses `UserProfileUpdate` with `extra="forbid"`.
   - Does not expose `access_role`.
   - Verified that profile updates cannot modify access roles.

2. **Admin Self-Registration:**
   - Registration with `access_role: "ADMIN"` is blocked with HTTP 403 Forbidden.

3. **Route Guards (`app/auth/dependencies.py`):**
   - `require_role`, `require_trainer`, `require_admin_role` correctly enforce role hierarchy based on database-backed user records.

4. **Database Seeds:**
   - Bootstrap scripts (`seed_master.py`, `seed_production.py`) securely seed demo accounts via CLI/internal execution only.

---

## 6. Required Security Invariants & Changes

### 6.1 Invariants
1. **Public Registration $\rightarrow$ OFFICIAL only:**
   - Public registration MUST NEVER persist a `TRAINER` or `ADMIN` role.
   - Any registration payload requesting `TRAINER` or `ADMIN` (regardless of casing, leading/trailing whitespace, or aliases) MUST be rejected with HTTP 403 Forbidden.
   - Valid public registrations must unconditionally persist `access_role = "OFFICIAL"`.

2. **Trainer Provisioning $\rightarrow$ ADMIN only:**
   - Promoting a user from `OFFICIAL` $\rightarrow$ `TRAINER` is ONLY possible via authenticated and authorized `ADMIN` functionality.
   - `TRAINER` and `OFFICIAL` users are strictly forbidden from provisioning/promoting trainers.
   - Unauthenticated callers are rejected with HTTP 401.

3. **Admin Provisioning $\rightarrow$ Secure Bootstrap Only:**
   - `ADMIN` accounts cannot be created via public registration or trainer promotion endpoints.

### 6.2 Proposed Code Modifications
1. **`app/auth/schemas.py`:**
   - Normalize `access_role` in `RegisterRequest` (strip whitespace, uppercase).
2. **`app/auth/router.py`:**
   - In `register()`, reject both `ADMIN` and `TRAINER` with HTTP 403 Forbidden.
   - Ensure `access_role_value` is strictly `"OFFICIAL"`.
3. **`app/admin/router.py` & `app/admin/service.py`:**
   - Expose `POST /api/v1/admin/users/{user_id}/promote-to-trainer` under `require_admin_role`.
   - Implement `promote_user_to_trainer` to safely update `access_role` to `"TRAINER"`.
4. **`tests/test_rbac.py` & `tests/test_auth.py`:**
   - Replace `test_registration_as_trainer_allowed` with regression tests verifying rejection of `TRAINER`, `trainer`, ` TRAINER `, `ADMIN`, `admin`, ` ADMIN `.
   - Add tests verifying Admin trainer promotion and RBAC barriers (Trainer/Official/Unauthenticated forbidden).

---

## 7. Required Regression Tests

1. Public registration without `access_role` defaults to `OFFICIAL` in DB.
2. Public registration with `"access_role": "TRAINER"` is rejected with HTTP 403.
3. Public registration with `"access_role": "ADMIN"` is rejected with HTTP 403.
4. Public registration with `"access_role": "trainer"` (lowercase) is rejected with HTTP 403.
5. Public registration with `"access_role": "admin"` (lowercase) is rejected with HTTP 403.
6. Public registration with `"access_role": "  TRAINER  "` (whitespace variation) is rejected with HTTP 403.
7. Public registration with `"access_role": "  admin  "` is rejected with HTTP 403.
8. Authenticated ADMIN can promote an OFFICIAL to TRAINER via `/api/v1/admin/users/{id}/promote-to-trainer`.
9. Authenticated TRAINER cannot promote an OFFICIAL to TRAINER (HTTP 403).
10. Authenticated OFFICIAL cannot promote an OFFICIAL to TRAINER (HTTP 403).
11. Unauthenticated request to trainer promotion is rejected with HTTP 401.
12. Existing login, JWT claims, and profile access continue functioning seamlessly.
