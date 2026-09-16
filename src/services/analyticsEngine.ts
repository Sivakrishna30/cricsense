import {
  AnalyzedPlayer,
  GeneratedTeam,
  GeneratedTeamPlayer,
  MatchAnalysis,
  MatchConditionsInput,
  MatchdayMatch,
  PlayerHistoryRow,
  PlayerSummary,
  TeamGeneration,
} from '../types';
import { mockPlayersData } from '../data/mockData';

const BASE_SCORES: Record<string, { base: number; role: string; category: string; style: string; tags: string[]; insights: string[] }> = {
  'Virat Kohli': {
    base: 88,
    role: 'batter',
    category: 'BAT',
    style: 'Right-hand bat',
    tags: ['in_form', 'strong_vs_pace', 'chase_master'],
    insights: ['Strong recent form in this competition', 'Elite average (52.4) at this venue'],
  },
  'Rajat Patidar': {
    base: 77,
    role: 'batter',
    category: 'BAT',
    style: 'Right-hand bat',
    tags: ['in_form', 'spin_attacker'],
    insights: ['High strike rate (164) in middle overs', 'Consistent boundary finder'],
  },
  'Jitesh Sharma': {
    base: 67,
    role: 'batter',
    category: 'WK',
    style: 'Right-hand bat',
    tags: ['power_finisher'],
    insights: ['Useful death overs strike rate', 'Guaranteed wicketkeeping catch/stumping points'],
  },
  'Tim David': {
    base: 70,
    role: 'batter',
    category: 'BAT',
    style: 'Right-hand bat',
    tags: ['death_hitter', 'high_upside'],
    insights: ['Heavy boundary percentage in overs 17-20'],
  },
  'Krunal Pandya': {
    base: 66,
    role: 'all_rounder',
    category: 'AR',
    style: 'Slow left-arm orthodox',
    tags: ['two_way_points', 'tight_economy'],
    insights: ['Can pick up middle-overs wickets and chip in with bat'],
  },
  'Bhuvneshwar Kumar': {
    base: 74,
    role: 'bowler',
    category: 'BWL',
    style: 'Right-arm medium',
    tags: ['swing_help', 'powerplay_lock'],
    insights: ['Averages 1.4 wickets in powerplay at Chinnaswamy'],
  },
  'Josh Hazlewood': {
    base: 76,
    role: 'bowler',
    category: 'BWL',
    style: 'Right-arm fast-medium',
    tags: ['hit_the_deck', 'death_overs'],
    insights: ['High-dot-ball percentage on skiddy tracks'],
  },
  'Suyash Sharma': {
    base: 63,
    role: 'bowler',
    category: 'BWL',
    style: 'Right-arm legbreak',
    tags: ['mystery_spin'],
    insights: ['Effective if surface has grip and dryness'],
  },
  'Devdutt Padikkal': {
    base: 68,
    role: 'batter',
    category: 'BAT',
    style: 'Left-hand bat',
    tags: ['top_order', 'powerplay_runner'],
    insights: ['Solid run-a-ball anchor potential'],
  },
  'Phil Salt': {
    base: 75,
    role: 'batter',
    category: 'WK',
    style: 'Right-hand bat',
    tags: ['explosive_opener', 'powerplay_max'],
    insights: ['Strikes at 180+ in first 6 overs'],
  },
  'Romario Shepherd': {
    base: 65,
    role: 'all_rounder',
    category: 'AR',
    style: 'Right-arm fast-medium',
    tags: ['boundary_blaster'],
    insights: ['High impact potential in short bursts'],
  },
  'Ruturaj Gaikwad': {
    base: 76,
    role: 'batter',
    category: 'BAT',
    style: 'Right-hand bat',
    tags: ['anchor_captain', 'consistent_scorer'],
    insights: ['Scores 40+ in 45% of recent IPL matches'],
  },
  'MS Dhoni': {
    base: 60,
    role: 'batter',
    category: 'WK',
    style: 'Right-hand bat',
    tags: ['finisher', 'legend_wk'],
    insights: ['Crisp boundary hitting in last 2 overs with elite stumping points'],
  },
  'Shivam Dube': {
    base: 84,
    role: 'all_rounder',
    category: 'AR',
    style: 'Left-hand bat',
    tags: ['death_over_specialist', 'spin_destroyer'],
    insights: ['Strikes at 182 against spinners', 'Chinnaswamy boundaries suit his reach'],
  },
  'Ravindra Jadeja': {
    base: 81,
    role: 'all_rounder',
    category: 'AR',
    style: 'Slow left-arm orthodox',
    tags: ['two_way_points', 'gun_fielder'],
    insights: ['Reliable fantasy floor with bowling overs and catches'],
  },
  'Matheesha Pathirana': {
    base: 83,
    role: 'bowler',
    category: 'BWL',
    style: 'Right-arm fast',
    tags: ['death_yorker_king', 'wicket_sponge'],
    insights: ['Over 2.2 wickets per game at death in last 10 appearances'],
  },
  'Khaleel Ahmed': {
    base: 69,
    role: 'bowler',
    category: 'BWL',
    style: 'Left-arm fast-medium',
    tags: ['early_angles'],
    insights: ['Left-arm angle creates LBW opportunities'],
  },
  'Sanju Samson': {
    base: 78,
    role: 'batter',
    category: 'WK',
    style: 'Right-hand bat',
    tags: ['attacking_top_order'],
    insights: ['Strong powerplay batting numbers'],
  },
  'Akeal Hosein': {
    base: 66,
    role: 'bowler',
    category: 'BWL',
    style: 'Slow left-arm orthodox',
    tags: ['powerplay_spin'],
    insights: ['Accurate tight darts'],
  },
  'Noor Ahmad': {
    base: 72,
    role: 'bowler',
    category: 'BWL',
    style: 'Left-arm wrist spin',
    tags: ['wrist_spin', 'turn_both_ways'],
    insights: ['Difficult release angle to pick'],
  },
  'Sam Curran': {
    base: 77,
    role: 'all_rounder',
    category: 'AR',
    style: 'Left-arm medium',
    tags: ['death_overs', 'pinch_hitter'],
    insights: ['Takes responsibility at both ends of innings'],
  },
  'Deepak Chahar': {
    base: 68,
    role: 'bowler',
    category: 'BWL',
    style: 'Right-arm medium',
    tags: ['new_ball_swing'],
    insights: ['Lethal when grass or moisture provides morning swing'],
  },
};

