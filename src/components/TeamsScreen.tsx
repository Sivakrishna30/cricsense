import React from 'react';
import { AlertCircle, Award, ShieldCheck, UserCheck, Info } from 'lucide-react';
import { GeneratedTeam, TeamGeneration } from '../types';

interface TeamsScreenProps {
  teams: TeamGeneration | null;
  busy: boolean;
  onPlayerPress: (playerName: string) => void;
}

const TEAM_THEMES: Record<string, { bg: string; text: string; border: string }> = {
  'Chennai Super Kings': { bg: 'bg-yellow-50', text: 'text-yellow-900', border: 'border-yellow-200' },
  'Mumbai Indians': { bg: 'bg-blue-50', text: 'text-blue-900', border: 'border-blue-200' },
  'Kolkata Knight Riders': { bg: 'bg-purple-50', text: 'text-purple-900', border: 'border-purple-200' },
  'Royal Challengers Bengaluru': { bg: 'bg-red-50', text: 'text-red-900', border: 'border-red-200' },
  'Sunrisers Hyderabad': { bg: 'bg-orange-50', text: 'text-orange-900', border: 'border-orange-200' },
  'Gujarat Titans': { bg: 'bg-indigo-50', text: 'text-indigo-900', border: 'border-indigo-200' },
  'Lucknow Super Giants': { bg: 'bg-pink-50', text: 'text-pink-900', border: 'border-pink-200' },
  'Delhi Capitals': { bg: 'bg-sky-50', text: 'text-sky-900', border: 'border-sky-200' },
  'Rajasthan Royals': { bg: 'bg-blue-50', text: 'text-blue-900', border: 'border-blue-200' },
  'Punjab Kings': { bg: 'bg-red-50', text: 'text-red-900', border: 'border-red-200' },
};

const ROLE_ORDER: Record<string, number> = {
  WK: 0,
  BAT: 1,
  AR: 2,
  BWL: 3,
};

const formatTeamTitle = (id: string) => {
  if (id === 'risky_team') return 'Gamble Team (Differential Picks):';
  if (id === 'common_team_1') return 'Common Team 1 (Optimal Stability):';
  if (id === 'common_team_2') return 'Common Team 2 (Balanced Alternative):';
  return id.split('_').map((w) => w.charAt(0).toUpperCase() + w.slice(1)).join(' ') + ':';
};

