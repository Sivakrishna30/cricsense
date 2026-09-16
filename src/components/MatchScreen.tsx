import React, { useEffect, useState } from 'react';
import {
  Sparkles,
  MapPin,
  TrendingUp,
  Droplets,
  Wind,
  Layers,
  Users,
  ChevronRight,
  ShieldCheck,
} from 'lucide-react';
import {
  AnalyzedPlayer,
  MatchAnalysis,
  MatchConditionsInput,
  MatchdayMatch,
  VenueStats,
} from '../types';
import { getVenueStats } from '../services/api';

interface MatchScreenProps {
  match: MatchdayMatch | null;
  analysis: MatchAnalysis | null;
  conditions: MatchConditionsInput;
  busy: boolean;
  onConditionsChange: (value: MatchConditionsInput) => void;
  onRefreshAnalysis: () => void;
  onFantasyTeams: () => void;
  onPlayerPress: (playerName: string) => void;
}

function getScoreTone(score: number): { bg: string; text: string; border: string } {
  if (score >= 80) return { bg: 'bg-emerald-600', text: 'text-white', border: 'border-emerald-700' };
  if (score >= 65) return { bg: 'bg-emerald-800', text: 'text-white', border: 'border-emerald-900' };
  return { bg: 'bg-rose-600', text: 'text-white', border: 'border-rose-700' };
}

