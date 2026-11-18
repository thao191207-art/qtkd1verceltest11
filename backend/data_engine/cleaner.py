import re
from typing import Dict, Any, List, Optional, Tuple
import pandas as pd
import numpy as np

def calculate_quality_score(df: pd.DataFrame, issues: List[Dict[str, Any]]) -> int:
    if df.empty:
        return 0
    total_cells = df.shape[0] * max(df.shape[1], 1)
    if total_cells == 0:
        return 0

    score = 100.0

    # Missing value penalty (up to 35 points)
    missing_cells = int(df.isna().sum().sum())
    missing_ratio = missing_cells / total_cells
    score -= min(missing_ratio * 70, 35.0)

    # Duplicate rows penalty (up to 25 points)
    duplicate_rows = int(df.duplicated().sum())
    dup_ratio = duplicate_rows / max(len(df), 1)
    score -= min(dup_ratio * 60, 25.0)

    # Issue severity penalty
    for issue in issues:
        severity = issue.get("severity")
        if severity == "high": # Nghiêm trọng
            score -= 5.0
        elif severity == "medium": # Cảnh báo
            score -= 2.0
        elif severity == "low": # Thông tin
            score -= 0.5

    return int(max(min(round(score), 100), 0))

def profile_dataset(df: pd.DataFrame) -> Dict[str, Any]:
    total_rows = len(df)
    total_cols = len(df.columns)
    
    if total_rows == 0 or total_cols == 0:
        return {
            "total_rows": total_rows,
            "total_cols": total_cols,
            "quality_score": 0,
            "duplicate_rows": 0,
            "duplicate_percentage": 0,
            "columns_profile": {},
            "issues": []
        }

    duplicate_rows = int(df.duplicated().sum())
    dup_pct = round((duplicate_rows / total_rows) * 100, 2)

    issues: List[Dict[str, Any]] = []

    # Duplicate rows issue
    if duplicate_rows > 0:
        issues.append({
            "id": "dup_rows",
            "column": "Toàn bộ bảng",
            "type": "duplicate_rows",
            "title": "Dòng dữ liệu trùng lặp",
            "description": f"Phát hiện {duplicate_rows:,} dòng ({dup_pct}%) bị trùng lặp hoàn toàn.",
            "severity": "high" if dup_pct > 5 else "medium",
            "suggested_action": "remove_duplicates",
            "count": duplicate_rows
        })

    cols_profile: Dict[str, Any] = {}

    for col in df.columns:
        series = df[col]
        missing_count = int(series.isna().sum())
        missing_pct = round((missing_count / total_rows) * 100, 2)
        unique_count = int(series.nunique(dropna=True))

        valid_series = series.dropna()

        # Inconsistency detection
        whitespace_issues = 0
        casing_issues = 0
        currency_number_strings = 0
        invalid_dates = 0

        # Outlier detection
        outliers_iqr = 0
        outliers_zscore = 0
        q1, q3, iqr = None, None, None
        lower_bound, upper_bound = None, None

        is_bool = (
            pd.api.types.is_bool_dtype(series)
            or series.dtype == bool
            or series.dtype == "boolean"
            or str(series.dtype).lower() in ("bool", "boolean")
        )
        is_numeric = pd.api.types.is_numeric_dtype(series) and not is_bool

        if is_bool:
            # Explicitly bypass IQR/Z-score outlier detection for boolean columns to prevent numpy boolean subtract error
            pass
        elif is_numeric and len(valid_series) > 4:
            # IQR outliers
            try:
                numeric_valid = pd.to_numeric(valid_series, errors="coerce").dropna().astype(float)
                if len(numeric_valid) > 4:
                    q1 = float(numeric_valid.quantile(0.25))
                    q3 = float(numeric_valid.quantile(0.75))
                    iqr = q3 - q1
                    if iqr > 0:
                        lower_bound = q1 - 1.5 * iqr
                        upper_bound = q3 + 1.5 * iqr
                        outliers_iqr = int(((numeric_valid < lower_bound) | (numeric_valid > upper_bound)).sum())

                    # Z-score outliers
                    std = float(numeric_valid.std())
                    if std > 0:
                        mean = float(numeric_valid.mean())
                        # Guarantees pure float subtraction, avoiding any boolean subtract
                        z_scores = np.abs((numeric_valid - mean) / std)
                        outliers_zscore = int((z_scores > 3.0).sum())
            except Exception:
                pass

        elif pd.api.types.is_string_dtype(series) or series.dtype == 'object':
            str_series = valid_series.astype(str)
            # Whitespace check
            whitespace_mask = str_series.str.strip() != str_series
            whitespace_issues = int(whitespace_mask.sum())

            # Mixed casing in categorical-like data
            if 1 < unique_count < 50:
                lowered_unique = len(str_series.str.lower().unique())
                if lowered_unique < unique_count:
                    casing_issues = unique_count - lowered_unique

            # Detect currency / number formatted as string
            currency_pattern = re.compile(r'[\$,₫€đVND]|^\d{1,3}(,\d{3})+(\.\d+)?$')
            currency_matches = str_series.apply(lambda x: bool(currency_pattern.search(x)))
            currency_number_strings = int(currency_matches.sum())

        # Compile issues for column
        if missing_count > 0:
            severity = "high" if missing_pct > 20 else ("medium" if missing_pct > 5 else "low")
            issues.append({
                "id": f"missing_{col}",
                "column": col,
                "type": "missing_values",
                "title": f"Dữ liệu khuyết thiếu ở cột '{col}'",
                "description": f"Có {missing_count:,} giá trị trống ({missing_pct}%).",
                "severity": severity,
                "suggested_action": "fill_missing",
                "count": missing_count
            })

        if whitespace_issues > 0:
            issues.append({
                "id": f"whitespace_{col}",
                "column": col,
                "type": "whitespace",
                "title": f"Khoảng trắng thừa ở cột '{col}'",
                "description": f"Có {whitespace_issues:,} giá trị chứa khoảng trắng ở đầu hoặc cuối.",
                "severity": "low",
                "suggested_action": "trim_whitespace",
                "count": whitespace_issues
            })

        if casing_issues > 0:
            issues.append({
                "id": f"casing_{col}",
                "column": col,
                "type": "casing",
                "title": f"Chữ hoa/thường không đồng nhất ở cột '{col}'",
                "description": f"Phát hiện các giá trị phân loại khác nhau chỉ vì định dạng hoa/thường.",
                "severity": "low",
                "suggested_action": "standardize_casing",
                "count": casing_issues
            })

        if currency_number_strings > 0 and currency_number_strings / max(len(valid_series), 1) > 0.5:
            issues.append({
                "id": f"currency_str_{col}",
                "column": col,
                "type": "unconverted_numeric",
                "title": f"Cột '{col}' chứa định dạng số/tiền tệ đang là văn bản",
                "description": f"Có {currency_number_strings:,} giá trị chứa ký hiệu tiền tệ hoặc dấu phân cách hàng nghìn.",
                "severity": "medium",
                "suggested_action": "convert_to_numeric",
                "count": currency_number_strings
            })

        if outliers_iqr > 0:
            pct_outliers = round((outliers_iqr / total_rows) * 100, 2)
            issues.append({
                "id": f"outlier_{col}",
                "column": col,
                "type": "outliers",
                "title": f"Giá trị ngoại lai (outliers) ở cột '{col}'",
                "description": f"Phát hiện {outliers_iqr:,} điểm dị biệt ({pct_outliers}%) ngoài ngưỡng IQR [{lower_bound:.2f}, {upper_bound:.2f}].",
                "severity": "medium" if pct_outliers > 5 else "low",
                "suggested_action": "handle_outliers",
                "count": outliers_iqr
            })

        cols_profile[col] = {
            "dtype": str(series.dtype),
            "missing_count": missing_count,
            "missing_percentage": missing_pct,
            "unique_count": unique_count,
            "is_numeric": bool(is_numeric),
            "whitespace_issues": whitespace_issues,
            "casing_issues": casing_issues,
            "outliers_iqr": outliers_iqr,
            "outliers_zscore": outliers_zscore,
            "lower_bound": lower_bound,
            "upper_bound": upper_bound
        }

    quality_score = calculate_quality_score(df, issues)

    return {
        "total_rows": total_rows,
        "total_cols": total_cols,
        "quality_score": quality_score,
        "duplicate_rows": duplicate_rows,
        "duplicate_percentage": dup_pct,
        "columns_profile": cols_profile,
        "issues": issues
    }

