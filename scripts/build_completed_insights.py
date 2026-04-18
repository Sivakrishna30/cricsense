"""
Build completed_match_insights table from Cricsheet ball-by-ball data.
For each completed IPL match that has a cached team_generation_json:
1. Find the match in Cricsheet data
2. Compute fantasy points per player (runs + boundaries + wickets + catches)
3. Rank players → top 11 = IPL Fantasy 11
4. Compare vs our cached CricSense 11 predicted teams
5. Store in completed_match_insights table
"""
import sys, json, zipfile, io, urllib.request
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.db import analytics_db

CREATE_SQL = """
CREATE TABLE IF NOT EXISTS completed_match_insights (
    match_id TEXT PRIMARY KEY,
    match_name TEXT,
    match_date TEXT,
    ipl_fantasy_11_json TEXT,
    cricsense_team1_json TEXT,
    cricsense_team2_json TEXT,
    cricsense_risky_json TEXT,
    team1_intersection INTEGER DEFAULT 0,
    team2_intersection INTEGER DEFAULT 0,
    risky_intersection INTEGER DEFAULT 0,
    computed_at TEXT
)
"""

def compute_fantasy_points(match_data: dict) -> dict:
    """Compute IPL-style fantasy points for each player from ball-by-ball data."""
    points = {}

    innings_list = match_data.get("innings", [])
    for inning_idx, inn in enumerate(innings_list):
        for over in inn.get("overs", []):
            for ball in over.get("deliveries", []):
                batter = ball.get("batter", "")
                bowler = ball.get("bowler", "")
                runs = ball.get("runs", {})
                bat_runs = runs.get("batter", 0)
                extras = runs.get("extras", 0)
                wides = ball.get("extras", {}).get("wides", 0)
                no_balls = ball.get("extras", {}).get("noballs", 0)
                wickets = ball.get("wickets", [])

                # Batting points
                if batter:
                    if batter not in points:
                        points[batter] = {"runs": 0, "fours": 0, "sixes": 0, "wickets": 0, "catches": 0, "dots_bowled": 0, "balls_faced": 0}
                    points[batter]["runs"] += bat_runs
                    if bat_runs == 4:
                        points[batter]["fours"] += 1
                    elif bat_runs == 6:
                        points[batter]["sixes"] += 1
                    if no_balls == 0 and wides == 0:
                        points[batter]["balls_faced"] += 1

                # Bowling points
                if bowler:
                    if bowler not in points:
                        points[bowler] = {"runs": 0, "fours": 0, "sixes": 0, "wickets": 0, "catches": 0, "dots_bowled": 0, "balls_faced": 0}
                    is_legal = no_balls == 0 and wides == 0
                    total_runs_ball = bat_runs + extras
                    if is_legal and total_runs_ball == 0:
                        points[bowler]["dots_bowled"] += 1

                for w in wickets:
                    kind = w.get("kind", "")
                    dismissed = w.get("player_out", "")
                    if kind not in ("run out", "retired hurt", "obstructing the field"):
                        if bowler:
                            if bowler not in points:
                                points[bowler] = {"runs": 0, "fours": 0, "sixes": 0, "wickets": 0, "catches": 0, "dots_bowled": 0, "balls_faced": 0}
                            points[bowler]["wickets"] += 1
                    # Fielder catch/stumping
                    for f in w.get("fielders", []):
                        fname = f.get("name", "")
                        if fname:
                            if fname not in points:
                                points[fname] = {"runs": 0, "fours": 0, "sixes": 0, "wickets": 0, "catches": 0, "dots_bowled": 0, "balls_faced": 0}
                            points[fname]["catches"] += 1

    # Calculate fantasy score
    fantasy = {}
    for player, stats in points.items():
        r = stats["runs"]
        score = r  # 1 pt per run
        score += stats["fours"] * 1   # +1 per boundary (total 5 per 4)
        score += stats["sixes"] * 2   # +2 per six (total 8 per 6)
        # Milestone bonuses
        if r >= 100: score += 16
        elif r >= 50: score += 8
        elif r >= 30: score += 4
        # Duck penalty
        if r == 0 and stats["balls_faced"] >= 1:
            score -= 2
        score += stats["wickets"] * 25
        score += stats["dots_bowled"] * 0.5
        # Wicket haul bonus
        w = stats["wickets"]
        if w >= 5: score += 16
        elif w >= 4: score += 8
        elif w >= 3: score += 4
        score += stats["catches"] * 8
        fantasy[player] = round(score, 1)

    return fantasy


