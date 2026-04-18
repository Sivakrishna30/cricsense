from datetime import date

from fastapi import Body, FastAPI, Header, HTTPException, Query

from app.auth import delete_current_user_account, get_current_user_from_token, login_with_provider, refresh_session, revoke_refresh_token
from app.live import CricApiClient
from app.matchday import MatchdayService
from app.match_context import get_batter_vs_bowler, get_player_vs_opponent, get_player_vs_venue
from app.meta import TRANSPARENCY_PAYLOAD
from app.repositories import (
    find_best_player_match,
    get_event_coverage,
    get_player_derived,
    get_player_recent_history,
    get_player_style_splits,
    search_players,
    get_venue_stats,
)
from app.runtime import analyze_match, generate_teams
from app.schemas import AuthResponse, HealthResponse, LogoutRequest, ProviderLoginRequest, RefreshRequest
from app.db import analytics_db


app = FastAPI(title="CricSense Backend")
live_client = CricApiClient()
matchday_service = MatchdayService(live_client=live_client)


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok")


@app.post("/auth/provider-login", response_model=AuthResponse)
def auth_provider_login(payload: ProviderLoginRequest):
    return login_with_provider(payload.provider, payload.identity_token, payload.device_label)


@app.post("/auth/refresh", response_model=AuthResponse)
def auth_refresh(payload: RefreshRequest):
    refreshed = refresh_session(payload.refresh_token)
    return {**refreshed, "refresh_token": None}


@app.post("/auth/logout")
def auth_logout(payload: LogoutRequest):
    revoke_refresh_token(payload.refresh_token)
    return {"status": "ok"}


@app.get("/auth/me")
def auth_me(authorization: str | None = Header(default=None)):
    return get_current_user_from_token(authorization)


@app.delete("/auth/me")
def auth_delete_me(authorization: str | None = Header(default=None)):
    return delete_current_user_account(authorization)


@app.get("/system/status")
def system_status():
    with analytics_db() as conn:
        style_count = conn.execute("SELECT COUNT(*) FROM player_style_splits").fetchone()[0]
        profile_count = conn.execute("SELECT COUNT(*) FROM player_final_profiles").fetchone()[0]
    return {
        "analytics": {
            "player_style_splits": style_count,
            "player_final_profiles": profile_count,
        }
    }


@app.get("/meta/transparency")
def meta_transparency():
    return TRANSPARENCY_PAYLOAD


@app.get("/players/search")
def player_search(q: str = Query(..., min_length=2), limit: int = 10):
    return {"items": search_players(q, limit)}


@app.get("/players/{player_name}")
def player_summary(player_name: str):
    row = get_player_derived(player_name)
    if not row:
        raise HTTPException(status_code=404, detail="Player not found")
    return row


@app.get("/players/{player_name}/history")
def player_history(player_name: str, limit: int = 10):
    return get_player_recent_history(player_name, limit)


@app.get("/players/{player_name}/splits")
def player_splits(player_name: str, limit: int = 25):
    return {"items": get_player_style_splits(player_name, limit)}


@app.get("/coverage/events")
def coverage_events():
    return {"items": get_event_coverage()}


@app.get("/matchday/ipl/today")
def matchday_ipl_today(include_squads: bool = False, target_date: date | None = Query(default=None)):
    return matchday_service.get_today_ipl_matches(target_date=target_date, include_squads=include_squads)
@app.get("/matchday/ipl/completed")
def matchday_ipl_completed():
    return matchday_service.get_completed_ipl_matches()


@app.get("/matchday/ipl/matches/{match_id}")
def matchday_ipl_match(match_id: str, include_squads: bool = True):
    payload = matchday_service.get_match_detail(match_id, include_squads=include_squads)
    if not payload:
        raise HTTPException(status_code=404, detail="Match not found")
    return payload


@app.get("/context/player-vs-venue")
def player_vs_venue(player_name: str, venue: str, years: int = 3):
    return get_player_vs_venue(player_name, venue, years)


@app.get("/context/player-vs-opponent")
def player_vs_opponent(player_name: str, opponent: str, years: int = 3):
    return get_player_vs_opponent(player_name, opponent, years)


@app.get("/context/batter-vs-bowler")
def batter_vs_bowler(batter: str, bowler: str, years: int = 3):
    return get_batter_vs_bowler(batter, bowler, years)


