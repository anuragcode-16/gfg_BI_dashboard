from pydantic import BaseModel, Field
from typing import Optional


class QueryRequest(BaseModel):
    query: str = Field(..., description="Natural language question about the data")
    session_id: str = Field(..., description="Session ID for conversation tracking")


class QueryResponse(BaseModel):
    sql: Optional[str] = None
    data: Optional[list[dict]] = None
    columns: Optional[list[str]] = None
    vis_config: Optional[dict] = None
    error: Optional[str] = None
    row_count: int = 0


class UploadResponse(BaseModel):
    session_id: str
    table_name: str
    schema_description: str
    row_count: int
    column_count: int


class SessionInfo(BaseModel):
    session_id: str
    using_uploaded: bool
    message_count: int
    dataset: str


class HealthResponse(BaseModel):
    status: str
    default_db_ready: bool
    model: str
