import React from 'react';
import { Calendar, ChevronRight, CloudRain, MapPin, RefreshCw, Trophy, Sparkles } from 'lucide-react';
import { MatchdayMatch, MatchdayResponse } from '../types';

interface HomeScreenProps {
  matchday: MatchdayResponse | null;
  completedMatches: MatchdayResponse | null;
  loading: boolean;
  error: string | null;
  onOpenMatch: (matchId: string) => void;
  onOpenCompletedMatch: (matchId: string) => void;
  onRetry: () => void;
}

export const HomeScreen: React.FC<HomeScreenProps> = ({
  matchday,
  completedMatches,
  loading,
  error,
  onOpenMatch,
  onOpenCompletedMatch,
  onRetry,
}) => {
  return (
    <div className="space-y-6 pb-12">
      {/* Hero Header */}
      <div className="bg-gradient-to-r from-emerald-900 to-emerald-800 text-white rounded-2xl p-5 sm:p-6 shadow-sm">
        <div className="flex items-center gap-2 mb-2 text-emerald-200 text-xs font-semibold tracking-wide uppercase">
          <Sparkles className="w-3.5 h-3.5" />
          <span>Matchday Intelligence</span>
        </div>
        <h2 className="text-2xl sm:text-3xl font-extrabold tracking-tight">Today&apos;s IPL matches</h2>
        <p className="text-emerald-100 text-sm sm:text-base mt-2 leading-relaxed max-w-xl">
          Open a match, add simple conditions like dew or pitch surface, and get clean analytical fantasy team suggestions.
        </p>
      </div>

      {/* Free tier banner */}
      <div className="bg-emerald-50/70 border border-emerald-200/80 rounded-xl p-3.5 flex items-center justify-between text-xs text-emerald-900">
        <div>
          <span className="font-bold uppercase tracking-wider text-[11px] bg-emerald-200/70 text-emerald-950 px-2 py-0.5 rounded mr-2">Free Tier</span>
          <span>Analytics engine active with full player form &amp; venue models.</span>
        </div>
        <span className="hidden sm:inline-block text-emerald-700 font-medium">Guest Mode</span>
      </div>

      {/* Matches Content */}
      {loading ? (
        <div className="flex flex-col items-center justify-center py-16 space-y-3 bg-white rounded-2xl border border-slate-200">
          <div className="w-8 h-8 border-3 border-emerald-800 border-t-transparent rounded-full animate-spin" />
          <p className="text-sm font-medium text-slate-500">Loading IPL match schedule &amp; models...</p>
        </div>
      ) : error ? (
        <div className="bg-red-50 border border-red-200 rounded-2xl p-6 text-center">
          <h3 className="text-base font-bold text-red-900 mb-1">Live match feed unavailable</h3>
          <p className="text-sm text-red-700 mb-4">{error}</p>
          <button
            onClick={onRetry}
            className="inline-flex items-center gap-2 px-4 py-2 bg-white text-red-700 font-semibold text-sm rounded-xl border border-red-300 shadow-xs hover:bg-red-50 transition-colors cursor-pointer"
          >
            <RefreshCw className="w-4 h-4" />
            <span>Retry</span>
          </button>
        </div>
      ) : (matchday?.matches || []).length === 0 ? (
        <div className="bg-white border border-slate-200 rounded-2xl p-8 text-center">
          <p className="text-base font-semibold text-slate-800">No scheduled IPL matches found</p>
          <p className="text-sm text-slate-500 mt-1">Check the completed matches section below for historical accuracy reports.</p>
        </div>
      ) : (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-bold text-slate-900 flex items-center gap-2">
              <Calendar className="w-4 h-4 text-emerald-800" />
              <span>Upcoming &amp; Live Fixtures</span>
            </h3>
            <span className="text-xs font-semibold text-slate-500">{matchday?.matches.length} matches</span>
          </div>

          <div className="grid gap-3.5">
            {matchday?.matches.map((match: MatchdayMatch) => {
              const [team1, team2] = match.teams;
              return (
                <div
                  key={match.id}
                  id={`match-card-${match.id}`}
                  onClick={() => onOpenMatch(match.id)}
                  className="group bg-white hover:bg-slate-50/80 border border-slate-200 hover:border-emerald-600 rounded-2xl p-4 sm:p-5 transition-all shadow-xs hover:shadow-md cursor-pointer relative"
                >
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-xs font-bold uppercase tracking-wider text-emerald-900 bg-emerald-100 px-2 py-0.5 rounded-full">
                      {match.status}
                    </span>
                    <span className="text-xs font-medium text-slate-500 flex items-center gap-1">
                      <MapPin className="w-3.5 h-3.5 text-slate-400" />
                      <span className="truncate max-w-[180px]">{match.venue}</span>
                    </span>
                  </div>

                  <div className="flex items-center justify-between py-2">
                    <div>
                      <h4 className="text-base sm:text-lg font-bold text-slate-900 group-hover:text-emerald-900 transition-colors">
                        {team1} <span className="text-slate-400 font-normal">vs</span> {team2}
                      </h4>
                      {match.weather?.summary_text && (
                        <p className="text-xs text-slate-500 mt-1 flex items-center gap-1.5">
                          <CloudRain className="w-3.5 h-3.5 text-emerald-700" />
                          <span>{match.weather.summary_text}</span>
                        </p>
                      )}
                    </div>
                    <div className="p-2 rounded-xl bg-slate-100 group-hover:bg-emerald-800 group-hover:text-white transition-colors text-slate-600">
                      <ChevronRight className="w-5 h-5" />
                    </div>
                  </div>

                  <div className="mt-3 pt-2.5 border-t border-slate-100 flex items-center justify-between text-xs text-slate-500">
                    <span>
                      Squad: <strong className="text-slate-700">{match.squad_source === 'actual' ? 'Confirmed post-toss' : 'Probable Playing 11'}</strong>
                    </span>
                    <span className="text-emerald-800 font-medium group-hover:underline">Tap to customize conditions →</span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Completed IPL Matches Section */}
      {!loading && !error && (completedMatches?.matches || []).length > 0 && (
        <div className="mt-8 pt-6 border-t border-slate-200">
          <div className="mb-4">
            <div className="flex items-center gap-2 text-emerald-800 text-xs font-bold uppercase tracking-wider mb-1">
              <Trophy className="w-4 h-4" />
              <span>Model Verification</span>
            </div>
            <h3 className="text-xl font-extrabold text-slate-900">Completed IPL matches</h3>
            <p className="text-sm text-slate-600 mt-1">
              Review historical model accuracy percentages compared to actual Dream11 / IPL Fantasy 11 scores.
            </p>
          </div>

          <div className="grid gap-3">
            {completedMatches?.matches.map((match: MatchdayMatch) => (
              <div
                key={match.id}
                id={`completed-match-${match.id}`}
                onClick={() => onOpenCompletedMatch(match.id)}
                className="bg-white hover:bg-slate-50 border border-slate-200 hover:border-emerald-500 rounded-xl p-4 transition-all shadow-xs flex items-center justify-between cursor-pointer group"
              >
                <div>
                  <h4 className="text-base font-bold text-slate-900 group-hover:text-emerald-800 transition-colors">
                    {match.teams.join(' vs ')}
                  </h4>
                  <p className="text-xs text-slate-500 mt-0.5">
                    {match.date} · {match.venue}
                  </p>
                  <span className="inline-block text-xs font-bold text-emerald-800 bg-emerald-50 border border-emerald-200 px-2 py-0.5 rounded-md mt-2">
                    View Accuracy Insights →
                  </span>
                </div>
                <div className="p-2 rounded-xl bg-slate-100 group-hover:bg-emerald-800 group-hover:text-white transition-colors text-slate-600">
                  <ChevronRight className="w-5 h-5" />
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
