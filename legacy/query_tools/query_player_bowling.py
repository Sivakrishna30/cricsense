import argparse
import sqlite3
from pathlib import Path


DB_PATH = Path("cricsense.db")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Full player bowling history from the indexed CricSense SQLite store.")
    parser.add_argument("--player", required=True, help="Player name, for example: RA Jadeja")
    parser.add_argument("--limit", type=int, default=25, help="Rows to print. Default: 25")
    return parser.parse_args()


def overs_from_balls(legal_balls: int) -> str:
    return f"{legal_balls // 6}.{legal_balls % 6}"


def main() -> None:
    args = parse_args()
    if not DB_PATH.exists():
        raise FileNotFoundError(f"Missing database: {DB_PATH}. Run index_cricsheet_players.py first.")

    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row

    rows = connection.execute(
        """
        SELECT match_date, season, match_type, team_name, opponent_name, venue,
               legal_balls_bowled, maidens, runs_conceded, wickets, wides, no_balls,
               economy, did_bowl
        FROM player_match_bowling
        WHERE player_name = ?
        ORDER BY match_date DESC
        LIMIT ?
        """,
        (args.player, args.limit),
    ).fetchall()

    total = connection.execute(
        "SELECT COUNT(*) FROM player_match_bowling WHERE player_name = ?",
        (args.player,),
    ).fetchone()[0]

    print(f"\nPlayer: {args.player}")
    print(f"Total indexed matches: {total}")
    print(f"Showing latest {len(rows)} rows\n")

    for row in rows:
        figures = f"{row['wickets']}/{row['runs_conceded']}"
        overs = overs_from_balls(row["legal_balls_bowled"])
        print(
            f"{row['match_date']} | {row['match_type']} | {row['team_name']} vs {row['opponent_name']} | "
            f"{overs} overs | {figures} | maidens {row['maidens']} | econ {row['economy']} | "
            f"wides {row['wides']} | no-balls {row['no_balls']} | {row['venue']}"
        )

    connection.close()


if __name__ == "__main__":
    main()
