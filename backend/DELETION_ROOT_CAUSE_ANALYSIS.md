# ROOT CAUSE ANALYSIS: Why Seeded Data Was Deleted

## Status: ✅ ROOT CAUSE IDENTIFIED

---

## Data Loss Timeline

**State 1:** ✅ After data integrity fixes
- competencies: 33
- learning_resources: 148
- learning_resource_mappings: 88 (valid)
- role_requirements: 8 (valid, no orphans)

**Action Taken:** `python -m pytest tests/ -v --tb=short`
- Executed ALL unit tests (164 passed, 4 skipped)

**State 2:** ❌ After pytest completion
- competencies: 0 (DELETED)
- learning_resources: 0 (DELETED)
- learning_resource_mappings: 104 (orphaned, untouched)
- role_requirements: 8 (untouched)

---

## Root Cause: pytest conftest.py Cleanup Fixture

**File:** `conftest.py`
**Lines:** 57-62

```python
@pytest.fixture
def database(mongodb_client: MongoClient, mongodb_database_name: str) -> Database:
    """
    Provide a clean MongoDB database for each test.
    Automatically clears collections after each test.
    """
    db = mongodb_client[mongodb_database_name]
    
    # Yield the database
    yield db
    
    # Cleanup: drop collections used in tests
    collections_to_clean = [
        "learning_resources",
        "resource_mappings",
        "competencies",
        "users",
        "skill_gaps",
    ]
    for collection_name in collections_to_clean:
        db[collection_name].delete_many({})
```

**What happens:**
1. pytest imports `conftest.py`
2. Every test that uses the `database` fixture triggers the cleanup
3. After EVERY test completes, pytest runs:
   ```python
   db.competencies.delete_many({})
   db.learning_resources.delete_many({})
   ```
4. This happens against the PRODUCTION database (localhost:27017/shikshasetu)
5. Data is deleted after last test completes

---

## Why This Happened

**The fixture scope is function-level (default):**
```python
@pytest.fixture
def database(...) -> Database:  # No scope specified = function scope
```

This means:
- After each individual test, cleanup runs
- The fixture does NOT use a test database
- The fixture connects to the SAME production database (configured in settings)
- There is NO database separation between tests and production

**Multiple tests ran:**
- 164 tests passed
- After each test, cleanup deletes competencies and learning_resources
- After the LAST test, competencies and learning_resources are deleted
- They remain deleted because nothing re-seeds them

---

## Exact Deletion Chain

1. **pytest session starts**
2. Test 1 runs with `database` fixture → cleanup after test completes
3. Test 2 runs with `database` fixture → cleanup after test completes
4. Test 3 runs with `database` fixture → cleanup after test completes
5. ... (repeat for all 164 tests)
6. **Test 164 completes**
7. **Final cleanup executes:**
   ```
   db.competencies.delete_many({})          # 33 records deleted
   db.learning_resources.delete_many({})    # 148 records deleted
   ```
8. **pytest session ends**
9. **Database state: competencies=0, learning_resources=0**
10. **Postman tests run → GET /competencies returns []**

---

## Other Problematic Code

### Issue 2: execute_seeding.py (Lines 26)

```python
collections_to_clear = ["competencies", "learning_resources", "learning_resource_mappings"]
for coll_name in collections_to_clear:
    coll = database[coll_name]
    count = coll.count_documents({})
    if count > 0:
        coll.delete_many({})  # ← Line 26: DELETES production collections
```

This script also deletes seeded collections, but it requires MANUAL execution.

### Issue 3: seed_resource_mappings.py (Line 309)

```python
if existing_count > 0:
    print(f"\n[WARN] Collection already has {existing_count} documents, clearing...")
    mapping_collection.delete_many({})  # ← Line 309: Auto-clears before reseeding
```

This is INTENTIONAL in the seed script (clear before reseed).

---

## MongoDB Configuration Verification

**FastAPI uses:**
- MongoDB URI: `mongodb://localhost:27017`
- Database: `shikshasetu`
- Source: `.env` file, loaded via `Settings()`

