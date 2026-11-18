from typing import Dict, Any, List, Optional
import pandas as pd
import numpy as np
from backend.data_engine.cleaner import filter_dataframe

def get_columns_by_type(df: pd.DataFrame) -> Dict[str, List[str]]:
    numeric_cols = []
    categorical_cols = []
    datetime_cols = []
    boolean_cols = []

    for col in df.columns:
        series = df[col]
        if pd.api.types.is_numeric_dtype(series):
            numeric_cols.append(col)
        elif pd.api.types.is_datetime64_any_dtype(series):
            datetime_cols.append(col)
        elif pd.api.types.is_bool_dtype(series):
            boolean_cols.append(col)
        else:
            # Check if parseable as datetime
            sample = series.dropna().head(20).astype(str)
            if not sample.empty and sum(sample.str.match(r'^\d{4}[-/.]\d{1,2}|^\d{1,2}[-/.]\d{1,2}')) > len(sample) * 0.7:
                try:
                    pd.to_datetime(sample, errors='raise')
                    datetime_cols.append(col)
                    continue
                except Exception:
                    pass
            categorical_cols.append(col)

    return {
        "numeric": numeric_cols,
        "categorical": categorical_cols,
        "datetime": datetime_cols,
        "boolean": boolean_cols,
        "all": list(df.columns)
    }

def get_summary_statistics(df: pd.DataFrame) -> Dict[str, Any]:
    stats = {}
    col_types = get_columns_by_type(df)

    for col in df.columns:
        series = df[col]
        total_count = len(series)
        null_count = int(series.isna().sum())
        non_null_count = total_count - null_count

        if col in col_types["numeric"]:
            valid = pd.to_numeric(series, errors='coerce').dropna()
            if not valid.empty:
                stats[col] = {
                    "type": "numeric",
                    "count": non_null_count,
                    "missing": null_count,
                    "mean": round(float(valid.mean()), 2),
                    "std": round(float(valid.std()), 2) if len(valid) > 1 else 0.0,
                    "min": round(float(valid.min()), 2),
                    "q25": round(float(valid.quantile(0.25)), 2),
                    "median": round(float(valid.median()), 2),
                    "q75": round(float(valid.quantile(0.75)), 2),
                    "max": round(float(valid.max()), 2),
                    "sum": round(float(valid.sum()), 2)
                }
            else:
                stats[col] = {"type": "numeric", "count": 0, "missing": total_count}
        else:
            valid = series.dropna()
            unique_count = int(valid.nunique())
            top_val = None
            top_freq = None
            if not valid.empty:
                vc = valid.value_counts()
                top_val = str(vc.index[0])
                top_freq = int(vc.iloc[0])

            stats[col] = {
                "type": "datetime" if col in col_types["datetime"] else "categorical",
                "count": non_null_count,
                "missing": null_count,
                "unique": unique_count,
                "top": top_val,
                "frequency": top_freq
            }

    return stats

def get_correlation_matrix(df: pd.DataFrame) -> Dict[str, Any]:
    col_types = get_columns_by_type(df)
    numeric_cols = col_types["numeric"]

    if len(numeric_cols) < 2:
        return {"columns": numeric_cols, "matrix": [], "pairs": []}

    numeric_df = df[numeric_cols].apply(pd.to_numeric, errors='coerce')
    corr = numeric_df.corr(method='pearson').fillna(0)

    matrix = []
    for row_col in numeric_cols:
        row_data = {"name": row_col}
        for col_name in numeric_cols:
            row_data[col_name] = round(float(corr.loc[row_col, col_name]), 3)
        matrix.append(row_data)

    # Top correlated pairs
    pairs = []
    seen = set()
    for i, c1 in enumerate(numeric_cols):
        for j, c2 in enumerate(numeric_cols):
            if i < j:
                val = float(corr.loc[c1, c2])
                pairs.append({
                    "col1": c1,
                    "col2": c2,
                    "correlation": round(val, 3),
                    "abs_correlation": round(abs(val), 3)
                })
    pairs.sort(key=lambda x: x["abs_correlation"], reverse=True)

    return {
        "columns": numeric_cols,
        "matrix": matrix,
        "pairs": pairs[:15]
    }

def get_distributions(df: pd.DataFrame, column: str, bins: int = 10) -> Dict[str, Any]:
    if column not in df.columns:
        return {"data": []}

    series = df[column]
    if pd.api.types.is_numeric_dtype(series):
        valid = pd.to_numeric(series, errors='coerce').dropna()
        if valid.empty:
            return {"data": []}
        
        counts, bin_edges = np.histogram(valid, bins=bins)
        data = []
        for i in range(len(counts)):
            label = f"{bin_edges[i]:.1f} - {bin_edges[i+1]:.1f}"
            data.append({
                "range": label,
                "count": int(counts[i]),
                "start": float(bin_edges[i]),
                "end": float(bin_edges[i+1])
            })
        return {
            "type": "numeric",
            "column": column,
            "data": data,
            "min": float(valid.min()),
            "max": float(valid.max()),
            "mean": float(valid.mean())
        }
    else:
        # Categorical top values
        valid = series.dropna().astype(str)
        vc = valid.value_counts().head(15)
        data = [{"category": str(k), "count": int(v)} for k, v in vc.items()]
        return {
            "type": "categorical",
            "column": column,
            "data": data
        }

