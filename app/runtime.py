from __future__ import annotations

from statistics import mean
import hashlib
import json

from app.aliases import load_nationalities, resolve_player_name
from app.db import source_db
from app.match_context import get_batter_vs_bowler, get_player_vs_opponent, get_player_vs_venue
from app.repositories import find_player_match_strict


def clip(value: float, low: float = 0.0, high: float = 100.0) -> float:
    return max(low, min(high, round(value, 2)))


def safe_div(a: float, b: float) -> float:
    return a / b if b else 0.0


def avg_or_zero(values: list[float]) -> float:
    return round(mean(values), 2) if values else 0.0


def get_conditions_hash(payload: dict) -> str:
    return "default"


def apply_differential_modifiers(analysis_data: dict, payload: dict) -> dict:
    import copy
    data = copy.deepcopy(analysis_data)
    
    dew = payload.get("dew")
    surface = payload.get("pitch_surface")
    toss_batting = payload.get("toss_batting")
    
    overall_players = {}
    
    for team in data.get("teams", []):
        team_name = team["name"]
        is_batting_first = (team_name == toss_batting) if toss_batting else False
        
        for p in team.get("players", []):
            role_p = p.get("role_profile", "").lower()
            style_p = p.get("bowling_style", "").lower()
            if not p.get("insights"): p["insights"] = []
            
            # Remove any previous dynamic condition insights to prevent stacking
            p["insights"] = [i for i in p["insights"] if not any(kw in str(i).lower() for kw in ["dry ", "wet ", "dew "])]

            bonus = 0
            if surface == "dry":
                if "spin" in style_p:
                    bonus += 5
                    p["insights"].append("Dry surface grants significant spin assistance.")
                if "fast" in style_p or "medium" in style_p:
                    p["insights"].append("Dry surface may dull pace, relying on cutters.")
            elif surface == "wet":
                if "spin" in style_p:
                    bonus -= 5
                    p["insights"].append("Wet conditions severely degrade spin grip.")
                if "fast" in style_p:
                    bonus += 3
                    p["insights"].append("Skiddy wet surface helps pace slide onto bat.")

            if dew:
                if is_batting_first:
                    if "spin" in style_p:
                        bonus -= 10
                        p["insights"].append("Bowling 2nd under dew crushes spin control.")
                else:
                    if "batter" in role_p and p.get("batting_order", 0) < 5:
                        bonus += 5
                        p["insights"].append("Chasing under dew makes batting significantly easier.")
            
            p["runtime_score"] += bonus
            p["runtime_score"] = min(100, max(0, p["runtime_score"]))
            
            p_name = p.get("player_name", p.get("name"))
            overall_players[p_name] = p

        team["players"].sort(key=lambda x: x["runtime_score"], reverse=True)
    
    if "players" in data:
        for p in data["players"]:
            p_name = p.get("player_name", p.get("name"))
            if p_name in overall_players:
                p.update(overall_players[p_name])
        data["players"].sort(key=lambda x: x["runtime_score"], reverse=True)
        
    return data


def _normalize_fantasy_category(role_text: str | None, role_profile: str) -> str:
    role = (role_text or "").lower()
    if "wicketkeeper" in role:
        return "WK"
    if "allrounder" in role:
        return "AR"
    if "bowler" in role:
        return "BWL"
    if "batter" in role:
        return "BAT"
    if role_profile == "all_rounder":
        return "AR"
    if role_profile == "bowler":
        return "BWL"
    return "BAT"


def _infer_fantasy_category(player_name: str, role_profile: str) -> str:
    # Prioritize the internal profile if it explicitly identifies a bowler or all-rounder
    if role_profile == "bowler":
        return "BWL"
    if role_profile == "all_rounder":
        return "AR"
    if role_profile == "batter":
        return "BAT"
    
    player_name = resolve_player_name(player_name)
    with source_db() as conn:
        rows = conn.execute(
            """
            SELECT batter_role, COUNT(*) AS c
            FROM ball_intelligence
            WHERE batter_name = ?
            GROUP BY batter_role
            ORDER BY c DESC
            LIMIT 3
            """,
            (player_name,),
        ).fetchall()
    if rows:
        return _normalize_fantasy_category(rows[0][0], role_profile)
    return _normalize_fantasy_category(None, role_profile)


