import React from 'react';
import { Award, BarChart2, ShieldAlert, Sparkles, User, History } from 'lucide-react';
import { PlayerHistoryRow, PlayerSummary } from '../types';

interface PlayerScreenProps {
  profile: PlayerSummary | null;
  history: PlayerHistoryRow[];
  busy: boolean;
}

export const PlayerScreen: React.FC<PlayerScreenProps> = ({
  profile,
  history,
  busy,
}) => {
  if (busy) {
    return (
      <div className="flex flex-col items-center justify-center py-20 space-y-3">
        <div className="w-8 h-8 border-3 border-emerald-800 border-t-transparent rounded-full animate-spin" />
        <p className="text-sm font-medium text-slate-500">Loading player profile and history...</p>
      </div>
    );
  }

  const strengthTags = profile?.strength_tags || profile?.tags_json || [];
  const riskTags = profile?.risk_tags || [];

  return (
    <div className="space-y-5 pb-16">
      {/* Player Header Card */}
      <div className="bg-white border border-slate-200 rounded-2xl p-5 shadow-xs">
        <div className="flex items-center gap-3">
          <div className="w-12 h-12 rounded-2xl bg-emerald-100 text-emerald-800 flex items-center justify-center font-black text-lg shadow-2xs">
            {profile?.player_name?.charAt(0) || 'P'}
          </div>
          <div>
            <h2 className="text-xl sm:text-2xl font-black text-slate-900 tracking-tight">
              {profile?.player_name}
            </h2>
            <p className="text-xs sm:text-sm font-semibold text-emerald-800 uppercase tracking-wider mt-0.5">
              {profile?.role_profile || 'Player profile'} · <span className="text-slate-600 font-normal">{profile?.play_type || 'Context derived'}</span>
            </p>
          </div>
        </div>

        {/* 5-Layer Analytical Score Grid */}
        <div className="mt-5 grid grid-cols-2 sm:grid-cols-5 gap-2.5">
          <div className="bg-slate-50 border border-slate-100 rounded-xl p-3 text-center">
            <span className="text-[11px] font-semibold text-slate-500 uppercase">Recent Form</span>
            <span className="text-lg font-black text-slate-900 mt-0.5 block">
              {Math.round(profile?.recent_form_score || 0)}
            </span>
          </div>
          <div className="bg-slate-50 border border-slate-100 rounded-xl p-3 text-center">
            <span className="text-[11px] font-semibold text-slate-500 uppercase">Consistency</span>
            <span className="text-lg font-black text-slate-900 mt-0.5 block">
              {Math.round(profile?.consistency_score || 0)}
            </span>
          </div>
          <div className="bg-slate-50 border border-slate-100 rounded-xl p-3 text-center">
            <span className="text-[11px] font-semibold text-slate-500 uppercase">Stats Layer</span>
            <span className="text-lg font-black text-slate-900 mt-0.5 block">
              {Math.round(profile?.base_stats_score || 0)}
            </span>
          </div>
          <div className="bg-slate-50 border border-slate-100 rounded-xl p-3 text-center">
            <span className="text-[11px] font-semibold text-slate-500 uppercase">Context Layer</span>
            <span className="text-lg font-black text-slate-900 mt-0.5 block">
              {Math.round(profile?.context_score || 0)}
            </span>
          </div>
          <div className="bg-emerald-50 border border-emerald-100 rounded-xl p-3 text-center col-span-2 sm:col-span-1">
            <span className="text-[11px] font-semibold text-emerald-800 uppercase">Instinct Layer</span>
            <span className="text-lg font-black text-emerald-950 mt-0.5 block">
              {Math.round(profile?.instinct_score || 0)}
            </span>
          </div>
        </div>
      </div>

      {/* Strengths & Weaknesses */}
      <div className="bg-white border border-slate-200 rounded-2xl p-5 shadow-xs space-y-4">
        <div>
          <h3 className="text-sm font-bold uppercase tracking-wider text-slate-700 mb-2 flex items-center gap-1.5">
            <Sparkles className="w-4 h-4 text-emerald-700" />
            <span>Analytical Strengths</span>
          </h3>
          <div className="flex flex-wrap gap-2">
            {strengthTags.map((item) => (
              <span
                key={item}
                className="text-xs font-semibold bg-emerald-50 text-emerald-900 border border-emerald-200 px-2.5 py-1 rounded-lg"
              >
                {item}
              </span>
            ))}
          </div>
        </div>

        <div className="pt-2 border-t border-slate-100">
          <h3 className="text-sm font-bold uppercase tracking-wider text-slate-700 mb-1.5 flex items-center gap-1.5">
            <ShieldAlert className="w-4 h-4 text-amber-700" />
            <span>Risk / Matchup Vulnerabilities</span>
          </h3>
          <p className="text-xs text-slate-600 mb-2 leading-relaxed">
            {profile?.weakness_summary || 'No major weakness recorded.'}
          </p>
          <div className="flex flex-wrap gap-2">
            {riskTags.map((item) => (
              <span
                key={item}
                className="text-xs font-semibold bg-amber-50 text-amber-900 border border-amber-200 px-2.5 py-1 rounded-lg"
              >
                {item}
              </span>
            ))}
          </div>
        </div>
      </div>

      {/* Recent Matches */}
      <div className="bg-white border border-slate-200 rounded-2xl p-5 shadow-xs space-y-3">
        <h3 className="text-base font-bold text-slate-900 flex items-center gap-2">
          <History className="w-4 h-4 text-emerald-800" />
          <span>Recent Match Performance</span>
        </h3>

        <div className="divide-y divide-slate-100">
          {history.map((row, index) => (
            <div key={`${row.match_date}-${index}`} className="py-3 flex items-center justify-between">
              <div>
                <p className="text-sm font-bold text-slate-900">{row.event_name || 'IPL Match'}</p>
                <p className="text-xs text-slate-500 mt-0.5">
                  {row.match_date} · {row.venue}
                </p>
              </div>
              <div className="text-right">
                <span className="text-sm font-black text-emerald-900 bg-emerald-50 border border-emerald-200 px-2.5 py-1 rounded-lg">
                  {profile?.role_profile === 'bowler'
                    ? `${row.wickets != null ? row.wickets : 0} wkts / ${row.runs_conceded != null ? row.runs_conceded : '?'}`
                    : profile?.role_profile === 'all_rounder'
                    ? `${row.runs != null ? row.runs : 0} (${row.balls || 0}) • ${row.wickets != null ? row.wickets : 0} wkts`
                    : `${row.runs != null ? row.runs : 0} runs (${row.balls || 0}b)`}
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
