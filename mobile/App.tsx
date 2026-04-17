import { StatusBar } from 'expo-status-bar';
import { useEffect, useMemo, useState } from 'react';
import {
  ActivityIndicator,
  Pressable,
  SafeAreaView,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  View,
} from 'react-native';

import { getFantasyTeams, getMatchAnalysis, getMatchDetail, getPlayerHistory, getPlayerProfile, getTodayMatches } from './src/api';
import { colors } from './src/theme';
import {
  GeneratedTeam,
  MatchAnalysis,
  MatchConditionsInput,
  MatchdayMatch,
  MatchdayResponse,
  PlayerHistoryRow,
  PlayerSummary,
  Screen,
  TeamGeneration,
} from './src/types';

const disclaimer =
  'CricSense is an analytical support tool. These teams are based on available data and context, not a promise of winnings. Please apply your own judgment before entering contests.';

function scoreTone(score: number) {
  if (score >= 80) return { color: colors.success };
  if (score >= 65) return { color: colors.primary };
  return { color: colors.danger };
}

export default function App() {
  const [screen, setScreen] = useState<Screen>({ name: 'home' });
  const [matchday, setMatchday] = useState<MatchdayResponse | null>(null);
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
    rainPercent: '0',
    pitchReport: '',
    tossWinner: '',
    tossDecision: 'bowl',
  });

  useEffect(() => {
    void loadHome();
  }, []);

  async function loadHome() {
    setLoadingHome(true);
    setHomeError(null);
    try {
      const payload = await getTodayMatches();
      setMatchday(payload);
    } catch (error) {
      setMatchday(null);
      setHomeError('Unable to fetch today’s live match list. Make sure the backend is running and your phone is on the same Wi-Fi.');
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
    } finally {
      setBusy(false);
    }
  }

  async function refreshAnalysis() {
    if (!selectedMatch) return;
    setBusy(true);
    try {
      setAnalysis(await getMatchAnalysis(selectedMatch, conditions));
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
      setTeams(await getFantasyTeams(detail, conditions));
    } finally {
      setBusy(false);
    }
  }

  async function openPlayer(playerName: string) {
    setBusy(true);
    setScreen({ name: 'player', playerName });
    try {
      const [profile, history] = await Promise.all([getPlayerProfile(playerName), getPlayerHistory(playerName)]);
      setPlayerProfile(profile);
      setPlayerHistory(history);
    } finally {
      setBusy(false);
    }
  }

  const content = useMemo(() => {
    if (screen.name === 'settings') {
      return <SettingsScreen onBack={() => setScreen({ name: 'home' })} />;
    }
    if (screen.name === 'match') {
      return (
        <MatchScreen
          match={selectedMatch}
          analysis={analysis}
          conditions={conditions}
          busy={busy}
          onBack={() => setScreen({ name: 'home' })}
          onConditionsChange={setConditions}
          onRefreshAnalysis={() => void refreshAnalysis()}
          onFantasyTeams={() => void openTeams(screen.matchId)}
          onPlayerPress={(name) => void openPlayer(name)}
        />
      );
    }
    if (screen.name === 'teams') {
      return <TeamsScreen teams={teams} busy={busy} onBack={() => setScreen({ name: 'match', matchId: screen.matchId })} />;
    }
    if (screen.name === 'player') {
      return <PlayerScreen profile={playerProfile} history={playerHistory} busy={busy} onBack={() => setScreen({ name: 'home' })} />;
    }
    return (
        <HomeScreen
          matchday={matchday}
          loading={loadingHome}
          error={homeError}
          onOpenMatch={(id) => void openMatch(id)}
          onOpenSettings={() => setScreen({ name: 'settings' })}
          onRetry={() => void loadHome()}
        />
      );
  }, [analysis, busy, conditions, loadingHome, matchday, playerHistory, playerProfile, screen, selectedMatch, teams]);

  return (
    <SafeAreaView style={styles.safeArea}>
      <StatusBar style="dark" />
      {content}
    </SafeAreaView>
  );
}

