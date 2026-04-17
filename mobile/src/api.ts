import { mockAnalysis, mockHistory, mockMatchday, mockPlayer, mockTeams } from './mockData';
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

export async function getMatchDetail(matchId: string): Promise<MatchdayMatch> {
  return requestJson<MatchdayMatch>(`/matchday/ipl/matches/${encodeURIComponent(matchId)}?include_squads=true`);
}

function buildWeatherText(input: MatchConditionsInput) {
  const parts = [`rain ${input.rainPercent || '0'}%`];
  if (input.dew) {
    parts.push('dew likely');
  }
  return parts.join(', ');
}

function buildAnalysisPayload(match: MatchdayMatch, conditions?: MatchConditionsInput) {
  return {
    match_name: match.name,
    competition: 'Indian Premier League',
    venue: match.venue,
    weather: conditions ? buildWeatherText(conditions) : '',
    pitch_report: conditions?.pitchReport ?? '',
    toss_winner: conditions?.tossWinner || null,
    toss_decision: conditions?.tossWinner ? conditions.tossDecision : null,
    teams: (match.squads || []).map((team) => ({
      name: team.teamName || team.shortname || '',
      squad: (team.players || []).map((player) => player.name).filter(Boolean),
    })),
  };
}

export async function getMatchAnalysis(match: MatchdayMatch, conditions?: MatchConditionsInput): Promise<MatchAnalysis> {
  try {
    return await requestJson<MatchAnalysis>('/runtime/match-analysis', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(buildAnalysisPayload(match, conditions)),
    });
  } catch {
    return mockAnalysis;
  }
}

export async function getFantasyTeams(match: MatchdayMatch, conditions?: MatchConditionsInput): Promise<TeamGeneration> {
  try {
    return await requestJson<TeamGeneration>('/runtime/team-generation', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(buildAnalysisPayload(match, conditions)),
    });
  } catch {
    return mockTeams;
  }
}

export async function getPlayerProfile(playerName: string): Promise<PlayerSummary> {
  try {
    return await requestJson<PlayerSummary>(`/players/${encodeURIComponent(playerName)}`);
  } catch {
    return { ...mockPlayer, player_name: playerName };
  }
}

export async function getPlayerHistory(playerName: string): Promise<PlayerHistoryRow[]> {
  try {
    return await requestJson<PlayerHistoryRow[]>(`/players/${encodeURIComponent(playerName)}/history?limit=8`);
  } catch {
    return mockHistory;
  }
}