def build_completed_insights():
    # Load completed match IDs from precalculated_matches
    with analytics_db() as conn:
        conn.execute(CREATE_SQL)
        conn.commit()

        rows = conn.execute("""
            SELECT match_id, match_analysis_json, team_generation_json
            FROM precalculated_matches
            WHERE conditions_hash = 'default' AND team_generation_json IS NOT NULL
        """).fetchall()

    if not rows:
        print("No precalculated matches found.")
        return

    # Download Cricsheet zip
    zip_path = Path("recently_added_30_json.zip")
    if not zip_path.exists():
        print("Downloading Cricsheet recent zip...")
        url = "https://cricsheet.org/downloads/recently_added_30_json.zip"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            zip_path.write_bytes(resp.read())

    # Build index: Date -> list of matches on that date
    date_index = {} 
    with zipfile.ZipFile(zip_path) as z:
        for fn in z.namelist():
            if not fn.endswith(".json"): continue
            raw = json.loads(z.read(fn))
            info = raw.get("info", {})
            if "Indian Premier League" not in info.get("event", {}).get("name", ""): continue
            date = info.get("dates", [""])[0]
            if date not in date_index: date_index[date] = []
            date_index[date].append(raw)

    results = []
    for row in rows:
        match_id = row["match_id"]
        analysis = json.loads(row["match_analysis_json"])
        teams_obj = json.loads(row["team_generation_json"])
        match_name = analysis.get("match_name", "Unknown")
        
        # Extract teams from match_name e.g. "Sunrisers Hyderabad vs Chennai Super Kings"
        # or "Royal Challengers Bengaluru vs Delhi Capitals"
        match_teams_raw = match_name.split(",")[0].split(" vs ")
        analysis_teams = {t.strip().lower() for t in match_teams_raw}
        
        # Try to find match date
        match_date = analysis.get("date", "")
        
        candidates = date_index.get(match_date, [])
        if not candidates:
            # Fallback: check all available IPL matches in the zip
            candidates = [m for sublist in date_index.values() for m in sublist]

        best_match = None
        for cand in candidates:
            cand_teams = {t.lower() for t in cand["info"].get("teams", [])}
            # Match if both teams found in candidate
            matches = 0
            for at in analysis_teams:
                # Fuzzy team match (e.g. "SRH" in "Sunrisers Hyderabad" or vice versa)
                if any(at in ct or ct in at for ct in cand_teams):
                    matches += 1
            if matches >= 2:
                best_match = cand
                break
        
        if not best_match:
            print(f"  SKIPPING {match_name}: No Cricsheet match found for teams {analysis_teams}")
            continue

        fantasy = compute_fantasy_points(best_match)
        if not fantasy:
            print(f"  ERROR {match_name}: Computed 0 fantasy points from Cricsheet JSON")
            continue

        sorted_players = sorted(fantasy.items(), key=lambda x: x[1], reverse=True)
        ipl_f11 = [{"player_name": p, "actual_fantasy_points": pts} for p, pts in sorted_players[:11]]
        ipl_f11_names = {p["player_name"].lower() for p in ipl_f11}

        # Compare vs our teams
        def extract_players(team_key):
            t = teams_obj.get(team_key, {})
            players_raw = t.get("players", [])
            return [p["player_name"] if isinstance(p, dict) else p for p in players_raw]

        def get_intersection(team_key):
            p_names = {n.lower() for n in extract_players(team_key)}
            # Fuzzy match player names (e.g. "V Kohli" matches "Virat Kohli")
            count = 0
            for pn in p_names:
                if any(pn in fn or fn in pn for fn in ipl_f11_names):
                    count += 1
            return count

        def build_team_json(team_key, label):
            t = teams_obj.get(team_key, {})
            if not t: return None
            players = extract_players(team_key)
            return json.dumps({
                "team_type": label,
                "captain": t.get("captain"),
                "vice_captain": t.get("vice_captain"),
                "players": [{"player_name": n} for n in players],
                "intersection_count": get_intersection(team_key),
            })

        results.append((
            match_id, match_name, match_date,
            json.dumps(ipl_f11),
            build_team_json("common_team_1", "CricSense 11 — Prediction 1"),
            build_team_json("common_team_2", "CricSense 11 — Prediction 2"),
            build_team_json("risky_team", "CricSense 11 — High Risk"),
            get_intersection("common_team_1"),
            get_intersection("common_team_2"),
            get_intersection("risky_team"),
            datetime.now().isoformat(),
        ))
        print(f"  SUCCESS {match_name}: Found {len(fantasy)} players, Intersection={get_intersection('common_team_1')}/11")

    with analytics_db() as conn:
        conn.executemany("""
            INSERT OR REPLACE INTO completed_match_insights (
                match_id, match_name, match_date,
                ipl_fantasy_11_json, cricsense_team1_json, cricsense_team2_json, cricsense_risky_json,
                team1_intersection, team2_intersection, risky_intersection,
                computed_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, results)
        conn.commit()
        count = conn.execute("SELECT COUNT(*) FROM completed_match_insights").fetchone()[0]
        print(f"\nDone! {count} completed match insights stored.")


if __name__ == "__main__":
    build_completed_insights()