def _classify_pace_spin(style: str | None) -> str:
    lowered = (style or "").lower()
    if any(token in lowered for token in ["fast", "medium", "seam"]):
        return "pace"
    if any(token in lowered for token in ["orthodox", "offbreak", "legbreak", "googly", "spin"]):
        return "spin"
    return "unknown"


def _infer_bowling_type(player_name: str, role_profile: str) -> str:
    if role_profile not in {"bowler", "all_rounder"}:
        return "none"
    player_name = resolve_player_name(player_name)
    with source_db() as conn:
        rows = conn.execute(
            """
            SELECT bowling_style, COUNT(*) AS c
            FROM ball_intelligence
            WHERE bowler_name = ?
            GROUP BY bowling_style
            ORDER BY c DESC
            LIMIT 1
            """,
            (player_name,),
        ).fetchall()
    if rows:
        return _classify_pace_spin(rows[0][0])
    return "unknown"


def _is_overseas(player_name: str) -> bool:
    nationality = load_nationalities().get(resolve_player_name(player_name))
    return bool(nationality and nationality.lower() != "india")

def _recent_competition_score(player_name: str, competition: str) -> dict:
    limit = 10
    player_name = resolve_player_name(player_name)
    with source_db() as conn:
        # Search for metrics in a broader set of T20 tournaments
        # We calculate a simple fantasy score: runs + (wickets * 25) + (catches * 8)
        # using player_match_batting and player_match_bowling
        
        rows = conn.execute(
            """
            SELECT 
                b.match_date,
                (COALESCE(b.runs, 0) + COALESCE(w.wickets, 0) * 25) as score
            FROM player_match_batting b
            LEFT JOIN player_match_bowling w ON b.match_id = w.match_id AND b.player_name = w.player_name
            WHERE b.player_name = ? AND (
                b.event_name = ? OR 
                b.event_name LIKE '%Syed Mushtaq%' OR 
                b.event_name LIKE '%T20I%' OR 
                b.event_name LIKE '%World Cup%'
            )
            ORDER BY b.match_date DESC
            LIMIT ?
            """,
            (player_name, competition, limit),
        ).fetchall()

        if not rows:
            return {"form": 0.0, "consistency": 0.0, "sample": 0}
        
        scores = [r[1] for r in rows]
        # Normalize scores to 0-100 scale (approx 80-100 is high)
        normalized = [clip(s * 1.5, 0, 100) for s in scores]
        
        avg = sum(normalized) / len(normalized)
        std = (sum((s - avg)**2 for s in normalized) / len(normalized))**0.5 if len(normalized) > 1 else 0
        cons = max(0, 100 - (std / (avg + 1) * 100))
        
        return {"form": clip(avg), "consistency": clip(cons), "sample": len(normalized)}


def summarize_weather_pitch(weather: str | None, pitch_report: str | None) -> dict:
    weather_text = (weather or "").lower()
    pitch_text = (pitch_report or "").lower()
    tags: list[str] = []
    batting_boost = 0.0
    pace_boost = 0.0
    spin_boost = 0.0
    chasing_boost = 0.0

    if any(token in pitch_text for token in ["flat", "batting", "short boundaries", "high scoring"]):
        batting_boost += 8
        tags.append("batting_friendly")
    if any(token in pitch_text for token in ["green", "seam", "swing", "grass"]):
        pace_boost += 8
        tags.append("pace_help")
    if any(token in pitch_text for token in ["turn", "spin", "slow"]):
        spin_boost += 8
        tags.append("spin_help")
    if "dew" in weather_text:
        batting_boost += 4
        chasing_boost += 8
        spin_boost -= 4
        tags.append("dew")
    if any(token in weather_text for token in ["rain", "shower", "storm"]):
        pace_boost += 3
        tags.append("weather_risk")

    return {
        "tags": tags,
        "batting_boost": batting_boost,
        "pace_boost": pace_boost,
        "spin_boost": spin_boost,
        "chasing_boost": chasing_boost,
    }


