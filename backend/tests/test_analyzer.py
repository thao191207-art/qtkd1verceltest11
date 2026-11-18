import pytest
import pandas as pd
from backend.data_engine.analyzer import (
    get_columns_by_type, get_summary_statistics, get_correlation_matrix,
    compute_pivot_data, drill_down_records
)

def test_pivot_computation():
    df = pd.DataFrame({
        "Region": ["North", "North", "South", "South"],
        "Product": ["Rose", "Lily", "Rose", "Lily"],
        "Sales": [100, 150, 200, 250]
    })
    pivot_res = compute_pivot_data(
        df=df,
        rows=["Region"],
        cols=["Product"],
        values=["Sales"],
        agg_func="sum"
    )

    assert "chart_data" in pivot_res
    assert len(pivot_res["chart_data"]) == 2  # North and South
    assert pivot_res["total_rows"] == 4

def test_drill_down():
    df = pd.DataFrame({
        "Branch": ["HCM", "HN", "HCM"],
        "Amount": [10, 20, 30]
    })
    records = drill_down_records(df, {"Branch": "HCM"})
    assert len(records) == 2
    assert all(r["Branch"] == "HCM" for r in records)