function HomeScreen({
  matchday,
  loading,
  error,
  onOpenMatch,
  onOpenSettings,
  onRetry,
}: {
  matchday: MatchdayResponse | null;
  loading: boolean;
  error: string | null;
  onOpenMatch: (matchId: string) => void;
  onOpenSettings: () => void;
  onRetry: () => void;
}) {
  return (
    <ScrollView style={styles.screen} contentContainerStyle={styles.content}>
      <View style={styles.topBar}>
        <View>
          <View style={styles.brandRow}>
            <Text style={styles.brand}>CricSense</Text>
            <Text style={styles.mvpTag}>[mvp]</Text>
          </View>
          <Text style={styles.subtle}>Guest mode · IPL focus</Text>
        </View>
        <Pressable style={styles.settingsButton} onPress={onOpenSettings}>
          <Text style={styles.settingsText}>Settings</Text>
        </Pressable>
      </View>

      <View style={styles.heroHeader}>
        <Text style={styles.heroTitle}>Today&apos;s IPL matches</Text>
        <Text style={styles.heroText}>
          Open a match, add simple conditions like dew or rain chance if you checked them, and get clean analysis.
        </Text>
      </View>

      <AdSlot label="Free tier banner" />

      {loading ? (
        <ActivityIndicator size="large" color={colors.primary} />
      ) : error ? (
        <View style={styles.sectionCard}>
          <Text style={styles.sectionTitle}>Live match feed unavailable</Text>
          <Text style={styles.sectionText}>{error}</Text>
          <Pressable style={styles.secondaryButton} onPress={onRetry}>
            <Text style={styles.secondaryButtonText}>Retry</Text>
          </Pressable>
        </View>
      ) : (matchday?.matches || []).length === 0 ? (
        <View style={styles.sectionCard}>
          <Text style={styles.sectionTitle}>No IPL matches found</Text>
          <Text style={styles.sectionText}>No live IPL matches were returned for today’s device date.</Text>
        </View>
      ) : (
        (matchday?.matches || []).map((match) => (
          <Pressable key={match.id} style={styles.matchCard} onPress={() => onOpenMatch(match.id)}>
            <Text style={styles.matchTitle}>{match.teams.join(' vs ')}</Text>
            <Text style={styles.matchMeta}>{match.venue}</Text>
            <Text style={styles.matchMeta}>{match.status}</Text>
            <Text style={styles.weatherText}>Open match to add dew, rain %, and pitch note if needed.</Text>
          </Pressable>
        ))
      )}
    </ScrollView>
  );
}