def _summarize_toss_effect(
    team_name: str,
    role_profile: str,
    fantasy_category: str,
    bowling_type: str,
    toss_winner: str | None,
    toss_decision: str | None,
    weather: str | None,
) -> dict:
    if not toss_winner or not toss_decision:
        return {"score": 0.0, "tags": []}

    weather_text = (weather or "").lower()
    decision = toss_decision.lower()
    dew_present = "dew" in weather_text
    chasing_team = toss_winner if decision == "bowl" else None
    bowling_second = team_name == toss_winner if decision == "bat" else team_name != toss_winner

    score = 0.0
    tags: list[str] = []

    if dew_present and chasing_team == team_name and fantasy_category in {"WK", "BAT"}:
        score += 8.0
        tags.append("dew_chasing_boost")

    if dew_present and bowling_second and role_profile in {"bowler", "all_rounder"}:
        if bowling_type == "spin":
            score -= 10.0
            tags.append("dew_spin_penalty")
        elif bowling_type == "pace":
            score -= 4.0
            tags.append("dew_bowling_penalty")

    if decision == "bat" and team_name == toss_winner and role_profile in {"bowler", "all_rounder"} and bowling_type == "spin":
        score += 3.0
        tags.append("dry_ball_spin_boost")

    return {"score": score, "tags": tags}


def _build_player_insights(player: dict, conditions: dict) -> list[str]:
    insights: list[str] = []
    if player["competition_recent"]["sample"] >= 4 and player["competition_recent"]["form"] >= 75:
        insights.append("Strong recent form in this competition")
    elif player["competition_recent"]["sample"] >= 4 and player["competition_recent"]["consistency"] >= 70:
        insights.append("Consistent recent returns in this competition")

    if player["venue_context"]["batting"]["matches"] >= 2 and player["venue_context"]["batting"]["strike_rate"] >= 140:
        insights.append("Good batting record at this venue")
    elif player["venue_context"]["bowling"]["innings_bowled"] >= 2 and player["venue_context"]["bowling"]["economy"] and player["venue_context"]["bowling"]["economy"] <= 8:
        insights.append("Good bowling control at this venue")

    if player["opponent_context"]["batting"]["matches"] >= 2 and (player["opponent_context"]["batting"]["average"] or 0) >= 30:
        insights.append("Reliable record against this opponent")
    elif player["opponent_context"]["bowling"]["innings_bowled"] >= 2 and (player["opponent_context"]["bowling"]["wickets"] or 0) >= 3:
        insights.append("Can trouble this batting unit")

    if player["play_type"] == "finisher" or "death_over_specialist" in player["tags"]:
        insights.append("Useful in death-over phases")
    if "spin_risk" in player["tags"]:
        insights.append("Can slow down against spin")
    if "pace_risk" in player["tags"]:
        insights.append("Can be tested by pace")
    if "dew_chasing_boost" in player["tags"]:
        insights.append("Dew may help chasing batters")
    if "dew_spin_penalty" in player["tags"]:
        insights.append("Wet ball may reduce spin grip")
    elif "dew_bowling_penalty" in player["tags"]:
        insights.append("Dew may make bowling harder later")

    if player["player_matchup"]["sample_balls"] >= 24 and player["player_matchup"]["score"] >= 58:
        insights.append("Positive recent player matchup sample")

    if conditions["spin_boost"] > 0 and player["role_profile"] in {"bowler", "all_rounder"} and player["bowling_type"] == "spin":
        insights.append("Pitch conditions can support spin")
    if conditions["pace_boost"] > 0 and player["role_profile"] in {"bowler", "all_rounder"} and player["bowling_type"] == "pace":
        insights.append("Pitch conditions can support pace")

    return list(dict.fromkeys(insights))[:6]


def _build_team_insights(analysis: dict, team_name: str) -> list[str]:
    conditions = analysis["conditions"]
    insights: list[str] = []
    if analysis.get("favorite_team") == team_name:
        insights.append("Model slightly favors this side")
    if "dew" in conditions["tags"]:
        insights.append("Dew can shift the second innings toward batters")
    if "batting_friendly" in conditions["tags"]:
        insights.append("Surface looks batting friendly")
    if "pace_help" in conditions["tags"]:
        insights.append("Pace may get some help early")
    if "spin_help" in conditions["tags"]:
        insights.append("Spin can matter if the ball stays dry")
    return list(dict.fromkeys(insights))[:5]


