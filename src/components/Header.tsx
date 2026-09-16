import React from 'react';
import { ArrowLeft, Settings as SettingsIcon } from 'lucide-react';

interface HeaderProps {
  title?: string;
  onBack?: () => void;
  onOpenSettings?: () => void;
  showSettings?: boolean;
}

export const Header: React.FC<HeaderProps> = ({
  title,
  onBack,
  onOpenSettings,
  showSettings = false,
}) => {
  if (onBack) {
    return (
      <header className="flex items-center justify-between py-3 px-4 border-b border-slate-200 bg-white sticky top-0 z-30 shadow-xs">
        <button
          id="btn-back-header"
          onClick={onBack}
          className="flex items-center gap-1.5 text-slate-700 hover:text-emerald-800 font-semibold text-sm px-2.5 py-1.5 rounded-lg hover:bg-slate-100 transition-colors cursor-pointer"
        >
          <ArrowLeft className="w-4 h-4 text-emerald-800" />
          <span>Back</span>
        </button>
        <h1 className="text-base sm:text-lg font-bold text-slate-800 tracking-tight text-center truncate max-w-[240px] sm:max-w-md">
          {title || 'CricSense'}
        </h1>
        <div className="w-16" />
      </header>
    );
  }

  return (
    <header className="flex items-center justify-between py-3.5 px-4 sm:px-6 border-b border-slate-200 bg-white sticky top-0 z-30 shadow-xs">
      <div>
        <div className="flex items-baseline gap-2">
          <span className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight">CricSense</span>
          <span className="text-xs font-bold text-emerald-800 bg-emerald-50 border border-emerald-200 px-1.5 py-0.5 rounded-md">[mvp]</span>
        </div>
        <p className="text-xs text-slate-500 font-medium mt-0.5">Guest mode · IPL focus</p>
      </div>
      {showSettings && onOpenSettings && (
        <button
          id="btn-open-settings"
          onClick={onOpenSettings}
          className="flex items-center gap-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 px-3.5 py-2 rounded-xl text-sm font-semibold border border-slate-200 transition-colors cursor-pointer"
        >
          <SettingsIcon className="w-4 h-4 text-slate-600" />
          <span>Settings</span>
        </button>
      )}
    </header>
  );
};
