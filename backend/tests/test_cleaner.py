import pytest
import pandas as pd
import numpy as np
from backend.data_engine.cleaner import (
    profile_dataset, apply_cleaning_action, filter_dataframe, calculate_quality_score
)

def test_profile_dataset_detects_duplicates_and_missing():
    data = {
        "Name": ["Hoa Hồng", "Hoa Lan", "Hoa Lan", None, "Hoa Cúc"],
        "Price": [100.0, 200.0, 200.0, 150.0, None],
        "Category": ["VIP", "VIP", "VIP", "Standard", "Standard"]
    }
    df = pd.DataFrame(data)
    profile = profile_dataset(df)

    assert profile["total_rows"] == 5
    assert profile["total_cols"] == 3
    assert profile["duplicate_rows"] == 1  # Row index 1 and 2 are identical
    assert len(profile["issues"]) >= 2
    assert profile["quality_score"] < 100

def test_clean_action_remove_duplicates():
    df = pd.DataFrame({
        "A": [1, 2, 2, 3],
        "B": ["x", "y", "y", "z"]
    })
    new_df, before, after = apply_cleaning_action(df, "remove_duplicates", {})
    assert len(new_df) == 3
    assert after["duplicates"] == 0

def test_clean_action_fill_missing():
    df = pd.DataFrame({
        "Val": [10.0, 20.0, None, 30.0]
    })
    # Mean fill
    new_df, before, after = apply_cleaning_action(df, "fill_missing", {"column": "Val", "method": "mean"})
    assert new_df["Val"].isna().sum() == 0
    assert new_df["Val"].iloc[2] == 20.0

    # Drop missing
    new_df2, _, after2 = apply_cleaning_action(df, "fill_missing", {"column": "Val", "method": "drop"})
    assert len(new_df2) == 3

def test_clean_action_standardize_text():
    df = pd.DataFrame({
        "City": ["  Hà Nội  ", "Đà NẴNG", "sài gòn "]
    })
    new_df, _, _ = apply_cleaning_action(df, "standardize_text", {"column": "City", "operation": "trim"})
    assert new_df["City"].iloc[0] == "Hà Nội"

    new_df_lower, _, _ = apply_cleaning_action(df, "standardize_text", {"column": "City", "operation": "lowercase"})
    assert new_df_lower["City"].iloc[1] == "đà nẵng"

def test_filter_dataframe():
    df = pd.DataFrame({
        "Item": ["A", "B", "C", "D"],
        "Qty": [5, 15, 25, 35]
    })
    conds = [{"column": "Qty", "operator": "greater", "value": 10}]
    res = filter_dataframe(df, conds)
    assert len(res) == 3
    assert "A" not in res["Item"].values