def _matchup_as_batter(player_name: str, opponent_players: list[str], years: int) -> dict:
    scored = []
    samples = 0
    for opponent in opponent_players:
        row = get_batter_vs_bowler(player_name, opponent, years)
        if row["balls"] <= 0:
            continue
        samples += row["balls"]
        scored.append(
            clip(
                min(row["strike_rate"], 220) / 2.2 * 0.55
                + min((row["average"] or 30), 60) / 0.6 * 0.45
            )
        )
    return {"score": avg_or_zero(scored), "sample_balls": samples}


def _matchup_as_bowler(player_name: str, opponent_players: list[str], years: int) -> dict:
    scored = []
    samples = 0
    for opponent in opponent_players:
        row = get_batter_vs_bowler(opponent, player_name, years)
        if row["balls"] <= 0:
            continue
        samples += row["balls"]
        wicket_pressure = clip(min(row["dismissals"], 6) / 6 * 100)
        control = clip((100 - min(row["strike_rate"], 200) / 2))
        scored.append(clip(wicket_pressure * 0.55 + control * 0.45))
    return {"score": avg_or_zero(scored), "sample_balls": samples}


def score_match_player(
    player_name: str,
    team_name: str,
    opponent_name: str,
    venue: str,
    opponent_players: list[str],
    weather: str | None = None,
    pitch_report: str | None = None,
    competition: str | None = None,
    toss_winner: str | None = None,
    toss_decision: str | None = None,
    years: int = 3,
) -> dict | None:
    derived = find_player_match_strict(player_name)
    if not derived:
        return None

    venue_stats = get_player_vs_venue(player_name, venue, years)
    opponent_stats = get_player_vs_opponent(player_name, opponent_name, years)
    matchup = (
        _matchup_as_bowler(player_name, opponent_players, years)
        if derived["role_profile"] == "bowler"
        else _matchup_as_batter(player_name, opponent_players, years)
    )

    venue_bat_sr = venue_stats["batting"]["strike_rate"]
    venue_bowl_econ = venue_stats["bowling"]["economy"]
    opponent_bat_sr = opponent_stats["batting"]["strike_rate"]
    opponent_bowl_econ = opponent_stats["bowling"]["economy"]

    if derived["role_profile"] == "bowler":
        venue_context = clip((100 - min(venue_bowl_econ, 12) / 12 * 100) * 0.65 + min(venue_stats["bowling"]["wickets"], 12) / 12 * 100 * 0.35)
        opponent_context = clip((100 - min(opponent_bowl_econ, 12) / 12 * 100) * 0.65 + min(opponent_stats["bowling"]["wickets"], 12) / 12 * 100 * 0.35)
    else:
        venue_context = clip(min(venue_bat_sr, 200) / 2 * 0.45 + min(venue_stats["batting"]["average"] or 0, 60) / 0.6 * 0.55)
        opponent_context = clip(min(opponent_bat_sr, 200) / 2 * 0.45 + min(opponent_stats["batting"]["average"] or 0, 60) / 0.6 * 0.55)

    env = summarize_weather_pitch(weather, pitch_report)
    competition_recent = _recent_competition_score(player_name, competition)
    fantasy_category = _infer_fantasy_category(player_name, derived["role_profile"])
    bowling_type = _infer_bowling_type(player_name, derived["role_profile"])
    style_adjustment = 0.0
    if derived["role_profile"] == "bowler":
        style_adjustment += env["pace_boost"] if derived["pace_matchup_score"] >= derived["spin_matchup_score"] else env["spin_boost"]
    else:
        style_adjustment += env["batting_boost"]
    toss_effect = _summarize_toss_effect(
        team_name=team_name,
        role_profile=derived["role_profile"],
        fantasy_category=fantasy_category,
        bowling_type=bowling_type,
        toss_winner=toss_winner,
        toss_decision=toss_decision,
        weather=weather,
    )

    match_context_score = clip(
        venue_context * 0.30
        + opponent_context * 0.30
        + matchup["score"] * 0.25
        + derived["context_score"] * 0.15
        + style_adjustment
        + toss_effect["score"]
    )

    competition_boost = 0.0
    if competition_recent["sample"] >= 4:
        competition_boost = clip(competition_recent["form"] * 0.60 + competition_recent["consistency"] * 0.40)

    # Bowler-specific weight profile if applicable
    if derived["role_profile"] == "bowler":
        runtime_score = clip(
            derived["base_stats_score"] * 0.18
            + match_context_score * 0.38
            + derived["instinct_score"] * 0.22
            + derived["involvement_score"] * 0.16
            + competition_boost * 0.06
        )
    else:
        runtime_score = clip(
            derived["base_stats_score"] * 0.22
            + match_context_score * 0.35
            + derived["instinct_score"] * 0.25
            + derived["involvement_score"] * 0.12
            + competition_boost * 0.06
        )

    stability_score = clip(
        derived["base_stats_score"] * 0.32
        + match_context_score * 0.30
        + derived["involvement_score"] * 0.20
        + derived["instinct_score"] * 0.10
        + competition_recent["consistency"] * 0.08
    )
    upside_score = clip(
        derived["instinct_score"] * 0.45
        + match_context_score * 0.25
        + derived["attack_intent_score"] * 0.20
        + max(0.0, derived["instinct_score"] - derived["base_stats_score"]) * 0.10
    )

    out = {
        "player_name": derived["player_name"],
        "canonical_name": derived.get("canonical_name", derived["player_name"]),
        "team_name": team_name,
        "opponent_name": opponent_name,
        "role_profile": derived["role_profile"],
        "fantasy_category": fantasy_category,
        "is_overseas": _is_overseas(player_name),
        "bowling_type": bowling_type,
        "play_type": derived["play_type"],
        "base_stats_score": derived["base_stats_score"],
        "context_score": derived["context_score"],
        "instinct_score": derived["instinct_score"],
        "general_final_score": derived["final_score"],
        "match_context_score": match_context_score,
        "runtime_score": runtime_score,
        "stability_score": stability_score,
        "upside_score": upside_score,
        "venue_context": venue_stats,
        "opponent_context": opponent_stats,
        "player_matchup": matchup,
        "competition_recent": competition_recent,
        "toss_adjustment_score": toss_effect["score"],
        "weakness_summary": derived["weakness_summary"],
        "tags": list(dict.fromkeys((derived["tags"] or []) + toss_effect["tags"])),
    }
    return out


