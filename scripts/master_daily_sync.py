import sys
import json
import urllib.request
import zipfile
import sqlite3
from pathlib import Path
from datetime import datetime

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

# Import logic from other scripts
from scripts.ingest_recent_updates import ingest_recent_updates
import derive_player_layers as dpl
import scripts.build_completed_insights as bci
import scripts.daily_cache_warmup as dcw
import scripts.build_venue_stats as bvs

ZIP_PATH = BASE_DIR / "recently_added_30_json.zip"
ZIP_URL = "https://cricsheet.org/downloads/recently_added_30_json.zip"

def master_sync():
    print(f"[{datetime.now().isoformat()}] CRICSENSE MASTER DAILY SYNC STARTING...")
    
    # Step 1: Download latest Cricsheet data
    try:
        print("\nStep 1: Downloading latest Cricsheet data...")
        req = urllib.request.Request(ZIP_URL, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = resp.read()
        ZIP_PATH.write_bytes(data)
        print(f"  [SUCCESS] Downloaded {len(data)/1024/1024:.2f} MB.")
    except Exception as e:
        print(f"  [CRITICAL ERROR] Failed to download Cricsheet data: {e}")
        # Continue anyway to process whatever we already have in local ZIP if exists
    
    # Step 2: Ingest into Source DB
    try:
        print("\nStep 2: Ingesting into cricsense.db...")
        ingest_recent_updates()
        print("  [SUCCESS] Source database updated.")
    except Exception as e:
        print(f"  [ERROR] Ingestion failed: {e}")

    # Step 3: Re-derive Intelligence Layers (Form, Roles, Tags)
    try:
        print("\nStep 3: Re-deriving Intelligence Layers (Player Profiles)...")
        read_conn = sqlite3.connect(f"file:{dpl.SOURCE_DB_PATH}?mode=ro", uri=True)
        write_conn = sqlite3.connect(dpl.OUTPUT_DB_PATH)
        
        dpl.reset_output_tables(write_conn)
        print("  Calculating style splits...")
        dpl.derive_style_splits(read_conn, write_conn)
        print("  Calculating player profiles and form weighting...")
        dpl.derive_player_profiles(read_conn, write_conn)
        
        read_conn.close()
        write_conn.close()
        print("  [SUCCESS] Intelligence layers refreshed.")
    except Exception as e:
        print(f"  [ERROR] Intelligence derivation failed: {e}")

    # Step 4: Build Venue Analytics
    try:
        print("\nStep 4: Rebuilding venue stats...")
        bvs.main()
        print("  [SUCCESS] Venue analytics updated.")
    except Exception as e:
        print(f"  [ERROR] Venue stats failed: {e}")

    # Step 5: Index Accuracy Insights (Yesterday's Match vs Preds)
    try:
        print("\nStep 5: Indexing completed match accuracy reports...")
        bci.build_completed_insights()
        print("  [SUCCESS] Accuracy insights populated.")
    except Exception as e:
        print(f"  [ERROR] Accuracy computation failed: {e}")

    # Step 6: Daily Cache Warmup (Pre-calculate Today's Predictions)
    try:
        print("\nStep 6: Warming up cache for today's matches...")
        dcw.main()
        print("  [SUCCESS] Today's predictions are pre-rendered.")
    except Exception as e:
        print(f"  [ERROR] Cache warmup failed: {e}")

    print(f"\n[{datetime.now().isoformat()}] CRICSENSE MASTER DAILY SYNC COMPLETE.")

if __name__ == "__main__":
    master_sync()