function MatchScreen({
  match,
  analysis,
  conditions,
  busy,
  onBack,
  onConditionsChange,
  onRefreshAnalysis,
  onFantasyTeams,
  onPlayerPress,
}: {
  match: MatchdayMatch | null;
  analysis: MatchAnalysis | null;
  conditions: MatchConditionsInput;
  busy: boolean;
  onBack: () => void;
  onConditionsChange: (value: MatchConditionsInput) => void;
  onRefreshAnalysis: () => void;
  onFantasyTeams: () => void;
  onPlayerPress: (playerName: string) => void;
}) {
  const squadPlayers = analysis?.players || [];
  return (
    <ScrollView style={styles.screen} contentContainerStyle={styles.content}>
      <BackHeader title={match?.name || 'Match details'} onBack={onBack} />
      {busy && <ActivityIndicator size="small" color={colors.primary} />}

      <View style={styles.sectionCard}>
        <Text style={styles.sectionTitle}>{match?.venue}</Text>
        <Text style={styles.sectionText}>Skip auto weather for now. Add simple conditions before generating teams.</Text>
        <Text style={styles.sectionText}>Squad source: {match?.squad_source || 'pending'}</Text>
        {analysis?.favorite_team ? <Text style={styles.highlightText}>Model lean: {analysis.favorite_team}</Text> : null}
      </View>

      <View style={styles.sectionCard}>
        <Text style={styles.sectionTitle}>Optional match inputs</Text>
        <Text style={styles.sectionText}>These are optional. Users can quickly check Google and type simple match conditions.</Text>
        <View style={styles.toggleRow}>
          <Pressable
            style={[styles.choiceChip, conditions.dew ? styles.choiceChipActive : undefined]}
            onPress={() => onConditionsChange({ ...conditions, dew: true })}
          >
            <Text style={[styles.choiceChipText, conditions.dew ? styles.choiceChipTextActive : undefined]}>Dew yes</Text>
          </Pressable>
          <Pressable
            style={[styles.choiceChip, !conditions.dew ? styles.choiceChipActive : undefined]}
            onPress={() => onConditionsChange({ ...conditions, dew: false })}
          >
            <Text style={[styles.choiceChipText, !conditions.dew ? styles.choiceChipTextActive : undefined]}>Dew no</Text>
          </Pressable>
        </View>

        <Text style={styles.inputLabel}>Rain chance %</Text>
        <TextInput
          style={styles.textInput}
          keyboardType="number-pad"
          value={conditions.rainPercent}
          onChangeText={(value) => onConditionsChange({ ...conditions, rainPercent: value.replace(/[^0-9]/g, '').slice(0, 3) })}
          placeholder="0"
          placeholderTextColor={colors.muted}
        />

        <Text style={styles.inputLabel}>Pitch note</Text>
        <TextInput
          style={[styles.textInput, styles.textArea]}
          multiline
          value={conditions.pitchReport}
          onChangeText={(value) => onConditionsChange({ ...conditions, pitchReport: value })}
          placeholder="Flat batting pitch, spin if dry, or seam early"
          placeholderTextColor={colors.muted}
        />

        <Text style={styles.inputLabel}>Toss winner</Text>
        <View style={styles.toggleRow}>
          {(match?.teams || []).map((teamName) => {
            const active = conditions.tossWinner === teamName;
            return (
              <Pressable
                key={teamName}
                style={[styles.choiceChip, active ? styles.choiceChipActive : undefined]}
                onPress={() => onConditionsChange({ ...conditions, tossWinner: teamName })}
              >
                <Text style={[styles.choiceChipText, active ? styles.choiceChipTextActive : undefined]}>{teamName}</Text>
              </Pressable>
            );
          })}
        </View>

        <Text style={styles.inputLabel}>Toss decision</Text>
        <View style={styles.toggleRow}>
          <Pressable
            style={[styles.choiceChip, conditions.tossDecision === 'bat' ? styles.choiceChipActive : undefined]}
            onPress={() => onConditionsChange({ ...conditions, tossDecision: 'bat' })}
          >
            <Text style={[styles.choiceChipText, conditions.tossDecision === 'bat' ? styles.choiceChipTextActive : undefined]}>Bat first</Text>
          </Pressable>
          <Pressable
            style={[styles.choiceChip, conditions.tossDecision === 'bowl' ? styles.choiceChipActive : undefined]}
            onPress={() => onConditionsChange({ ...conditions, tossDecision: 'bowl' })}
          >
            <Text style={[styles.choiceChipText, conditions.tossDecision === 'bowl' ? styles.choiceChipTextActive : undefined]}>Bowl first</Text>
          </Pressable>
        </View>

        <Pressable style={styles.secondaryButton} onPress={onRefreshAnalysis}>
          <Text style={styles.secondaryButtonText}>Refresh analysis with inputs</Text>
        </Pressable>
      </View>

      <View style={styles.sectionCard}>
        <Text style={styles.sectionTitle}>Player pool</Text>
        <Text style={styles.sectionText}>Overall score and tags are shown from the current analysis layer.</Text>
        {squadPlayers.map((player) => {
          const tone = scoreTone(player.runtime_score);
          return (
            <Pressable key={`${player.team_name}-${player.player_name}`} style={styles.playerCard} onPress={() => onPlayerPress(player.player_name)}>
              <View style={styles.playerRow}>
                <View style={{ flex: 1 }}>
                  <Text style={styles.playerName}>{player.player_name}</Text>
                  <Text style={styles.playerMeta}>
                    {player.team_name} · {player.fantasy_category || player.role_profile}
                  </Text>
                </View>
                <View style={[styles.scorePill, { backgroundColor: tone.color }]}>
                  <Text style={styles.scoreText}>{Math.round(player.runtime_score)}</Text>
                </View>
              </View>
              <View style={styles.tagRow}>
                {(player.tags || []).slice(0, 3).map((tag) => (
                  <Tag key={tag} label={tag.replaceAll('_', ' ')} />
                ))}
              </View>
              {(player.insights || []).slice(0, 2).map((insight) => (
                <Text key={insight} style={styles.insightLine}>
                  {insight}
                </Text>
              ))}
            </Pressable>
          );
        })}
      </View>

      <Pressable style={styles.primaryButton} onPress={onFantasyTeams}>
        <Text style={styles.primaryButtonText}>Get fantasy teams</Text>
      </Pressable>
    </ScrollView>
  );
}

