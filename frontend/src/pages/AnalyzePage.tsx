import React, { useState, useEffect } from 'react';
import {
  BarChart, Bar, LineChart, Line, AreaChart, Area, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend,
  ResponsiveContainer
} from 'recharts';
import {
  BarChart3, TrendingUp, Table2, Layers, ArrowUpDown,
  RefreshCw, X, ArrowRight
} from 'lucide-react';
import ApiService from '../services/api';

const ACCENT_COLORS = [
  '#2F8BFF', '#38BDF8', '#34D399', '#FBBF24', '#A78BFA',
  '#F87171', '#06B6D4', '#EC4899', '#60A5FA', '#10B981'
];

interface AnalyzePageProps {
  sessionId: string;
  onContinue: () => void;
  initialPivotConfig?: {
    rows?: string[];
    values?: string[];
    agg_func?: string;
    chart_type?: string;
  };
}

export const AnalyzePage: React.FC<AnalyzePageProps> = ({
  sessionId,
  onContinue,
  initialPivotConfig,
}) => {
  const [activeTab, setActiveTab] = useState<'pivot' | 'custom' | 'overview'>('pivot');
  const [loading, setLoading] = useState(true);
  const [pivotLoading, setPivotLoading] = useState(false);

  // Overview data
  const [colTypes, setColTypes] = useState<{
    numeric: string[];
    categorical: string[];
    datetime: string[];
    all: string[];
  }>({ numeric: [], categorical: [], datetime: [], all: [] });
  const [summaryStats, setSummaryStats] = useState<Record<string, any>>({});
  const [correlations, setCorrelations] = useState<{ columns: string[]; matrix: any[]; pairs: any[] }>({
    columns: [], matrix: [], pairs: []
  });

  // Pivot & PivotChart State
  const [pivotRows, setPivotRows] = useState<string[]>(initialPivotConfig?.rows || []);
  const [pivotCols, setPivotCols] = useState<string[]>([]);
  const [pivotValues, setPivotValues] = useState<string[]>(initialPivotConfig?.values || []);
  const [pivotAgg, setPivotAgg] = useState<string>(initialPivotConfig?.agg_func || 'sum');
  const [pivotChartType, setPivotChartType] = useState<string>(initialPivotConfig?.chart_type || 'bar');
  const [pivotSort, setPivotSort] = useState<'asc' | 'desc'>('desc');
  const [pivotResult, setPivotResult] = useState<any>(null);

  // Drilldown & Segment Detail Panel
  const [drillDownRecords, setDrillDownRecords] = useState<Record<string, any>[] | null>(null);
  const [selectedSegmentLabel, setSelectedSegmentLabel] = useState<string | null>(null);
  const [drillDownLoading, setDrillDownLoading] = useState(false);

  // Custom Chart Builder State (Tab 2)
  const [customDimension, setCustomDimension] = useState<string>('');
  const [customMeasure, setCustomMeasure] = useState<string>('');
  const [customAgg, setCustomAgg] = useState<string>('sum');
  const [customChartType, setCustomChartType] = useState<string>('bar');
  const [customChartData, setCustomChartData] = useState<any[]>([]);

  // Distribution Explorer (Tab 3)
  const [distColumn, setDistColumn] = useState<string>('');
  const [distData, setDistData] = useState<any>(null);

  // Fetch Overview Data
  useEffect(() => {
    const fetchOverview = async () => {
      try {
        setLoading(true);
        const res = await ApiService.getAnalyzeOverview(sessionId);
        setColTypes(res.col_types);
        setSummaryStats(res.summary);
        setCorrelations(res.correlations);

        const cats = res.col_types.categorical || [];
        const nums = res.col_types.numeric || [];

        const defaultRow = initialPivotConfig?.rows?.[0] || cats[0] || nums[0] || '';
        const defaultVal = initialPivotConfig?.values?.[0] || nums[0] || '';

        if (!pivotRows.length && defaultRow) setPivotRows([defaultRow]);
        if (!pivotValues.length && defaultVal) setPivotValues([defaultVal]);

        setCustomDimension(defaultRow);
        setCustomMeasure(defaultVal);
        setDistColumn(nums[0] || cats[0] || '');
      } catch (err) {
        console.error('Error fetching overview', err);
      } finally {
        setLoading(false);
      }
    };
    fetchOverview();
  }, [sessionId]);

  // Execute Pivot computation
  const executePivot = async () => {
    if (!pivotRows.length && !pivotCols.length) return;
    try {
      setPivotLoading(true);
      const res = await ApiService.computePivot({
        session_id: sessionId,
        rows: pivotRows,
        cols: pivotCols,
        values: pivotValues,
        agg_func: pivotAgg,
        sort_order: pivotSort,
      });
      setPivotResult(res);
    } catch (err) {
      console.error('Error executing pivot', err);
    } finally {
      setPivotLoading(false);
    }
  };

  useEffect(() => {
    if (pivotRows.length > 0 || pivotCols.length > 0) {
      executePivot();
    }
  }, [pivotRows, pivotCols, pivotValues, pivotAgg, pivotSort]);

  // Custom chart builder
  useEffect(() => {
    if (!customDimension || !customMeasure) return;
    const fetchCustom = async () => {
      try {
        const res = await ApiService.computePivot({
          session_id: sessionId,
          rows: [customDimension],
          values: [customMeasure],
          agg_func: customAgg,
          sort_order: 'desc',
        });
        setCustomChartData(res.chart_data || []);
      } catch (err) {
        console.error('Error custom chart', err);
      }
    };
    fetchCustom();
  }, [customDimension, customMeasure, customAgg, customChartType]);

  // Distribution
  useEffect(() => {
    if (!distColumn) return;
    const fetchDist = async () => {
      try {
        const res = await ApiService.getDistribution(sessionId, distColumn);
        setDistData(res);
      } catch (err) {
        console.error('Error fetching distribution', err);
      }
    };
    fetchDist();
  }, [distColumn]);

  // Drilldown segment handler
  const handleChartClick = async (entry: any) => {
    if (!entry) return;
    const payload = entry.payload || entry;
    const segName = payload.name || payload[pivotRows[0]] || 'Phân khúc';
    setSelectedSegmentLabel(String(segName));

    const rowFilters: Record<string, any> = {};
    pivotRows.forEach((r) => {
      if (payload[r] !== undefined) {
        rowFilters[r] = payload[r];
      }
    });

    try {
      setDrillDownLoading(true);
      const res = await ApiService.drillDown({
        session_id: sessionId,
        row_filters: rowFilters,
        limit: 50,
      });
      setDrillDownRecords(res.records);
    } catch (err) {
      console.error('Drill down error', err);
    } finally {
      setDrillDownLoading(false);
    }
  };

  const togglePivotRow = (col: string) => {
    setPivotRows((prev) =>
      prev.includes(col) ? prev.filter((c) => c !== col) : [...prev, col]
    );
  };

  const togglePivotCol = (col: string) => {
    setPivotCols((prev) =>
      prev.includes(col) ? prev.filter((c) => c !== col) : [...prev, col]
    );
  };

  const togglePivotValue = (col: string) => {
    setPivotValues([col]);
  };

  if (loading) {
    return (
      <div className="p-16 text-center flex flex-col items-center justify-center space-y-4">
        <RefreshCw className="w-10 h-10 text-cyan-400 animate-spin" />
        <p className="text-slate-300 font-bold text-sm">Đang nạp và tính toán cấu trúc số liệu phân tích...</p>
      </div>
    );
  }

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-8 animate-fadeIn">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center space-x-2">
            <span className="text-[10px] font-extrabold uppercase tracking-widest text-cyan-400 bg-cyan-950/70 border border-cyan-800/60 px-2.5 py-0.5 rounded-full">
              BƯỚC 3: PHÂN TÍCH
            </span>
          </div>
          <h2 className="text-2xl font-black text-white mt-1 tracking-tight">Khai Phá Số Liệu & PivotChart Đa Chiều</h2>
          <p className="text-slate-400 mt-1 text-xs">
            Kéo thả các trường dữ liệu, thay đổi phép toán tổng hợp và nhấp vào biểu đồ để đào sâu (drill-down) bản ghi chi tiết.
          </p>
        </div>

        <button
          onClick={onContinue}
          className="flex items-center space-x-2 active-nav-glow px-6 py-2.5 rounded-xl font-bold text-xs cursor-pointer transition-all whitespace-nowrap"
        >
          <span>Xem Báo Cáo Tự Động</span>
          <ArrowRight className="w-4 h-4 text-white" />
        </button>
      </div>

      {/* Navigation Tabs */}
      <div className="flex border-b border-white/10 space-x-6 text-xs font-extrabold">
        <button
          onClick={() => setActiveTab('pivot')}
          className={`pb-3.5 flex items-center space-x-2 border-b-2 transition-all ${
            activeTab === 'pivot'
              ? 'border-cyan-400 text-cyan-300 drop-shadow-[0_0_8px_rgba(56,189,248,0.5)]'
              : 'border-transparent text-slate-400 hover:text-slate-200'
          }`}
        >
          <Table2 className="w-4 h-4" />
          <span>PivotChart Đa Chiều</span>
        </button>

        <button
          onClick={() => setActiveTab('custom')}
          className={`pb-3.5 flex items-center space-x-2 border-b-2 transition-all ${
            activeTab === 'custom'
              ? 'border-cyan-400 text-cyan-300 drop-shadow-[0_0_8px_rgba(56,189,248,0.5)]'
              : 'border-transparent text-slate-400 hover:text-slate-200'
          }`}
        >
          <BarChart3 className="w-4 h-4" />
          <span>Biểu Đồ Tùy Biến</span>
        </button>

        <button
          onClick={() => setActiveTab('overview')}
          className={`pb-3.5 flex items-center space-x-2 border-b-2 transition-all ${
            activeTab === 'overview'
              ? 'border-cyan-400 text-cyan-300 drop-shadow-[0_0_8px_rgba(56,189,248,0.5)]'
              : 'border-transparent text-slate-400 hover:text-slate-200'
          }`}
        >
          <TrendingUp className="w-4 h-4" />
          <span>Thống Kê Tổng Quan & Tương Quan</span>
        </button>
      </div>

      {/* ===================== TAB 1: PIVOTCHART FEATURE ===================== */}
      {activeTab === 'pivot' && (
        <div className="space-y-6">
          {/* Pivot Controls Panel (Left control panel & PivotChart drop zones) */}
          <div className="glass-panel p-6 space-y-5">
            <div className="flex flex-wrap items-center justify-between gap-4 border-b border-white/[0.08] pb-4">
              <h3 className="font-extrabold text-white text-sm flex items-center space-x-2">
                <Layers className="w-4 h-4 text-cyan-400" />
                <span>Thiết Lập Vùng Kéo Thả (Pivot Builder)</span>
              </h3>

              <div className="flex flex-wrap items-center gap-3 text-xs">
                {/* Aggregation Selector */}
                <div className="flex items-center space-x-1.5">
                  <span className="text-slate-400 font-semibold">Phép toán (Agg):</span>
                  <select
                    value={pivotAgg}
                    onChange={(e) => setPivotAgg(e.target.value)}
                    className="glass-input p-1.5 font-bold text-white text-xs"
                  >
                    <option value="sum" className="bg-slate-900 text-white">Tổng (SUM)</option>
                    <option value="average" className="bg-slate-900 text-white">Trung bình (AVERAGE)</option>
                    <option value="count" className="bg-slate-900 text-white">Đếm dòng (COUNT)</option>
                    <option value="min" className="bg-slate-900 text-white">Tối thiểu (MIN)</option>
                    <option value="max" className="bg-slate-900 text-white">Tối đa (MAX)</option>
                    <option value="median" className="bg-slate-900 text-white">Trung vị (MEDIAN)</option>
                  </select>
                </div>

                {/* Sort Order */}
                <button
                  onClick={() => setPivotSort((s) => (s === 'desc' ? 'asc' : 'desc'))}
                  className="flex items-center space-x-1.5 glass-card px-3 py-1.5 text-xs text-slate-300 font-bold hover:text-white"
                >
                  <ArrowUpDown className="w-3.5 h-3.5 text-cyan-400" />
                  <span>Sắp xếp: {pivotSort === 'desc' ? 'Giảm dần' : 'Tăng dần'}</span>
                </button>

                {/* Chart Type Selector */}
                <div className="flex items-center space-x-1 bg-white/[0.04] p-1 rounded-xl border border-white/10">
                  {['bar', 'line', 'area', 'pie'].map((type) => (
                    <button
                      key={type}
                      onClick={() => setPivotChartType(type)}
                      className={`px-3 py-1 rounded-lg text-xs font-bold capitalize transition-all ${
                        pivotChartType === type
                          ? 'bg-blue-600 text-white shadow-[0_0_12px_rgba(47,139,255,0.5)]'
                          : 'text-slate-400 hover:text-white'
                      }`}
                    >
                      {type === 'bar' ? 'Cột' : type === 'line' ? 'Đường' : type === 'area' ? 'Miền' : 'Tròn'}
                    </button>
                  ))}
                </div>
              </div>
            </div>

            {/* Field Drop Slots in Responsive Grid */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs">
              {/* Slot 1: Rows (Dimensions) */}
              <div className="p-4 bg-white/[0.03] rounded-2xl border border-white/[0.08] space-y-2">
                <span className="font-extrabold text-cyan-300 block uppercase tracking-wider text-[10px]">
                  Hàng / Trục X (Rows):
                </span>
                <div className="flex flex-wrap gap-1.5">
                  {colTypes.all.map((col) => {
                    const isRow = pivotRows.includes(col);
                    return (
                      <button
                        key={col}
                        onClick={() => togglePivotRow(col)}
                        className={`px-2.5 py-1 rounded-lg font-bold text-xs transition-all ${
                          isRow
                            ? 'bg-gradient-to-r from-blue-600 to-cyan-500 text-white shadow-[0_0_12px_rgba(47,139,255,0.4)]'
                            : 'bg-white/[0.04] text-slate-400 border border-white/[0.08] hover:border-white/20'
                        }`}
                      >
                        {col}
                      </button>
                    );
                  })}
                </div>
              </div>

              {/* Slot 2: Columns (Optional 2D) */}
              <div className="p-4 bg-white/[0.03] rounded-2xl border border-white/[0.08] space-y-2">
                <span className="font-extrabold text-blue-400 block uppercase tracking-wider text-[10px]">
                  Cột Phân Cấp (Columns 2D):
                </span>
                <div className="flex flex-wrap gap-1.5">
                  {colTypes.all.map((col) => {
                    const isCol = pivotCols.includes(col);
                    return (
                      <button
                        key={col}
                        onClick={() => togglePivotCol(col)}
                        className={`px-2.5 py-1 rounded-lg font-bold text-xs transition-all ${
                          isCol
                            ? 'bg-blue-600 text-white shadow-[0_0_12px_rgba(59,130,246,0.5)]'
                            : 'bg-white/[0.04] text-slate-400 border border-white/[0.08] hover:border-white/20'
                        }`}
                      >
                        {col}
                      </button>
                    );
                  })}
                </div>
              </div>

              {/* Slot 3: Values (Measures) */}
              <div className="p-4 bg-white/[0.03] rounded-2xl border border-white/[0.08] space-y-2">
                <span className="font-extrabold text-amber-400 block uppercase tracking-wider text-[10px]">
                  Giá Trị / Chỉ Số (Values):
                </span>
                <div className="flex flex-wrap gap-1.5">
                  {colTypes.numeric.length > 0 ? (
                    colTypes.numeric.map((col) => {
                      const isVal = pivotValues.includes(col);
                      return (
                        <button
                          key={col}
                          onClick={() => togglePivotValue(col)}
                          className={`px-2.5 py-1 rounded-lg font-bold text-xs transition-all ${
                            isVal
                              ? 'bg-amber-500 text-slate-950 font-black shadow-[0_0_12px_rgba(245,158,11,0.5)]'
                            : 'bg-white/[0.04] text-slate-400 border border-white/[0.08] hover:border-white/20'
                          }`}
                        >
                          {col}
                        </button>
                      );
                    })
                  ) : (
                    <span className="text-slate-500 italic text-xs">Đang tự động đếm dòng dữ liệu</span>
                  )}
                </div>
              </div>
            </div>
          </div>

          {/* Main Chart Area */}
          <div className="glass-panel p-6 space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <h4 className="font-extrabold text-white text-base">
                  Biểu Đồ Pivot Tương Tác ({pivotChartType.toUpperCase()})
                </h4>
                <p className="text-xs text-slate-400">
                  Nhấp vào bất kỳ cột, đường hoặc phân đoạn nào trên biểu đồ để xem 50 bản ghi gốc chi tiết (Drill-down).
                </p>
              </div>
              {pivotLoading && <RefreshCw className="w-4 h-4 text-cyan-400 animate-spin" />}
            </div>

            {/* Dark Themed Recharts Container */}
            <div className="h-80 w-full pt-4">
              {pivotResult?.chart_data && pivotResult.chart_data.length > 0 ? (
                <ResponsiveContainer width="100%" height="100%">
                  {pivotChartType === 'line' ? (
                    <LineChart data={pivotResult.chart_data} onClick={handleChartClick}>
                      <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.08)" />
                      <XAxis dataKey="name" stroke="#94a3b8" fontSize={11} />
                      <YAxis stroke="#94a3b8" fontSize={11} />
                      <Tooltip contentStyle={{ backgroundColor: 'rgba(7, 12, 24, 0.95)', borderColor: 'rgba(255, 255, 255, 0.15)', borderRadius: '14px', backdropFilter: 'blur(16px)', color: '#fff' }} />
                      <Legend />
                      {pivotResult.col_keys?.length > 0 ? (
                        pivotResult.col_keys.map((k: string, idx: number) => (
                          <Line key={k} type="monotone" dataKey={k} stroke={ACCENT_COLORS[idx % ACCENT_COLORS.length]} strokeWidth={2.5} dot={{ r: 4 }} />
                        ))
                      ) : (
                        <Line type="monotone" dataKey={pivotResult.value_col} stroke="#38BDF8" strokeWidth={3} dot={{ r: 5, fill: '#38BDF8' }} />
                      )}
                    </LineChart>
                  ) : pivotChartType === 'area' ? (
                    <AreaChart data={pivotResult.chart_data} onClick={handleChartClick}>
                      <defs>
                        <linearGradient id="areaGlow" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="5%" stopColor="#2F8BFF" stopOpacity={0.6}/>
                          <stop offset="95%" stopColor="#2F8BFF" stopOpacity={0.0}/>
                        </linearGradient>
                      </defs>
                      <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.08)" />
                      <XAxis dataKey="name" stroke="#94a3b8" fontSize={11} />
                      <YAxis stroke="#94a3b8" fontSize={11} />
                      <Tooltip contentStyle={{ backgroundColor: 'rgba(7, 12, 24, 0.95)', borderColor: 'rgba(255, 255, 255, 0.15)', borderRadius: '14px', color: '#fff' }} />
                      <Area type="monotone" dataKey={pivotResult.value_col} stroke="#38BDF8" fill="url(#areaGlow)" strokeWidth={2.5} />
                    </AreaChart>
                  ) : pivotChartType === 'pie' ? (
                    <PieChart onClick={handleChartClick}>
                      <Tooltip contentStyle={{ backgroundColor: 'rgba(7, 12, 24, 0.95)', borderColor: 'rgba(255, 255, 255, 0.15)', borderRadius: '14px', color: '#fff' }} />
                      <Legend />
                      <Pie
                        data={pivotResult.chart_data}
                        dataKey={pivotResult.value_col}
                        nameKey="name"
                        cx="50%"
                        cy="50%"
                        outerRadius={105}
                        innerRadius={55}
                        paddingAngle={3}
                      >
                        {pivotResult.chart_data.map((_: any, index: number) => (
                          <Cell key={`cell-${index}`} fill={ACCENT_COLORS[index % ACCENT_COLORS.length]} />
                        ))}
                      </Pie>
                    </PieChart>
                  ) : (
                    <BarChart data={pivotResult.chart_data} onClick={handleChartClick}>
                      <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.08)" />
                      <XAxis dataKey="name" stroke="#94a3b8" fontSize={11} />
                      <YAxis stroke="#94a3b8" fontSize={11} />
                      <Tooltip contentStyle={{ backgroundColor: 'rgba(7, 12, 24, 0.95)', borderColor: 'rgba(255, 255, 255, 0.15)', borderRadius: '14px', color: '#fff' }} />
                      <Legend />
                      {pivotResult.col_keys?.length > 0 ? (
                        pivotResult.col_keys.map((k: string, idx: number) => (
                          <Bar key={k} dataKey={k} fill={ACCENT_COLORS[idx % ACCENT_COLORS.length]} radius={[6, 6, 0, 0]} />
                        ))
                      ) : (
                        <Bar dataKey={pivotResult.value_col} fill="#2F8BFF" radius={[6, 6, 0, 0]} />
                      )}
                    </BarChart>
                  )}
                </ResponsiveContainer>
              ) : (
                <div className="h-full flex items-center justify-center text-slate-500 text-xs">
                  Chưa có dữ liệu. Vui lòng chọn ít nhất một Hàng (Row) hoặc Cột (Column).
                </div>
              )}
            </div>
          </div>

          {/* Synchronized Pivot Table */}
          {pivotResult?.table_data && pivotResult.table_data.length > 0 && (
            <div className="glass-panel p-6 space-y-4">
              <h4 className="font-extrabold text-white text-base">Bảng Pivot Dữ Liệu Đồng Bộ</h4>
              <div className="border border-white/10 rounded-2xl overflow-x-auto max-h-72 bg-black/20">
                <table className="w-full text-left text-xs border-collapse">
                  <thead className="bg-white/[0.06] text-slate-200 font-bold sticky top-0 z-10 backdrop-blur-md">
                    <tr>
                      <th className="p-3 border-b border-r border-white/10 text-cyan-300">Phân loại (Hàng)</th>
                      {pivotResult.col_keys?.length > 0 ? (
                        pivotResult.col_keys.map((k: string) => (
                          <th key={k} className="p-3 border-b border-r border-white/10 text-right text-slate-200 font-mono">
                            {k}
                          </th>
                        ))
                      ) : (
                        <th className="p-3 border-b border-r border-white/10 text-right text-slate-200 font-mono">
                          {pivotAgg.toUpperCase()} của {pivotResult.value_col}
                        </th>
                      )}
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-white/[0.05]">
                    {pivotResult.table_data.map((row: any, rIdx: number) => (
                      <tr
                        key={rIdx}
                        onClick={() => handleChartClick(row)}
                        className="hover:bg-white/[0.04] cursor-pointer transition-colors"
                        title="Nhấp để xem dòng chi tiết"
                      >
                        <td className="p-2.5 border-r border-white/[0.05] font-bold text-white">
                          {row.name}
                        </td>
                        {pivotResult.col_keys?.length > 0 ? (
                          pivotResult.col_keys.map((k: string) => (
                            <td key={k} className="p-2.5 border-r border-white/[0.05] text-right text-slate-300 font-mono">
                              {Number(row[k] || 0).toLocaleString()}
                            </td>
                          ))
                        ) : (
                          <td className="p-2.5 border-r border-white/[0.05] text-right text-cyan-300 font-mono font-bold">
                            {Number(row[pivotResult.value_col] || 0).toLocaleString()}
                          </td>
                        )}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      )}

      {/* ===================== TAB 2: CUSTOM CHART BUILDER ===================== */}
      {activeTab === 'custom' && (
        <div className="space-y-6">
          <div className="glass-panel p-6 space-y-4">
            <h3 className="font-extrabold text-white text-sm">Bộ Khởi Tạo Biểu Đồ Tùy Biến</h3>
            <div className="grid grid-cols-1 sm:grid-cols-4 gap-4 text-xs">
              <div>
                <label className="font-bold text-slate-300 block mb-1">Trục X (Chiều phân loại):</label>
                <select
                  value={customDimension}
                  onChange={(e) => setCustomDimension(e.target.value)}
                  className="glass-input w-full p-2.5 font-medium"
                >
                  {colTypes.all.map((c) => <option key={c} value={c} className="bg-slate-900 text-white">{c}</option>)}
                </select>
              </div>

              <div>
                <label className="font-bold text-slate-300 block mb-1">Trục Y (Chỉ số đo lường):</label>
                <select
                  value={customMeasure}
                  onChange={(e) => setCustomMeasure(e.target.value)}
                  className="glass-input w-full p-2.5 font-medium"
                >
                  {colTypes.numeric.map((c) => <option key={c} value={c} className="bg-slate-900 text-white">{c}</option>)}
                </select>
              </div>

              <div>
                <label className="font-bold text-slate-300 block mb-1">Phép toán tổng hợp:</label>
                <select
                  value={customAgg}
                  onChange={(e) => setCustomAgg(e.target.value)}
                  className="glass-input w-full p-2.5 font-medium"
                >
                  <option value="sum" className="bg-slate-900 text-white">Tổng (SUM)</option>
                  <option value="average" className="bg-slate-900 text-white">Trung bình (AVERAGE)</option>
                  <option value="count" className="bg-slate-900 text-white">Đếm dòng (COUNT)</option>
                  <option value="min" className="bg-slate-900 text-white">Tối thiểu (MIN)</option>
                  <option value="max" className="bg-slate-900 text-white">Tối đa (MAX)</option>
                </select>
              </div>

              <div>
                <label className="font-bold text-slate-300 block mb-1">Loại biểu đồ:</label>
                <select
                  value={customChartType}
                  onChange={(e) => setCustomChartType(e.target.value)}
                  className="glass-input w-full p-2.5 font-medium"
                >
                  <option value="bar" className="bg-slate-900 text-white">Cột (Bar Chart)</option>
                  <option value="line" className="bg-slate-900 text-white">Đường (Line Chart)</option>
                  <option value="area" className="bg-slate-900 text-white">Miền (Area Chart)</option>
                  <option value="pie" className="bg-slate-900 text-white">Tròn (Pie Chart)</option>
                </select>
              </div>
            </div>
          </div>

          <div className="glass-panel p-6 h-96">
            <ResponsiveContainer width="100%" height="100%">
              {customChartType === 'line' ? (
                <LineChart data={customChartData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.08)" />
                  <XAxis dataKey="name" stroke="#94a3b8" fontSize={11} />
                  <YAxis stroke="#94a3b8" fontSize={11} />
                  <Tooltip contentStyle={{ backgroundColor: 'rgba(7, 12, 24, 0.95)', borderColor: 'rgba(255, 255, 255, 0.15)', borderRadius: '14px', color: '#fff' }} />
                  <Line type="monotone" dataKey={customMeasure} stroke="#38BDF8" strokeWidth={2.5} dot={{ r: 4 }} />
                </LineChart>
              ) : customChartType === 'pie' ? (
                <PieChart>
                  <Tooltip contentStyle={{ backgroundColor: 'rgba(7, 12, 24, 0.95)', borderColor: 'rgba(255, 255, 255, 0.15)', borderRadius: '14px', color: '#fff' }} />
                  <Legend />
                  <Pie data={customChartData} dataKey={customMeasure} nameKey="name" outerRadius={110} innerRadius={50}>
                    {customChartData.map((_, i) => <Cell key={i} fill={ACCENT_COLORS[i % ACCENT_COLORS.length]} />)}
                  </Pie>
                </PieChart>
              ) : (
                <BarChart data={customChartData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.08)" />
                  <XAxis dataKey="name" stroke="#94a3b8" fontSize={11} />
                  <YAxis stroke="#94a3b8" fontSize={11} />
                  <Tooltip contentStyle={{ backgroundColor: 'rgba(7, 12, 24, 0.95)', borderColor: 'rgba(255, 255, 255, 0.15)', borderRadius: '14px', color: '#fff' }} />
                  <Bar dataKey={customMeasure} fill="#2F8BFF" radius={[6, 6, 0, 0]} />
                </BarChart>
              )}
            </ResponsiveContainer>
          </div>
        </div>
      )}

      {/* ===================== TAB 3: OVERVIEW & CORRELATIONS ===================== */}
      {activeTab === 'overview' && (
        <div className="space-y-6">
          {/* Summary Stats Table */}
          <div className="glass-panel p-6 space-y-4">
            <h3 className="font-extrabold text-white text-base">Thống Kê Mô Tả Chi Tiết Các Cột</h3>
            <div className="border border-white/10 rounded-2xl overflow-x-auto max-h-72 bg-black/20">
              <table className="w-full text-left text-xs border-collapse">
                <thead className="bg-white/[0.06] text-slate-200 font-bold sticky top-0 z-10 backdrop-blur-md">
                  <tr>
                    <th className="p-3 border-b border-r border-white/10 text-cyan-300">Cột</th>
                    <th className="p-3 border-b border-r border-white/10">Kiểu</th>
                    <th className="p-3 border-b border-r border-white/10 text-right">Tổng hợp</th>
                    <th className="p-3 border-b border-r border-white/10 text-right">Trung bình</th>
                    <th className="p-3 border-b border-r border-white/10 text-right">Trung vị</th>
                    <th className="p-3 border-b border-r border-white/10 text-right">Độ lệch chuẩn</th>
                    <th className="p-3 border-b border-r border-white/10 text-right">Tối thiểu</th>
                    <th className="p-3 border-b border-r border-white/10 text-right">Tối đa</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-white/[0.05]">
                  {Object.entries(summaryStats).map(([col, st]: any) => (
                    <tr key={col} className="hover:bg-white/[0.04]">
                      <td className="p-2.5 border-r border-white/[0.05] font-bold text-white">{col}</td>
                      <td className="p-2.5 border-r border-white/[0.05] text-slate-400 uppercase text-[10px] font-bold">
                        {st.type}
                      </td>
                      <td className="p-2.5 border-r border-white/[0.05] text-right font-mono text-cyan-300">{st.sum?.toLocaleString() || '-'}</td>
                      <td className="p-2.5 border-r border-white/[0.05] text-right font-mono text-slate-300">{st.mean?.toLocaleString() || '-'}</td>
                      <td className="p-2.5 border-r border-white/[0.05] text-right font-mono text-slate-300">{st.median?.toLocaleString() || '-'}</td>
                      <td className="p-2.5 border-r border-white/[0.05] text-right font-mono text-slate-400">{st.std?.toLocaleString() || '-'}</td>
                      <td className="p-2.5 border-r border-white/[0.05] text-right font-mono text-slate-400">{st.min?.toLocaleString() || '-'}</td>
                      <td className="p-2.5 border-r border-white/[0.05] text-right font-mono text-slate-400">{st.max?.toLocaleString() || '-'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Correlation Matrix */}
          {correlations.columns.length >= 2 && (
            <div className="glass-panel p-6 space-y-4">
              <h3 className="font-extrabold text-white text-base">Ma Trận Tương Quan Pearson Giữa Các Chỉ Số</h3>
              <div className="border border-white/10 rounded-2xl overflow-x-auto bg-black/20">
                <table className="w-full text-center text-xs border-collapse">
                  <thead className="bg-white/[0.06] text-slate-200 font-bold">
                    <tr>
                      <th className="p-3 border-b border-r border-white/10 text-left text-cyan-300">Chỉ số</th>
                      {correlations.columns.map((c) => (
                        <th key={c} className="p-3 border-b border-r border-white/10">{c}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {correlations.matrix.map((row: any) => (
                      <tr key={row.name}>
                        <td className="p-2.5 border-b border-r border-white/[0.05] text-left font-bold text-white">
                          {row.name}
                        </td>
                        {correlations.columns.map((c) => {
                          const val = row[c];
                          const bgIntensity = Math.abs(val);
                          const isPos = val > 0;
                          return (
                            <td
                              key={c}
                              className="p-2.5 border-b border-r border-white/[0.05] font-mono font-bold"
                              style={{
                                backgroundColor: isPos
                                  ? `rgba(47, 139, 255, ${bgIntensity * 0.45})`
                                  : `rgba(248, 113, 113, ${bgIntensity * 0.45})`,
                                color: bgIntensity > 0.5 ? '#ffffff' : '#94a3b8'
                              }}
                            >
                              {val}
                            </td>
                          );
                        })}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Distribution Explorer */}
          <div className="glass-panel p-6 space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="font-extrabold text-white text-base">Khám Phá Phân Bổ Tần Suất (Distribution)</h3>
              <select
                value={distColumn}
                onChange={(e) => setDistColumn(e.target.value)}
                className="glass-input text-xs p-2 font-medium"
              >
                {colTypes.all.map((c) => <option key={c} value={c} className="bg-slate-900 text-white">{c}</option>)}
              </select>
            </div>

            {distData && distData.data && (
              <div className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={distData.data}>
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.08)" />
                    <XAxis dataKey={distData.type === 'numeric' ? 'range' : 'category'} stroke="#94a3b8" fontSize={11} />
                    <YAxis stroke="#94a3b8" fontSize={11} />
                    <Tooltip contentStyle={{ backgroundColor: 'rgba(7, 12, 24, 0.95)', borderColor: 'rgba(255, 255, 255, 0.15)', borderRadius: '14px', color: '#fff' }} />
                    <Bar dataKey="count" fill="#38BDF8" radius={[6, 6, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Drill-down / Segment Detail Modal Drawer in dark glassmorphism */}
      {drillDownRecords && (
        <div className="fixed inset-0 bg-black/75 backdrop-blur-md z-50 flex items-center justify-center p-4">
          <div className="glass-panel p-6 max-w-4xl w-full space-y-4 border border-white/20 shadow-2xl max-h-[85vh] flex flex-col bg-[#0B1220]/95">
            <div className="flex items-center justify-between border-b border-white/10 pb-3">
              <div>
                <h4 className="font-extrabold text-white text-base">
                  Chi Tiết Phân Đoạn (Drill-Down): <span className="text-cyan-400">{selectedSegmentLabel}</span>
                </h4>
                <p className="text-xs text-slate-400">
                  Hiển thị tối đa 50 bản ghi gốc tương ứng với phân đoạn số liệu đã chọn.
                </p>
              </div>
              <div className="flex items-center space-x-2">
                {drillDownLoading && <RefreshCw className="w-4 h-4 text-cyan-400 animate-spin" />}
                <button
                  onClick={() => setDrillDownRecords(null)}
                  className="p-1.5 text-slate-400 hover:text-white rounded-xl hover:bg-white/10"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>
            </div>

            <div className="flex-1 overflow-x-auto overflow-y-auto border border-white/10 rounded-2xl bg-black/20">
              <table className="w-full text-left text-xs border-collapse">
                <thead className="bg-white/[0.06] text-slate-200 font-bold sticky top-0 z-10 backdrop-blur-md">
                  <tr>
                    <th className="p-2.5 border-b border-r border-white/10 w-12 text-center text-slate-500">#</th>
                    {drillDownRecords.length > 0 &&
                      Object.keys(drillDownRecords[0]).map((k) => (
                        <th key={k} className="p-2.5 border-b border-r border-white/10 whitespace-nowrap text-cyan-300 font-mono">
                          {k}
                        </th>
                      ))}
                  </tr>
                </thead>
                <tbody className="divide-y divide-white/[0.05]">
                  {drillDownRecords.map((r, i) => (
                    <tr key={i} className="hover:bg-white/[0.04]">
                      <td className="p-2 border-r border-white/10 text-center text-slate-500 font-mono text-[11px]">
                        {i + 1}
                      </td>
                      {Object.keys(r).map((k) => (
                        <td key={k} className="p-2 border-r border-white/[0.05] whitespace-nowrap text-slate-300">
                          {r[k] !== null && r[k] !== undefined ? String(r[k]) : '-'}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <div className="flex justify-end pt-2 border-t border-white/10">
              <button
                onClick={() => setDrillDownRecords(null)}
                className="px-5 py-2 text-xs font-extrabold text-white active-nav-glow rounded-xl"
              >
                Đóng
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default AnalyzePage;