def compute_pivot_data(
    df: pd.DataFrame,
    rows: List[str],
    cols: List[str],
    values: List[str],
    agg_func: str = "sum", # 'sum', 'average', 'count', 'min', 'max', 'median'
    filters: Optional[List[Dict[str, Any]]] = None,
    sort_order: str = "desc"
) -> Dict[str, Any]:
    filtered_df = filter_dataframe(df, filters) if filters else df

    if filtered_df.empty:
        return {"rows": [], "columns": [], "chart_data": [], "table_data": [], "total_rows": 0}

    # Map aggregation function
    agg_map = {
        "sum": "sum",
        "average": "mean",
        "avg": "mean",
        "count": "count",
        "min": "min",
        "max": "max",
        "median": "median"
    }
    numpy_agg = agg_map.get(agg_func.lower(), "sum")

    # If no rows or values selected, fallback gracefully
    if not rows and not cols:
        return {"rows": [], "columns": [], "chart_data": [], "table_data": [], "total_rows": len(filtered_df)}

    # Ensure value column is numeric if agg is sum/mean/median
    val_col = values[0] if values else None
    if val_col and numpy_agg in {"sum", "mean", "median"}:
        filtered_df = filtered_df.copy()
        filtered_df[val_col] = pd.to_numeric(filtered_df[val_col], errors='coerce').fillna(0)

    try:
        if rows and not cols:
            # Simple group by rows
            if val_col:
                grouped = filtered_df.groupby(rows, observed=False)[val_col].agg(numpy_agg).reset_index()
            else:
                grouped = filtered_df.groupby(rows, observed=False).size().reset_index(name="count")
                val_col = "count"

            # Sort
            if val_col in grouped.columns:
                grouped = grouped.sort_values(by=val_col, ascending=(sort_order == "asc"))

            chart_data = []
            for _, r in grouped.head(100).iterrows():
                row_label = " - ".join([str(r[c]) for c in rows])
                chart_data.append({
                    "name": row_label,
                    val_col: round(float(r[val_col]), 2) if isinstance(r[val_col], (int, float, np.number)) else str(r[val_col]),
                    **{c: str(r[c]) for c in rows}
                })

            return {
                "chart_data": chart_data,
                "table_data": chart_data,
                "row_keys": rows,
                "col_keys": [],
                "value_col": val_col,
                "total_rows": len(filtered_df)
            }

        elif rows and cols:
            # 2D Pivot table
            if not val_col:
                filtered_df["_count_"] = 1
                val_col = "_count_"
                numpy_agg = "count"

            piv = pd.pivot_table(
                filtered_df,
                index=rows,
                columns=cols,
                values=val_col,
                aggfunc=numpy_agg,
                fill_value=0,
                observed=False
            )

            # Flatten column multi-index
            if isinstance(piv.columns, pd.MultiIndex):
                piv.columns = [" - ".join([str(v) for v in col]).strip() for col in piv.columns]
            else:
                piv.columns = [str(col) for col in piv.columns]

            piv = piv.reset_index()
            # Construct row label
            piv["name"] = piv[rows].astype(str).agg(" - ".join, axis=1)

            chart_cols = [c for c in piv.columns if c not in rows and c != "name"]
            records = piv.to_dict(orient="records")

            # Clean NaNs in records
            for r in records:
                for k, v in r.items():
                    if pd.isna(v):
                        r[k] = 0
                    elif isinstance(v, (np.floating, float)):
                        r[k] = round(float(v), 2)
                    elif isinstance(v, (np.integer, int)):
                        r[k] = int(v)

            return {
                "chart_data": records[:100],
                "table_data": records,
                "row_keys": rows,
                "col_keys": chart_cols,
                "value_col": val_col,
                "total_rows": len(filtered_df)
            }
        else:
            # Only cols selected
            grouped = filtered_df.groupby(cols, observed=False)[val_col].agg(numpy_agg).reset_index()
            chart_data = [{"name": str(r[cols[0]]), val_col: round(float(r[val_col]), 2)} for _, r in grouped.iterrows()]
            return {
                "chart_data": chart_data,
                "table_data": chart_data,
                "row_keys": cols,
                "col_keys": [],
                "value_col": val_col,
                "total_rows": len(filtered_df)
            }

    except Exception as e:
        return {
            "error": str(e),
            "chart_data": [],
            "table_data": [],
            "total_rows": len(filtered_df)
        }

def drill_down_records(
    df: pd.DataFrame,
    row_filters: Dict[str, Any],
    limit: int = 50
) -> List[Dict[str, Any]]:
    """
    Returns underlying rows matching specific row segment values.
    """
    sub_df = df.copy()
    for col, val in row_filters.items():
        if col in sub_df.columns:
            sub_df = sub_df[sub_df[col].astype(str) == str(val)]

    records = sub_df.head(limit).replace({np.nan: None}).to_dict(orient="records")
    return records