function TeamsScreen({
  teams,
  busy,
  onBack,
}: {
  teams: TeamGeneration | null;
  busy: boolean;
  onBack: () => void;
}) {
  const list: GeneratedTeam[] = teams ? [teams.common_team_1, teams.common_team_2, teams.risky_team] : [];
  return (
    <ScrollView style={styles.screen} contentContainerStyle={styles.content}>
      <BackHeader title="Fantasy teams" onBack={onBack} />
      {busy && <ActivityIndicator size="small" color={colors.primary} />}

      <View style={styles.disclaimerCard}>
        <Text style={styles.disclaimerTitle}>Professional note</Text>
        <Text style={styles.disclaimerText}>{teams?.disclaimer || disclaimer}</Text>
      </View>

      <View style={styles.sectionCard}>
        <Text style={styles.sectionTitle}>Captain suggestions</Text>
        <Text style={styles.sectionText}>Use these as guidance only. Feel free to trust your own instinct before finalizing captain and vice-captain.</Text>
        {(teams?.captain_suggestions || []).map((item) => (
          <View key={`${item.type}-${item.captain}-${item.vice_captain}`} style={styles.historyRow}>
            <View style={{ flex: 1 }}>
              <Text style={styles.teamPlayerName}>{item.captain} · {item.vice_captain}</Text>
              <Text style={styles.matchMeta}>{item.reason}</Text>
            </View>
            <Text style={styles.teamPlayerMeta}>{item.type.replaceAll('_', ' ')}</Text>
          </View>
        ))}
      </View>

      {list.map((team) => (
        <View key={team.team_type} style={styles.sectionCard}>
          <Text style={styles.sectionTitle}>{team.team_type.replaceAll('_', ' ')}</Text>
          <Text style={styles.sectionText}>Captain: {team.captain || 'TBD'}</Text>
          <Text style={styles.sectionText}>Vice-captain: {team.vice_captain || 'TBD'}</Text>
          {team.players.map((player) => (
            <View key={player.player_name} style={styles.teamPlayerRow}>
              <Text style={styles.teamPlayerName}>{player.player_name}</Text>
              <Text style={styles.teamPlayerMeta}>
                {player.fantasy_category} · {Math.round(player.runtime_score)}
              </Text>
            </View>
          ))}
        </View>
      ))}
      <AdSlot label="Inline ad slot" />
    </ScrollView>
  );
}

function PlayerScreen({
  profile,
  history,
  busy,
  onBack,
}: {
  profile: PlayerSummary | null;
  history: PlayerHistoryRow[];
  busy: boolean;
  onBack: () => void;
}) {
  return (
    <ScrollView style={styles.screen} contentContainerStyle={styles.content}>
      <BackHeader title={profile?.player_name || 'Player'} onBack={onBack} />
      {busy && <ActivityIndicator size="small" color={colors.primary} />}

      <View style={styles.sectionCard}>
        <Text style={styles.sectionTitle}>{profile?.role_profile || 'Player profile'}</Text>
        <Text style={styles.sectionText}>Play type: {profile?.play_type || 'Context derived'}</Text>
        <Text style={styles.sectionText}>Recent form: {Math.round(profile?.recent_form_score || 0)}</Text>
        <Text style={styles.sectionText}>Consistency: {Math.round(profile?.consistency_score || 0)}</Text>
        <Text style={styles.sectionText}>Stats layer: {Math.round(profile?.base_stats_score || 0)}</Text>
        <Text style={styles.sectionText}>Context layer: {Math.round(profile?.context_score || 0)}</Text>
        <Text style={styles.sectionText}>Instinct layer: {Math.round(profile?.instinct_score || 0)}</Text>
      </View>

      <View style={styles.sectionCard}>
        <Text style={styles.sectionTitle}>Strengths</Text>
        <View style={styles.tagRow}>
          {(profile?.strength_tags || profile?.tags_json || []).map((item) => (
            <Tag key={item} label={item} />
          ))}
        </View>
        <Text style={[styles.sectionTitle, { marginTop: 16 }]}>Risk / weakness</Text>
        <Text style={styles.sectionText}>{profile?.weakness_summary || 'No major weakness summary yet.'}</Text>
        <View style={styles.tagRow}>
          {(profile?.risk_tags || []).map((item) => (
            <Tag key={item} label={item} tone="warning" />
          ))}
        </View>
      </View>

      <View style={styles.sectionCard}>
        <Text style={styles.sectionTitle}>Recent matches</Text>
        {history.map((row, index) => (
          <View key={`${row.match_date}-${index}`} style={styles.historyRow}>
            <View style={{ flex: 1 }}>
              <Text style={styles.teamPlayerName}>{row.event_name || 'Match'}</Text>
              <Text style={styles.matchMeta}>{row.match_date} · {row.venue}</Text>
            </View>
            <Text style={styles.teamPlayerMeta}>
              {row.runs != null ? `${row.runs} (${row.balls || 0})` : `${row.wickets || 0} wkts`}
            </Text>
          </View>
        ))}
      </View>
      <AdSlot label="Free tier banner" />
    </ScrollView>
  );
}

