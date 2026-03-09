# backend/routes/query.py
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
import json

from llm_engine import generate_sql, generate_visualization, retry_sql
from utils.database import execute_sql, get_schema
from utils.rag_store import rag_store, summarize_dataframe

router = APIRouter()


class QueryRequest(BaseModel):
    query: str
    session_id: Optional[str] = None
    conversation_history: Optional[list] = None
    previous_sql: Optional[str] = None
    db_path: Optional[str] = None
    schema_override: Optional[str] = None


class QueryResponse(BaseModel):
    sql: Optional[str] = None
    data: Optional[list] = None
    columns: Optional[list] = None
    visualization: Optional[dict] = None
    error: Optional[str] = None
    row_count: int = 0


@router.post("/query", response_model=QueryResponse)
async def run_query(req: QueryRequest):
    """Process a natural language query and return SQL + data + chart config."""

    # 1. Generate SQL from natural language (RAG context injected automatically)
    sql, error_or_model = generate_sql(
        user_query=req.query,
        schema_override=req.schema_override,
        conversation_history=req.conversation_history,
        previous_sql=req.previous_sql,
        session_id=req.session_id,
    )

    if not sql:
        if error_or_model and "API key" in str(error_or_model):
            return QueryResponse(error="API key not configured. Set OPENROUTER_API_KEY in .env.")
        elif error_or_model and "cannot answer" in str(error_or_model).lower():
            return QueryResponse(error="Cannot answer this question with the available data.")
        else:
            return QueryResponse(error=str(error_or_model or "Unknown error generating SQL."))

    # 2. Execute SQL
    target_db = req.db_path
    df, exec_error = execute_sql(sql, db_path=target_db)

    # 3. Retry on error
    if exec_error:
        corrected_sql, _ = retry_sql(sql, exec_error, req.query, schema_override=req.schema_override)
        if corrected_sql:
            df, exec_error = execute_sql(corrected_sql, db_path=target_db)
            if not exec_error:
                sql = corrected_sql

    if exec_error:
        return QueryResponse(sql=sql, error=f"SQL execution failed: {exec_error}")

    if df is None or df.empty:
        return QueryResponse(sql=sql, error="Query returned no results.", row_count=0)

    # 4. Generate visualization config
    vis_config = generate_visualization(req.query, df)

    # 5. Persist successful interaction in RAG store for future context enrichment
    rag_store.store_interaction(
        query=req.query,
        sql=sql,
        df_summary=summarize_dataframe(df),
        session_id=req.session_id or "default",
    )

    return QueryResponse(
        sql=sql,
        data=df.to_dict(orient="records"),
        columns=list(df.columns),
        visualization=vis_config,
        row_count=len(df),
    )


@router.get("/schema")
async def get_current_schema():
    """Return the current database schema."""
    schema = get_schema()
    return {"schema": schema}
