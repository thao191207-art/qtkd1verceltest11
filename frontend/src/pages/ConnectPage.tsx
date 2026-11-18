import React, { useState, useRef } from 'react';
import {
  UploadCloud, FileSpreadsheet, FileText, AlertCircle, ArrowRight,
  Eye, RefreshCw, X, Table2, Layers
} from 'lucide-react';
import ApiService, { type SourceItemConfig } from '../services/api';

interface FileInfo {
  file_name: string;
  file_size: number;
  file_path: string;
  extension: string;
  sheets: string[];
  default_sheet: string;
  sheets_info: Record<string, {
    row_count: number;
    column_count: number;
    header_row?: number;
    columns: string[];
    column_types: Record<string, string>;
    preview: Record<string, any>[];
    is_formula_sheet?: boolean;
    warning?: string | null;
  }>;
  selectedSheet: string;
  headerRow: number;
  selected: boolean;
  typeOverrides: Record<string, string>;
}

interface ConnectPageProps {
  sessionId: string;
  onContinue: () => void;
  onDatasetLoaded: (stats: { rows: number; cols: number; qualityScore: number }) => void;
}

const DATA_TYPES = [
  { value: 'string', label: 'Văn bản (String)' },
  { value: 'category', label: 'Danh mục (Category)' },
  { value: 'number', label: 'Số / Tiền tệ (Number)' },
  { value: 'integer', label: 'Số nguyên (Integer)' },
  { value: 'float', label: 'Số thực (Float)' },
  { value: 'percentage', label: 'Tỷ lệ % (Percentage)' },
  { value: 'date', label: 'Ngày tháng (Date)' },
  { value: 'datetime', label: 'Ngày & Giờ (Datetime)' },
  { value: 'flag', label: 'Cờ Đúng/Sai (Flag)' },
  { value: 'boolean', label: 'Đúng / Sai (Boolean)' },
  { value: 'identifier', label: 'Mã định danh (ID)' },
  { value: 'free_text', label: 'Văn bản tự do (Text)' },
];

