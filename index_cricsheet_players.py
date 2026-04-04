import json
import sqlite3
import zipfile
from pathlib import Path


ZIP_PATH = Path("cricsheet_all_json.zip")
DB_PATH = Path("cricsense.db")


CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS player_match_batting (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    player_name TEXT NOT NULL,
    team_name TEXT,
    opponent_name TEXT,
    match_id TEXT NOT NULL,
    match_date TEXT,
    season TEXT,
    match_type TEXT,
    venue TEXT,
    city TEXT,
    event_name TEXT,
    result_text TEXT,
    winner TEXT,
    win_by_type TEXT,
    win_by_value INTEGER,
    innings_count INTEGER NOT NULL DEFAULT 0,
    match_completed INTEGER NOT NULL DEFAULT 1,
    runs INTEGER NOT NULL DEFAULT 0,
    balls INTEGER NOT NULL DEFAULT 0,
    fours INTEGER NOT NULL DEFAULT 0,
    sixes INTEGER NOT NULL DEFAULT 0,
    dismissal TEXT NOT NULL DEFAULT 'did not bat',
    did_bat INTEGER NOT NULL DEFAULT 0,
    strike_rate REAL NOT NULL DEFAULT 0,
    UNIQUE(player_name, match_id)
);
"""

CREATE_BOWLING_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS player_match_bowling (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    player_name TEXT NOT NULL,
    team_name TEXT,
    opponent_name TEXT,
    match_id TEXT NOT NULL,
    match_date TEXT,
    season TEXT,
    match_type TEXT,
    venue TEXT,
    city TEXT,
    event_name TEXT,
    result_text TEXT,
    winner TEXT,
    win_by_type TEXT,
    win_by_value INTEGER,
    innings_count INTEGER NOT NULL DEFAULT 0,
    match_completed INTEGER NOT NULL DEFAULT 1,
    balls_bowled INTEGER NOT NULL DEFAULT 0,
    legal_balls_bowled INTEGER NOT NULL DEFAULT 0,
    maidens INTEGER NOT NULL DEFAULT 0,
    runs_conceded INTEGER NOT NULL DEFAULT 0,
    wickets INTEGER NOT NULL DEFAULT 0,
    wides INTEGER NOT NULL DEFAULT 0,
    no_balls INTEGER NOT NULL DEFAULT 0,
    economy REAL NOT NULL DEFAULT 0,
    did_bowl INTEGER NOT NULL DEFAULT 0,
    UNIQUE(player_name, match_id)
);
"""

