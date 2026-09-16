import React, { useEffect, useState } from 'react';
import { Award, CheckCircle, ShieldCheck, Trophy, Sparkles } from 'lucide-react';
import { CompletedMatchInsight } from '../types';
import { getCompletedInsights } from '../services/api';

interface CompletedMatchScreenProps {
  matchId: string;
  onBack: () => void;
}

export const CompletedMatchScreen: React.FC<CompletedMatchScreenProps> = ({
  matchId,
  onBack,
}) => {
  const [data, setData] = useState<CompletedMatchInsight | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        const payload = await getCompletedInsights(matchId);
        setData(payload);
      } catch {
        alert('Failed to load insights for this match.');
      } finally {
        setLoading(false);
      }
    }
    void load();
  }, [matchId]);

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center py-20 space-y-3">
        <div className="w-8 h-8 border-3 border-emerald-800 border-t-transparent rounded-full animate-spin" />
        <p className="text-sm font-medium text-slate-500">Loading IPL Fantasy 11 accuracy maps...</p>
      </div>
    );
  }

  if (!data) return null;

  const formatTitle = (id: string) => {
    if (id === 'risky_team') return 'Gamble Team (Differential):';
    if (id === 'common_team_1') return 'Common Team 1 (Optimal Stability):';
    if (id === 'common_team_2') return 'Common Team 2 (Alternative):';
    return id.split('_').map((word) => word.charAt(0).toUpperCase() + word.slice(1)).join(' ') + ':';
  };

  return (
    <div className="space-y-6 pb-16">
      {/* Hero Header */}
      <div className="bg-gradient-to-r from-emerald-950 to-emerald-850 text-white rounded-2xl p-5 sm:p-6 shadow-sm">
        <div className="flex items-center gap-2 mb-1.5 text-emerald-300 text-xs font-bold uppercase tracking-wider">
          <Trophy className="w-4 h-4" />
          <span>Post-Match Validation</span>
        </div>
        <h2 className="text-2xl font-extrabold tracking-tight">Accuracy Report</h2>
        <p className="text-emerald-100 text-sm mt-1.5 leading-relaxed">
          Comparing our pre-match algorithm generation with the absolute actual outcome and Dream11 / IPL Fantasy points.
        </p>
      </div>

      {data.status === 'pending' ? (
        <div className="bg-white border border-slate-200 rounded-2xl p-6 text-center space-y-2">
          <h3 className="text-base font-bold text-slate-900">Data Pending</h3>
          <p className="text-sm text-slate-500">
            {data.message || 'Scorecard data is being synchronized. Please check back shortly.'}
          </p>
        </div>
      ) : (
        <>
          {/* Actual Perfect IPL Fantasy 11 */}
          <div className="bg-white border border-slate-200 rounded-2xl p-5 shadow-xs space-y-3">
            <div>
              <h3 className="text-base font-extrabold text-slate-900 flex items-center gap-2">
                <Sparkles className="w-4 h-4 text-emerald-800" />
                <span>Actual IPL Fantasy 11 (Perfect Team)</span>
              </h3>
              <p className="text-xs text-slate-500 mt-0.5">
                Top 11 players by actual fantasy points scored in this completed match.
              </p>
            </div>

            <div className="divide-y divide-slate-100">
              {data.perfect_11?.map((p, i) => (
                <div key={i} className="py-2.5 flex items-center justify-between text-sm">
                  <div className="flex items-center gap-2.5">
                    <span className="w-6 h-6 rounded-full bg-slate-100 text-slate-600 font-bold text-xs flex items-center justify-center">
                      {i + 1}
                    </span>
                    <span className="font-bold text-slate-900">{p.player_name}</span>
                    {p.role && <span className="text-xs text-slate-500 font-medium">({p.role})</span>}
                  </div>
                  <span className="font-black text-emerald-900 bg-emerald-50 border border-emerald-200 px-2.5 py-0.5 rounded-md text-xs">
                    {p.actual_fantasy_points} pts
                  </span>
                </div>
              ))}
            </div>
          </div>

          <h3 className="text-lg font-black text-slate-900 pt-2 flex items-center gap-2">
            <ShieldCheck className="w-5 h-5 text-emerald-800" />
            <span>CricSense 11 Predictions vs Actuals</span>
          </h3>

          {/* Predicted Teams comparison */}
          {['common_team_1', 'common_team_2', 'risky_team'].map((teamKey) => {
            const teamData = data.predicted_teams?.[teamKey as keyof typeof data.predicted_teams];
            if (!teamData) return null;

            return (
              <div
                key={teamKey}
                className="bg-white border border-slate-200 rounded-2xl p-5 shadow-xs space-y-4"
              >
                <div className="flex items-center justify-between pb-2 border-b border-slate-100">
                  <h4 className="text-base font-extrabold text-slate-900">{formatTitle(teamKey)}</h4>
                </div>

                <div className="grid grid-cols-2 gap-3 bg-slate-50 p-3.5 rounded-xl border border-slate-100">
                  <div>
                    <span className="text-[11px] font-bold uppercase tracking-wider text-slate-500 block">
                      IPL Fantasy 11 Match
                    </span>
                    <span className="text-xl font-black text-emerald-800 mt-0.5 block">
                      {teamData.intersection_count} / 11
                    </span>
                  </div>
                  <div className="text-right">
                    <span className="text-[11px] font-bold uppercase tracking-wider text-slate-500 block">
                      Total Match Score
                    </span>
                    <span className="text-xl font-black text-slate-900 mt-0.5 block">
                      {teamData.total_points} pts
                    </span>
                  </div>
                </div>

                <div className="divide-y divide-slate-100">
                  {teamData.players.map((p, i) => {
                    const matched = data.perfect_11?.some(
                      (perf) => perf.player_name.toLowerCase() === p.player_name.toLowerCase()
                    );
                    const isCaptain = p.player_name === teamData.captain;
                    const isViceCaptain = p.player_name === teamData.vice_captain;

                    return (
                      <div key={i} className="py-2.5 flex items-center justify-between text-sm">
                        <div className="flex items-center gap-2">
                          <span
                            className={`font-bold ${
                              matched ? 'text-emerald-800 font-extrabold' : 'text-slate-700'
                            }`}
                          >
                            {p.player_name}
                          </span>
                          {isCaptain && (
                            <span className="text-[10px] font-bold bg-emerald-800 text-white px-1.5 py-0.2 rounded">
                              C
                            </span>
                          )}
                          {isViceCaptain && (
                            <span className="text-[10px] font-bold bg-emerald-700 text-white px-1.5 py-0.2 rounded">
                              VC
                            </span>
                          )}
                        </div>
                        {matched ? (
                          <span className="flex items-center gap-1 text-xs font-bold text-emerald-800 bg-emerald-50 border border-emerald-200 px-2 py-0.5 rounded-md">
                            <CheckCircle className="w-3.5 h-3.5" />
                            <span>In IPL Fantasy 11 ✓</span>
                          </span>
                        ) : (
                          <span className="text-xs text-slate-400 font-medium">Outside Top 11</span>
                        )}
                      </div>
                    );
                  })}
                </div>
              </div>
            );
          })}
        </>
      )}
    </div>
  );
};