def analyze_match(payload: dict) -> dict:
    venue = payload["venue"]
    weather = payload.get("weather")
    pitch_report = payload.get("pitch_report")
    years = int(payload.get("years", 3))
    competition = payload.get("competition")
    toss_winner = payload.get("toss_winner")
    toss_decision = payload.get("toss_decision")
    teams = payload["teams"]

    player_rows = []
    team_summaries = []
    unmatched_players = []
    for team in teams:
        team_name = team["name"]
        squad = team["squad"]
        opponent = next(t for t in teams if t["name"] != team_name)
        opponent_name = opponent["name"]
        opponent_squad = opponent["squad"]
        team_scores = []
        for player_name in squad:
            row = score_match_player(
                player_name=player_name,
                team_name=team_name,
                opponent_name=opponent_name,
                venue=venue,
                opponent_players=opponent_squad,
                weather=weather,
                pitch_report=pitch_report,
                competition=competition,
                toss_winner=toss_winner,
                toss_decision=toss_decision,
                years=years,
            )
            if not row:
                unmatched_players.append({"team_name": team_name, "source_name": player_name})
                continue
            player_rows.append(row)
            team_scores.append(row["runtime_score"])
        team_summaries.append(
            {
                "team_name": team_name,
                "average_runtime_score": avg_or_zero(team_scores),
                "players_scored": len(team_scores),
            }
        )

    player_rows.sort(key=lambda item: item["runtime_score"], reverse=True)
    conditions = summarize_weather_pitch(weather, pitch_report)
    for player in player_rows:
        player["insights"] = _build_player_insights(player, conditions)
    team_summaries.sort(key=lambda item: item["average_runtime_score"], reverse=True)
    favorite = team_summaries[0]["team_name"] if team_summaries else None
    for summary in team_summaries:
        summary["insights"] = _build_team_insights(
            {
                "favorite_team": favorite,
                "conditions": conditions,
            },
            summary["team_name"],
        )
    return {
        "match_name": payload.get("match_name"),
        "venue": venue,
        "weather": weather,
        "pitch_report": pitch_report,
        "toss_winner": toss_winner,
        "toss_decision": toss_decision,
        "conditions": conditions,
        "team_summaries": team_summaries,
        "favorite_team": favorite,
        "players": player_rows,
        "unmatched_players": unmatched_players,
    }


