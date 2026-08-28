# ShikshaSetu Backend API Endpoints

**API Prefix:** `/api/v1`  
**Version:** 0.3.0

## Summary

- **Total Endpoints:** 32
- **Authenticated Endpoints:** 21
- **Public Endpoints:** 11
- **Modules:** 11

---

## Authentication Endpoints

### POST /api/v1/auth/register
**Description:** User registration endpoint  
**Authentication:** None  
**Request Body:** `RegisterRequest`  
**Response:** `UserResponse` (201 Created)  

### POST /api/v1/auth/login
**Description:** User login endpoint  
**Authentication:** None  
**Request Body:** `LoginRequest`  
**Response:** `TokenResponse` (200 OK)  

### GET /api/v1/auth/me
**Description:** Get current authenticated user  
**Authentication:** Required (JWT)  
**Response:** `UserResponse` (200 OK)  

---

## User Management Endpoints

### GET /api/v1/users/me
**Description:** Get current user profile  
**Authentication:** Required (JWT)  
**Response:** `UserResponse` (200 OK)  

### PUT /api/v1/users/me
**Description:** Update current user profile  
**Authentication:** Required (JWT)  
**Request Body:** `UserProfileUpdate`  
**Response:** `UserResponse` (200 OK)  

---

## Assessment Endpoints

### POST /api/v1/assessments
**Description:** Start an assessment attempt  
**Authentication:** Required (JWT)  
**Request Body:** `StartAssessmentRequest`  
**Response:** `AssessmentAttemptResponse` (201 Created)  

### GET /api/v1/assessments/{attempt_id}
**Description:** Get assessment attempt by ID  
**Authentication:** Required (JWT)  
**Path Parameters:** 
- `attempt_id` (string, required)

**Response:** `AssessmentAttemptResponse` (200 OK)  

### POST /api/v1/assessments/{attempt_id}/submit
**Description:** Submit assessment answers  
**Authentication:** Required (JWT)  
**Path Parameters:**
- `attempt_id` (string, required)

**Request Body:** `SubmitAssessmentRequest`  
**Response:** `AssessmentSubmissionResponse` (200 OK)  

### GET /api/v1/assessments/configs
**Description:** List all active assessment configurations  
**Authentication:** None  
**Response:** `list[AssessmentConfigurationResponse]` (200 OK)  

### GET /api/v1/assessments/configs/{competency_code}
**Description:** Get assessment configuration for a specific competency  
**Authentication:** None  
**Path Parameters:**
- `competency_code` (string, required)

**Response:** `AssessmentConfigurationResponse` (200 OK)  

---

## Capability Assessment Endpoints

### POST /api/v1/assessments/capability
**Description:** Create a capability assessment  
**Authentication:** Required (JWT)  
**Request Body:** `CapabilityAssessmentCreateRequest`  
**Response:** `CapabilityAssessmentResponse` (201 Created)  
**Notes:** Loads questions from question bank based on configuration

### GET /api/v1/assessments/capability
**Description:** List user's capability assessments  
**Authentication:** Required (JWT)  
**Query Parameters:**
- `competency_code` (string, optional) - Filter by competency
- `status_filter` (string, optional) - Filter by status (IN_PROGRESS, SUBMITTED)
- `limit` (integer, optional, default=100) - Maximum results

**Response:** `list[CapabilityAssessmentListResponse]` (200 OK)  

### GET /api/v1/assessments/capability/{assessment_id}
**Description:** Get a capability assessment  
**Authentication:** Required (JWT)  
**Path Parameters:**
- `assessment_id` (string, required)

**Response:** `CapabilityAssessmentResponse` (200 OK)  
**Notes:** Does not expose answer keys

### POST /api/v1/assessments/capability/{assessment_id}/submit
**Description:** Submit assessment answers  
**Authentication:** Required (JWT)  
**Path Parameters:**
- `assessment_id` (string, required)

**Request Body:** `CapabilityAssessmentSubmitRequest`  
**Response:** `CapabilityAssessmentSubmitResponse` (200 OK)  
**Notes:** Server-side scoring, evidence creation, and competency profile update

### GET /api/v1/assessments/capability/{assessment_id}/results
**Description:** Get assessment results  
**Authentication:** Required (JWT)  
**Path Parameters:**
- `assessment_id` (string, required)

**Response:** `CapabilityAssessmentResultsResponse` (200 OK)  

---

## Competency Endpoints

### GET /api/v1/competencies
**Description:** List all competencies  
**Authentication:** None  
**Response:** `list[CompetencyResponse]` (200 OK)  

### GET /api/v1/competencies/{competency_id}
**Description:** Get a specific competency  
**Authentication:** None  
**Path Parameters:**
- `competency_id` (string, required)

**Response:** `CompetencyResponse` (200 OK)  

---

## Role Endpoints

### GET /api/v1/roles
**Description:** List all roles  
**Authentication:** None  
**Response:** `list[RoleResponse]` (200 OK)  

### GET /api/v1/roles/{role_id}
**Description:** Get a specific role  
**Authentication:** None  
**Path Parameters:**
- `role_id` (string, required)

**Response:** `RoleResponse` (200 OK)  

### GET /api/v1/roles/{role_id}/requirements
**Description:** Get role competency requirements  
**Authentication:** None  
**Path Parameters:**
- `role_id` (string, required)

**Response:** `list[RoleRequirementResponse]` (200 OK)  

---

## Quiz Endpoints

