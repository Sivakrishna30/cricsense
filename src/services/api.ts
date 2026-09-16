import {
  CompletedMatchInsight,
  MatchAnalysis,
  MatchConditionsInput,
  MatchdayMatch,
  MatchdayResponse,
  PlayerHistoryRow,
  PlayerSummary,
  TeamGeneration,
  VenueStats,
} from '../types';
import {
  mockMatches,
  mockCompletedMatches,
  mockVenueStats,
  mockCompletedInsights,
} from '../data/mockData';
import {
  analyzeMatch,
  generateTeams,
  getPlayerProfileData,
} from './analyticsEngine';

export async function getTodayMatches(): Promise<MatchdayResponse> {
  // Simulate quick asynchronous retrieval
  await new Promise((resolve) => setTimeout(resolve, 60));
  const localDate = new Date().toISOString().slice(0, 10);
  return {
    date: localDate,
    competition: 'Indian Premier League 2026',
    matches: mockMatches,
  };
}

export async function getCompletedMatches(): Promise<MatchdayResponse> {
  await new Promise((resolve) => setTimeout(resolve, 50));
  return {
    date: new Date().toISOString().slice(0, 10),
    competition: 'Indian Premier League 2026',
    matches: mockCompletedMatches,
  };
}

export async function getMatchDetail(matchId: string): Promise<MatchdayMatch> {
  await new Promise((resolve) => setTimeout(resolve, 50));
  const found = mockMatches.find((m) => m.id === matchId) || mockCompletedMatches.find((m) => m.id === matchId);
  if (!found) {
    throw new Error(`Match not found: ${matchId}`);
  }
  return found;
}

export async function getMatchAnalysis(
  match: MatchdayMatch,
  conditions?: MatchConditionsInput
): Promise<MatchAnalysis> {
  await new Promise((resolve) => setTimeout(resolve, 80));
  return analyzeMatch(match, conditions);
}

export async function getFantasyTeams(
  match: MatchdayMatch,
  conditions?: MatchConditionsInput
): Promise<TeamGeneration> {
  await new Promise((resolve) => setTimeout(resolve, 100));
  const analysis = analyzeMatch(match, conditions);
  return generateTeams(match, analysis);
}

export async function getPlayerProfile(playerName: string): Promise<PlayerSummary> {
  await new Promise((resolve) => setTimeout(resolve, 40));
  return getPlayerProfileData(playerName).summary;
}

export async function getPlayerHistory(playerName: string): Promise<PlayerHistoryRow[]> {
  await new Promise((resolve) => setTimeout(resolve, 40));
  return getPlayerProfileData(playerName).history;
}

export async function getVenueStats(venue: string): Promise<VenueStats | null> {
  await new Promise((resolve) => setTimeout(resolve, 30));
  return mockVenueStats[venue] || null;
}

export async function getCompletedInsights(matchId: string): Promise<CompletedMatchInsight> {
  await new Promise((resolve) => setTimeout(resolve, 60));
  const data = mockCompletedInsights[matchId];
  if (data) {
    return data;
  }
  return {
    match_id: matchId,
    status: 'pending',
    message: 'Data is being synced from official match scorecard. Check back shortly.',
    perfect_11: [],
    predicted_teams: undefined,
  };
}
