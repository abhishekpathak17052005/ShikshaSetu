# ShikshaSetu Backend

Phase 1 and Phase 2 backend foundation for ShikshaSetu.

## Stack

- Python 3.12+
- FastAPI
- MongoDB with PyMongo
- Pydantic Settings
- pytest

## Setup

From the `backend` directory:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Start MongoDB locally, or set `MONGODB_URI` and `MONGODB_DATABASE` in `.env`.

## Run

From the `backend` directory:

```powershell
uvicorn app.main:app --reload
```

The API is available at `http://127.0.0.1:8000`. FastAPI documentation is at `/docs`.

## Seed Phase 2 Framework

The repeatable seed command creates or updates the five Phase 2 collections, 33 prototype competencies, the prototype Statistical Officer role, and eight role requirements:

```powershell
python -m app.scripts.seed_framework
```

The seed uses stable competency and role codes, so repeated runs do not create duplicates.

## API

```text
GET /api/v1/health
GET /api/v1/competencies
GET /api/v1/competencies/{competency_id}
GET /api/v1/roles
GET /api/v1/roles/{role_id}
GET /api/v1/roles/{role_id}/requirements
```

Phase 2 definitions are marked as prototype and are not official MoSPI or iGOT definitions. Competency evidence is append-only and scoring is intentionally not implemented yet.

## Authentication

Add these values to `.env` for local development:

```text
JWT_SECRET=change-this-development-secret-32
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=60
```

Never use the example secret outside development. Register an employee with an existing Phase 2 role:

```powershell
Invoke-RestMethod -Method Post http://127.0.0.1:8000/api/v1/auth/register -ContentType 'application/json' -Body '{"email":"employee@example.com","password":"correct-horse-battery","full_name":"Example Employee","role_id":"ROLE_OBJECT_ID","designation":"Statistical Officer","department":"Statistics","employee_id":"EMP-001"}'
```

Login returns a bearer token. Send it to protected endpoints:

```text
POST /api/v1/auth/login
GET  /api/v1/auth/me
GET  /api/v1/users/me
PUT  /api/v1/users/me
Authorization: Bearer <access_token>
```

Professional `role_id` and application `access_role` are separate. New registrations are `EMPLOYEE`; profile updates cannot change either authorization or professional role.

## Phase 4 Assessment

Seed the curated, deterministic prototype assessment after seeding the framework:

```powershell
python -m app.assessments.seed
```

Assessment flow:

```text
POST /api/v1/assessments
GET  /api/v1/assessments/{attempt_id}
POST /api/v1/assessments/{attempt_id}/submit
```

Knowledge and scenario results use the prototype 1–5 mapping of 0–19%=1, 20–39%=2, 40–59%=3, 60–79%=4, and 80–100%=5. The configured weights are self assessment 20%, knowledge 40%, scenario 30%, and training evidence 10%. Missing components are excluded and the available weights are renormalized. Prototype confidence equals available evidence-weight coverage.

## Health Check

```text
GET /api/v1/health
```

The endpoint returns HTTP 200 only when the application has a database handle and MongoDB responds to a ping. Database failures return HTTP 503 without exposing connection details.

## Test

From the `backend` directory:

```powershell
pytest
```

The tests mock database reachability and do not require a local MongoDB server.
