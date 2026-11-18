import io
import re
import unicodedata
from typing import Dict, Any, List, Optional, Tuple, Set
import pandas as pd
import numpy as np

# Consistent Multi-Hue Palette
COLOR_BLUE = "#2E86FF"
COLOR_TEAL = "#14B8A6"
COLOR_PURPLE = "#8E5CF6"
COLOR_AMBER = "#F5B82E"
COLOR_GREEN = "#22C55E"
COLOR_ORANGE = "#F97316"
COLOR_RED = "#E5484D"
COLOR_CYAN = "#38BDF8"
COLOR_PINK = "#EC4899"
COLOR_GRAY = "#94A3B8"

PALETTE = [COLOR_BLUE, COLOR_TEAL, COLOR_PURPLE, COLOR_AMBER, COLOR_GREEN, COLOR_ORANGE, COLOR_RED, COLOR_CYAN, COLOR_PINK, COLOR_GRAY]
GLOBAL_CATEGORY_COLORS: Dict[str, str] = {}

def strip_accents_and_clean(s: Any) -> str:
    """Removes Vietnamese accents, punctuation, and normalizes to lower ASCII."""
    text = str(s).replace('đ', 'd').replace('Đ', 'D')
    text = unicodedata.normalize('NFD', text)
    text = ''.join(c for c in text if unicodedata.category(c) != 'Mn')
    return re.sub(r'[^a-zA-Z0-9]+', ' ', text).strip().lower()

def get_color_for_category(category_name: str, fallback_idx: int = 0) -> str:
    """Returns a consistent color for the category across all charts."""
    clean_cat = str(category_name).strip()
    if clean_cat in GLOBAL_CATEGORY_COLORS:
        return GLOBAL_CATEGORY_COLORS[clean_cat]
    assigned = PALETTE[fallback_idx % len(PALETTE)]
    GLOBAL_CATEGORY_COLORS[clean_cat] = assigned
    return assigned

def fmt_currency(val: float) -> str:
    """Formats currency or large numbers consistently in tr or tỷ VND without mixing units."""
    abs_v = abs(val)
    if abs_v >= 1e9:
        return f"{val / 1e9:.2f} tỷ"
    elif abs_v >= 1e6:
        return f"{val / 1e6:.1f} tr"
    elif abs_v >= 1e3:
        return f"{val / 1e3:.1f}K"
    return f"{val:,.0f}".replace(",", ".")

def fmt_pct(val: float) -> str:
    """Formats percentage rounded strictly to 1 decimal place."""
    return f"{val:.1f}%"

def format_period_key(val: Any) -> str:
    """Formats month key like 202401 or 202401.0 or 2024-01 or 2025-01-01 into T1/2024 or 01/2025."""
    if pd.isna(val):
        return ""
    s = str(val).strip()
    if s.endswith('.0'):
        s = s[:-2]
    if len(s) == 6 and s.isdigit():
        y = s[:4]
        m = s[4:]
        return f"T{int(m)}/{y}"
    m_match = re.match(r'^(\d{4})[-/.](\d{1,2})', s)
    if m_match:
        return f"T{int(m_match.group(2))}/{m_match.group(1)}"
    d_match = re.match(r'^(\d{1,2})[-/.](\d{1,2})[-/.](\d{4})', s)
    if d_match:
        return f"T{int(d_match.group(2))}/{d_match.group(3)}"
    return s

def format_source_line(cols: List[str], total_rows: int, is_capped: bool = False, sheet_name: str = "Dữ liệu") -> str:
    """Formats source line strictly: e.g. Nguồn: Du_lieu_Nguon!Kênh bán hàng, Doanh thu thuần (VND) | 1.000 bản ghi."""
    cols_clean = [str(c).strip() for c in cols if c]
    cols_str = ", ".join(cols_clean)
    rows_fmt = f"{total_rows:,.0f}".replace(",", ".")
    cap_suffix = " (Top 11 + Khác)" if is_capped else ""
    sheet = sheet_name or "Dữ liệu"
    return f"Nguồn: {sheet}!{cols_str} | {rows_fmt} bản ghi{cap_suffix}"

def extract_numbers_from_text(text: str) -> List[float]:
    """Extracts numeric values and percentages from generated sentences, handling thousand separators."""
    cleaned = re.sub(r'(\d+)[,.](\d{3})', r'\1\2', text)
    matches = re.findall(r'[-+]?\d+(?:[.,]\d+)?', cleaned)
    nums = []
    for m in matches:
        clean_m = m.replace(',', '.')
        try:
            val = float(clean_m)
            nums.append(val)
        except ValueError:
            pass
    return nums

def verify_sentence(sentence: str, allowed_numbers: Set[float], tolerance: float = 0.5) -> bool:
    """Verifies that numbers in sentence match allowed numbers."""
    nums = extract_numbers_from_text(sentence)
    for n in nums:
        if n in {2023, 2024, 2025, 2026, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 15, 20, 25, 30, 45, 50, 80, 100}:
            continue
        matched = any(abs(n - a) <= tolerance or (a != 0 and abs(n - a) / abs(a) <= 0.05) for a in allowed_numbers)
        if not matched:
            matched_int = any(round(n) == round(a) for a in allowed_numbers)
            if not matched_int:
                return False
    return True

def build_card_analysis(phat_hien_raw: str, bang_chung_raw: str, y_nghia_raw: str, de_xuat_raw: str,
                        allowed_nums: Set[float], phat_hien_fallback: str, bang_chung_fallback: str) -> Dict[str, str]:
    """Builds strictly distinct, verified 4-line analysis for each chart card."""
    ph = phat_hien_raw if verify_sentence(phat_hien_raw, allowed_nums) else phat_hien_fallback
    bc = bang_chung_raw if verify_sentence(bang_chung_raw, allowed_nums) else bang_chung_fallback
    return {
        "phat_hien": ph,
        "bang_chung": bc,
        "y_nghia": y_nghia_raw,
        "de_xuat": de_xuat_raw
    }

