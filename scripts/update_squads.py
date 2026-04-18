import zipfile
import json
import os
from datetime import date
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).parent.parent))
from app.repositories import find_best_player_match

def main():
    zip_path = Path(__file__).parent.parent / "recently_added_30_json.zip"
    dest_path = Path(__file__).parent.parent / "app" / "ipl_recent_squads.json"
    
    if not zip_path.exists():
        print(f"Zip not found at {zip_path}")
        return

    # To ensure we get the latest match for each team, we need to sort json files by match date.
    # Luckily, cricsheet info contains dates. We will parse and store them.
    team_squads = {}
    team_last_date = {}

    try:
        with zipfile.ZipFile(zip_path) as z:
            json_files = [n for n in z.namelist() if n.endswith('.json')]
            
            for name in json_files:
                with z.open(name) as f:
                    data = json.load(f)
                    info = data.get("info", {})
                    event = info.get("event", {}).get("name", "")
                    
                    if "Indian Premier League" in event or "IPL" in event:
                        dates = info.get("dates", [])
                        match_date = dates[0] if dates else "1970-01-01"
                        
                        players_registry = info.get("players", {})
                        for team, players_list in players_registry.items():
                            # If we haven't seen this team, or this match is newer than the last seen:
                            if team not in team_last_date or match_date > team_last_date[team]:
                                team_last_date[team] = match_date
                                mapped = []
                                for p in players_list:
                                    derived = find_best_player_match(p)
                                    mapped.append(derived["player_name"] if derived else p)
                                team_squads[team] = mapped

        with open(dest_path, "w", encoding='utf-8') as f:
            json.dump(team_squads, f, indent=2)
            
        print(f"Extracted {len(team_squads)} IPL squads to {dest_path}")
        for t, squad in team_squads.items():
            print(f"- {t} ({team_last_date[t]}): {len(squad)} players")
            
    except Exception as e:
        print("Error processing zip:", e)

if __name__ == "__main__":
    main()