export const MatchScreen: React.FC<MatchScreenProps> = ({
  match,
  analysis,
  conditions,
  busy,
  onConditionsChange,
  onRefreshAnalysis,
  onFantasyTeams,
  onPlayerPress,
}) => {
  const [venueStats, setVenueStats] = useState<VenueStats | null>(null);

  useEffect(() => {
    if (match?.venue) {
      void getVenueStats(match.venue).then((stats) => {
        if (stats) setVenueStats(stats);
      });
    }
  }, [match?.venue]);

  const squadPlayers = analysis?.players || [];

  return (
    <div className="space-y-5 pb-16">
      {/* Match Meta Card */}
      <div className="bg-white border border-slate-200 rounded-2xl p-5 shadow-xs">
        <div className="flex items-center gap-2 text-xs font-semibold text-slate-500 mb-1">
          <MapPin className="w-4 h-4 text-emerald-700" />
          <span>{match?.venue}</span>
        </div>
        <h2 className="text-xl sm:text-2xl font-extrabold text-slate-900 tracking-tight">
          {match?.name}
        </h2>

        <div className="mt-3 flex flex-wrap gap-2 text-xs font-medium">
          <span className="bg-slate-100 text-slate-700 px-2.5 py-1 rounded-lg border border-slate-200">
            Squad: {match?.squad_source === 'actual' ? 'Confirmed post-toss' : 'Probable 11 previous match'}
          </span>
          {analysis?.favorite_team && (
            <span className="bg-emerald-50 text-emerald-900 px-2.5 py-1 rounded-lg border border-emerald-200 flex items-center gap-1 font-bold">
              <TrendingUp className="w-3.5 h-3.5 text-emerald-700" />
              <span>Model lean: {analysis.favorite_team}</span>
            </span>
          )}
        </div>
      </div>

      {/* Venue Intelligence */}
      {venueStats && (
        <div className="bg-white border border-slate-200 rounded-2xl p-5 shadow-xs">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-base font-bold text-slate-900 flex items-center gap-2">
              <Layers className="w-4 h-4 text-emerald-800" />
              <span>Venue intelligence</span>
            </h3>
            <span className="text-xs text-slate-500 font-medium">
              {venueStats.matches_sampled} matches analyzed
            </span>
          </div>

          <div className="grid grid-cols-3 gap-2.5 sm:gap-4 text-center">
            <div className="bg-slate-50 border border-slate-100 rounded-xl p-3">
              <span className="text-xs text-slate-500 block font-semibold">1st Innings Avg</span>
              <span className="text-lg sm:text-xl font-extrabold text-slate-900 mt-0.5 block">
                {venueStats.avg_first_innings}
              </span>
            </div>
            <div className="bg-slate-50 border border-slate-100 rounded-xl p-3">
              <span className="text-xs text-slate-500 block font-semibold">2nd Innings Avg</span>
              <span className="text-lg sm:text-xl font-extrabold text-slate-900 mt-0.5 block">
                {venueStats.avg_second_innings}
              </span>
            </div>
            <div className="bg-emerald-50/70 border border-emerald-100 rounded-xl p-3">
              <span className="text-xs text-emerald-800 block font-semibold">Chasers Win %</span>
              <span className="text-lg sm:text-xl font-extrabold text-emerald-900 mt-0.5 block">
                {venueStats.chasing_win_percent}%
              </span>
            </div>
          </div>
        </div>
      )}

      {/* Optional Match Inputs */}
      <div className="bg-white border border-slate-200 rounded-2xl p-5 shadow-xs space-y-4">
        <div>
          <h3 className="text-base font-bold text-slate-900 flex items-center gap-2">
            <Sparkles className="w-4 h-4 text-emerald-800" />
            <span>Optional match conditions</span>
          </h3>
          <p className="text-xs text-slate-500 mt-1">
            Toggle observed conditions (or match toss status) to immediately re-weight pitch, dew, and pace/spin modifiers.
          </p>
        </div>

        {/* Dew Toggle */}
        <div>
          <label className="text-xs font-bold text-slate-700 uppercase tracking-wider block mb-2 flex items-center gap-1.5">
            <Droplets className="w-3.5 h-3.5 text-blue-600" />
            <span>Dew probability</span>
          </label>
          <div className="flex gap-2">
            <button
              type="button"
              onClick={() => onConditionsChange({ ...conditions, dew: true })}
              className={`px-4 py-2 rounded-xl text-xs sm:text-sm font-semibold border transition-all cursor-pointer ${
                conditions.dew
                  ? 'bg-emerald-800 text-white border-emerald-900 shadow-xs'
                  : 'bg-slate-50 text-slate-700 border-slate-200 hover:bg-slate-100'
              }`}
            >
              Heavy Dew Expected
            </button>
            <button
              type="button"
              onClick={() => onConditionsChange({ ...conditions, dew: false })}
              className={`px-4 py-2 rounded-xl text-xs sm:text-sm font-semibold border transition-all cursor-pointer ${
                !conditions.dew
                  ? 'bg-emerald-800 text-white border-emerald-900 shadow-xs'
                  : 'bg-slate-50 text-slate-700 border-slate-200 hover:bg-slate-100'
              }`}
            >
              No / Minimal Dew
            </button>
          </div>
        </div>

        {/* Pitch Surface Toggle */}
        <div>
          <label className="text-xs font-bold text-slate-700 uppercase tracking-wider block mb-2 flex items-center gap-1.5">
            <Wind className="w-3.5 h-3.5 text-amber-600" />
            <span>Pitch Surface</span>
          </label>
          <div className="flex flex-wrap gap-2">
            <button
              type="button"
              onClick={() => onConditionsChange({ ...conditions, pitchSurface: 'dry' })}
              className={`px-4 py-2 rounded-xl text-xs sm:text-sm font-semibold border transition-all cursor-pointer ${
                conditions.pitchSurface === 'dry'
                  ? 'bg-emerald-800 text-white border-emerald-900 shadow-xs'
                  : 'bg-slate-50 text-slate-700 border-slate-200 hover:bg-slate-100'
              }`}
            >
              Dry Surface (Spin Grip)
            </button>
            <button
              type="button"
              onClick={() => onConditionsChange({ ...conditions, pitchSurface: 'wet' })}
              className={`px-4 py-2 rounded-xl text-xs sm:text-sm font-semibold border transition-all cursor-pointer ${
                conditions.pitchSurface === 'wet'
                  ? 'bg-emerald-800 text-white border-emerald-900 shadow-xs'
                  : 'bg-slate-50 text-slate-700 border-slate-200 hover:bg-slate-100'
              }`}
            >
              Wet / Moist Surface (Skid)
            </button>
            <button
              type="button"
              onClick={() => onConditionsChange({ ...conditions, pitchSurface: '' })}
              className={`px-4 py-2 rounded-xl text-xs sm:text-sm font-semibold border transition-all cursor-pointer ${
                !conditions.pitchSurface
                  ? 'bg-emerald-800 text-white border-emerald-900 shadow-xs'
                  : 'bg-slate-50 text-slate-700 border-slate-200 hover:bg-slate-100'
              }`}
            >
              Standard Track
            </button>
          </div>
        </div>

        {/* Toss Batting First Toggle */}
        <div>
          <label className="text-xs font-bold text-slate-700 uppercase tracking-wider block mb-2">
            Toss Batting First
          </label>
          <div className="flex flex-wrap gap-2">
            {(match?.teams || []).map((team) => (
              <button
                key={team}
                type="button"
                onClick={() => onConditionsChange({ ...conditions, tossBatting: team })}
                className={`px-4 py-2 rounded-xl text-xs sm:text-sm font-semibold border transition-all cursor-pointer ${
                  conditions.tossBatting === team
                    ? 'bg-emerald-800 text-white border-emerald-900 shadow-xs'
                    : 'bg-slate-50 text-slate-700 border-slate-200 hover:bg-slate-100'
                }`}
              >
                {team} bats
              </button>
            ))}
            <button
              type="button"
              onClick={() => onConditionsChange({ ...conditions, tossBatting: '' })}
              className={`px-4 py-2 rounded-xl text-xs sm:text-sm font-semibold border transition-all cursor-pointer ${
                !conditions.tossBatting
                  ? 'bg-emerald-800 text-white border-emerald-900 shadow-xs'
                  : 'bg-slate-50 text-slate-700 border-slate-200 hover:bg-slate-100'
              }`}
            >
              Toss Unknown
            </button>
          </div>
        </div>

        <button
          type="button"
          onClick={onRefreshAnalysis}
          disabled={busy}
          className="w-full py-2.5 px-4 bg-slate-100 hover:bg-slate-200 text-slate-800 font-bold text-xs sm:text-sm rounded-xl border border-slate-200 transition-colors flex items-center justify-center gap-2 cursor-pointer disabled:opacity-50"
        >
          {busy ? (
            <div className="w-4 h-4 border-2 border-slate-800 border-t-transparent rounded-full animate-spin" />
          ) : (
            <Sparkles className="w-4 h-4 text-emerald-800" />
          )}
          <span>Refresh Analysis With Selected Inputs</span>
        </button>
      </div>

      {/* Player Pool List */}
      <div className="bg-white border border-slate-200 rounded-2xl p-5 shadow-xs space-y-3">
        <div className="flex items-center justify-between mb-2">
          <div>
            <h3 className="text-base sm:text-lg font-bold text-slate-900 flex items-center gap-2">
              <Users className="w-4 h-4 text-emerald-800" />
              <span>Player Pool &amp; Runtime Scores</span>
            </h3>
            <p className="text-xs text-slate-500 mt-0.5">
              Ranked by analytical engine incorporating form, venue, and condition modifiers.
            </p>
          </div>
          <span className="text-xs font-semibold text-slate-500 bg-slate-100 px-2 py-1 rounded-md">
            {squadPlayers.length} players
          </span>
        </div>

        <div className="divide-y divide-slate-100">
          {squadPlayers.map((player: AnalyzedPlayer) => {
            const tone = getScoreTone(player.runtime_score);
            return (
              <div
                key={`${player.team_name}-${player.player_name}`}
                onClick={() => onPlayerPress(player.player_name)}
                className="py-3 sm:py-3.5 flex flex-col gap-2 hover:bg-slate-50 -mx-2 px-2 rounded-xl transition-colors cursor-pointer group"
              >
                <div className="flex items-start justify-between gap-3">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="text-sm sm:text-base font-bold text-slate-900 group-hover:text-emerald-800 truncate">
                        {player.player_name}
                      </span>
                      {player.is_overseas && (
                        <span className="text-[10px] uppercase font-bold text-amber-800 bg-amber-100 px-1.5 py-0.2 rounded">
                          Overseas
                        </span>
                      )}
                    </div>
                    <p className="text-xs text-slate-500 mt-0.5 font-medium">
                      {player.team_name} · <span className="font-semibold text-slate-700">{player.fantasy_category || player.role_profile}</span>
                    </p>
                  </div>

                  <div className="flex items-center gap-2">
                    <div className={`w-11 h-8 flex items-center justify-center rounded-lg font-extrabold text-sm ${tone.bg} ${tone.text} shadow-2xs`}>
                      {Math.round(player.runtime_score)}
                    </div>
                    <ChevronRight className="w-4 h-4 text-slate-400 group-hover:text-emerald-800 transition-colors" />
                  </div>
                </div>

                {/* Tags */}
                {player.tags && player.tags.length > 0 && (
                  <div className="flex flex-wrap gap-1.5">
                    {player.tags.slice(0, 3).map((tag) => (
                      <span
                        key={tag}
                        className="text-[11px] font-semibold bg-slate-100 text-slate-600 px-2 py-0.5 rounded-md border border-slate-200/60"
                      >
                        {tag.replace(/_/g, ' ')}
                      </span>
                    ))}
                  </div>
                )}

                {/* Insights */}
                {player.insights && player.insights.length > 0 && (
                  <div className="space-y-0.5 mt-0.5">
                    {player.insights.slice(0, 2).map((insight) => (
                      <p key={insight} className="text-xs text-emerald-900/90 flex items-start gap-1.5">
                        <span className="text-emerald-700 font-bold">•</span>
                        <span>{insight}</span>
                      </p>
                    ))}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>

      {/* Floating/Bottom Action Button */}
      <div className="sticky bottom-4 z-20 pt-2">
        <button
          id="btn-get-fantasy-teams"
          type="button"
          onClick={onFantasyTeams}
          className="w-full py-4 px-6 bg-emerald-800 hover:bg-emerald-900 text-white font-extrabold text-base rounded-2xl shadow-lg hover:shadow-xl transition-all flex items-center justify-center gap-2 cursor-pointer"
        >
          <ShieldCheck className="w-5 h-5" />
          <span>Get Fantasy Teams</span>
        </button>
      </div>
    </div>
  );
};
