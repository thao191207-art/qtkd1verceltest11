import React, { useState, useEffect, useRef } from 'react';
import {
  FileSpreadsheet, FileDown, Image,
  RefreshCw, ExternalLink, Activity, AlertTriangle,
  Calendar, CheckCircle2, TrendingDown,
  Sparkles, ShieldCheck, ArrowRight, BarChart2,
  DollarSign, Percent, Award, Package, ShoppingBag
} from 'lucide-react';
import {
  ResponsiveContainer, BarChart, Bar, Line, ComposedChart,
  PieChart, Pie, Cell, XAxis, YAxis, Tooltip, Legend, CartesianGrid
} from 'recharts';
import html2canvas from 'html2canvas';
import { ApiService } from '../services/api';
import { useTheme } from '../context/ThemeContext';

interface ReportPageProps {
  sessionId: string;
  onOpenPivotForProblem: (pivotConfig: any) => void;
}

export const ReportPage: React.FC<ReportPageProps> = ({
  sessionId,
  onOpenPivotForProblem,
}) => {
  const { theme } = useTheme();
  const [report, setReport] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [exportingImage, setExportingImage] = useState(false);
  const dashboardRef = useRef<HTMLDivElement>(null);

  const isDark = theme === 'dark';
  const chartGridColor = isDark ? 'rgba(255, 255, 255, 0.08)' : 'rgba(15, 23, 42, 0.08)';
  const chartAxisColor = isDark ? '#94A3B8' : '#475569';
  const tooltipBg = isDark ? '#0B1220' : '#FFFFFF';
  const tooltipBorder = isDark ? 'rgba(255, 255, 255, 0.16)' : 'rgba(15, 23, 42, 0.15)';
  const tooltipTextColor = isDark ? '#F8FAFC' : '#0F172A';

  useEffect(() => {
    const fetchReport = async () => {
      try {
        setLoading(true);
        const res = await ApiService.generateReport(sessionId);
        setReport(res);
      } catch (err) {
        console.error('Error generating report', err);
      } finally {
        setLoading(false);
      }
    };
    fetchReport();
  }, [sessionId]);

  const handleExportPNG = async () => {
    if (!dashboardRef.current) return;
    try {
      setExportingImage(true);
      const canvas = await html2canvas(dashboardRef.current, {
        scale: 2,
        useCORS: true,
        backgroundColor: isDark ? '#05080F' : '#F4F7FB',
      });
      const link = document.createElement('a');
      link.download = `FLOWER_HAPPY_Bao_Cao_${new Date().toISOString().slice(0, 10)}.png`;
      link.href = canvas.toDataURL('image/png');
      link.click();
    } catch (err) {
      console.error('PNG export failed', err);
    } finally {
      setExportingImage(false);
    }
  };

  const scrollToChart = (chartId: string) => {
    const el = document.getElementById(chartId);
    if (el) {
      el.scrollIntoView({ behavior: 'smooth', block: 'center' });
      el.classList.add('ring-2', 'ring-cyan-400');
      setTimeout(() => el.classList.remove('ring-2', 'ring-cyan-400'), 2500);
    }
  };

  const getSeverityBadge = (sev: string) => {
    if (sev === 'CAO') {
      return (
        <span className="inline-flex items-center px-2 py-0.5 rounded text-[10px] font-extrabold uppercase bg-rose-500/15 text-rose-600 dark:text-rose-300 border border-rose-500/40">
          CAO
        </span>
      );
    }
    if (sev === 'TRUNG BÌNH') {
      return (
        <span className="inline-flex items-center px-2 py-0.5 rounded text-[10px] font-extrabold uppercase bg-amber-500/15 text-amber-600 dark:text-amber-300 border border-amber-500/40">
          TRUNG BÌNH
        </span>
      );
    }
    return (
      <span className="inline-flex items-center px-2 py-0.5 rounded text-[10px] font-extrabold uppercase bg-emerald-500/15 text-emerald-600 dark:text-emerald-300 border border-emerald-500/40">
        THẤP
      </span>
    );
  };

  const getKpiAccentGradient = (accentTheme?: string) => {
    switch (accentTheme) {
      case 'blue':
        return 'from-sky-400 to-blue-600';
      case 'navy':
        return 'from-blue-600 to-indigo-600';
      case 'green':
        return 'from-emerald-400 to-teal-500';
      case 'red':
        return 'from-rose-500 to-red-600';
      case 'amber':
        return 'from-amber-400 to-orange-500';
      case 'purple':
        return 'from-purple-500 to-indigo-600';
      default:
        return 'from-blue-500 to-cyan-500';
    }
  };

  const getKpiIcon = (idx: number, accentTheme?: string) => {
    switch (accentTheme || idx) {
      case 'blue':
      case 0:
        return <ShoppingBag className="w-4 h-4 text-sky-400" />;
      case 'navy':
      case 1:
        return <DollarSign className="w-4 h-4 text-indigo-400" />;
      case 'green':
      case 2:
        return <Percent className="w-4 h-4 text-emerald-400" />;
      case 'red':
      case 3:
        return <TrendingDown className="w-4 h-4 text-rose-400" />;
      case 'amber':
      case 4:
        return <Award className="w-4 h-4 text-amber-400" />;
      case 'purple':
      case 5:
        return <Package className="w-4 h-4 text-purple-400" />;
      default:
        return <Activity className="w-4 h-4 text-cyan-400" />;
    }
  };

  const renderChart = (card: any) => {
    const chartType = card.chart_type || 'bar';
    const cardData = card.data || [];

    // 1. Combo Chart (Bar on left Y-axis, Line on right Y-axis)
    if (chartType === 'combo') {
      return (
        <ResponsiveContainer width="100%" height="100%">
          <ComposedChart data={cardData} margin={{ top: 10, right: 15, left: -5, bottom: 20 }}>
            <CartesianGrid strokeDasharray="3 3" stroke={chartGridColor} />
            <XAxis
              dataKey={card.x_axis || 'period'}
              stroke={chartAxisColor}
              tick={{ fontSize: 10, fill: chartAxisColor }}
              interval={0}
              angle={-25}
              textAnchor="end"
            />
            <YAxis
              yAxisId="left"
              stroke={chartAxisColor}
              tick={{ fontSize: 10, fill: chartAxisColor }}
            />
            <YAxis
              yAxisId="right"
              orientation="right"
              stroke="#34D399"
              tick={{ fontSize: 10, fill: '#34D399' }}
              tickFormatter={(v) => `${v}%`}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: tooltipBg,
                borderColor: tooltipBorder,
                color: tooltipTextColor,
                borderRadius: 12,
                fontSize: 11,
              }}
            />
            <Legend wrapperStyle={{ fontSize: 11, paddingTop: 6 }} />
            {(card.bars || []).map((b: any, bIdx: number) => (
              <Bar
                key={bIdx}
                yAxisId={b.yAxisId || 'left'}
                dataKey={b.key}
                name={b.name}
                fill={b.color || '#2E86FF'}
                radius={[4, 4, 0, 0]}
              />
            ))}
            {(card.lines || []).map((l: any, lIdx: number) => (
              <Line
                key={lIdx}
                yAxisId={l.yAxisId || 'right'}
                type="monotone"
                dataKey={l.key}
                name={l.name}
                stroke={l.color || '#34D399'}
                strokeWidth={2.5}
                dot={{ r: 3 }}
              />
            ))}
          </ComposedChart>
        </ResponsiveContainer>
      );
    }

    // 2. Donut / Pie Chart
    if (chartType === 'donut' || chartType === 'pie') {
      return (
        <ResponsiveContainer width="100%" height="100%">
          <PieChart margin={{ top: 5, right: 5, left: 5, bottom: 5 }}>
            <Tooltip
              contentStyle={{
                backgroundColor: tooltipBg,
                borderColor: tooltipBorder,
                color: tooltipTextColor,
                borderRadius: 12,
                fontSize: 11,
              }}
              formatter={(value: any, name: any, item: any) => [
                `${value} tr (${item.payload.share_pct}%)`,
                name,
              ]}
            />
            <Legend wrapperStyle={{ fontSize: 11, paddingTop: 6 }} />
            <Pie
              data={cardData}
              dataKey="value"
              nameKey="category"
              innerRadius={50}
              outerRadius={80}
              paddingAngle={4}
            >
              {cardData.map((entry: any, index: number) => (
                <Cell key={`cell-${index}`} fill={entry.color || '#2E86FF'} />
              ))}
            </Pie>
          </PieChart>
        </ResponsiveContainer>
      );
    }

    // 3. Horizontal Bar Chart (Sorted category ranking)
    if (chartType === 'horizontal_bar') {
      return (
        <ResponsiveContainer width="100%" height="100%">
          <BarChart
            data={cardData}
            layout="vertical"
            margin={{ top: 5, right: 20, left: 80, bottom: 5 }}
          >
            <CartesianGrid strokeDasharray="3 3" stroke={chartGridColor} horizontal={false} />
            <XAxis
              type="number"
              stroke={chartAxisColor}
              tick={{ fontSize: 10, fill: chartAxisColor }}
            />
            <YAxis
              type="category"
              dataKey="category"
              stroke={chartAxisColor}
              tick={{ fontSize: 10, fill: chartAxisColor }}
              width={75}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: tooltipBg,
                borderColor: tooltipBorder,
                color: tooltipTextColor,
                borderRadius: 12,
                fontSize: 11,
              }}
              formatter={(v: any) => [`${v} tr`, 'Doanh thu']}
            />
            <Bar
              dataKey={card.bars?.[0]?.key || 'revenue_mil'}
              name={card.bars?.[0]?.name || 'Doanh thu (tr)'}
              fill="#2E86FF"
              radius={[0, 4, 4, 0]}
            >
              {cardData.map((entry: any, index: number) => (
                <Cell key={index} fill={entry.color || '#2E86FF'} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      );
    }

    // 4. Stacked Column / Bar Chart
    if (chartType === 'stacked_bar') {
      return (
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={cardData} margin={{ top: 10, right: 10, left: -10, bottom: 20 }}>
            <CartesianGrid strokeDasharray="3 3" stroke={chartGridColor} />
            <XAxis
              dataKey={card.x_axis || 'category'}
              stroke={chartAxisColor}
              tick={{ fontSize: 10, fill: chartAxisColor }}
              interval={0}
              angle={-25}
              textAnchor="end"
            />
            <YAxis stroke={chartAxisColor} tick={{ fontSize: 10, fill: chartAxisColor }} />
            <Tooltip
              contentStyle={{
                backgroundColor: tooltipBg,
                borderColor: tooltipBorder,
                color: tooltipTextColor,
                borderRadius: 12,
                fontSize: 11,
              }}
            />
            <Legend wrapperStyle={{ fontSize: 11, paddingTop: 6 }} />
            {(card.bars || []).map((b: any, bIdx: number) => (
              <Bar
                key={bIdx}
                dataKey={b.key}
                name={b.name}
                fill={b.color || '#2E86FF'}
                stackId="a"
              />
            ))}
          </BarChart>
        </ResponsiveContainer>
      );
    }

    // 5. Waterfall Chart (Revenue to Profit Flow)
    if (chartType === 'waterfall') {
      return (
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={cardData} margin={{ top: 10, right: 10, left: -10, bottom: 20 }}>
            <CartesianGrid strokeDasharray="3 3" stroke={chartGridColor} />
            <XAxis
              dataKey="category"
              stroke={chartAxisColor}
              tick={{ fontSize: 10, fill: chartAxisColor }}
              interval={0}
              angle={-20}
              textAnchor="end"
            />
            <YAxis stroke={chartAxisColor} tick={{ fontSize: 10, fill: chartAxisColor }} />
            <Tooltip
              contentStyle={{
                backgroundColor: tooltipBg,
                borderColor: tooltipBorder,
                color: tooltipTextColor,
                borderRadius: 12,
                fontSize: 11,
              }}
              formatter={(v: any) => [`${v} tr`, 'Giá trị']}
            />
            <Bar dataKey="amount_mil" radius={[4, 4, 0, 0]}>
              {cardData.map((entry: any, index: number) => (
                <Cell key={index} fill={entry.fill || '#2E86FF'} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      );
    }

    // 6. Grouped Bar or Standard Bar Chart
    return (
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={cardData} margin={{ top: 10, right: 10, left: -10, bottom: 20 }}>
          <CartesianGrid strokeDasharray="3 3" stroke={chartGridColor} />
          <XAxis
            dataKey={card.x_axis || 'category'}
            stroke={chartAxisColor}
            tick={{ fontSize: 10, fill: chartAxisColor }}
            interval={0}
            angle={-25}
            textAnchor="end"
          />
          <YAxis stroke={chartAxisColor} tick={{ fontSize: 10, fill: chartAxisColor }} />
          <Tooltip
            contentStyle={{
              backgroundColor: tooltipBg,
              borderColor: tooltipBorder,
              color: tooltipTextColor,
              borderRadius: 12,
              fontSize: 11,
            }}
          />
          <Legend wrapperStyle={{ fontSize: 11, paddingTop: 6 }} />
          {(card.bars || []).map((b: any, bIdx: number) => (
            <Bar
              key={bIdx}
              dataKey={b.key}
              name={b.name}
              fill={b.color || '#2E86FF'}
              radius={[4, 4, 0, 0]}
            />
          ))}
          {(card.lines || []).map((l: any, lIdx: number) => (
            <Line
              key={lIdx}
              type="monotone"
              dataKey={l.key}
              name={l.name}
              stroke={l.color || '#34D399'}
              strokeWidth={2.5}
              dot={{ r: 3 }}
            />
          ))}
        </BarChart>
      </ResponsiveContainer>
    );
  };

  if (loading) {
    return (
      <div className="p-16 text-center flex flex-col items-center justify-center space-y-4">
        <RefreshCw className="w-10 h-10 text-cyan-500 dark:text-cyan-400 animate-spin" />
        <h3 className="font-extrabold text-[var(--text-primary)] text-lg">Đang Phân Tích & Lập Kế Hoạch Báo Cáo Thích Ứng...</h3>
        <p className="text-xs text-[var(--text-secondary)] max-w-md">
          Hệ thống đang quét cấu trúc dữ liệu, lập kế hoạch trực quan hóa đa dạng biểu đồ và nhận diện các vấn đề kinh doanh thực tế.
        </p>
      </div>
    );
  }

  if (!report) {
    return (
      <div className="p-8 text-center text-[var(--text-secondary)]">
        Không có dữ liệu để tạo báo cáo. Vui lòng hoàn thành các bước trước đó.
      </div>
    );
  }

  const {
    data_scope,
    kpis,
    headline,
    planner_summary,
    cross_check_warning,
    main_problems,
    positive_signals,
    no_problems_message,
    problem_groups,
    chart_cards,
  } = report;

  const cardsMap = new Map((chart_cards || []).map((c: any) => [c.id, c]));

  return (
    <div className="p-6 md:p-8 max-w-[1500px] mx-auto space-y-8 animate-fadeIn" ref={dashboardRef}>
      {/* 1. Header & Data Scope */}
      <div className="border-b border-[var(--panel-border)] pb-6 space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <div className="flex items-center space-x-2">
              <span className="text-[10px] font-extrabold uppercase tracking-widest text-cyan-600 dark:text-cyan-400 bg-cyan-500/10 border border-cyan-500/30 px-2.5 py-0.5 rounded-full">
                BƯỚC 4: BÁO CÁO THÍCH ỨNG DỮ LIỆU
              </span>
              <span className="text-[11px] text-[var(--text-secondary)] flex items-center space-x-1">
                <Calendar className="w-3 h-3 text-cyan-500 dark:text-cyan-400" />
                <span>{data_scope?.date_range}</span>
              </span>
            </div>
            <h2 className="text-2xl md:text-3xl font-black text-[var(--text-primary)] tracking-tight mt-1">
              Báo Cáo Điều Hành & Giải Pháp Kinh Doanh
            </h2>
            <p className="text-xs text-[var(--text-secondary)] mt-1">
              {planner_summary}
            </p>
          </div>

          {/* Action Export Buttons */}
          <div className="flex items-center space-x-2.5 shrink-0">
            <a
              href={ApiService.getExcelExportUrl(sessionId)}
              download
              className="flex items-center space-x-1.5 px-3 py-2 text-xs font-bold rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white shadow-lg shadow-emerald-500/20 transition-all"
            >
              <FileSpreadsheet className="w-4 h-4" />
              <span>Xuất Excel</span>
            </a>
            <a
              href={ApiService.getPdfExportUrl(sessionId)}
              download
              className="flex items-center space-x-1.5 px-3 py-2 text-xs font-bold rounded-xl bg-blue-600 hover:bg-blue-500 text-white shadow-lg shadow-blue-500/20 transition-all"
            >
              <FileDown className="w-4 h-4" />
              <span>Xuất PDF</span>
            </a>
            <button
              onClick={handleExportPNG}
              disabled={exportingImage}
              className="flex items-center space-x-1.5 px-3 py-2 text-xs font-bold rounded-xl glass-card hover:bg-[var(--card-hover-bg)] text-[var(--text-primary)] border-[var(--panel-border)] transition-all"
            >
              <Image className="w-4 h-4 text-cyan-500" />
              <span>{exportingImage ? 'Đang xuất...' : 'Ảnh PNG'}</span>
            </button>
          </div>
        </div>

        {/* Cross-check warning if any */}
        {cross_check_warning && (
          <div className="p-3 bg-amber-500/10 border border-amber-500/30 rounded-xl text-xs text-amber-700 dark:text-amber-300 flex items-center space-x-2">
            <AlertTriangle className="w-4 h-4 text-amber-500 shrink-0" />
            <span className="font-semibold">{cross_check_warning}</span>
          </div>
        )}

        {/* Quality Scope Indicator */}
        <div className="flex flex-wrap items-center gap-3 text-xs">
          <div className="px-3 py-1.5 glass-card rounded-lg flex items-center space-x-2 border-[var(--panel-border)]">
            <Activity className="w-3.5 h-3.5 text-cyan-500 dark:text-cyan-400" />
            <span className="text-[var(--text-secondary)]">Quy mô toàn bộ:</span>
            <span className="font-mono font-bold text-[var(--text-primary)]">{data_scope?.order_count?.toLocaleString()} bản ghi</span>
          </div>

          <div className="px-3 py-1.5 glass-card rounded-lg flex items-center space-x-2 border-[var(--panel-border)]">
            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500 dark:text-emerald-400" />
            <span className="text-[var(--text-secondary)]">Điểm chất lượng:</span>
            <span className="font-mono font-bold text-emerald-600 dark:text-emerald-400">{data_scope?.quality_score}%</span>
          </div>

          {data_scope?.quality_warning && (
            <div className="px-3 py-1.5 bg-amber-500/10 border border-amber-500/30 text-amber-600 dark:text-amber-300 rounded-lg flex items-center space-x-2">
              <AlertTriangle className="w-3.5 h-3.5 text-amber-500 shrink-0" />
              <span>{data_scope.quality_warning}</span>
            </div>
          )}
        </div>
      </div>

      {/* 2. KPI Row with colored header bands matching reference screenshot */}
      {kpis && kpis.length > 0 && (
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3.5">
          {kpis.map((k: any, idx: number) => {
            const isAlert = k.is_negative_alert;
            const accentGrad = getKpiAccentGradient(k.accent_theme);

            return (
              <div
                key={k.id || idx}
                className="glass-card relative overflow-hidden flex flex-col justify-between border-[var(--card-border)] hover:border-cyan-400/40 transition-all shadow-sm"
              >
                {/* Colored Top Accent Header Band */}
                <div className={`h-1.5 w-full bg-gradient-to-r ${accentGrad}`} />

                <div className="p-4 space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-[10px] font-bold text-[var(--text-muted)] uppercase tracking-wider block truncate pr-1">
                      {k.label}
                    </span>
                    <div className="p-1 rounded-lg bg-[var(--bg-secondary)] border border-[var(--panel-border)] shrink-0">
                      {getKpiIcon(idx, k.accent_theme)}
                    </div>
                  </div>

                  <div className="text-xl md:text-2xl font-black font-mono text-[var(--text-primary)] tracking-tight">
                    {k.value}
                  </div>

                  <div className="pt-2 border-t border-[var(--panel-border)] flex items-center justify-between text-[10px]">
                    <span className="text-[var(--text-muted)] truncate max-w-[80px]">{k.subtext}</span>
                    <span className={`font-bold flex items-center space-x-0.5 ${
                      isAlert ? 'text-rose-500' : 'text-emerald-500'
                    }`}>
                      {k.change_label}
                    </span>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* 3. Headline Statement */}
      {headline && (
        <div className="glass-panel p-5 border-l-4 border-l-cyan-500 flex items-start space-x-3.5">
          <div className="w-8 h-8 rounded-lg bg-cyan-500/20 text-cyan-600 dark:text-cyan-400 flex items-center justify-center shrink-0 mt-0.5">
            <Sparkles className="w-4 h-4" />
          </div>
          <div>
            <h4 className="text-xs uppercase font-extrabold tracking-wider text-cyan-600 dark:text-cyan-400">
              Thông Điệp Quản Trị Trọng Tâm
            </h4>
            <p className="text-sm md:text-base font-bold text-[var(--text-primary)] mt-1">
              {headline}
            </p>
          </div>
        </div>
      )}

      {/* 4. VẤN ĐỀ CHÍNH (Xếp theo Mức độ × Tác động) */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <span className="w-2.5 h-2.5 rounded-full bg-rose-500 animate-pulse" />
            <h3 className="text-base font-black text-[var(--text-primary)] tracking-wide uppercase">
              VẤN ĐỀ TRỌNG TÂM CẦN XỬ LÝ
            </h3>
          </div>
          <span className="text-xs text-[var(--text-secondary)]">
            Tự động kích hoạt khi có sai lệch có ý nghĩa kinh doanh (&ge;10%)
          </span>
        </div>

        {main_problems && main_problems.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {main_problems.map((prob: any, idx: number) => (
              <div
                key={prob.id || idx}
                className="glass-card p-5 border-rose-500/30 flex flex-col justify-between hover:border-rose-500/50 transition-all shadow-sm"
              >
                <div className="space-y-3">
                  {/* Top Bar: Severity & Impact */}
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-2">
                      <span className="font-mono text-xs font-bold text-[var(--text-muted)]">#{idx + 1}</span>
                      {getSeverityBadge(prob.severity)}
                    </div>
                    {prob.impact_str && (
                      <span className="text-xs font-mono font-extrabold text-rose-600 dark:text-rose-400 bg-rose-500/10 px-2 py-0.5 rounded border border-rose-500/30">
                        {prob.impact_str}
                      </span>
                    )}
                  </div>

                  {/* Problem Title */}
                  <h4 className="font-bold text-[var(--text-primary)] text-sm leading-snug">
                    {prob.title}
                  </h4>

                  {/* Evidence Numbers */}
                  <div className="space-y-1 bg-[var(--bg-secondary)]/50 p-2.5 rounded-xl text-xs">
                    <span className="text-[10px] font-bold uppercase tracking-wider text-[var(--text-muted)] block">
                      Bằng chứng từ số liệu:
                    </span>
                    {prob.evidence?.map((ev: string, eIdx: number) => (
                      <div key={eIdx} className="text-[var(--text-secondary)] font-medium flex items-center space-x-1.5">
                        <span className="w-1.5 h-1.5 rounded-full bg-cyan-500 shrink-0" />
                        <span>{ev}</span>
                      </div>
                    ))}
                  </div>

                  {/* Probable Cause Hypothesis */}
                  <div className="text-xs text-[var(--text-secondary)]">
                    <strong className="text-[var(--text-primary)]">Nguyên nhân giả định: </strong>
                    <span>{prob.probable_cause}</span>
                  </div>

                  {/* Action */}
                  <div className="text-xs p-2.5 rounded-lg bg-emerald-500/10 border border-emerald-500/30 text-emerald-700 dark:text-emerald-300">
                    <strong>Đề xuất hành động: </strong>
                    <span>{prob.action}</span>
                  </div>
                </div>

                {/* Footer Action Links */}
                <div className="mt-4 pt-3 border-t border-[var(--panel-border)] flex items-center justify-between text-xs">
                  {prob.linked_chart_id ? (
                    <button
                      onClick={() => scrollToChart(prob.linked_chart_id)}
                      className="text-cyan-600 dark:text-cyan-400 hover:underline font-bold flex items-center space-x-1"
                    >
                      <span>Xem biểu đồ</span>
                      <ArrowRight className="w-3.5 h-3.5" />
                    </button>
                  ) : <span />}

                  {prob.pivot_preset && (
                    <button
                      onClick={() => onOpenPivotForProblem(prob.pivot_preset)}
                      className="text-[var(--text-secondary)] hover:text-[var(--text-primary)] font-medium flex items-center space-x-1 bg-[var(--bg-secondary)] px-2 py-1 rounded"
                    >
                      <span>Mở PivotChart</span>
                      <ExternalLink className="w-3 h-3" />
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="glass-panel p-6 border-emerald-500/30 space-y-3">
            <div className="flex items-center space-x-2 text-emerald-600 dark:text-emerald-400 font-bold">
              <ShieldCheck className="w-5 h-5" />
              <span>{no_problems_message || 'Không phát hiện vấn đề vượt ngưỡng trong dữ liệu này.'}</span>
            </div>
            {positive_signals && positive_signals.length > 0 && (
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-2">
                {positive_signals.map((sig: any, sIdx: number) => (
                  <div key={sIdx} className="p-3 bg-emerald-500/10 rounded-xl border border-emerald-500/20 text-xs">
                    <span className="font-bold text-[var(--text-primary)] block mb-0.5">{sig.title}</span>
                    <span className="text-[var(--text-secondary)]">{sig.detail}</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>

      {/* 5. CÁC NHÓM BIỂU ĐỒ BẢO CHỨNG THEO VẤN ĐỀ */}
      {problem_groups && problem_groups.length > 0 && (
        <div className="space-y-10">
          <div className="border-t border-[var(--panel-border)] pt-8">
            <h3 className="text-lg font-black text-[var(--text-primary)] uppercase tracking-wide">
              CÁC NHÓM BIỂU ĐỒ BẢO CHỨNG CHI TIẾT
            </h3>
            <p className="text-xs text-[var(--text-secondary)] mt-0.5">
              Mỗi biểu đồ đi kèm nhận định chi tiết, bằng chứng cụ thể và giả định nguyên nhân được kiểm chứng trực tiếp từ toàn bộ dữ liệu thực tế.
            </p>
          </div>

          {problem_groups.map((group: any) => {
            const groupCards = (group.chart_ids || [])
              .map((id: string) => cardsMap.get(id))
              .filter(Boolean);

            if (groupCards.length === 0) return null;

            return (
              <div key={group.id} className="space-y-4">
                {/* Group Header */}
                <div className="p-4 glass-panel border-l-4 border-l-blue-500 flex flex-col md:flex-row md:items-center justify-between gap-2">
                  <div>
                    <h4 className="font-extrabold text-[var(--text-primary)] text-base">
                      {group.title}
                    </h4>
                    <p className="text-xs text-[var(--text-secondary)] mt-0.5">
                      {group.problem_statement}
                    </p>
                  </div>
                  <span className="text-[11px] font-mono text-[var(--text-muted)] bg-[var(--bg-secondary)] px-2.5 py-1 rounded-full shrink-0">
                    {groupCards.length} biểu đồ liên kết
                  </span>
                </div>

                {/* Group Charts Grid */}
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
                  {groupCards.map((card: any) => {
                    const an = card.analysis || {};

                    return (
                      <div
                        key={card.id}
                        id={card.id}
                        className="glass-card p-5 flex flex-col justify-between space-y-4 hover:border-cyan-400/40 transition-all"
                      >
                        {/* Card Title & Pivot Quick Link */}
                        <div className="flex items-start justify-between gap-3">
                          <div>
                            <div className="flex items-center space-x-2">
                              <span className="text-[9px] font-extrabold uppercase px-1.5 py-0.5 rounded bg-blue-500/10 text-blue-500 dark:text-blue-400 border border-blue-500/20">
                                {card.chart_type}
                              </span>
                              <h5 className="font-extrabold text-[var(--text-primary)] text-sm leading-snug">
                                {card.title}
                              </h5>
                            </div>
                            {card.source_line && (
                              <span className="text-[10px] font-mono text-[var(--text-muted)] block mt-1">
                                {card.source_line}
                              </span>
                            )}
                          </div>
                          {card.pivot_config && (
                            <button
                              onClick={() => onOpenPivotForProblem(card.pivot_config)}
                              className="text-[10px] font-bold text-cyan-600 dark:text-cyan-400 hover:underline flex items-center space-x-1 shrink-0 bg-cyan-500/10 px-2 py-1 rounded border border-cyan-500/20"
                              title="Mở phân tích sâu trong PivotChart"
                            >
                              <BarChart2 className="w-3 h-3" />
                              <span>Pivot</span>
                            </button>
                          )}
                        </div>

                        {/* Chart Render */}
                        <div className="h-64 w-full pt-2">
                          {renderChart(card)}
                        </div>

                        {/* Analysis Block (4 Lines) */}
                        <div className="space-y-1.5 text-xs bg-[var(--bg-secondary)]/50 p-3.5 rounded-xl border border-[var(--panel-border)]">
                          {an.phat_hien && (
                            <p className="text-[var(--text-primary)] leading-relaxed">
                              <strong className="text-cyan-600 dark:text-cyan-400">Phát hiện: </strong>
                              {an.phat_hien}
                            </p>
                          )}
                          {an.bang_chung && (
                            <p className="text-[var(--text-secondary)] leading-relaxed">
                              <strong className="text-[var(--text-primary)]">Bằng chứng: </strong>
                              {an.bang_chung}
                            </p>
                          )}
                          {an.y_nghia && (
                            <p className="text-[var(--text-secondary)] leading-relaxed">
                              <strong className="text-amber-600 dark:text-amber-400">Ý nghĩa: </strong>
                              {an.y_nghia}
                            </p>
                          )}
                          {an.de_xuat && (
                            <p className="text-emerald-700 dark:text-emerald-300 leading-relaxed">
                              <strong>Đề xuất: </strong>
                              {an.de_xuat}
                            </p>
                          )}
                        </div>
                      </div>
                    );
                  })}
                </div>

                {/* Group Conclusion */}
                {group.conclusion && (
                  <div className="p-3 bg-[var(--card-bg)] rounded-xl border border-[var(--panel-border)] text-xs text-[var(--text-secondary)] italic">
                    <strong>Kết luận nhóm: </strong>
                    {group.conclusion}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}

      {/* Empty State when no charts could be planned */}
      {(!chart_cards || chart_cards.length === 0) && (
        <div className="glass-panel p-12 text-center space-y-4">
          <div className="w-12 h-12 rounded-2xl bg-amber-500/10 text-amber-500 mx-auto flex items-center justify-center">
            <AlertTriangle className="w-6 h-6" />
          </div>
          <h4 className="font-extrabold text-[var(--text-primary)] text-base">
            Không Có Biểu Đồ Nào Phù Hợp Để Hiển Thị
          </h4>
          <p className="text-xs text-[var(--text-secondary)] max-w-md mx-auto">
            {planner_summary || 'Tệp dữ liệu thiếu các cột số đo hoặc không đủ danh mục để vẽ biểu đồ.'}
          </p>
        </div>
      )}
    </div>
  );
};

export default ReportPage;
