import argparse
import sqlite3
from pathlib import Path


DB_PATH = Path("cricsense.db")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Ball-by-ball lookup for a player from the indexed CricSense SQLite store.")
    parser.add_argument("--player", required=True, help="Player name, for example: MS Dhoni")
    parser.add_argument("--match-id", help="Optional match id filter")
    parser.add_argument("--limit", type=int, default=30, help="Rows to print. Default: 30")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if not DB_PATH.exists():
        raise FileNotFoundError(f"Missing database: {DB_PATH}. Run index_cricsheet_players.py first.")

    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row

    if args.match_id:
        rows = connection.execute(
            """
            SELECT match_id, match_date, innings_number, over_number, ball_in_over,
                   batting_team, bowling_team, bowler_name, batter_runs, extras_runs,
                   total_runs, is_legal_ball, wicket_flag, wicket_kind, player_out
            FROM player_ball_by_ball
            WHERE batter_name = ?
              AND match_id = ?
            ORDER BY innings_number, over_number, ball_in_over
            LIMIT ?
            """,
            (args.player, args.match_id, args.limit),
        ).fetchall()
    else:
        rows = connection.execute(
            """
            SELECT match_id, match_date, innings_number, over_number, ball_in_over,
                   batting_team, bowling_team, bowler_name, batter_runs, extras_runs,
                   total_runs, is_legal_ball, wicket_flag, wicket_kind, player_out
            FROM player_ball_by_ball
            WHERE batter_name = ?
            ORDER BY match_date DESC, innings_number DESC, over_number DESC, ball_in_over DESC
            LIMIT ?
            """,
            (args.player, args.limit),
        ).fetchall()

    print(f"\nPlayer: {args.player}")
    print(f"Ball rows returned: {len(rows)}\n")

    for row in rows:
        wicket_text = f" | wicket {row['wicket_kind']} {row['player_out']}" if row["wicket_flag"] else ""
        legal_ball = "legal" if row["is_legal_ball"] else "extra"
        print(
            f"{row['match_date']} | match {row['match_id']} | inns {row['innings_number']} | "
            f"{row['over_number']}.{row['ball_in_over']} | vs {row['bowler_name']} | "
            f"bat {row['batter_runs']} | extras {row['extras_runs']} | total {row['total_runs']} | "
            f"{legal_ball}{wicket_text}"
        )

    connection.close()


if __name__ == "__main__":
    main()
