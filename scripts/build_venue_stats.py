import sys
import os
from pathlib import Path
from datetime import date, timedelta
import sqlite3

# Add root path to sys so app modules can be imported
sys.path.append(str(Path(__file__).parent.parent))

from app.db import source_db, analytics_db

def main():
    print("Building Venue Intelligence...")
    
    # Calculate cutoff for last 4 years of IPL data
    cutoff = (date.today() - timedelta(days=365*4)).isoformat()
    
    with source_db() as conn:
        rows = conn.execute("""
            SELECT match_id, match_date, venue, team_name, winner, win_by_type, SUM(runs) as total_runs
            FROM player_match_batting
            WHERE event_name LIKE '%Indian Premier League%' AND match_date >= ?
            GROUP BY match_id, team_name
        """, (cutoff,)).fetchall()
        
    matches = {}
    for r in rows:
        m_id = r["match_id"]
        if m_id not in matches:
            matches[m_id] = {
                "venue": r["venue"],
                "winner": r["winner"],
                "win_by_type": r["win_by_type"],
                "teams": []
            }
        matches[m_id]["teams"].append({
            "name": r["team_name"],
            "score": r["total_runs"]
        })
        
    venue_metrics = {}
    
    for m_id, m_data in matches.items():
        if len(m_data["teams"]) != 2: continue
        
        t1 = m_data["teams"][0]
        t2 = m_data["teams"][1]
        
        venue = m_data["venue"]
        winner = m_data["winner"]
        win_by_type = (m_data["win_by_type"] or "").lower()
        
        if venue not in venue_metrics:
            venue_metrics[venue] = {
                "matches": 0,
                "first_inn_scores": [],
                "second_inn_scores": [],
                "chasing_wins": 0
            }
            
        # Determine innings based on result type
        # If won by runs, winner batted first
        # If won by wickets, winner chased (batted second)
        v_data = venue_metrics[venue]
        v_data["matches"] += 1
        
        if win_by_type == "runs":
            if t1["name"] == winner:
                v_data["first_inn_scores"].append(t1["score"])
                v_data["second_inn_scores"].append(t2["score"])
            else:
                v_data["first_inn_scores"].append(t2["score"])
                v_data["second_inn_scores"].append(t1["score"])
        elif win_by_type == "wickets":
            v_data["chasing_wins"] += 1
            if t1["name"] == winner:
                v_data["second_inn_scores"].append(t1["score"])
                v_data["first_inn_scores"].append(t2["score"])
            else:
                v_data["second_inn_scores"].append(t2["score"])
                v_data["first_inn_scores"].append(t1["score"])
        else:
            # draw/tie etc, assume higher score was first innings (proxy)
            if t1["score"] >= t2["score"]:
                v_data["first_inn_scores"].append(t1["score"])
                v_data["second_inn_scores"].append(t2["score"])
            else:
                v_data["first_inn_scores"].append(t2["score"])
                v_data["second_inn_scores"].append(t1["score"])
                
    # Prepare inserts
    final_rows = []
    for venue, data in venue_metrics.items():
        if data["matches"] < 2: continue
        
        fio = data["first_inn_scores"]
        sio = data["second_inn_scores"]
        
        avg_1 = round(sum(fio) / len(fio)) if fio else 0
        avg_2 = round(sum(sio) / len(sio)) if sio else 0
        chasing_win_pct = round((data["chasing_wins"] / data["matches"]) * 100)
        
        final_rows.append((venue, data["matches"], avg_1, avg_2, chasing_win_pct))

    print(f"Computed stats for {len(final_rows)} venues.")
        
    with analytics_db() as a_conn:
        a_conn.execute("DROP TABLE IF EXISTS venue_stats")
        a_conn.execute("""
            CREATE TABLE venue_stats (
                venue TEXT PRIMARY KEY,
                matches_sampled INTEGER,
                avg_first_innings INTEGER,
                avg_second_innings INTEGER,
                chasing_win_percent INTEGER
            )
        """)
        a_conn.executemany("""
            INSERT INTO venue_stats (venue, matches_sampled, avg_first_innings, avg_second_innings, chasing_win_percent)
            VALUES (?, ?, ?, ?, ?)
        """, final_rows)
        a_conn.commit()

    print("Success: venue_stats table created in cricsense_analytics.db")

if __name__ == "__main__":
    main()
