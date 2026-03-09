import uuid
from threading import Lock


class Session:
    def __init__(self):
        self.history: list[dict] = []
        self.using_uploaded: bool = False
        self.uploaded_schema: str | None = None
        self.uploaded_db_path: str | None = None
        self.last_sql: str | None = None


class SessionStore:
    """Thread-safe in-memory session store for conversation tracking."""

    def __init__(self):
        self._sessions: dict[str, Session] = {}
        self._lock = Lock()

    def create(self) -> str:
        session_id = uuid.uuid4().hex
        with self._lock:
            self._sessions[session_id] = Session()
        return session_id

    def get(self, session_id: str) -> Session | None:
        with self._lock:
            return self._sessions.get(session_id)

    def get_or_create(self, session_id: str) -> Session:
        with self._lock:
            if session_id not in self._sessions:
                self._sessions[session_id] = Session()
            return self._sessions[session_id]

    def delete(self, session_id: str) -> bool:
        with self._lock:
            if session_id in self._sessions:
                del self._sessions[session_id]
                return True
            return False


sessions = SessionStore()