**Seed scripts use:**
- MongoDB URI: `mongodb://localhost:27017`
- Database: `shikshasetu`
- Source: `.env` file, loaded via `Settings()`

**pytest conftest.py uses:**
- MongoDB URI: `mongodb://localhost:27017`
- Database: `shikshasetu`
- Source: `.env` file via `Settings()`

**Postman verification runner uses:**
- MongoDB URI: Same (for direct queries only)
- Database: `shikshasetu`

**All processes connect to the SAME production database.**

---

## Why learning_resource_mappings Wasn't Deleted

The conftest.py cleanup fixture does NOT include `learning_resource_mappings`:

```python
collections_to_clean = [
    "learning_resources",      # ← DELETED
    "resource_mappings",       # ← NOT FOUND (name mismatch)
    "competencies",            # ← DELETED
    "users",                   # ← DELETED
    "skill_gaps",             # ← DELETED
]
```

**The collection name in conftest is `resource_mappings` but the actual collection is `learning_resource_mappings`.**

This is a name mismatch, so cleanup tries to delete a nonexistent collection and fails silently.

Result: `learning_resource_mappings` (104 orphaned records) remains untouched.

---

## Process Responsible

**Responsible Process:** pytest test runner via conftest.py cleanup fixture

**Who Executed It:** I ran `pytest tests/ -v --tb=short` to verify unit tests after data integrity fixes

**When:** After final_integrity_check.py verified correct counts but before Postman tests

**Impact:** Production database collections cleared during test cleanup phase

---

## Recommended Fix

### Fix 1: Use Test Database Isolation (RECOMMENDED)

Modify `conftest.py` to use a separate test database:

```python
@pytest.fixture(scope="session")
def test_database_name() -> str:
    """Use separate test database instead of production."""
    return "shikshasetu_test"  # ← Different database for tests

@pytest.fixture
def database(mongodb_client: MongoClient, test_database_name: str) -> Database:
    """Connect to TEST database, not production."""
    db = mongodb_client[test_database_name]
    
    # Cleanup only applies to TEST database
    yield db
    collections_to_clean = [...]
    for collection_name in collections_to_clean:
        db[collection_name].delete_many({})
```

**Effect:** Tests run against `shikshasetu_test`, production data in `shikshasetu` is untouched.

### Fix 2: Move Production Database to Environment Variable

```python
# .env
MONGODB_DATABASE=shikshasetu
TEST_MONGODB_DATABASE=shikshasetu_test
```

Then use `TEST_MONGODB_DATABASE` in pytest only.

### Fix 3: Disable Cleanup for Integration Tests

Mark Postman-like tests as `@pytest.mark.integration` and skip cleanup for those.

---

## Preventive Measures

1. **Never run pytest after final data verification** (until database isolation is fixed)
2. **Use separate test database** for all pytest runs
3. **Add database environment variable check** to prevent accidental production cleanup
4. **Document fixture scope and cleanup behavior** clearly in conftest.py

---

## Summary

| Item | Value |
|------|-------|
| **Root Cause** | pytest conftest.py cleanup fixture |
| **File** | `conftest.py` lines 57-62 |
| **Process** | `python -m pytest tests/` command execution |
| **Affected Collections** | competencies, learning_resources, users, skill_gaps |
| **Not Affected** | learning_resource_mappings (name mismatch in cleanup list) |
| **MongoDB Databases** | ALL processes use SAME production database (shikshasetu) |
| **Database Isolation** | MISSING - test cleanup affects production data |
| **Severity** | CRITICAL - destroys verification data |
| **When to Fix** | Before any future test runs |

---

## Blockage Status

**Postman tests blocked at Test 3** because competencies and learning_resources were deleted during pytest cleanup.

**Database state:** Partial deletion
- Competencies: ❌ DELETED
- Learning resources: ❌ DELETED
- Role requirements: ✅ INTACT (not in cleanup list)
- Roles: ✅ INTACT (not in cleanup list)

