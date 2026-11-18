import React from 'react';
import { Database, Sparkles, BarChart3, FileSpreadsheet, Lock, CheckCircle2, Hexagon } from 'lucide-react';

export interface StepItem {
  id: number;
  title: string;
  subtitle: string;
  icon: React.ReactNode;
}

interface SidebarProps {
  currentStep: number;
  completedSteps: number[];
  onSelectStep: (stepId: number) => void;
  datasetStats?: {
    rows: number;
    cols: number;
    qualityScore?: number;
  };
}

export const Sidebar: React.FC<SidebarProps> = ({
  currentStep,
  completedSteps,
  onSelectStep,
  datasetStats,
}) => {
  const steps: StepItem[] = [
    {
      id: 1,
      title: 'Kết nối',
      subtitle: 'Chọn nguồn dữ liệu',
      icon: <Database className="w-5 h-5" />,
    },
    {
      id: 2,
      title: 'Làm sạch',
      subtitle: 'Kiểm tra và chuẩn hóa',
      icon: <Sparkles className="w-5 h-5" />,
    },
    {
      id: 3,
      title: 'Phân tích',
      subtitle: 'Khám phá số liệu',
      icon: <BarChart3 className="w-5 h-5" />,
    },
    {
      id: 4,
      title: 'Báo cáo',
      subtitle: 'Xem kết quả và xuất tệp',
      icon: <FileSpreadsheet className="w-5 h-5" />,
    },
  ];

  return (
    <aside className="w-72 glass-panel m-6 mr-0 flex flex-col h-[calc(100vh-3rem)] sticky top-6 select-none z-20 transition-all">
      {/* Sidebar Header Badge (inspired by reference image) */}
      <div className="p-5 border-b border-[var(--panel-border)] flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-blue-600/30 to-cyan-500/30 border border-cyan-400/40 flex items-center justify-center shadow-[0_0_12px_rgba(56,189,248,0.25)]">
            <Hexagon className="w-5 h-5 text-cyan-500 dark:text-cyan-300" />
          </div>
          <div>
            <span className="text-[11px] font-bold uppercase tracking-wider text-[var(--text-muted)] block">QUY TRÌNH</span>
            <span className="text-xs font-extrabold text-[var(--text-primary)]">4 BƯỚC XỬ LÝ</span>
          </div>
        </div>
        <span className="text-[11px] font-bold text-cyan-600 dark:text-cyan-400 bg-cyan-500/10 px-2 py-0.5 rounded-full border border-cyan-500/30 shadow-inner">
          {currentStep}/4
        </span>
      </div>

      {/* Sequential Steps List */}
      <nav className="flex-1 p-4 space-y-2.5 overflow-y-auto">
        {steps.map((step) => {
          const isCurrent = currentStep === step.id;
          const isCompleted = completedSteps.includes(step.id);
          const isLocked = !isCurrent && !isCompleted && step.id > Math.max(0, ...completedSteps, 1);

          return (
            <button
              key={step.id}
              disabled={isLocked}
              onClick={() => onSelectStep(step.id)}
              className={`w-full text-left p-3.5 rounded-2xl transition-all duration-300 flex items-start space-x-3.5 border group ${
                isCurrent
                  ? 'active-nav-glow'
                  : isLocked
                  ? 'bg-transparent border-transparent text-[var(--text-muted)] cursor-not-allowed opacity-40'
                  : 'bg-[var(--card-bg)] hover:bg-[var(--card-hover-bg)] border-[var(--card-border)] hover:border-[var(--card-border-hover)] text-[var(--text-secondary)] hover:text-[var(--text-primary)]'
              }`}
            >
              {/* Rounded icon tile */}
              <div
                className={`p-2.5 rounded-xl transition-all ${
                  isCurrent
                    ? 'bg-white/20 text-white shadow-sm'
                    : isCompleted
                    ? 'bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/30'
                    : 'bg-[var(--bg-secondary)] text-[var(--text-muted)] border border-[var(--panel-border)]'
                }`}
              >
                {step.icon}
              </div>

              {/* Title & subtitle */}
              <div className="flex-1 min-w-0">
                <div className="flex items-center justify-between">
                  <span className={`text-sm font-bold truncate ${isCurrent ? 'text-white' : 'text-[var(--text-primary)]'}`}>
                    {step.id}. {step.title}
                  </span>
                  {isLocked && <Lock className="w-3.5 h-3.5 text-[var(--text-muted)] ml-1.5 flex-shrink-0" />}
                  {isCompleted && !isCurrent && (
                    <CheckCircle2 className="w-4 h-4 text-emerald-500 dark:text-emerald-400 ml-1.5 flex-shrink-0" />
                  )}
                </div>
                <p className={`text-xs mt-0.5 truncate ${isCurrent ? 'text-blue-100 font-medium' : 'text-[var(--text-muted)]'}`}>
                  {step.subtitle}
                </p>
              </div>
            </button>
          );
        })}
      </nav>

      {/* Dataset Summary Tile in Sidebar Bottom */}
      {datasetStats && datasetStats.rows > 0 && (
        <div className="p-4 m-4 bg-[var(--card-bg)] rounded-2xl border border-[var(--panel-border)] text-xs text-[var(--text-secondary)] space-y-2 shadow-inner">
          <div className="flex items-center justify-between">
            <span className="font-bold text-[var(--text-primary)] text-[11px] uppercase tracking-wider">Tập Dữ Liệu</span>
            {datasetStats.qualityScore !== undefined && (
              <span className="bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 font-bold px-2 py-0.5 rounded-full border border-emerald-500/30 text-[10px]">
                {datasetStats.qualityScore}% Chất lượng
              </span>
            )}
          </div>
          <div className="flex justify-between text-[var(--text-muted)] text-[11px]">
            <span>Tổng số dòng:</span>
            <span className="font-bold font-mono text-[var(--text-primary)]">{datasetStats.rows.toLocaleString()}</span>
          </div>
          <div className="flex justify-between text-[var(--text-muted)] text-[11px]">
            <span>Số thuộc tính:</span>
            <span className="font-bold font-mono text-[var(--text-primary)]">{datasetStats.cols} cột</span>
          </div>
        </div>
      )}
    </aside>
  );
};

export default Sidebar;
