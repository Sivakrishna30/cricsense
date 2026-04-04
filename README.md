# CricSense

CricSense is a cricket intelligence backend for match-specific player analysis and fantasy team generation.

The project is built around one principle:

`No secret ingredients.`

The model should be understandable, reviewable, and improvable. Trust comes from transparent data, transparent formulas, and clear limitations.

## What CricSense Does

CricSense is not trying to be:
- a raw score app
- a historical stats dump
- a black-box prediction engine

It is trying to answer:
- Which players look strong for this match?
- Why do they look strong?
- What are their strengths and risks?
- How do venue, matchup, toss, weather, and pitch change the picture?
- What fantasy teams make sense for `safe/common` and `risky/upside` play styles?

## Current Architecture

### Source Data

Raw/source data lives in `cricsense.db`.

Main source tables:
- `player_match_batting`
- `player_match_bowling`
- `player_ball_by_ball`
- `commentary_events`
- `ball_intelligence`

### Derived Data

Derived/product-facing data lives in `cricsense_analytics.db`.

Main derived tables:
- `player_style_splits`
- `player_final_profiles`

### Backend

The backend is a FastAPI app in [`app/`](C:/Users/DELL/Downloads/cricsense/app).

## Scoring Philosophy

The model currently has `3` permanent player layers and `1` runtime match layer.

### 1. Stats Layer

Purpose:
- represent current cricket relevance
- reward recent form and recent consistency
- keep only a light long-term floor

Main stored fields:
- `base_stats_score`
- `recent_form_score`
- `consistency_score`
- `selection_trust_score`

Current formula:

```text
base_stats_score =
  recent_form_score * 0.35 +
  consistency_score * 0.30 +
  cross_tournament_consistency_score * 0.20 +
  long_term_floor_score * 0.15
```

Interpretation:
- recent form matters most
- repeated usefulness matters a lot
- performances across recent tournaments matter
- old career data is only a stabilizer

### 2. Context Layer

Purpose:
- describe the player’s cricket fit and broad matchup shape

Main stored fields:
- `context_score`
- `role_profile`
- `play_type`
- `venue_score`
- `opponent_score`
- `format_score`
- `spin_matchup_score`
- `pace_matchup_score`
- `weakness_summary`
- `tags_json`

Current formula:

```text
context_score =
  venue_score * 0.25 +
  opponent_score * 0.25 +
  format_score * 0.15 +
  bowling_style_matchup_score * 0.20 +
  recent_context_form * 0.15
```

Important note:
- the stored context layer is a broad player-context identity
- exact `player vs venue`, `player vs opponent`, and `batter vs bowler` are calculated only at runtime

### 3. Instinct Layer

Purpose:
- capture pressure handling, momentum impact, and match temperament

Main stored fields:
- `instinct_score`
- `pressure_score`
- `momentum_score`
- `attack_intent_score`

Current formula:

```text
instinct_score =
  pressure_score * 0.30 +
  momentum_score * 0.25 +
  attack_intent_score * 0.20 +
  smart_aggression_score * 0.15 +
  bounce_back_score * 0.10
```

Interpretation:
- pressure and momentum matter most
- attack intent matters, but not alone
- blind aggression is not the goal
- recovery after failures still matters

## Commentary Usage

Commentary is used as an internal analytical input, not as an output product.

Source:
- `commentary_events` in `cricsense.db`

Current commentary-derived signals:
- `commentary_pressure`
- `commentary_momentum`
- `commentary_attack`
- `commentary_fielding`
- `commentary_turning`

These are used to strengthen:
- `pressure_score`
- `momentum_score`
- `attack_intent_score`
- a few English tags such as pressure-handling or death-over relevance

Raw commentary text is not returned by the API.

## Final General Player Score

Stored field:
- `final_score`

Current formula:

```text
final_score =
  base_stats_score * 0.35 +
  context_score * 0.25 +
  instinct_score * 0.25 +
  recent_form_score * 0.10 +
  involvement_score * 0.05
```