@app.get("/context/venue-stats")
def venue_stats(venue: str):
    return get_venue_stats(venue) or {}


@app.post("/runtime/match-analysis")
def runtime_match_analysis(payload: dict = Body(...)):
    from app.runtime import apply_differential_modifiers
    mid = payload.get("match_id")
    if mid:
        from app.db import analytics_db
        import json
        with analytics_db() as conn:
            row = conn.execute("SELECT match_analysis_json FROM precalculated_matches WHERE match_id = ? AND conditions_hash = 'default'", (mid, )).fetchone()
            if row:
                base_data = json.loads(row[0])
                return apply_differential_modifiers(base_data, payload)
    return apply_differential_modifiers(analyze_match(payload), payload)


@app.get("/runtime/completed-insights")
def get_completed_insights(match_id: str):
    import json
    from app.db import analytics_db
    with analytics_db() as conn:
        row = conn.execute(
            "SELECT * FROM completed_match_insights WHERE match_id = ?", (match_id,)
        ).fetchone()
    if not row:
        return {
            "match_id": match_id,
            "status": "pending",
            "message": "Data not available for that match, check tomorrow.",
            "perfect_11": [],
            "predicted_teams": None
        }
    row = dict(row)
    return {
        "match_id": match_id,
        "match_name": row.get("match_name"),
        "match_date": row.get("match_date"),
        "perfect_11": json.loads(row["ipl_fantasy_11_json"] or "[]"),
        "predicted_teams": {
            "common_team_1": json.loads(row["cricsense_team1_json"]) if row.get("cricsense_team1_json") else None,
            "common_team_2": json.loads(row["cricsense_team2_json"]) if row.get("cricsense_team2_json") else None,
            "risky_team": json.loads(row["cricsense_risky_json"]) if row.get("cricsense_risky_json") else None,
        }
    }


@app.post("/runtime/team-generation")
def runtime_team_generation(payload: dict = Body(...)):
    from app.runtime import apply_differential_modifiers, generate_teams, analyze_match
    import json
    mid = payload.get("match_id")
    if mid:
        from app.db import analytics_db
        with analytics_db() as conn:
            row = conn.execute(
                "SELECT match_analysis_json, team_generation_json FROM precalculated_matches WHERE match_id = ? AND conditions_hash = 'default'",
                (mid,)
            ).fetchone()
            if row and row["team_generation_json"]:
                # Use precomputed teams, only reapply differential for user conditions
                base_analysis = json.loads(row["match_analysis_json"])
                modified = apply_differential_modifiers(base_analysis, payload)
                return generate_teams(modified)
    return generate_teams(payload)


@app.get("/live/matches")
def live_matches():
    return live_client.list_matches()


@app.get("/live/matches/{match_id}")
def live_match_context(match_id: str):
    return {
        "match": live_client.get_match_summary(match_id),
        "scorecard": live_client.get_match_scorecard(match_id),
        "squad": live_client.get_match_squad(match_id),
    }


@app.get("/live/matches/{match_id}/player-pool")
def live_match_player_pool(match_id: str):
    squad = live_client.get_match_squad(match_id)
    data = squad.get("data") or []
    matched_players = []
    unmatched_players = []

    for team in data:
        players = team.get("players") or []
        for player in players:
            player_name = player.get("name") or player.get("playerName") or ""
            if not player_name:
                continue
            derived = find_best_player_match(player_name)
            if derived:
                matched_players.append(
                    {
                        "team": team.get("teamName") or team.get("name"),
                        "source_name": player_name,
                        "matched_name": derived["player_name"],
                        "role_profile": derived["role_profile"],
                        "final_fantasy_score": derived["final_score"],
                        "instinct_score": derived["instinct_score"],
                        "context_score": derived["context_score"],
                        "base_stats_score": derived["base_stats_score"],
                    }
                )
            else:
                unmatched_players.append(
                    {
                        "team": team.get("teamName") or team.get("name"),
                        "source_name": player_name,
                    }
                )

    matched_players.sort(key=lambda item: item["final_fantasy_score"], reverse=True)
    return {
        "match_id": match_id,
        "matched_players": matched_players,
        "unmatched_players": unmatched_players,
    }