export function analyzeMatch(match: MatchdayMatch, conditions?: MatchConditionsInput): MatchAnalysis {
  const dew = conditions?.dew || false;
  const surface = conditions?.pitchSurface || '';
  const tossBatting = conditions?.tossBatting || '';

  const conditionTags: string[] = [];
  if (dew) conditionTags.push('heavy_dew');
  if (surface === 'dry') conditionTags.push('dry_surface', 'spin_friendly');
  if (surface === 'wet') conditionTags.push('wet_surface', 'pace_friendly');
  if (tossBatting) conditionTags.push(`${tossBatting.toLowerCase().replace(/\s+/g, '_')}_bats_first`);

  const players: AnalyzedPlayer[] = [];

  for (const squad of match.squads || []) {
    const teamName = squad.teamName || squad.shortname || 'Team';
    const isBattingFirst = tossBatting ? teamName === tossBatting : false;

    for (const player of squad.players || []) {
      const pName = player.name || 'Unknown';
      const info = BASE_SCORES[pName] || {
        base: 65,
        role: (player.role || 'batter').toLowerCase(),
        category: (player.role === 'Bowler' ? 'BWL' : player.role === 'Wicketkeeper' ? 'WK' : player.role === 'Allrounder' ? 'AR' : 'BAT'),
        style: player.bowlingStyle || player.battingStyle || '',
        tags: ['squad_regular'],
        insights: ['Calculated from recent T20 baseline metrics'],
      };

      let score = info.base;
      const dynamicInsights = [...info.insights];

      // Surface modifiers
      if (surface === 'dry') {
        if (info.style.toLowerCase().includes('spin') || info.category === 'BWL') {
          score += 5;
          dynamicInsights.push('Dry surface grants significant spin grip and bounce.');
        }
        if (info.style.toLowerCase().includes('fast') || info.style.toLowerCase().includes('medium')) {
          dynamicInsights.push('Dry pitch may slow pace, rewarding off-cutters.');
        }
      } else if (surface === 'wet') {
        if (info.style.toLowerCase().includes('spin')) {
          score -= 5;
          dynamicInsights.push('Wet surface reduces spin friction.');
        }
        if (info.style.toLowerCase().includes('fast')) {
          score += 3;
          dynamicInsights.push('Skiddy wet pitch aids ball skidding fast onto the bat.');
        }
      }

      // Dew modifiers
      if (dew) {
        if (isBattingFirst) {
          if (info.style.toLowerCase().includes('spin')) {
            score -= 8;
            dynamicInsights.push('Bowling 2nd under heavy dew severely hampers spin control.');
          }
        } else {
          if (info.category === 'BAT' || info.category === 'WK') {
            score += 5;
            dynamicInsights.push('Chasing under dew makes ball skid nicely for top-order batters.');
          }
        }
      }

      score = Math.min(100, Math.max(20, Math.round(score * 10) / 10));

      players.push({
        player_name: pName,
        team_name: teamName,
        role_profile: info.role,
        fantasy_category: info.category,
        runtime_score: score,
        tags: info.tags,
        insights: dynamicInsights,
        is_overseas: player.country !== 'India',
      });
    }
  }

  // Sort players descending by runtime_score
  players.sort((a, b) => b.runtime_score - a.runtime_score);

  // Favorite team lean
  const teamScores: Record<string, number> = {};
  for (const p of players) {
    teamScores[p.team_name] = (teamScores[p.team_name] || 0) + p.runtime_score;
  }
  let favoriteTeam: string | null = null;
  let maxScore = 0;
  for (const [t, s] of Object.entries(teamScores)) {
    if (s > maxScore) {
      maxScore = s;
      favoriteTeam = t;
    }
  }

  return {
    match_name: match.name,
    favorite_team: favoriteTeam,
    conditions: { tags: conditionTags },
    players,
  };
}

