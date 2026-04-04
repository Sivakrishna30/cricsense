import json
import sqlite3
from collections import defaultdict
from pathlib import Path


SOURCE_DB_PATH = Path("cricsense.db")
OUTPUT_DB_PATH = Path("cricsense_analytics.db")


PLAYER_STYLE_SPLITS_SQL = """
CREATE TABLE IF NOT EXISTS player_style_splits (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    player_name TEXT NOT NULL,
    split_category TEXT NOT NULL,
    split_value TEXT NOT NULL,
    balls INTEGER NOT NULL DEFAULT 0,
    runs INTEGER NOT NULL DEFAULT 0,
    dismissals INTEGER NOT NULL DEFAULT 0,
    boundaries INTEGER NOT NULL DEFAULT 0,
    dots INTEGER NOT NULL DEFAULT 0,
    useful_events INTEGER NOT NULL DEFAULT 0,
    strike_rate REAL NOT NULL DEFAULT 0,
    average REAL,
    UNIQUE(player_name, split_category, split_value)
);
"""

PLAYER_FINAL_PROFILES_SQL = """
CREATE TABLE IF NOT EXISTS player_final_profiles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    player_name TEXT NOT NULL,
    role_profile TEXT NOT NULL,
    play_type TEXT NOT NULL,
    batting_style_hint TEXT,
    bowling_style_hint TEXT,
    base_stats_score REAL NOT NULL DEFAULT 0,
    context_score REAL NOT NULL DEFAULT 0,
    instinct_score REAL NOT NULL DEFAULT 0,
    final_score REAL NOT NULL DEFAULT 0,
    recent_form_score REAL NOT NULL DEFAULT 0,
    consistency_score REAL NOT NULL DEFAULT 0,
    selection_trust_score REAL NOT NULL DEFAULT 0,
    involvement_score REAL NOT NULL DEFAULT 0,
    pressure_score REAL NOT NULL DEFAULT 0,
    momentum_score REAL NOT NULL DEFAULT 0,
    attack_intent_score REAL NOT NULL DEFAULT 0,
    venue_score REAL NOT NULL DEFAULT 0,
    opponent_score REAL NOT NULL DEFAULT 0,
    format_score REAL NOT NULL DEFAULT 0,
    spin_matchup_score REAL NOT NULL DEFAULT 0,
    pace_matchup_score REAL NOT NULL DEFAULT 0,
    weakness_summary TEXT NOT NULL DEFAULT '',
    tags_json TEXT NOT NULL DEFAULT '[]',
    UNIQUE(player_name)
);
"""


def clip(value: float, low: float = 0.0, high: float = 100.0) -> float:
    return max(low, min(high, round(value, 2)))


def safe_div(a: float, b: float) -> float:
    return a / b if b else 0.0


def norm(value: float, benchmark: float) -> float:
    return clip((value / benchmark) * 100) if benchmark else 0.0


def useful_batting_innings_score(runs: int, sr: float) -> bool:
    return runs >= 30 or (runs >= 20 and sr >= 130)


def classify_pace_spin(style: str) -> str:
    lowered = (style or "").lower()
    if any(token in lowered for token in ["fast", "medium", "seam"]):
        return "pace"
    if any(token in lowered for token in ["orthodox", "offbreak", "legbreak", "googly", "spin"]):
        return "spin"
    return "unknown"


def reset_output_tables(connection: sqlite3.Connection) -> None:
    connection.execute("DROP TABLE IF EXISTS player_style_splits")
    connection.execute("DROP TABLE IF EXISTS player_final_profiles")
    connection.execute(PLAYER_STYLE_SPLITS_SQL)
    connection.execute(PLAYER_FINAL_PROFILES_SQL)
    connection.execute(
        "CREATE INDEX IF NOT EXISTS idx_player_style_split ON player_style_splits(player_name, split_category, split_value)"
    )
    connection.execute(
        "CREATE INDEX IF NOT EXISTS idx_player_final_profiles_name ON player_final_profiles(player_name)"
    )
    connection.commit()


