"""In-memory recommendation cache with explicit event-driven invalidation."""

import time
from typing import Any, Dict, Optional

# In-memory recommendation cache: key -> (timestamp, data)
_RECOMMENDATION_CACHE: Dict[str, tuple[float, Any]] = {}
CACHE_TTL_SECONDS = 180.0  # 3-minute TTL safety boundary


def get_cached_recommendations(user_id: str, limit: Optional[int] = None) -> Optional[Any]:
    """Retrieve cached recommendation response if valid and unexpired."""
    key = f"{user_id}:{limit}"
    entry = _RECOMMENDATION_CACHE.get(key)
    if not entry:
        return None
    timestamp, data = entry
    if time.time() - timestamp > CACHE_TTL_SECONDS:
        _RECOMMENDATION_CACHE.pop(key, None)
        return None
    return data


def set_cached_recommendations(user_id: str, data: Any, limit: Optional[int] = None) -> None:
    """Store recommendation response in cache."""
    key = f"{user_id}:{limit}"
    _RECOMMENDATION_CACHE[key] = (time.time(), data)


def invalidate_recommendations_cache(user_id: Optional[str] = None) -> None:
    """
    Invalidate recommendation cache.
    
    Must be called whenever competency state changes:
    - Adaptive assessment completed
    - Quiz submitted
    - Learning activity completed
    - Role / competency profile reconciled
    """
    if user_id is None:
        _RECOMMENDATION_CACHE.clear()
        return

    uid_str = str(user_id)
    keys_to_del = [k for k in _RECOMMENDATION_CACHE if k.startswith(f"{uid_str}:") or k == uid_str]
    for k in keys_to_del:
        _RECOMMENDATION_CACHE.pop(k, None)