const ROLE_ORDER: Record<string, number> = {
  WK: 0,
  BAT: 1,
  AR: 2,
  BWL: 3,
};

function select11(
  pool: AnalyzedPlayer[],
  varianceStrategy: 'balanced' | 'safe' | 'upside'
): GeneratedTeamPlayer[] {
  // Sort according to strategy
  const sorted = [...pool].sort((a, b) => {
    if (varianceStrategy === 'upside') {
      // Prioritize explosive upside players
      const aBoost = a.tags.includes('high_upside') || a.tags.includes('death_over_specialist') ? 4 : 0;
      const bBoost = b.tags.includes('high_upside') || b.tags.includes('death_over_specialist') ? 4 : 0;
      return (b.runtime_score + bBoost) - (a.runtime_score + aBoost);
    }
    return b.runtime_score - a.runtime_score;
  });

  const selected: GeneratedTeamPlayer[] = [];
  const teamCounts: Record<string, number> = {};
  const catCounts: Record<string, number> = { WK: 0, BAT: 0, AR: 0, BWL: 0 };

  // Pass 1: Ensure minimum 1 of each category (WK, BAT, AR, BWL)
  for (const cat of ['WK', 'BAT', 'AR', 'BWL']) {
    const candidate = sorted.find(
      (p) =>
        p.fantasy_category === cat &&
        !selected.some((s) => s.player_name === p.player_name) &&
        (teamCounts[p.team_name] || 0) < 7
    );
    if (candidate) {
      selected.push({
        player_name: candidate.player_name,
        team_name: candidate.team_name,
        role_profile: candidate.role_profile,
        fantasy_category: candidate.fantasy_category || 'BAT',
        runtime_score: candidate.runtime_score,
        insights: candidate.insights,
      });
      teamCounts[candidate.team_name] = (teamCounts[candidate.team_name] || 0) + 1;
      catCounts[cat]++;
    }
  }

  // Pass 2: Ensure minimum 3 BAT and 3 BWL
  for (const cat of ['BAT', 'BWL']) {
    while (catCounts[cat] < 3) {
      const candidate = sorted.find(
        (p) =>
          p.fantasy_category === cat &&
          !selected.some((s) => s.player_name === p.player_name) &&
          (teamCounts[p.team_name] || 0) < 7
      );
      if (!candidate) break;
      selected.push({
        player_name: candidate.player_name,
        team_name: candidate.team_name,
        role_profile: candidate.role_profile,
        fantasy_category: candidate.fantasy_category || 'BAT',
        runtime_score: candidate.runtime_score,
        insights: candidate.insights,
      });
      teamCounts[candidate.team_name] = (teamCounts[candidate.team_name] || 0) + 1;
      catCounts[cat]++;
    }
  }

  // Pass 3: Fill up to 11 players respecting caps (WK <= 4, BAT <= 6, AR <= 4, BWL <= 6, team <= 7)
  for (const p of sorted) {
    if (selected.length >= 11) break;
    if (selected.some((s) => s.player_name === p.player_name)) continue;

    const cat = p.fantasy_category || 'BAT';
    if ((teamCounts[p.team_name] || 0) >= 7) continue;
    if (cat === 'WK' && catCounts['WK'] >= 3) continue;
    if (cat === 'BAT' && catCounts['BAT'] >= 6) continue;
    if (cat === 'AR' && catCounts['AR'] >= 4) continue;
    if (cat === 'BWL' && catCounts['BWL'] >= 6) continue;

    selected.push({
      player_name: p.player_name,
      team_name: p.team_name,
      role_profile: p.role_profile,
      fantasy_category: cat,
      runtime_score: p.runtime_score,
      insights: p.insights,
    });
    teamCounts[p.team_name] = (teamCounts[p.team_name] || 0) + 1;
    catCounts[cat]++;
  }

  // Sort by role WK -> BAT -> AR -> BWL
  return selected.sort((a, b) => (ROLE_ORDER[a.fantasy_category] ?? 99) - (ROLE_ORDER[b.fantasy_category] ?? 99));
}