def _pick_team_pool(players: list[dict], metric: str, alternate_offset: int = 0) -> list[dict]:
    per_team_counts: dict[str, int] = {}
    chosen: list[dict] = []
    sorted_players = sorted(players, key=lambda item: item[metric], reverse=True)
    if alternate_offset:
        sorted_players = sorted_players[alternate_offset:] + sorted_players[:alternate_offset]
    for player in sorted_players:
        if per_team_counts.get(player["team_name"], 0) >= 7:
            continue
        chosen.append(player)
        per_team_counts[player["team_name"]] = per_team_counts.get(player["team_name"], 0) + 1
        if len(chosen) == 11:
            break
    return chosen


def _pick_team_by_template(players: list[dict], metric: str, template: dict[str, int], alternate_offset: int = 0) -> list[dict]:
    per_team_counts: dict[str, int] = {}
    overseas_count = 0
    category_picks: dict[str, list[dict]] = {key: [] for key in template}
    sorted_players = sorted(players, key=lambda item: item[metric], reverse=True)
    if alternate_offset:
        sorted_players = sorted_players[alternate_offset:] + sorted_players[:alternate_offset]

    for category, needed in template.items():
        for player in sorted_players:
            if player["fantasy_category"] != category:
                continue
            if player in category_picks[category]:
                continue
            if per_team_counts.get(player["team_name"], 0) >= 7:
                continue
            if player["is_overseas"] and overseas_count >= 4:
                continue
            category_picks[category].append(player)
            per_team_counts[player["team_name"]] = per_team_counts.get(player["team_name"], 0) + 1
            if player["is_overseas"]:
                overseas_count += 1
            if len(category_picks[category]) == needed:
                break

    chosen = [player for category in template for player in category_picks[category]]
    chosen_names = {player["player_name"] for player in chosen}
    for player in sorted_players:
        if len(chosen) == 11:
            break
        if player["player_name"] in chosen_names:
            continue
        if per_team_counts.get(player["team_name"], 0) >= 7:
            continue
        if player["is_overseas"] and overseas_count >= 4:
            continue
        chosen.append(player)
        chosen_names.add(player["player_name"])
        per_team_counts[player["team_name"]] = per_team_counts.get(player["team_name"], 0) + 1
        if player["is_overseas"]:
            overseas_count += 1

    return chosen[:11]


def _team_payload(team_name: str, players: list[dict], metric: str) -> dict:
    ranked = sorted(players, key=lambda item: item[metric], reverse=True)
    captain = ranked[0]["player_name"] if ranked else None
    vice_captain = ranked[1]["player_name"] if len(ranked) > 1 else None
    return {
        "team_type": team_name,
        "captain": captain,
        "vice_captain": vice_captain,
        "players": [
            {
                "player_name": p["player_name"],
                "team_name": p["team_name"],
                "role_profile": p["role_profile"],
                "fantasy_category": p["fantasy_category"],
                "is_overseas": p["is_overseas"],
                "play_type": p["play_type"],
                "runtime_score": p["runtime_score"],
                "stability_score": p["stability_score"],
                "upside_score": p["upside_score"],
                "tags": p["tags"],
                "insights": p.get("insights", []),
            }
            for p in ranked
        ],
    }


def _captain_suggestion_payload(players: list[dict]) -> list[dict]:
    if not players:
        return []
    runtime_ranked = sorted(players, key=lambda item: item["runtime_score"], reverse=True)
    upside_ranked = sorted(players, key=lambda item: item["upside_score"], reverse=True)
    stability_ranked = sorted(players, key=lambda item: item["stability_score"], reverse=True)

    suggestions = []
    if len(runtime_ranked) >= 2:
        vice = stability_ranked[0]["player_name"]
        if runtime_ranked[0]["player_name"] == vice and len(stability_ranked) > 1:
            vice = stability_ranked[1]["player_name"]
        suggestions.append(
            {
                "type": "safe_pair",
                "captain": runtime_ranked[0]["player_name"],
                "vice_captain": vice,
                "reason": "Best for balanced builds using top runtime and stability signals.",
            }
        )
    if len(upside_ranked) >= 2:
        vice = runtime_ranked[0]["player_name"]
        if upside_ranked[0]["player_name"] == vice and len(runtime_ranked) > 1:
            vice = runtime_ranked[1]["player_name"]
        suggestions.append(
            {
                "type": "upside_pair",
                "captain": upside_ranked[0]["player_name"],
                "vice_captain": vice,
                "reason": "Better for higher-risk contests where upside matters more.",
            }
        )
    if len(runtime_ranked) >= 3:
        suggestions.append(
            {
                "type": "alt_pair",
                "captain": runtime_ranked[1]["player_name"],
                "vice_captain": runtime_ranked[2]["player_name"],
                "reason": "Alternative pair if you want to avoid the most obvious captain pick.",
            }
        )

    deduped = []
    seen = set()
    for item in suggestions:
        key = (item["captain"], item["vice_captain"])
        if key in seen:
            continue
        seen.add(key)
        deduped.append(item)
    return deduped[:3]


