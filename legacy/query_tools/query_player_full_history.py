import argparse
import sqlite3
from pathlib import Path


DB_PATH = Path("cricsense.db")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Full player batting history from the indexed CricSense SQLite store.")
    parser.add_argument("--player", required=True, help="Player name, for example: MS Dhoni")
    parser.add_argument("--limit", type=int, default=25, help="Rows to print. Default: 25")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if not DB_PATH.exists():
        raise FileNotFoundError(f"Missing database: {DB_PATH}. Run index_cricsheet_players.py first.")

    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row

    rows = connection.execute(
        """
        SELECT match_date, season, match_type, team_name, opponent_name, venue,
               runs, balls, fours, sixes, strike_rate, dismissal, did_bat
        FROM player_match_batting
        WHERE player_name = ?
        ORDER BY match_date DESC
        LIMIT ?
        """,
        (args.player, args.limit),
    ).fetchall()

    total = connection.execute(
        "SELECT COUNT(*) FROM player_match_batting WHERE player_name = ?",
        (args.player,),
    ).fetchone()[0]

    print(f"\nPlayer: {args.player}")
    print(f"Total indexed matches: {total}")
    print(f"Showing latest {len(rows)} rows\n")

    for row in rows:
        print(
            f"{row['match_date']} | {row['match_type']} | {row['team_name']} vs {row['opponent_name']} | "
            f"{row['runs']} ({row['balls']}) | 4s {row['fours']} | 6s {row['sixes']} | "
            f"SR {row['strike_rate']} | {row['dismissal']} | {row['venue']}"
        )

    connection.close()


if __name__ == "__main__":
    main()
