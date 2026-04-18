import { MatchAnalysis, MatchConditionsInput, MatchdayMatch, MatchdayResponse, PlayerHistoryRow, PlayerSummary, TeamGeneration } from './types';

const API_BASE_URL = 'http://192.168.0.4:8000';

async function requestJson<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, init);
  if (!response.ok) {
    throw new Error(`Request failed: ${response.status}`);
  }
  return response.json() as Promise<T>;
}

export async function getTodayMatches(): Promise<MatchdayResponse> {
  const localDate = new Date().toISOString().slice(0, 10);
  return requestJson<MatchdayResponse>(`/matchday/ipl/today?target_date=${localDate}`);
}

export async function getCompletedMatches(): Promise<MatchdayResponse> {
  return requestJson<MatchdayResponse>('/matchday/ipl/completed');
}

export async function getMatchDetail(matchId: string): Promise<MatchdayMatch> {
  return requestJson<MatchdayMatch>(`/matchday/ipl/matches/${encodeURIComponent(matchId)}?include_squads=true`);
}

function buildAnalysisPayload(match: MatchdayMatch, conditions?: MatchConditionsInput) {
  return {
    match_id: match.id,
    match_name: match.name,
    competition: 'Indian Premier League',
    venue: match.venue,
    dew: conditions?.dew || false,
    pitch_surface: conditions?.pitchSurface || '',
    toss_batting: conditions?.tossBatting || '',
    teams: (match.squads || []).map((team) => ({
      name: team.teamName || team.shortname || '',
      squad: (team.players || []).map((player) => player.name).filter(Boolean),
    })),
  };
}

export async function getMatchAnalysis(match: MatchdayMatch, conditions?: MatchConditionsInput): Promise<MatchAnalysis> {
  return await requestJson<MatchAnalysis>('/runtime/match-analysis', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(buildAnalysisPayload(match, conditions)),
  });
}

export async function getFantasyTeams(match: MatchdayMatch, conditions?: MatchConditionsInput): Promise<TeamGeneration> {
  return await requestJson<TeamGeneration>('/runtime/team-generation', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(buildAnalysisPayload(match, conditions)),
  });
}

export async function getPlayerProfile(playerName: string): Promise<PlayerSummary> {
  return await requestJson<PlayerSummary>(`/players/${encodeURIComponent(playerName)}`);
}

export async function getPlayerHistory(playerName: string): Promise<PlayerHistoryRow[]> {
  const data = await requestJson<PlayerHistoryRow[]>(`/players/${encodeURIComponent(playerName)}/history`);
  return Array.isArray(data) ? data : [];
}

export interface VenueStats {
  venue?: string;
  matches_sampled?: number;
  avg_first_innings?: number;
  avg_second_innings?: number;
  chasing_win_percent?: number;
}

export async function getVenueStats(venue: string): Promise<VenueStats | null> {
  try {
    const stats = await requestJson<VenueStats>(`/context/venue-stats?venue=${encodeURIComponent(venue)}`);
    return stats.venue ? stats : null;
  } catch {
    return null;
  }
}
