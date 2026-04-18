import sqlite3
import os
from pathlib import Path

DB_PATH = "cricsense.db"
CUTOFF_DATE = "2021-04-01"

def transform():
    if not os.path.exists(DB_PATH):
        print(f"DB not found at {DB_PATH}")
        return

    initial_size = os.path.getsize(DB_PATH) / (1024 * 1024)
    print(f"Initial DB Size: {initial_size:.2f} MB")

    conn = sqlite3.connect(DB_PATH)
    try:
        # 1. Count rows to delete
        r = conn.execute("SELECT COUNT(*) FROM player_match_batting WHERE match_date < ?", (CUTOFF_DATE,)).fetchone()[0]
        print(f"Historical batting rows to delete: {r}")

        if r > 0:
            print("Deleting historical data (Pre-2021)...")
            conn.execute("DELETE FROM player_match_batting WHERE match_date < ?", (CUTOFF_DATE,))
            conn.execute("DELETE FROM player_match_bowling WHERE match_date < ?", (CUTOFF_DATE,))
            conn.execute("DELETE FROM player_ball_by_ball WHERE match_date < ?", (CUTOFF_DATE,))
            conn.commit()
            print("Deletions committed.")

        print("Vacuuming database (this physically shrinks the file)...")
        conn.execute("VACUUM")
        print("Vacuum complete.")

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        conn.close()

    final_size = os.path.getsize(DB_PATH) / (1024 * 1024)
    print(f"Final DB Size: {final_size:.2f} MB")
    print(f"Reduction: {initial_size - final_size:.2f} MB ({(1 - final_size/initial_size)*100:.1f}%)")

if __name__ == "__main__":
    transform()