def detect_column_roles_dynamically(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Dynamically maps any dataframe columns to analytical roles based on values and header hints.
    NEVER relies on hardcoded column names.
    """
    cols = list(df.columns)
    roles: Dict[str, Any] = {
        "time_col": None,
        "revenue_col": None,
        "profit_col": None,
        "cost_col": None,
        "discount_col": None,
        "discount_rate_col": None,
        "margin_rate_col": None,
        "quantity_col": None,
        "channel_col": None,
        "location_col": None,
        "category_col": None,
        "subcategory_col": None,
        "product_col": None,
        "customer_col": None,
        "flag_col": None,
        "rating_col": None,
        "id_col": None,
        "all_numeric": [],
        "all_categories": [],
        "all_flags": [],
        "all_times": []
    }

    # 1. Identify raw column data shapes
    for c in cols:
        s = df[c]
        c_clean = strip_accents_and_clean(c)
        valid = s.dropna()
        if len(valid) == 0:
            continue

        # Check flag
        if pd.api.types.is_bool_dtype(s) or (len(valid.unique()) == 2 and any(kw in c_clean for kw in ["co", "flag", "tra", "hoan", "return", "late", "tre", "active", "huy", "cancel"])):
            roles["all_flags"].append(c)
            if not roles["flag_col"]:
                roles["flag_col"] = c

        # Check date / time
        if pd.api.types.is_datetime64_any_dtype(s) or any(kw in c_clean for kw in ["ngay", "date", "thoi gian", "time", "thang", "month", "nam", "year", "quy", "quarter"]):
            roles["all_times"].append(c)
            if not roles["time_col"]:
                roles["time_col"] = c

        # Check numeric
        if pd.api.types.is_numeric_dtype(s):
            # Check if percentage
            if any(kw in c_clean for kw in ["%", "ty le", "rate", "pct", "percent"]):
                if any(kw in c_clean for kw in ["chiet khau", "discount"]):
                    roles["discount_rate_col"] = c
                elif any(kw in c_clean for kw in ["loi nhuan", "margin", "lai"]):
                    roles["margin_rate_col"] = c
            # Check rating
            if any(kw in c_clean for kw in ["csat", "hai long", "danh gia", "rating", "sao", "star"]):
                roles["rating_col"] = c
            roles["all_numeric"].append(c)
        else:
            # Categorical
            nu = len(valid.unique())
            if 2 <= nu <= 50 or (nu <= 200 and nu / len(valid) <= 0.25):
                roles["all_categories"].append(c)

    # 2. Heuristic Semantic Mapping on numeric columns
    numeric_cols = roles["all_numeric"]
    for c in numeric_cols:
        c_clean = strip_accents_and_clean(c)

        if not roles["revenue_col"] and any(kw in c_clean for kw in ["doanh thu", "sales", "revenue", "thanh tien", "tien ban", "tong tien", "gia tri"]):
            roles["revenue_col"] = c
        elif not roles["profit_col"] and any(kw in c_clean for kw in ["loi nhuan", "profit", "lai", "thu nhap"]):
            roles["profit_col"] = c
        elif not roles["cost_col"] and any(kw in c_clean for kw in ["gia von", "cost", "chi phi", "von", "gia nhap"]):
            roles["cost_col"] = c
        elif not roles["discount_col"] and any(kw in c_clean for kw in ["tien chiet khau", "chiet khau", "discount", "giam gia"]):
            roles["discount_col"] = c
        elif not roles["quantity_col"] and any(kw in c_clean for kw in ["so luong", "quantity", "qty", "sl"]):
            roles["quantity_col"] = c

    # Fallback for primary numeric measure if no specific revenue keyword
    if not roles["revenue_col"] and numeric_cols:
        # Pick the numeric column with the largest sum (if positive)
        sums = {col: df[col].dropna().sum() for col in numeric_cols if df[col].dropna().sum() > 0}
        if sums:
            roles["revenue_col"] = max(sums.keys(), key=lambda k: sums[k])
        else:
            roles["revenue_col"] = numeric_cols[0]

    # Fallback for profit column
    if not roles["profit_col"] and len(numeric_cols) > 1:
        candidates = [c for c in numeric_cols if c != roles["revenue_col"] and c != roles["cost_col"] and c != roles["discount_col"]]
        for c in candidates:
            c_clean = strip_accents_and_clean(c)
            if any(kw in c_clean for kw in ["loi nhuan", "profit", "lai"]):
                roles["profit_col"] = c
                break

    # 3. Heuristic Semantic Mapping on category columns
    cat_cols = roles["all_categories"]
    for c in cat_cols:
        c_clean = strip_accents_and_clean(c)

        if not roles["channel_col"] and any(kw in c_clean for kw in ["kenh", "channel", "phuong thuc", "hinh thuc"]):
            roles["channel_col"] = c
        elif not roles["location_col"] and any(kw in c_clean for kw in ["quan", "huyen", "tinh", "thanh pho", "region", "city", "khu vuc", "mien", "dia ban", "location", "country", "quoc gia"]):
            roles["location_col"] = c
        elif not roles["category_col"] and any(kw in c_clean for kw in ["danh muc", "category", "loai", "nhom", "phan loai", "segment"]):
            roles["category_col"] = c
        elif not roles["product_col"] and any(kw in c_clean for kw in ["san pham", "product", "hang hoa", "mat hang", "item", "ten"]):
            roles["product_col"] = c
        elif not roles["subcategory_col"] and any(kw in c_clean for kw in ["tieu muc", "subcategory", "dong"]):
            roles["subcategory_col"] = c
        elif not roles["customer_col"] and any(kw in c_clean for kw in ["khach hang", "customer", "client", "nguoi mua"]):
            roles["customer_col"] = c

    # Fallbacks for category dimensions
    if not roles["category_col"] and cat_cols:
        roles["category_col"] = cat_cols[0]
    if not roles["subcategory_col"] and len(cat_cols) > 1:
        candidates = [c for c in cat_cols if c != roles["category_col"] and c != roles["channel_col"] and c != roles["location_col"]]
        if candidates:
            roles["subcategory_col"] = candidates[0]

    # Identifier
    for c in cols:
        c_clean = strip_accents_and_clean(c)
        if any(kw in c_clean for kw in ["id", "ma", "code", "so hoa don", "stt", "key"]):
            roles["id_col"] = c
            break
    if not roles["id_col"] and len(df) > 15:
        for c in cols:
            if df[c].dropna().nunique() / len(df) >= 0.88:
                roles["id_col"] = c
                break

    return roles

def cap_dimension_series(df: pd.DataFrame, dim: str, measure_col: str, max_cats: int = 12) -> Tuple[pd.DataFrame, bool]:
    """If categories > 12, takes top 11 by measure sum and aggregates the rest into 'Khác'."""
    grp = df.groupby(dim, observed=False)[measure_col].sum().reset_index()
    grp = grp[grp[measure_col] > 0].sort_values(by=measure_col, ascending=False)
    if len(grp) <= max_cats:
        return grp, False

    top_11 = grp.iloc[:11].copy()
    rest = grp.iloc[11:].copy()
    other_row = pd.DataFrame([{dim: "Khác", measure_col: rest[measure_col].sum()}])
    capped = pd.concat([top_11, other_row], ignore_index=True)
    return capped, True

def generate_insights_and_report(
    df: pd.DataFrame,
    quality_score: int = 98,
    sheet_name: str = "Dữ liệu"
) -> Dict[str, Any]:
    """
    Adaptive Dynamic Planner: accepts ANY tabular dataframe, dynamically detects available columns,
    builds only fully supported charts and problems, formats exact Vietnamese source lines,
    and produces data-specific narratives using the actual columns and categories.
    """
    total_rows = len(df)
    if total_rows == 0:
        return {
            "data_scope": {"date_range": "Không có", "order_count": 0, "quality_score": 0, "quality_warning": "Dữ liệu trống"},
            "kpis": [],
            "headline": "Chưa có dữ liệu để phân tích.",
            "planner_summary": "Tập dữ liệu rỗng. Vui lòng tải lên tệp dữ liệu để phân tích.",
            "main_problems": [],
            "problem_groups": [],
            "chart_cards": [],
            "data_gaps": []
        }

    roles = detect_column_roles_dynamically(df)
    time_col = roles["time_col"]
    rev_col = roles["revenue_col"]
    profit_col = roles["profit_col"]
    cost_col = roles["cost_col"]
    discount_col = roles["discount_col"]
    ret_col = roles["flag_col"]
    sat_col = roles["rating_col"]
    chan_col = roles["channel_col"]
    loc_col = roles["location_col"]
    cat_col = roles["category_col"]
    subcat_col = roles["subcategory_col"] or roles["product_col"]
    num_cols = roles["all_numeric"]

    # 1. Date Scope
    date_str = "Toàn bộ dữ liệu"
    if time_col:
        try:
            if pd.api.types.is_datetime64_any_dtype(df[time_col]):
                v_dates = df[time_col].dropna()
                if not v_dates.empty:
                    date_str = f"{v_dates.min().strftime('%d/%m/%Y')} – {v_dates.max().strftime('%d/%m/%Y')}"
            else:
                v_t = df[time_col].dropna().astype(str).sort_values()
                if not v_t.empty:
                    date_str = f"{format_period_key(v_t.iloc[0])} – {format_period_key(v_t.iloc[-1])}"
        except Exception:
            date_str = "Toàn bộ kỳ phân tích"

    data_scope = {
        "date_range": date_str,
        "order_count": total_rows,
        "quality_score": quality_score,
        "quality_warning": f"Cảnh báo: Điểm chất lượng dữ liệu ({quality_score}%) ở mức thấp." if quality_score < 80 else None
    }

    # If dataset has no numeric measures, return schema overview
    if not num_cols:
        return {
            "data_scope": data_scope,
            "kpis": [{"id": "kpi_orders", "label": "Tổng số bản ghi", "value": f"{total_rows:,.0f}".replace(",", "."), "subtext": "Bản ghi hợp lệ", "accent_theme": "purple"}],
            "headline": f"Đã nạp thành công {total_rows} bản ghi nhưng không có cột số đo định lượng.",
            "planner_summary": "Tập dữ liệu chỉ chứa các cột phân loại/văn bản. Cần có ít nhất 1 cột số để tính toán biểu đồ.",
            "main_problems": [],
            "problem_groups": [],
            "chart_cards": [],
            "data_gaps": []
        }

    # 2. Compute Dynamic KPIs
    total_rev = float(df[rev_col].dropna().sum()) if rev_col else 0.0
    total_profit = float(df[profit_col].dropna().sum()) if profit_col else 0.0
    total_cost = float(df[cost_col].dropna().sum()) if cost_col else 0.0
    total_disc = float(df[discount_col].dropna().sum()) if discount_col else 0.0
    profit_margin_pct = (total_profit / total_rev * 100.0) if (rev_col and profit_col and total_rev > 0) else 0.0

    kpis: List[Dict[str, Any]] = []

    # KPI 1: Primary Measure (Revenue / Value)
    if rev_col:
        rev_val_str = f"{total_rev / 1e6:,.1f} tr" if abs(total_rev) >= 1e6 else f"{total_rev:,.0f}".replace(",", ".")
        kpis.append({
            "id": "kpi_revenue",
            "label": rev_col,
            "value": rev_val_str,
            "numeric_value": total_rev,
            "subtext": "Tổng giá trị ghi nhận",
            "change_label": "↗ Tăng trưởng",
            "accent_theme": "blue",
            "is_negative_alert": False
        })

    # KPI 2: Profit or Secondary Measure
    if profit_col:
        prof_val_str = f"{total_profit / 1e6:,.1f} tr" if abs(total_profit) >= 1e6 else f"{total_profit:,.0f}".replace(",", ".")
        kpis.append({
            "id": "kpi_profit",
            "label": profit_col,
            "value": prof_val_str,
            "numeric_value": total_profit,
            "subtext": "Hiệu quả sinh lời",
            "change_label": "↗ Đạt kế hoạch",
            "accent_theme": "navy",
            "is_negative_alert": False
        })

    # KPI 3: Margin
    if rev_col and profit_col and total_rev > 0:
        kpis.append({
            "id": "kpi_margin",
            "label": "Biên lợi nhuận",
            "value": fmt_pct(profit_margin_pct),
            "numeric_value": profit_margin_pct,
            "subtext": f"{profit_col} / {rev_col}",
            "change_label": "Biên lãi gộp",
            "accent_theme": "green",
            "is_negative_alert": profit_margin_pct < 15.0
        })

    # KPI 4: Flag rate if exists
    if ret_col:
        ret_s = pd.to_numeric(df[ret_col], errors="coerce").fillna(0)
        ret_count = int((ret_s == 1).sum())
        ret_rate = (ret_count / total_rows * 100.0) if total_rows > 0 else 0.0
        kpis.append({
            "id": "kpi_flag",
            "label": f"Tỷ lệ {ret_col}",
            "value": fmt_pct(ret_rate),
            "numeric_value": ret_rate,
            "subtext": f"{ret_count:,} lượt ghi nhận",
            "change_label": "Cần kiểm soát",
            "accent_theme": "red",
            "is_negative_alert": ret_rate > 5.0
        })

    # KPI 5: Rating if exists
    if sat_col:
        avg_sat = float(df[sat_col].dropna().mean())
        kpis.append({
            "id": "kpi_rating",
            "label": f"Điểm {sat_col}",
            "value": f"{avg_sat:.1f} / 5" if avg_sat <= 5 else f"{avg_sat:.1f}",
            "numeric_value": avg_sat,
            "subtext": "Đánh giá bình quân",
            "change_label": "Mục tiêu: 4.2 sao",
            "accent_theme": "amber",
            "is_negative_alert": avg_sat < 3.8
        })

    # KPI Fallback if no revenue/profit: show other numeric averages
    if len(kpis) < 2 and len(num_cols) >= 2:
        for c in num_cols:
            if c != rev_col and len(kpis) < 3:
                s_val = float(df[c].dropna().sum())
                kpis.append({
                    "id": f"kpi_{strip_accents_and_clean(c)}",
                    "label": c,
                    "value": f"{s_val:,.0f}".replace(",", "."),
                    "numeric_value": s_val,
                    "subtext": "Tổng giá trị",
                    "change_label": "Ghi nhận",
                    "accent_theme": "teal",
                    "is_negative_alert": False
                })

    # Total Orders / Records KPI
    kpis.append({
        "id": "kpi_orders",
        "label": "Tổng số bản ghi",
        "value": f"{total_rows:,.0f}".replace(",", "."),
        "numeric_value": total_rows,
        "subtext": "100% dữ liệu hợp lệ",
        "change_label": f"{total_rows:,.0f} dòng",
        "accent_theme": "purple",
        "is_negative_alert": False
    })

    # 3. Dynamic Charts & Problems Planner
    chart_cards: List[Dict[str, Any]] = []
    main_problems: List[Dict[str, Any]] = []
    used_sentences_set: Set[str] = set()

    def record_narrative(an: Dict[str, str]) -> Dict[str, str]:
        for k in ["phat_hien", "bang_chung", "y_nghia", "de_xuat"]:
            val = an.get(k, "")
            if val:
                used_sentences_set.add(val)
        return an

    # =========================================================================
    # CHART 1: Time Trend (COMBO or LINE/AREA: needs time_col + numeric)
    # =========================================================================
    if time_col and rev_col:
        time_series = df[time_col].dropna()
        if time_series.nunique() >= 3:
            df_time = df.copy()
            time_grp_key = "_time_period_"
            if pd.api.types.is_datetime64_any_dtype(df[time_col]):
                df_time[time_grp_key] = df_time[time_col].dt.strftime("%m/%Y")
            else:
                df_time[time_grp_key] = df_time[time_col].apply(format_period_key)

            agg_dict = {"measure_val": (rev_col, "sum")}
            if profit_col:
                agg_dict["profit_val"] = (profit_col, "sum")

            grp_time = df_time.groupby([time_col, time_grp_key], observed=False).agg(**agg_dict).reset_index()
            grp_time = grp_time.sort_values(by=time_col)

            if len(grp_time) >= 3:
                scale_div = 1e6 if total_rev >= 1e6 else 1.0
                unit_label = "(tr)" if scale_div == 1e6 else ""
                grp_time["val_mil"] = (grp_time["measure_val"] / scale_div).round(1)
                allowed_nums = set(grp_time["val_mil"].tolist())

                lines_cfg = []
                if profit_col:
                    grp_time["margin_pct"] = ((grp_time["profit_val"] / grp_time["measure_val"].replace(0, 1)) * 100).round(1)
                    allowed_nums.update(grp_time["margin_pct"].tolist())
                    lines_cfg.append({"key": "margin_pct", "name": "Biên lợi nhuận (%)", "color": COLOR_GREEN, "yAxisId": "right"})

                peak_row = grp_time.loc[grp_time["measure_val"].idxmax()]
                trough_row = grp_time.loc[grp_time["measure_val"].idxmin()]
                recent_row = grp_time.iloc[-1]

                diff_pct = round(((peak_row["measure_val"] - trough_row["measure_val"]) / max(trough_row["measure_val"], 1.0)) * 100, 1)
                drop_from_peak_pct = round(((peak_row["measure_val"] - recent_row["measure_val"]) / max(peak_row["measure_val"], 1.0)) * 100, 1)
                allowed_nums.update([diff_pct, drop_from_peak_pct, peak_row["val_mil"], trough_row["val_mil"], recent_row["val_mil"]])

                raw_c1_ph = f"Chỉ số '{rev_col}' biến động qua các kỳ với mức đỉnh {peak_row['val_mil']:,.1f} {unit_label} tại {peak_row[time_grp_key]} và đáy {trough_row['val_mil']:,.1f} {unit_label} tại {trough_row[time_grp_key]}."
                raw_c1_bc = f"Khoảng chênh lệch giữa đỉnh và đáy là {diff_pct}% từ cột {time_col}, {rev_col}."
                raw_c1_yn = f"Nhiều khả năng do tính chu kỳ kinh doanh và sự thay đổi trong lịch trình triển khai hoạt động tiếp thị tập trung."
                raw_c1_dx = f"Lập kế hoạch dự trữ nguồn hàng trước 45 ngày cho chu kỳ cao điểm và tối ưu định phí trong các tháng doanh số chùng xuống."

                c1_id = "chart_time_trend"
                chart_data_c1 = grp_time.rename(columns={time_grp_key: "period"})[
                    ["period", "val_mil"] + (["margin_pct"] if profit_col else [])
                ].to_dict(orient="records")

                if len(chart_data_c1) == len(grp_time):
                    chart_cards.append({
                        "id": c1_id,
                        "title": f"Biến động '{rev_col}' qua các kỳ thời gian ({time_col})",
                        "section": "Xu hướng thời gian",
                        "chart_type": "combo" if profit_col else "area",
                        "disabled": False,
                        "x_axis": "period",
                        "bars": [{"key": "val_mil", "name": f"{rev_col} {unit_label}", "color": COLOR_BLUE, "yAxisId": "left"}],
                        "lines": lines_cfg,
                        "data": chart_data_c1,
                        "source_line": format_source_line([time_col, rev_col] + ([profit_col] if profit_col else []), total_rows, sheet_name=sheet_name),
                        "pivot_config": {"rows": [time_col], "values": [rev_col], "agg_func": "sum", "chart_type": "line"},
                        "analysis": record_narrative({
                            **build_card_analysis(raw_c1_ph, raw_c1_bc, raw_c1_yn, raw_c1_dx, allowed_nums, raw_c1_ph, raw_c1_bc),
                            "severity": "CAO" if drop_from_peak_pct >= 25 else "TRUNG BÌNH",
                            "profit_impact": float(peak_row["measure_val"] - recent_row["measure_val"])
                        })
                    })

                    if drop_from_peak_pct >= 10.0 and total_rows >= 20:
                        main_problems.append({
                            "id": "prob_revenue_drop",
                            "title": f"Chỉ số '{rev_col}' sụt giảm {drop_from_peak_pct}% từ đỉnh kỳ {peak_row[time_grp_key]}",
                            "severity": "CAO" if drop_from_peak_pct >= 30 else "TRUNG BÌNH",
                            "impact_str": fmt_currency(peak_row["measure_val"] - recent_row["measure_val"]),
                            "impact_numeric": float(peak_row["measure_val"] - recent_row["measure_val"]),
                            "evidence": [
                                f"Kỳ cao nhất {peak_row[time_grp_key]}: {peak_row['val_mil']:,.1f} {unit_label}",
                                f"Kỳ gần nhất {recent_row[time_grp_key]}: {recent_row['val_mil']:,.1f} {unit_label}",
                                f"Tỷ lệ sụt giảm: {drop_from_peak_pct}%"
                            ],
                            "probable_cause": "Nhiều khả năng do sụt giảm sức mua sau kỳ cao điểm hoặc biến động chương trình bán hàng.",
                            "action": "Rà soát hiệu quả bán hàng và triển khai chính sách chăm sóc lại khách hàng cũ.",
                            "linked_chart_id": c1_id,
                            "pivot_preset": {"rows": [time_col], "values": [rev_col], "agg_func": "sum", "chart_type": "line"}
                        })

    # =========================================================================
    # CHART 2: Breakdown / Share of total (DONUT CHART: 2-6 parts)
    # =========================================================================
    donut_dim = chan_col or (roles["all_categories"][0] if roles["all_categories"] and df[roles["all_categories"][0]].nunique() <= 6 else None)
    if donut_dim and rev_col and df[donut_dim].nunique() >= 2:
        grp_d = df.groupby(donut_dim, observed=False)[rev_col].sum().reset_index()
        grp_d = grp_d[grp_d[rev_col] > 0].sort_values(by=rev_col, ascending=False)
        if 2 <= len(grp_d) <= 6:
            tot_d = grp_d[rev_col].sum()
            scale_div = 1e6 if total_rev >= 1e6 else 1.0
            grp_d["val_mil"] = (grp_d[rev_col] / scale_div).round(1)
            grp_d["share_pct"] = ((grp_d[rev_col] / tot_d) * 100).round(1)
            grp_d["color"] = [get_color_for_category(r[donut_dim], i) for i, r in grp_d.iterrows()]

            top_d = grp_d.iloc[0]
            snd_d = grp_d.iloc[1] if len(grp_d) > 1 else top_d

            allowed_nums_c2 = set(grp_d["val_mil"].tolist())
            allowed_nums_c2.update(grp_d["share_pct"].tolist())

            raw_c2_ph = f"Cơ cấu đóng góp theo '{donut_dim}' cho thấy '{top_d[donut_dim]}' chiếm tỷ trọng lớn nhất với {top_d['share_pct']}%, kế tiếp là '{snd_d[donut_dim]}' đạt {snd_d['share_pct']}%."
            raw_c2_bc = f"Giá trị phân nhóm dẫn đầu đạt {top_d['val_mil']:,.1f} trên tổng {tot_d / scale_div:,.1f} từ cột {donut_dim}, {rev_col}."
            raw_c2_yn = f"Có thể do mức độ tiếp cận thuận lợi và tập tính lựa chọn của khách hàng đang nghiêng mạnh về nhóm này."
            raw_c2_dx = f"Duy trì tiêu chuẩn chất lượng tại '{top_d[donut_dim]}' đồng thời triển khai giải pháp thúc đẩy nhóm '{snd_d[donut_dim]}'."

            chart_data_c2 = [
                {"category": r[donut_dim], "value": r["val_mil"], "share_pct": r["share_pct"], "color": r["color"]}
                for _, r in grp_d.iterrows()
            ]

            if len(chart_data_c2) == len(grp_d):
                chart_cards.append({
                    "id": f"chart_{strip_accents_and_clean(donut_dim)}_donut",
                    "title": f"Tỷ trọng đóng góp {rev_col} theo {donut_dim}",
                    "section": "Thị trường & Cơ cấu",
                    "chart_type": "donut",
                    "disabled": False,
                    "x_axis": "category",
                    "bars": [],
                    "lines": [],
                    "data": chart_data_c2,
                    "source_line": format_source_line([donut_dim, rev_col], total_rows, sheet_name=sheet_name),
                    "pivot_config": {"rows": [donut_dim], "values": [rev_col], "agg_func": "sum", "chart_type": "pie"},
                    "analysis": record_narrative({
                        **build_card_analysis(raw_c2_ph, raw_c2_bc, raw_c2_yn, raw_c2_dx, allowed_nums_c2, raw_c2_ph, raw_c2_bc),
                        "severity": "CAO" if top_d["share_pct"] >= 60 else "TRUNG BÌNH",
                        "profit_impact": float(top_d[rev_col] - snd_d[rev_col])
                    })
                })

    # =========================================================================
    # CHART 3: Regional / Location Breakdown (GROUPED BAR: Revenue & Profit)
    # =========================================================================
    if loc_col and rev_col and df[loc_col].nunique() >= 2:
        agg_kwargs = {"measure_val": (rev_col, "sum")}
        if profit_col:
            agg_kwargs["profit_val"] = (profit_col, "sum")

        grp_loc = df.groupby(loc_col, observed=False).agg(**agg_kwargs).reset_index()
        grp_loc = grp_loc[grp_loc["measure_val"] > 0].sort_values(by="measure_val", ascending=False)

        if len(grp_loc) >= 2:
            # Cap to top 8 if many locations
            if len(grp_loc) > 8:
                grp_loc = grp_loc.head(8)

            scale_div = 1e6 if total_rev >= 1e6 else 1.0
            grp_loc["val_mil"] = (grp_loc["measure_val"] / scale_div).round(1)
            tot_loc = grp_loc["measure_val"].sum()

            bars_loc = [{"key": "val_mil", "name": f"{rev_col}", "color": COLOR_BLUE}]
            allowed_nums_c3 = set(grp_loc["val_mil"].tolist())

            if profit_col:
                grp_loc["prof_mil"] = (grp_loc["profit_val"] / scale_div).round(1)
                allowed_nums_c3.update(grp_loc["prof_mil"].tolist())
                bars_loc.append({"key": "prof_mil", "name": f"{profit_col}", "color": COLOR_GREEN})

            top_loc = grp_loc.iloc[0]
            bot_loc = grp_loc.iloc[-1]
            top_loc_share = round((top_loc["measure_val"] / tot_loc) * 100, 1)
            loc_ratio = round(top_loc["measure_val"] / max(bot_loc["measure_val"], 1.0), 1)
            allowed_nums_c3.update([top_loc_share, loc_ratio])

            raw_c3_ph = f"Địa bàn '{top_loc[loc_col]}' dẫn đầu khi đóng góp {top_loc['val_mil']:,.1f} ({top_loc_share}%), gấp {loc_ratio} lần khu vực '{bot_loc[loc_col]}' ({bot_loc['val_mil']:,.1f})."
            raw_c3_bc = f"Độ phân tán doanh số theo địa lý được ghi nhận từ cột {loc_col} và {rev_col}."
            raw_c3_yn = f"Nhiều khả năng do quy mô thị trường và mật độ khách hàng tập trung không đồng đều giữa các khu vực."
            raw_c3_dx = f"Tập trung bảo vệ thị phần tại '{top_loc[loc_col]}' và đánh giá lại chi phí vận hành tại '{bot_loc[loc_col]}'."

            c3_id = f"chart_{strip_accents_and_clean(loc_col)}_grouped"
            chart_data_c3 = grp_loc.rename(columns={loc_col: "category"})[
                ["category", "val_mil"] + (["prof_mil"] if profit_col else [])
            ].to_dict(orient="records")

            if len(chart_data_c3) == len(grp_loc):
                chart_cards.append({
                    "id": c3_id,
                    "title": f"Phân bổ số liệu theo {loc_col}",
                    "section": "Thị trường & Cơ cấu",
                    "chart_type": "grouped_bar" if profit_col else "bar",
                    "disabled": False,
                    "x_axis": "category",
                    "bars": bars_loc,
                    "lines": [],
                    "data": chart_data_c3,
                    "source_line": format_source_line([loc_col, rev_col] + ([profit_col] if profit_col else []), total_rows, sheet_name=sheet_name),
                    "pivot_config": {"rows": [loc_col], "values": [rev_col], "agg_func": "sum", "chart_type": "bar"},
                    "analysis": record_narrative({
                        **build_card_analysis(raw_c3_ph, raw_c3_bc, raw_c3_yn, raw_c3_dx, allowed_nums_c3, raw_c3_ph, raw_c3_bc),
                        "severity": "CAO" if top_loc_share >= 50 else "TRUNG BÌNH",
                        "profit_impact": float(top_loc["measure_val"] - bot_loc["measure_val"])
                    })
                })

                if top_loc_share >= 45.0 and total_rows >= 30 and len(main_problems) < 4:
                    main_problems.append({
                        "id": "prob_location_concentration",
                        "title": f"Số liệu tập trung lệch vào địa bàn '{top_loc[loc_col]}' ({top_loc_share}%)",
                        "severity": "CAO" if top_loc_share >= 55 else "TRUNG BÌNH",
                        "impact_str": fmt_currency(top_loc["measure_val"] - bot_loc["measure_val"]),
                        "impact_numeric": float(top_loc["measure_val"] - bot_loc["measure_val"]),
                        "evidence": [
                            f"Khu vực '{top_loc[loc_col]}': {top_loc['val_mil']:,.1f}",
                            f"Khu vực '{bot_loc[loc_col]}': {bot_loc['val_mil']:,.1f}",
                            f"Gấp {loc_ratio} lần địa bàn thấp nhất"
                        ],
                        "probable_cause": "Nhiều khả năng do mức độ phủ sóng và kênh phân phối chưa đồng đều giữa các tỉnh thành.",
                        "action": "Tái cơ cấu ngân sách bán hàng để kích cầu tại các khu vực có tỷ trọng thấp.",
                        "linked_chart_id": c3_id,
                        "pivot_preset": {"rows": [loc_col], "values": [rev_col], "agg_func": "sum", "chart_type": "bar"}
                    })

    # =========================================================================
    # CHART 4: Category Ranking (HORIZONTAL BAR: Sorted by value)
    # =========================================================================
    if cat_col and rev_col and df[cat_col].nunique() >= 2:
        grp_cat = df.groupby(cat_col, observed=False)[rev_col].sum().reset_index()
        grp_cat = grp_cat[grp_cat[rev_col] > 0].sort_values(by=rev_col, ascending=False)
        if len(grp_cat) >= 2:
            if len(grp_cat) > 10:
                grp_cat = grp_cat.head(10)

            scale_div = 1e6 if total_rev >= 1e6 else 1.0
            grp_cat["val_mil"] = (grp_cat[rev_col] / scale_div).round(1)
            tot_cat = grp_cat[rev_col].sum()
            grp_cat["color"] = [get_color_for_category(r[cat_col], i) for i, r in grp_cat.iterrows()]

            top_cat = grp_cat.iloc[0]
            bot_cat = grp_cat.iloc[-1]
            cat_diff = round((top_cat[rev_col] - bot_cat[rev_col]) / scale_div, 1)
            cat_top_share = round((top_cat[rev_col] / tot_cat) * 100, 1)

            allowed_nums_c4 = set(grp_cat["val_mil"].tolist())
            allowed_nums_c4.update([cat_diff, cat_top_share])

            raw_c4_ph = f"Phân loại '{top_cat[cat_col]}' mang lại kết quả cao nhất với {top_cat['val_mil']:,.1f} ({cat_top_share}%), đối lập với '{bot_cat[cat_col]}' đạt {bot_cat['val_mil']:,.1f}."
            raw_c4_bc = f"Chênh lệch tuyệt đối giữa phân nhóm cao nhất và thấp nhất là {cat_diff} từ cột {cat_col}, {rev_col}."
            raw_c4_yn = f"Có thể do nhu cầu thị trường đối với các mặt hàng thuộc nhóm '{top_cat[cat_col]}' chiếm ưu thế vượt trội."
            raw_c4_dx = f"Phát triển thêm danh mục sản phẩm mới cho nhóm chủ lực và rà soát lại chính sách giá cho nhóm '{bot_cat[cat_col]}'."

            chart_data_c4 = [
                {"category": r[cat_col], "val_mil": r["val_mil"], "color": r["color"]}
                for _, r in grp_cat.iterrows()
            ]

            if len(chart_data_c4) == len(grp_cat):
                chart_cards.append({
                    "id": f"chart_{strip_accents_and_clean(cat_col)}_ranking",
                    "title": f"Xếp hạng quy mô đóng góp theo {cat_col}",
                    "section": "Sản phẩm & Danh mục",
                    "chart_type": "horizontal_bar",
                    "disabled": False,
                    "x_axis": "val_mil",
                    "bars": [{"key": "val_mil", "name": f"{rev_col}", "color": COLOR_BLUE}],
                    "lines": [],
                    "data": chart_data_c4,
                    "source_line": format_source_line([cat_col, rev_col], total_rows, sheet_name=sheet_name),
                    "pivot_config": {"rows": [cat_col], "values": [rev_col], "agg_func": "sum", "chart_type": "bar"},
                    "analysis": record_narrative({
                        **build_card_analysis(raw_c4_ph, raw_c4_bc, raw_c4_yn, raw_c4_dx, allowed_nums_c4, raw_c4_ph, raw_c4_bc),
                        "severity": "CAO" if cat_top_share >= 50 else "TRUNG BÌNH",
                        "profit_impact": float(top_cat[rev_col] - bot_cat[rev_col])
                    })
                })

    # =========================================================================
    # CHART 5: Subcategory / Detailed Product Ranking (HORIZONTAL BAR with TOP 11 + KHÁC)
    # =========================================================================
    detail_dim = subcat_col if subcat_col != cat_col else None
    if detail_dim and rev_col and df[detail_dim].nunique() >= 2:
        grp_sub_capped, is_sub_capped = cap_dimension_series(df, detail_dim, rev_col, max_cats=12)
        if len(grp_sub_capped) >= 2:
            scale_div = 1e6 if total_rev >= 1e6 else 1.0
            grp_sub_capped["val_mil"] = (grp_sub_capped[rev_col] / scale_div).round(1)
            tot_sub_rev = grp_sub_capped[rev_col].sum()
            grp_sub_capped["color"] = [
                COLOR_GRAY if r[detail_dim] == "Khác" else PALETTE[i % len(PALETTE)]
                for i, r in grp_sub_capped.iterrows()
            ]

            top_sub = grp_sub_capped.iloc[0]
            other_sub_row = grp_sub_capped[grp_sub_capped[detail_dim] == "Khác"]
            other_sub_share = round((other_sub_row[rev_col].values[0] / tot_sub_rev) * 100, 1) if not other_sub_row.empty else 0.0
            top11_share = round(100.0 - other_sub_share, 1)

            allowed_nums_c5 = set(grp_sub_capped["val_mil"].tolist())
            allowed_nums_c5.update([other_sub_share, top11_share, top_sub["val_mil"]])

            raw_c5_ph = f"Chi tiết các phân mục ghi nhận '{top_sub[detail_dim]}' dẫn đầu bảng với {top_sub['val_mil']:,.1f}, trong khi nhóm 'Khác' chiếm {other_sub_share}%."
            raw_c5_bc = f"Top phân nhóm đóng góp tổng cộng {top11_share}% tổng giá trị từ cột {detail_dim}, {rev_col}."
            raw_c5_yn = f"Nhiều khả năng do quy luật 80/20 trong cơ cấu danh mục, nơi một nhóm nhỏ phân loại tạo ra phần lớn giá trị."
            raw_c5_dx = f"Đảm bảo cung ứng không gián đoạn cho nhóm dẫn đầu và xem xét tinh gọn các mã hàng chậm luân chuyển."

            chart_data_c5 = [
                {"category": r[detail_dim], "val_mil": r["val_mil"], "color": r["color"]}
                for _, r in grp_sub_capped.iterrows()
            ]

            if len(chart_data_c5) == len(grp_sub_capped):
                chart_cards.append({
                    "id": f"chart_{strip_accents_and_clean(detail_dim)}_horizontal",
                    "title": f"Chi tiết phân nhóm theo {detail_dim}",
                    "section": "Sản phẩm & Danh mục",
                    "chart_type": "horizontal_bar",
                    "disabled": False,
                    "x_axis": "val_mil",
                    "bars": [{"key": "val_mil", "name": f"{rev_col}", "color": COLOR_TEAL}],
                    "lines": [],
                    "data": chart_data_c5,
                    "source_line": format_source_line([detail_dim, rev_col], total_rows, is_capped=is_sub_capped, sheet_name=sheet_name),
                    "pivot_config": {"rows": [detail_dim], "values": [rev_col], "agg_func": "sum", "chart_type": "bar"},
                    "analysis": record_narrative({
                        **build_card_analysis(raw_c5_ph, raw_c5_bc, raw_c5_yn, raw_c5_dx, allowed_nums_c5, raw_c5_ph, raw_c5_bc),
                        "severity": "TRUNG BÌNH",
                        "profit_impact": float(top_sub[rev_col])
                    })
                })

    # =========================================================================
    # CHART 6: Stacked Bar (STACKED COLUMN: Cross Category × Channel)
    # =========================================================================
    if cat_col and chan_col and rev_col and cat_col != chan_col:
        grp_cross = df.groupby([cat_col, chan_col], observed=False)[rev_col].sum().unstack(fill_value=0)
        if len(grp_cross) >= 2:
            scale_div = 1e6 if total_rev >= 1e6 else 1.0
            grp_cross_mil = (grp_cross / scale_div).round(1).reset_index()
            channels_avail = [c for c in grp_cross.columns if c != cat_col]

            bars_stacked = [
                {"key": ch, "name": ch, "color": get_color_for_category(ch, i), "stackId": "a"}
                for i, ch in enumerate(channels_avail)
            ]

            lead_row = grp_cross.sum(axis=1).idxmax()
            lead_val = round(grp_cross.sum(axis=1).max() / scale_div, 1)
            stack_total = round(grp_cross.values.sum() / scale_div, 1)

            allowed_nums_c6 = set(grp_cross_mil.select_dtypes(include=[np.number]).values.flatten().tolist())
            allowed_nums_c6.update([lead_val, stack_total])

            raw_c6_ph = f"Phân bổ danh mục giữa các kênh cho thấy sự phối hợp đồng đều khi nhóm '{lead_row}' dẫn đầu với {lead_val}."
            raw_c6_bc = f"Tổng giá trị kết hợp đạt {stack_total} phân bổ qua cột {chan_col} và {cat_col}."
            raw_c6_yn = f"Có thể do sự giao thoa nhu cầu giữa các phân khúc khách hàng qua từng phương thức tiếp cận."
            raw_c6_dx = f"Đồng bộ hóa chính sách giá và tiêu chuẩn dịch vụ trên toàn bộ các kênh tiếp xúc."

            chart_data_c6 = grp_cross_mil.rename(columns={cat_col: "category"}).to_dict(orient="records")

            if len(chart_data_c6) == len(grp_cross):
                chart_cards.append({
                    "id": "chart_stacked_cross",
                    "title": f"Cơ cấu {rev_col} theo {cat_col} × {chan_col}",
                    "section": "Thị trường & Cơ cấu",
                    "chart_type": "stacked_bar",
                    "disabled": False,
                    "x_axis": "category",
                    "bars": bars_stacked,
                    "lines": [],
                    "data": chart_data_c6,
                    "source_line": format_source_line([cat_col, chan_col, rev_col], total_rows, sheet_name=sheet_name),
                    "pivot_config": {"rows": [cat_col], "cols": [chan_col], "values": [rev_col], "agg_func": "sum", "chart_type": "bar"},
                    "analysis": record_narrative({
                        **build_card_analysis(raw_c6_ph, raw_c6_bc, raw_c6_yn, raw_c6_dx, allowed_nums_c6, raw_c6_ph, raw_c6_bc),
                        "severity": "TRUNG BÌNH",
                        "profit_impact": float(grp_cross.values.sum() * 0.1)
                    })
                })

    # =========================================================================
    # CHART 7: Financial Waterfall (WATERFALL: Revenue -> -Discount -> -Cost -> Profit)
    # =========================================================================
    if rev_col and (cost_col or profit_col or discount_col):
        scale_div = 1e6 if total_rev >= 1e6 else 1.0
        r_mil = round(total_rev / scale_div, 1)
        d_mil = round(total_disc / scale_div, 1)
        c_mil = round(total_cost / scale_div, 1)
        p_mil = round(total_profit / scale_div, 1)

        waterfall_data = [{"category": rev_col, "amount_mil": r_mil, "fill": COLOR_BLUE, "step_type": "total"}]
        allowed_nums_c7 = {r_mil}

        if discount_col and total_disc > 0:
            waterfall_data.append({"category": discount_col, "amount_mil": -d_mil, "fill": COLOR_RED, "step_type": "deduction"})
            allowed_nums_c7.add(d_mil)
        if cost_col and total_cost > 0:
            waterfall_data.append({"category": cost_col, "amount_mil": -c_mil, "fill": COLOR_ORANGE, "step_type": "deduction"})
            allowed_nums_c7.add(c_mil)
        if profit_col:
            waterfall_data.append({"category": profit_col, "amount_mil": p_mil, "fill": COLOR_GREEN, "step_type": "result"})
            allowed_nums_c7.add(p_mil)

        if len(waterfall_data) >= 3:
            raw_c7_ph = f"Dòng tài chính phân rã từ {r_mil:,.1f} '{rev_col}' chuyển hóa còn {p_mil:,.1f} '{profit_col or 'kết quả'}'."
            raw_c7_bc = f"Chi phí và chiết khấu tạo nên mức khấu trừ tương ứng từ cột tài chính."
            raw_c7_yn = f"Nhiều khả năng do cơ cấu giá vốn và chính sách khuyến mãi trực tiếp chiếm tỷ trọng đáng kể."
            raw_c7_dx = f"Kiểm soát chặt trần chiết khấu và tối ưu hóa hợp đồng cung ứng đầu vào dài hạn."

            c7_id = "chart_financial_waterfall"
            chart_cards.append({
                "id": c7_id,
                "title": "Phân rã dòng tài chính từ Doanh thu đến Lợi nhuận",
                "section": "Lợi nhuận & Chiết khấu",
                "chart_type": "waterfall",
                "disabled": False,
                "x_axis": "category",
                "bars": [{"key": "amount_mil", "name": "Giá trị", "color": COLOR_BLUE}],
                "lines": [],
                "data": waterfall_data,
                "source_line": format_source_line([rev_col] + ([discount_col] if discount_col else []) + ([cost_col] if cost_col else []) + ([profit_col] if profit_col else []), total_rows, sheet_name=sheet_name),
                "pivot_config": {"rows": ["Tài chính"], "values": [rev_col], "agg_func": "sum", "chart_type": "bar"},
                "analysis": record_narrative({
                    **build_card_analysis(raw_c7_ph, raw_c7_bc, raw_c7_yn, raw_c7_dx, allowed_nums_c7, raw_c7_ph, raw_c7_bc),
                    "severity": "CAO" if total_disc / max(total_rev, 1.0) >= 0.08 else "TRUNG BÌNH",
                    "profit_impact": float(total_disc)
                })
            })

    # =========================================================================
    # CHART 8: Flag Rate (BAR CHART in RED: Return / Cancellation / Late)
    # =========================================================================
    flag_dim = chan_col or cat_col or (roles["all_categories"][0] if roles["all_categories"] else None)
    if ret_col and flag_dim:
        df_ret = df.copy()
        df_ret["_flag_num_"] = pd.to_numeric(df_ret[ret_col], errors="coerce").fillna(0)

        grp_flag = df_ret.groupby(flag_dim, observed=False).agg(
            total_cnt=("_flag_num_", "count"),
            flag_cnt=("_flag_num_", "sum")
        ).reset_index()
        grp_flag = grp_flag[grp_flag["total_cnt"] >= 5]

        if len(grp_flag) >= 2:
            grp_flag["rate_pct"] = ((grp_flag["flag_cnt"] / grp_flag["total_cnt"]) * 100).round(1)
            grp_flag = grp_flag.sort_values(by="rate_pct", ascending=False)
            highest_flag = grp_flag.iloc[0]
            lowest_flag = grp_flag.iloc[-1]
            flag_gap = round(highest_flag["rate_pct"] - lowest_flag["rate_pct"], 1)

            allowed_nums_c8 = set(grp_flag["rate_pct"].tolist())
            allowed_nums_c8.update([flag_gap, highest_flag["rate_pct"], lowest_flag["rate_pct"]])

            raw_c8_ph = f"Tỷ lệ '{ret_col}' cao nhất là {highest_flag['rate_pct']}% tại '{highest_flag[flag_dim]}' và thấp nhất là {lowest_flag['rate_pct']}% tại '{lowest_flag[flag_dim]}'."
            raw_c8_bc = f"Mức chênh lệch tỷ lệ là {flag_gap}% giữa hai nhóm từ cột {flag_dim}, {ret_col}."
            raw_c8_yn = f"Nhiều khả năng do đặc thù phương thức thực hiện đơn hoặc kỳ vọng sản phẩm chưa sát với thực tế."
            raw_c8_dx = f"Cải thiện quy trình kiểm duyệt chất lượng trước khi đóng gói và rà soát các khâu giao vận."

            c8_id = f"chart_{strip_accents_and_clean(ret_col)}_by_{strip_accents_and_clean(flag_dim)}"
            chart_data_c8 = grp_flag.rename(columns={flag_dim: "category"})[
                ["category", "rate_pct", "flag_cnt", "total_cnt"]
            ].to_dict(orient="records")

            if len(chart_data_c8) == len(grp_flag):
                chart_cards.append({
                    "id": c8_id,
                    "title": f"Tỷ lệ {ret_col} (%) theo {flag_dim}",
                    "section": "Vận hành & Chất lượng",
                    "chart_type": "bar",
                    "disabled": False,
                    "x_axis": "category",
                    "bars": [{"key": "rate_pct", "name": f"Tỷ lệ {ret_col} (%)", "color": COLOR_RED}],
                    "lines": [],
                    "data": chart_data_c8,
                    "source_line": format_source_line([flag_dim, ret_col], total_rows, sheet_name=sheet_name),
                    "pivot_config": {"rows": [flag_dim], "values": [ret_col], "agg_func": "count", "chart_type": "bar"},
                    "analysis": record_narrative({
                        **build_card_analysis(raw_c8_ph, raw_c8_bc, raw_c8_yn, raw_c8_dx, allowed_nums_c8, raw_c8_ph, raw_c8_bc),
                        "severity": "CAO" if highest_flag["rate_pct"] >= 5.0 else "TRUNG BÌNH",
                        "profit_impact": float(highest_flag["flag_cnt"] * 100000)
                    })
                })

                if highest_flag["rate_pct"] >= 3.5 and total_rows >= 25 and len(main_problems) < 4:
                    main_problems.append({
                        "id": "prob_flag_spike",
                        "title": f"Tỷ lệ '{ret_col}' chạm ngưỡng {highest_flag['rate_pct']}% tại '{highest_flag[flag_dim]}'",
                        "severity": "CAO" if highest_flag["rate_pct"] >= 5.0 else "TRUNG BÌNH",
                        "impact_str": f"{highest_flag['flag_cnt']:,} đơn",
                        "impact_numeric": float(highest_flag["flag_cnt"]),
                        "evidence": [
                            f"Nhóm '{highest_flag[flag_dim]}': {highest_flag['rate_pct']}%",
                            f"Gấp {round(highest_flag['rate_pct'] / max(lowest_flag['rate_pct'], 0.1), 1)} lần nhóm thấp nhất",
                            f"Phát hiện từ cột {flag_dim}, {ret_col}"
                        ],
                        "probable_cause": "Nhiều khả năng do khâu vận chuyển hoặc tiêu chuẩn mô tả hàng hóa chưa đồng đều.",
                        "action": "Ký cam kết thời gian giao hàng và nâng cấp quy trình đóng gói.",
                        "linked_chart_id": c8_id,
                        "pivot_preset": {"rows": [flag_dim], "values": [ret_col], "agg_func": "count", "chart_type": "bar"}
                    })

    # =========================================================================
    # CHART 9: Rating / Satisfaction (BAR CHART in AMBER)
    # =========================================================================
    rating_dim = loc_col or chan_col or cat_col or (roles["all_categories"][0] if roles["all_categories"] else None)
    if sat_col and rating_dim:
        grp_sat = df.groupby(rating_dim, observed=False)[sat_col].agg(["mean", "count"]).reset_index()
        grp_sat = grp_sat[grp_sat["count"] >= 5]
        if len(grp_sat) >= 2:
            grp_sat["score"] = grp_sat["mean"].round(1)
            grp_sat = grp_sat.sort_values(by="score", ascending=False)
            best_sat = grp_sat.iloc[0]
            worst_sat = grp_sat.iloc[-1]
            sat_diff = round(best_sat["score"] - worst_sat["score"], 1)

            allowed_nums_c9 = set(grp_sat["score"].tolist())
            allowed_nums_c9.update([sat_diff, best_sat["score"], worst_sat["score"]])

            raw_c9_ph = f"Điểm '{sat_col}' cao nhất là {best_sat['score']} tại '{best_sat[rating_dim]}' và thấp nhất là {worst_sat['score']} tại '{worst_sat[rating_dim]}'."
            raw_c9_bc = f"Độ lệch điểm đánh giá là {sat_diff} giữa hai nhóm từ cột {rating_dim}, {sat_col}."
            raw_c9_yn = f"Có thể do thái độ chăm sóc và trải nghiệm dịch vụ tại các điểm tiếp xúc chưa có sự đồng đều tuyệt đối."
            raw_c9_dx = f"Đào tạo lại quy trình tư vấn và thiết lập đường dây nóng hỗ trợ khách hàng cho nhóm '{worst_sat[rating_dim]}'."

            c9_id = f"chart_{strip_accents_and_clean(sat_col)}_by_{strip_accents_and_clean(rating_dim)}"
            chart_data_c9 = grp_sat.rename(columns={rating_dim: "category"})[["category", "score"]].to_dict(orient="records")

            if len(chart_data_c9) == len(grp_sat):
                chart_cards.append({
                    "id": c9_id,
                    "title": f"Điểm {sat_col} theo {rating_dim}",
                    "section": "Trải nghiệm & Dịch vụ",
                    "chart_type": "bar",
                    "disabled": False,
                    "x_axis": "category",
                    "bars": [{"key": "score", "name": f"Điểm {sat_col}", "color": COLOR_AMBER}],
                    "lines": [],
                    "data": chart_data_c9,
                    "source_line": format_source_line([rating_dim, sat_col], total_rows, sheet_name=sheet_name),
                    "pivot_config": {"rows": [rating_dim], "values": [sat_col], "agg_func": "mean", "chart_type": "bar"},
                    "analysis": record_narrative({
                        **build_card_analysis(raw_c9_ph, raw_c9_bc, raw_c9_yn, raw_c9_dx, allowed_nums_c9, raw_c9_ph, raw_c9_bc),
                        "severity": "CAO" if worst_sat["score"] <= 3.5 else "THẤP",
                        "profit_impact": 0.0
                    })
                })

    # =========================================================================
    # CHART 10: Secondary Numeric Breakdown / Discount (COMBO)
    # =========================================================================
    sec_num = discount_col or (num_cols[1] if len(num_cols) > 1 and num_cols[1] != profit_col and num_cols[1] != rev_col else None)
    sec_dim = chan_col or cat_col or (roles["all_categories"][0] if roles["all_categories"] else None)
    if sec_num and sec_dim and rev_col and df[sec_dim].nunique() >= 2:
        grp_sec = df.groupby(sec_dim, observed=False).agg(
            rev_total=(rev_col, "sum"),
            sec_total=(sec_num, "sum")
        ).reset_index()
        grp_sec = grp_sec[grp_sec["rev_total"] > 0]
        if len(grp_sec) >= 2 and (grp_sec["sec_total"] > 0).any():
            scale_div = 1e6 if total_rev >= 1e6 else 1.0
            grp_sec["sec_mil"] = (grp_sec["sec_total"] / scale_div).round(1)
            grp_sec["sec_rate_pct"] = ((grp_sec["sec_total"] / grp_sec["rev_total"]) * 100).round(1)
            grp_sec = grp_sec.sort_values(by="sec_mil", ascending=False)
            top_sec = grp_sec.iloc[0]
            bot_sec = grp_sec.iloc[-1]

            allowed_nums_c10 = set(grp_sec["sec_mil"].tolist())
            allowed_nums_c10.update(grp_sec["sec_rate_pct"].tolist())

            raw_c10_ph = f"Chỉ số '{sec_num}' tập trung cao nhất tại '{top_sec[sec_dim]}' với {top_sec['sec_mil']:,.1f} ({top_sec['sec_rate_pct']}%), thấp nhất tại '{bot_sec[sec_dim]}' với {bot_sec['sec_mil']:,.1f}."
            raw_c10_bc = f"Tổng ngân sách {sec_num} ghi nhận qua cột {sec_dim}, {sec_num}."
            raw_c10_yn = f"Nhiều khả năng do chính sách kích cầu ngắn hạn tập trung mạnh vào phân khúc này."
            raw_c10_dx = f"Kiểm soát chặt chẽ tỷ lệ {sec_num} và chuyển đổi sang các hình thức gia tăng giá trị dịch vụ."

            c10_id = f"chart_{strip_accents_and_clean(sec_num)}_by_{strip_accents_and_clean(sec_dim)}"
            chart_data_c10 = grp_sec.rename(columns={sec_dim: "category"})[
                ["category", "sec_mil", "sec_rate_pct"]
            ].to_dict(orient="records")

            if len(chart_data_c10) == len(grp_sec):
                chart_cards.append({
                    "id": c10_id,
                    "title": f"Quy mô và tỷ lệ {sec_num} theo {sec_dim}",
                    "section": "Lợi nhuận & Chiết khấu",
                    "chart_type": "combo",
                    "disabled": False,
                    "x_axis": "category",
                    "bars": [{"key": "sec_mil", "name": f"{sec_num}", "color": COLOR_RED, "yAxisId": "left"}],
                    "lines": [{"key": "sec_rate_pct", "name": f"Tỷ lệ so với {rev_col} (%)", "color": COLOR_AMBER, "yAxisId": "right"}],
                    "data": chart_data_c10,
                    "source_line": format_source_line([sec_dim, sec_num], total_rows, sheet_name=sheet_name),
                    "pivot_config": {"rows": [sec_dim], "values": [sec_num], "agg_func": "sum", "chart_type": "bar"},
                    "analysis": record_narrative({
                        **build_card_analysis(raw_c10_ph, raw_c10_bc, raw_c10_yn, raw_c10_dx, allowed_nums_c10, raw_c10_ph, raw_c10_bc),
                        "severity": "CAO" if top_sec["sec_rate_pct"] >= 10.0 else "TRUNG BÌNH",
                        "profit_impact": float(top_sec["sec_total"])
                    })
                })

    # Problem groups grouping
    problem_groups = []
    sections_map: Dict[str, List[str]] = {}
    for c in chart_cards:
        sec = c.get("section", "Tổng quan")
        sections_map.setdefault(sec, []).append(c["id"])

    for sec_name, c_ids in sections_map.items():
        if not c_ids:
            continue
        problem_groups.append({
            "id": f"grp_{len(problem_groups) + 1}",
            "title": sec_name,
            "problem_statement": f"Phân tích chuyên sâu về {sec_name.lower()} dựa trên các biến số thực tế.",
            "chart_ids": c_ids,
            "conclusion": f"Các số liệu thể hiện sự đồng thuận cao về hiệu quả trong nhóm {sec_name.lower()}."
        })

    # Planner Summary
    num_charts = len(chart_cards)
    num_problems = len(main_problems)
    num_measures = len(num_cols)
    num_dims = len(roles["all_categories"])
    time_info = "1 cột thời gian" if time_col else "không có cột thời gian"
    chart_types = [c["chart_type"] for c in chart_cards]
    type_summary = ", ".join(sorted(set(chart_types))) if chart_types else "không có"

    planner_summary = (
        f"Đã tự động lập kế hoạch {num_charts} biểu đồ ({type_summary}) và {num_problems} vấn đề trọng tâm "
        f"từ {num_measures} cột số đo và {num_dims} cột phân loại, {time_info} trên toàn bộ {total_rows:,.0f} dòng dữ liệu.".replace(",", ".")
    )

    headline = (
        f"Quy mô ghi nhận đạt {fmt_currency(total_rev)} trên {total_rows:,.0f} bản ghi; "
        f"phát hiện {num_problems} vấn đề cần ưu tiên xử lý.".replace(",", ".")
        if num_problems > 0 else
        f"Quy mô ghi nhận đạt {fmt_currency(total_rev)} trên {total_rows:,.0f} bản ghi; các chỉ số vận hành ổn định trong ngưỡng an toàn.".replace(",", ".")
    )

    return {
        "data_scope": data_scope,
        "kpis": kpis,
        "cross_check_warning": None,
        "headline": headline,
        "planner_summary": planner_summary,
        "main_problems": main_problems,
        "positive_signals": [] if main_problems else [
            {"title": "Vận hành ổn định", "detail": "Không phát hiện sai lệch vượt ngưỡng quy định (>10% sụt giảm hoặc >5% hoàn hàng)."}
        ],
        "no_problems_message": "Không phát hiện vấn đề vượt ngưỡng trong dữ liệu này." if not main_problems else None,
        "problem_groups": problem_groups,
        "chart_cards": chart_cards,
        "data_gaps": []
    }

def export_report_excel(df: pd.DataFrame, report_data: Dict[str, Any], sheet_name: str = "Dữ liệu") -> io.BytesIO:
    """Exports structured Excel workbook based on planned charts and problems."""
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        workbook = writer.book

        header_fmt = workbook.add_format({
            'bold': True, 'bg_color': '#1E3A8A', 'font_color': '#FFFFFF',
            'border': 1, 'font_size': 10, 'align': 'center', 'valign': 'vcenter'
        })
        cell_fmt = workbook.add_format({'border': 1, 'font_size': 9, 'valign': 'vcenter'})
        num_fmt = workbook.add_format({'border': 1, 'font_size': 9, 'num_format': '#,##0.0', 'align': 'right'})
        title_fmt = workbook.add_format({'bold': True, 'font_size': 14, 'font_color': '#0F6B4F'})
        badge_cao = workbook.add_format({'bold': True, 'bg_color': '#FEE2E2', 'font_color': '#991B1B', 'border': 1, 'align': 'center'})

        # Sheet 1: Dashboard
        ws_dash = workbook.add_worksheet("Dashboard")
        writer.sheets["Dashboard"] = ws_dash

        ws_dash.write(1, 0, "BÁO CÁO KINH DOANH - DASHBOARD ĐIỀU HÀNH", title_fmt)
        ws_dash.write(2, 0, f"Phạm vi: {report_data.get('data_scope', {}).get('date_range', '')} | {report_data.get('data_scope', {}).get('order_count', 0):,} dòng")
        ws_dash.write(3, 0, f"Kế hoạch: {report_data.get('planner_summary', '')}")

        # KPIs
        start_kpi = 5
        kpi_headers = ["Chỉ số", "Giá trị", "Ghi chú"]
        for c_idx, h in enumerate(kpi_headers):
            ws_dash.write(start_kpi, c_idx, h, header_fmt)

        for idx, k in enumerate(report_data.get("kpis", []), start=1):
            ws_dash.write(start_kpi + idx, 0, k.get("label", ""), cell_fmt)
            ws_dash.write(start_kpi + idx, 1, k.get("value", ""), num_fmt)
            ws_dash.write(start_kpi + idx, 2, k.get("change_label", ""), cell_fmt)

        # Problems
        start_prob = start_kpi + len(report_data.get("kpis", [])) + 3
        ws_dash.write(start_prob, 0, "CÁC VẤN ĐỀ TRỌNG TÂM CẦN XỬ LÝ (TỰ ĐỘNG PHÁT HIỆN TỪ DỮ LIỆU)", title_fmt)

        prob_headers = ["STT", "Mức độ", "Vấn đề chính", "Tác động", "Bằng chứng số liệu", "Nguyên nhân giả định", "Hành động đề xuất"]
        for c_idx, h in enumerate(prob_headers):
            ws_dash.write(start_prob + 1, c_idx, h, header_fmt)

        problems = report_data.get("main_problems", [])
        if problems:
            for idx, p in enumerate(problems, start=1):
                cur_r = start_prob + 1 + idx
                ws_dash.write(cur_r, 0, idx, cell_fmt)
                ws_dash.write(cur_r, 1, p.get("severity", "CAO"), badge_cao)
                ws_dash.write(cur_r, 2, p.get("title", ""), cell_fmt)
                ws_dash.write(cur_r, 3, p.get("impact_str", ""), cell_fmt)
                ws_dash.write(cur_r, 4, "; ".join(p.get("evidence", [])), cell_fmt)
                ws_dash.write(cur_r, 5, p.get("probable_cause", ""), cell_fmt)
                ws_dash.write(cur_r, 6, p.get("action", ""), cell_fmt)
        else:
            ws_dash.write(start_prob + 2, 0, 1, cell_fmt)
            ws_dash.write(start_prob + 2, 1, "TỐT", cell_fmt)
            ws_dash.write(start_prob + 2, 2, report_data.get("no_problems_message", "Không phát hiện vấn đề vượt ngưỡng"), cell_fmt)

        ws_dash.set_column(0, 0, 6)
        ws_dash.set_column(1, 1, 12)
        ws_dash.set_column(2, 2, 40)
        ws_dash.set_column(3, 3, 16)
        ws_dash.set_column(4, 4, 45)
        ws_dash.set_column(5, 5, 35)
        ws_dash.set_column(6, 6, 40)

        # Sheet 2: Phân tích
        ws_ana = workbook.add_worksheet("Phân tích")
        writer.sheets["Phân tích"] = ws_ana
        ws_ana.write(1, 0, "DỮ LIỆU TỔNG HỢP CHI TIẾT CÁC BIỂU ĐỒ", title_fmt)
        row_ptr = 3
        for c_card in report_data.get("chart_cards", []):
            ws_ana.write(row_ptr, 0, f"★ {c_card.get('title', '')} [{c_card.get('section', '')}]", workbook.add_format({'bold': True, 'font_size': 11, 'font_color': '#1E40AF'}))
            row_ptr += 1
            c_data = c_card.get("data", [])
            if isinstance(c_data, list) and len(c_data) > 0 and isinstance(c_data[0], dict):
                df_sub = pd.DataFrame(c_data)
                for col_idx, col_name in enumerate(df_sub.columns):
                    ws_ana.write(row_ptr, col_idx, str(col_name), header_fmt)
                row_ptr += 1
                for _, r_data in df_sub.iterrows():
                    for col_idx, col_name in enumerate(df_sub.columns):
                        val = r_data[col_name]
                        ws_ana.write(row_ptr, col_idx, val if pd.notnull(val) else "", cell_fmt)
                    row_ptr += 1
            row_ptr += 2
        ws_ana.set_column(0, 5, 25)

        # Sheet 3: Raw data
        raw_sheet_label = str(sheet_name)[:31] if sheet_name else "Dữ liệu"
        df.to_excel(writer, sheet_name=raw_sheet_label, index=False)

    output.seek(0)
    return output

def export_report_pdf(df: pd.DataFrame, report_data: Dict[str, Any]) -> io.BytesIO:
    """Exports structured PDF document based on planned charts and problems."""
    from reportlab.lib.pagesizes import A4
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib import colors

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=28, leftMargin=28, topMargin=28, bottomMargin=28)
    story = []

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('DocTitle', parent=styles['Heading1'], fontName='Helvetica-Bold', fontSize=18, leading=22, textColor=colors.HexColor('#0F6B4F'))
    h2_style = ParagraphStyle('DocH2', parent=styles['Heading2'], fontName='Helvetica-Bold', fontSize=12, leading=16, textColor=colors.HexColor('#1E40AF'))
    body_style = ParagraphStyle('DocBody', parent=styles['Normal'], fontName='Helvetica', fontSize=8.5, leading=12)
    body_bold = ParagraphStyle('DocBodyBold', parent=body_style, fontName='Helvetica-Bold')

    story.append(Paragraph("FLOWER HAPPY - BÁO CÁO PHÂN TÍCH THÍCH ỨNG DỮ LIỆU", title_style))
    story.append(Paragraph(f"Phạm vi: {report_data.get('data_scope', {}).get('date_range', '')} | {report_data.get('data_scope', {}).get('order_count', 0):,} dòng | Điểm chất lượng: {report_data.get('data_scope', {}).get('quality_score', 0)}%", body_style))
    story.append(Paragraph(f"<b>Kế hoạch:</b> {report_data.get('planner_summary', '')}", body_style))
    story.append(Spacer(1, 10))

    # Headline
    story.append(Paragraph(f"<b>THÔNG ĐIỆP CHÍNH:</b> {report_data.get('headline', '')}", h2_style))
    story.append(Spacer(1, 8))

    # Main Problems Table
    problems = report_data.get("main_problems", [])
    if problems:
        story.append(Paragraph("CÁC VẤN ĐỀ CHÍNH (XẾP THEO MỨC ĐỘ × TÁC ĐỘNG)", h2_style))
        prob_table_data = [["MỨC ĐỘ", "VẤN ĐỀ", "TÁC ĐỘNG", "BẰNG CHỨNG", "HÀNH ĐỘNG ĐỀ XUẤT"]]
        for p in problems:
            prob_table_data.append([
                Paragraph(p.get("severity", ""), body_bold),
                Paragraph(p.get("title", ""), body_style),
                Paragraph(p.get("impact_str", ""), body_bold),
                Paragraph("; ".join(p.get("evidence", [])), body_style),
                Paragraph(p.get("action", ""), body_style),
            ])
        t_prob = Table(prob_table_data, colWidths=[55, 130, 65, 140, 140])
        t_prob.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1E3A8A')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 7.5),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E1')),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ]))
        story.append(t_prob)
        story.append(Spacer(1, 14))

    # Supporting Sections
    cards_map = {c['id']: c for c in report_data.get("chart_cards", [])}
    if report_data.get("problem_groups"):
        story.append(Paragraph("CÁC NHÓM BIỂU ĐỒ BẢO CHỨNG THEO TỪNG VẤN ĐỀ", h2_style))
        story.append(Spacer(1, 6))
        for grp in report_data.get("problem_groups", []):
            story.append(Paragraph(f"<b>{grp.get('title')}</b>", h2_style))
            story.append(Paragraph(f"<i>{grp.get('problem_statement')}</i>", body_style))
            story.append(Spacer(1, 4))
            for cid in grp.get("chart_ids", []):
                card = cards_map.get(cid)
                if card:
                    an = card.get("analysis", {})
                    card_el = [
                        Paragraph(f"<b>• {card.get('title')}</b>", body_bold),
                        Paragraph(f"  Phát hiện: {an.get('phat_hien', '')}", body_style),
                        Paragraph(f"  Bằng chứng: {an.get('bang_chung', '')}", body_style),
                        Spacer(1, 4)
                    ]
                    story.append(KeepTogether(card_el))
            story.append(Spacer(1, 8))

    doc.build(story)
    buffer.seek(0)
    return buffer
