import React, { useEffect, useMemo, useState } from 'react';
import { Header } from './components/Header';
import { HomeScreen } from './components/HomeScreen';
import { MatchScreen } from './components/MatchScreen';
import { TeamsScreen } from './components/TeamsScreen';
import { PlayerScreen } from './components/PlayerScreen';
import { CompletedMatchScreen } from './components/CompletedMatchScreen';
import { SettingsScreen } from './components/SettingsScreen';
import {
  getCompletedMatches,
  getFantasyTeams,
  getMatchAnalysis,
  getMatchDetail,
  getPlayerHistory,
  getPlayerProfile,
  getTodayMatches,
} from './services/api';
import {
  MatchAnalysis,
  MatchConditionsInput,
  MatchdayMatch,
  MatchdayResponse,
  PlayerHistoryRow,
  PlayerSummary,
  Screen,
  TeamGeneration,
} from './types';

export default function App() {
  const [screen, setScreen] = useState<Screen>({ name: 'home' });
  const [matchday, setMatchday] = useState<MatchdayResponse | null>(null);
  const [completedMatches, setCompletedMatches] = useState<MatchdayResponse | null>(null);
  const [loadingHome, setLoadingHome] = useState(true);
  const [homeError, setHomeError] = useState<string | null>(null);
  const [selectedMatch, setSelectedMatch] = useState<MatchdayMatch | null>(null);
  const [analysis, setAnalysis] = useState<MatchAnalysis | null>(null);
  const [teams, setTeams] = useState<TeamGeneration | null>(null);
  const [playerProfile, setPlayerProfile] = useState<PlayerSummary | null>(null);
  const [playerHistory, setPlayerHistory] = useState<PlayerHistoryRow[]>([]);
  const [busy, setBusy] = useState(false);
  const [conditions, setConditions] = useState<MatchConditionsInput>({
    dew: false,
    pitchSurface: '',
    tossBatting: '',
  });

  useEffect(() => {
    void loadHome();
  }, []);

  async function loadHome() {
    setLoadingHome(true);
    setHomeError(null);
    try {
      const [payload, completed] = await Promise.all([
        getTodayMatches(),
        getCompletedMatches(),
      ]);
      setMatchday(payload);
      setCompletedMatches(completed);
    } catch (error) {
      setMatchday(null);
      setCompletedMatches(null);
      setHomeError('Unable to load match lists. Please retry.');
    } finally {
      setLoadingHome(false);
    }
  }

  async function openMatch(matchId: string) {
    setBusy(true);
    setScreen({ name: 'match', matchId });
    try {
      const detail = await getMatchDetail(matchId);
      setSelectedMatch(detail);
      const runtime = await getMatchAnalysis(detail, conditions);
      setAnalysis(runtime);
    } catch {
      alert('Failed to load match or analysis.');
    } finally {
      setBusy(false);
    }
  }

  async function refreshAnalysis() {
    if (!selectedMatch) return;
    setBusy(true);
    try {
      const updated = await getMatchAnalysis(selectedMatch, conditions);
      setAnalysis(updated);
    } catch {
      alert('Could not refresh analysis with new inputs.');
    } finally {
      setBusy(false);
    }
  }

  async function openTeams(matchId: string) {
    setScreen({ name: 'teams', matchId });
    const detail = selectedMatch && selectedMatch.id === matchId ? selectedMatch : await getMatchDetail(matchId);
    if (!selectedMatch || selectedMatch.id !== matchId) {
      setSelectedMatch(detail);
    }
    setBusy(true);
    try {
      const teamsData = await getFantasyTeams(detail, conditions);
      setTeams(teamsData);
    } catch {
      alert('Could not load fantasy teams.');
    } finally {
      setBusy(false);
    }
  }

  async function openPlayer(playerName: string, returnTo?: Screen) {
    setBusy(true);
    setScreen({ name: 'player', playerName, returnTo });
    try {
      const [profile, history] = await Promise.all([
        getPlayerProfile(playerName),
        getPlayerHistory(playerName),
      ]);
      setPlayerProfile(profile);
      setPlayerHistory(history);
    } catch {
      alert(`Could not load details for ${playerName}.`);
    } finally {
      setBusy(false);
    }
  }

  const headerTitle = useMemo(() => {
    if (screen.name === 'match') return selectedMatch?.name || 'Match Details';
    if (screen.name === 'teams') return 'Fantasy Teams';
    if (screen.name === 'player') return playerProfile?.player_name || screen.playerName;
    if (screen.name === 'completed-match') return 'Accuracy Report';
    if (screen.name === 'settings') return 'Settings & About';
    return undefined;
  }, [screen, selectedMatch, playerProfile]);

  const handleBack = useMemo(() => {
    if (screen.name === 'home') return undefined;
    if (screen.name === 'match') return () => setScreen({ name: 'home' });
    if (screen.name === 'teams') return () => setScreen({ name: 'match', matchId: screen.matchId });
    if (screen.name === 'player') return () => setScreen(screen.returnTo || { name: 'home' });
    if (screen.name === 'completed-match') return () => setScreen({ name: 'home' });
    if (screen.name === 'settings') return () => setScreen({ name: 'home' });
    return undefined;
  }, [screen]);

  return (
    <div className="min-h-screen bg-slate-100 flex flex-col items-center">
      {/* Container simulating high-precision mobile/tablet app frame */}
      <div className="w-full max-w-2xl min-h-screen bg-slate-50 border-x border-slate-200/80 flex flex-col shadow-xs">
        <Header
          title={headerTitle}
          onBack={handleBack}
          onOpenSettings={() => setScreen({ name: 'settings' })}
          showSettings={screen.name === 'home'}
        />

        <main className="flex-1 p-4 sm:p-6">
          {screen.name === 'home' && (
            <HomeScreen
              matchday={matchday}
              completedMatches={completedMatches}
              loading={loadingHome}
              error={homeError}
              onOpenMatch={(id) => void openMatch(id)}
              onOpenCompletedMatch={(id) => setScreen({ name: 'completed-match', matchId: id })}
              onRetry={() => void loadHome()}
            />
          )}

          {screen.name === 'match' && (
            <MatchScreen
              match={selectedMatch}
              analysis={analysis}
              conditions={conditions}
              busy={busy}
              onConditionsChange={setConditions}
              onRefreshAnalysis={() => void refreshAnalysis()}
              onFantasyTeams={() => void openTeams(screen.matchId)}
              onPlayerPress={(name) => void openPlayer(name, { name: 'match', matchId: screen.matchId })}
            />
          )}

          {screen.name === 'teams' && (
            <TeamsScreen
              teams={teams}
              busy={busy}
              onPlayerPress={(name) => void openPlayer(name, { name: 'teams', matchId: screen.matchId })}
            />
          )}

          {screen.name === 'player' && (
            <PlayerScreen
              profile={playerProfile}
              history={playerHistory}
              busy={busy}
            />
          )}

          {screen.name === 'completed-match' && (
            <CompletedMatchScreen
              matchId={screen.matchId}
              onBack={() => setScreen({ name: 'home' })}
            />
          )}

          {screen.name === 'settings' && (
            <SettingsScreen onBack={() => setScreen({ name: 'home' })} />
          )}
        </main>
      </div>
    </div>
  );
}
