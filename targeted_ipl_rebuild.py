import sqlite3
import derive_player_layers as d
from app.db import source_db, analytics_db

def targeted_rebuild():
    print("=== Targeted IPL 2026 Player Re-derivation ===")
    
    # 1. Identify IPL 2026 players
    with source_db() as conn:
        players = conn.execute("""
            SELECT DISTINCT player_name FROM player_match_batting WHERE season = '2026'
            UNION
            SELECT DISTINCT player_name FROM player_match_bowling WHERE season = '2026'
        """).fetchall()
        target_names = [row[0] for row in players]
    
    print(f"Found {len(target_names)} players in IPL 2026 season.")
    
    # 2. Run derivation for targets
    # We don't want to reset the whole table, but the INSERT INTO ... ON CONFLICT (if it had one) would be better.
    # However, derive_player_layers.reset_output_tables clears everything.
    # To save time and keep others, I'll modify the script to DELETE ONLY the target players before inserting.
    
    read_conn = sqlite3.connect(f"file:{d.SOURCE_DB_PATH}?mode=ro", uri=True)
    write_conn = sqlite3.connect(d.OUTPUT_DB_PATH)
    
    print("Cleaning up old profiles for target players...")
    placeholders = ', '.join(['?'] * len(target_names))
    write_conn.execute(f"DELETE FROM player_final_profiles WHERE player_name IN ({placeholders})", target_names)
    write_conn.commit()
    
    print("Re-deriving profiles with new weighted logic...")
    d.derive_player_profiles(read_conn, write_conn, target_players=target_names)
    
    read_conn.close()
    write_conn.close()
    print("\nTargeted rebuild complete.")

if __name__ == "__main__":
    targeted_rebuild()
