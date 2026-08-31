# Phase 1C: Frontend Integration (Corrected Architecture)

**Objective**: Connect frontend to learning activities API. Display real activity tracking without artificial competency inflation.

## What Changes

### Current Frontend Issue
- Home.tsx uses **mock data** (no API calls)
- Does not show learning activity status
- Does not show supporting evidence flow

### Phase 1C Deliverables

#### 1. API Service (`frontend/client/src/services/api.ts`)
```typescript
// Axios client with auth interceptor
export class LearningActivitiesAPI {
  async startActivity(resourceId: string, competencyId: string)
  async getActivities(status?: string)
  async getActivity(activityId: string)
  async updateProgress(activityId: string, progress: number, duration?: number)
  async completeActivity(activityId: string, finalScore?: number)
}
```

#### 2. React Hook (`frontend/client/src/hooks/useLearningActivities.ts`)
```typescript
export function useLearningActivities() {
  const [activities, setActivities] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  
  const startActivity = async (resourceId, competencyId) => { }
  const completeActivity = async (activityId) => { }
  const updateProgress = async (activityId, progress) => { }
  const listActivities = async (status) => { }
  
  return { activities, loading, error, startActivity, completeActivity, updateProgress, listActivities }
}
```

#### 3. UI Components (`frontend/client/src/components/`)

**LearningActivityCard.tsx**
```
- Shows resource name
- Progress bar (0-100%)
- Status badge (Not Started, In Progress, Completed)
- Start/Continue/Complete buttons
- Associated competency
- Duration tracking
- Last accessed timestamp
```

**LearningActivityList.tsx**
```
- Filter: In Progress, Completed, All
- Sort: Recently Accessed, Recently Completed
- List of activities with cards
- Loading state
- Error handling
```

**CompetencyEvidencePanel.tsx**
```
- Shows current competency level (UNCHANGED by learning completion)
- Shows skill gap (UNCHANGED by learning completion)
- Shows evidence from learning (confidence: 0.3)
- Shows evidence from assessments (confidence: 0.8)
- Next step: "Complete an assessment to demonstrate skill"
```

#### 4. Home.tsx Updates
Replace:
```typescript
// REMOVE: Mock data (2000 lines)
const mockActivities = [...]
const mockCompetencyProfile = [...]
const mockGaps = [...]

// ADD: Real API calls
const { activities, loading } = useLearningActivities()
const { gaps, competencies } = useSkillGaps()

// Display real activities, gaps, and competency
```

#### 5. Recommendation Flow UI Update
When user clicks "Start Learning" on a recommendation:
```
Recommendation: "Improve Planning & Analysis (PA01)"
    ↓
  [Learn] button (opens resource picker)
    ↓
  Select resource from learning_resources API
    ↓
  startActivity(resource_id, "PA01")
    ↓
  LearningActivityCard shows In Progress
    ↓
  User studies...
    ↓
  completeActivity(activityId)
    ↓
  Response shows:
    - Activity: completed ✓
    - Evidence: generated (confidence 0.3) 
    - Competency: UNCHANGED (still 2.5)
    - Gap: UNCHANGED (still 1.5)
    - Next: "Take an assessment to update competency"
    ↓
  User clicks "Take Assessment"
    ↓
  [Capability Assessment UI]
    ↓
  Assessment submitted
    ↓
  Evidence created (type: CAPABILITY_ASSESSMENT, confidence: 0.8)
    ↓
  Competency updated (now 3.0)
    ↓
  Gap updated (now 1.0)
    ↓
  User sees reduced gap, updated recommendation
```

## Test Plan

### API Service Tests
```
✓ startActivity creates activity with correct status
✓ getActivities returns user's activities only
✓ updateProgress increments without modifying competency
✓ completeActivity returns evidence + unchanged competency
✓ Authentication required for all operations
```

### Component Tests
```
✓ LearningActivityCard displays correctly
✓ Progress bar updates on completeActivity
✓ CompetencyEvidencePanel shows correct values
✓ Evidence confidence displayed (0.3 vs 0.8)
✓ "Next step" message displays when appropriate
```

### Integration Tests
```
✓ User can start → track → complete learning activity
✓ Competency does NOT change after learning completion
✓ Evidence is recorded with confidence=0.3
✓ Frontend shows supporting evidence in UI
```

## Key UI Messages (Critical for SIH)

When activity completes:
```
✅ Learning Complete

Supporting Evidence Generated
Evidence Type: Learning Activity
Confidence: Supporting (0.3)

Your competency level remains: PA01 Level 2.5
Your skill gap remains: 1.5 levels

Next Step: Take a capability assessment to demonstrate your skill
and update your competency level.
```

When assessment completes:
```
✅ Assessment Complete

Demonstrated Capability Evidence
Evidence Type: Capability Assessment
Confidence: Authoritative (0.8)

✅ Competency updated: PA01 Level 3.0
✅ Skill gap improved: 1.0 levels
```

## Files to Create/Modify

**Create**:
- `frontend/client/src/services/api.ts` (150 lines)
- `frontend/client/src/hooks/useLearningActivities.ts` (80 lines)
- `frontend/client/src/components/LearningActivityCard.tsx` (100 lines)
- `frontend/client/src/components/LearningActivityList.tsx` (120 lines)
- `frontend/client/src/components/CompetencyEvidencePanel.tsx` (100 lines)
- `frontend/client/src/tests/useLearningActivities.test.ts` (80 lines)
- `frontend/client/src/tests/LearningActivityCard.test.tsx` (100 lines)

**Modify**:
- `frontend/client/src/pages/Home.tsx` (remove mock, add real API calls)
- `frontend/client/src/pages/Recommendation.tsx` (update "Start Learning" flow)

## Time Estimate
- API Service + Hook: 45 min
- Components: 90 min
- Home.tsx integration: 60 min
- Tests: 45 min
- **Total: ~4 hours**

## Success Criteria

✅ Frontend makes real API calls (no mock data)
✅ Learning activities display with real progress
✅ Competency level NOT changed by learning completion
✅ Supporting evidence shown in UI
✅ Clear messaging: "Assessment needed to update competency"
✅ E2E flow works: gap → recommend → learn → assess → competency → gap
✅ All existing tests pass
✅ New frontend tests added (10+)
