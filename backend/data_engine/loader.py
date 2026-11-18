import os
import json
import re
import unicodedata
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import pandas as pd
import numpy as np

ALLOWED_EXTENSIONS = {".xlsx", ".xls", ".csv", ".json"}

def strip_accents_and_clean(s: Any) -> str:
    """Removes Vietnamese accents, punctuation, and normalizes to lower ASCII."""
    text = str(s).replace('đ', 'd').replace('Đ', 'D')
    text = unicodedata.normalize('NFD', text)
    text = ''.join(c for c in text if unicodedata.category(c) != 'Mn')
    return re.sub(r'[^a-zA-Z0-9]+', ' ', text).strip().lower()

def to_flag(series: pd.Series) -> pd.Series:
    """
    Converts flag columns containing 'Có'/'Không', 'Yes'/'No', 'True'/'False', '1'/'0', 1/0
    strictly to nullable Int8 (1 or 0), and returns NaN for anything else.
    """
    if series is None or len(series) == 0:
        return series
    
    flag_map = {
        "có": 1, "co": 1, "yes": 1, "true": 1, "1": 1, "1.0": 1, 1: 1, 1.0: 1, "đúng": 1, "dung": 1, "đạt": 1, "dat": 1,
        "không": 0, "khong": 0, "no": 0, "false": 0, "0": 0, "0.0": 0, 0: 0, 0.0: 0, "sai": 0, "không đạt": 0, "khong dat": 0
    }

    if pd.api.types.is_bool_dtype(series) or series.dtype == bool or str(series.dtype).lower() in ("bool", "boolean"):
        return series.fillna(False).astype(int).astype("Int8")

    def _map_val(x):
        if pd.isna(x):
            return np.nan
        if isinstance(x, (bool, np.bool_)):
            return 1 if x else 0
        if isinstance(x, (int, float, np.integer, np.floating)):
            if x == 1:
                return 1
            if x == 0:
                return 0
        return flag_map.get(str(x).strip().lower(), np.nan)

    mapped = series.apply(_map_val)
    return pd.to_numeric(mapped, errors="coerce").astype("Int8")

def detect_header_row(file_path: Path, sheet_name: Optional[str] = None) -> int:
    """
    Scans the first 10 rows (0-9) to locate the row with the most non-empty text cells.
    Allows user override in UI.
    """
    try:
        ext = file_path.suffix.lower()
        rows_data: List[List[Any]] = []

        if ext in {".xlsx", ".xls"}:
            raw_top = pd.read_excel(file_path, sheet_name=sheet_name, header=None, nrows=10)
            for _, r in raw_top.iterrows():
                rows_data.append(r.tolist())
        elif ext == ".csv":
            import csv
            for enc in ["utf-8-sig", "utf-8", "latin-1"]:
                try:
                    with open(file_path, "r", encoding=enc, errors="replace") as f:
                        reader = csv.reader(f)
                        rows_data = []
                        for i, r in enumerate(reader):
                            if i >= 10:
                                break
                            rows_data.append(r)
                    break
                except Exception:
                    continue
        else:
            return 0
        
        best_row = 0
        max_non_empty = -1

        for r_idx, cells in enumerate(rows_data):
            count = sum(1 for c in cells if pd.notna(c) and str(c).strip() != "" and not str(c).startswith("Unnamed:"))
            if count > max_non_empty:
                max_non_empty = count
                best_row = int(r_idx)

        return best_row
    except Exception:
        return 0

def validate_uploaded_file(file_path: Path, max_size_bytes: int) -> Tuple[bool, Optional[str]]:
    ext = file_path.suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        return False, f"Định dạng tệp '{ext}' không được hỗ trợ. Vui lòng tải lên .xlsx, .xls, .csv, hoặc .json."
    
    file_size = file_path.stat().st_size
    if file_size == 0:
        return False, "File không có dòng dữ liệu nào."
    
    if file_size > max_size_bytes:
        max_mb = max_size_bytes / (1024 * 1024)
        return False, f"Dung lượng tệp vượt quá giới hạn cho phép ({max_mb:.0f} MB)."
    
    return True, None

