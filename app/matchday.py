from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from typing import Any

import requests

from app.config import settings
from app.live import CricApiClient


def now_utc() -> datetime:
    return datetime.now(UTC)


def parse_match_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    return dt if dt.tzinfo else dt.replace(tzinfo=UTC)


def _cache_path() -> Path:
    path = settings.matchday_cache_path
    return path if path.is_absolute() else settings.base_dir / path


def _read_cache() -> dict[str, Any]:
    path = _cache_path()
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _write_cache(payload: dict[str, Any]) -> None:
    path = _cache_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _get_cache_entry(section: str, key: str) -> dict[str, Any] | None:
    payload = _read_cache()
    return payload.get(section, {}).get(key)


def _put_cache_entry(section: str, key: str, value: Any) -> Any:
    payload = _read_cache()
    payload.setdefault(section, {})[key] = {
        "stored_at": now_utc().isoformat(),
        "value": value,
    }
    _write_cache(payload)
    return value


def _is_entry_fresh(entry: dict[str, Any] | None, ttl_seconds: int) -> bool:
    if not entry:
        return False
    stored_at = parse_match_datetime(entry.get("stored_at"))
    if not stored_at:
        return False
    return now_utc() - stored_at < timedelta(seconds=ttl_seconds)


def _extract_city_from_venue(venue: str | None) -> str | None:
    if not venue:
        return None
    parts = [part.strip() for part in venue.split(",") if part.strip()]
    if not parts:
        return None
    return parts[-1]


def _normalize_weather(summary: dict[str, Any]) -> str:
    parts: list[str] = []
    temp = summary.get("temperature_c")
    precip = summary.get("precipitation_probability")
    wind = summary.get("wind_speed_kmh")
    dew_point = summary.get("dew_point_c")
    if temp is not None:
        parts.append(f"{temp}C")
    if precip is not None:
        parts.append(f"{precip}% rain")
    if wind is not None:
        parts.append(f"{wind} km/h wind")
    if dew_point is not None and temp is not None and temp - dew_point <= 3:
        parts.append("high dew chance")
    return ", ".join(parts)


@dataclass
class WeatherClient:
    geocode_url: str = settings.weather_geocode_url
    forecast_url: str = settings.weather_forecast_url

    def get_match_weather(self, venue: str, match_dt: datetime | None) -> dict[str, Any] | None:
        city = _extract_city_from_venue(venue)
        if not city or not match_dt:
            return None

        cache_key = f"{city}:{match_dt.date().isoformat()}:{match_dt.hour}"
        entry = _get_cache_entry("weather", cache_key)
        if _is_entry_fresh(entry, settings.weather_cache_ttl_seconds):
            return entry["value"]

        try:
            geo = requests.get(
                self.geocode_url,
                params={"name": city, "count": 1, "language": "en", "format": "json"},
                timeout=20,
            )
            geo.raise_for_status()
            geo_payload = geo.json()
            results = geo_payload.get("results") or []
            if not results:
                return entry["value"] if entry else None

            lat = results[0]["latitude"]
            lon = results[0]["longitude"]
            forecast = requests.get(
                self.forecast_url,
                params={
                    "latitude": lat,
                    "longitude": lon,
                    "hourly": "temperature_2m,precipitation_probability,dew_point_2m,wind_speed_10m",
                    "timezone": "auto",
                    "start_date": match_dt.date().isoformat(),
                    "end_date": match_dt.date().isoformat(),
                },
                timeout=20,
            )
            forecast.raise_for_status()
            data = forecast.json().get("hourly") or {}
            times = data.get("time") or []
            target_hour = match_dt.astimezone().replace(minute=0, second=0, microsecond=0).isoformat(timespec="minutes")

            index = 0
            if times:
                for idx, value in enumerate(times):
                    if value.startswith(target_hour[:13]):
                        index = idx
                        break

            summary = {
                "city": city,
                "temperature_c": (data.get("temperature_2m") or [None])[index],
                "precipitation_probability": (data.get("precipitation_probability") or [None])[index],
                "dew_point_c": (data.get("dew_point_2m") or [None])[index],
                "wind_speed_kmh": (data.get("wind_speed_10m") or [None])[index],
            }
            summary["summary_text"] = _normalize_weather(summary)
            return _put_cache_entry("weather", cache_key, summary)
        except Exception:
            return entry["value"] if entry else None