export const ConnectPage: React.FC<ConnectPageProps> = ({
  sessionId,
  onContinue,
  onDatasetLoaded,
}) => {
  const [filesList, setFilesList] = useState<FileInfo[]>([]);
  const [isDragging, setIsDragging] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [initializing, setInitializing] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [activePreviewFileIdx, setActivePreviewFileIdx] = useState<number | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const formatFileSize = (bytes: number): string => {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
  };

  const handleFilesSelected = async (files: FileList | File[]) => {
    const validFiles: File[] = [];
    setErrorMessage(null);

    const allowed = ['.xlsx', '.xls', '.csv', '.json'];
    for (let i = 0; i < files.length; i++) {
      const f = files[i];
      const ext = f.name.substring(f.name.lastIndexOf('.')).toLowerCase();
      if (!allowed.includes(ext)) {
        setErrorMessage(`Tệp "${f.name}" không hợp lệ. Chỉ hỗ trợ .xlsx, .xls, .csv, và .json.`);
        return;
      }
      if (f.size === 0) {
        setErrorMessage(`Tệp "${f.name}" là tệp rỗng (0 bytes). Vui lòng chọn tệp có dữ liệu.`);
        return;
      }
      if (f.size > 50 * 1024 * 1024) {
        setErrorMessage(`Tệp "${f.name}" vượt quá giới hạn 50 MB.`);
        return;
      }
      validFiles.push(f);
    }

    if (validFiles.length === 0) return;

    try {
      setUploading(true);
      const res = await ApiService.uploadFiles(sessionId, validFiles);
      
      const newItems: FileInfo[] = res.files.map((item: any) => {
        const selSheet = item.default_sheet || (item.sheets.length > 0 ? item.sheets[0] : '');
        const sheetData = item.sheets_info ? item.sheets_info[selSheet] : null;
        return {
          ...item,
          selectedSheet: selSheet,
          headerRow: sheetData?.header_row ?? item.header_row ?? 0,
          selected: true,
          typeOverrides: { ...(sheetData?.column_types || item.column_types || {}) },
        };
      });

      setFilesList((prev) => [...prev, ...newItems]);
      if (activePreviewFileIdx === null && newItems.length > 0) {
        setActivePreviewFileIdx(filesList.length);
      }
    } catch (err: any) {
      setErrorMessage(err.response?.data?.detail || err.message || 'Lỗi tải lên tệp.');
    } finally {
      setUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = '';
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files) {
      handleFilesSelected(e.dataTransfer.files);
    }
  };

  const handleSheetChange = (fileIdx: number, newSheet: string) => {
    setFilesList((prev) => {
      const updated = [...prev];
      const item = updated[fileIdx];
      item.selectedSheet = newSheet;
      const sheetData = item.sheets_info[newSheet];
      if (sheetData) {
        if (sheetData.header_row !== undefined) {
          item.headerRow = sheetData.header_row;
        }
        item.typeOverrides = { ...(sheetData.column_types || {}) };
      }
      return updated;
    });
  };

  const handleHeaderRowChange = (fileIdx: number, rowNum: number) => {
    setFilesList((prev) => {
      const updated = [...prev];
      updated[fileIdx].headerRow = Math.max(0, rowNum);
      return updated;
    });
  };

  const handleTypeOverride = (fileIdx: number, colName: string, newType: string) => {
    setFilesList((prev) => {
      const updated = [...prev];
      updated[fileIdx].typeOverrides = {
        ...updated[fileIdx].typeOverrides,
        [colName]: newType,
      };
      return updated;
    });
  };

  const toggleSelectFile = (idx: number) => {
    setFilesList((prev) => {
      const updated = [...prev];
      updated[idx].selected = !updated[idx].selected;
      return updated;
    });
  };

  const removeFile = (idx: number) => {
    setFilesList((prev) => prev.filter((_, i) => i !== idx));
    if (activePreviewFileIdx === idx) {
      setActivePreviewFileIdx(null);
    }
  };

  const handleProceed = async () => {
    const selectedFiles = filesList.filter((f) => f.selected);
    if (selectedFiles.length === 0) {
      setErrorMessage('Vui lòng chọn ít nhất một tệp/bảng tính để tiếp tục.');
      return;
    }

    try {
      setInitializing(true);
      setErrorMessage(null);

      const sources: SourceItemConfig[] = selectedFiles.map((f) => ({
        file_path: f.file_path,
        sheet_name: f.selectedSheet,
        header_row: f.headerRow,
      }));

      const combinedOverrides: Record<string, string> = {};
      selectedFiles.forEach((f) => {
        Object.assign(combinedOverrides, f.typeOverrides);
      });

      const res = await ApiService.initializeDataset({
        session_id: sessionId,
        sources,
        type_overrides: combinedOverrides,
      });

      onDatasetLoaded({
        rows: res.total_rows,
        cols: res.total_columns,
        qualityScore: res.quality_score,
      });

      onContinue();
    } catch (err: any) {
      setErrorMessage(err.response?.data?.detail || err.message || 'Không thể hợp nhất dữ liệu.');
    } finally {
      setInitializing(false);
    }
  };

  const activeFile = activePreviewFileIdx !== null ? filesList[activePreviewFileIdx] : null;
  const activeSheetData = activeFile ? activeFile.sheets_info[activeFile.selectedSheet] : null;

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-8 animate-fadeIn">
      {/* Page Title & Intro */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center space-x-2">
            <span className="text-[10px] font-extrabold uppercase tracking-widest text-cyan-400 bg-cyan-950/70 border border-cyan-800/60 px-2.5 py-0.5 rounded-full">
              BƯỚC 1: KẾT NỐI
            </span>
          </div>
          <h2 className="text-2xl font-black text-white mt-1 tracking-tight">Chọn Nguồn Dữ Liệu Thực Tế</h2>
          <p className="text-slate-400 mt-1 text-xs">
            Hỗ trợ kéo-thả các tệp .xlsx, .xls, .csv, .json. Hệ thống sẽ phân tích cấu trúc, nhận diện sheet và suy luận kiểu dữ liệu tự động.
          </p>
        </div>

        {filesList.length > 0 && (
          <button
            onClick={handleProceed}
            disabled={initializing || filesList.filter((f) => f.selected).length === 0}
            className="flex items-center space-x-2.5 active-nav-glow px-6 py-2.5 rounded-xl font-bold text-xs cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed transition-all"
          >
            {initializing ? (
              <>
                <RefreshCw className="w-4 h-4 animate-spin text-white" />
                <span>Đang hợp nhất dữ liệu...</span>
              </>
            ) : (
              <>
                <span>Tiếp tục sang Làm sạch</span>
                <ArrowRight className="w-4 h-4 text-white" />
              </>
            )}
          </button>
        )}
      </div>

      {/* Error Alert */}
      {errorMessage && (
        <div className="p-4 bg-rose-950/60 border border-rose-600/40 rounded-2xl flex items-start space-x-3 text-rose-200 text-xs shadow-glass">
          <AlertCircle className="w-4 h-4 text-rose-400 flex-shrink-0 mt-0.5" />
          <div className="flex-1">
            <span className="font-bold text-rose-300">Lỗi kiểm tra tệp: </span>
            {errorMessage}
          </div>
          <button onClick={() => setErrorMessage(null)} className="text-rose-400 hover:text-rose-200 font-bold">
            <X className="w-4 h-4" />
          </button>
        </div>
      )}

      {/* Large Glass Drop Zone with Glowing Dashed Border */}
      <div
        onDragOver={(e) => { e.preventDefault(); setIsDragging(true); }}
        onDragLeave={() => setIsDragging(false)}
        onDrop={handleDrop}
        onClick={() => fileInputRef.current?.click()}
        className={`glass-panel border-2 border-dashed p-12 text-center cursor-pointer transition-all duration-300 group ${
          isDragging
            ? 'border-cyan-400 bg-cyan-950/30 shadow-[0_0_40px_rgba(56,189,248,0.3)] scale-[1.01]'
            : 'border-white/15 hover:border-cyan-400/80 hover:bg-white/[0.04] shadow-glass'
        }`}
      >
        <input
          ref={fileInputRef}
          type="file"
          multiple
          accept=".xlsx,.xls,.csv,.json"
          className="hidden"
          onChange={(e) => e.target.files && handleFilesSelected(e.target.files)}
        />
        <div className="flex flex-col items-center justify-center space-y-4">
          <div className="w-16 h-16 rounded-2xl bg-gradient-to-tr from-blue-600/30 to-cyan-400/30 border border-cyan-400/40 flex items-center justify-center text-cyan-300 shadow-[0_0_20px_rgba(47,139,255,0.4)] group-hover:scale-110 transition-transform duration-300">
            <UploadCloud className="w-8 h-8" />
          </div>
          <div>
            <h3 className="font-bold text-white text-base tracking-wide">
              {uploading ? 'Đang đọc và kiểm tra tệp...' : 'Kéo thả tệp dữ liệu vào đây hoặc nhấp để chọn'}
            </h3>
            <p className="text-xs text-slate-400 mt-1.5">
              Hỗ trợ Microsoft Excel (.xlsx, .xls), CSV (.csv) và JSON (.json)
            </p>
            <div className="flex items-center justify-center space-x-2 mt-2">
              <span className="text-[11px] font-semibold text-slate-500 bg-white/[0.04] px-2.5 py-0.5 rounded-full border border-white/[0.08]">
                Dung lượng tối đa: 50 MB / tệp
              </span>
              <span className="text-[11px] font-semibold text-cyan-400 bg-cyan-950/60 px-2.5 py-0.5 rounded-full border border-cyan-800/60">
                Cho phép kết hợp nhiều tệp
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Uploaded File Cards Grid */}
      {filesList.length > 0 && (
        <div className="space-y-6">
          <div className="flex items-center justify-between">
            <h3 className="text-base font-extrabold text-white flex items-center space-x-2">
              <span>Danh Sách Tệp Đã Nạp ({filesList.length})</span>
            </h3>
            <span className="text-xs text-slate-400">
              Chọn nguồn dữ liệu cần đưa vào phân tích
            </span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {filesList.map((file, idx) => {
              const sheetData = file.sheets_info[file.selectedSheet] || {
                row_count: 0,
                column_count: 0,
                columns: [],
              };
              const isSelected = file.selected;
              const isCurrentPreview = activePreviewFileIdx === idx;

              return (
                <div
                  key={idx}
                  className={`glass-card p-5 flex flex-col justify-between relative overflow-hidden transition-all ${
                    isSelected
                      ? 'border-blue-500/40 bg-white/[0.06] shadow-[0_0_20px_rgba(47,139,255,0.15)]'
                      : 'border-white/[0.08] opacity-50'
                  } ${isCurrentPreview ? 'ring-2 ring-cyan-400/80 border-transparent shadow-[0_0_25px_rgba(56,189,248,0.3)]' : ''}`}
                >
                  <div>
                    {/* Card Header */}
                    <div className="flex items-start justify-between">
                      <div className="flex items-center space-x-3">
                        <input
                          type="checkbox"
                          checked={isSelected}
                          onChange={() => toggleSelectFile(idx)}
                          className="w-4 h-4 rounded text-blue-500 bg-slate-900 border-white/20 focus:ring-cyan-500 cursor-pointer"
                        />
                        <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-blue-600/30 to-cyan-500/30 border border-cyan-400/30 flex items-center justify-center text-cyan-300">
                          {file.extension === '.json' ? (
                            <FileText className="w-5 h-5" />
                          ) : (
                            <FileSpreadsheet className="w-5 h-5" />
                          )}
                        </div>
                        <div className="min-w-0">
                          <h4 className="font-bold text-white text-sm truncate max-w-[170px]" title={file.file_name}>
                            {file.file_name}
                          </h4>
                          <span className="text-[11px] font-mono text-slate-400">{formatFileSize(file.file_size)}</span>
                        </div>
                      </div>

                      <button
                        onClick={() => removeFile(idx)}
                        className="text-slate-400 hover:text-rose-400 transition-colors p-1"
                        title="Xóa tệp"
                      >
                        <X className="w-4 h-4" />
                      </button>
                    </div>

                    {/* Stats pills */}
                    <div className="grid grid-cols-2 gap-2 mt-4 text-xs bg-white/[0.03] p-2.5 rounded-xl border border-white/[0.08]">
                      <div>
                        <span className="text-slate-400 block text-[10px] uppercase font-bold tracking-wider">Số dòng</span>
                        <span className="font-extrabold font-mono text-white text-sm">{sheetData.row_count.toLocaleString()}</span>
                      </div>
                      <div>
                        <span className="text-slate-400 block text-[10px] uppercase font-bold tracking-wider">Số cột</span>
                        <span className="font-extrabold font-mono text-cyan-300 text-sm">{sheetData.column_count}</span>
                      </div>
                    </div>

                    {/* Sheet Picker for Excel */}
                    {file.sheets.length > 1 && (
                      <div className="mt-3">
                        <label className="text-[11px] font-bold text-slate-300 block mb-1">
                          Chọn Sheet phân tích:
                        </label>
                        <select
                          value={file.selectedSheet}
                          onChange={(e) => handleSheetChange(idx, e.target.value)}
                          className={`glass-input w-full text-xs p-2 font-medium ${
                            sheetData.is_formula_sheet ? 'border-amber-500/50 text-amber-200' : 'text-white'
                          }`}
                        >
                          {file.sheets.map((s) => {
                            const sInfo = file.sheets_info[s];
                            const isFormula = sInfo?.is_formula_sheet;
                            const isRaw = s.toLowerCase().includes('dữ liệu') || s.toLowerCase().includes('data');
                            return (
                              <option key={s} value={s} className="bg-slate-900 text-white">
                                {s} ({sInfo?.row_count?.toLocaleString() || 0} dòng) {isRaw ? '★ NGUỒN GỐC' : isFormula ? '⚠️ Công thức' : ''}
                              </option>
                            );
                          })}
                        </select>
                        {sheetData.is_formula_sheet && (
                          <div className="mt-1.5 p-2 bg-amber-950/60 border border-amber-600/40 rounded-lg text-[10px] text-amber-200 flex items-start space-x-1.5">
                            <AlertCircle className="w-3.5 h-3.5 text-amber-400 flex-shrink-0 mt-0.5" />
                            <span>{sheetData.warning || "Sheet này là bảng tóm tắt/công thức. Vui lòng chọn sheet có dữ liệu giao dịch gốc."}</span>
                          </div>
                        )}
                      </div>
                    )}

                    {/* Detected columns summary pill */}
                    {sheetData.columns && sheetData.columns.length > 0 && (
                      <div className="mt-2.5 pt-2 border-t border-white/[0.05] text-[11px] text-slate-400">
                        <span className="text-slate-500 text-[10px] uppercase font-bold block mb-1">Cột đã phát hiện ({sheetData.columns.length}):</span>
                        <div className="flex flex-wrap gap-1 max-h-12 overflow-hidden">
                          {sheetData.columns.slice(0, 6).map((cName: string) => (
                            <span key={cName} className="px-1.5 py-0.5 rounded bg-white/[0.04] border border-white/[0.08] text-[10px] text-slate-300 font-mono">
                              {cName}
                            </span>
                          ))}
                          {sheetData.columns.length > 6 && (
                            <span className="text-[10px] text-slate-500 font-mono self-center">
                              +{sheetData.columns.length - 6} nữa
                            </span>
                          )}
                        </div>
                      </div>
                    )}

                    {/* Header Row Index */}
                    <div className="mt-3 flex items-center justify-between text-xs">
                      <span className="text-slate-300 font-medium">Dòng tiêu đề (Header):</span>
                      <div className="flex items-center space-x-1.5">
                        <input
                          type="number"
                          min={0}
                          max={10}
                          value={file.headerRow}
                          onChange={(e) => handleHeaderRowChange(idx, parseInt(e.target.value) || 0)}
                          className="glass-input w-12 text-center py-1 px-1 font-mono font-bold text-xs"
                        />
                        <span className="text-slate-500 text-[10px]">(chỉ số 0)</span>
                      </div>
                    </div>
                  </div>

                  {/* Card Footer Actions */}
                  <div className="mt-4 pt-3 border-t border-white/[0.08] flex items-center justify-between">
                    <button
                      onClick={() => setActivePreviewFileIdx(idx)}
                      className={`text-xs font-bold px-3 py-1.5 rounded-xl flex items-center space-x-1.5 transition-all ${
                        isCurrentPreview
                          ? 'bg-cyan-500 text-white shadow-[0_0_12px_rgba(56,189,248,0.5)]'
                          : 'bg-white/[0.06] hover:bg-white/[0.12] text-slate-300 border border-white/10'
                      }`}
                    >
                      <Eye className="w-3.5 h-3.5" />
                      <span>Xem & Cấu hình</span>
                    </button>
                    <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${
                      isSelected ? 'text-emerald-400 bg-emerald-950/60 border border-emerald-800/60' : 'text-slate-500'
                    }`}>
                      {isSelected ? '✓ Đã chọn' : 'Bỏ qua'}
                    </span>
                  </div>
                </div>
              );
            })}
          </div>

          {/* Active File Preview & Column Types Config */}
          {activeFile && activeSheetData && (
            <div className="glass-panel p-6 space-y-6">
              <div className="flex items-center justify-between border-b border-white/[0.08] pb-4">
                <div className="flex items-center space-x-3">
                  <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-blue-600/30 to-cyan-500/30 border border-cyan-400/30 flex items-center justify-center text-cyan-300">
                    <Table2 className="w-5 h-5" />
                  </div>
                  <div>
                    <h4 className="font-extrabold text-white text-base">
                      Cấu Hình & Xem Trước: {activeFile.file_name}
                      {activeFile.selectedSheet && ` [${activeFile.selectedSheet}]`}
                    </h4>
                    <p className="text-xs text-slate-400">
                      Xác nhận kiểu dữ liệu từng cột và kiểm tra 20 dòng đầu tiên trước khi đưa vào phân tích.
                    </p>
                  </div>
                </div>
              </div>

              {/* Column Types Grid */}
              <div>
                <h5 className="text-[11px] font-extrabold uppercase tracking-wider text-slate-400 mb-3 flex items-center space-x-2">
                  <Layers className="w-3.5 h-3.5 text-cyan-400" />
                  <span>Xác Nhận Kiểu Dữ Liệu Tự Động ({activeSheetData.columns.length} cột)</span>
                </h5>
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 max-h-56 overflow-y-auto p-1">
                  {activeSheetData.columns.map((colName) => {
                    const currentType = activeFile.typeOverrides[colName] || 'string';
                    return (
                      <div key={colName} className="p-3 bg-white/[0.03] rounded-xl border border-white/[0.08] text-xs space-y-1.5">
                        <span className="font-bold text-slate-200 block truncate" title={colName}>
                          {colName}
                        </span>
                        <select
                          value={currentType}
                          onChange={(e) => handleTypeOverride(activePreviewFileIdx!, colName, e.target.value)}
                          className="glass-input w-full text-xs py-1 px-2 font-medium"
                        >
                          {DATA_TYPES.map((t) => (
                            <option key={t.value} value={t.value} className="bg-slate-900 text-white">{t.label}</option>
                          ))}
                        </select>
                      </div>
                    );
                  })}
                </div>
              </div>

              {/* Live Preview Table */}
              <div>
                <h5 className="text-[11px] font-extrabold uppercase tracking-wider text-slate-400 mb-2">
                  Xem trước 20 dòng đầu tiên:
                </h5>
                <div className="border border-white/10 rounded-2xl overflow-x-auto max-h-72 bg-black/20">
                  <table className="w-full text-left text-xs border-collapse">
                    <thead className="bg-white/[0.06] text-slate-200 font-bold sticky top-0 z-10 backdrop-blur-md">
                      <tr>
                        <th className="p-2.5 border-b border-r border-white/10 w-12 text-center text-slate-500">#</th>
                        {activeSheetData.columns.map((col) => (
                          <th key={col} className="p-2.5 border-b border-r border-white/10 whitespace-nowrap min-w-[140px] text-cyan-300 font-mono">
                            {col}
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-white/[0.05]">
                      {activeSheetData.preview.length === 0 ? (
                        <tr>
                          <td colSpan={activeSheetData.columns.length + 1} className="p-6 text-center text-slate-500">
                            Không có dữ liệu xem trước.
                          </td>
                        </tr>
                      ) : (
                        activeSheetData.preview.map((row, rIdx) => (
                          <tr key={rIdx} className="hover:bg-white/[0.04] transition-colors">
                            <td className="p-2 border-r border-white/10 text-center text-slate-500 text-[11px] font-mono">
                              {rIdx + 1}
                            </td>
                            {activeSheetData.columns.map((col) => {
                              const val = row[col];
                              return (
                                <td key={col} className="p-2 border-r border-white/[0.05] whitespace-nowrap text-slate-300">
                                  {val !== null && val !== undefined ? String(val) : (
                                    <span className="text-slate-600 italic">null</span>
                                  )}
                                </td>
                              );
                            })}
                          </tr>
                        ))
                      )}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          )}

          {/* Bottom Proceed Button */}
          <div className="flex justify-end pt-4">
            <button
              onClick={handleProceed}
              disabled={initializing || filesList.filter((f) => f.selected).length === 0}
              className="flex items-center space-x-2.5 active-nav-glow px-8 py-3.5 rounded-2xl font-black text-sm cursor-pointer disabled:opacity-40 disabled:cursor-not-allowed transition-all"
            >
              {initializing ? (
                <>
                  <RefreshCw className="w-4 h-4 animate-spin text-white" />
                  <span>Đang nạp và hợp nhất dữ liệu...</span>
                </>
              ) : (
                <>
                  <span>Tiếp tục sang bước Làm sạch</span>
                  <ArrowRight className="w-4 h-4 text-white" />
                </>
              )}
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default ConnectPage;
