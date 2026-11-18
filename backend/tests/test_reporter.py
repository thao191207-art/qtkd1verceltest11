import io
import pytest
import pandas as pd
from backend.data_engine.reporter import generate_insights_and_report, export_report_excel, export_report_pdf

def test_generate_insights_on_synthetic_data():
    data = {
        "Order_ID": [f"ORD{i}" for i in range(100)],
        "Net_Sales_VND": [1000000.0 + i * 50000 for i in range(100)],
        "Profit_VND": [250000.0 + i * 12000 for i in range(100)],
        "Cost_VND": [750000.0 + i * 38000 for i in range(100)],
        "Channel": ["Cửa hàng trực tiếp", "Website / App", "Sàn TMĐT", "Cửa hàng trực tiếp"] * 25,
        "Region": ["Miền Bắc", "Miền Nam", "Miền Trung", "Miền Nam"] * 25,
        "City": ["Hà Nội", "TP. Hồ Chí Minh", "Đà Nẵng", "Cần Thơ"] * 25,
        "Category": ["Dược phẩm", "Thực phẩm chức năng", "Dược mỹ phẩm", "Thiết bị y tế"] * 25,
        "Subcategory": ["Tim mạch", "Kháng sinh", "Vitamin", "Khẩu trang"] * 25,
        "Segment": ["Cá nhân", "VIP", "B2B", "Cá nhân"] * 25,
        "Shipping_Days": [1, 2, 4, 5] * 25,
        "Customer_Satisfaction": [4.5, 4.2, 2.5, 2.1] * 25,
        "Discount": [0.0, 0.05, 0.15, 0.20] * 25,
        "Returned": ["Không", "Không", "Có", "Không"] * 25,
        "Payment_Method": ["COD", "Thẻ tín dụng", "Ví MoMo", "ZaloPay"] * 25,
        "Month_Key": ["202401", "202402", "202403", "202404"] * 25,
        "Quarter_Key": ["20241", "20241", "20242", "20242"] * 25,
    }
    df = pd.DataFrame(data)
    report = generate_insights_and_report(df, quality_score=98)

    assert "kpis" in report
    assert len(report["kpis"]) == 6
    assert "chart_cards" in report
    assert len(report["chart_cards"]) >= 6
    assert "main_problems" in report
    assert len(report["main_problems"]) >= 1
    assert "problem_groups" in report
    assert len(report["problem_groups"]) >= 1

    # Check analysis structure on first chart card
    card1 = report["chart_cards"][0]
    assert "analysis" in card1
    an1 = card1["analysis"]
    assert "phat_hien" in an1
    assert "bang_chung" in an1
    assert "y_nghia" in an1
    assert "de_xuat" in an1
    assert an1["severity"] in ["CAO", "TRUNG BÌNH", "THẤP"]

    # Test Excel export
    excel_stream = export_report_excel(df, report)
    assert isinstance(excel_stream, io.BytesIO)
    assert len(excel_stream.getvalue()) > 0

    # Test PDF export
    pdf_stream = export_report_pdf(df, report)
    assert isinstance(pdf_stream, io.BytesIO)

def test_planner_on_small_3_column_csv():
    # Small 3-col 50-row dataset
    df_small = pd.DataFrame({
        "Category": ["Hoa hồng", "Hoa ly", "Hoa lan", "Hoa tulip", "Hoa cúc"] * 10,
        "Sales_VND": [1000000 + i * 50000 for i in range(50)],
        "Quantity": [5 + (i % 8) for i in range(50)]
    })
    report = generate_insights_and_report(df_small, quality_score=95)
    assert "planner_summary" in report
    assert "Đã tự động" in report["planner_summary"]
    # Must have fewer charts (1 or 2), not 16
    assert 1 <= len(report["chart_cards"]) <= 3
    # All charts must be active (disabled == False)
    for c in report["chart_cards"]:
        assert c.get("disabled") is False
        assert len(c.get("data", [])) > 0
    # No empty sections
    assert len(report["problem_groups"]) >= 1

def test_planner_on_date_only_no_measures():
    # Date only, no numeric measures
    df_date = pd.DataFrame({
        "Date": pd.date_range("2025-01-01", periods=10, freq="D"),
        "Note": [f"Ghi chú {i}" for i in range(10)]
    })
    report = generate_insights_and_report(df_date, quality_score=90)
    assert len(report["chart_cards"]) == 0
    assert len(report["main_problems"]) == 0
    assert "không có cột số đo" in report["planner_summary"].lower()