def apply_cleaning_action(
    df: pd.DataFrame,
    action: str,
    params: Dict[str, Any]
) -> Tuple[pd.DataFrame, Dict[str, Any], Dict[str, Any]]:
    """
    Executes a cleaning action on df, returning: (new_df, before_stats, after_stats)
    """
    before_stats = {
        "rows": len(df),
        "columns": len(df.columns),
        "null_count": int(df.isna().sum().sum()),
        "duplicates": int(df.duplicated().sum())
    }

    new_df = df.copy()

    if action == "remove_duplicates":
        subset = params.get("subset")
        new_df = new_df.drop_duplicates(subset=subset, keep=params.get("keep", "first")).reset_index(drop=True)

    elif action == "fill_missing":
        column = params["column"]
        method = params["method"] # 'mean', 'median', 'mode', 'constant', 'drop'
        if column in new_df.columns:
            if method == "drop":
                new_df = new_df.dropna(subset=[column]).reset_index(drop=True)
            elif method == "mean" and pd.api.types.is_numeric_dtype(new_df[column]):
                val = new_df[column].mean()
                new_df[column] = new_df[column].fillna(val)
            elif method == "median" and pd.api.types.is_numeric_dtype(new_df[column]):
                val = new_df[column].median()
                new_df[column] = new_df[column].fillna(val)
            elif method == "mode":
                mode_vals = new_df[column].mode()
                if not mode_vals.empty:
                    new_df[column] = new_df[column].fillna(mode_vals.iloc[0])
            elif method == "constant":
                val = params.get("value")
                new_df[column] = new_df[column].fillna(val)

    elif action == "standardize_text":
        column = params["column"]
        operation = params.get("operation", "trim") # 'trim', 'lowercase', 'uppercase', 'titlecase'
        if column in new_df.columns:
            series = new_df[column].astype(str)
            if operation == "trim":
                new_df[column] = series.str.strip()
            elif operation == "lowercase":
                new_df[column] = series.str.strip().str.lower()
            elif operation == "uppercase":
                new_df[column] = series.str.strip().str.upper()
            elif operation == "titlecase":
                new_df[column] = series.str.strip().str.title()
            new_df[column] = new_df[column].replace({"nan": None, "None": None})

    elif action == "standardize_date":
        column = params["column"]
        target_fmt = params.get("target_format", "%Y-%m-%d")
        if column in new_df.columns:
            parsed = pd.to_datetime(new_df[column], errors='coerce')
            new_df[column] = parsed.dt.strftime(target_fmt)

    elif action == "convert_type":
        column = params["column"]
        target_type = params["target_type"] # 'float', 'integer', 'string', 'datetime', 'boolean'
        if column in new_df.columns:
            if target_type in {"float", "integer"}:
                cleaned = new_df[column].astype(str).str.replace(r'[\$,₫€\sđVND]', '', regex=True).str.replace(',', '')
                numeric = pd.to_numeric(cleaned, errors='coerce')
                if target_type == "integer":
                    new_df[column] = numeric.astype('Int64')
                else:
                    new_df[column] = numeric.astype(float)
            elif target_type == "datetime":
                new_df[column] = pd.to_datetime(new_df[column], errors='coerce')
            elif target_type == "boolean":
                bool_map = {'true': True, '1': True, 'yes': True, 'đúng': True,
                            'false': False, '0': False, 'no': False, 'sai': False}
                new_df[column] = new_df[column].astype(str).str.lower().map(bool_map)
            elif target_type == "string":
                new_df[column] = new_df[column].astype(str).replace({"nan": None, "None": None})

    elif action == "handle_outliers":
        column = params["column"]
        method = params.get("method", "winsorize") # 'winsorize', 'drop', 'flag'
        if column in new_df.columns and pd.api.types.is_numeric_dtype(new_df[column]):
            valid = new_df[column].dropna()
            q1 = valid.quantile(0.25)
            q3 = valid.quantile(0.75)
            iqr = q3 - q1
            lower = q1 - 1.5 * iqr
            upper = q3 + 1.5 * iqr

            if method == "winsorize":
                new_df[column] = new_df[column].clip(lower=lower, upper=upper)
            elif method == "drop":
                mask = (new_df[column] >= lower) & (new_df[column] <= upper)
                new_df = new_df[mask | new_df[column].isna()].reset_index(drop=True)
            elif method == "flag":
                flag_col = f"{column}_is_outlier"
                new_df[flag_col] = (new_df[column] < lower) | (new_df[column] > upper)

    elif action == "rename_column":
        old_col = params["old_name"]
        new_col = params["new_name"]
        if old_col in new_df.columns and new_col:
            new_df = new_df.rename(columns={old_col: new_col})

    elif action == "bulk_clean":
        # Bulk clean: 1. strip text whitespace, 2. drop duplicate rows, 3. auto-convert currency/clean numeric strings
        for col in new_df.columns:
            if pd.api.types.is_string_dtype(new_df[col]) or new_df[col].dtype == 'object':
                new_df[col] = new_df[col].astype(str).str.strip().replace({"nan": None, "None": None})
                # If majority are currency/formatted numbers, convert to float
                non_null = new_df[col].dropna()
                if len(non_null) > 0:
                    cleaned_s = non_null.str.replace(r'[\$,₫€\sđVND]', '', regex=True).str.replace(',', '')
                    converted = pd.to_numeric(cleaned_s, errors='coerce')
                    if converted.notnull().sum() / len(non_null) >= 0.8:
                        new_df[col] = pd.to_numeric(new_df[col].astype(str).str.replace(r'[\$,₫€\sđVND]', '', regex=True).str.replace(',', ''), errors='coerce')
        new_df = new_df.drop_duplicates().reset_index(drop=True)

    after_stats = {
        "rows": len(new_df),
        "columns": len(new_df.columns),
        "null_count": int(new_df.isna().sum().sum()),
        "duplicates": int(new_df.duplicated().sum()),
        "rows_changed": abs(len(new_df) - len(df)),
        "nulls_changed": abs(int(new_df.isna().sum().sum()) - int(df.isna().sum().sum()))
    }

    return new_df, before_stats, after_stats

