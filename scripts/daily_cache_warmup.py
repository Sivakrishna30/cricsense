import sys
import os
from pathlib import Path
import json

sys.path.append(str(Path(__file__).parent.parent))

from app.matchday import MatchdayService
from app.runtime import generate_teams, analyze_match
from app.db import analytics_db

def init_table():
    with analytics_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS precalculated_matches (
                match_id TEXT,
                conditions_hash TEXT,
                match_analysis_json TEXT,
                team_generation_json TEXT,
                PRIMARY KEY (match_id, conditions_hash)
            )
        """)
        conn.commit()

def main():
    print("Starting default daily cache warmup (1 base calculation per match)...")
    init_table()
    
    service = MatchdayService()
    try:
        matches = service.get_today_ipl_matches(include_squads=True)
        date = matches.get('date')
        match_list = matches.get('matches', [])
        
        for m in match_list:
            team_names = [t.get("teamName", t.get("name")) for t in m.get("squads", [])] if m.get("squads") else []
            if not team_names:
                continue
            
            payload = {
                "match_id": m["id"],
                "match_name": m["name"],
                "competition": "Indian Premier League",
                "venue": m["venue"],
                "dew": False,
                "pitch_surface": "",
                "toss_batting": "",
                "teams": [{"name": t.get("teamName", t.get("name")), "squad": [p["name"] for p in t.get("players", [])]} for t in m.get("squads", [])]
            }
            
            with analytics_db() as a_conn:
                try:
                    a_data = analyze_match(payload)
                    t_data = generate_teams(payload)
                    
                    a_conn.execute("""
                        INSERT OR REPLACE INTO precalculated_matches (match_id, conditions_hash, match_analysis_json, team_generation_json)
                        VALUES (?, 'default', ?, ?)
                    """, (m["id"], json.dumps(a_data), json.dumps(t_data)))
                    print(f"  Saved default cache sequence for {m['id']}")
                except Exception as e:
                    print(f"Failed iter: {e}")
                    pass
                a_conn.commit()
        
        print(f"Warmup successful! Handled {len(match_list)} matches for {date}.")
    except Exception as e:
        print(f"Warmup strictly failed: {e}")

if __name__ == "__main__":
    main()
