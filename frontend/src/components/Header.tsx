import React from 'react';
import { Bell, Settings, RotateCcw, Hexagon, Database, Layers, ShieldCheck, Sun, Moon } from 'lucide-react';
import { useTheme } from '../context/ThemeContext';

interface HeaderProps {
  currentStep: number;
  stepTitle: string;
  stepSubtitle: string;
  totalRows?: number;
  totalCols?: number;
  qualityScore?: number;
  onNewSession: () => void;
}

export const Header: React.FC<HeaderProps> = ({
  totalRows,
  totalCols,
  qualityScore,
  onNewSession,
}) => {
  const { theme, toggleTheme } = useTheme();

  return (
    <header className="glass-panel mx-6 mt-6 mb-4 px-6 py-3.5 flex items-center justify-between sticky top-6 z-30 transition-all">
      {/* Brand & Logo on Left */}
      <div className="flex items-center space-x-3.5">
        <div className="relative group">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-blue-500 via-cyan-500 to-indigo-600 p-[1px] shadow-[0_0_18px_rgba(47,139,255,0.5)]">
            <div className="w-full h-full bg-[#070C18] dark:bg-[#070C18] rounded-xl flex items-center justify-center">
              <Hexagon className="w-5 h-5 text-cyan-400 group-hover:rotate-45 transition-transform duration-500" />
            </div>
          </div>
          <div className="absolute -inset-0.5 bg-cyan-400/20 rounded-xl blur-sm -z-10 group-hover:bg-cyan-400/40 transition-colors" />
        </div>

        <div>
          <div className="flex items-center space-x-2">
            <h1 className="font-extrabold text-base tracking-wide text-[var(--text-primary)] drop-shadow-sm">
              FLOWER HAPPY
            </h1>
            <span className="text-[10px] font-bold uppercase tracking-widest text-cyan-500 dark:text-cyan-400 bg-cyan-500/10 border border-cyan-500/30 px-2 py-0.5 rounded-full shadow-inner">
              PRO
            </span>
          </div>
          <p className="text-[11px] text-[var(--text-muted)] font-medium">Hệ Thống Phân Tích Dữ Liệu Doanh Nghiệp</p>
        </div>
      </div>

      {/* Dataset quick info in center if available */}
      {totalRows !== undefined && totalRows > 0 && (
        <div className="hidden lg:flex items-center space-x-3 bg-white/[0.04] border border-[var(--panel-border)] px-3.5 py-1.5 rounded-xl text-xs text-[var(--text-secondary)]">
          <div className="flex items-center space-x-1.5">
            <Database className="w-3.5 h-3.5 text-cyan-500 dark:text-cyan-400" />
            <span><strong className="text-[var(--text-primary)] font-mono">{totalRows.toLocaleString()}</strong> dòng</span>
          </div>
          <span className="text-slate-400 dark:text-slate-600">|</span>
          <div className="flex items-center space-x-1.5">
            <Layers className="w-3.5 h-3.5 text-blue-500 dark:text-blue-400" />
            <span><strong className="text-[var(--text-primary)] font-mono">{totalCols}</strong> cột</span>
          </div>
          {qualityScore !== undefined && (
            <>
              <span className="text-slate-400 dark:text-slate-600">|</span>
              <div className="flex items-center space-x-1.5">
                <ShieldCheck className="w-3.5 h-3.5 text-emerald-500 dark:text-emerald-400" />
                <span>Chất lượng: <strong className="text-emerald-500 dark:text-emerald-400 font-mono">{qualityScore}%</strong></span>
              </div>
            </>
          )}
        </div>
      )}

      {/* Right User/Session Badge, Theme Toggle, Bell, Gear, Reset */}
      <div className="flex items-center space-x-2.5">
        {/* Theme Toggle (Sáng / Tối) */}
        <button
          onClick={toggleTheme}
          className="flex items-center space-x-1.5 text-xs font-bold px-3 py-1.5 rounded-xl border border-[var(--panel-border)] bg-[var(--card-bg)] hover:bg-[var(--card-hover-bg)] text-[var(--text-primary)] transition-all shadow-sm"
          title={`Chuyển sang giao diện ${theme === 'dark' ? 'Sáng' : 'Tối'}`}
          aria-label="Chuyển đổi giao diện Sáng / Tối"
        >
          {theme === 'dark' ? (
            <>
              <Sun className="w-3.5 h-3.5 text-amber-400" />
              <span>Sáng</span>
            </>
          ) : (
            <>
              <Moon className="w-3.5 h-3.5 text-blue-600" />
              <span>Tối</span>
            </>
          )}
        </button>

        {/* Reset Session Button */}
        <button
          onClick={onNewSession}
          className="flex items-center space-x-1.5 text-xs font-medium text-[var(--text-secondary)] hover:text-[var(--text-primary)] bg-[var(--card-bg)] hover:bg-[var(--card-hover-bg)] px-3 py-2 rounded-xl border border-[var(--panel-border)] transition-all shadow-sm"
          title="Tạo phiên phân tích mới"
        >
          <RotateCcw className="w-3.5 h-3.5 text-[var(--text-muted)]" />
          <span className="hidden sm:inline">Phiên mới</span>
        </button>

        {/* User / Session Avatar Badge */}
        <div className="flex items-center space-x-2.5 bg-[var(--card-bg)] border border-[var(--panel-border)] px-3 py-1.5 rounded-xl shadow-inner">
          <div className="w-8 h-8 rounded-full bg-gradient-to-tr from-blue-600 to-cyan-400 text-white font-extrabold text-xs flex items-center justify-center shadow-[0_0_12px_rgba(47,139,255,0.4)]">
            FH
          </div>
          <div className="text-left hidden sm:block">
            <div className="text-xs font-bold text-[var(--text-primary)]">Phiên Phân Tích</div>
            <div className="text-[10px] text-emerald-500 dark:text-emerald-400 flex items-center space-x-1 font-medium">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
              <span>Trực tuyến</span>
            </div>
          </div>
        </div>

        {/* Notification Bell */}
        <button
          className="p-2.5 bg-[var(--card-bg)] hover:bg-[var(--card-hover-bg)] border border-[var(--panel-border)] rounded-xl text-[var(--text-secondary)] hover:text-[var(--text-primary)] transition-all relative"
          title="Thông báo hệ thống"
        >
          <Bell className="w-4 h-4" />
          <span className="w-2 h-2 rounded-full bg-cyan-400 absolute top-2 right-2 shadow-[0_0_8px_#38BDF8]" />
        </button>

        {/* Settings Gear */}
        <button
          className="p-2.5 bg-[var(--card-bg)] hover:bg-[var(--card-hover-bg)] border border-[var(--panel-border)] rounded-xl text-[var(--text-secondary)] hover:text-[var(--text-primary)] transition-all"
          title="Cấu hình hệ thống"
        >
          <Settings className="w-4 h-4" />
        </button>
      </div>
    </header>
  );
};

export default Header;
