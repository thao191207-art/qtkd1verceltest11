import React, { useState, useEffect } from 'react';
import {
  Sparkles, AlertTriangle, Info, AlertCircle, Trash2,
  Undo2, RotateCcw, Filter, CheckCircle2, ChevronRight, ArrowRight,
  RefreshCw, Plus, Edit2, ChevronLeft, Activity
} from 'lucide-react';
import ApiService, { type FilterCondition } from '../services/api';

interface Issue {
  id: string;
  column: string;
  type: string;
  title: string;
  description: string;
  severity: 'high' | 'medium' | 'low';
  suggested_action: string;
  count: number;
}

interface ProfileData {
  total_rows: number;
  total_cols: number;
  quality_score: number;
  duplicate_rows: number;
  duplicate_percentage: number;
  columns_profile: Record<string, any>;
  issues: Issue[];
}

interface CleanPageProps {
  sessionId: string;
  onContinue: () => void;
  onStatsUpdated: (stats: { rows: number; cols: number; qualityScore: number }) => void;
}

export const CleanPage: React.FC<CleanPageProps> = ({
  sessionId,
  onContinue,
  onStatsUpdated,
}) => {
  const [profile, setProfile] = useState<ProfileData | null>(null);
  const [history, setHistory] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  // Table Preview State
  const [previewPage, setPreviewPage] = useState(1);
  const [previewData, setPreviewData] = useState<{
    total_rows: number;
    columns: string[];
    records: Record<string, any>[];
  } | null>(null);

  // Modals & Action States
  const [activeModal, setActiveModal] = useState<string | null>(null);
  const [selectedColumn, setSelectedColumn] = useState<string>('');
  
  // Fill missing
  const [missingMethod, setMissingMethod] = useState<'drop' | 'mean' | 'median' | 'mode' | 'constant'>('mean');
  const [constantVal, setConstantVal] = useState('');

  // Text standardize
  const [textOp, setTextOp] = useState<'trim' | 'lowercase' | 'uppercase' | 'titlecase'>('trim');

  // Convert type
  const [targetType, setTargetType] = useState('float');

  // Outliers
  const [outlierMethod, setOutlierMethod] = useState<'winsorize' | 'drop' | 'flag'>('winsorize');

  // Rename column
  const [newColName, setNewColName] = useState('');

  // Filter conditions
  const [filterConditions, setFilterConditions] = useState<FilterCondition[]>([
    { column: '', operator: 'equals', value: '' }
  ]);
  const [filterLogic, setFilterLogic] = useState<'AND' | 'OR'>('AND');

  const fetchProfileAndPreview = async () => {
    try {
      setLoading(true);
      const profRes = await ApiService.getCleaningProfile(sessionId);
      setProfile(profRes.profile);
      setHistory(profRes.history || []);
      
      const prevRes = await ApiService.getCleaningPreview(sessionId, previewPage, 20);
      setPreviewData(prevRes);

      if (profRes.profile) {
        onStatsUpdated({
          rows: profRes.profile.total_rows,
          cols: profRes.profile.total_cols,
          qualityScore: profRes.profile.quality_score,
        });
      }
    } catch (err: any) {
      setErrorMessage(err.response?.data?.detail || err.message || 'Không thể tải hồ sơ làm sạch.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchProfileAndPreview();
  }, [sessionId, previewPage]);

  const handleAction = async (action: string, params: Record<string, any>) => {
    try {
      setActionLoading(true);
      setErrorMessage(null);
      const res = await ApiService.executeCleaningAction({
        session_id: sessionId,
        action,
        params,
      });

      setProfile(res.profile);
      setSuccessMessage(`Áp dụng thành công: ${action}`);
      setActiveModal(null);

      const prevRes = await ApiService.getCleaningPreview(sessionId, 1, 20);
      setPreviewData(prevRes);
      setPreviewPage(1);

      onStatsUpdated({
        rows: res.profile.total_rows,
        cols: res.profile.total_cols,
        qualityScore: res.profile.quality_score,
      });

      const profRes = await ApiService.getCleaningProfile(sessionId);
      setHistory(profRes.history || []);
    } catch (err: any) {
      setErrorMessage(err.response?.data?.detail || err.message || 'Lỗi áp dụng thao tác.');
    } finally {
      setActionLoading(false);
    }
  };

  const handleUndo = async () => {
    try {
      setActionLoading(true);
      setErrorMessage(null);
      const res = await ApiService.undoCleaning(sessionId);
      setProfile(res.profile);
      setSuccessMessage(res.message);

      const prevRes = await ApiService.getCleaningPreview(sessionId, 1, 20);
      setPreviewData(prevRes);

      onStatsUpdated({
        rows: res.profile.total_rows,
        cols: res.profile.total_cols,
        qualityScore: res.profile.quality_score,
      });

      const profRes = await ApiService.getCleaningProfile(sessionId);
      setHistory(profRes.history || []);
    } catch (err: any) {
      setErrorMessage(err.response?.data?.detail || err.message || 'Không thể hoàn tác.');
    } finally {
      setActionLoading(false);
    }
  };

  const handleReset = async () => {
    if (!window.confirm('Bạn có chắc muốn đặt lại dữ liệu về trạng thái ban đầu? Mọi bước làm sạch sẽ được hoàn trả.')) {
      return;
    }
    try {
      setActionLoading(true);
      setErrorMessage(null);
      const res = await ApiService.resetCleaning(sessionId);
      setProfile(res.profile);
      setSuccessMessage(res.message);

      const prevRes = await ApiService.getCleaningPreview(sessionId, 1, 20);
      setPreviewData(prevRes);

      onStatsUpdated({
        rows: res.profile.total_rows,
        cols: res.profile.total_cols,
        qualityScore: res.profile.quality_score,
      });

      const profRes = await ApiService.getCleaningProfile(sessionId);
      setHistory(profRes.history || []);
    } catch (err: any) {
      setErrorMessage(err.response?.data?.detail || err.message || 'Không thể đặt lại dữ liệu.');
    } finally {
      setActionLoading(false);
    }
  };

  const handleApplyFilter = async () => {
    const validConds = filterConditions.filter((c) => c.column && c.operator);
    if (validConds.length === 0) {
      setErrorMessage('Vui lòng chọn ít nhất một điều kiện lọc hợp lệ.');
      return;
    }
    try {
      setActionLoading(true);
      setErrorMessage(null);
      const res = await ApiService.applyFilter({
        session_id: sessionId,
        conditions: validConds,
        logic: filterLogic,
      });

      setProfile(res.profile);
      setSuccessMessage('Đã áp dụng bộ lọc thành công.');
      setActiveModal(null);

      const prevRes = await ApiService.getCleaningPreview(sessionId, 1, 20);
      setPreviewData(prevRes);
      setPreviewPage(1);

      onStatsUpdated({
        rows: res.profile.total_rows,
        cols: res.profile.total_cols,
        qualityScore: res.profile.quality_score,
      });

      const profRes = await ApiService.getCleaningProfile(sessionId);
      setHistory(profRes.history || []);
    } catch (err: any) {
      setErrorMessage(err.response?.data?.detail || err.message || 'Lỗi áp dụng bộ lọc.');
    } finally {
      setActionLoading(false);
    }
  };

  const addFilterCondition = () => {
    const cols = previewData?.columns || [];
    setFilterConditions((prev) => [
      ...prev,
      { column: cols[0] || '', operator: 'equals', value: '' }
    ]);
  };

  const removeFilterCondition = (idx: number) => {
    setFilterConditions((prev) => prev.filter((_, i) => i !== idx));
  };

  const columns = previewData?.columns || [];

  // Total missing cells & outliers calculation
  let totalMissing = 0;
  let totalOutliers = 0;
  if (profile?.columns_profile) {
    Object.values(profile.columns_profile).forEach((cp: any) => {
      totalMissing += cp.missing_count || 0;
      totalOutliers += cp.outliers_iqr || 0;
    });
  }

  // Circular score progress calculations
  const score = profile?.quality_score || 0;
  const radius = 34;
  const circumference = 2 * Math.PI * radius;
  const strokeDashoffset = circumference - (score / 100) * circumference;

  if (loading && !profile) {
    return (
      <div className="p-16 text-center flex flex-col items-center justify-center space-y-4">
        <RefreshCw className="w-10 h-10 text-cyan-400 animate-spin" />
        <p className="text-slate-300 font-bold text-sm">Đang tự động rà soát và kiểm tra chất lượng dữ liệu...</p>
      </div>
    );
  }

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-8 animate-fadeIn">
      {/* Top Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center space-x-2">
            <span className="text-[10px] font-extrabold uppercase tracking-widest text-cyan-400 bg-cyan-950/70 border border-cyan-800/60 px-2.5 py-0.5 rounded-full">
              BƯỚC 2: LÀM SẠCH
            </span>
          </div>
          <h2 className="text-2xl font-black text-white mt-1 tracking-tight">Kiểm Tra & Chuẩn Hóa Dữ Liệu</h2>
          <p className="text-slate-400 mt-1 text-xs">
            Rà soát giá trị trống, trùng lặp, chuẩn hóa văn bản/tiền tệ và xử lý ngoại lai IQR để đảm bảo tính chuẩn xác trước khi phân tích.
          </p>
        </div>

        {/* Global Controls & Next Step */}
        <div className="flex items-center space-x-3">
          <button
            onClick={handleUndo}
            disabled={actionLoading || history.length === 0}
            className="flex items-center space-x-1.5 text-xs font-bold px-3.5 py-2 glass-card text-slate-300 hover:text-white disabled:opacity-40 disabled:cursor-not-allowed transition-all"
            title="Hoàn tác thao tác gần nhất"
          >
            <Undo2 className="w-3.5 h-3.5 text-cyan-400" />
            <span>Hoàn tác ({history.length})</span>
          </button>

          <button
            onClick={handleReset}
            disabled={actionLoading || history.length === 0}
            className="flex items-center space-x-1.5 text-xs font-bold px-3.5 py-2 glass-card text-slate-300 hover:text-rose-400 disabled:opacity-40 disabled:cursor-not-allowed transition-all"
            title="Đặt lại dữ liệu gốc ban đầu"
          >
            <RotateCcw className="w-3.5 h-3.5 text-slate-400" />
            <span>Đặt lại gốc</span>
          </button>

          <button
            onClick={onContinue}
            className="flex items-center space-x-2 active-nav-glow px-6 py-2.5 rounded-xl font-bold text-xs cursor-pointer transition-all"
          >
            <span>Phân tích số liệu</span>
            <ArrowRight className="w-4 h-4 text-white" />
          </button>
        </div>
      </div>

      {/* Messages */}
      {errorMessage && (
        <div className="p-4 bg-rose-950/60 border border-rose-600/40 rounded-2xl flex items-center justify-between text-rose-200 text-xs shadow-glass">
          <div className="flex items-center space-x-2">
            <AlertCircle className="w-4 h-4 text-rose-400 flex-shrink-0" />
            <span>{errorMessage}</span>
          </div>
          <button onClick={() => setErrorMessage(null)} className="text-rose-400 hover:text-rose-200 font-bold ml-4">✕</button>
        </div>
      )}

      {successMessage && (
        <div className="p-4 bg-emerald-950/60 border border-emerald-600/40 rounded-2xl flex items-center justify-between text-emerald-200 text-xs shadow-glass">
          <div className="flex items-center space-x-2">
            <CheckCircle2 className="w-4 h-4 text-emerald-400 flex-shrink-0" />
            <span>{successMessage}</span>
          </div>
          <button onClick={() => setSuccessMessage(null)} className="text-emerald-400 font-bold ml-4">✕</button>
        </div>
      )}

      {/* 4 KPI Cards in a row (Matching the reference aesthetic) */}
      {profile && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {/* Card 1: Data Quality Score Donut */}
          <div className="glass-card p-5 flex items-center justify-between">
            <div className="space-y-1">
              <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider block">Điểm Chất Lượng</span>
              <div className="text-2xl font-black font-mono text-white tracking-tight">{score}%</div>
              <span className="text-[11px] font-semibold text-emerald-400 block">
                {score >= 80 ? 'Xuất sắc' : score >= 65 ? 'Tốt' : 'Cần cải thiện'}
              </span>
            </div>
            {/* SVG Donut Progress Ring */}
            <div className="relative w-20 h-20 flex items-center justify-center flex-shrink-0">
              <svg className="w-full h-full transform -rotate-90" viewBox="0 0 80 80">
                <circle
                  cx="40"
                  cy="40"
                  r={radius}
                  stroke="rgba(255, 255, 255, 0.08)"
                  strokeWidth="7"
                  fill="transparent"
                />
                <circle
                  cx="40"
                  cy="40"
                  r={radius}
                  stroke="#38BDF8"
                  strokeWidth="7"
                  strokeDasharray={circumference}
                  strokeDashoffset={strokeDashoffset}
                  strokeLinecap="round"
                  fill="transparent"
                  className="transition-all duration-1000 ease-out"
                />
              </svg>
              <div className="absolute font-extrabold text-sm font-mono text-white">
                {score}%
              </div>
            </div>
          </div>

          {/* Card 2: Missing Values */}
          <div className="glass-card p-5 flex flex-col justify-between">
            <div className="flex items-center justify-between">
              <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">Giá Trị Trống</span>
              <div className="w-8 h-8 rounded-lg bg-amber-500/20 text-amber-400 flex items-center justify-center border border-amber-500/30">
                <AlertTriangle className="w-4 h-4" />
              </div>
            </div>
            <div className="mt-3">
              <div className="text-3xl font-black font-mono text-white tracking-tight">{totalMissing.toLocaleString()}</div>
              <div className="text-[11px] text-amber-400 mt-1 flex items-center space-x-1 font-semibold">
                <span>{totalMissing > 0 ? 'Cần điền hoặc xóa' : '✓ Không có giá trị trống'}</span>
              </div>
            </div>
          </div>

          {/* Card 3: Duplicates */}
          <div className="glass-card p-5 flex flex-col justify-between">
            <div className="flex items-center justify-between">
              <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">Dòng Trùng Lặp</span>
              <div className="w-8 h-8 rounded-lg bg-rose-500/20 text-rose-400 flex items-center justify-center border border-rose-500/30">
                <Trash2 className="w-4 h-4" />
              </div>
            </div>
            <div className="mt-3">
              <div className="text-3xl font-black font-mono text-white tracking-tight">{profile.duplicate_rows.toLocaleString()}</div>
              <div className={`text-[11px] mt-1 font-semibold ${profile.duplicate_rows > 0 ? 'text-rose-400' : 'text-emerald-400'}`}>
                {profile.duplicate_rows > 0 ? `${profile.duplicate_percentage}% toàn bộ tệp` : '✓ Không có dòng trùng'}
              </div>
            </div>
          </div>

          {/* Card 4: Outliers */}
          <div className="glass-card p-5 flex flex-col justify-between">
            <div className="flex items-center justify-between">
              <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">Điểm Ngoại Lai (IQR)</span>
              <div className="w-8 h-8 rounded-lg bg-purple-500/20 text-purple-400 flex items-center justify-center border border-purple-500/30">
                <Activity className="w-4 h-4" />
              </div>
            </div>
            <div className="mt-3">
              <div className="text-3xl font-black font-mono text-white tracking-tight">{totalOutliers.toLocaleString()}</div>
              <div className="text-[11px] text-purple-400 mt-1 font-semibold">
                {totalOutliers > 0 ? 'Ngoài ngưỡng Q1 - 1.5*IQR' : '✓ Không phát hiện'}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Before / After Comparison Bar */}
      {history.length > 0 && history[history.length - 1]?.after_stats && (
        <div className="glass-card p-4 flex flex-wrap items-center justify-between gap-4 border-l-4 border-l-cyan-400">
          <div className="flex items-center space-x-3 text-xs">
            <span className="text-cyan-400 font-extrabold uppercase tracking-wider">Hiệu quả bước gần nhất:</span>
            <span className="text-slate-300 font-bold">{history[history.length - 1].action_name}</span>
          </div>
          <div className="flex items-center space-x-6 text-xs font-mono">
            <div>
              <span className="text-slate-500 text-[10px] block uppercase">Số dòng:</span>
              <span className="text-slate-300 font-bold">{history[history.length - 1].before_stats.rows}</span>
              <span className="text-cyan-400 mx-1.5 font-bold">→</span>
              <span className="text-white font-extrabold">{history[history.length - 1].after_stats.rows}</span>
            </div>
            <div>
              <span className="text-slate-500 text-[10px] block uppercase">Giá trị trống:</span>
              <span className="text-slate-300 font-bold">{history[history.length - 1].before_stats.null_count}</span>
              <span className="text-cyan-400 mx-1.5 font-bold">→</span>
              <span className="text-emerald-400 font-extrabold">{history[history.length - 1].after_stats.null_count}</span>
            </div>
          </div>
        </div>
      )}

      {/* Cleaning Actions Toolbar */}
      <div className="glass-panel p-5 space-y-3">
        <div className="flex items-center justify-between">
          <h3 className="font-extrabold text-white text-sm flex items-center space-x-2">
            <Sparkles className="w-4 h-4 text-cyan-400" />
            <span>Công Cụ Chuẩn Hóa Dữ Liệu</span>
          </h3>
          <span className="text-xs text-slate-400">Áp dụng tức thì trên tập dữ liệu phiên hiện tại</span>
        </div>

        <div className="flex flex-wrap gap-2.5 pt-1">
          <button
            onClick={() => handleAction('bulk_clean', {})}
            disabled={actionLoading}
            className="px-4 py-2 bg-gradient-to-r from-blue-600 to-cyan-500 text-white rounded-xl text-xs font-extrabold flex items-center space-x-2 shadow-[0_0_15px_rgba(47,139,255,0.4)] hover:brightness-110 transition-all"
          >
            <Sparkles className="w-3.5 h-3.5 text-white" />
            <span>Làm sạch tự động (Bulk Clean)</span>
          </button>

          <button
            onClick={() => handleAction('remove_duplicates', {})}
            disabled={actionLoading}
            className="px-3.5 py-2 glass-card text-xs font-bold text-slate-200 hover:text-white flex items-center space-x-1.5"
          >
            <Trash2 className="w-3.5 h-3.5 text-rose-400" />
            <span>Xóa trùng lặp</span>
          </button>

          <button
            onClick={() => { setSelectedColumn(columns[0] || ''); setActiveModal('fill_missing'); }}
            className="px-3.5 py-2 glass-card text-xs font-bold text-slate-200 hover:text-white"
          >
            <span>Điền / Xóa giá trị trống</span>
          </button>

          <button
            onClick={() => { setSelectedColumn(columns[0] || ''); setActiveModal('standardize_text'); }}
            className="px-3.5 py-2 glass-card text-xs font-bold text-slate-200 hover:text-white"
          >
            <span>Chuẩn hóa văn bản</span>
          </button>

          <button
            onClick={() => { setSelectedColumn(columns[0] || ''); setActiveModal('convert_type'); }}
            className="px-3.5 py-2 glass-card text-xs font-bold text-slate-200 hover:text-white"
          >
            <span>Chuyển đổi kiểu dữ liệu</span>
          </button>

          <button
            onClick={() => { setSelectedColumn(columns[0] || ''); setActiveModal('handle_outliers'); }}
            className="px-3.5 py-2 glass-card text-xs font-bold text-slate-200 hover:text-white"
          >
            <span>Xử lý ngoại lai (Outliers)</span>
          </button>

          <button
            onClick={() => { setSelectedColumn(columns[0] || ''); setNewColName(columns[0] || ''); setActiveModal('rename_column'); }}
            className="px-3.5 py-2 glass-card text-xs font-bold text-slate-200 hover:text-white flex items-center space-x-1.5"
          >
            <Edit2 className="w-3.5 h-3.5 text-slate-400" />
            <span>Đổi tên cột</span>
          </button>

          <button
            onClick={() => setActiveModal('filter_tool')}
            className="px-3.5 py-2 glass-card text-cyan-400 hover:text-cyan-300 border-cyan-500/40 text-xs font-extrabold flex items-center space-x-1.5 shadow-[0_0_12px_rgba(56,189,248,0.2)]"
          >
            <Filter className="w-3.5 h-3.5 text-cyan-400" />
            <span>Bộ lọc điều kiện</span>
          </button>
        </div>
      </div>

      {/* Main 2-Column Responsive Area (Desktop: 2 cols, Tablet: stack) */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left: Issues List (2 cols) */}
        <div className="lg:col-span-2 space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="font-extrabold text-white text-base">Danh Sách Vấn Đề Cần Khắc Phục</h3>
            <span className="text-xs text-slate-400 font-medium">Phân loại theo mức độ ưu tiên</span>
          </div>

          {profile?.issues.length === 0 ? (
            <div className="glass-panel p-8 text-center space-y-2 border-emerald-500/30">
              <CheckCircle2 className="w-10 h-10 text-emerald-400 mx-auto" />
              <h4 className="font-bold text-white text-sm">Dữ liệu sạch và không phát hiện bất thường</h4>
              <p className="text-xs text-slate-400">Không có dòng trùng lặp, giá trị trống hoặc lỗi định dạng cần xử lý.</p>
            </div>
          ) : (
            <div className="space-y-3">
              {profile?.issues.map((issue) => {
                const isHigh = issue.severity === 'high';
                const isMed = issue.severity === 'medium';
                return (
                  <div
                    key={issue.id}
                    className={`glass-card p-4 flex items-start justify-between space-x-4 ${
                      isHigh
                        ? 'border-rose-500/30 bg-rose-950/20'
                        : isMed
                        ? 'border-amber-500/30 bg-amber-950/20'
                        : 'border-white/[0.08]'
                    }`}
                  >
                    <div className="flex items-start space-x-3.5">
                      <div className={`p-2.5 rounded-xl mt-0.5 ${
                        isHigh ? 'bg-rose-500/20 text-rose-400 border border-rose-500/30' :
                        isMed ? 'bg-amber-500/20 text-amber-400 border border-amber-500/30' :
                        'bg-cyan-500/20 text-cyan-400 border border-cyan-500/30'
                      }`}>
                        {isHigh ? <AlertCircle className="w-4 h-4" /> : isMed ? <AlertTriangle className="w-4 h-4" /> : <Info className="w-4 h-4" />}
                      </div>
                      <div>
                        <div className="flex items-center space-x-2">
                          <h4 className="font-bold text-white text-sm">{issue.title}</h4>
                          <span className={`text-[10px] font-extrabold px-2 py-0.5 rounded-full uppercase ${
                            isHigh ? 'bg-rose-500/20 text-rose-300 border border-rose-500/40' :
                            isMed ? 'bg-amber-500/20 text-amber-300 border border-amber-500/40' :
                            'bg-cyan-500/20 text-cyan-300 border border-cyan-500/40'
                          }`}>
                            {isHigh ? 'Nghiêm trọng' : isMed ? 'Cảnh báo' : 'Thông tin'}
                          </span>
                        </div>
                        <p className="text-xs text-slate-300 mt-1">{issue.description}</p>
                      </div>
                    </div>

                    <button
                      onClick={() => {
                        if (issue.suggested_action === 'remove_duplicates') {
                          handleAction('remove_duplicates', {});
                        } else if (issue.suggested_action === 'fill_missing') {
                          setSelectedColumn(issue.column);
                          setActiveModal('fill_missing');
                        } else if (issue.suggested_action === 'trim_whitespace') {
                          handleAction('standardize_text', { column: issue.column, operation: 'trim' });
                        } else if (issue.suggested_action === 'convert_to_numeric') {
                          handleAction('convert_type', { column: issue.column, target_type: 'float' });
                        } else if (issue.suggested_action === 'handle_outliers') {
                          setSelectedColumn(issue.column);
                          setActiveModal('handle_outliers');
                        }
                      }}
                      className="text-xs font-bold text-cyan-300 hover:text-white bg-cyan-950/60 hover:bg-cyan-800/80 px-3.5 py-1.5 rounded-xl border border-cyan-600/50 shadow-[0_0_12px_rgba(56,189,248,0.2)] transition-all whitespace-nowrap"
                    >
                      Khắc phục nhanh
                    </button>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* Right: Transformation Log Panel (1 col) */}
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="font-extrabold text-white text-base">Nhật Ký Biến Đổi ({history.length})</h3>
            <span className="text-xs text-slate-400">Các bước đã áp dụng</span>
          </div>

          <div className="glass-panel p-4 space-y-3 max-h-[480px] overflow-y-auto">
            {history.length === 0 ? (
              <p className="text-xs text-slate-500 text-center py-10 font-medium">Chưa có thao tác làm sạch nào được thực hiện.</p>
            ) : (
              history.map((step, idx) => (
                <div key={idx} className="p-3 bg-white/[0.03] rounded-xl border border-white/[0.08] text-xs space-y-1.5">
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-cyan-300">
                      {idx + 1}. {step.action_name}
                    </span>
                    <span className="text-[10px] font-mono text-slate-500">
                      {new Date(step.timestamp * 1000).toLocaleTimeString()}
                    </span>
                  </div>
                  {step.params?.column && (
                    <div className="text-slate-400 text-[11px]">
                      Cột: <code className="bg-white/10 px-1 py-0.5 rounded text-white font-mono">{step.params.column}</code>
                    </div>
                  )}
                  {step.after_stats && (
                    <div className="text-[10px] text-slate-400 flex justify-between pt-1 border-t border-white/[0.06] font-mono">
                      <span>Dòng: {step.before_stats?.rows} → {step.after_stats?.rows}</span>
                      <span>Khuyết: {step.before_stats?.null_count} → {step.after_stats?.null_count}</span>
                    </div>
                  )}
                </div>
              ))
            )}
          </div>
        </div>
      </div>

      {/* Live Data Preview Table */}
      {previewData && (
        <div className="glass-panel p-6 space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="font-extrabold text-white text-base">Dữ Liệu Đang Làm Sạch (Xem trước)</h3>
              <p className="text-xs text-slate-400">
                Hiển thị trang {previewPage} / {Math.ceil(previewData.total_rows / 20) || 1} (Tổng: {previewData.total_rows.toLocaleString()} dòng)
              </p>
            </div>

            {/* Pagination Controls */}
            <div className="flex items-center space-x-2">
              <button
                onClick={() => setPreviewPage((p) => Math.max(1, p - 1))}
                disabled={previewPage === 1}
                className="p-1.5 glass-card text-slate-400 hover:text-white disabled:opacity-30"
              >
                <ChevronLeft className="w-4 h-4" />
              </button>
              <span className="text-xs font-mono font-bold text-slate-300 px-2">Trang {previewPage}</span>
              <button
                onClick={() => setPreviewPage((p) => p + 1)}
                disabled={previewPage * 20 >= previewData.total_rows}
                className="p-1.5 glass-card text-slate-400 hover:text-white disabled:opacity-30"
              >
                <ChevronRight className="w-4 h-4" />
              </button>
            </div>
          </div>

          <div className="border border-white/10 rounded-2xl overflow-x-auto max-h-80 bg-black/20">
            <table className="w-full text-left text-xs border-collapse">
              <thead className="bg-white/[0.06] text-slate-200 font-bold sticky top-0 z-10 backdrop-blur-md">
                <tr>
                  <th className="p-2.5 border-b border-r border-white/10 w-12 text-center text-slate-500">#</th>
                  {previewData.columns.map((c) => (
                    <th key={c} className="p-2.5 border-b border-r border-white/10 whitespace-nowrap min-w-[140px] text-cyan-300 font-mono">
                      {c}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-white/[0.05]">
                {previewData.records.map((r, rIdx) => (
                  <tr key={rIdx} className="hover:bg-white/[0.04] transition-colors">
                    <td className="p-2 border-r border-white/10 text-center text-slate-500 text-[11px] font-mono">
                      {(previewPage - 1) * 20 + rIdx + 1}
                    </td>
                    {previewData.columns.map((c) => (
                      <td key={c} className="p-2 border-r border-white/[0.05] whitespace-nowrap text-slate-300">
                        {r[c] !== null && r[c] !== undefined ? String(r[c]) : (
                          <span className="text-slate-600 italic">null</span>
                        )}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Modals for actions in dark glassmorphism */}

      {/* Modal: Fill Missing */}
      {activeModal === 'fill_missing' && (
        <div className="fixed inset-0 bg-black/70 backdrop-blur-md z-50 flex items-center justify-center p-4">
          <div className="glass-panel p-6 max-w-md w-full space-y-4 border border-white/20 shadow-2xl animate-scaleIn bg-[#0B1220]/95">
            <h4 className="font-extrabold text-white text-base">Xử Lý Giá Trị Khuyết Thiếu</h4>
            <div>
              <label className="text-xs font-bold text-slate-300 block mb-1">Chọn Cột:</label>
              <select
                value={selectedColumn}
                onChange={(e) => setSelectedColumn(e.target.value)}
                className="glass-input w-full text-xs p-2.5 font-medium"
              >
                {columns.map((c) => <option key={c} value={c} className="bg-slate-900 text-white">{c}</option>)}
              </select>
            </div>
            <div>
              <label className="text-xs font-bold text-slate-300 block mb-1">Phương pháp:</label>
              <select
                value={missingMethod}
                onChange={(e) => setMissingMethod(e.target.value as any)}
                className="glass-input w-full text-xs p-2.5 font-medium"
              >
                <option value="mean" className="bg-slate-900 text-white">Điền giá trị trung bình (Mean - cho cột số)</option>
                <option value="median" className="bg-slate-900 text-white">Điền giá trị trung vị (Median - cho cột số)</option>
                <option value="mode" className="bg-slate-900 text-white">Điền giá trị xuất hiện nhiều nhất (Mode)</option>
                <option value="constant" className="bg-slate-900 text-white">Điền giá trị cố định tự nhập</option>
                <option value="drop" className="bg-slate-900 text-white">Xóa các dòng bị thiếu giá trị này</option>
              </select>
            </div>
            {missingMethod === 'constant' && (
              <div>
                <label className="text-xs font-bold text-slate-300 block mb-1">Giá trị cố định:</label>
                <input
                  type="text"
                  value={constantVal}
                  onChange={(e) => setConstantVal(e.target.value)}
                  className="glass-input w-full text-xs p-2.5"
                  placeholder="Nhập giá trị cần điền..."
                />
              </div>
            )}
            <div className="flex justify-end space-x-2 pt-2 border-t border-white/10">
              <button onClick={() => setActiveModal(null)} className="px-4 py-2 text-xs font-bold text-slate-400 hover:text-white">
                Hủy
              </button>
              <button
                onClick={() => handleAction('fill_missing', { column: selectedColumn, method: missingMethod, value: constantVal })}
                disabled={actionLoading || !selectedColumn}
                className="px-5 py-2 text-xs font-extrabold text-white active-nav-glow rounded-xl"
              >
                Áp dụng
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Modal: Standardize Text */}
      {activeModal === 'standardize_text' && (
        <div className="fixed inset-0 bg-black/70 backdrop-blur-md z-50 flex items-center justify-center p-4">
          <div className="glass-panel p-6 max-w-md w-full space-y-4 border border-white/20 shadow-2xl bg-[#0B1220]/95">
            <h4 className="font-extrabold text-white text-base">Chuẩn Hóa Văn Bản</h4>
            <div>
              <label className="text-xs font-bold text-slate-300 block mb-1">Chọn Cột:</label>
              <select
                value={selectedColumn}
                onChange={(e) => setSelectedColumn(e.target.value)}
                className="glass-input w-full text-xs p-2.5 font-medium"
              >
                {columns.map((c) => <option key={c} value={c} className="bg-slate-900 text-white">{c}</option>)}
              </select>
            </div>
            <div>
              <label className="text-xs font-bold text-slate-300 block mb-1">Thao tác định dạng:</label>
              <select
                value={textOp}
                onChange={(e) => setTextOp(e.target.value as any)}
                className="glass-input w-full text-xs p-2.5 font-medium"
              >
                <option value="trim" className="bg-slate-900 text-white">Cắt khoảng trắng thừa ở đầu và cuối (Trim)</option>
                <option value="lowercase" className="bg-slate-900 text-white">Chuyển sang chữ thường toàn bộ (lowercase)</option>
                <option value="uppercase" className="bg-slate-900 text-white">Chuyển sang CHỮ HOA toàn bộ (UPPERCASE)</option>
                <option value="titlecase" className="bg-slate-900 text-white">Viết hoa chữ cái đầu mỗi từ (Title Case)</option>
              </select>
            </div>
            <div className="flex justify-end space-x-2 pt-2 border-t border-white/10">
              <button onClick={() => setActiveModal(null)} className="px-4 py-2 text-xs font-bold text-slate-400 hover:text-white">
                Hủy
              </button>
              <button
                onClick={() => handleAction('standardize_text', { column: selectedColumn, operation: textOp })}
                disabled={actionLoading || !selectedColumn}
                className="px-5 py-2 text-xs font-extrabold text-white active-nav-glow rounded-xl"
              >
                Áp dụng
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Modal: Convert Type */}
      {activeModal === 'convert_type' && (
        <div className="fixed inset-0 bg-black/70 backdrop-blur-md z-50 flex items-center justify-center p-4">
          <div className="glass-panel p-6 max-w-md w-full space-y-4 border border-white/20 shadow-2xl bg-[#0B1220]/95">
            <h4 className="font-extrabold text-white text-base">Chuyển Đổi Kiểu Dữ Liệu</h4>
            <div>
              <label className="text-xs font-bold text-slate-300 block mb-1">Chọn Cột:</label>
              <select
                value={selectedColumn}
                onChange={(e) => setSelectedColumn(e.target.value)}
                className="glass-input w-full text-xs p-2.5 font-medium"
              >
                {columns.map((c) => <option key={c} value={c} className="bg-slate-900 text-white">{c}</option>)}
              </select>
            </div>
            <div>
              <label className="text-xs font-bold text-slate-300 block mb-1">Kiểu dữ liệu đích:</label>
              <select
                value={targetType}
                onChange={(e) => setTargetType(e.target.value)}
                className="glass-input w-full text-xs p-2.5 font-medium"
              >
                <option value="float" className="bg-slate-900 text-white">Số thực / Tiền tệ (Float - tự làm sạch ký hiệu $, ₫, dấu phẩy)</option>
                <option value="integer" className="bg-slate-900 text-white">Số nguyên (Integer)</option>
                <option value="datetime" className="bg-slate-900 text-white">Ngày tháng (Datetime - YYYY-MM-DD)</option>
                <option value="boolean" className="bg-slate-900 text-white">Đúng / Sai (Boolean)</option>
                <option value="string" className="bg-slate-900 text-white">Văn bản (String)</option>
              </select>
            </div>
            <div className="flex justify-end space-x-2 pt-2 border-t border-white/10">
              <button onClick={() => setActiveModal(null)} className="px-4 py-2 text-xs font-bold text-slate-400 hover:text-white">
                Hủy
              </button>
              <button
                onClick={() => handleAction('convert_type', { column: selectedColumn, target_type: targetType })}
                disabled={actionLoading || !selectedColumn}
                className="px-5 py-2 text-xs font-extrabold text-white active-nav-glow rounded-xl"
              >
                Áp dụng
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Modal: Outliers */}
      {activeModal === 'handle_outliers' && (
        <div className="fixed inset-0 bg-black/70 backdrop-blur-md z-50 flex items-center justify-center p-4">
          <div className="glass-panel p-6 max-w-md w-full space-y-4 border border-white/20 shadow-2xl bg-[#0B1220]/95">
            <h4 className="font-extrabold text-white text-base">Xử Lý Giá Trị Ngoại Lai (Outliers)</h4>
            <div>
              <label className="text-xs font-bold text-slate-300 block mb-1">Chọn Cột Số:</label>
              <select
                value={selectedColumn}
                onChange={(e) => setSelectedColumn(e.target.value)}
                className="glass-input w-full text-xs p-2.5 font-medium"
              >
                {columns.map((c) => <option key={c} value={c} className="bg-slate-900 text-white">{c}</option>)}
              </select>
            </div>
            <div>
              <label className="text-xs font-bold text-slate-300 block mb-1">Phương pháp xử lý:</label>
              <select
                value={outlierMethod}
                onChange={(e) => setOutlierMethod(e.target.value as any)}
                className="glass-input w-full text-xs p-2.5 font-medium"
              >
                <option value="winsorize" className="bg-slate-900 text-white">Cắt ngưỡng (Winsorize - đưa về biên IQR)</option>
                <option value="drop" className="bg-slate-900 text-white">Xóa các dòng chứa giá trị ngoại lai</option>
                <option value="flag" className="bg-slate-900 text-white">Tạo cột mới đánh dấu ngoại lai (Flag)</option>
              </select>
            </div>
            <div className="flex justify-end space-x-2 pt-2 border-t border-white/10">
              <button onClick={() => setActiveModal(null)} className="px-4 py-2 text-xs font-bold text-slate-400 hover:text-white">
                Hủy
              </button>
              <button
                onClick={() => handleAction('handle_outliers', { column: selectedColumn, method: outlierMethod })}
                disabled={actionLoading || !selectedColumn}
                className="px-5 py-2 text-xs font-extrabold text-white active-nav-glow rounded-xl"
              >
                Áp dụng
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Modal: Rename Column */}
      {activeModal === 'rename_column' && (
        <div className="fixed inset-0 bg-black/70 backdrop-blur-md z-50 flex items-center justify-center p-4">
          <div className="glass-panel p-6 max-w-md w-full space-y-4 border border-white/20 shadow-2xl bg-[#0B1220]/95">
            <h4 className="font-extrabold text-white text-base">Đổi Tên Cột Dữ Liệu</h4>
            <div>
              <label className="text-xs font-bold text-slate-300 block mb-1">Chọn Cột Cần Đổi:</label>
              <select
                value={selectedColumn}
                onChange={(e) => { setSelectedColumn(e.target.value); setNewColName(e.target.value); }}
                className="glass-input w-full text-xs p-2.5 font-medium"
              >
                {columns.map((c) => <option key={c} value={c} className="bg-slate-900 text-white">{c}</option>)}
              </select>
            </div>
            <div>
              <label className="text-xs font-bold text-slate-300 block mb-1">Tên mới:</label>
              <input
                type="text"
                value={newColName}
                onChange={(e) => setNewColName(e.target.value)}
                className="glass-input w-full text-xs p-2.5 font-mono"
                placeholder="Nhập tên cột mới..."
              />
            </div>
            <div className="flex justify-end space-x-2 pt-2 border-t border-white/10">
              <button onClick={() => setActiveModal(null)} className="px-4 py-2 text-xs font-bold text-slate-400 hover:text-white">
                Hủy
              </button>
              <button
                onClick={() => handleAction('rename_column', { old_name: selectedColumn, new_name: newColName })}
                disabled={actionLoading || !selectedColumn || !newColName}
                className="px-5 py-2 text-xs font-extrabold text-white active-nav-glow rounded-xl"
              >
                Lưu tên mới
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Modal: Filter Tool */}
      {activeModal === 'filter_tool' && (
        <div className="fixed inset-0 bg-black/70 backdrop-blur-md z-50 flex items-center justify-center p-4">
          <div className="glass-panel p-6 max-w-xl w-full space-y-4 border border-white/20 shadow-2xl max-h-[85vh] overflow-y-auto bg-[#0B1220]/95">
            <div className="flex items-center justify-between">
              <h4 className="font-extrabold text-white text-base">Bộ Lọc Điều Kiện Dữ Liệu</h4>
              <div className="flex items-center space-x-1 bg-white/[0.06] p-1 rounded-xl text-xs">
                <button
                  onClick={() => setFilterLogic('AND')}
                  className={`px-3 py-1 rounded-lg font-bold ${filterLogic === 'AND' ? 'active-nav-glow text-white' : 'text-slate-400'}`}
                >
                  VÀ (AND)
                </button>
                <button
                  onClick={() => setFilterLogic('OR')}
                  className={`px-3 py-1 rounded-lg font-bold ${filterLogic === 'OR' ? 'active-nav-glow text-white' : 'text-slate-400'}`}
                >
                  HOẶC (OR)
                </button>
              </div>
            </div>

            <div className="space-y-3">
              {filterConditions.map((cond, idx) => (
                <div key={idx} className="p-3 bg-white/[0.03] rounded-2xl border border-white/[0.08] text-xs space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-slate-300">Điều kiện {idx + 1}:</span>
                    {filterConditions.length > 1 && (
                      <button onClick={() => removeFilterCondition(idx)} className="text-rose-400 hover:text-rose-300 font-bold">
                        Xóa
                      </button>
                    )}
                  </div>
                  <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
                    <select
                      value={cond.column}
                      onChange={(e) => {
                        const updated = [...filterConditions];
                        updated[idx].column = e.target.value;
                        setFilterConditions(updated);
                      }}
                      className="glass-input p-2 font-medium"
                    >
                      {columns.map((c) => <option key={c} value={c} className="bg-slate-900 text-white">{c}</option>)}
                    </select>

                    <select
                      value={cond.operator}
                      onChange={(e) => {
                        const updated = [...filterConditions];
                        updated[idx].operator = e.target.value;
                        setFilterConditions(updated);
                      }}
                      className="glass-input p-2 font-medium"
                    >
                      <option value="equals" className="bg-slate-900 text-white">Bằng (=)</option>
                      <option value="not_equals" className="bg-slate-900 text-white">Khác (≠)</option>
                      <option value="contains" className="bg-slate-900 text-white">Chứa chuỗi</option>
                      <option value="greater" className="bg-slate-900 text-white">Lớn hơn (&gt;)</option>
                      <option value="less" className="bg-slate-900 text-white">Nhỏ hơn (&lt;)</option>
                      <option value="in" className="bg-slate-900 text-white">Trong danh sách (phân tách bởi phẩy)</option>
                      <option value="is_null" className="bg-slate-900 text-white">Giá trị trống (NULL)</option>
                      <option value="not_null" className="bg-slate-900 text-white">Không trống</option>
                    </select>

                    <input
                      type="text"
                      value={cond.value || ''}
                      onChange={(e) => {
                        const updated = [...filterConditions];
                        updated[idx].value = e.target.value;
                        setFilterConditions(updated);
                      }}
                      className="glass-input p-2"
                      placeholder="Giá trị so khớp..."
                      disabled={cond.operator === 'is_null' || cond.operator === 'not_null'}
                    />
                  </div>
                </div>
              ))}
            </div>

            <button
              onClick={addFilterCondition}
              className="w-full py-2.5 border border-dashed border-white/20 hover:border-cyan-400 rounded-xl text-xs font-bold text-cyan-400 flex items-center justify-center space-x-1.5 transition-colors"
            >
              <Plus className="w-3.5 h-3.5" />
              <span>Thêm điều kiện lọc</span>
            </button>

            <div className="flex justify-end space-x-2 pt-2 border-t border-white/10">
              <button onClick={() => setActiveModal(null)} className="px-4 py-2 text-xs font-bold text-slate-400 hover:text-white">
                Hủy
              </button>
              <button
                onClick={handleApplyFilter}
                disabled={actionLoading}
                className="px-5 py-2 text-xs font-extrabold text-white active-nav-glow rounded-xl"
              >
                Áp dụng bộ lọc
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default CleanPage;
