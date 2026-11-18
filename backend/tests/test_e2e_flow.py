import pytest
from pathlib import Path
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_full_pipeline_end_to_end():
    # 1. Health check
    res_health = client.get("/api/health")
    assert res_health.status_code == 200
    assert res_health.json()["status"] == "ok"

    # 2. Create new session
    res_sess = client.post("/api/session/new")
    assert res_sess.status_code == 200
    session_id = res_sess.json()["session_id"]
    assert session_id

    # 3. Upload file (Connect Page)
    sample_file_path = Path("data/sample_flower_business.xlsx")
    assert sample_file_path.exists()

    with open(sample_file_path, "rb") as f:
        res_upload = client.post(
            "/api/upload",
            data={"session_id": session_id},
            files={"files": ("sample_flower_business.xlsx", f, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
        )
    assert res_upload.status_code == 200
    upload_data = res_upload.json()
    assert len(upload_data["files"]) == 1
    file_info = upload_data["files"][0]
    assert file_info["file_name"] == "sample_flower_business.xlsx"
    assert file_info["total_rows"] == 354
    assert file_info["total_columns"] == 11
    assert "Doanh_Thu_2026" in file_info["sheets"]

    # 4. Initialize dataset (Unlocks Step 2)
    res_init = client.post(
        "/api/dataset/initialize",
        json={
            "session_id": session_id,
            "sources": [
                {
                    "file_path": file_info["file_path"],
                    "sheet_name": "Doanh_Thu_2026",
                    "header_row": 0
                }
            ]
        }
    )
    assert res_init.status_code == 200
    init_data = res_init.json()
    assert init_data["total_rows"] == 354
    assert init_data["total_columns"] == 11
    assert init_data["quality_score"] > 0

    # 5. Profile cleaning (Clean Page)
    res_prof = client.get(f"/api/cleaning/profile?session_id={session_id}")
    assert res_prof.status_code == 200
    prof = res_prof.json()["profile"]
    assert prof["duplicate_rows"] == 4  # The 4 duplicates we intentionally injected
    assert len(prof["issues"]) >= 2

    # 6. Apply cleaning: remove duplicates
    res_clean_dup = client.post(
        "/api/cleaning/action",
        json={
            "session_id": session_id,
            "action": "remove_duplicates",
            "params": {}
        }
    )
    assert res_clean_dup.status_code == 200
    after_dup_stats = res_clean_dup.json()["after_stats"]
    assert after_dup_stats["duplicates"] == 0
    assert after_dup_stats["rows"] == 350

    # 7. Apply cleaning: standardize text (trim whitespace on Khu_Vuc)
    res_clean_trim = client.post(
        "/api/cleaning/action",
        json={
            "session_id": session_id,
            "action": "standardize_text",
            "params": {"column": "Khu_Vuc", "operation": "trim"}
        }
    )
    assert res_clean_trim.status_code == 200

    # 8. Preview table
    res_prev = client.get(f"/api/cleaning/preview?session_id={session_id}&page=1&limit=10")
    assert res_prev.status_code == 200
    assert len(res_prev.json()["records"]) == 10

    # 9. Overview and Pivot Analysis (Analyze Page)
    res_overview = client.get(f"/api/analyze/overview?session_id={session_id}")
    assert res_overview.status_code == 200
    overview_data = res_overview.json()
    assert "Doanh_Thu" in overview_data["summary"]
    assert "correlations" in overview_data

    # 10. Pivot table calculation
    res_pivot = client.post(
        "/api/analyze/pivot",
        json={
            "session_id": session_id,
            "rows": ["Khu_Vuc"],
            "cols": [],
            "values": ["Doanh_Thu"],
            "agg_func": "sum",
            "sort_order": "desc"
        }
    )
    assert res_pivot.status_code == 200
    pivot_data = res_pivot.json()
    assert len(pivot_data["chart_data"]) == 5  # 5 distinct regions
    assert "Doanh_Thu" in pivot_data["chart_data"][0]

    # 11. Drill down
    res_drill = client.post(
        "/api/analyze/drilldown",
        json={
            "session_id": session_id,
            "row_filters": {"Khu_Vuc": "Hà Nội"},
            "limit": 20
        }
    )
    assert res_drill.status_code == 200
    assert len(res_drill.json()["records"]) > 0

    # 12. Automated Insights & Report (Report Page)
    res_report = client.get(f"/api/report/generate?session_id={session_id}")
    assert res_report.status_code == 200
    rep = res_report.json()
    assert len(rep["kpis"]) >= 3
    assert len(rep["main_problems"]) >= 1
    assert len(rep["chart_cards"]) >= 1
    # Check problem has severity and impact
    assert rep["main_problems"][0]["severity"] in ["CAO", "TRUNG BÌNH", "THẤP"]
    assert "impact_str" in rep["main_problems"][0]

    # 13. Export Excel
    res_excel = client.get(f"/api/report/export/excel?session_id={session_id}")
    assert res_excel.status_code == 200
    assert res_excel.headers["content-type"] == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    assert len(res_excel.content) > 1000

    # 14. Export PDF
    res_pdf = client.get(f"/api/report/export/pdf?session_id={session_id}")
    assert res_pdf.status_code == 200
    assert res_pdf.headers["content-type"] == "application/pdf"
    assert len(res_pdf.content) > 1000
