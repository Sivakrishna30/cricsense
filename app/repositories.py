import json

from app.aliases import load_aliases, resolve_player_name
from app.db import analytics_db, source_db


def search_players(query: str, limit: int = 10):
    aliases = load_aliases()
    resolved_query = resolve_player_name(query)
    with analytics_db() as conn:
        rows = conn.execute(
            """
            SELECT player_name, role_profile, final_score AS final_fantasy_score
            FROM player_final_profiles
            WHERE player_name LIKE ?
            ORDER BY final_score DESC, player_name ASC
            LIMIT ?
            """,
            (f"%{resolved_query}%", limit),
        ).fetchall()
        items = [dict(row) for row in rows]
        if items:
            reverse_aliases = {v: k for k, v in aliases.items()}
            for item in items:
                item["canonical_name"] = reverse_aliases.get(item["player_name"], item["player_name"])
            return items

    with source_db() as conn:
        rows = conn.execute(
            """
            SELECT DISTINCT player_name
            FROM player_match_batting
            WHERE player_name LIKE ?
            ORDER BY player_name ASC
            LIMIT ?
            """,
            (f"%{resolved_query}%", limit),
        ).fetchall()
        return [
            {
                "player_name": row["player_name"],
                "canonical_name": {v: k for k, v in aliases.items()}.get(row["player_name"], row["player_name"]),
                "role_profile": None,
                "final_fantasy_score": None,
            }
            for row in rows
        ]


def get_player_derived(player_name: str):
    player_name = resolve_player_name(player_name)
    with analytics_db() as conn:
        row = conn.execute(
            "SELECT * FROM player_final_profiles WHERE player_name = ?",
            (player_name,),
        ).fetchone()
        if not row:
            return None
        data = dict(row)
        data["tags"] = json.loads(data.pop("tags_json"))
        return data


def get_player_recent_history(player_name: str, limit: int = 10):
    player_name = resolve_player_name(player_name)
    with source_db() as conn:
        batting = conn.execute(
            """
            SELECT match_date, event_name, match_type, team_name, opponent_name, venue, runs, balls
            FROM player_match_batting
            WHERE player_name = ? AND match_completed = 1
            ORDER BY match_date DESC
            LIMIT ?
            """,
            (player_name, limit),
        ).fetchall()
        bowling = conn.execute(
            """
            SELECT match_date, event_name, match_type, team_name, opponent_name, venue, wickets, legal_balls_bowled, runs_conceded
            FROM player_match_bowling
            WHERE player_name = ? AND match_completed = 1
            ORDER BY match_date DESC
            LIMIT ?
            """,
            (player_name, limit),
        ).fetchall()
        return {
            "batting": [dict(row) for row in batting],
            "bowling": [dict(row) for row in bowling],
        }


def get_player_style_splits(player_name: str, limit: int = 25):
    player_name = resolve_player_name(player_name)
    with analytics_db() as conn:
        rows = conn.execute(
            """
            SELECT split_category, split_value, balls, runs, dismissals, strike_rate, average
            FROM player_style_splits
            WHERE player_name = ?
            ORDER BY split_category, runs DESC
            LIMIT ?
            """,
            (player_name, limit),
        ).fetchall()
        return [dict(row) for row in rows]


def get_event_coverage():
    with source_db() as conn:
        rows = conn.execute(
            """
            SELECT event_name, COUNT(*) AS match_rows
            FROM player_match_batting
            WHERE event_name IS NOT NULL
            GROUP BY event_name
            ORDER BY match_rows DESC
            LIMIT 50
            """
        ).fetchall()
        return [dict(row) for row in rows]


def find_best_player_match(name: str):
    aliases = load_aliases()
    name = resolve_player_name(name)
    with analytics_db() as conn:
        exact = conn.execute(
            """
            SELECT * FROM player_final_profiles
            WHERE player_name = ?
            """,
            (name,),
        ).fetchone()
        if exact:
            row = dict(exact)
            row["tags"] = json.loads(row.pop("tags_json"))
            row["canonical_name"] = {v: k for k, v in aliases.items()}.get(row["player_name"], row["player_name"])
            return row

        like = conn.execute(
            """
            SELECT * FROM player_final_profiles
            WHERE player_name LIKE ?
            ORDER BY final_score DESC, player_name ASC
            LIMIT 1
            """,
            (f"%{name.split()[-1]}%",),
        ).fetchone()
        if not like:
            return None
        row = dict(like)
        row["tags"] = json.loads(row.pop("tags_json"))
        row["canonical_name"] = {v: k for k, v in aliases.items()}.get(row["player_name"], row["player_name"])
        return row


def find_player_match_strict(name: str):
    aliases = load_aliases()
    name = resolve_player_name(name)
    with analytics_db() as conn:
        exact = conn.execute(
            """
            SELECT * FROM player_final_profiles
            WHERE player_name = ?
            """,
            (name,),
        ).fetchone()
        if not exact:
            return None
        row = dict(exact)
        row["tags"] = json.loads(row.pop("tags_json"))
        row["canonical_name"] = {v: k for k, v in aliases.items()}.get(row["player_name"], row["player_name"])
        return row