CREATE_BALL_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS player_ball_by_ball (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    match_id TEXT NOT NULL,
    innings_number INTEGER NOT NULL,
    over_number INTEGER NOT NULL,
    ball_in_over INTEGER NOT NULL,
    match_date TEXT,
    season TEXT,
    match_type TEXT,
    venue TEXT,
    city TEXT,
    event_name TEXT,
    batting_team TEXT,
    bowling_team TEXT,
    batter_name TEXT NOT NULL,
    bowler_name TEXT,
    non_striker_name TEXT,
    batter_runs INTEGER NOT NULL DEFAULT 0,
    extras_runs INTEGER NOT NULL DEFAULT 0,
    total_runs INTEGER NOT NULL DEFAULT 0,
    is_legal_ball INTEGER NOT NULL DEFAULT 1,
    extras_detail TEXT,
    wicket_flag INTEGER NOT NULL DEFAULT 0,
    wicket_kind TEXT,
    player_out TEXT,
    fielders_json TEXT,
    UNIQUE(match_id, innings_number, over_number, ball_in_over, batter_name, bowler_name, non_striker_name)
);
"""


def reset_table(connection: sqlite3.Connection) -> None:
    connection.execute("DROP TABLE IF EXISTS player_match_batting")
    connection.execute("DROP TABLE IF EXISTS player_match_bowling")
    connection.execute("DROP TABLE IF EXISTS player_ball_by_ball")
    connection.execute(CREATE_TABLE_SQL)
    connection.execute(CREATE_BOWLING_TABLE_SQL)
    connection.execute(CREATE_BALL_TABLE_SQL)
    connection.execute(
        "CREATE INDEX IF NOT EXISTS idx_player_date ON player_match_batting(player_name, match_date)"
    )
    connection.execute(
        "CREATE INDEX IF NOT EXISTS idx_bowler_date ON player_match_bowling(player_name, match_date)"
    )
    connection.execute(
        "CREATE INDEX IF NOT EXISTS idx_ball_player_date ON player_ball_by_ball(batter_name, match_date)"
    )
    connection.execute(
        "CREATE INDEX IF NOT EXISTS idx_ball_bowler_date ON player_ball_by_ball(bowler_name, match_date)"
    )
    connection.execute(
        "CREATE INDEX IF NOT EXISTS idx_ball_match_player ON player_ball_by_ball(match_id, batter_name)"
    )
    connection.commit()


def delivery_counts_as_ball(delivery: dict) -> bool:
    extras = delivery.get("extras", {})
    return "wides" not in extras


def build_match_rows(match_data: dict, match_id: str) -> list[dict]:
    info = match_data.get("info", {})
    teams = info.get("teams", [])
    players_by_team = info.get("players", {})
    match_date = (info.get("dates") or [""])[0]
    event = info.get("event", {})
    outcome = info.get("outcome", {})
    result_text = outcome.get("result", "")
    winner = outcome.get("winner", "")
    win_by = outcome.get("by", {})
    win_by_type = next(iter(win_by.keys()), "") if win_by else ""
    win_by_value = int(next(iter(win_by.values()))) if win_by else 0
    innings_count = len(match_data.get("innings", []))
    match_completed = 0 if result_text in {"no result"} else 1

    player_rows: dict[str, dict] = {}

    for team_name, squad in players_by_team.items():
        opponent_name = next((team for team in teams if team != team_name), "")
        for player_name in squad:
            player_rows[player_name] = {
                "player_name": player_name,
                "team_name": team_name,
                "opponent_name": opponent_name,
                "match_id": match_id,
                "match_date": match_date,
                "season": info.get("season", ""),
                "match_type": info.get("match_type", ""),
                "venue": info.get("venue", ""),
                "city": info.get("city", ""),
                "event_name": event.get("name", ""),
                "result_text": result_text,
                "winner": winner,
                "win_by_type": win_by_type,
                "win_by_value": win_by_value,
                "innings_count": innings_count,
                "match_completed": match_completed,
                "runs": 0,
                "balls": 0,
                "fours": 0,
                "sixes": 0,
                "dismissal": "did not bat",
                "did_bat": 0,
                "strike_rate": 0.0,
            }

    for innings in match_data.get("innings", []):
        for over in innings.get("overs", []):
            for delivery in over.get("deliveries", []):
                batter = delivery.get("batter")
                if batter and batter in player_rows:
                    row = player_rows[batter]
                    batter_runs = delivery.get("runs", {}).get("batter", 0)
                    row["runs"] += batter_runs
                    row["did_bat"] = 1
                    if delivery_counts_as_ball(delivery):
                        row["balls"] += 1
                    if batter_runs == 4:
                        row["fours"] += 1
                    elif batter_runs == 6:
                        row["sixes"] += 1

                for wicket in delivery.get("wickets", []):
                    player_out = wicket.get("player_out")
                    if player_out and player_out in player_rows:
                        player_rows[player_out]["dismissal"] = wicket.get("kind", "out")

    for row in player_rows.values():
        if row["did_bat"] and row["dismissal"] == "did not bat":
            row["dismissal"] = "not out"
        if row["balls"] > 0:
            row["strike_rate"] = round((row["runs"] / row["balls"]) * 100, 2)

    return list(player_rows.values())


def build_bowling_rows(match_data: dict, match_id: str) -> list[dict]:
    info = match_data.get("info", {})
    teams = info.get("teams", [])
    players_by_team = info.get("players", {})
    match_date = (info.get("dates") or [""])[0]
    event = info.get("event", {})
    outcome = info.get("outcome", {})
    result_text = outcome.get("result", "")
    winner = outcome.get("winner", "")
    win_by = outcome.get("by", {})
    win_by_type = next(iter(win_by.keys()), "") if win_by else ""
    win_by_value = int(next(iter(win_by.values()))) if win_by else 0
    innings_count = len(match_data.get("innings", []))
    match_completed = 0 if result_text in {"no result"} else 1

    bowler_rows: dict[str, dict] = {}

    for team_name, squad in players_by_team.items():
        opponent_name = next((team for team in teams if team != team_name), "")
        for player_name in squad:
            bowler_rows[player_name] = {
                "player_name": player_name,
                "team_name": team_name,
                "opponent_name": opponent_name,
                "match_id": match_id,
                "match_date": match_date,
                "season": info.get("season", ""),
                "match_type": info.get("match_type", ""),
                "venue": info.get("venue", ""),
                "city": info.get("city", ""),
                "event_name": event.get("name", ""),
                "result_text": result_text,
                "winner": winner,
                "win_by_type": win_by_type,
                "win_by_value": win_by_value,
                "innings_count": innings_count,
                "match_completed": match_completed,
                "balls_bowled": 0,
                "legal_balls_bowled": 0,
                "maidens": 0,
                "runs_conceded": 0,
                "wickets": 0,
                "wides": 0,
                "no_balls": 0,
                "economy": 0.0,
                "did_bowl": 0,
            }

    for innings in match_data.get("innings", []):
        over_totals: dict[tuple[str, int], int] = {}
        legal_ball_counts: dict[tuple[str, int], int] = {}

        for over in innings.get("overs", []):
            over_number = over.get("over", 0)
            for delivery in over.get("deliveries", []):
                bowler = delivery.get("bowler")
                if not bowler or bowler not in bowler_rows:
                    continue

                row = bowler_rows[bowler]
                row["did_bowl"] = 1
                row["balls_bowled"] += 1

                if delivery_counts_as_ball(delivery):
                    row["legal_balls_bowled"] += 1
                    legal_ball_counts[(bowler, over_number)] = legal_ball_counts.get((bowler, over_number), 0) + 1

                total_runs = delivery.get("runs", {}).get("total", 0)
                row["runs_conceded"] += total_runs
                over_totals[(bowler, over_number)] = over_totals.get((bowler, over_number), 0) + total_runs

                extras = delivery.get("extras", {})
                row["wides"] += extras.get("wides", 0)
                row["no_balls"] += extras.get("noballs", 0)

                for wicket in delivery.get("wickets", []):
                    kind = wicket.get("kind", "")
                    if kind and kind not in {"run out", "retired hurt", "retired out", "obstructing the field"}:
                        row["wickets"] += 1

        for key, over_runs in over_totals.items():
            if over_runs == 0 and legal_ball_counts.get(key, 0) >= 6:
                bowler_rows[key[0]]["maidens"] += 1

    for row in bowler_rows.values():
        if row["legal_balls_bowled"] > 0:
            row["economy"] = round((row["runs_conceded"] * 6) / row["legal_balls_bowled"], 2)

    return list(bowler_rows.values())


def build_ball_rows(match_data: dict, match_id: str) -> list[dict]:
    info = match_data.get("info", {})
    teams = info.get("teams", [])
    match_date = (info.get("dates") or [""])[0]
    event = info.get("event", {})
    rows: list[dict] = []

    for innings_index, innings in enumerate(match_data.get("innings", []), start=1):
        batting_team = innings.get("team", "")
        bowling_team = next((team for team in teams if team != batting_team), "")

        for over in innings.get("overs", []):
            for ball_index, delivery in enumerate(over.get("deliveries", []), start=1):
                wickets = delivery.get("wickets", [])
                rows.append(
                    {
                        "match_id": match_id,
                        "innings_number": innings_index,
                        "over_number": over.get("over", 0),
                        "ball_in_over": ball_index,
                        "match_date": match_date,
                        "season": info.get("season", ""),
                        "match_type": info.get("match_type", ""),
                        "venue": info.get("venue", ""),
                        "city": info.get("city", ""),
                        "event_name": event.get("name", ""),
                        "batting_team": batting_team,
                        "bowling_team": bowling_team,
                        "batter_name": delivery.get("batter", ""),
                        "bowler_name": delivery.get("bowler", ""),
                        "non_striker_name": delivery.get("non_striker", ""),
                        "batter_runs": delivery.get("runs", {}).get("batter", 0),
                        "extras_runs": delivery.get("runs", {}).get("extras", 0),
                        "total_runs": delivery.get("runs", {}).get("total", 0),
                        "is_legal_ball": 1 if delivery_counts_as_ball(delivery) else 0,
                        "extras_detail": json.dumps(delivery.get("extras", {}), separators=(",", ":")),
                        "wicket_flag": 1 if wickets else 0,
                        "wicket_kind": wickets[0].get("kind", "") if wickets else "",
                        "player_out": wickets[0].get("player_out", "") if wickets else "",
                        "fielders_json": json.dumps(wickets[0].get("fielders", []), separators=(",", ":"))
                        if wickets
                        else "[]",
                    }
                )

    return rows


def insert_rows(connection: sqlite3.Connection, rows: list[dict]) -> None:
    connection.executemany(
        """
        INSERT OR REPLACE INTO player_match_batting (
            player_name, team_name, opponent_name, match_id, match_date, season,
            match_type, venue, city, event_name, result_text, winner, win_by_type,
            win_by_value, innings_count, match_completed, runs, balls, fours, sixes,
            dismissal, did_bat, strike_rate
        ) VALUES (
            :player_name, :team_name, :opponent_name, :match_id, :match_date, :season,
            :match_type, :venue, :city, :event_name, :result_text, :winner, :win_by_type,
            :win_by_value, :innings_count, :match_completed, :runs, :balls, :fours, :sixes,
            :dismissal, :did_bat, :strike_rate
        )
        """,
        rows,
    )


def insert_bowling_rows(connection: sqlite3.Connection, rows: list[dict]) -> None:
    connection.executemany(
        """
        INSERT OR REPLACE INTO player_match_bowling (
            player_name, team_name, opponent_name, match_id, match_date, season,
            match_type, venue, city, event_name, result_text, winner, win_by_type,
            win_by_value, innings_count, match_completed, balls_bowled, legal_balls_bowled,
            maidens, runs_conceded, wickets, wides, no_balls, economy, did_bowl
        ) VALUES (
            :player_name, :team_name, :opponent_name, :match_id, :match_date, :season,
            :match_type, :venue, :city, :event_name, :result_text, :winner, :win_by_type,
            :win_by_value, :innings_count, :match_completed, :balls_bowled, :legal_balls_bowled,
            :maidens, :runs_conceded, :wickets, :wides, :no_balls, :economy, :did_bowl
        )
        """,
        rows,
    )


def insert_ball_rows(connection: sqlite3.Connection, rows: list[dict]) -> None:
    connection.executemany(
        """
        INSERT OR REPLACE INTO player_ball_by_ball (
            match_id, innings_number, over_number, ball_in_over, match_date, season,
            match_type, venue, city, event_name, batting_team, bowling_team, batter_name,
            bowler_name, non_striker_name, batter_runs, extras_runs, total_runs,
            is_legal_ball, extras_detail, wicket_flag, wicket_kind, player_out, fielders_json
        ) VALUES (
            :match_id, :innings_number, :over_number, :ball_in_over, :match_date, :season,
            :match_type, :venue, :city, :event_name, :batting_team, :bowling_team, :batter_name,
            :bowler_name, :non_striker_name, :batter_runs, :extras_runs, :total_runs,
            :is_legal_ball, :extras_detail, :wicket_flag, :wicket_kind, :player_out, :fielders_json
        )
        """,
        rows,
    )


def index_cricsheet() -> None:
    if not ZIP_PATH.exists():
        raise FileNotFoundError(f"Missing ZIP file: {ZIP_PATH}")

    connection = sqlite3.connect(DB_PATH)
    reset_table(connection)

    total_matches = 0
    total_rows = 0
    total_bowling_rows = 0
    total_ball_rows = 0

    with zipfile.ZipFile(ZIP_PATH) as zip_file:
        for member_name in zip_file.namelist():
            if not member_name.endswith(".json"):
                continue

            match_data = json.loads(zip_file.read(member_name))
            match_id = member_name.replace(".json", "")
            rows = build_match_rows(match_data, match_id)
            bowling_rows = build_bowling_rows(match_data, match_id)
            ball_rows = build_ball_rows(match_data, match_id)
            insert_rows(connection, rows)
            insert_bowling_rows(connection, bowling_rows)
            insert_ball_rows(connection, ball_rows)

            total_matches += 1
            total_rows += len(rows)
            total_bowling_rows += len(bowling_rows)
            total_ball_rows += len(ball_rows)

            if total_matches % 1000 == 0:
                connection.commit()
                print(f"Indexed {total_matches} matches...")

    connection.commit()
    connection.close()
    print(
        f"Done. Indexed {total_matches} matches, {total_rows} batting rows, "
        f"{total_bowling_rows} bowling rows, "
        f"and {total_ball_rows} ball rows into {DB_PATH}."
    )


if __name__ == "__main__":
    index_cricsheet()
