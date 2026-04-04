import argparse
import sqlite3
from pathlib import Path


DB_PATH = Path("cricsense.db")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Batter vs bowler head-to-head from CricSense delivery data.")
    parser.add_argument("--batter", required=True, help="Batter name, for example: MS Dhoni")
    parser.add_argument("--bowler", required=True, help="Bowler name, for example: JJ Bumrah")
    parser.add_argument("--limit", type=int, default=20, help="Recent deliveries to print. Default: 20")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if not DB_PATH.exists():
        raise FileNotFoundError(f"Missing database: {DB_PATH}. Run index_cricsheet_players.py first.")

    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row

    summary = connection.execute(
        """
        SELECT
            COUNT(*) AS deliveries,
            SUM(is_legal_ball) AS legal_balls,
            SUM(batter_runs) AS batter_runs,
            SUM(total_runs) AS total_runs,
            SUM(CASE WHEN batter_runs = 4 THEN 1 ELSE 0 END) AS fours,
            SUM(CASE WHEN batter_runs = 6 THEN 1 ELSE 0 END) AS sixes,
            SUM(CASE WHEN wicket_flag = 1 AND player_out = batter_name THEN 1 ELSE 0 END) AS dismissals
        FROM player_ball_by_ball
        WHERE batter_name = ?
          AND bowler_name = ?
        """,
        (args.batter, args.bowler),
    ).fetchone()

    batter_runs = summary["batter_runs"] or 0
    legal_balls = summary["legal_balls"] or 0
    dismissals = summary["dismissals"] or 0
    strike_rate = round((batter_runs * 100) / legal_balls, 2) if legal_balls else 0.0
    average = round(batter_runs / dismissals, 2) if dismissals else None

    print(f"\nHead to Head: {args.batter} vs {args.bowler}\n")
    print("Summary")
    print(f"Deliveries: {summary['deliveries'] or 0}")
    print(f"Legal Balls: {legal_balls}")
    print(f"Batter Runs: {batter_runs}")
    print(f"Total Runs Off Bat+Extras: {summary['total_runs'] or 0}")
    print(f"4s: {summary['fours'] or 0}")
    print(f"6s: {summary['sixes'] or 0}")
    print(f"Dismissals: {dismissals}")
    print(f"Strike Rate: {strike_rate}")
    print(f"Average: {average if average is not None else 'NA'}\n")

    deliveries = connection.execute(
        """
        SELECT match_date, match_id, innings_number, over_number, ball_in_over,
               batter_runs, extras_runs, total_runs, wicket_flag, wicket_kind, player_out
        FROM player_ball_by_ball
        WHERE batter_name = ?
          AND bowler_name = ?
        ORDER BY match_date DESC, innings_number DESC, over_number DESC, ball_in_over DESC
        LIMIT ?
        """,
        (args.batter, args.bowler, args.limit),
    ).fetchall()

    print("Recent Deliveries")
    for row in deliveries:
        wicket_text = f" | wicket {row['wicket_kind']} {row['player_out']}" if row["wicket_flag"] else ""
        print(
            f"{row['match_date']} | match {row['match_id']} | inns {row['innings_number']} | "
            f"{row['over_number']}.{row['ball_in_over']} | bat {row['batter_runs']} | "
            f"extras {row['extras_runs']} | total {row['total_runs']}{wicket_text}"
        )

    connection.close()


if __name__ == "__main__":
    main()