function SettingsScreen({ onBack }: { onBack: () => void }) {
  return (
    <ScrollView style={styles.screen} contentContainerStyle={styles.content}>
      <BackHeader title="Settings" onBack={onBack} />
      <View style={styles.sectionCard}>
        <Text style={styles.sectionTitle}>Guest mode enabled</Text>
        <Text style={styles.sectionText}>Users can browse match analysis without login. Google sign-in can be added later for saved teams and account sync.</Text>
      </View>
      <View style={styles.sectionCard}>
        <Text style={styles.sectionTitle}>Plans</Text>
        <Text style={styles.sectionText}>Free now. Pro and Premium can unlock ad-free usage and deeper reports later.</Text>
      </View>
      <View style={styles.sectionCard}>
        <Text style={styles.sectionTitle}>Policy and Terms</Text>
        <Text style={styles.sectionText}>
          CricSense is an analytics app based on recent scores, performance context, and instinct signals. It does not guarantee winnings.
        </Text>
        <Text style={styles.sectionText}>
          Captain and vice-captain suggestions are guidance only. Users should apply their own judgment before entering contests.
        </Text>
      </View>
      <View style={styles.sectionCard}>
        <Text style={styles.sectionTitle}>Account actions</Text>
        <Text style={styles.sectionText}>Logout and delete-account flows are reserved for signed-in users. Password flow is not required for provider sign-in.</Text>
      </View>
    </ScrollView>
  );
}

function BackHeader({ title, onBack }: { title: string; onBack: () => void }) {
  return (
    <View style={styles.topBar}>
      <Pressable onPress={onBack}>
        <Text style={styles.backText}>Back</Text>
      </Pressable>
      <Text style={styles.pageTitle}>{title}</Text>
      <View style={{ width: 48 }} />
    </View>
  );
}

function Tag({ label, tone = 'default' }: { label: string; tone?: 'default' | 'warning' }) {
  return (
    <View style={[styles.tag, tone === 'warning' ? styles.tagWarning : styles.tagDefault]}>
      <Text style={styles.tagText}>{label}</Text>
    </View>
  );
}