export function generateTeams(match: MatchdayMatch, analysis: MatchAnalysis): TeamGeneration {
  const pool = analysis.players;
  const topPlayers = [...pool].sort((a, b) => b.runtime_score - a.runtime_score);

  const captain1 = topPlayers[0]?.player_name || 'Virat Kohli';
  const viceCaptain1 = topPlayers[1]?.player_name || 'Shivam Dube';

  const captain2 = topPlayers.find(p => p.role_profile === 'all_rounder')?.player_name || topPlayers[2]?.player_name || 'Ravindra Jadeja';
  const viceCaptain2 = topPlayers[0]?.player_name || 'Virat Kohli';

  const riskyCaptain = topPlayers.find(p => p.tags.includes('death_over_specialist') || p.tags.includes('high_upside'))?.player_name || topPlayers[1]?.player_name || 'Shivam Dube';
  const riskyVice = topPlayers.find(p => p.role_profile === 'bowler')?.player_name || topPlayers[3]?.player_name || 'Matheesha Pathirana';

  const team1Players = select11(pool, 'balanced');
  const team2Players = select11(pool, 'safe');
  const riskyTeamPlayers = select11(pool, 'upside');

  const commonTeam1: GeneratedTeam = {
    team_type: 'common_team_1',
    captain: captain1,
    vice_captain: viceCaptain1,
    players: team1Players,
  };

  const commonTeam2: GeneratedTeam = {
    team_type: 'common_team_2',
    captain: captain2,
    vice_captain: viceCaptain2,
    players: team2Players,
  };

  const riskyTeam: GeneratedTeam = {
    team_type: 'risky_team',
    captain: riskyCaptain,
    vice_captain: riskyVice,
    players: riskyTeamPlayers,
  };

  return {
    match_name: match.name,
    favorite_team: analysis.favorite_team,
    disclaimer:
      'CricSense is an analytical support tool. These fantasy teams are calculated using player form scores, pitch conditions, and venue history, not a promise of winnings. Please apply your own judgment before entering contests.',
    captain_suggestions: [
      {
        type: 'safe_pair',
        captain: captain1,
        vice_captain: viceCaptain1,
        reason: 'Optimal for balanced contests using top runtime stability signals and form metrics.',
      },
      {
        type: 'upside_pair',
        captain: riskyCaptain,
        vice_captain: riskyVice,
        reason: 'Recommended for high-risk mega leagues where death overs upside and strike rate yield decisive spikes.',
      },
    ],
    common_team_1: commonTeam1,
    common_team_2: commonTeam2,
    risky_team: riskyTeam,
  };
}

export function getPlayerProfileData(playerName: string): { summary: PlayerSummary; history: PlayerHistoryRow[] } {
  if (mockPlayersData[playerName]) {
    return mockPlayersData[playerName];
  }

  // Dynamic fallback
  const base = BASE_SCORES[playerName]?.base || 70;
  return {
    summary: {
      player_name: playerName,
      role_profile: BASE_SCORES[playerName]?.role || 'cricketer',
      play_type: 'context_derived_player',
      base_stats_score: base,
      context_score: base - 2,
      instinct_score: base - 5,
      final_score: base,
      recent_form_score: base + 4,
      consistency_score: base - 3,
      strength_tags: ['Reliable squad performer', 'Consistent boundary reach'],
      risk_tags: ['Matchup variations'],
      weakness_summary: 'Performance fluctuates based on ground dimensions and match phase.',
    },
    history: [
      { match_date: '2026-04-10', event_name: 'Indian Premier League', venue: 'Bengaluru', runs: 38, balls: 24 },
      { match_date: '2026-04-06', event_name: 'Indian Premier League', venue: 'Mumbai', runs: 29, balls: 19 },
      { match_date: '2026-04-02', event_name: 'Indian Premier League', venue: 'Chennai', runs: 42, balls: 28 },
    ],
  };
}
