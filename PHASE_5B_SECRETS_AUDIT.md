# Phase 5B — Secrets & Repository Hygiene Audit

**Audit Date:** 2026-09-06  
**Auditor:** Antigravity Engineering & Security Remediation Agent  
**Scope:** ShikshaSetu Repository (Root, Backend, Frontend, CI/CD, Deployment Configs, Git History)  
**Status:** COMPLETE — REMEDIATIONS IDENTIFIED  

---

## 1. Executive Summary

An audit of the ShikshaSetu codebase, configuration files, and git history was conducted in response to the P0 product audit finding:
> *"Sensitive credentials/secrets were present in the project/archive, including MongoDB URI, JWT secret and LLM/API key."*

The audit identified:
1. **Hardcoded Cloud Database Credentials:** Direct MongoDB Atlas connection strings with embedded credentials were hardcoded in `backend/create_demo_accounts.py`, `backend/scripts/live_prod_verify_final_3g.py`, and recorded in `backend/DIAGNOSIS_REPORT.md`.
2. **Historical Git Exposure:** The aforementioned credentials were committed to git history across several previous commits. **Credential exposure requires rotation.**
3. **Tracked Environment Configuration:** `frontend/.env.production` was actively tracked by git.
4. **Weak / Missing Production Fallback Safeguards:** `backend/app/core/config.py` permitted a default development JWT secret even when operating in production mode without validation.
5. **Frontend Safety:** Confirmed clean. No server secrets, private API keys, or database URIs are present in frontend client bundles.

---

## 2. Secrets Inventory & Findings by Category

| Category | Secret Variable / Type | Location(s) | Git Tracking Status | Real Credential vs Placeholder | Required at Runtime |
|---|---|---|---|---|---|
| **Database Connection String** | `MONGODB_URI` | `backend/create_demo_accounts.py` | Tracked | Real credential | Yes (Backend runtime) |
| **Database Connection String** | `MONGODB_URI` | `backend/scripts/live_prod_verify_final_3g.py` | Tracked | Real credential | Script only |
| **Database Connection String** | `MONGODB_URI` | `backend/DIAGNOSIS_REPORT.md` | Tracked | Real credential | No (Documentation) |
| **Database Connection String** | `MONGODB_URI` | `backend/.env` | Untracked (Ignored) | Real / Local config | Yes (Backend local dev) |
| **Auth Signing Secret** | `JWT_SECRET` / `SECRET_KEY` | `backend/app/core/config.py` | Tracked | Default placeholder fallback | Yes (Backend auth) |
| **LLM Provider Key** | `LLM_API_KEY` / `GEMINI_API_KEY` | `backend/app/core/config.py` | Tracked | Empty string (Mock fallback) | Optional (AI service) |
| **Frontend Public Config** | `VITE_API_URL` / `VITE_API_BASE_URL` | `frontend/.env.production` | Tracked | Public Render URL (Not a secret) | Yes (Frontend build) |
| **Frontend Public Config** | `VITE_API_URL` / `VITE_API_BASE_URL` | `frontend/.env.example` | Tracked | Public URL placeholder | No (Template) |

*(Note: In accordance with security constraints, no actual secret or credential strings are displayed in this report).*

---

## 3. Git Tracking & Git History Analysis

### 3.1 Tracked Sensitive Files
- `frontend/.env.production`: Tracked by git. Must be removed from git cache (`git rm --cached`) and ignored.
- `backend/create_demo_accounts.py`: Tracked by git. Hardcoded connection string must be replaced with configuration loading via `get_settings().mongodb_uri`.
- `backend/scripts/live_prod_verify_final_3g.py`: Tracked by git. Hardcoded connection string must be replaced with `os.environ.get("MONGODB_URI")` or `get_settings().mongodb_uri`.
- `backend/DIAGNOSIS_REPORT.md`: Tracked by git. Hardcoded connection string must be sanitized.

### 3.2 Git History Inspection
Git commit log inspection (`git log -S "<pattern>"`) revealed that MongoDB Atlas connection strings were committed historically in commits including `8d320ec`, `abb597d`, `dc5904d`, `d3f2d34`, and `ddc678f`.

> [!CAUTION]
> **Credential exposure requires rotation.**  
> Because credentials exist in git history, the MongoDB Atlas user password must be rotated immediately in the MongoDB Atlas console.

---

## 4. Configuration Architecture & Loading Mechanism

### 4.1 Backend
- **Local Development:** Loads from `.env` file via `pydantic_settings.BaseSettings` with `SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")`.
- **Production Deployment:** Reads environment variables supplied by the platform (e.g., Render, Docker).
- **Hardening Requirement:**
  - Support `AliasChoices("JWT_SECRET", "SECRET_KEY")` and `AliasChoices("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "ACCESS_TOKEN_EXPIRE_MINUTES")` for Render compatibility.
  - Enforce strict validation: when `APP_ENV=production`, reject default development secrets and fail fast with an informative error message if `JWT_SECRET` is missing or insecure.

### 4.2 Frontend
- **Local Development & Production:** Configured via Vite's `import.meta.env`.
- Public configurations (`VITE_API_BASE_URL`, `VITE_API_URL`) are read from environment variables during Vite compilation.
- No private secrets are exposed to or consumed by the client bundle.

---

## 5. Frontend Secret Check

- Inspected all occurrences of `import.meta.env` across `frontend/client/src/`.
- Found only:
  - `VITE_API_BASE_URL` / `VITE_API_URL`: Backend endpoint URLs.
  - `VITE_OAUTH_PORTAL_URL` / `VITE_APP_ID`: Generic OAuth redirection helpers.
  - `VITE_FRONTEND_FORGE_API_KEY`: Client-side map proxy reference.
- No private tokens, private API keys, database URLs, or JWT secrets are present in frontend source code.

---

## 6. Deployment Configuration (Render)

- `render.yaml` backend service defines:
  - `SECRET_KEY` with `generateValue: true`
  - `MONGODB_URI` with `sync: false` (to be set in Render dashboard)
  - `GEMINI_API_KEY` with `sync: false` (to be set in Render dashboard)
  - `APP_ENV: production`
- Compatibility verified: `app.core.config.Settings` updated to accept `SECRET_KEY` as an alias for `JWT_SECRET`.

---

## 7. Required Actions & Remediations

1. **Repository Hygiene:**
   - Update `.gitignore` in root and `frontend/.gitignore` to ignore `.env*` while preserving `!.env.example`.
   - Untrack `frontend/.env.production` from git cache.
   - Create root `.env.example` with clean placeholders.
   - Update `backend/.env.example` with comprehensive, safe placeholders.
2. **Eliminate Hardcoded Credentials:**
   - Refactor `backend/create_demo_accounts.py` to use `get_settings()`.
   - Refactor `backend/scripts/live_prod_verify_final_3g.py` to load `MONGODB_URI` dynamically.
   - Sanitize `backend/DIAGNOSIS_REPORT.md`.
3. **Production Security Guardrails:**
   - Add model validator in `backend/app/core/config.py` requiring a secure `JWT_SECRET` in production mode.
4. **Credential Rotation & History Cleanup (Manual Ops):**
   - Rotate MongoDB Atlas user credentials in the database host console.
   - Plan repository history sanitization prior to public distribution.