function AdSlot({ label }: { label: string }) {
  return (
    <View style={styles.adSlot}>
      <Text style={styles.adText}>{label}</Text>
      <Text style={styles.adSubText}>Ad-free plans can be added later without blocking the main flow.</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  safeArea: {
    flex: 1,
    backgroundColor: colors.background,
  },
  screen: {
    flex: 1,
    backgroundColor: colors.background,
  },
  content: {
    padding: 18,
    gap: 16,
  },
  topBar: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 6,
  },
  brandRow: {
    flexDirection: 'row',
    alignItems: 'flex-end',
    gap: 6,
  },
  brand: {
    fontSize: 28,
    fontWeight: '700',
    color: colors.text,
  },
  mvpTag: {
    fontSize: 12,
    color: colors.primary,
    fontWeight: '700',
    marginBottom: 4,
  },
  pageTitle: {
    flex: 1,
    textAlign: 'center',
    fontSize: 18,
    fontWeight: '700',
    color: colors.text,
  },
  subtle: {
    color: colors.muted,
    marginTop: 4,
  },
  settingsButton: {
    backgroundColor: colors.surface,
    paddingHorizontal: 14,
    paddingVertical: 10,
    borderRadius: 16,
    borderWidth: 1,
    borderColor: colors.border,
  },
  settingsText: {
    color: colors.text,
    fontWeight: '600',
  },
  heroHeader: {
    backgroundColor: colors.primarySoft,
    borderRadius: 22,
    padding: 20,
    borderWidth: 1,
    borderColor: colors.border,
  },
  heroTitle: {
    fontSize: 24,
    fontWeight: '700',
    color: colors.text,
  },
  heroText: {
    color: colors.muted,
    marginTop: 8,
    lineHeight: 20,
  },
  matchCard: {
    backgroundColor: colors.surface,
    borderRadius: 20,
    padding: 18,
    borderWidth: 1,
    borderColor: colors.border,
    shadowColor: colors.shadow,
    shadowOpacity: 1,
    shadowRadius: 10,
    shadowOffset: { width: 0, height: 6 },
    elevation: 1,
  },
  matchTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: colors.text,
  },
  matchMeta: {
    color: colors.muted,
    marginTop: 4,
  },
  weatherText: {
    marginTop: 10,
    color: colors.text,
    fontSize: 13,
  },
  sectionCard: {
    backgroundColor: colors.surface,
    borderRadius: 20,
    padding: 18,
    borderWidth: 1,
    borderColor: colors.border,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: colors.text,
  },
  sectionText: {
    color: colors.muted,
    marginTop: 6,
    lineHeight: 20,
  },
  toggleRow: {
    flexDirection: 'row',
    gap: 10,
    marginTop: 12,
  },
  choiceChip: {
    backgroundColor: colors.surfaceAlt,
    borderRadius: 999,
    paddingHorizontal: 14,
    paddingVertical: 10,
  },
  choiceChipActive: {
    backgroundColor: colors.primary,
  },
  choiceChipText: {
    color: colors.text,
    fontWeight: '600',
  },
  choiceChipTextActive: {
    color: '#fff',
  },
  inputLabel: {
    marginTop: 14,
    color: colors.text,
    fontWeight: '600',
  },
  textInput: {
    marginTop: 8,
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: 14,
    backgroundColor: colors.surface,
    paddingHorizontal: 14,
    paddingVertical: 12,
    color: colors.text,
  },
  textArea: {
    minHeight: 84,
    textAlignVertical: 'top',
  },
  highlightText: {
    marginTop: 10,
    color: colors.primary,
    fontWeight: '700',
  },
  playerCard: {
    paddingVertical: 14,
    borderBottomWidth: 1,
    borderBottomColor: colors.border,
  },
  playerRow: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  playerName: {
    fontSize: 16,
    fontWeight: '700',
    color: colors.text,
  },
  playerMeta: {
    marginTop: 3,
    color: colors.muted,
  },
  scorePill: {
    minWidth: 48,
    borderRadius: 999,
    paddingHorizontal: 12,
    paddingVertical: 8,
    alignItems: 'center',
  },
  scoreText: {
    color: '#fff',
    fontWeight: '700',
  },
  tagRow: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
    marginTop: 10,
  },
  tag: {
    paddingHorizontal: 10,
    paddingVertical: 6,
    borderRadius: 999,
  },
  tagDefault: {
    backgroundColor: colors.accentSoft,
  },
  tagWarning: {
    backgroundColor: colors.primarySoft,
  },
  tagText: {
    color: colors.text,
    fontSize: 12,
    fontWeight: '600',
  },
  insightLine: {
    color: colors.muted,
    marginTop: 6,
    lineHeight: 18,
  },
  primaryButton: {
    backgroundColor: colors.primary,
    borderRadius: 18,
    paddingVertical: 16,
    alignItems: 'center',
  },
  primaryButtonText: {
    color: '#fff',
    fontWeight: '700',
    fontSize: 16,
  },
  secondaryButton: {
    marginTop: 14,
    backgroundColor: colors.accentSoft,
    borderRadius: 16,
    paddingVertical: 14,
    alignItems: 'center',
  },
  secondaryButtonText: {
    color: colors.text,
    fontWeight: '700',
  },
  disclaimerCard: {
    backgroundColor: colors.surfaceAlt,
    borderRadius: 20,
    padding: 18,
    borderWidth: 1,
    borderColor: colors.border,
  },
  disclaimerTitle: {
    fontSize: 16,
    fontWeight: '700',
    color: colors.text,
  },
  disclaimerText: {
    color: colors.muted,
    marginTop: 8,
    lineHeight: 20,
  },
  teamPlayerRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingVertical: 8,
    borderBottomWidth: 1,
    borderBottomColor: colors.border,
  },
  teamPlayerName: {
    color: colors.text,
    fontWeight: '600',
  },
  teamPlayerMeta: {
    color: colors.muted,
  },
  backText: {
    color: colors.primary,
    fontWeight: '700',
    width: 48,
  },
  historyRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingVertical: 10,
    borderBottomWidth: 1,
    borderBottomColor: colors.border,
  },
  adSlot: {
    backgroundColor: colors.surface,
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: 20,
    padding: 16,
    alignItems: 'center',
  },
  adText: {
    color: colors.primary,
    fontWeight: '700',
  },
  adSubText: {
    color: colors.muted,
    marginTop: 6,
    textAlign: 'center',
    lineHeight: 18,
  },
});


