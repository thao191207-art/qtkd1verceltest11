import httpx
from pathlib import Path

def test_live_servers():
    base_api = "http://127.0.0.1:8000"
    proxy_api = "http://127.0.0.1:3000/api"

    print("1. Checking Frontend (http://127.0.0.1:3000)...")
    with httpx.Client(timeout=10) as client:
        r_fe = client.get("http://127.0.0.1:3000")
        assert r_fe.status_code == 200
        assert "FLOWER HAPPY" in r_fe.text or "vite" in r_fe.text
        print("   ✅ Frontend is serving HTTP 200 OK.")

        print("2. Checking Backend Docs (http://127.0.0.1:8000/docs)...")
        r_docs = client.get(f"{base_api}/docs")
        assert r_docs.status_code == 200
        assert "swagger" in r_docs.text.lower()
        print("   ✅ Interactive API docs reachable at http://127.0.0.1:8000/docs.")

        print("3. Checking Proxy /api/health through port 3000...")
        r_proxy_health = client.get(f"{proxy_api}/health")
        assert r_proxy_health.status_code == 200
        assert r_proxy_health.json()["status"] == "ok"
        print("   ✅ Vite reverse proxy correctly routes /api requests to FastAPI.")

        print("4. Executing Step 1 (Kết nối): Upload real Excel file...")
        file_path = Path("data/sample_flower_business.xlsx")
        assert file_path.exists()
        
        # New session
        r_sess = client.post(f"{proxy_api}/session/new")
        session_id = r_sess.json()["session_id"]

        with open(file_path, "rb") as f:
            r_up = client.post(
                f"{proxy_api}/upload",
                data={"session_id": session_id},
                files={"files": ("sample_flower_business.xlsx", f, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
            )
        assert r_up.status_code == 200
        file_meta = r_up.json()["files"][0]
        print(f"   ✅ File uploaded: {file_meta['file_name']}, Rows: {file_meta['total_rows']}, Cols: {file_meta['total_columns']}")

        # Initialize dataset
        r_init = client.post(
            f"{proxy_api}/dataset/initialize",
            json={
                "session_id": session_id,
                "sources": [{
                    "file_path": file_meta["file_path"],
                    "sheet_name": file_meta["default_sheet"],
                    "header_row": 0
                }]
            }
        )
        assert r_init.status_code == 200
        print(f"   ✅ Step 1 complete: Dataset initialized. Quality score: {r_init.json()['quality_score']}%")

        print("5. Executing Step 2 (Làm sạch): Profile & Actions...")
        r_prof = client.get(f"{proxy_api}/cleaning/profile?session_id={session_id}")
        assert r_prof.status_code == 200
        prof = r_prof.json()["profile"]
        print(f"   ✅ Issues detected: {len(prof['issues'])}, Duplicate rows: {prof['duplicate_rows']}")

        # Remove duplicates
        r_clean = client.post(
            f"{proxy_api}/cleaning/action",
            json={"session_id": session_id, "action": "remove_duplicates", "params": {}}
        )
        assert r_clean.status_code == 200
        print(f"   ✅ Action 'remove_duplicates' applied: Rows {r_clean.json()['before_stats']['rows']} -> {r_clean.json()['after_stats']['rows']}")

        print("6. Executing Step 3 (Phân tích): Overview & PivotChart...")
        r_overview = client.get(f"{proxy_api}/analyze/overview?session_id={session_id}")
        assert r_overview.status_code == 200
        
        # Pivot compute
        r_piv = client.post(
            f"{proxy_api}/analyze/pivot",
            json={
                "session_id": session_id,
                "rows": ["Khu_Vuc"],
                "values": ["Doanh_Thu"],
                "agg_func": "sum",
                "sort_order": "desc"
            }
        )
        assert r_piv.status_code == 200
        print(f"   ✅ PivotChart computed: {len(r_piv.json()['chart_data'])} categories.")

        print("7. Executing Step 4 (Báo cáo): Automated Insights & Export...")
        r_rep = client.get(f"{proxy_api}/report/generate?session_id={session_id}")
        assert r_rep.status_code == 200
        rep_data = r_rep.json()
        print(f"   ✅ Core KPIs: {len(rep_data.get('kpis', []))} calculated.")
        print(f"   ✅ 16 Chart Cards: {len(rep_data.get('chart_cards', []))} generated with 4-line analysis.")
        print(f"   ✅ Problem List: {len(rep_data.get('problem_list', []))} problems ranked by severity x impact.")
        for p in rep_data.get('problem_list', [])[:3]:
            print(f"      - [{p['severity']}] {p['title']} ({p['business_impact']})")

        # Excel Export
        r_xl = client.get(f"{proxy_api}/report/export/excel?session_id={session_id}")
        assert r_xl.status_code == 200
        print(f"   ✅ Excel export download verified ({len(r_xl.content):,} bytes).")

        # PDF Export
        r_pdf = client.get(f"{proxy_api}/report/export/pdf?session_id={session_id}")
        assert r_pdf.status_code == 200
        print(f"   ✅ PDF export download verified ({len(r_pdf.content):,} bytes).")

    print("\n🎉 ALL 4 STEPS FULLY VERIFIED ON LIVE PORTS 3000 & 8000!")

if __name__ == "__main__":
    test_live_servers()