Interpretation:
- the permanent player profile is mostly driven by stats, context, and instinct
- it is not supposed to be the final match-specific fantasy answer by itself

## Runtime Match Layer

This is the match-specific layer.

It is not stored permanently.
It is calculated only when a match is selected.

Inputs:
- `competition`
- `venue`
- `weather`
- `pitch_report`
- `toss_winner`
- `toss_decision`
- `teams`
- `squads`
- recent window, default `3 years`

Runtime context pieces:
- `player vs venue`
- `player vs opponent`
- `batter vs bowler`
- competition-specific recent form
- weather and pitch heuristics
- toss and dew adjustments

Current runtime score:

```text
runtime_score =
  base_stats_score * 0.24 +
  match_context_score * 0.35 +
  instinct_score * 0.25 +
  involvement_score * 0.10 +
  competition_boost * 0.06
```

Additional runtime scores:
- `stability_score`
- `upside_score`

### Toss and Dew Logic

The runtime layer currently adjusts for:
- chasing boost if dew is likely
- penalty for bowlers bowling second in dew
- stronger penalty for spinners bowling second in dew
- small dry-ball spin boost when spin bowlers bowl first on a dry surface

This is intentionally simple and explicit.

## Team Generation

Current output:
- `common_team_1`
- `common_team_2`
- `risky_team`

Current constraints:
- `11` players
- Dream11-style category templates
- max `7` from one team
- max `4` overseas players

Current category templates:

```text
common_team_1 = 1 WK, 4 BAT, 2 AR, 4 BWL
common_team_2 = 1 WK, 3 BAT, 3 AR, 4 BWL
risky_team    = 1 WK, 3 BAT, 4 AR, 3 BWL
```

Captain and vice-captain are currently selected from the generated team ordering.

## English Insights

The runtime layer also returns simple UI-friendly labels such as:
- `Strong recent form in this competition`
- `Consistent recent returns in this competition`
- `Good batting record at this venue`
- `Reliable record against this opponent`
- `Useful in death-over phases`
- `Can slow down against spin`
- `Dew may help chasing batters`
- `Wet ball may reduce spin grip`

These are explanations built on top of the scoring outputs, not extra hidden logic.

## API Summary

Main routes:
- `GET /health`
- `GET /system/status`
- `GET /players/search?q=...`
- `GET /players/{player_name}`
- `GET /players/{player_name}/history`
- `GET /players/{player_name}/splits`
- `GET /coverage/events`
- `GET /context/player-vs-venue`
- `GET /context/player-vs-opponent`
- `GET /context/batter-vs-bowler`
- `POST /runtime/match-analysis`
- `POST /runtime/team-generation`
- `GET /live/matches`
- `GET /live/matches/{match_id}`
- `GET /live/matches/{match_id}/player-pool`

For more API notes, see [BACKEND.md](C:/Users/DELL/Downloads/cricsense/BACKEND.md).

## Running the Backend

1. Create `.env` from `.env.example`
2. Start the API:

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

3. Open:

```text
http://127.0.0.1:8000/docs
```

## Current Limitations

This project is usable, but not finished in every area.

Known limitations:
- some player-name aliasing still depends on manual mapping
- live commentary/highlights are not yet part of the runtime pipeline
- live score support is limited to match list, squad, and scorecard
- some context heuristics are still simplified proxies
- captain/vice-captain logic can still be refined
- team generation is rule-aware, but still heuristic

## Data Transparency

This repository intentionally documents:
- the source tables
- the derived tables
- the scoring layers
- the formulas
- the constraints
- the current limitations

If a result looks wrong, it should be debuggable.
If a formula is weak, it should be replaceable.
If a tag is misleading, it should be auditable.

That transparency is a feature, not a compromise.

## Reference Files

- [DERIVED_LOGIC.md](C:/Users/DELL/Downloads/cricsense/DERIVED_LOGIC.md)
- [BACKEND.md](C:/Users/DELL/Downloads/cricsense/BACKEND.md)
