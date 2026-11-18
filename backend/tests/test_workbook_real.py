import io
from pathlib import Path
import pytest
import pandas as pd
from backend.data_engine.loader import load_and_combine_sources, clean_and_validate_dataframe, EXPECTED_27_COLUMNS
from backend.data_engine.reporter import generate_insights_and_report, export_report_excel, export_report_pdf

REAL_WORKBOOK_PATH = Path(r"C:\Users\ADMIIN\Downloads\Dashboard_Ban_hang.xlsx")

@pytest.mark.skipif(not REAL_WORKBOOK_PATH.exists(), reason="Real workbook file not found in Downloads")
def test_real_workbook_load_and_columns():
    # 1. Load real workbook's "Dữ liệu" sheet
    df, meta = load_and_combine_sources([
        {"file_path": str(REAL_WORKBOOK_PATH), "sheet_name": "Dữ liệu", "header_row": 0}
    ])

    # Assert 15,000 rows
    assert len(df) == 15000, f"Expected 15,000 rows, got {len(df)}"

    # Assert 27 named columns
    assert len(df.columns) == 27, f"Expected 27 columns after dropping AB/AC, got {len(df.columns)}"
    assert list(df.columns) == EXPECTED_27_COLUMNS, "Columns do not match expected 27 named columns"

    # Assert warnings contains note on dropped columns AB and AC
    assert len(meta.get("warnings", [])) > 0, "Expected warning about dropping columns AB and AC"
    assert any("loại bỏ" in w.lower() for w in meta.get("warnings", [])), "Warning message missing"

@pytest.mark.skipif(not REAL_WORKBOOK_PATH.exists(), reason="Real workbook file not found in Downloads")
def test_real_workbook_kpi_sums():
    df, _ = load_and_combine_sources([
        {"file_path": str(REAL_WORKBOOK_PATH), "sheet_name": "Dữ liệu", "header_row": 0}
    ])
    report = generate_insights_and_report(df, quality_score=98)

    # Calculate exact sums from workbook
    raw_df = pd.read_excel(REAL_WORKBOOK_PATH, sheet_name="Dữ liệu")
    expected_net_sales = float(raw_df["Net_Sales_VND"].sum())
    expected_profit = float(raw_df["Profit_VND"].sum())

    # Get computed KPIs
    kpi_map = {k["id"]: k["numeric_value"] for k in report["kpis"]}

    assert abs(kpi_map["kpi_revenue"] - expected_net_sales) < 1.0, "Net Sales sum does not match workbook sum"
    assert abs(kpi_map["kpi_profit"] - expected_profit) < 1.0, "Profit sum does not match workbook sum"

    # Acceptance values: 19,315.922 tr đ and 4,748.668 tr đ
    assert round(expected_net_sales / 1e6, 3) == 19315.922
    assert round(expected_profit / 1e6, 3) == 4748.668
    assert round((expected_profit / expected_net_sales) * 100, 3) == 24.584

@pytest.mark.skipif(not REAL_WORKBOOK_PATH.exists(), reason="Real workbook file not found in Downloads")
def test_each_chart_has_nonzero_data():
    df, _ = load_and_combine_sources([
        {"file_path": str(REAL_WORKBOOK_PATH), "sheet_name": "Dữ liệu", "header_row": 0}
    ])
    report = generate_insights_and_report(df, quality_score=98)

    chart_cards = report["chart_cards"]
    assert len(chart_cards) >= 6, f"Expected at least 6 charts, got {len(chart_cards)}"

    for card in chart_cards:
        assert not card.get("disabled"), f"Chart {card['id']} is disabled: {card.get('reason')}"
        data = card.get("data", [])
        assert len(data) > 0, f"Chart {card['id']} has empty data"

        # Check at least one non-zero numeric value
        found_nonzero = False
        for record in data:
            if isinstance(record, dict):
                for v in record.values():
                    if isinstance(v, (int, float)) and v != 0:
                        found_nonzero = True
                        break
            if found_nonzero:
                break
        assert found_nonzero, f"Chart {card['id']} has no non-zero values"

        # Check analysis text: no 0.0 tr and no invalid columns
        an = card.get("analysis", {})
        for field in ["phat_hien", "bang_chung", "y_nghia", "de_xuat"]:
            text = an.get(field, "")
            assert "0.0 tr" not in text, f"Chart {card['id']} has '0.0 tr' in {field}: {text}"
            assert "100.00% đến 100.00%" not in text, f"Chart {card['id']} has equal range in {field}: {text}"

@pytest.mark.skipif(not REAL_WORKBOOK_PATH.exists(), reason="Real workbook file not found in Downloads")
def test_export_excel_and_pdf():
    df, _ = load_and_combine_sources([
        {"file_path": str(REAL_WORKBOOK_PATH), "sheet_name": "Dữ liệu", "header_row": 0}
    ])
    report = generate_insights_and_report(df, quality_score=98)

    excel_stream = export_report_excel(df, report)
    assert isinstance(excel_stream, io.BytesIO)
    assert len(excel_stream.getvalue()) > 50000

    pdf_stream = export_report_pdf(df, report)
    assert isinstance(pdf_stream, io.BytesIO)
    assert len(pdf_stream.getvalue()) > 5000
