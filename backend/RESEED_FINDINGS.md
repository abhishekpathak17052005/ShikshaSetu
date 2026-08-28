# RESEED VERIFICATION - CRITICAL FINDINGS

## Status: BLOCKED - Seed Script Bug Detected

During the reseeding and verification process, a critical bug was discovered in the seed_resource_mappings script that breaks all HTTP API calls to recommendations endpoints.

---

## BEFORE RESEED

```
competencies:                0
roles:                       1
role_requirements:          24 (orphaned)
learning_resources:          0
learning_resource_mappings: 104 (orphaned)
```

---

## AFTER RESEED

```
competencies:               33 ✅
roles:                       1 ✅
role_requirements:          32 (8 valid + 24 orphaned old records) ⚠️
learning_resources:        148 ✅ (63 iGOT + 85 NSSTA)
learning_resource_mappings: 88 (BUT ALL HAVE WRONG resource_id FORMAT) ❌
```

---

## CRITICAL BUG: Resource ID Mismatch

### Problem

The `seed_resource_mappings.py` script stores resource references incorrectly:

**What the script does:**
```python
all_mappings.append({
    "resource_id": resource_id,  # ← Stores MongoDB ObjectId (_id)
    "competency_id": competency_id,
    "competency_code": competency_code,
    ...
})
```

**What actually happens:**
- `resource_id` = `6a907717936a14f0bf23a281` (MongoDB ObjectId)

**What the HTTP API expects:**
- `resource_id` = `IGOT-do_1144751221174108161801` (human-readable ID from resource document)

### Evidence

**Learning Resources Collection:**
```
{
  "_id": ObjectId("6a907717936a14f0bf23a281"),
  "resource_id": "IGOT-do_1144751221174108161801",  ← This is the correct ID
  "provider": "IGOT",
  ...
}
```

**Learning Resource Mappings Collection (WRONG):**
```
{
  "_id": ObjectId("6a907757..."),
  "resource_id": "6a907717936a14f0bf23a281",  ← Should be "IGOT-do_1144751221174108161801"
  "competency_code": "TECH_AI_ML",
  "provider": "IGOT",
  ...
}
```

### Impact

**Query in HTTP API (learning_resources/router.py):**
```python
# API tries to find resources by resource_id field
resources = db.learning_resource_mappings.find({
    "resource_id": "6a907717936a14f0bf23a281"
})
# Finds mapping ✓

# But then tries to load the resource:
resource = db.learning_resources.find_one({
    "resource_id": resource_obj["resource_id"]  # Looks for "6a907717936a14f0bf23a281"
})
# NOT FOUND ❌ (should be "IGOT-do_1144751221174108161801")
```

### Result

All HTTP API endpoints that use resource_id fail:
- ❌ GET /recommendations/me returns 0 (no resources found)
- ❌ GET /recommendations/resources/unmapped returns 404
- ❌ Any endpoint joining mappings to resources fails

---

## VERIFICATION RESULTS

### Step 4: Role Requirements Integrity

```
Role: Statistical Officer
  Total requirements: 32
  Valid references:  8 ✓ (newly seeded competencies)
  Orphan references: 24 ✗ (from previous session - not cleared)
  Status: ✗ HAS ORPHANS
```

**Cause:** `seed_framework.py` uses `upsert=True` which doesn't delete old records.
**Impact:** Skill gap calculation may reference deleted competencies

### Step 5: Resource Mappings Integrity

```
Total mappings:           88
Valid mappings:            0 ❌ (ALL FAIL)
Orphan resource refs:     88 ✗
Orphan competency refs:    0 ✓

Sample mapping:
  Resource in mapping:  "6a907717936a14f0bf23a281" (ObjectId)
  Actual resource_id:   "IGOT-do_1144751221174108161801" (correct ID)
  Query result:         NOT FOUND ❌
```

---

## ROOT CAUSE

**Bug in seed_resource_mappings.py line ~210:**

```python
# WRONG: Stores _id instead of resource_id
all_mappings.append({
    "resource_id": resource_id,  # resource_id = doc["_id"] 
    ...
})

# Should be:
all_mappings.append({
    "resource_id": doc.get("resource_id"),  # Use the resource_id field, not _id
    ...
})
```

---

## POSTMAN VERIFICATION BLOCKED

**Current State:**
- ✅ Registration works
- ✅ Login works
- ✅ Competencies retrieval works
- ✅ Role data correct
- ❌ Resource mappings point to wrong resource IDs
- ❌ Skill gaps calculation requires valid competencies (24 orphaned records)
- ❌ Recommendations cannot be generated (no valid resource mappings)

**Tests that will fail:**
- ❌ Test 3: GET /competencies (returns 33, but role reqs are orphaned)
- ❌ Test 7: GET /skill-gaps/me (may fail due to orphaned competency refs)
- ❌ Test 8: GET /recommendations/me (0 recommendations, wrong resource_id in mappings)
- ❌ Test 10: GET /recommendations/resources/unmapped (404, resource_id mismatch)

---

## DECISION REQUIRED

**Two paths forward:**

### Option A: Fix the Seed Script
Modify `seed_resource_mappings.py` to store the correct `resource_id`:
```python
all_mappings.append({
    "resource_id": doc.get("resource_id"),  # NOT doc["_id"]
    ...
})
```

This requires modifying seed script code (not "application logic" per se).

### Option B: Work Around in API
Modify HTTP API routes to handle ObjectId format when querying resources (workaround).

This modifies application logic.

---

## CLEANUP ALSO NEEDED

The 24 orphaned role_requirements from the previous session need to be deleted:
```javascript
db.role_requirements.deleteMany({
  "competency_id": {$nin: [valid_competency_ids]}
})
```

But per instructions, this can only be done if explicitly authorized.

---

## RECOMMENDATION

**Fix the seed script bug** as it's a discovered issue during Postman testing, not pre-existing code.

Then:
1. Clear old mappings
2. Reseed mappings with correct resource_id format
3. Clear orphaned role_requirements
4. Reseed framework (or delete old orphaned records)
5. Re-run Postman verification

---

## BLOCKED AWAITING USER DECISION

Cannot proceed with Postman verification until:
1. Seed script bug is fixed, OR
2. API is modified to work around the bug, OR
3. User approves alternative approach

