import React, { useEffect, useState } from 'react';
import { View, Text, StyleSheet, ScrollView, ActivityIndicator, Pressable, SafeAreaView } from 'react-native';
import { MatchdayMatch, AnalyzedPlayer } from './types';

const API_BASE_URL = 'http://192.168.0.4:8000';

async function requestJson<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, init);
  if (!response.ok) {
    throw new Error(`Request failed: ${response.status}`);
  }
  return response.json() as Promise<T>;
}

export function CompletedMatchScreen({ matchId, onBack }: { matchId: string; onBack: () => void }) {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        const payload = await requestJson(`/runtime/completed-insights?match_id=${encodeURIComponent(matchId)}`);
        setData(payload);
      } catch (err) {
        alert("Failed to load insights for this match.");
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [matchId]);

  if (loading) {
    return (
      <View style={styles.centerContainer}>
        <ActivityIndicator size="large" color="#166534" />
        <Text style={{ marginTop: 10, color: '#666' }}>Loading IPL Fantasy 11 accuracy maps...</Text>
      </View>
    );
  }

  if (!data) return null;

  return (
    <SafeAreaView style={{ flex: 1, backgroundColor: '#FAFAFA' }}>
      <View style={styles.header}>
        <Pressable onPress={onBack} style={styles.backButton}>
          <Text style={styles.heroTitle}>← Back</Text>
        </Pressable>
        <Text style={styles.heroTitle}>Accuracy Report</Text>
      </View>

      <ScrollView contentContainerStyle={styles.content}>
        <View style={styles.heroHeader}>
          <Text style={styles.heroText}>Comparing our pre-match algorithm generation with the absolute actual outcome of the match.</Text>
        </View>

        {data.status === 'pending' ? (
          <View style={styles.sectionCard}>
            <Text style={styles.sectionTitle}>Data Pending</Text>
            <Text style={styles.sectionText}>{data.message || 'Data not available for that match, check tomorrow.'}</Text>
          </View>
        ) : (
          <>
            <View style={styles.sectionCard}>
                <Text style={styles.sectionTitle}>IPL Fantasy 11</Text>
                <Text style={styles.sectionText}>Top 11 players by actual fantasy points in this match.</Text>
                {data.perfect_11?.map((p: any, i: number) => (
                    <View key={i} style={styles.rowItem}>
                        <Text style={styles.rowPrimary}>{p.player_name}</Text>
                        <Text style={styles.rowSecondary}>{p.actual_fantasy_points} pts</Text>
                    </View>
                ))}
            </View>

            <Text style={styles.heroTitle}>CricSense 11 Predictions</Text>

            {['common_team_1', 'common_team_2', 'risky_team'].map((teamKey) => {
               const teamData = data.predicted_teams?.[teamKey];
               if (!teamData) return null;

               const formatTitle = (id: string) => {
                 if (id === 'risky_team') return 'Gamble Team:';
                 return id.split('_').map(word => word.charAt(0).toUpperCase() + word.slice(1)).join(' ') + ':';
               };

               return (
                <View key={teamKey} style={styles.sectionCard}>
                    <Text style={styles.sectionTitle}>{formatTitle(teamKey)}</Text>
                    
                    <View style={{flexDirection: 'row', justifyContent: 'space-between', marginBottom: 15}}>
                        <View>
                            <Text style={styles.statLabel}>IPL Fantasy 11 match</Text>
                            <Text style={styles.statValueHighlight}>{teamData.intersection_count} / 11</Text>
                        </View>
                        <View style={{alignItems: 'flex-end'}}>
                            <Text style={styles.statLabel}>Total Match Score</Text>
                            <Text style={styles.statValue}>{teamData.total_points} pts</Text>
                        </View>
                    </View>

                    {teamData.players.map((p: any, i: number) => {
                        const matched = data.perfect_11.some((perf: any) => perf.player_name === p.player_name);
                        return (
                            <View key={i} style={styles.rowItem}>
                                <Text style={[styles.rowPrimary, matched && { color: '#166534' }]}>
                                    {p.player_name} {p.player_name === teamData.captain ? '(C)' : p.player_name === teamData.vice_captain ? '(VC)' : ''}
                                </Text>
                                <Text style={styles.rowSecondary}>{matched ? 'In IPL Fantasy 11 ✓' : ''}</Text>
                            </View>
                        );
                    })}
                </View>
               );
            })}
          </>
        )}
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  centerContainer: { flex: 1, alignItems: 'center', justifyContent: 'center' },
  header: { padding: 20, paddingTop: 60, flexDirection: 'row', alignItems: 'center', backgroundColor: '#FAFAFA' },
  backButton: { marginRight: 20 },
  heroHeader: { marginBottom: 25 },
  heroTitle: { fontSize: 28, fontWeight: '800', color: '#111', letterSpacing: -0.5 },
  heroText: { fontSize: 16, color: '#555', lineHeight: 24, marginTop: 4 },
  content: { padding: 20 },
  sectionCard: { backgroundColor: '#FFF', borderRadius: 16, padding: 20, marginBottom: 16, elevation: 1 },
  sectionTitle: { fontSize: 20, fontWeight: '700', color: '#111', marginBottom: 12 },
  sectionText: { fontSize: 15, color: '#555', marginBottom: 10 },
  rowItem: { flexDirection: 'row', justifyContent: 'space-between', paddingVertical: 10, borderBottomWidth: 1, borderBottomColor: '#EEE' },
  rowPrimary: { fontSize: 16, fontWeight: '600', color: '#222' },
  rowSecondary: { fontSize: 14, color: '#666' },
  statLabel: { fontSize: 12, color: '#888', textTransform: 'uppercase', fontWeight: 'bold' },
  statValue: { fontSize: 20, fontWeight: '800', color: '#111', marginTop: 4 },
  statValueHighlight: { fontSize: 20, fontWeight: '800', color: '#166534', marginTop: 4 },
});