def infer_column_role(series: pd.Series, col_name: str = "") -> str:
    """
    Infers the analytical role of a column from its values, using header text only as hint:
    - 'date': datetime, dates, month/year periods
    - 'number': integer, float, currency, counts
    - 'percentage': rate, %, margin, discount rate
    - 'category': discrete values (2-50 distinct values or <= 25% unique)
    - 'identifier': almost all values unique (>85% unique strings/codes or ID hints)
    - 'flag': 2 distinct values (Có/Không, Yes/No, 0/1, True/False)
    - 'free_text': long or open-ended text
    """
    valid = series.dropna()
    total_valid = len(valid)
    if total_valid == 0:
        return "free_text"
    
    col_hint = strip_accents_and_clean(col_name)

    # 1. Flag: check boolean or exactly 2 boolean-like distinct values
    if pd.api.types.is_bool_dtype(series):
        return "flag"
    
    unique_vals = valid.unique()
    num_unique = len(unique_vals)
    if num_unique == 2:
        val_set = {str(x).strip().lower() for x in unique_vals}
        known_flag_vals = {
            "true", "false", "1", "0", "1.0", "0.0", "yes", "no", "co", "khong",
            "có", "không", "đúng", "sai", "dung", "sai", "đạt", "không đạt", "dat", "khong dat"
        }
        if val_set.issubset(known_flag_vals):
            return "flag"
        if any(kw in col_hint for kw in ["flag", "co", "tra", "hoan", "return", "late", "tre", "active", "is ", "has "]):
            return "flag"

    # 2. Date / Datetime
    if pd.api.types.is_datetime64_any_dtype(series):
        return "date"
    
    if any(kw in col_hint for kw in ["ngay", "date", "thoi gian", "time", "thang", "month", "nam", "year", "quy", "quarter"]):
        # Check if values look like dates
        sample_str = valid.astype(str).head(30)
        date_pattern = re.compile(r'^\d{4}[-/.]\d{1,2}[-/.]\d{1,2}|^\d{1,2}[-/.]\d{1,2}[-/.]\d{2,4}|^\d{4}[-/.]\d{1,2}|^\d{6}$')
        if sum(bool(date_pattern.match(s.strip())) for s in sample_str) / len(sample_str) >= 0.5:
            return "date"
        try:
            pd.to_datetime(sample_str, errors="raise")
            return "date"
        except Exception:
            pass

    # Sample date regex without header hint
    sample_str = valid.astype(str).head(30)
    date_regex = re.compile(r'^\d{4}[-/.]\d{1,2}[-/.]\d{1,2}|^\d{1,2}[-/.]\d{1,2}[-/.]\d{2,4}')
    if sum(bool(date_regex.match(s.strip())) for s in sample_str) / len(sample_str) >= 0.7:
        try:
            pd.to_datetime(sample_str, errors="raise")
            return "date"
        except Exception:
            pass

    # 3. Numeric & Percentage
    is_numeric = False
    numeric_series = None
    if pd.api.types.is_numeric_dtype(series):
        is_numeric = True
        numeric_series = valid
    else:
        # Check string numbers with currency symbols, thousand commas or dots
        cleaned_sample = sample_str.str.replace(r'[\$,₫€\sđVND%]', '', regex=True).str.replace(',', '')
        try:
            converted = pd.to_numeric(cleaned_sample, errors='coerce')
            if converted.notnull().sum() / len(sample_str) >= 0.8:
                is_numeric = True
                cleaned_full = valid.astype(str).str.replace(r'[\$,₫€\sđVND%]', '', regex=True).str.replace(',', '')
                numeric_series = pd.to_numeric(cleaned_full, errors='coerce').dropna()
        except Exception:
            pass

    if is_numeric and numeric_series is not None and len(numeric_series) > 0:
        # Check percentage
        if any(kw in col_hint for kw in ["%", "ty le", "rate", "pct", "percent", "percentage", "margin", "bien", "chiet khau"]):
            return "percentage"
        if 0 <= numeric_series.min() and numeric_series.max() <= 1.0 and (numeric_series.max() - numeric_series.min()) > 0:
            return "percentage"

        # Check Identifier disguised as integer (e.g. Order_ID, Customer_ID, STT, Code with high uniqueness)
        if any(kw in col_hint for kw in ["id", "ma", "code", "stt", "key", "so hoa don", "so phieu"]):
            if num_unique / total_valid >= 0.85:
                return "identifier"

        return "number"

    # 4. Identifier (non-numeric)
    if any(kw in col_hint for kw in ["id", "ma", "code", "stt", "key", "so hoa don", "so phieu", "barcode", "sku"]):
        return "identifier"
    if total_valid >= 15 and num_unique / total_valid >= 0.88:
        return "identifier"

    # 5. Category (discrete values)
    if num_unique <= 50 or (num_unique / total_valid <= 0.25 and num_unique <= 200):
        return "category"

    # 6. Free text
    return "free_text"

