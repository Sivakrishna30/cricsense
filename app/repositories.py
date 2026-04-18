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
        
        events = {}
        for row in batting:
            d = dict(row)
            events[d["match_date"]] = d

        for row in bowling:
            d = dict(row)
            if d["match_date"] in events:
                events[d["match_date"]]["wickets"] = d["wickets"]
                events[d["match_date"]]["runs_conceded"] = d["runs_conceded"]
                events[d["match_date"]]["legal_balls_bowled"] = d["legal_balls_bowled"]
            else:
                d["runs"] = None
                d["balls"] = None
                events[d["match_date"]] = d
                
        merged = sorted(events.values(), key=lambda x: x["match_date"], reverse=True)
        return merged[:limit]


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

def get_venue_stats(venue_name: str):
    with analytics_db() as conn:
        row = conn.execute("SELECT * FROM venue_stats WHERE venue = ?", (venue_name,)).fetchone()
        if row:
            return dict(row)
            
        venues = conn.execute("SELECT venue FROM venue_stats").fetchall()
        v_lower = venue_name.lower().replace(".", "").replace(",", "")
        ignore = {"stadium", "cricket", "international", "association", "ground", "sports"}
        w1 = {w for w in v_lower.split() if len(w) > 3 and w not in ignore}
        
        best_match = None
        best_score = 0
        for v in venues:
            db_v = v[0].lower().replace(".", "").replace(",", "")
            w2 = {w for w in db_v.split() if len(w) > 3 and w not in ignore}
            score = len(w1.intersection(w2))
            if score > best_score:
                best_score = score
                best_match = v[0]
                
        if best_match and best_score >= 1:
            return dict(conn.execute("SELECT * FROM venue_stats WHERE venue = ?", (best_match,)).fetchone())
            
        return None
