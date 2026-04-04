from datetime import date

from app.aliases import resolve_player_name
from app.db import source_db


def cutoff_date(years: int) -> str:
    today = date.today()
    return f"{today.year - years:04d}-{today.month:02d}-{today.day:02d}"


def safe_div(a: float, b: float) -> float:
    return a / b if b else 0.0


def summarize_batting(row) -> dict:
    runs = row["runs"] or 0
    balls = row["balls"] or 0
    outs = row["outs"] or 0
    matches = row["matches"] or 0
    innings = row["innings"] or 0
    return {
        "matches": matches,
        "innings": innings,
        "runs": runs,
        "balls": balls,
        "average": round(safe_div(runs, outs), 2) if outs else None,
        "strike_rate": round(safe_div(runs * 100, balls), 2) if balls else 0.0,
    }


def summarize_bowling(row) -> dict:
    wickets = row["wickets"] or 0
    balls = row["legal_balls"] or 0
    runs = row["runs_conceded"] or 0
    innings = row["innings_bowled"] or 0
    return {
        "innings_bowled": innings,
        "balls_bowled": balls,
        "wickets": wickets,
        "runs_conceded": runs,
        "economy": round(safe_div(runs * 6, balls), 2) if balls else 0.0,
        "bowling_average": round(safe_div(runs, wickets), 2) if wickets else None,
        "bowling_strike_rate": round(safe_div(balls, wickets), 2) if wickets else None,
    }


def get_player_vs_venue(player_name: str, venue: str, years: int = 3) -> dict:
    player_name = resolve_player_name(player_name)
    cutoff = cutoff_date(years)
    with source_db() as conn:
        bat = conn.execute(
            """
            SELECT
                COUNT(*) AS matches,
                SUM(did_bat) AS innings,
                SUM(CASE WHEN dismissal != 'not out' AND dismissal != 'did not bat' THEN 1 ELSE 0 END) AS outs,
                SUM(runs) AS runs,
                SUM(balls) AS balls
            FROM player_match_batting
            WHERE player_name = ? AND venue = ? AND match_completed = 1 AND match_date >= ?
            """,
            (player_name, venue, cutoff),
        ).fetchone()
        bowl = conn.execute(
            """
            SELECT
                SUM(did_bowl) AS innings_bowled,
                SUM(legal_balls_bowled) AS legal_balls,
                SUM(wickets) AS wickets,
                SUM(runs_conceded) AS runs_conceded
            FROM player_match_bowling
            WHERE player_name = ? AND venue = ? AND match_completed = 1 AND match_date >= ?
            """,
            (player_name, venue, cutoff),
        ).fetchone()
    return {
        "player_name": player_name,
        "venue": venue,
        "years": years,
        "batting": summarize_batting(bat),
        "bowling": summarize_bowling(bowl),
    }


def get_player_vs_opponent(player_name: str, opponent: str, years: int = 3) -> dict:
    player_name = resolve_player_name(player_name)
    cutoff = cutoff_date(years)
    with source_db() as conn:
        bat = conn.execute(
            """
            SELECT
                COUNT(*) AS matches,
                SUM(did_bat) AS innings,
                SUM(CASE WHEN dismissal != 'not out' AND dismissal != 'did not bat' THEN 1 ELSE 0 END) AS outs,
                SUM(runs) AS runs,
                SUM(balls) AS balls
            FROM player_match_batting
            WHERE player_name = ? AND opponent_name = ? AND match_completed = 1 AND match_date >= ?
            """,
            (player_name, opponent, cutoff),
        ).fetchone()
        bowl = conn.execute(
            """
            SELECT
                SUM(did_bowl) AS innings_bowled,
                SUM(legal_balls_bowled) AS legal_balls,
                SUM(wickets) AS wickets,
                SUM(runs_conceded) AS runs_conceded
            FROM player_match_bowling
            WHERE player_name = ? AND opponent_name = ? AND match_completed = 1 AND match_date >= ?
            """,
            (player_name, opponent, cutoff),
        ).fetchone()
    return {
        "player_name": player_name,
        "opponent": opponent,
        "years": years,
        "batting": summarize_batting(bat),
        "bowling": summarize_bowling(bowl),
    }


def get_batter_vs_bowler(batter: str, bowler: str, years: int = 3) -> dict:
    batter = resolve_player_name(batter)
    bowler = resolve_player_name(bowler)
    cutoff = cutoff_date(years)
    with source_db() as conn:
        row = conn.execute(
            """
            SELECT
                COUNT(*) AS balls,
                SUM(batter_runs) AS runs,
                SUM(CASE WHEN wicket_flag = 1 AND player_out = batter_name THEN 1 ELSE 0 END) AS dismissals,
                SUM(CASE WHEN batter_runs IN (4, 6) THEN 1 ELSE 0 END) AS boundaries
            FROM player_ball_by_ball
            WHERE batter_name = ? AND bowler_name = ? AND match_date >= ?
            """,
            (batter, bowler, cutoff),
        ).fetchone()
    balls = row["balls"] or 0
    runs = row["runs"] or 0
    dismissals = row["dismissals"] or 0
    return {
        "batter": batter,
        "bowler": bowler,
        "years": years,
        "balls": balls,
        "runs": runs,
        "dismissals": dismissals,
        "boundaries": row["boundaries"] or 0,
        "strike_rate": round(safe_div(runs * 100, balls), 2) if balls else 0.0,
        "average": round(safe_div(runs, dismissals), 2) if dismissals else None,
    }
