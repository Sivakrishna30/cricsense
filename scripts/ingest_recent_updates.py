import json
import sqlite3
import sys
import zipfile
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

from index_cricsheet_players import (
    CREATE_BALL_TABLE_SQL,
    CREATE_BOWLING_TABLE_SQL,
    CREATE_TABLE_SQL,
    build_ball_rows,
    build_bowling_rows,
    build_match_rows,
    insert_ball_rows,
    insert_bowling_rows,
    insert_rows,
)


ZIP_PATH = Path("recently_added_30_json.zip")
DB_PATH = Path("cricsense.db")


def ensure_tables(connection: sqlite3.Connection) -> None:
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


def ingest_recent_updates() -> None:
    if not ZIP_PATH.exists():
        raise FileNotFoundError(f"Missing ZIP file: {ZIP_PATH}")

    connection = sqlite3.connect(DB_PATH)
    ensure_tables(connection)

    total_matches = 0
    total_rows = 0
    total_bowling_rows = 0
    total_ball_rows = 0

    with zipfile.ZipFile(ZIP_PATH) as zip_file:
        for member_name in zip_file.namelist():
            if not member_name.endswith(".json"):
                continue

            match_data = json.loads(zip_file.read(member_name))
            match_id = Path(member_name).stem
            batting_rows = build_match_rows(match_data, match_id)
            bowling_rows = build_bowling_rows(match_data, match_id)
            ball_rows = build_ball_rows(match_data, match_id)

            insert_rows(connection, batting_rows)
            insert_bowling_rows(connection, bowling_rows)
            insert_ball_rows(connection, ball_rows)

            total_matches += 1
            total_rows += len(batting_rows)
            total_bowling_rows += len(bowling_rows)
            total_ball_rows += len(ball_rows)

            if total_matches % 25 == 0:
                connection.commit()
                print(f"Ingested {total_matches} recent matches...")

    connection.commit()
    connection.close()
    print(
        f"Done. Ingested {total_matches} recent matches, {total_rows} batting rows, "
        f"{total_bowling_rows} bowling rows, and {total_ball_rows} ball rows into {DB_PATH}."
    )


if __name__ == "__main__":
    ingest_recent_updates()
