import time
from typing import Any

import requests

from app.config import settings


class CricApiClient:
    def __init__(self) -> None:
        self.base_url = settings.cricapi_base_url.rstrip("/")
        self.api_key = settings.cricapi_key
        self.ttl = settings.live_cache_ttl_seconds
        self._cache: dict[str, tuple[float, Any]] = {}

    def _get(self, path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        if not self.api_key:
            raise RuntimeError("CRICAPI_KEY is not configured")
        params = dict(params or {})
        params["apikey"] = self.api_key
        cache_key = f"{path}:{sorted(params.items())}"
        now = time.time()
        cached = self._cache.get(cache_key)
        if cached and now - cached[0] < self.ttl:
            return cached[1]
        response = requests.get(f"{self.base_url}/{path}", params=params, timeout=20)
        response.raise_for_status()
        payload = response.json()
        self._cache[cache_key] = (now, payload)
        return payload

    def list_matches(self) -> dict[str, Any]:
        return self._get("matches", {"offset": 0})

    def get_series_info(self, series_id: str) -> dict[str, Any]:
        return self._get("series_info", {"id": series_id})

    def get_match_info(self, match_id: str) -> dict[str, Any]:
        return self._get("match_info", {"offset": 0, "id": match_id})

    def get_match_summary(self, match_id: str) -> dict[str, Any] | None:
        payload = self.list_matches()
        for match in payload.get("data") or []:
            if match.get("id") == match_id:
                return match
        return None

    def get_match_scorecard(self, match_id: str) -> dict[str, Any]:
        return self._get("match_scorecard", {"offset": 0, "id": match_id})

    def get_match_squad(self, match_id: str) -> dict[str, Any]:
        return self._get("match_squad", {"id": match_id})
