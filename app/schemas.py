from typing import Any

from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str


class PlayerSearchItem(BaseModel):
    player_name: str
    role_profile: str | None = None
    final_fantasy_score: float | None = None


class PlayerDerivedResponse(BaseModel):
    player_name: str
    scope: str
    role_profile: str
    final_fantasy_score: float
    instinct_score: float
    context_score: float
    base_relevance_score: float
    match_day_adjustment_score: float
    involvement_score: float
    recent_form_score: float
    consistency_score: float
    selection_trust_score: float
    venue_score: float
    opponent_score: float
    format_score: float
    spin_matchup_score: float
    pace_matchup_score: float
    yorker_matchup_score: float
    short_ball_matchup_score: float
    strength_tags: list[str]
    risk_tags: list[str]


class PlayerHistoryRow(BaseModel):
    match_date: str | None
    event_name: str | None
    match_type: str | None
    team_name: str | None
    opponent_name: str | None
    venue: str | None
    runs: int | None = None
    balls: int | None = None
    wickets: int | None = None
    legal_balls_bowled: int | None = None
    runs_conceded: int | None = None


class SplitRow(BaseModel):
    split_category: str
    split_value: str
    balls: int
    runs: int
    dismissals: int
    strike_rate: float
    average: float | None


class LiveMatchSummary(BaseModel):
    id: str
    name: str | None = None
    status: str | None = None
    team_info: list[dict[str, Any]] = []
    venue: str | None = None
    date: str | None = None


class LiveMatchContext(BaseModel):
    match: dict[str, Any]
    squad: dict[str, Any] | None = None
    scorecard: dict[str, Any] | None = None


class ProviderLoginRequest(BaseModel):
    provider: str
    identity_token: str
    device_label: str | None = None


class RefreshRequest(BaseModel):
    refresh_token: str


class LogoutRequest(BaseModel):
    refresh_token: str


class UserResponse(BaseModel):
    id: int
    email: str | None = None
    display_name: str | None = None
    avatar_url: str | None = None
    plan_tier: str


class AuthResponse(BaseModel):
    user: UserResponse
    access_token: str
    refresh_token: str | None = None
    token_type: str = "bearer"