def inspect_file(file_path: Path, header_row: Optional[int] = None) -> Dict[str, Any]:
    """
    Inspects tabular file (.xlsx, .xls, .csv, .json), listing all sheets with row/column counts,
    automatically detects header rows, infers column roles, and pre-selects the sheet
    with the most data rows.
    """
    ext = file_path.suffix.lower()
    file_size = file_path.stat().st_size
    file_name = file_path.name

    sheets_info: Dict[str, Any] = {}
    default_sheet = None
    warnings: List[str] = []

    if ext in {".xlsx", ".xls"}:
        try:
            xl = pd.ExcelFile(file_path)
            sheet_names = xl.sheet_names
            
            for sheet in sheet_names:
                sheet_header = header_row if header_row is not None else detect_header_row(file_path, sheet)

                try:
                    df_preview = pd.read_excel(file_path, sheet_name=sheet, header=sheet_header, nrows=25)
                    full_df = pd.read_excel(file_path, sheet_name=sheet, header=sheet_header)
                except Exception:
                    df_preview = pd.DataFrame()
                    full_df = pd.DataFrame()

                # Clean unnamed/empty columns for preview
                clean_cols = [str(c).strip() for c in full_df.columns if not str(c).startswith("Unnamed:")]
                cols = [str(c) for c in full_df.columns]
                col_roles = {col: infer_column_role(full_df[col], str(col)) for col in cols}
                
                preview_records = df_preview.head(20).replace({np.nan: None}).to_dict(orient="records")

                sheets_info[sheet] = {
                    "row_count": len(full_df),
                    "column_count": len(full_df.columns),
                    "header_row": sheet_header,
                    "columns": cols,
                    "column_types": col_roles,
                    "column_roles": col_roles,
                    "preview": preview_records,
                }

            # Pre-select the sheet with the most rows that has at least 1 data row
            sheets_with_data = {s: info for s, info in sheets_info.items() if info["row_count"] > 0}
            if sheets_with_data:
                default_sheet = max(sheets_with_data.keys(), key=lambda s: sheets_with_data[s]["row_count"])
            elif sheet_names:
                default_sheet = sheet_names[0]

        except Exception as e:
            raise ValueError(f"Không thể đọc tệp Excel '{file_name}': {str(e)}")

    elif ext == ".csv":
        csv_header = header_row if header_row is not None else detect_header_row(file_path)
        df = None
        for enc in ["utf-8", "utf-8-sig", "latin-1"]:
            try:
                df = pd.read_csv(file_path, header=csv_header, encoding=enc, nrows=25)
                full_df = pd.read_csv(file_path, header=csv_header, encoding=enc)
                break
            except Exception:
                continue
        
        if df is None:
            raise ValueError(f"Không thể đọc tệp CSV '{file_name}'. Vui lòng kiểm tra mã hóa văn bản (UTF-8).")

        cols = [str(c) for c in full_df.columns]
        col_roles = {col: infer_column_role(full_df[col], str(col)) for col in cols}
        preview_records = df.head(20).replace({np.nan: None}).to_dict(orient="records")

        sheets_info["Sheet1"] = {
            "row_count": len(full_df),
            "column_count": len(full_df.columns),
            "header_row": csv_header,
            "columns": cols,
            "column_types": col_roles,
            "column_roles": col_roles,
            "preview": preview_records,
        }
        default_sheet = "Sheet1"

    elif ext == ".json":
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            if isinstance(data, list):
                full_df = pd.DataFrame(data)
            elif isinstance(data, dict):
                first_list = next((v for v in data.values() if isinstance(v, list)), None)
                if first_list:
                    full_df = pd.DataFrame(first_list)
                else:
                    full_df = pd.DataFrame([data])
            else:
                full_df = pd.DataFrame()

            cols = [str(c) for c in full_df.columns]
            col_roles = {col: infer_column_role(full_df[col], str(col)) for col in cols}
            preview_records = full_df.head(20).replace({np.nan: None}).to_dict(orient="records")

            sheets_info["Data"] = {
                "row_count": len(full_df),
                "column_count": len(full_df.columns),
                "header_row": 0,
                "columns": cols,
                "column_types": col_roles,
                "column_roles": col_roles,
                "preview": preview_records,
            }
            default_sheet = "Data"
        except Exception as e:
            raise ValueError(f"Không thể đọc tệp JSON '{file_name}': {str(e)}")

    # Check if file has 0 data rows across all sheets
    total_data_rows = sum(info["row_count"] for info in sheets_info.values())
    if total_data_rows == 0:
        raise ValueError("File không có dòng dữ liệu nào.")

    first_sheet_data = sheets_info[default_sheet] if default_sheet else {}

    return {
        "file_name": file_name,
        "file_size": file_size,
        "extension": ext,
        "sheets": list(sheets_info.keys()),
        "default_sheet": default_sheet,
        "sheets_info": sheets_info,
        "total_rows": first_sheet_data.get("row_count", 0),
        "total_columns": first_sheet_data.get("column_count", 0),
        "header_row": header_row or first_sheet_data.get("header_row", 0),
        "columns": first_sheet_data.get("columns", []),
        "column_types": first_sheet_data.get("column_roles", {}),
        "column_roles": first_sheet_data.get("column_roles", {}),
        "preview": first_sheet_data.get("preview", []),
        "warnings": warnings
    }

