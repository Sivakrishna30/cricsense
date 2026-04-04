import csv
import io
import json
import re
import sqlite3
import zipfile
from pathlib import Path


DB_PATH = Path("cricsense.db")
FULL_COMMENTARY_ZIP = Path("data_sources/commentary_full_ipl_2017_2025.zip")
HIGHLIGHT_COMMENTARY_ZIPS = [
    Path("data_sources/commentary_highlights_ipl_2008_2020_a.zip"),
    Path("data_sources/commentary_highlights_ipl_2008_2020_b.zip"),
]
ENRICHED_BALL_ZIP = Path("data_sources/enriched_ball_by_ball_multiformat.zip")


COMMENTARY_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS commentary_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_name TEXT NOT NULL,
    source_type TEXT NOT NULL,
    match_id TEXT NOT NULL,
    season TEXT,
    event_name TEXT,
    match_date TEXT,
    venue TEXT,
    team_name TEXT,
    opponent_name TEXT,
    innings_number INTEGER,
    over_number REAL,
    ball_number REAL,
    batter_name TEXT,
    bowler_name TEXT,
    commentary_text TEXT NOT NULL,
    score_label TEXT,
    match_status TEXT,
    pressure_score INTEGER NOT NULL DEFAULT 0,
    momentum_shift_score INTEGER NOT NULL DEFAULT 0,
    fielding_impact_score INTEGER NOT NULL DEFAULT 0,
    attack_intent_score INTEGER NOT NULL DEFAULT 0,
    turning_point_flag INTEGER NOT NULL DEFAULT 0,
    emotion_tags_json TEXT NOT NULL DEFAULT '[]',
    ball_style_hints_json TEXT NOT NULL DEFAULT '[]'
);
"""

BALL_INTELLIGENCE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS ball_intelligence (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_name TEXT NOT NULL,
    match_id TEXT NOT NULL,
    season TEXT,
    match_date TEXT,
    venue TEXT,
    event_name TEXT,
    innings_number INTEGER,
    ball_code REAL,
    batting_team TEXT,
    bowling_team TEXT,
    batter_name TEXT,
    non_striker_name TEXT,
    bowler_name TEXT,
    ball_length TEXT,
    ball_line TEXT,
    shot_played TEXT,
    shot_direction TEXT,
    runs_off_bat INTEGER,
    extras INTEGER,
    wicket_flag INTEGER NOT NULL DEFAULT 0,
    wicket_type TEXT,
    player_dismissed TEXT,
    match_format TEXT,
    batting_style TEXT,
    bowling_style TEXT,
    batter_role TEXT,
    bowler_role TEXT
);
"""


def reset_tables(connection: sqlite3.Connection) -> None:
    connection.execute("DROP TABLE IF EXISTS commentary_events")
    connection.execute("DROP TABLE IF EXISTS ball_intelligence")
    connection.execute(COMMENTARY_TABLE_SQL)
    connection.execute(BALL_INTELLIGENCE_TABLE_SQL)
    connection.execute(
        "CREATE INDEX IF NOT EXISTS idx_commentary_match ON commentary_events(match_id, innings_number, over_number, ball_number)"
    )
    connection.execute(
        "CREATE INDEX IF NOT EXISTS idx_commentary_player ON commentary_events(batter_name, bowler_name)"
    )
    connection.execute(
        "CREATE INDEX IF NOT EXISTS idx_ball_intelligence_match ON ball_intelligence(match_id, innings_number, ball_code)"
    )
    connection.execute(
        "CREATE INDEX IF NOT EXISTS idx_ball_intelligence_player ON ball_intelligence(batter_name, bowler_name)"
    )
    connection.commit()