export const TeamsScreen: React.FC<TeamsScreenProps> = ({
  teams,
  busy,
  onPlayerPress,
}) => {
  const teamList: GeneratedTeam[] = teams
    ? [teams.common_team_1, teams.common_team_2, teams.risky_team]
    : [];

  const sortPlayers = (players: any[]) => {
    return [...players].sort((a, b) => {
      const orderA = ROLE_ORDER[a.fantasy_category] ?? 99;
      const orderB = ROLE_ORDER[b.fantasy_category] ?? 99;
      return orderA - orderB;
    });
  };

  return (
    <div className="space-y-6 pb-16">
      {/* Disclaimer Card */}
      <div className="bg-amber-50/70 border border-amber-200/80 rounded-2xl p-4 sm:p-5 shadow-xs flex items-start gap-3.5">
        <AlertCircle className="w-5 h-5 text-amber-700 shrink-0 mt-0.5" />
        <div>
          <h3 className="text-sm font-bold text-amber-900 mb-1">Professional analytical note</h3>
          <p className="text-xs text-amber-900/85 leading-relaxed">
            {teams?.disclaimer ||
              'CricSense is an analytical support tool. These fantasy teams are calculated using player form scores, pitch conditions, and venue history, not a promise of winnings. Please apply your own judgment before entering contests.'}
          </p>
        </div>
      </div>

      {/* Captain Suggestions */}
      {teams?.captain_suggestions && teams.captain_suggestions.length > 0 && (
        <div className="bg-white border border-slate-200 rounded-2xl p-5 shadow-xs space-y-3">
          <div className="flex items-center gap-2 mb-1">
            <Award className="w-4 h-4 text-emerald-800" />
            <h3 className="text-base font-bold text-slate-900">Captain &amp; Vice-Captain Recommendations</h3>
          </div>
          <p className="text-xs text-slate-500">
            Use these pairing signals as tactical guidance. Match type variance dictates whether to lean safe or upside.
          </p>

          <div className="grid gap-2.5 pt-2">
            {teams.captain_suggestions.map((item) => (
              <div
                key={`${item.type}-${item.captain}-${item.vice_captain}`}
                className="bg-slate-50 border border-slate-200/80 rounded-xl p-3.5 flex flex-col sm:flex-row sm:items-center justify-between gap-2"
              >
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-extrabold text-slate-900">
                      (C) {item.captain} · (VC) {item.vice_captain}
                    </span>
                  </div>
                  <p className="text-xs text-slate-600 mt-1">{item.reason}</p>
                </div>
                <span className="self-start sm:self-center text-[11px] font-bold uppercase tracking-wider text-emerald-900 bg-emerald-100 px-2.5 py-1 rounded-md">
                  {item.type.replace(/_/g, ' ')}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* 3 Generated Teams */}
      {teamList.map((team, idx) => (
        <div
          key={team.team_type}
          id={`team-card-${team.team_type}`}
          className="bg-white border border-slate-200 rounded-2xl p-5 shadow-xs space-y-4"
        >
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-1 pb-2 border-b border-slate-100">
            <div>
              <h3 className="text-base sm:text-lg font-extrabold text-slate-900">
                {formatTeamTitle(team.team_type)}
              </h3>
              <div className="flex items-center gap-3 text-xs font-semibold text-slate-600 mt-0.5">
                <span>Captain (2x): <strong className="text-emerald-800">{team.captain || 'TBD'}</strong></span>
                <span>•</span>
                <span>Vice-Captain (1.5x): <strong className="text-emerald-800">{team.vice_captain || 'TBD'}</strong></span>
              </div>
            </div>
            <span className="text-xs font-bold text-slate-500 bg-slate-100 px-2.5 py-1 rounded-md self-start sm:self-center">
              11 / 11 Players
            </span>
          </div>

          <div className="grid gap-2">
            {sortPlayers(team.players).map((player: any) => {
              const franchiseStyle = TEAM_THEMES[player.team_name] || {
                bg: 'bg-slate-50',
                text: 'text-slate-900',
                border: 'border-slate-200',
              };
              const isCaptain = player.player_name === team.captain;
              const isViceCaptain = player.player_name === team.vice_captain;

              return (
                <div
                  key={player.player_name}
                  onClick={() => onPlayerPress(player.player_name)}
                  className={`flex items-center justify-between p-2.5 sm:p-3 rounded-xl border ${franchiseStyle.bg} ${franchiseStyle.border} hover:opacity-90 transition-all cursor-pointer group`}
                >
                  <div className="flex items-center gap-2">
                    <span className="w-9 text-center text-xs font-bold uppercase tracking-wider bg-white/80 text-slate-800 py-1 rounded border border-slate-200/60">
                      {player.fantasy_category}
                    </span>
                    <div>
                      <div className="flex items-center gap-1.5">
                        <span className={`text-sm font-bold ${franchiseStyle.text} group-hover:underline`}>
                          {player.player_name}
                        </span>
                        {isCaptain && (
                          <span className="text-[10px] font-black bg-emerald-800 text-white px-1.5 py-0.5 rounded shadow-2xs">
                            C (2x)
                          </span>
                        )}
                        {isViceCaptain && (
                          <span className="text-[10px] font-black bg-emerald-700 text-white px-1.5 py-0.5 rounded shadow-2xs">
                            VC (1.5x)
                          </span>
                        )}
                      </div>
                      <p className="text-[11px] text-slate-600 font-medium">
                        {player.team_name}
                      </p>
                    </div>
                  </div>

                  <div className="flex items-center gap-2">
                    <span className="text-xs font-extrabold text-slate-700 bg-white/90 px-2 py-1 rounded-md border border-slate-200/70">
                      {Math.round(player.runtime_score)} pts
                    </span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      ))}
    </div>
  );
};
