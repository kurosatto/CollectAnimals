import pytest


@pytest.fixture(autouse=True)
def _reset_rate_limits():
    """Every test starts with fresh rate limits (all test requests share one address)."""
    from app import limits
    for limit in limits.ALL:
        limit.clear()
    yield
