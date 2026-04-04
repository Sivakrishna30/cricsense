# CricSense Derivation Summary

## Data Layers

Source data in `cricsense.db`:
- `player_match_batting`
- `player_match_bowling`
- `player_ball_by_ball`
- `commentary_events`
- `ball_intelligence`

Derived data in `cricsense_analytics.db`:
- `player_style_splits`
- `player_final_profiles`

## Product Model

CricSense now uses:
1. `stats layer`
2. `context layer`
3. `instinct layer`
4. `match-specific runtime layer`
5. `team-generation layer`

The permanent player table is `player_final_profiles`.
Match-specific context is calculated only at runtime for a selected match.

## 1. Stats Layer

Purpose:
- represent current cricket relevance
- weight recent form and recent consistency more than old career totals

Stored fields:
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

`recent_form_score`
- batters: recent runs, recent SR, recent runs per innings
- bowlers: recent wickets, recent economy

`consistency_score`
- batters: useful innings rate + low-score avoidance
- bowlers: wicket-match rate + economy stability

`cross_tournament_consistency_score`
- uses recent event buckets like IPL, Syed Mushtaq, BBL, SA20, CPL, etc.

`long_term_floor_score`
- light historical floor so tiny samples do not overinflate ratings

## 2. Context Layer

Purpose:
- describe the player’s broad cricket fit and matchup shape

Stored fields:
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

Notes:
- current stored `venue_score` and `opponent_score` are broad context proxies
- exact `player vs venue`, `player vs opponent`, `batter vs bowler` are runtime-only

## 3. Instinct Layer

Purpose:
- capture pressure behavior, momentum influence, and match temperament

Stored fields:
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

## Commentary Usage

Commentary is now used inside the permanent player derivation.

Source:
- `commentary_events` in `cricsense.db`

Commentary-backed signals:
- `commentary_pressure`
- `commentary_momentum`
- `commentary_attack`
- `commentary_fielding`
- `commentary_turning`

These feed:
- `pressure_score`
- `momentum_score`
- `attack_intent_score`
- some tags such as `handles_pressure`

Commentary is not exposed as raw text in the backend output.

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

## Match-Specific Runtime Layer

This is not stored permanently.
It is calculated only when a match is selected.

Inputs:
- venue
- weather summary
- pitch report
- teams
- squads
- recent window, default `3 years`

Runtime context pieces:
- `player vs venue`
- `player vs opponent`
- `batter vs bowler`
- weather/pitch heuristics

Runtime score:

```text
runtime_score =
  base_stats_score * 0.30 +
  match_context_score * 0.35 +
  instinct_score * 0.25 +
  involvement_score * 0.10
```

Also produced:
- `stability_score`
- `upside_score`

## Team Generation Layer

Endpoint generates:
- `common_team_1`
- `common_team_2`
- `risky_team`

Logic:
- `common` teams prioritize runtime score
- `risky` team prioritizes upside score
- maximum `7` players from one team
- captain and vice-captain chosen from the selected team score ordering