def filter_dataframe(df: pd.DataFrame, conditions: List[Dict[str, Any]], logic: str = "AND") -> pd.DataFrame:
    """
    conditions: list of {column, operator, value, value2}
    operators: 'equals', 'not_equals', 'contains', 'greater', 'less', 'between', 'in', 'is_null', 'not_null'
    logic: 'AND' | 'OR'
    """
    if not conditions:
        return df

    mask_list = []
    for cond in conditions:
        col = cond.get("column")
        op = cond.get("operator")
        val = cond.get("value")
        val2 = cond.get("value2")

        if col not in df.columns:
            continue

        series = df[col]

        if op == "is_null":
            m = series.isna()
        elif op == "not_null":
            m = series.notna()
        elif op == "equals":
            m = (series == val) | (series.astype(str) == str(val))
        elif op == "not_equals":
            m = (series != val) & (series.astype(str) != str(val))
        elif op == "contains":
            m = series.astype(str).str.contains(str(val), case=False, na=False)
        elif op == "greater":
            num_s = pd.to_numeric(series, errors='coerce')
            m = num_s > float(val)
        elif op == "less":
            num_s = pd.to_numeric(series, errors='coerce')
            m = num_s < float(val)
        elif op == "between":
            num_s = pd.to_numeric(series, errors='coerce')
            m = (num_s >= float(val)) & (num_s <= float(val2))
        elif op == "in":
            # Multi-select list
            items = val if isinstance(val, list) else [v.strip() for v in str(val).split(",")]
            m = series.astype(str).isin([str(x) for x in items])
        else:
            m = pd.Series([True] * len(df), index=df.index)

        mask_list.append(m)

    if not mask_list:
        return df

    if logic.upper() == "OR":
        final_mask = mask_list[0]
        for m in mask_list[1:]:
            final_mask = final_mask | m
    else: # AND
        final_mask = mask_list[0]
        for m in mask_list[1:]:
            final_mask = final_mask & m

    return df[final_mask].reset_index(drop=True)
