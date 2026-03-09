# backend/routes/upload.py
import os
import sys
from fastapi import APIRouter, UploadFile, File
from io import BytesIO

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, PROJECT_ROOT)

from utils.database import upload_csv_to_sqlite, get_uploaded_schema, csv_to_sqlite

router = APIRouter()

# In-memory state for uploaded data
_upload_state = {
    "active": False,
    "db_path": None,
    "schema": None,
    "table_name": None,
    "row_count": 0,
    "col_count": 0,
}


@router.post("/upload")
async def upload_csv(file: UploadFile = File(...)):
    """Upload a CSV file and create a temporary SQLite database."""
    try:
        contents = await file.read()
        file_like = BytesIO(contents)

        db_path, df, table_name = upload_csv_to_sqlite(file_like)

        if db_path and df is not None:
            schema = get_uploaded_schema(df, table_name)
            _upload_state.update({
                "active": True,
                "db_path": db_path,
                "schema": schema,
                "table_name": table_name,
                "row_count": len(df),
                "col_count": len(df.columns),
            })
            return {
                "success": True,
                "message": f"Uploaded {len(df)} rows, {len(df.columns)} columns.",
                "schema": schema,
                "db_path": db_path,
                "table_name": table_name,
                "row_count": len(df),
                "col_count": len(df.columns),
            }
        else:
            return {"success": False, "message": "Failed to process CSV file."}
    except Exception as e:
        return {"success": False, "message": str(e)}


@router.post("/reset")
async def reset_to_default():
    """Reset to the default insurance dataset."""
    _upload_state.update({
        "active": False,
        "db_path": None,
        "schema": None,
        "table_name": None,
        "row_count": 0,
        "col_count": 0,
    })
    return {"success": True, "message": "Reverted to default dataset."}


@router.get("/upload/status")
async def get_upload_status():
    """Get current upload status."""
    return _upload_state
