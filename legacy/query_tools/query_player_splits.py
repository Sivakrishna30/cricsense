import argparse
import sqlite3
from pathlib import Path


DB_PATH = Path("cricsense.db")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Player aggregate splits from the indexed CricSense SQLite store.")
    parser.add_argument("--player", required=True, help="Player name, for example: RA Jadeja")
    parser.add_argument(
        "--mode",
        choices=["all", "completed"],
        default="all",
        help="Use all indexed matches or only completed matches. Default: all",
    )
    parser.add_argument(
        "--top",
        type=int,
        default=10,
        help="Rows to show for venue/opponent splits. Default: 10",
    )
    return parser.parse_args()


def overs_from_balls(legal_balls: int) -> str:
    return f"{legal_balls // 6}.{legal_balls % 6}"


def where_clause(mode: str) -> str:
    if mode == "completed":
        return "WHERE player_name = ? AND match_completed = 1"
    return "WHERE player_name = ?"


def print_batting_split(
    connection: sqlite3.Connection,
    player_name: str,
    mode: str,
    group_by: str,
    label: str,
    limit: int | None = None,
) -> None:
    limit_sql = f"LIMIT {limit}" if limit else ""
    rows = connection.execute(
        f"""
        SELECT
            {group_by} AS split_value,
            COUNT(*) AS matches,
            SUM(did_bat) AS innings,
            SUM(CASE WHEN dismissal = 'not out' THEN 1 ELSE 0 END) AS not_outs,
            SUM(CASE WHEN dismissal != 'not out' AND dismissal != 'did not bat' THEN 1 ELSE 0 END) AS outs,
            SUM(runs) AS runs,
            SUM(balls) AS balls,
            SUM(fours) AS fours,
            SUM(sixes) AS sixes
        FROM player_match_batting
        {where_clause(mode)}
        GROUP BY {group_by}
        HAVING SUM(did_bat) > 0 OR SUM(runs) > 0 OR SUM(balls) > 0
        ORDER BY runs DESC, matches DESC, split_value
        {limit_sql}
        """,
        (player_name,),
    ).fetchall()

    print(f"Batting Split: {label}")
    if not rows:
        print("No batting rows\n")
        return

    for row in rows:
        runs = row["runs"] or 0
        balls = row["balls"] or 0
        outs = row["outs"] or 0
        avg = round(runs / outs, 2) if outs else None
        sr = round((runs * 100) / balls, 2) if balls else 0.0
        print(
            f"{row['split_value']} | M {row['matches']} | Inn {row['innings']} | "
            f"Runs {runs} | Avg {avg if avg is not None else 'NA'} | SR {sr} | "
            f"4s {row['fours'] or 0} | 6s {row['sixes'] or 0}"
        )
    print()


def print_bowling_split(
    connection: sqlite3.Connection,
    player_name: str,
    mode: str,
    group_by: str,
    label: str,
    limit: int | None = None,
) -> None:
    limit_sql = f"LIMIT {limit}" if limit else ""
    rows = connection.execute(
        f"""
        SELECT
            {group_by} AS split_value,
            COUNT(*) AS matches,
            SUM(did_bowl) AS innings_bowled,
            SUM(legal_balls_bowled) AS legal_balls,
            SUM(maidens) AS maidens,
            SUM(runs_conceded) AS runs_conceded,
            SUM(wickets) AS wickets,
            SUM(wides) AS wides,
            SUM(no_balls) AS no_balls
        FROM player_match_bowling
        {where_clause(mode)}
        GROUP BY {group_by}
        HAVING SUM(did_bowl) > 0 OR SUM(legal_balls_bowled) > 0 OR SUM(wickets) > 0
        ORDER BY wickets DESC, runs_conceded ASC, matches DESC, split_value
        {limit_sql}
        """,
        (player_name,),
    ).fetchall()

    print(f"Bowling Split: {label}")
    if not rows:
        print("No bowling rows\n")
        return

    for row in rows:
        wickets = row["wickets"] or 0
        runs_conceded = row["runs_conceded"] or 0
        legal_balls = row["legal_balls"] or 0
        avg = round(runs_conceded / wickets, 2) if wickets else None
        econ = round((runs_conceded * 6) / legal_balls, 2) if legal_balls else 0.0
        strike_rate = round(legal_balls / wickets, 2) if wickets else None
        print(
            f"{row['split_value']} | M {row['matches']} | Bowl Inn {row['innings_bowled']} | "
            f"Overs {overs_from_balls(legal_balls)} | Wkts {wickets} | Avg {avg if avg is not None else 'NA'} | "
            f"Econ {econ} | SR {strike_rate if strike_rate is not None else 'NA'}"
        )
    print()


def main() -> None:
    args = parse_args()
    if not DB_PATH.exists():
        raise FileNotFoundError(f"Missing database: {DB_PATH}. Run index_cricsheet_players.py first.")

    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row

    print(f"\nPlayer Splits: {args.player}")
    print(f"Mode: {args.mode}\n")

    print_batting_split(connection, args.player, args.mode, "season", "Season")
    print_batting_split(connection, args.player, args.mode, "opponent_name", "Opponent", args.top)
    print_batting_split(connection, args.player, args.mode, "venue", "Venue", args.top)

    print_bowling_split(connection, args.player, args.mode, "season", "Season")
    print_bowling_split(connection, args.player, args.mode, "opponent_name", "Opponent", args.top)
    print_bowling_split(connection, args.player, args.mode, "venue", "Venue", args.top)

    connection.close()


if __name__ == "__main__":
    main()
