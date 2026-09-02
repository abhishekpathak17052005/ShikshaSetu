"""Tests for recommendation caching and event-driven invalidation."""

import pytest
from app.learning_resources.cache import (
    get_cached_recommendations,
    set_cached_recommendations,
    invalidate_recommendations_cache,
)


def test_recommendation_cache_lifecycle():
    user_id = "test_user_123"
    fake_recs = {"recommendations": [{"resource_id": "RES-1", "score": 0.95}]}

    # Initially empty
    assert get_cached_recommendations(user_id) is None

    # Set cache
    set_cached_recommendations(user_id, fake_recs)
    cached = get_cached_recommendations(user_id)
    assert cached is not None
    assert cached["recommendations"][0]["resource_id"] == "RES-1"

    # Invalidate user cache
    invalidate_recommendations_cache(user_id)
    assert get_cached_recommendations(user_id) is None


def test_recommendation_cache_isolation_by_user():
    user_a = "user_a"
    user_b = "user_b"
    data_a = {"user": "a"}
    data_b = {"user": "b"}

    set_cached_recommendations(user_a, data_a)
    set_cached_recommendations(user_b, data_b)

    assert get_cached_recommendations(user_a) == data_a
    assert get_cached_recommendations(user_b) == data_b

    # Invalidate only user_a
    invalidate_recommendations_cache(user_a)
    assert get_cached_recommendations(user_a) is None
    assert get_cached_recommendations(user_b) == data_b

    # Invalidate all
    invalidate_recommendations_cache(None)
    assert get_cached_recommendations(user_b) is None
