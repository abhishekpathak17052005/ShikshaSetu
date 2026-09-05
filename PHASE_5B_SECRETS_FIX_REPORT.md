# Phase 5B — Secrets & Repository Hygiene Fix Report

**Report Date:** 2026-09-06  
**Status:** COMPLETE — READY FOR USER REVIEW  
**Remediation Phase:** Phase 5B (Security Fix #2: Secrets & Repository Hygiene)  

---

## 1. Vulnerability & Findings

The product security audit flagged a P0 issue regarding exposed secrets and credentials:
> *"Sensitive credentials/secrets were present in the project/archive, including MongoDB URI, JWT secret and LLM/API key."*

During our repository and history investigation, we confirmed:
1. **Hardcoded MongoDB Atlas Connection Strings:** A MongoDB Atlas URI containing embedded database username and password was hardcoded in `backend/create_demo_accounts.py` and `backend/scripts/live_prod_verify_final_3g.py`, as well as documented in `backend/DIAGNOSIS_REPORT.md`.
2. **Historical Git Exposure:** The connection string was previously committed to git history across commits `8d320ec`, `abb597d`, `dc5904d`, `d3f2d34`, and `ddc678f`.
3. **Tracked Environment File:** `frontend/.env.production` was tracked in git.
4. **Weak / Missing Production Fallback Safeguards:** `backend/app/core/config.py` permitted fallback to a default development JWT secret even when operating in production mode without validation.

---

## 2. Root Cause

1. **Ad-hoc utility scripts:** Helper and diagnostic scripts directly initialized `MongoClient('mongodb+srv://...')` with hardcoded credentials instead of consuming `get_settings().mongodb_uri`.
2. **Permissive `.gitignore` rules in submodules:** `frontend/.gitignore` had specific `.env.local` entries but lacked generic wildcard ignore for `.env.*`, resulting in `frontend/.env.production` being committed.
3. **Missing Pydantic production validator:** `Settings` defined a default `jwt_secret` for local development but had no validator to prevent this default from being used when `APP_ENV=production`.

---

## 3. Files Changed

| File Path | Description of Changes |
|---|---|
| [backend/app/core/config.py](file:///c:/Users/Lenovo/Desktop/ShikshaSetu/backend/app/core/config.py) | Added `AliasChoices` (`SECRET_KEY`, `ACCESS_TOKEN_EXPIRE_MINUTES`, `GEMINI_API_KEY`) and `@model_validator` enforcing strict secret strength in production mode |
| [backend/create_demo_accounts.py](file:///c:/Users/Lenovo/Desktop/ShikshaSetu/backend/create_demo_accounts.py) | Replaced hardcoded connection string with `get_settings().mongodb_uri` and `settings.mongodb_database` |
| [backend/scripts/live_prod_verify_final_3g.py](file:///c:/Users/Lenovo/Desktop/ShikshaSetu/backend/scripts/live_prod_verify_final_3g.py) | Replaced hardcoded connection string with `os.environ.get("MONGODB_URI") or settings.mongodb_uri` |
| [backend/DIAGNOSIS_REPORT.md](file:///c:/Users/Lenovo/Desktop/ShikshaSetu/backend/DIAGNOSIS_REPORT.md) | Sanitized hardcoded connection string to placeholder format |
| [.env.example](file:///c:/Users/Lenovo/Desktop/ShikshaSetu/.env.example) | Created comprehensive root-level environment variable template with zero real secrets |
| [backend/.env.example](file:///c:/Users/Lenovo/Desktop/ShikshaSetu/backend/.env.example) | Updated backend environment template with comprehensive placeholders |
| [frontend/.env.example](file:///c:/Users/Lenovo/Desktop/ShikshaSetu/frontend/.env.example) | Cleaned frontend environment template with generic placeholders |
| [frontend/.gitignore](file:///c:/Users/Lenovo/Desktop/ShikshaSetu/frontend/.gitignore) | Added `.env`, `.env.*`, `!.env.example` rules |
| `frontend/.env.production` | Removed from git index cache (`git rm --cached`) |
| [backend/tests/test_config_security.py](file:///c:/Users/Lenovo/Desktop/ShikshaSetu/backend/tests/test_config_security.py) | Added automated test suite for configuration validation and alias resolution |

---

## 4. Repository Security & Configuration Changes

### 4.1 Git Tracking Status
- `git rm --cached frontend/.env.production` untracked the production configuration file.
- `git ls-files | Select-String "\.env"` now verifies that **only** `.env.example` files are tracked by git.
- `.gitignore` in both root and frontend explicitly enforce:
  ```gitignore
  .env
  .env.*
  !.env.example
  ```

### 4.2 Configuration Loading & Production Enforcement
- `app.core.config.Settings` now uses Pydantic V2 `AliasChoices`:
  - `jwt_secret`: checks `JWT_SECRET` and `SECRET_KEY` (compatible with Render's auto-generated `SECRET_KEY`).
  - `jwt_access_token_expire_minutes`: checks `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` and `ACCESS_TOKEN_EXPIRE_MINUTES`.
  - `llm_api_key`: checks `LLM_API_KEY`, `GEMINI_API_KEY`, and `OPENAI_API_KEY`.
- `validate_production_secrets` model validator:
  - If `APP_ENV` is set to `production` or `prod`, it strictly rejects default secrets (`"change-this-development-secret-32"`, `"secret"`, etc.) or secrets shorter than 16 characters, failing fast at startup.

---

## 5. Frontend Security Audit & Verification

- **Audit Findings:** Frontend code was audited across `frontend/client/src/`. No private credentials, database URIs, or server signing keys are referenced. Only public endpoints (`VITE_API_BASE_URL` / `VITE_API_URL`) are read by the client.
- **Typecheck:** `npm run check` passed with **0 errors**.
- **Production Build:** `npm run build` completed successfully with **0 errors**, emitting clean bundles to `dist/public/`.

---

## 6. Backend Test Results

Ran automated pytest test suite (`test_config_security.py`, `test_auth.py`, `test_rbac.py`, `test_admin.py`):
```text
tests/test_config_security.py .....                                      [  6%]
tests/test_auth.py .......                                               [ 16%]
tests/test_rbac.py .........................                             [ 50%]
tests/test_admin.py ....................................                 [100%]
====================== 73 passed, 15 warnings in 16.47s =======================
```

---

## 7. Status of Credential Rotation & Git History Cleanup

> [!CAUTION]
> **1. Credential Rotation is REQUIRED:**  
> Because the MongoDB Atlas connection credentials were committed in previous git history commits (`8d320ec`, `abb597d`, etc.), the database user password must be rotated directly in the MongoDB Atlas console by the repository administrator.

> [!WARNING]
> **2. Git History Cleanup is REQUIRED before public release:**  
> To completely remove historical occurrences of the credentials from the git commit DAG, an administrator should execute a history-cleaning tool (e.g. `git-filter-repo` or BFG Repo-Cleaner) followed by a force-push to origin when all team members are coordinated.
> *(Per instruction, no history rewrite was performed automatically).*

---

## 8. Remaining Security Concerns

- All current working tree files and tracked files are now clean of real credentials.
- All secrets load dynamically from environment variables at runtime.
- Production environment configurations are guarded against weak default fallbacks.
- Ready for Phase 5C or final review.
