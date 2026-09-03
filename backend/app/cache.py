import time
from typing import Generic, TypeVar

T = TypeVar("T")

"""
A simple in-memory TTL cache for API responses
This cache is used to store API responses for a short period of time to avoid making unnecessary API calls
"""
class TTLCache(Generic[T]):

    def __init__(self, ttl_seconds: int = 60) -> None:
        self._ttl_seconds = ttl_seconds
        self._store: dict[str, tuple[float, T]] = {}

    def get(self, key: str) -> T | None:
        entry = self._store.get(key)
        if entry is None:
            return None
        expires_at, value = entry
        if time.monotonic() >= expires_at:
            del self._store[key]
            return None
        return value

    def set(self, key: str, value: T) -> None:
        self._store[key] = (time.monotonic() + self._ttl_seconds, value)
