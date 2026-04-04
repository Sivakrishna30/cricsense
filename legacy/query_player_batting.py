import argparse
import sqlite3
from datetime import date
from pathlib import Path


DB_PATH = Path("cricsense.db")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Fast player lookup from the indexed CricSense SQLite store.")
    parser.add_argument("--player", required=True, help="Player name, for example: MS Dhoni")
    parser.add_argument("--years", type=int, default=5, help="Lookback window in years. Default: 5")
    return parser.parse_args()


def print_report(player_name: str, years: int) -> None:
    if not DB_PATH.exists():
        raise FileNotFoundError(f"Missing database: {DB_PATH}. Run index_cricsheet_players.py first.")

    start_year = date.today().year - years
    start_date = f"{start_year:04d}-{date.today().month:02d}-{date.today().day:02d}"

    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row

    rows = connection.execute(
        """
        SELECT match_date, match_type, team_name, opponent_name, runs, balls,
               strike_rate, dismissal, venue, did_bat
        FROM player_match_batting
        WHERE player_name = ?
          AND match_date >= ?
        ORDER BY match_date
        """,
        (player_name, start_date),
    ).fetchall()

    print(f"\nPlayer: {player_name}")
    print(f"Window: last {years} year(s)")
    print(f"Matches found: {len(rows)}\n")

    if not rows:
        connection.close()
        return

    total_runs = sum(row["runs"] for row in rows)
    total_balls = sum(row["balls"] for row in rows)
    innings = sum(1 for row in rows if row["did_bat"])
    strike_rate = round((total_runs / total_balls) * 100, 2) if total_balls else 0.0

    print("Summary")
    print(f"Runs: {total_runs}")
    print(f"Innings: {innings}")
    print(f"Balls: {total_balls}")
    print(f"Strike Rate: {strike_rate}\n")

    print("Match Details")
    for row in rows:
        teams = f"{row['team_name']} vs {row['opponent_name']}"
        print(
            f"{row['match_date']} | {row['match_type']} | {teams} | "
            f"{row['runs']} ({row['balls']}) | SR {row['strike_rate']} | "
            f"{row['dismissal']} | {row['venue']}"
        )

    connection.close()


if __name__ == "__main__":
    args = parse_args()
    print_report(args.player, args.years)
