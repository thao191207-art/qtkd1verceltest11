import { useState, useEffect } from 'react';
import { ThemeProvider } from './context/ThemeContext';
import Sidebar from './components/Sidebar';
import Header from './components/Header';
import ConnectPage from './pages/ConnectPage';
import CleanPage from './pages/CleanPage';
import AnalyzePage from './pages/AnalyzePage';
import ReportPage from './pages/ReportPage';
import ApiService from './services/api';

function AppContent() {
  const [sessionId, setSessionId] = useState<string>('');
  const [currentStep, setCurrentStep] = useState<number>(1);
  const [completedSteps, setCompletedSteps] = useState<number[]>([]);
  const [datasetStats, setDatasetStats] = useState<{
    rows: number;
    cols: number;
    qualityScore?: number;
  }>({ rows: 0, cols: 0 });

  // Transition config for Analyze page when clicking from report
  const [pivotConfigForAnalyze, setPivotConfigForAnalyze] = useState<any>(null);

  // Initialize session on mount
  const initializeNewSession = async () => {
    try {
      const res = await ApiService.createNewSession();
      setSessionId(res.session_id);
      setCurrentStep(1);
      setCompletedSteps([]);
      setDatasetStats({ rows: 0, cols: 0 });
      setPivotConfigForAnalyze(null);
    } catch (err) {
      console.error('Failed to create session', err);
    }
  };

  useEffect(() => {
    initializeNewSession();
  }, []);

  const handleStepNavigation = (stepId: number) => {
    if (stepId === 1 || completedSteps.includes(stepId) || stepId <= Math.max(0, ...completedSteps) + 1) {
      setCurrentStep(stepId);
    }
  };

  const handleDatasetLoaded = (stats: { rows: number; cols: number; qualityScore: number }) => {
    setDatasetStats(stats);
    if (!completedSteps.includes(1)) {
      setCompletedSteps((prev) => [...prev, 1]);
    }
    setCurrentStep(2);
  };

  const handleCleanCompleted = () => {
    if (!completedSteps.includes(2)) {
      setCompletedSteps((prev) => [...prev, 2]);
    }
    setCurrentStep(3);
  };

  const handleAnalyzeCompleted = () => {
    if (!completedSteps.includes(3)) {
      setCompletedSteps((prev) => [...prev, 3]);
    }
    setCurrentStep(4);
  };

  const handleOpenPivotForProblem = (config: any) => {
    setPivotConfigForAnalyze(config);
    if (!completedSteps.includes(3)) {
      setCompletedSteps((prev) => [...prev, 3]);
    }
    setCurrentStep(3);
  };

  const stepDetails = [
    { title: 'Kết Nối Dữ Liệu', subtitle: 'Tải lên và cấu hình nguồn tệp kinh doanh thực tế' },
    { title: 'Làm Sạch & Chuẩn Hóa', subtitle: 'Phát hiện lỗi, loại bỏ trùng lặp và nâng cao chất lượng dữ liệu' },
    { title: 'Phân Tích Số Liệu', subtitle: 'PivotChart tương tác, trực quan hóa và đào sâu phân đoạn' },
    { title: 'Báo Cáo Hoạt Động', subtitle: 'Trích xuất insights, phát hiện rủi ro và xuất file PDF/Excel/PNG' },
  ];

  if (!sessionId) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[var(--bg-primary)] text-[var(--text-secondary)]">
        <div className="flex items-center space-x-3">
          <div className="w-4 h-4 rounded-full bg-cyan-400 animate-ping" />
          <span className="font-extrabold text-sm tracking-wide text-[var(--text-primary)]">Đang khởi tạo FLOWER HAPPY...</span>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[var(--bg-primary)] text-[var(--text-primary)] relative overflow-x-hidden flex transition-colors duration-300">
      {/* Background Glowing Ambient Orbs */}
      <div className="fixed inset-0 pointer-events-none overflow-hidden z-0 opacity-[var(--orb-opacity)] transition-opacity duration-300">
        {/* Top left cyan orb */}
        <div className="absolute -top-32 -left-32 w-[550px] h-[550px] bg-cyan-500 rounded-full blur-[140px]" />
        {/* Center blue orb */}
        <div className="absolute top-1/4 left-1/3 w-[650px] h-[650px] bg-blue-600 rounded-full blur-[160px]" />
        {/* Bottom right indigo orb */}
        <div className="absolute -bottom-32 -right-32 w-[600px] h-[600px] bg-indigo-600 rounded-full blur-[150px]" />
        {/* Top right sky orb */}
        <div className="absolute top-12 right-1/4 w-[400px] h-[400px] bg-sky-400 rounded-full blur-[120px]" />
      </div>

      {/* Left Sidebar */}
      <Sidebar
        currentStep={currentStep}
        completedSteps={completedSteps}
        onSelectStep={handleStepNavigation}
        datasetStats={datasetStats}
      />

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col min-w-0 z-10 relative">
        <Header
          currentStep={currentStep}
          stepTitle={stepDetails[currentStep - 1].title}
          stepSubtitle={stepDetails[currentStep - 1].subtitle}
          totalRows={datasetStats.rows}
          totalCols={datasetStats.cols}
          qualityScore={datasetStats.qualityScore}
          onNewSession={initializeNewSession}
        />

        <main className="flex-1 overflow-y-auto pb-12">
          {currentStep === 1 && (
            <ConnectPage
              sessionId={sessionId}
              onContinue={() => {
                if (!completedSteps.includes(1)) {
                  setCompletedSteps((prev) => [...prev, 1]);
                }
                setCurrentStep(2);
              }}
              onDatasetLoaded={handleDatasetLoaded}
            />
          )}

          {currentStep === 2 && (
            <CleanPage
              sessionId={sessionId}
              onContinue={handleCleanCompleted}
              onStatsUpdated={(stats) => setDatasetStats(stats)}
            />
          )}

          {currentStep === 3 && (
            <AnalyzePage
              sessionId={sessionId}
              onContinue={handleAnalyzeCompleted}
              initialPivotConfig={pivotConfigForAnalyze}
            />
          )}

          {currentStep === 4 && (
            <ReportPage
              sessionId={sessionId}
              onOpenPivotForProblem={handleOpenPivotForProblem}
            />
          )}
        </main>
      </div>
    </div>
  );
}

export function App() {
  return (
    <ThemeProvider>
      <AppContent />
    </ThemeProvider>
  );
}

export default App;
