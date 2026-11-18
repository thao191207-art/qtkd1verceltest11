import os
import shutil
from pathlib import Path
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel

from backend.config import (
    HOST, BACKEND_PORT, FRONTEND_PORT, UPLOAD_PATH,
    MAX_UPLOAD_SIZE_BYTES, MAX_UPLOAD_SIZE_MB
)
from backend.session_store import session_manager
from backend.data_engine.loader import (
    validate_uploaded_file, inspect_file, load_and_combine_sources
)
from backend.data_engine.cleaner import (
    profile_dataset, apply_cleaning_action, filter_dataframe
)
from backend.data_engine.analyzer import (
    get_columns_by_type, get_summary_statistics,
    get_correlation_matrix, get_distributions,
    compute_pivot_data, drill_down_records
)
from backend.data_engine.reporter import (
    generate_insights_and_report, export_report_excel, export_report_pdf
)

app = FastAPI(
    title="FLOWER HAPPY API",
    description="Backend API phục vụ phân tích dữ liệu kinh doanh thực tế",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS
origins = [
    f"http://localhost:{FRONTEND_PORT}",
    f"http://127.0.0.1:{FRONTEND_PORT}",
    f"http://localhost:3000",
    f"http://127.0.0.1:3000",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ----------------- Request Models -----------------
class SourceItemConfig(BaseModel):
    file_path: str
    sheet_name: Optional[str] = None
    header_row: int = 0

class InitDatasetRequest(BaseModel):
    session_id: str
    sources: List[SourceItemConfig]
    type_overrides: Optional[Dict[str, str]] = None

class CleaningActionRequest(BaseModel):
    session_id: str
    action: str
    params: Dict[str, Any] = {}

class FilterCondition(BaseModel):
    column: str
    operator: str
    value: Any = None
    value2: Any = None

class ApplyFilterRequest(BaseModel):
    session_id: str
    conditions: List[FilterCondition]
    logic: str = "AND"

class PivotRequest(BaseModel):
    session_id: str
    rows: List[str] = []
    cols: List[str] = []
    values: List[str] = []
    agg_func: str = "sum"
    filters: Optional[List[Dict[str, Any]]] = None
    sort_order: str = "desc"

class DrillDownRequest(BaseModel):
    session_id: str
    row_filters: Dict[str, Any]
    limit: int = 50

# ----------------- Endpoints -----------------
@app.get("/api/health")
def health_check():
    return {"status": "ok", "app": "FLOWER HAPPY", "version": "1.0.0"}

@app.post("/api/session/new")
def create_new_session():
    session = session_manager.get_or_create()
    return {"session_id": session.session_id}

@app.get("/api/session/{session_id}/status")
def get_session_status(session_id: str):
    session = session_manager.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Không tìm thấy phiên làm việc.")
    
    has_dataset = session.current_df is not None
    return {
        "session_id": session.session_id,
        "has_dataset": has_dataset,
        "total_rows": len(session.current_df) if has_dataset else 0,
        "total_cols": len(session.current_df.columns) if has_dataset else 0,
        "history_count": len(session.history),
        "files_count": len(session.files)
    }

# ----------------- Page 1: Kết nối (Connect) -----------------
@app.post("/api/upload")
async def upload_files(
    session_id: Optional[str] = Form(None),
    files: List[UploadFile] = File(...)
):
    session = session_manager.get_or_create(session_id)
    session_upload_dir = UPLOAD_PATH / session.session_id
    session_upload_dir.mkdir(parents=True, exist_ok=True)

    inspected_files = []

    for file in files:
        file_path = session_upload_dir / file.filename
        # Save file to disk
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Validate file
        is_valid, error_msg = validate_uploaded_file(file_path, MAX_UPLOAD_SIZE_BYTES)
        if not is_valid:
            if file_path.exists():
                file_path.unlink()
            raise HTTPException(status_code=400, detail=error_msg)

        # Inspect file
        try:
            info = inspect_file(file_path, header_row=0)
            info["file_path"] = str(file_path)
            session.files.append(info)
            inspected_files.append(info)
        except Exception as e:
            if file_path.exists():
                file_path.unlink()
            raise HTTPException(status_code=400, detail=str(e))

    return {
        "session_id": session.session_id,
        "files": inspected_files
    }

@app.post("/api/dataset/initialize")
def initialize_dataset(req: InitDatasetRequest):
    session = session_manager.get(req.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Phiên làm việc không tồn tại.")

    sources_dict = [s.model_dump() for s in req.sources]
    try:
        combined_df, metadata = load_and_combine_sources(sources_dict, req.type_overrides)
        session.set_dataset(combined_df, metadata)
        
        # Initial profile
        prof = profile_dataset(combined_df)
        
        return {
            "status": "success",
            "message": "Nạp dữ liệu hợp nhất thành công.",
            "total_rows": len(combined_df),
            "total_columns": len(combined_df.columns),
            "columns": list(combined_df.columns),
            "quality_score": prof["quality_score"],
            "metadata": metadata
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=400, detail=f"Lỗi khởi tạo tập dữ liệu: {str(e)}")

# ----------------- Page 2: Làm sạch (Clean) -----------------
@app.get("/api/cleaning/profile")
def get_cleaning_profile(session_id: str):
    session = session_manager.get(session_id)
    if not session or session.current_df is None:
        raise HTTPException(status_code=404, detail="Chưa có dữ liệu trong phiên làm việc.")

    prof = profile_dataset(session.current_df)
    col_types = get_columns_by_type(session.current_df)

    return {
        "profile": prof,
        "col_types": col_types,
        "history": [
            {
                "action_name": h["action_name"],
                "params": h["params"],
                "before_stats": h["before_stats"],
                "after_stats": h["after_stats"],
                "timestamp": h["timestamp"]
            }
            for h in session.history
        ]
    }

@app.get("/api/cleaning/preview")
def get_cleaning_preview(
    session_id: str,
    page: int = Query(1, ge=1),
    limit: int = Query(25, ge=1, le=100)
):
    session = session_manager.get(session_id)
    if not session or session.current_df is None:
        raise HTTPException(status_code=404, detail="Chưa có dữ liệu.")

    df = session.current_df
    total_rows = len(df)
    start_idx = (page - 1) * limit
    end_idx = min(start_idx + limit, total_rows)

    sub_df = df.iloc[start_idx:end_idx]
    # Replace NaNs with None for valid JSON
    records = sub_df.replace({float('nan'): None}).to_dict(orient="records")

    return {
        "total_rows": total_rows,
        "total_columns": len(df.columns),
        "columns": list(df.columns),
        "page": page,
        "limit": limit,
        "records": records
    }

@app.post("/api/cleaning/action")
def execute_cleaning_action(req: CleaningActionRequest):
    session = session_manager.get(req.session_id)
    if not session or session.current_df is None:
        raise HTTPException(status_code=404, detail="Chưa có dữ liệu.")

    try:
        new_df, before_stats, after_stats = apply_cleaning_action(
            session.current_df, req.action, req.params
        )
        session.push_transformation(req.action, req.params, before_stats, after_stats, new_df)
        
        prof = profile_dataset(new_df)
        return {
            "status": "success",
            "before_stats": before_stats,
            "after_stats": after_stats,
            "quality_score": prof["quality_score"],
            "profile": prof
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Không thể áp dụng thao tác làm sạch: {str(e)}")

@app.post("/api/cleaning/filter")
def execute_filter(req: ApplyFilterRequest):
    session = session_manager.get(req.session_id)
    if not session or session.current_df is None:
        raise HTTPException(status_code=404, detail="Chưa có dữ liệu.")

    try:
        conds = [c.model_dump() for c in req.conditions]
        filtered_df = filter_dataframe(session.current_df, conds, req.logic)
        
        before_stats = {"rows": len(session.current_df), "columns": len(session.current_df.columns)}
        after_stats = {"rows": len(filtered_df), "columns": len(filtered_df.columns)}
        
        session.push_transformation("apply_filter", {"conditions": conds, "logic": req.logic}, before_stats, after_stats, filtered_df)
        prof = profile_dataset(filtered_df)
        return {
            "status": "success",
            "before_stats": before_stats,
            "after_stats": after_stats,
            "profile": prof
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Lỗi áp dụng bộ lọc: {str(e)}")

@app.post("/api/cleaning/undo")
def undo_cleaning(session_id: str = Form(...)):
    session = session_manager.get(session_id)
    if not session or session.current_df is None:
        raise HTTPException(status_code=404, detail="Chưa có dữ liệu.")

    res = session.undo_transformation()
    if not res:
        raise HTTPException(status_code=400, detail="Không có thao tác nào để hoàn tác.")

    prof = profile_dataset(session.current_df)
    return {
        "status": "success",
        "message": "Đã hoàn tác thao tác gần nhất.",
        "quality_score": prof["quality_score"],
        "profile": prof
    }

@app.post("/api/cleaning/reset")
def reset_cleaning(session_id: str = Form(...)):
    session = session_manager.get(session_id)
    if not session or session.raw_df is None:
        raise HTTPException(status_code=404, detail="Chưa có dữ liệu gốc.")

    session.reset_to_raw()
    prof = profile_dataset(session.current_df)
    return {
        "status": "success",
        "message": "Đã đặt lại dữ liệu về trạng thái ban đầu.",
        "quality_score": prof["quality_score"],
        "profile": prof
    }

# ----------------- Page 3: Phân tích (Analyze) -----------------
@app.get("/api/analyze/overview")
def analyze_overview(session_id: str):
    session = session_manager.get(session_id)
    if not session or session.current_df is None:
        raise HTTPException(status_code=404, detail="Chưa có dữ liệu.")

    df = session.current_df
    col_types = get_columns_by_type(df)
    summary = get_summary_statistics(df)
    correlations = get_correlation_matrix(df)

    return {
        "total_rows": len(df),
        "total_columns": len(df.columns),
        "col_types": col_types,
        "summary": summary,
        "correlations": correlations
    }

@app.get("/api/analyze/distribution")
def analyze_distribution(session_id: str, column: str, bins: int = 10):
    session = session_manager.get(session_id)
    if not session or session.current_df is None:
        raise HTTPException(status_code=404, detail="Chưa có dữ liệu.")

    return get_distributions(session.current_df, column, bins)

@app.post("/api/analyze/pivot")
def analyze_pivot(req: PivotRequest):
    session = session_manager.get(req.session_id)
    if not session or session.current_df is None:
        raise HTTPException(status_code=404, detail="Chưa có dữ liệu.")

    return compute_pivot_data(
        df=session.current_df,
        rows=req.rows,
        cols=req.cols,
        values=req.values,
        agg_func=req.agg_func,
        filters=req.filters,
        sort_order=req.sort_order
    )

@app.post("/api/analyze/drilldown")
def analyze_drilldown(req: DrillDownRequest):
    session = session_manager.get(req.session_id)
    if not session or session.current_df is None:
        raise HTTPException(status_code=404, detail="Chưa có dữ liệu.")

    records = drill_down_records(session.current_df, req.row_filters, req.limit)
    return {
        "count": len(records),
        "records": records
    }

# ----------------- Page 4: Báo cáo (Report) -----------------
@app.get("/api/report/generate")
def report_generate(session_id: str):
    session = session_manager.get(session_id)
    if not session or session.current_df is None:
        raise HTTPException(status_code=404, detail="Chưa có dữ liệu.")

    return generate_insights_and_report(session.current_df)

@app.get("/api/report/export/excel")
def report_export_excel(session_id: str):
    session = session_manager.get(session_id)
    if not session or session.current_df is None:
        raise HTTPException(status_code=404, detail="Chưa có dữ liệu.")

    report_data = generate_insights_and_report(session.current_df)
    excel_stream = export_report_excel(session.current_df, report_data)

    headers = {
        'Content-Disposition': 'attachment; filename="FLOWER_HAPPY_Bao_Cao.xlsx"'
    }
    return StreamingResponse(
        excel_stream,
        media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        headers=headers
    )

@app.get("/api/report/export/pdf")
def report_export_pdf(session_id: str):
    session = session_manager.get(session_id)
    if not session or session.current_df is None:
        raise HTTPException(status_code=404, detail="Chưa có dữ liệu.")

    report_data = generate_insights_and_report(session.current_df)
    pdf_stream = export_report_pdf(session.current_df, report_data)

    headers = {
        'Content-Disposition': 'attachment; filename="FLOWER_HAPPY_Bao_Cao.pdf"'
    }
    return StreamingResponse(
        pdf_stream,
        media_type='application/pdf',
        headers=headers
    )
