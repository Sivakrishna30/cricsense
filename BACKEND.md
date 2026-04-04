# CricSense Backend

## Current Structure

- `cricsense.db`
  - historical/source store
- `cricsense_analytics.db`
  - derived analytics store
- `app/`
  - FastAPI backend

## Run

1. Create `.env` from `.env.example`
2. Start the API:

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

3. Open:

- `http://127.0.0.1:8000/docs`

## Current API

- `GET /health`
- `GET /system/status`
- `GET /players/search?q=virat`
- `GET /players/{player_name}`
- `GET /players/{player_name}/history`
- `GET /players/{player_name}/splits`
- `GET /coverage/events`
- `GET /context/player-vs-venue?player_name=...&venue=...&years=3`
- `GET /context/player-vs-opponent?player_name=...&opponent=...&years=3`
- `GET /context/batter-vs-bowler?batter=...&bowler=...&years=3`
- `POST /runtime/match-analysis`
- `POST /runtime/team-generation`
- `GET /live/matches`
- `GET /live/matches/{match_id}`
- `GET /live/matches/{match_id}/player-pool`

## Notes

- live routes require `CRICAPI_KEY`
- current live layer is intentionally limited to matches, squads, and scorecards
- commentary is used in the permanent player derivation, not fetched live
- runtime match analysis expects venue/weather/pitch/team/squad input and computes context on demand
