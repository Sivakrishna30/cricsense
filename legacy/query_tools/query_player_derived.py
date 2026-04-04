import argparse
import json
import sqlite3
from pathlib import Path


DB_PATH = Path("cricsense_analytics.db")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Query final CricSense player profile.")
    parser.add_argument("--player", required=True, help="Player name")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    row = connection.execute(
        "SELECT * FROM player_final_profiles WHERE player_name = ?",
        (args.player,),
    ).fetchone()
    if not row:
        print("No final profile found.")
        connection.close()
        return

    print(f"\nFinal Profile: {args.player}\n")
    for key in [
        "role_profile",
        "play_type",
        "base_stats_score",
        "context_score",
        "instinct_score",
        "final_score",
        "recent_form_score",
        "consistency_score",
        "selection_trust_score",
        "involvement_score",
        "pressure_score",
        "momentum_score",
        "attack_intent_score",
        "venue_score",
        "opponent_score",
        "format_score",
        "spin_matchup_score",
        "pace_matchup_score",
        "weakness_summary",
    ]:
        print(f"{key}: {row[key]}")

    print(f"tags: {json.loads(row['tags_json'])}")
    connection.close()


if __name__ == "__main__":
    main()