class MatchdayService:
    def __init__(self, live_client: CricApiClient | None = None, weather_client: WeatherClient | None = None) -> None:
        self.live_client = live_client or CricApiClient()
        self.weather_client = weather_client or WeatherClient()

    def _series_schedule(self) -> list[dict[str, Any]]:
        if not settings.ipl_series_id:
            return []
        entry = _get_cache_entry("series", settings.ipl_series_id)
        if _is_entry_fresh(entry, settings.matchday_schedule_ttl_seconds):
            return entry["value"]
        try:
            payload = self.live_client.get_series_info(settings.ipl_series_id)
            matches = payload.get("data", {}).get("matchList") or []
            return _put_cache_entry("series", settings.ipl_series_id, matches)
        except Exception:
            return entry["value"] if entry else []

    def _match_info(self, match_id: str) -> dict[str, Any] | None:
        entry = _get_cache_entry("match_info", match_id)
        if _is_entry_fresh(entry, settings.matchday_info_ttl_seconds):
            return entry["value"]
        try:
            payload = self.live_client.get_match_info(match_id)
            data = payload.get("data")
            if data:
                return _put_cache_entry("match_info", match_id, data)
        except Exception:
            pass
        return entry["value"] if entry else None

    def _should_refresh_squad(self, match_dt: datetime | None, force: bool) -> bool:
        if force:
            return True
        if not match_dt:
            return False
        lead = timedelta(minutes=settings.squad_refresh_lead_minutes)
        return now_utc() >= match_dt - lead

    def _apply_local_squads(self, squad_data: list[dict[str, Any]]) -> list[dict[str, Any]]:
        local_path = settings.base_dir / "app" / "ipl_recent_squads.json"
        if not local_path.exists():
            return squad_data
        try:
            local_squads = json.loads(local_path.read_text(encoding="utf-8"))
        except Exception:
            return squad_data
        
        for team in squad_data:
            tname = team.get("teamName") or team.get("name")
            if tname and tname in local_squads:
                team["players"] = [{"name": p} for p in local_squads[tname]]
        return squad_data

    def _match_squad(self, match_id: str, match_dt: datetime | None, force: bool = False) -> list[dict[str, Any]] | None:
        entry = _get_cache_entry("match_squad", match_id)
        if _is_entry_fresh(entry, settings.matchday_squad_ttl_seconds):
            return self._apply_local_squads(entry["value"]) if entry.get("value") else None
        if not self._should_refresh_squad(match_dt, force):
            return self._apply_local_squads(entry["value"]) if entry else None
        try:
            payload = self.live_client.get_match_squad(match_id)
            data = payload.get("data")
            if data:
                _put_cache_entry("match_squad", match_id, data)
                return self._apply_local_squads(data)
        except Exception:
            pass
        return self._apply_local_squads(entry["value"]) if entry else None

    def get_today_ipl_matches(self, target_date: date | None = None, include_squads: bool = False) -> dict[str, Any]:
        target = target_date or now_utc().date()
        schedule = self._series_schedule()
        today_matches = [item for item in schedule if item.get("date") == target.isoformat()]
        enriched = []
        for match in today_matches:
            enriched.append(self._build_match_payload(match, include_squads=include_squads))
        return {"date": target.isoformat(), "competition": "Indian Premier League", "matches": enriched}

    def get_completed_ipl_matches(self) -> dict[str, Any]:
        from datetime import datetime, timezone
        schedule = self._series_schedule()
        past_matches = [item for item in schedule if item.get("matchEnded")]
        past_matches.sort(
            key=lambda x: parse_match_datetime(x.get("dateTimeGMT")) or datetime.min.replace(tzinfo=timezone.utc), 
            reverse=True
        )
        enriched = []
        for match in past_matches[:5]:
            enriched.append(self._build_match_payload(match, include_squads=False, skip_weather=True))
        return {"competition": "Indian Premier League", "matches": enriched}

    def get_match_detail(self, match_id: str, include_squads: bool = True) -> dict[str, Any] | None:
        schedule = self._series_schedule()
        match = next((item for item in schedule if item.get("id") == match_id), None)
        if not match:
            return None
        return self._build_match_payload(match, include_squads=include_squads)

    def _build_match_payload(self, match: dict[str, Any], include_squads: bool, skip_weather: bool = False) -> dict[str, Any]:
        match_id = match.get("id")
        info = self._match_info(match_id) if match_id else None
        base = info or match
        match_dt = parse_match_datetime(base.get("dateTimeGMT"))
        weather = None if skip_weather else self.weather_client.get_match_weather(base.get("venue"), match_dt)
        squads = self._match_squad(match_id, match_dt, force=include_squads) if match_id else None
        teams = base.get("teams") or []
        
        if not squads and teams:
            skeleton = [{"teamName": t} for t in teams]
            squads = self._apply_local_squads(skeleton)
            
        return {
            "id": match_id,
            "name": base.get("name"),
            "status": base.get("status"),
            "venue": base.get("venue"),
            "date": base.get("date"),
            "date_time_gmt": base.get("dateTimeGMT"),
            "teams": base.get("teams") or [],
            "team_info": base.get("teamInfo") or [],
            "has_squad": bool(base.get("hasSquad")),
            "fantasy_enabled": bool(base.get("fantasyEnabled")),
            "match_started": bool(base.get("matchStarted")),
            "match_ended": bool(base.get("matchEnded")),
            "weather": weather,
            "squads": squads,
            "squad_source": "actual" if self._should_refresh_squad(match_dt, force=False) else "probable",
        }
