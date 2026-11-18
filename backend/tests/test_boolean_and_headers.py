from pathlib import Path
import pytest
import pandas as pd
import numpy as np
from backend.data_engine.loader import (
    to_flag,
    detect_header_row,
    clean_and_validate_dataframe,
    load_and_combine_sources
)
from backend.data_engine.cleaner import profile_dataset, apply_cleaning_action

REAL_WORKBOOK_PATH = Path(r"C:\Users\ADMIIN\Downloads\Dashboard_Ban_hang.xlsx")

def test_to_flag_conversions():
    # 1. Test string values
    s_str = pd.Series(["Có", "Không", "yes", "NO", "true", "FALSE", "1", "0", "invalid", None])
    flag_res = to_flag(s_str)
    assert flag_res.iloc[0] == 1
    assert flag_res.iloc[1] == 0
    assert flag_res.iloc[2] == 1
    assert flag_res.iloc[3] == 0
    assert flag_res.iloc[4] == 1
    assert flag_res.iloc[5] == 0
    assert flag_res.iloc[6] == 1
    assert flag_res.iloc[7] == 0
    assert pd.isna(flag_res.iloc[8])
    assert pd.isna(flag_res.iloc[9])

    # 2. Test boolean dtype series
    s_bool = pd.Series([True, False, True, False])
    flag_bool = to_flag(s_bool)
    assert flag_bool.iloc[0] == 1
    assert flag_bool.iloc[1] == 0
    assert str(flag_bool.dtype).lower() == "int8"

def test_profile_dataset_no_boolean_subtract_error():
    # Ensure profile_dataset never fails with numpy boolean subtract
    df = pd.DataFrame({
        "bool_col": [True, False, True, False, True, False, True],
        "flag_col": to_flag(pd.Series(["Có", "Không", "Có", "Không", "Có", "Không", "Có"])),
        "num_col": [10.5, 20.0, 15.2, 100.0, 12.0, 14.5, 18.2]
    })
    
    prof = profile_dataset(df)
    assert prof["quality_score"] > 0
    assert "bool_col" in prof["columns_profile"]
    assert "flag_col" in prof["columns_profile"]
    assert prof["columns_profile"]["bool_col"]["is_numeric"] is False

def test_header_detection_and_column_normalization(tmp_path):
    # Create CSV with empty row, title row, then headers with messy spaces and casing
    csv_file = tmp_path / "test_dirty.csv"
    lines = [
        "BÁO CÁO DOANH SỐ NỘI BỘ",
        "Ghi chú: Dữ liệu chưa khóa sổ",
        " Order_ID , order_date , SALES_vnd , NET_SALES_vnd , PROFIT_vnd , channel , region ",
        "ORD-001,2025-01-01,1600000,1500000,300000,Online,Miền Bắc",
        "ORD-002,2025-01-02,2100000,2000000,500000,Trực tiếp,Miền Nam"
    ]
    csv_file.write_text("\n".join(lines), encoding="utf-8")

    # Header row should be detected as row 2 (0-indexed)
    detected_row = detect_header_row(csv_file)
    assert detected_row == 2

    # Load file with clean_and_validate
    df = pd.read_csv(csv_file, header=detected_row)
    cleaned_df, meta = clean_and_validate_dataframe(df, "test_dirty.csv")
    
    # Check normalized canonical column names
    assert "Order_ID" in cleaned_df.columns
    assert "Order_Date" in cleaned_df.columns
    assert "Sales_VND" in cleaned_df.columns
    assert "Net_Sales_VND" in cleaned_df.columns
    assert "Profit_VND" in cleaned_df.columns
    assert "Channel" in cleaned_df.columns
    assert "Region" in cleaned_df.columns

@pytest.mark.skipif(not REAL_WORKBOOK_PATH.exists(), reason="Real workbook file not found in Downloads")
def test_real_workbook_load_and_profile_end_to_end():
    # Load and initialize the real workbook
    df, meta = load_and_combine_sources([
        {"file_path": str(REAL_WORKBOOK_PATH), "sheet_name": "Dữ liệu", "header_row": 0}
    ])
    assert len(df) == 15000
    assert len(df.columns) == 27
    
    # Run profile_dataset
    prof = profile_dataset(df)
    assert prof["quality_score"] > 70
    assert prof["total_rows"] == 15000
    assert prof["total_cols"] == 27
    assert prof["columns_profile"]["Return_Flag"]["outliers_iqr"] == 0