def compute_commentary_features(text: str) -> dict:
    lowered = text.lower()
    emotion_tags: list[str] = []
    ball_style_hints: list[str] = []

    pressure_score = 0
    momentum_shift_score = 0
    fielding_impact_score = 0
    attack_intent_score = 0
    turning_point_flag = 0

    pressure_keywords = ["pressure", "nervy", "tight", "squeeze", "must", "crucial"]
    attack_keywords = ["four", "six", "heaves", "slogs", "lofted", "pulls", "driven", "attacks"]
    fielding_keywords = ["stunning catch", "brilliant catch", "direct hit", "misfield", "dropped", "save"]
    turning_keywords = ["turning point", "huge wicket", "massive over", "game-changing", "hat-trick"]
    ball_style_keywords = [
        "yorker",
        "slower ball",
        "off-cutter",
        "leg-cutter",
        "bouncer",
        "short ball",
        "full toss",
        "googly",
        "turn",
        "swing",
    ]

    for keyword in pressure_keywords:
        if keyword in lowered:
            pressure_score += 2
            emotion_tags.append(keyword.replace(" ", "_"))

    for keyword in attack_keywords:
        if keyword in lowered:
            attack_intent_score += 2
            if keyword in {"four", "six"}:
                momentum_shift_score += 1

    for keyword in fielding_keywords:
        if keyword in lowered:
            fielding_impact_score += 3
            emotion_tags.append(keyword.replace(" ", "_"))

    for keyword in turning_keywords:
        if keyword in lowered:
            turning_point_flag = 1
            momentum_shift_score += 3
            emotion_tags.append(keyword.replace(" ", "_"))

    for keyword in ball_style_keywords:
        if keyword in lowered:
            ball_style_hints.append(keyword.replace(" ", "_"))

    if "out" in lowered or "bowled" in lowered or "caught" in lowered or "lbw" in lowered:
        momentum_shift_score += 2
        pressure_score += 1

    if "four" in lowered or "six" in lowered:
        emotion_tags.append("boundary")
    if "dropped" in lowered:
        emotion_tags.append("missed_chance")
    if "slower" in lowered:
        emotion_tags.append("variation")

    return {
        "pressure_score": pressure_score,
        "momentum_shift_score": momentum_shift_score,
        "fielding_impact_score": fielding_impact_score,
        "attack_intent_score": attack_intent_score,
        "turning_point_flag": turning_point_flag,
        "emotion_tags_json": json.dumps(sorted(set(emotion_tags))),
        "ball_style_hints_json": json.dumps(sorted(set(ball_style_hints))),
    }


def parse_batter_bowler_pair(value: str) -> tuple[str, str]:
    if " to " in value:
        bowler, batter = value.split(" to ", 1)
        return batter.strip(), bowler.strip()
    return "", ""


def ingest_full_commentary(connection: sqlite3.Connection) -> int:
    if not FULL_COMMENTARY_ZIP.exists():
        return 0

    inserted = 0
    with zipfile.ZipFile(FULL_COMMENTARY_ZIP) as z:
        data = z.read("ipl_commentary_data.csv").decode("utf-8", errors="replace")
        reader = csv.DictReader(io.StringIO(data))
        rows = []
        for row in reader:
            commentary = row["ball_commentary"].strip()
            if not commentary:
                continue
            features = compute_commentary_features(commentary)
            rows.append(
                {
                    "source_name": FULL_COMMENTARY_ZIP.name,
                    "source_type": "full",
                    "match_id": row["match_id"],
                    "season": row["year"],
                    "event_name": row["series_name"],
                    "match_date": row["match_datetime"],
                    "venue": row["match_venue"],
                    "team_name": row["team1_name"],
                    "opponent_name": row["team2_name"],
                    "innings_number": None,
                    "over_number": float(row["over_no"]) if row["over_no"] else None,
                    "ball_number": float(row["ball_no"]) if row["ball_no"] else None,
                    "batter_name": "",
                    "bowler_name": "",
                    "commentary_text": commentary,
                    "score_label": "",
                    "match_status": row["match_status"],
                    **features,
                }
            )
            if len(rows) >= 5000:
                insert_commentary_rows(connection, rows)
                inserted += len(rows)
                rows = []
        if rows:
            insert_commentary_rows(connection, rows)
            inserted += len(rows)
    return inserted


def ingest_highlight_commentary(connection: sqlite3.Connection) -> int:
    inserted = 0
    for zip_path in HIGHLIGHT_COMMENTARY_ZIPS:
        if not zip_path.exists():
            continue
        with zipfile.ZipFile(zip_path) as z:
            data = z.read("IPL_Match_Highlights_Commentary.csv").decode("utf-8", errors="replace")
            reader = csv.DictReader(io.StringIO(data))
            rows = []
            for row in reader:
                commentary = row["Commentary"].strip()
                batter_name, bowler_name = parse_batter_bowler_pair(row["batsman"])
                over_ball = row["Over_num"]
                over_number = float(over_ball) if over_ball else None
                features = compute_commentary_features(commentary)
                rows.append(
                    {
                        "source_name": zip_path.name,
                        "source_type": "highlight",
                        "match_id": row["Match_id"],
                        "season": "",
                        "event_name": "Indian Premier League",
                        "match_date": "",
                        "venue": "",
                        "team_name": row["Team"],
                        "opponent_name": "",
                        "innings_number": None,
                        "over_number": over_number,
                        "ball_number": over_number,
                        "batter_name": batter_name,
                        "bowler_name": bowler_name,
                        "commentary_text": commentary,
                        "score_label": row["score"],
                        "match_status": "",
                        **features,
                    }
                )
                if len(rows) >= 5000:
                    insert_commentary_rows(connection, rows)
                    inserted += len(rows)
                    rows = []
            if rows:
                insert_commentary_rows(connection, rows)
                inserted += len(rows)
    return inserted