def derive_style_splits(read_connection: sqlite3.Connection, write_connection: sqlite3.Connection) -> None:
    read_connection.row_factory = sqlite3.Row
    rows = read_connection.execute(
        """
        SELECT batter_name, bowling_style, ball_length, runs_off_bat, wicket_flag, player_dismissed
        FROM ball_intelligence
        """
    )

    aggregates: dict[tuple[str, str, str], dict] = defaultdict(
        lambda: {"balls": 0, "runs": 0, "dismissals": 0, "boundaries": 0, "dots": 0, "useful_events": 0}
    )

    for row in rows:
        player_name = row["batter_name"]
        bowling_style = row["bowling_style"] or "unknown"
        pace_spin = classify_pace_spin(bowling_style)
        ball_length = row["ball_length"] or "unknown"
        runs = row["runs_off_bat"] or 0
        dismissed = 1 if row["wicket_flag"] and row["player_dismissed"] == player_name else 0
        useful_event = 1 if runs in {4, 6} else 0
        for key in [
            (player_name, "bowling_style", bowling_style),
            (player_name, "pace_spin", pace_spin),
            (player_name, "ball_length", ball_length),
        ]:
            bucket = aggregates[key]
            bucket["balls"] += 1
            bucket["runs"] += runs
            bucket["dismissals"] += dismissed
            bucket["boundaries"] += useful_event
            bucket["dots"] += 1 if runs == 0 else 0
            bucket["useful_events"] += useful_event

    insert_rows = []
    for (player_name, split_category, split_value), bucket in aggregates.items():
        balls = bucket["balls"]
        runs = bucket["runs"]
        dismissals = bucket["dismissals"]
        strike_rate = round(safe_div(runs * 100, balls), 2) if balls else 0.0
        average = round(safe_div(runs, dismissals), 2) if dismissals else None
        insert_rows.append(
            (
                player_name,
                split_category,
                split_value,
                balls,
                runs,
                dismissals,
                bucket["boundaries"],
                bucket["dots"],
                bucket["useful_events"],
                strike_rate,
                average,
            )
        )

    write_connection.executemany(
        """
        INSERT INTO player_style_splits (
            player_name, split_category, split_value, balls, runs, dismissals,
            boundaries, dots, useful_events, strike_rate, average
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        insert_rows,
    )
    write_connection.commit()


def aggregate_scored_rows(rows, score_fn) -> float:
    values = [score_fn(row) for row in rows]
    return safe_div(sum(values), len(values)) if values else 0.0


def load_maps(read_connection: sqlite3.Connection, write_connection: sqlite3.Connection) -> dict:
    read_connection.row_factory = sqlite3.Row
    write_connection.row_factory = sqlite3.Row

    batting = {}
    for row in read_connection.execute(
        """
        SELECT
            player_name,
            COUNT(*) AS matches,
            SUM(did_bat) AS innings,
            SUM(CASE WHEN dismissal != 'not out' AND dismissal != 'did not bat' THEN 1 ELSE 0 END) AS outs,
            SUM(runs) AS runs,
            SUM(balls) AS balls,
            SUM(fours) AS fours,
            SUM(sixes) AS sixes
        FROM player_match_batting
        WHERE match_completed = 1
        GROUP BY player_name
        """
    ):
        batting[row["player_name"]] = dict(row)

    bowling = {}
    for row in read_connection.execute(
        """
        SELECT
            player_name,
            COUNT(*) AS matches,
            SUM(did_bowl) AS innings_bowled,
            SUM(legal_balls_bowled) AS legal_balls,
            SUM(runs_conceded) AS runs_conceded,
            SUM(wickets) AS wickets
        FROM player_match_bowling
        WHERE match_completed = 1
        GROUP BY player_name
        """
    ):
        bowling[row["player_name"]] = dict(row)

    players = [row["player_name"] for row in read_connection.execute("SELECT DISTINCT player_name FROM player_match_batting")]
    recent = {player_name: {"bat": [], "bowl": []} for player_name in players}
    for row in read_connection.execute(
        """
        SELECT * FROM (
            SELECT
                player_name, match_date, event_name, match_type, venue, opponent_name, team_name,
                did_bat, runs, balls, dismissal,
                ROW_NUMBER() OVER (PARTITION BY player_name ORDER BY match_date DESC) AS rn
            FROM player_match_batting
            WHERE match_completed = 1
        )
        WHERE rn <= 20
        """
    ):
        recent[row["player_name"]]["bat"].append(dict(row))

    for row in read_connection.execute(
        """
        SELECT * FROM (
            SELECT
                player_name, match_date, event_name, match_type, venue, opponent_name, team_name,
                did_bowl, wickets, legal_balls_bowled, runs_conceded,
                ROW_NUMBER() OVER (PARTITION BY player_name ORDER BY match_date DESC) AS rn
            FROM player_match_bowling
            WHERE match_completed = 1
        )
        WHERE rn <= 20
        """
    ):
        recent[row["player_name"]]["bowl"].append(dict(row))

    fielding = defaultdict(lambda: {"fielding_events": 0, "keeping_events": 0})

    commentary = defaultdict(
        lambda: {
            "pressure_total": 0.0,
            "momentum_total": 0.0,
            "attack_total": 0.0,
            "fielding_total": 0.0,
            "turning_points": 0,
            "rows": 0,
        }
    )
    for row in read_connection.execute(
        """
        SELECT
            batter_name,
            bowler_name,
            pressure_score,
            momentum_shift_score,
            fielding_impact_score,
            attack_intent_score,
            turning_point_flag
        FROM commentary_events
        WHERE source_type IN ('full', 'highlight')
        """
    ):
        pressure = row["pressure_score"] or 0.0
        momentum = row["momentum_shift_score"] or 0.0
        fielding_score = row["fielding_impact_score"] or 0.0
        attack = row["attack_intent_score"] or 0.0
        turning_point = row["turning_point_flag"] or 0
        for player_name, attack_weight in (
            (row["batter_name"], 1.0),
            (row["bowler_name"], 0.45),
        ):
            if not player_name:
                continue
            bucket = commentary[player_name]
            bucket["pressure_total"] += pressure
            bucket["momentum_total"] += momentum
            bucket["attack_total"] += attack * attack_weight
            bucket["fielding_total"] += fielding_score
            bucket["turning_points"] += turning_point
            bucket["rows"] += 1

    splits = defaultdict(dict)
    for row in write_connection.execute(
        """
        SELECT player_name, split_category, split_value, balls, runs, dismissals, boundaries, dots, useful_events, strike_rate, average
        FROM player_style_splits
        """
    ):
        splits[row["player_name"]][(row["split_category"], row["split_value"])] = dict(row)

    batting_venue_rows = defaultdict(list)
    batting_opponent_rows = defaultdict(list)
    batting_format_rows = defaultdict(list)
    bowling_venue_rows = defaultdict(list)
    bowling_opponent_rows = defaultdict(list)
    bowling_format_rows = defaultdict(list)
    close_rows = defaultdict(list)

    death_rows = defaultdict(lambda: {"bat_runs": 0, "bat_balls": 0, "wickets": 0, "bowl_runs": 0, "bowl_balls": 0})
    for row in read_connection.execute(
        """
        SELECT batter_name, SUM(batter_runs) AS bat_runs, COUNT(*) AS bat_balls
        FROM player_ball_by_ball
        WHERE over_number >= 16
        GROUP BY batter_name
        """
    ):
        death_rows[row["batter_name"]]["bat_runs"] = row["bat_runs"] or 0
        death_rows[row["batter_name"]]["bat_balls"] = row["bat_balls"] or 0
    for row in read_connection.execute(
        """
        SELECT bowler_name, SUM(total_runs) AS bowl_runs, COUNT(*) AS bowl_balls, SUM(wicket_flag) AS wickets
        FROM player_ball_by_ball
        WHERE over_number >= 16
        GROUP BY bowler_name
        """
    ):
        death_rows[row["bowler_name"]]["bowl_runs"] = row["bowl_runs"] or 0
        death_rows[row["bowler_name"]]["bowl_balls"] = row["bowl_balls"] or 0
        death_rows[row["bowler_name"]]["wickets"] = row["wickets"] or 0

    style_hints = defaultdict(lambda: {"batting_style_hint": None, "bowling_style_hint": None})

    favorite_opponents = {}

    return {
        "batting": batting,
        "bowling": bowling,
        "recent": recent,
        "fielding": fielding,
        "commentary": commentary,
        "splits": splits,
        "batting_venue_rows": batting_venue_rows,
        "batting_opponent_rows": batting_opponent_rows,
        "batting_format_rows": batting_format_rows,
        "bowling_venue_rows": bowling_venue_rows,
        "bowling_opponent_rows": bowling_opponent_rows,
        "bowling_format_rows": bowling_format_rows,
        "close_rows": close_rows,
        "death_rows": death_rows,
        "style_hints": style_hints,
        "favorite_opponents": favorite_opponents,
    }


def compute_style_matchup(split: dict) -> float:
    if not split:
        return 0.0
    scoring_rate = norm(min(split.get("strike_rate", 0), 180), 130)
    dismissal_resistance = norm(max(0.1, 40 / max(safe_div(split.get("runs", 0), max(split.get("dismissals", 0), 1)), 1)), 1)
    intent = norm(safe_div(split.get("boundaries", 0), max(split.get("balls", 1), 1)), 0.14)
    consistency = norm(max(0.1, 1 - safe_div(split.get("dots", 0), max(split.get("balls", 1), 1))), 0.75)
    return clip(scoring_rate * 0.35 + dismissal_resistance * 0.30 + intent * 0.20 + consistency * 0.15)


def batting_row_score(row: dict) -> float:
    sr = safe_div(row["runs"] * 100, row["balls"]) if row["balls"] else 0.0
    return clip(norm(min(row["runs"], 80), 35) * 0.55 + norm(min(sr, 180), 135) * 0.45)


def bowling_row_score(row: dict) -> float:
    econ = safe_div(row["runs_conceded"] * 6, row["legal_balls_bowled"]) if row["legal_balls_bowled"] else 99.0
    return clip(norm(min(row["wickets"], 4), 1.5) * 0.60 + norm(max(0.1, 8 / max(econ, 1)), 1) * 0.40)


def classify_recent_role(recent_bat: list[sqlite3.Row], recent_bowl: list[sqlite3.Row]) -> tuple[str, float, float]:
    bat_innings = sum(r["did_bat"] for r in recent_bat)
    bat_balls = sum(r["balls"] for r in recent_bat)
    bowl_innings = sum(r["did_bowl"] for r in recent_bowl)
    bowl_balls = sum(r["legal_balls_bowled"] for r in recent_bowl)
    if bat_innings >= 4 and bowl_innings >= 4 and bowl_balls >= 48:
        return "all_rounder", 0.55, 0.45
    if bowl_innings >= 5 and bowl_balls >= 60 and bat_balls < 120:
        return "bowler", 0.10, 0.90
    return "batter", 0.90, 0.10


def pick_play_type(role_profile: str, attack_intent_score: float, pressure_score: float, death_rows: dict) -> str:
    if role_profile == "bowler":
        if death_rows["wickets"] >= 10:
            return "death_over_specialist"
        return "strike_bowler"
    if role_profile == "all_rounder":
        if pressure_score >= 55:
            return "impact_all_rounder"
        return "utility_all_rounder"
    if death_rows["bat_balls"] >= 60 and safe_div(death_rows["bat_runs"] * 100, max(death_rows["bat_balls"], 1)) >= 150:
        return "finisher"
    if attack_intent_score >= 65:
        return "aggressive_batter"
    return "top_order_batter"


def compute_player_profile(player_name: str, maps: dict) -> tuple:
    batting = maps["batting"].get(player_name, {})
    bowling = maps["bowling"].get(player_name, {})
    recent = maps["recent"].get(player_name, {"bat": [], "bowl": []})
    fielding = maps["fielding"].get(player_name, {"fielding_events": 0, "keeping_events": 0})
    commentary = maps["commentary"].get(
        player_name,
        {
            "pressure_total": 0.0,
            "momentum_total": 0.0,
            "attack_total": 0.0,
            "fielding_total": 0.0,
            "turning_points": 0,
            "rows": 0,
        },
    )
    splits = maps["splits"].get(player_name, {})
    batting_venue_rows = maps["batting_venue_rows"].get(player_name, [])
    batting_opponent_rows = maps["batting_opponent_rows"].get(player_name, [])
    batting_format_rows = maps["batting_format_rows"].get(player_name, [])
    bowling_venue_rows = maps["bowling_venue_rows"].get(player_name, [])
    bowling_opponent_rows = maps["bowling_opponent_rows"].get(player_name, [])
    bowling_format_rows = maps["bowling_format_rows"].get(player_name, [])
    close_rows = maps["close_rows"].get(player_name, [])
    death_rows = maps["death_rows"].get(player_name, {"bat_runs": 0, "bat_balls": 0, "wickets": 0, "bowl_runs": 0, "bowl_balls": 0})
    style_hints = maps["style_hints"].get(player_name, {"batting_style_hint": None, "bowling_style_hint": None})
    favorite_opponent = maps["favorite_opponents"].get(player_name)

    recent_bat = recent["bat"]
    recent_bowl = recent["bowl"]
    role_profile, batting_weight, bowling_weight = classify_recent_role(recent_bat, recent_bowl)

    runs = batting.get("runs", 0) or 0
    balls = batting.get("balls", 0) or 0
    outs = batting.get("outs", 0) or 0
    fours = batting.get("fours", 0) or 0
    sixes = batting.get("sixes", 0) or 0
    wickets = bowling.get("wickets", 0) or 0
    legal_balls = bowling.get("legal_balls", 0) or 0
    runs_conceded = bowling.get("runs_conceded", 0) or 0
    innings = batting.get("innings", 0) or 0
    innings_bowled = bowling.get("innings_bowled", 0) or 0

    batting_avg = safe_div(runs, outs) if outs else 0.0
    batting_sr = safe_div(runs * 100, balls) if balls else 0.0
    runs_per_innings = safe_div(runs, innings)
    boundary_rate = safe_div((fours + sixes), balls)
    useful_innings = 0
    low_scores = 0
    for row in recent_bat:
        row_sr = safe_div(row["runs"] * 100, row["balls"]) if row["balls"] else 0.0
        if row["did_bat"] and useful_batting_innings_score(row["runs"], row_sr):
            useful_innings += 1
        if row["did_bat"] and row["runs"] < 10:
            low_scores += 1
    recent_bat_innings = sum(r["did_bat"] for r in recent_bat)
    recent_runs = sum(r["runs"] for r in recent_bat)
    recent_balls = sum(r["balls"] for r in recent_bat)
    recent_sr = safe_div(recent_runs * 100, recent_balls) if recent_balls else 0.0

    wickets_per_innings = safe_div(wickets, innings_bowled)
    bowling_avg = safe_div(runs_conceded, wickets) if wickets else 999.0
    bowling_econ = safe_div(runs_conceded * 6, legal_balls) if legal_balls else 99.0
    bowling_sr = safe_div(legal_balls, wickets) if wickets else 999.0
    recent_wickets = sum(r["wickets"] for r in recent_bowl)
    recent_legal = sum(r["legal_balls_bowled"] for r in recent_bowl)
    recent_runs_conceded = sum(r["runs_conceded"] for r in recent_bowl)
    recent_bowl_innings = sum(r["did_bowl"] for r in recent_bowl)
    recent_econ = safe_div(recent_runs_conceded * 6, recent_legal) if recent_legal else 99.0

    long_term_batter_floor = clip(
        norm(min(batting_avg, 60), 35) * 0.30
        + norm(min(batting_sr, 180), 135) * 0.25
        + norm(min(runs_per_innings, 55), 28) * 0.20
        + norm(safe_div(useful_innings, max(recent_bat_innings, 1)), 0.15) * 0.15
        + norm(min(boundary_rate, 0.22), 0.15) * 0.10
    )
    wicket_matches = sum(1 for row in recent_bowl if row["wickets"] >= 1)
    long_term_bowler_floor = clip(
        norm(min(wickets_per_innings, 3.0), 1.2) * 0.30
        + norm(max(0.1, 8 / max(bowling_econ, 1)), 1) * 0.30
        + norm(max(0.1, 28 / max(bowling_avg, 1)), 1) * 0.20
        + norm(max(0.1, 24 / max(bowling_sr, 1)), 1) * 0.10
        + norm(safe_div(wicket_matches, max(recent_bowl_innings, 1)), 0.45) * 0.10
    )
    long_term_floor_score = clip(long_term_batter_floor * batting_weight + long_term_bowler_floor * bowling_weight)

    recent_batting_score = clip(
        norm(min(recent_runs, 500), 260) * 0.45
        + norm(min(recent_sr, 180), 140) * 0.30
        + norm(min(safe_div(recent_runs, max(recent_bat_innings, 1)), 70), 28) * 0.25
    )
    recent_bowling_score = clip(
        norm(min(recent_wickets, 25), 10) * 0.60
        + norm(max(0.1, 8 / max(recent_econ, 1)), 1) * 0.40
    )
    recent_form_score = clip(recent_batting_score * batting_weight + recent_bowling_score * bowling_weight)

    consistency_batting = clip(
        norm(safe_div(useful_innings, max(recent_bat_innings, 1)), 0.60) * 0.60
        + norm(max(0.1, 1 - safe_div(low_scores, max(recent_bat_innings, 1))), 1) * 0.40
    )
    consistency_bowling = clip(
        norm(safe_div(wicket_matches, max(recent_bowl_innings, 1)), 0.45) * 0.55
        + norm(max(0.1, 8 / max(recent_econ, 1)), 1) * 0.45
    )
    consistency_score = clip(consistency_batting * batting_weight + consistency_bowling * bowling_weight)

    batting_event_scores = []
    batting_by_event = defaultdict(list)
    for row in recent_bat:
        if row["did_bat"]:
            batting_by_event[row["event_name"] or "unknown"].append(row)
    for event_rows in batting_by_event.values():
        event_runs = sum(r["runs"] for r in event_rows)
        event_balls = sum(r["balls"] for r in event_rows)
        event_sr = safe_div(event_runs * 100, event_balls) if event_balls else 0.0
        event_useful = sum(
            1
            for r in event_rows
            if useful_batting_innings_score(r["runs"], safe_div(r["runs"] * 100, r["balls"]) if r["balls"] else 0.0)
        )
        batting_event_scores.append(
            clip(
                norm(min(safe_div(event_runs, max(len(event_rows), 1)), 70), 28) * 0.45
                + norm(min(event_sr, 180), 140) * 0.30
                + norm(safe_div(event_useful, max(len(event_rows), 1)), 0.60) * 0.25
            )
        )

    bowling_event_scores = []
    bowling_by_event = defaultdict(list)
    for row in recent_bowl:
        if row["did_bowl"]:
            bowling_by_event[row["event_name"] or "unknown"].append(row)
    for event_rows in bowling_by_event.values():
        event_wickets = sum(r["wickets"] for r in event_rows)
        event_balls = sum(r["legal_balls_bowled"] for r in event_rows)
        event_runs_conceded = sum(r["runs_conceded"] for r in event_rows)
        event_econ = safe_div(event_runs_conceded * 6, event_balls) if event_balls else 99.0
        wicket_games = sum(1 for r in event_rows if r["wickets"] >= 1)
        bowling_event_scores.append(
            clip(
                norm(min(safe_div(event_wickets, max(len(event_rows), 1)), 3), 1) * 0.45
                + norm(max(0.1, 8 / max(event_econ, 1)), 1) * 0.35
                + norm(safe_div(wicket_games, max(len(event_rows), 1)), 0.45) * 0.20
            )
        )

    cross_tournament_batting_consistency = clip(
        (safe_div(sum(batting_event_scores), len(batting_event_scores)) if batting_event_scores else 0.0) * 0.80
        + norm(min(len(batting_event_scores), 4), 2) * 0.20
    )
    cross_tournament_bowling_consistency = clip(
        (safe_div(sum(bowling_event_scores), len(bowling_event_scores)) if bowling_event_scores else 0.0) * 0.80
        + norm(min(len(bowling_event_scores), 4), 2) * 0.20
    )
    cross_tournament_consistency_score = clip(
        cross_tournament_batting_consistency * batting_weight
        + cross_tournament_bowling_consistency * bowling_weight
    )

    selection_trust_score = clip(
        norm(safe_div(len(recent_bat) + len(recent_bowl), 20), 0.80) * 0.45
        + norm(safe_div(sum(1 for r in recent_bat if "Premier League" in (r["event_name"] or "") or "World Cup" in (r["event_name"] or "") or "Syed Mushtaq" in (r["event_name"] or "")), max(len(recent_bat), 1)), 0.50) * 0.55
    )

    base_stats_score = clip(
        recent_form_score * 0.35
        + consistency_score * 0.30
        + cross_tournament_consistency_score * 0.20
        + long_term_floor_score * 0.15
    )

    batting_involvement = clip(
        norm(min(safe_div(recent_balls, max(recent_bat_innings, 1)), 45), 20) * 0.55
        + norm(safe_div(recent_bat_innings, max(len(recent_bat), 1)), 0.85) * 0.25
        + norm(min(safe_div(recent_runs, max(recent_bat_innings, 1)), 60), 25) * 0.20
    )
    bowling_involvement = clip(
        norm(safe_div(recent_bowl_innings, max(len(recent_bowl), 1)), 0.60) * 0.40
        + norm(min(safe_div(recent_legal, max(recent_bowl_innings, 1)), 24), 18) * 0.35
        + norm(min(safe_div(recent_wickets, max(recent_bowl_innings, 1)), 3), 1) * 0.25
    )
    fielding_score = clip(min((fielding["fielding_events"] or 0) * 0.8, 15))
    keeping_score = clip(min((fielding["keeping_events"] or 0) * 2.0, 12))
    commentary_rows = commentary["rows"] or 0
    commentary_pressure = clip(norm(safe_div(commentary["pressure_total"], max(commentary_rows, 1)), 7.5))
    commentary_momentum = clip(norm(safe_div(commentary["momentum_total"], max(commentary_rows, 1)), 7.0))
    commentary_attack = clip(norm(safe_div(commentary["attack_total"], max(commentary_rows, 1)), 6.5))
    commentary_fielding = clip(norm(safe_div(commentary["fielding_total"], max(commentary_rows, 1)), 6.0))
    commentary_turning = clip(norm(min(commentary["turning_points"], 40), 10))

    if role_profile == "all_rounder":
        involvement_score = clip(
            batting_involvement * 0.40
            + bowling_involvement * 0.45
            + max(fielding_score, commentary_fielding) * 0.15
        )
    elif role_profile == "bowler":
        involvement_score = clip(
            bowling_involvement * 0.82
            + max(fielding_score, commentary_fielding) * 0.14
            + keeping_score * 0.04
        )
    else:
        involvement_score = clip(
            batting_involvement * 0.82
            + max(fielding_score, commentary_fielding) * 0.12
            + keeping_score * 0.06
        )

    spin_split = splits.get(("pace_spin", "spin"), {})
    pace_split = splits.get(("pace_spin", "pace"), {})
    spin_matchup_score = compute_style_matchup(spin_split)
    pace_matchup_score = compute_style_matchup(pace_split)
    bowling_style_scores = [
        compute_style_matchup(splits.get(("bowling_style", "Right arm Offbreak"), {})),
        compute_style_matchup(splits.get(("bowling_style", "Legbreak"), {})),
        compute_style_matchup(splits.get(("bowling_style", "Slow Left arm Orthodox"), {})),
    ]
    bowling_style_scores = [score for score in bowling_style_scores if score > 0]
    bowling_style_matchup_score = clip(sum(bowling_style_scores) / len(bowling_style_scores)) if bowling_style_scores else clip((spin_matchup_score + pace_matchup_score) / 2)

    venue_score = clip(recent_form_score * 0.50 + base_stats_score * 0.30 + commentary_momentum * 0.20)
    opponent_score = clip(
        recent_form_score * 0.40
        + clip((spin_matchup_score + pace_matchup_score) / 2) * 0.40
        + commentary_pressure * 0.20
    )
    format_score = clip(recent_form_score * 0.70 + base_stats_score * 0.30)
    recent_context_form = clip(recent_form_score * 0.70 + clip((spin_matchup_score + pace_matchup_score) / 2) * 0.30)
    context_score = clip(
        venue_score * 0.25
        + opponent_score * 0.25
        + format_score * 0.15
        + bowling_style_matchup_score * 0.20
        + recent_context_form * 0.15
    )

    close_match_impact = clip(recent_form_score * 0.35 + involvement_score * 0.35 + commentary_pressure * 0.30)
    death_phase_impact = clip(
        norm(min(safe_div(death_rows["bat_runs"] * 100, max(death_rows["bat_balls"], 1)), 220), 150) * batting_weight
        + norm(min(death_rows["wickets"], 12), 4) * bowling_weight
    )
    pressure_score = clip(
        close_match_impact * 0.35
        + death_phase_impact * 0.25
        + involvement_score * 0.15
        + commentary_pressure * 0.15
        + commentary_turning * 0.10
    )
    momentum_score = clip(
        norm(min((spin_split.get("boundaries", 0) if spin_split else 0) + (pace_split.get("boundaries", 0) if pace_split else 0), 120), 45) * 0.35
        + norm(min(wickets, 80), 25) * 0.35
        + commentary_momentum * 0.30
    )
    attack_intent_score = clip(
        norm(min(boundary_rate, 0.20), 0.14) * 0.35
        + norm(min(recent_sr, 180), 145) * 0.25
        + norm(min(death_rows["bat_runs"], 250), 100) * 0.15
        + commentary_attack * 0.25
    )
    bounce_back_score = clip(norm(max(0.1, 1 - safe_div(low_scores, max(recent_bat_innings, 1))), 1))
    smart_aggression_score = clip(
        norm(min(boundary_rate, 0.20), 0.14) * 0.50
        + norm(min(recent_sr, 180), 145) * 0.30
        + norm(max(0.1, 1 - safe_div(outs, max(balls, 1))), 1) * 0.20
    )
    instinct_score = clip(
        pressure_score * 0.30
        + momentum_score * 0.25
        + attack_intent_score * 0.20
        + smart_aggression_score * 0.15
        + bounce_back_score * 0.10
    )

    final_score = clip(
        base_stats_score * 0.35
        + context_score * 0.25
        + instinct_score * 0.25
        + recent_form_score * 0.10
        + involvement_score * 0.05
    )

    weakness_bits = []
    tags = []
    if role_profile == "batter" and death_rows["bat_balls"] >= 50 and safe_div(death_rows["bat_runs"] * 100, max(death_rows["bat_balls"], 1)) >= 150:
        tags.append("death_over_specialist")
    if role_profile == "bowler" and death_rows["wickets"] >= 10:
        tags.append("death_over_specialist")
    if pace_matchup_score >= spin_matchup_score + 12:
        weakness_bits.append("weak on spin")
        tags.append("spin_risk")
    elif spin_matchup_score >= pace_matchup_score + 12:
        weakness_bits.append("weak on pace")
        tags.append("pace_risk")
    if pressure_score >= 60:
        tags.append("clutch")
    if commentary_rows >= 8 and commentary_pressure >= 55:
        tags.append("handles_pressure")
    if recent_form_score >= 65:
        tags.append("in_form")
    if favorite_opponent:
        tags.append(f"likes {favorite_opponent}")
    if role_profile == "batter" and recent_bat_innings and safe_div(recent_runs, recent_bat_innings) >= 30:
        tags.append("reliable batter")
    if role_profile == "bowler" and recent_bowl_innings and safe_div(recent_wickets, recent_bowl_innings) >= 1:
        tags.append("wicket_taker")
    if role_profile == "all_rounder":
        tags.append("two_way_points")
    tags = list(dict.fromkeys(tags))[:6]

    weakness_summary = ", ".join(weakness_bits[:2])
    play_type = pick_play_type(role_profile, attack_intent_score, pressure_score, death_rows)

    return (
        player_name,
        role_profile,
        play_type,
        style_hints.get("batting_style_hint"),
        style_hints.get("bowling_style_hint"),
        base_stats_score,
        context_score,
        instinct_score,
        final_score,
        recent_form_score,
        consistency_score,
        selection_trust_score,
        involvement_score,
        pressure_score,
        momentum_score,
        attack_intent_score,
        venue_score,
        opponent_score,
        format_score,
        spin_matchup_score,
        pace_matchup_score,
        weakness_summary,
        json.dumps(tags),
    )


def derive_player_profiles(read_connection: sqlite3.Connection, write_connection: sqlite3.Connection) -> None:
    maps = load_maps(read_connection, write_connection)
    players = sorted(set(maps["batting"]) | set(maps["bowling"]) | set(maps["splits"]))
    insert_sql = """
        INSERT INTO player_final_profiles (
            player_name, role_profile, play_type, batting_style_hint, bowling_style_hint,
            base_stats_score, context_score, instinct_score, final_score, recent_form_score,
            consistency_score, selection_trust_score, involvement_score, pressure_score,
            momentum_score, attack_intent_score, venue_score, opponent_score, format_score,
            spin_matchup_score, pace_matchup_score, weakness_summary, tags_json
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """
    batch = []
    total = len(players)
    for idx, player_name in enumerate(players, 1):
        try:
            batch.append(compute_player_profile(player_name, maps))
        except Exception as exc:
            print(f"FAILED player={player_name} idx={idx} error={exc}", flush=True)
            raise
        if len(batch) >= 50:
            write_connection.executemany(insert_sql, batch)
            write_connection.commit()
            print(f"Inserted {idx}/{total}")
            batch.clear()
    if batch:
        write_connection.executemany(insert_sql, batch)
        write_connection.commit()
        print(f"Inserted {total}/{total}")


def main() -> None:
    if not SOURCE_DB_PATH.exists():
        raise FileNotFoundError(f"Missing database: {SOURCE_DB_PATH}")
    print("reset/start", flush=True)
    read_connection = sqlite3.connect(f"file:{SOURCE_DB_PATH}?mode=ro", uri=True)
    write_connection = sqlite3.connect(OUTPUT_DB_PATH)
    reset_output_tables(write_connection)
    print("style_splits/start", flush=True)
    derive_style_splits(read_connection, write_connection)
    print("style_splits/done", flush=True)
    print("profiles/start", flush=True)
    derive_player_profiles(read_connection, write_connection)
    print("profiles/done", flush=True)
    split_count = write_connection.execute("SELECT COUNT(*) FROM player_style_splits").fetchone()[0]
    profile_count = write_connection.execute("SELECT COUNT(*) FROM player_final_profiles").fetchone()[0]
    read_connection.close()
    write_connection.close()
    print(f"Done. player_style_splits={split_count}, player_final_profiles={profile_count}")


if __name__ == "__main__":
    main()
