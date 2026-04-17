export type Screen =
  | { name: 'home' }
  | { name: 'match'; matchId: string }
  | { name: 'teams'; matchId: string }
  | { name: 'player'; playerName: string }
  | { name: 'settings' };

export type MatchdayWeather = {
  city?: string;
  temperature_c?: number | null;
  precipitation_probability?: number | null;
  dew_point_c?: number | null;
  wind_speed_kmh?: number | null;
  summary_text?: string;
};

export type MatchSquadTeam = {
  teamName?: string;
  shortname?: string;
  players?: Array<{
    id?: string;
    name?: string;
    role?: string;
    battingStyle?: string;
    bowlingStyle?: string;
    country?: string;
  }>;
};

export type MatchdayMatch = {
  id: string;
  name: string;
  status?: string;
  venue?: string;
  date?: string;
  date_time_gmt?: string;
  teams: string[];
  weather?: MatchdayWeather | null;
  squads?: MatchSquadTeam[] | null;
  squad_source?: string;
};

export type MatchdayResponse = {
  date: string;
  competition: string;
  matches: MatchdayMatch[];
};

export type MatchConditionsInput = {
  dew: boolean;
  rainPercent: string;
  pitchReport: string;
  tossWinner: string;
  tossDecision: 'bat' | 'bowl';
};

export type AnalyzedPlayer = {
  player_name: string;
  team_name: string;
  role_profile: string;
  play_type?: string;
  fantasy_category?: string;
  runtime_score: number;
  upside_score?: number;
  tags: string[];
  insights: string[];
  is_overseas?: boolean;
};

export type MatchAnalysis = {
  match_name: string;
  favorite_team?: string | null;
  conditions: {
    tags: string[];
  };
  players: AnalyzedPlayer[];
};

export type GeneratedTeam = {
  team_type: string;
  captain?: string | null;
  vice_captain?: string | null;
  players: Array<{
    player_name: string;
    team_name: string;
    role_profile: string;
    fantasy_category: string;
    runtime_score: number;
    insights: string[];
  }>;
};

export type TeamGeneration = {
  match_name: string;
  favorite_team?: string | null;
  disclaimer?: string;
  captain_suggestions?: Array<{
    type: string;
    captain: string;
    vice_captain: string;
    reason: string;
  }>;
  common_team_1: GeneratedTeam;
  common_team_2: GeneratedTeam;
  risky_team: GeneratedTeam;
};

export type PlayerSummary = {
  player_name: string;
  role_profile?: string;
  play_type?: string;
  base_stats_score?: number;
  context_score?: number;
  instinct_score?: number;
  final_score?: number;
  recent_form_score?: number;
  consistency_score?: number;
  strength_tags?: string[];
  risk_tags?: string[];
  tags_json?: string[];
  weakness_summary?: string;
};

export type PlayerHistoryRow = {
  match_date?: string | null;
  event_name?: string | null;
  venue?: string | null;
  runs?: number | null;
  balls?: number | null;
  wickets?: number | null;
  runs_conceded?: number | null;
};