def insert_commentary_rows(connection: sqlite3.Connection, rows: list[dict]) -> None:
    connection.executemany(
        """
        INSERT INTO commentary_events (
            source_name, source_type, match_id, season, event_name, match_date, venue,
            team_name, opponent_name, innings_number, over_number, ball_number,
            batter_name, bowler_name, commentary_text, score_label, match_status,
            pressure_score, momentum_shift_score, fielding_impact_score,
            attack_intent_score, turning_point_flag, emotion_tags_json, ball_style_hints_json
        ) VALUES (
            :source_name, :source_type, :match_id, :season, :event_name, :match_date, :venue,
            :team_name, :opponent_name, :innings_number, :over_number, :ball_number,
            :batter_name, :bowler_name, :commentary_text, :score_label, :match_status,
            :pressure_score, :momentum_shift_score, :fielding_impact_score,
            :attack_intent_score, :turning_point_flag, :emotion_tags_json, :ball_style_hints_json
        )
        """,
        rows,
    )
    connection.commit()


def safe_int(value: str) -> int:
    try:
        return int(float(value)) if value not in {"", None} else 0
    except ValueError:
        return 0


def safe_float(value: str) -> float | None:
    try:
        return float(value) if value not in {"", None} else None
    except ValueError:
        return None


def ingest_ball_intelligence(connection: sqlite3.Connection) -> int:
    if not ENRICHED_BALL_ZIP.exists():
        return 0

    inserted = 0
    with zipfile.ZipFile(ENRICHED_BALL_ZIP) as z:
        with z.open("ball_by_ball_data.csv") as f:
            wrapper = io.TextIOWrapper(f, encoding="utf-8", errors="replace")
            reader = csv.DictReader(wrapper)
            rows = []
            for row in reader:
                rows.append(
                    {
                        "source_name": ENRICHED_BALL_ZIP.name,
                        "match_id": row["match_id"],
                        "season": row["season"],
                        "match_date": row["start_date"],
                        "venue": row["venue"],
                        "event_name": row["event"],
                        "innings_number": safe_int(row["innings"]),
                        "ball_code": safe_float(row["ball"]),
                        "batting_team": row["batting_team"],
                        "bowling_team": row["bowling_team"],
                        "batter_name": row["striker"],
                        "non_striker_name": row["non_striker"],
                        "bowler_name": row["bowler"],
                        "ball_length": row["ball_length"],
                        "ball_line": row["ball_line"],
                        "shot_played": row["shot_played"],
                        "shot_direction": row["shot_direction"],
                        "runs_off_bat": safe_int(row["runs_off_bat"]),
                        "extras": safe_int(row["extras"]),
                        "wicket_flag": safe_int(row["wicket"]),
                        "wicket_type": row["wicket_type"],
                        "player_dismissed": row["player_dismissed"],
                        "match_format": row["format"],
                        "batting_style": row["batting style_striker"],
                        "bowling_style": row["bowling style_bowler"],
                        "batter_role": row["playing role_striker"],
                        "bowler_role": row["playing role_bowler"],
                    }
                )
                if len(rows) >= 10000:
                    insert_ball_rows(connection, rows)
                    inserted += len(rows)
                    rows = []
            if rows:
                insert_ball_rows(connection, rows)
                inserted += len(rows)
    return inserted


def insert_ball_rows(connection: sqlite3.Connection, rows: list[dict]) -> None:
    connection.executemany(
        """
        INSERT INTO ball_intelligence (
            source_name, match_id, season, match_date, venue, event_name, innings_number,
            ball_code, batting_team, bowling_team, batter_name, non_striker_name, bowler_name,
            ball_length, ball_line, shot_played, shot_direction, runs_off_bat, extras,
            wicket_flag, wicket_type, player_dismissed, match_format, batting_style,
            bowling_style, batter_role, bowler_role
        ) VALUES (
            :source_name, :match_id, :season, :match_date, :venue, :event_name, :innings_number,
            :ball_code, :batting_team, :bowling_team, :batter_name, :non_striker_name, :bowler_name,
            :ball_length, :ball_line, :shot_played, :shot_direction, :runs_off_bat, :extras,
            :wicket_flag, :wicket_type, :player_dismissed, :match_format, :batting_style,
            :bowling_style, :batter_role, :bowler_role
        )
        """,
        rows,
    )
    connection.commit()


def main() -> None:
    if not DB_PATH.exists():
        raise FileNotFoundError(f"Missing database: {DB_PATH}")

    connection = sqlite3.connect(DB_PATH)
    reset_tables(connection)

    full_count = ingest_full_commentary(connection)
    highlight_count = ingest_highlight_commentary(connection)
    ball_count = ingest_ball_intelligence(connection)

    print(
        f"Done. commentary_events rows: {full_count + highlight_count} "
        f"(full={full_count}, highlight={highlight_count}); "
        f"ball_intelligence rows: {ball_count}"
    )
    connection.close()


if __name__ == "__main__":
    main()