def clean_and_validate_dataframe(
    df: pd.DataFrame,
    source_name: str,
    type_overrides: Optional[Dict[str, str]] = None
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Cleans raw dataframe: drops fully empty rows and columns with warnings,
    converts flags to Int8, parses dates and numerics, and checks that file has data rows.
    NEVER rejects a file for missing specific column names.
    """
    warnings: List[str] = []
    parse_errors: Dict[str, int] = {}
    parsed_types: Dict[str, str] = {}
    type_overrides = type_overrides or {}

    # 1. Drop fully empty rows
    initial_rows = len(df)
    df = df.dropna(how="all")
    dropped_empty_rows = initial_rows - len(df)
    if dropped_empty_rows > 0:
        warnings.append(f"Đã loại bỏ {dropped_empty_rows} dòng hoàn toàn trống.")

    # 2. Drop fully empty columns (all NaN or all whitespace strings)
    cols_to_drop = []
    for col in df.columns:
        s = df[col]
        if s.isna().all():
            cols_to_drop.append(col)
        elif s.dropna().astype(str).str.strip().eq("").all():
            cols_to_drop.append(col)

    if cols_to_drop:
        df = df.drop(columns=cols_to_drop)
        warnings.append(f"Cảnh báo: Đã loại bỏ {len(cols_to_drop)} cột trống không có dữ liệu ({', '.join(str(c) for c in cols_to_drop[:5])}{'...' if len(cols_to_drop) > 5 else ''}) từ nguồn '{source_name}'.")

    # 3. Reject only if no data rows at all
    if len(df) == 0:
        raise ValueError("File không có dòng dữ liệu nào.")

    # 4. Clean and parse each column dynamically according to user override or value inference
    for col in df.columns:
        col_str = str(col)
        user_override = type_overrides.get(col_str)
        inferred_role = infer_column_role(df[col], col_str)
        effective_role = user_override or inferred_role

        if effective_role == "flag":
            df[col] = to_flag(df[col])
            parsed_types[col_str] = "flag"
        elif effective_role == "date":
            initial_na = int(df[col].isna().sum())
            df[col] = pd.to_datetime(df[col], errors="coerce")
            after_na = int(df[col].isna().sum())
            parse_errors[col_str] = max(0, after_na - initial_na)
            parsed_types[col_str] = "date"
        elif effective_role in ("number", "percentage", "integer", "float"):
            initial_na = int(df[col].isna().sum())
            if df[col].dtype == object:
                cleaned_str = (
                    df[col].astype(str)
                    .str.replace(r'[\$,₫€\sđVND%]', '', regex=True)
                    .str.replace(',', '')
                )
                df[col] = pd.to_numeric(cleaned_str, errors="coerce")
            else:
                df[col] = pd.to_numeric(df[col], errors="coerce")
            after_na = int(df[col].isna().sum())
            parse_errors[col_str] = max(0, after_na - initial_na)
            parsed_types[col_str] = effective_role
        elif effective_role == "category":
            parsed_types[col_str] = "category"
        elif effective_role == "identifier":
            parsed_types[col_str] = "identifier"
        else:
            parsed_types[col_str] = "free_text"

    metadata = {
        "source": source_name,
        "rows": len(df),
        "columns": len(df.columns),
        "column_names": list(df.columns),
        "warnings": warnings,
        "parse_errors": parse_errors,
        "parsed_types": parsed_types
    }

    return df, metadata

def load_and_combine_sources(
    source_configs: List[Dict[str, Any]],
    type_overrides: Optional[Dict[str, str]] = None
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """Loads and combines user-selected sources without any hardcoded column requirements."""
    if not source_configs:
        raise ValueError("Chưa chọn nguồn dữ liệu nào để phân tích.")

    dfs: List[pd.DataFrame] = []
    combined_warnings: List[str] = []
    source_metas: List[Dict[str, Any]] = []

    for src in source_configs:
        file_path_str = src.get("file_path")
        if not file_path_str:
            continue
        file_path = Path(file_path_str)
        sheet_name = src.get("sheet_name")
        header_row = src.get("header_row", 0)

        ext = file_path.suffix.lower()
        if ext in {".xlsx", ".xls"}:
            raw_df = pd.read_excel(file_path, sheet_name=sheet_name, header=header_row)
            source_label = f"{file_path.name} [{sheet_name}]" if sheet_name else file_path.name
        elif ext == ".csv":
            raw_df = None
            for enc in ["utf-8", "utf-8-sig", "latin-1"]:
                try:
                    raw_df = pd.read_csv(file_path, header=header_row, encoding=enc)
                    break
                except Exception:
                    continue
            if raw_df is None:
                raise ValueError(f"Không thể đọc file CSV '{file_path.name}'.")
            source_label = file_path.name
        elif ext == ".json":
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, list):
                raw_df = pd.DataFrame(data)
            else:
                raw_df = pd.DataFrame([data])
            source_label = file_path.name
        else:
            continue

        cleaned_df, meta = clean_and_validate_dataframe(raw_df, source_label, type_overrides)
        dfs.append(cleaned_df)
        combined_warnings.extend(meta.get("warnings", []))
        source_metas.append(meta)

    if not dfs:
        raise ValueError("File không có dòng dữ liệu nào.")

    if len(dfs) == 1:
        final_df = dfs[0]
    else:
        # Align columns
        common_cols = list(dfs[0].columns)
        for d in dfs[1:]:
            common_cols = [c for c in common_cols if c in d.columns]
        if not common_cols:
            final_df = pd.concat(dfs, ignore_index=True)
        else:
            final_df = pd.concat([d[common_cols] for d in dfs], ignore_index=True)

    report = {
        "total_rows": len(final_df),
        "total_columns": len(final_df.columns),
        "columns": list(final_df.columns),
        "warnings": combined_warnings,
        "sources": source_metas
    }

    return final_df, report
