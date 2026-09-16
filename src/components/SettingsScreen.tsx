import React from 'react';
import { Shield, Sparkles, User, FileText, Check } from 'lucide-react';

interface SettingsScreenProps {
  onBack: () => void;
}

export const SettingsScreen: React.FC<SettingsScreenProps> = ({ onBack }) => {
  return (
    <div className="space-y-4 pb-16">
      <div className="bg-white border border-slate-200 rounded-2xl p-5 shadow-xs">
        <h3 className="text-base font-bold text-slate-900 flex items-center gap-2 mb-1">
          <User className="w-4 h-4 text-emerald-800" />
          <span>Guest mode active</span>
        </h3>
        <p className="text-xs sm:text-sm text-slate-600 leading-relaxed">
          Users can browse match analysis and generate fantasy teams without login. Google sign-in can be configured for saved teams, contest sync, and account preferences.
        </p>
      </div>

      <div className="bg-white border border-slate-200 rounded-2xl p-5 shadow-xs">
        <h3 className="text-base font-bold text-slate-900 flex items-center gap-2 mb-1">
          <Sparkles className="w-4 h-4 text-emerald-800" />
          <span>Subscription Plans</span>
        </h3>
        <p className="text-xs sm:text-sm text-slate-600 leading-relaxed mb-3">
          Currently running on the Free Analytics Tier with full 5-layer algorithm access.
        </p>
        <div className="bg-emerald-50 border border-emerald-200 rounded-xl p-3 text-xs text-emerald-900 font-semibold flex items-center gap-2">
          <Check className="w-4 h-4 text-emerald-800" />
          <span>Free Plan active (Form, consistency, venue intelligence, and 3 AI teams included)</span>
        </div>
      </div>

      <div className="bg-white border border-slate-200 rounded-2xl p-5 shadow-xs">
        <h3 className="text-base font-bold text-slate-900 flex items-center gap-2 mb-1">
          <FileText className="w-4 h-4 text-emerald-800" />
          <span>Policy &amp; Terms of Transparency</span>
        </h3>
        <div className="space-y-2 text-xs sm:text-sm text-slate-600 leading-relaxed">
          <p>
            CricSense is an analytics decision support app based on recent player scores, performance context, pitch variables, and instinct signals. It does not guarantee fantasy contest winnings.
          </p>
          <p>
            Captain and vice-captain suggestions are analytical guidance only. Users should apply their own discretion before finalizing contest lineups.
          </p>
        </div>
      </div>

      <div className="bg-white border border-slate-200 rounded-2xl p-5 shadow-xs">
        <h3 className="text-base font-bold text-slate-900 flex items-center gap-2 mb-1">
          <Shield className="w-4 h-4 text-slate-600" />
          <span>Account actions</span>
        </h3>
        <p className="text-xs sm:text-sm text-slate-600 leading-relaxed">
          Sign-in session management, cloud backup, and delete-account workflows apply when signed into a verified provider account.
        </p>
      </div>
    </div>
  );
};