### POST /api/v1/quizzes
**Description:** Create a quiz from learning material  
**Authentication:** Required (JWT)  
**Request Body:** `QuizCreateRequest`  
**Response:** `QuizResponse` (201 Created)  
**Notes:** Generated questions hide correct answers until submission

### GET /api/v1/quizzes/{quiz_id}
**Description:** Retrieve a quiz by ID  
**Authentication:** Required (JWT)  
**Path Parameters:**
- `quiz_id` (string, required)

**Response:** `QuizResponse` (200 OK)  
**Notes:** User can only retrieve their own quizzes

### POST /api/v1/quizzes/{quiz_id}/submit
**Description:** Submit quiz answers  
**Authentication:** Required (JWT)  
**Path Parameters:**
- `quiz_id` (string, required)

**Request Body:** `QuizSubmitRequest`  
**Response:** `QuizResultResponse` (200 OK)  
**Notes:** Server-side scoring, evidence creation, and competency profile update

---

## Skill Gap Endpoints

### GET /api/v1/skill-gaps/me
**Description:** Get skill gaps for authenticated employee  
**Authentication:** Required (JWT)  
**Response:** `SkillGapResponse` (200 OK)  

---

## AI & Document Processing Endpoints

### POST /api/v1/learning-materials/upload
**Description:** Upload a learning material document (PDF, DOCX, PPTX)  
**Authentication:** Required (JWT)  
**Content-Type:** `multipart/form-data`  
**Request:** File upload  
**Response:** `UploadResponse` (201 Created)  
**Notes:** Supported formats: PDF, DOCX, PPTX. Max size: 50MB (configurable)

### GET /api/v1/learning-materials/{material_id}
**Description:** Get learning material metadata  
**Authentication:** Required (JWT)  
**Path Parameters:**
- `material_id` (string, required)

**Response:** `LearningMaterialResponse` (200 OK)  

### POST /api/v1/learning-materials/{material_id}/generate-questions
**Description:** Generate grounded MCQs from a learning material  
**Authentication:** Required (JWT)  
**Path Parameters:**
- `material_id` (string, required)

**Request Body:** `GenerationRequest`  
**Response:** `GenerationResponse` (200 OK)  
**Notes:** Generates questions with source traceability

---

## Learning Resources & Recommendations Endpoints

### GET /api/v1/recommendations/me
**Description:** Get personalized learning recommendations  
**Authentication:** Required (JWT)  
**Query Parameters:**
- `limit` (integer, optional) - Maximum number of recommendations

**Response:** `RecommendationResponse` (200 OK)  
**Notes:** Uses user's skill gaps and role to generate ranked recommendations

### GET /api/v1/recommendations/resources/{resource_id}
**Description:** Get detailed information about a learning resource  
**Authentication:** Required (JWT)  
**Path Parameters:**
- `resource_id` (string, required) - Example: "IGOT-12345" or "NSSTA-PROTO-xxx"

**Response:** Resource document with metadata (200 OK)  

### GET /api/v1/recommendations/competencies/{competency_code}/resources
**Description:** Get all learning resources mapped to a competency  
**Authentication:** Required (JWT)  
**Path Parameters:**
- `competency_code` (string, required) - Example: "STAT-SAMPLING"

**Query Parameters:**
- `provider` (string, optional) - Filter by provider (IGOT, NSSTA)

**Response:** Competency resources with metadata (200 OK)  

### GET /api/v1/recommendations/resources/unmapped
**Description:** Get learning resources with no competency mappings  
**Authentication:** Required (JWT)  
**Query Parameters:**
- `provider` (string, optional) - Filter by provider (IGOT, NSSTA)
- `limit` (integer, optional, default=10) - Maximum results

**Response:** List of unmapped resources (200 OK)  
**Notes:** Browseable resources only

---

## Health Check Endpoint

### GET /api/v1/health
**Description:** Health check endpoint  
**Authentication:** None  
**Response:** `HealthResponse` (200 OK)  
**Response on Error:** 503 Service Unavailable

---

## Authentication

### JWT Token Format
- **Algorithm:** HS256 (configurable)
- **Expiration:** 60 minutes (configurable via JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
- **Secret:** Configured via JWT_SECRET environment variable

### Usage
Include the token in the `Authorization` header:
```
Authorization: Bearer <token>
```

---

## Error Responses

### 400 Bad Request
- Invalid request parameters
- Validation errors
- Business logic violations

### 401 Unauthorized
- Missing or invalid authentication token
- Expired token

### 403 Forbidden
- User lacks required permissions
- Access denied to resource

### 404 Not Found
- Resource not found
- Invalid resource ID

### 409 Conflict
- Duplicate resource (e.g., duplicate email)
- Quiz already submitted

### 413 Payload Too Large
- File exceeds maximum size limit

### 503 Service Unavailable
- Database is unavailable
- LLM provider not configured
- External service unavailable

---

## Configuration

### Environment Variables
- `API_PREFIX` - API prefix (default: `/api/v1`)
- `JWT_SECRET` - JWT signing secret
- `JWT_ALGORITHM` - JWT algorithm (default: `HS256`)
- `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` - Token expiration (default: 60)
- `MAX_UPLOAD_SIZE_MB` - Max file upload size (default: 50)
- `CHUNK_SIZE` - Document chunk size (default: 500)
- `CHUNK_OVERLAP` - Chunk overlap (default: 100)
- `MAX_QUESTIONS_PER_GENERATION` - Max questions per generation (default: 5)
- `LLM_PROVIDER` - LLM provider (mock, openai, gemini)
- `EMBEDDING_PROVIDER` - Embedding provider (mock, openai, gemini)
