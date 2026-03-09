# routes.py
import io
import logging

from fastapi import APIRouter, HTTPException, UploadFile, File
from fastapi.responses import JSONResponse

from schemas import QueryRequest, QueryResponse, UploadResponse, SessionInfo, HealthResponse
from session_store import sessions
from llm_engine import generate_sql, generate_visualization, retry_sql, MODEL_NAME, client
from utils.database import (
    csv_to_sqlite,
    execute_sql,
    upload_csv_to_sqlite,
    get_uploaded_schema,
    DB_PATH,
)
from utils.rag_store import rag_store, summarize_dataframe

logger = logging.getLogger(__name__)

router = APIRouter()


# ── Health ───────────────────────────────────────────────────────────────────

@router.get("/health", response_model=HealthResponse)
def health_check():
    """Check API and database readiness."""
    db_file = DB_PATH.replace("sqlite:///", "")
    import os
    return HealthResponse(
        status="ok",
        default_db_ready=os.path.exists(db_file),
        model=MODEL_NAME,
    )


# ── Sessions ─────────────────────────────────────────────────────────────────

@router.post("/sessions", response_model=SessionInfo)
def create_session():
    """Create a new conversation session."""
    sid = sessions.create()
    session = sessions.get(sid)
    return SessionInfo(
        session_id=sid,
        using_uploaded=session.using_uploaded,
        message_count=len(session.history),
        dataset="default",
    )


@router.get("/sessions/{session_id}", response_model=SessionInfo)
def get_session(session_id: str):
    """Get session info."""
    session = sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return SessionInfo(
        session_id=session_id,
        using_uploaded=session.using_uploaded,
        message_count=len(session.history),
        dataset="uploaded" if session.using_uploaded else "default",
    )


@router.delete("/sessions/{session_id}")
def delete_session(session_id: str):
    """Delete a session and its conversation history."""
    if not sessions.delete(session_id):
        raise HTTPException(status_code=404, detail="Session not found")
    return {"detail": "Session deleted"}


@router.get("/sessions/{session_id}/history")
def get_history(session_id: str):
    """Return the full conversation history for a session."""
    session = sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session.history


# ── Query ────────────────────────────────────────────────────────────────────

@router.post("/query", response_model=QueryResponse)
def run_query(req: QueryRequest):
    """
    Accept a natural language question, generate SQL, execute it,
    and return data + visualization config.
    """
    session = sessions.get_or_create(req.session_id)

    # Append user message to history
    session.history.append({"role": "user", "content": req.query})

    # Determine active schema / db
    active_schema = session.uploaded_schema if session.using_uploaded else None
    active_db = session.uploaded_db_path if session.using_uploaded else None

    conversation_history = session.history if len(session.history) > 1 else None
    previous_sql = session.last_sql

    # 1) Generate SQL (with RAG context injected for first questions)
    sql, error_or_model = generate_sql(
        user_query=req.query,
        schema_override=active_schema,
        conversation_history=conversation_history,
        previous_sql=previous_sql,
        session_id=req.session_id,
    )

    if not sql:
        if error_or_model and "API key" in str(error_or_model):
            msg = "API key not configured. Please set OPENROUTER_API_KEY in the .env file."
        elif error_or_model and "cannot answer" in str(error_or_model).lower():
            msg = "The requested information is not available in the current dataset schema."
        else:
            msg = f"Failed to generate query: {error_or_model or 'Unknown error'}"
        session.history.append({"role": "assistant", "text": msg})
        return QueryResponse(error=msg)

    # 2) Execute SQL
    df, error = execute_sql(sql, db_path=active_db)

    if error:
        corrected_sql, _ = retry_sql(sql, error, req.query, schema_override=active_schema)
        if corrected_sql:
            df, error = execute_sql(corrected_sql, db_path=active_db)
            if not error:
                sql = corrected_sql

    if error:
        msg = "System encountered an exception during data retrieval."
        session.history.append({"role": "assistant", "text": msg, "sql": sql})
        return QueryResponse(sql=sql, error=msg)

    if df is None or df.empty:
        msg = "The query returned zero records."
        session.history.append({"role": "assistant", "text": msg, "sql": sql})
        return QueryResponse(sql=sql, error=msg, data=[], columns=[], row_count=0)

    # 3) Visualization config
    vis_config = generate_visualization(req.query, df)

    session.last_sql = sql
    data_records = df.to_dict(orient="records")

    # 4) Persist successful interaction in the RAG store for future context
    rag_store.store_interaction(
        query=req.query,
        sql=sql,
        df_summary=summarize_dataframe(df),
        session_id=req.session_id or "default",
    )

    session.history.append({
        "role": "assistant",
        "text": "",
        "sql": sql,
        "df": data_records,
        "vis_config": vis_config,
        "query": req.query,
    })

    return QueryResponse(
        sql=sql,
        data=data_records,
        columns=list(df.columns),
        vis_config=vis_config,
        row_count=len(df),
    )


# ── CSV Upload ───────────────────────────────────────────────────────────────

@router.post("/upload", response_model=UploadResponse)
def upload_csv(session_id: str, file: UploadFile = File(...)):
    """Upload a CSV file and bind it to a session."""
    session = sessions.get_or_create(session_id)

    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are supported")

    contents = file.file.read()
    buf = io.BytesIO(contents)

    db_path, df, table_name = upload_csv_to_sqlite(buf)
    if db_path is None or df is None:
        raise HTTPException(status_code=422, detail="Failed to process the uploaded CSV")

    session.using_uploaded = True
    session.uploaded_db_path = db_path
    session.uploaded_schema = get_uploaded_schema(df, table_name)
    session.history = []
    session.last_sql = None

    return UploadResponse(
        session_id=session_id,
        table_name=table_name,
        schema_description=session.uploaded_schema,
        row_count=len(df),
        column_count=len(df.columns),
    )


@router.post("/sessions/{session_id}/revert")
def revert_to_default(session_id: str):
    """Revert a session back to the default insurance dataset."""
    session = sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    session.using_uploaded = False
    session.uploaded_schema = None
    session.uploaded_db_path = None
    session.history = []
    session.last_sql = None
    return {"detail": "Reverted to default dataset"}
