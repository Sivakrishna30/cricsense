import argparse
import sqlite3
from pathlib import Path


DB_PATH = Path("cricsense.db")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Combined CricSense player profile from the indexed SQLite store.")
    parser.add_argument("--player", required=True, help="Player name, for example: RA Jadeja")
    parser.add_argument("--recent", type=int, default=5, help="Recent batting/bowling rows to show. Default: 5")
    return parser.parse_args()


def overs_from_balls(legal_balls: int) -> str:
    return f"{legal_balls // 6}.{legal_balls % 6}"


def print_batting_section(connection: sqlite3.Connection, player_name: str, recent: int) -> None:
    batting_summary = connection.execute(
        """
        SELECT
            COUNT(*) AS matches,
            SUM(did_bat) AS innings,
            SUM(CASE WHEN dismissal != 'not out' AND dismissal != 'did not bat' THEN 1 ELSE 0 END) AS outs,
            SUM(runs) AS runs,
            SUM(balls) AS balls,
            SUM(fours) AS fours,
            SUM(sixes) AS sixes
        FROM player_match_batting
        WHERE player_name = ?
        """,
        (player_name,),
    ).fetchone()

    runs = batting_summary["runs"] or 0
    balls = batting_summary["balls"] or 0
    outs = batting_summary["outs"] or 0
    average = round(runs / outs, 2) if outs else None
    strike_rate = round((runs / balls) * 100, 2) if balls else 0.0

    print("Batting Summary")
    print(f"Matches: {batting_summary['matches'] or 0}")
    print(f"Innings: {batting_summary['innings'] or 0}")
    print(f"Runs: {runs}")
    print(f"Balls: {balls}")
    print(f"4s: {batting_summary['fours'] or 0}")
    print(f"6s: {batting_summary['sixes'] or 0}")
    print(f"Average: {average if average is not None else 'NA'}")
    print(f"Strike Rate: {strike_rate}\n")

    recent_batting = connection.execute(
        """
        SELECT match_date, match_type, team_name, opponent_name, runs, balls, strike_rate, dismissal, venue
        FROM player_match_batting
        WHERE player_name = ?
        ORDER BY match_date DESC
        LIMIT ?
        """,
        (player_name, recent),
    ).fetchall()

    print("Recent Batting")
    for row in recent_batting:
        print(
            f"{row['match_date']} | {row['match_type']} | {row['team_name']} vs {row['opponent_name']} | "
            f"{row['runs']} ({row['balls']}) | SR {row['strike_rate']} | {row['dismissal']} | {row['venue']}"
        )
    print()


def print_bowling_section(connection: sqlite3.Connection, player_name: str, recent: int) -> None:
    bowling_summary = connection.execute(
        """
        SELECT
            COUNT(*) AS matches,
            SUM(did_bowl) AS innings_bowled,
            SUM(legal_balls_bowled) AS legal_balls,
            SUM(maidens) AS maidens,
            SUM(runs_conceded) AS runs_conceded,
            SUM(wickets) AS wickets,
            SUM(wides) AS wides,
            SUM(no_balls) AS no_balls
        FROM player_match_bowling
        WHERE player_name = ?
        """,
        (player_name,),
    ).fetchone()

    wickets = bowling_summary["wickets"] or 0
    runs_conceded = bowling_summary["runs_conceded"] or 0
    legal_balls = bowling_summary["legal_balls"] or 0
    average = round(runs_conceded / wickets, 2) if wickets else None
    economy = round((runs_conceded * 6) / legal_balls, 2) if legal_balls else 0.0
    strike_rate = round(legal_balls / wickets, 2) if wickets else None

    print("Bowling Summary")
    print(f"Matches: {bowling_summary['matches'] or 0}")
    print(f"Innings Bowled: {bowling_summary['innings_bowled'] or 0}")
    print(f"Overs: {overs_from_balls(legal_balls)}")
    print(f"Maidens: {bowling_summary['maidens'] or 0}")
    print(f"Runs Conceded: {runs_conceded}")
    print(f"Wickets: {wickets}")
    print(f"Wides: {bowling_summary['wides'] or 0}")
    print(f"No Balls: {bowling_summary['no_balls'] or 0}")
    print(f"Average: {average if average is not None else 'NA'}")
    print(f"Economy: {economy}")
    print(f"Strike Rate: {strike_rate if strike_rate is not None else 'NA'}\n")

    recent_bowling = connection.execute(
        """
        SELECT match_date, match_type, team_name, opponent_name, legal_balls_bowled,
               maidens, runs_conceded, wickets, economy, venue
        FROM player_match_bowling
        WHERE player_name = ?
        ORDER BY match_date DESC
        LIMIT ?
        """,
        (player_name, recent),
    ).fetchall()

    print("Recent Bowling")
    for row in recent_bowling:
        figures = f"{row['wickets']}/{row['runs_conceded']}"
        print(
            f"{row['match_date']} | {row['match_type']} | {row['team_name']} vs {row['opponent_name']} | "
            f"{overs_from_balls(row['legal_balls_bowled'])} overs | {figures} | "
            f"econ {row['economy']} | {row['venue']}"
        )
    print()


def print_role_hints(connection: sqlite3.Connection, player_name: str) -> None:
    batting = connection.execute(
        """
        SELECT AVG(CASE WHEN did_bat = 1 THEN strike_rate END) AS avg_sr, SUM(runs) AS runs
        FROM player_match_batting
        WHERE player_name = ?
        """,
        (player_name,),
    ).fetchone()
    bowling = connection.execute(
        """
        SELECT AVG(CASE WHEN did_bowl = 1 THEN economy END) AS avg_econ, SUM(wickets) AS wickets
        FROM player_match_bowling
        WHERE player_name = ?
        """,
        (player_name,),
    ).fetchone()

    total_runs = batting["runs"] or 0
    total_wickets = bowling["wickets"] or 0
    avg_sr = round(batting["avg_sr"], 2) if batting["avg_sr"] is not None else None
    avg_econ = round(bowling["avg_econ"], 2) if bowling["avg_econ"] is not None else None

    role_tags: list[str] = []
    if total_runs >= 1000:
        role_tags.append("batting volume")
    if avg_sr is not None and avg_sr >= 120:
        role_tags.append("batting intent")
    if total_wickets >= 100:
        role_tags.append("wicket-taking")
    if avg_econ is not None and avg_econ <= 7:
        role_tags.append("control bowler")

    print("Profile Tags")
    print(", ".join(role_tags) if role_tags else "insufficient data")
    print()


def main() -> None:
    args = parse_args()
    if not DB_PATH.exists():
        raise FileNotFoundError(f"Missing database: {DB_PATH}. Run index_cricsheet_players.py first.")

    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row

    total_matches = connection.execute(
        """
        SELECT COUNT(DISTINCT match_id)
        FROM (
            SELECT match_id FROM player_match_batting WHERE player_name = ?
            UNION
            SELECT match_id FROM player_match_bowling WHERE player_name = ?
        )
        """,
        (args.player, args.player),
    ).fetchone()[0]

    print(f"\nPlayer Profile: {args.player}")
    print(f"Indexed Matches: {total_matches}\n")

    print_role_hints(connection, args.player)
    print_batting_section(connection, args.player, args.recent)
    print_bowling_section(connection, args.player, args.recent)

    connection.close()


if __name__ == "__main__":
    main()