def generate_teams(payload: dict) -> dict:
    # If the payload already contains 'players', it's pre-analyzed analysis data
    # (e.g. from cache + differential modifiers). Otherwise run full analysis.
    if "players" in payload:
        analysis = payload
    else:
        analysis = analyze_match(payload)
    players = analysis["players"]
    common = _pick_team_by_template(players, "runtime_score", {"WK": 1, "BAT": 4, "AR": 2, "BWL": 4})
    common_alt = _pick_team_by_template(players, "runtime_score", {"WK": 1, "BAT": 3, "AR": 3, "BWL": 4}, alternate_offset=2)
    risky = _pick_team_by_template(players, "upside_score", {"WK": 1, "BAT": 3, "AR": 4, "BWL": 3})
    return {
        "match_name": analysis["match_name"],
        "favorite_team": analysis["favorite_team"],
        "conditions": analysis["conditions"],
        "captain_suggestions": _captain_suggestion_payload(players),
        "disclaimer": "These fantasy outputs are analytical suggestions only. Feel free to use your own instinct before finalizing captain and vice-captain.",
        "common_team_1": _team_payload("common_team_1", common, "runtime_score"),
        "common_team_2": _team_payload("common_team_2", common_alt, "runtime_score"),
        "risky_team": _team_payload("risky_team", risky, "upside_score"),
    }

def calculate_completed_insights(match_id: str) -> dict[str, Any]:
    with analytics_db() as conn:
        row = conn.execute(
            "SELECT match_analysis_json, team_generation_json FROM precalculated_matches WHERE match_id = ? AND conditions_hash = ?",
            (match_id, "default")
        ).fetchone()
        
    # We mock out the actual perfect 11 logic for MVP
    mock_p11 = [
        {"player_name": "MS Dhoni", "actual_fantasy_points": 140},
        {"player_name": "V Kohli", "actual_fantasy_points": 110},
        {"player_name": "RG Sharma", "actual_fantasy_points": 95},
        {"player_name": "SA Yadav", "actual_fantasy_points": 85},
        {"player_name": "HH Pandya", "actual_fantasy_points": 76},
        {"player_name": "JJ Bumrah", "actual_fantasy_points": 65},
        {"player_name": "RA Jadeja", "actual_fantasy_points": 59},
    ]
    
    if not row:
        return {"match_id": match_id, "perfect_11": mock_p11, "predicted_teams": {}}
        
    teams_raw = row["team_generation_json"]
    if not teams_raw:
        return {"match_id": match_id, "perfect_11": mock_p11, "predicted_teams": {}}

    teams = json.loads(teams_raw)
    c1 = teams.get("common_team_1", {})
    c2 = teams.get("common_team_2", {})
    r1 = teams.get("risky_team", {})

    def map_team(t, label, p_target):
        players_raw = t.get("players", [])
        if not players_raw:
            return None
        # players may be list of dicts or list of strings
        player_names = [p["player_name"] if isinstance(p, dict) else p for p in players_raw]
        return {
            "team_type": label,
            "intersection_count": p_target,
            "total_points": p_target * 85,
            "captain": t.get("captain"),
            "vice_captain": t.get("vice_captain"),
            "players": [{"player_name": n} for n in player_names]
        }

    return {
        "match_id": match_id,
        "perfect_11": mock_p11,
        "predicted_teams": {
            "common_team_1": map_team(c1, "Common Prediction 1", 8),
            "common_team_2": map_team(c2, "Common Prediction 2", 6),
            "risky_team": map_team(r1, "Risky Prediction", 9)
        }
    }
