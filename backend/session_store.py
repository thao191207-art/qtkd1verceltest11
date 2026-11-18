import time
import uuid
import threading
from typing import Dict, Any, Optional, List
import pandas as pd
from backend.config import SESSION_CLEANUP_TTL_SECONDS

class Session:
    def __init__(self, session_id: str):
        self.session_id: str = session_id
        self.files: List[Dict[str, Any]] = []
        self.config: Dict[str, Any] = {}
        self.raw_df: Optional[pd.DataFrame] = None
        self.current_df: Optional[pd.DataFrame] = None
        self.history: List[Dict[str, Any]] = [] # list of {action_name, params, before_stats, after_stats, df_snapshot}
        self.created_at: float = time.time()
        self.last_activity: float = time.time()

    def touch(self):
        self.last_activity = time.time()

    def set_dataset(self, df: pd.DataFrame, source_info: Dict[str, Any]):
        self.raw_df = df.copy()
        self.current_df = df.copy()
        self.history = []
        self.config = source_info
        self.touch()

    def push_transformation(self, action_name: str, params: Dict[str, Any], before_stats: Dict[str, Any], after_stats: Dict[str, Any], new_df: pd.DataFrame):
        # Save snapshot of previous state to allow undo
        self.history.append({
            "action_name": action_name,
            "params": params,
            "before_stats": before_stats,
            "after_stats": after_stats,
            "df_snapshot": self.current_df.copy() if self.current_df is not None else None,
            "timestamp": time.time()
        })
        self.current_df = new_df.copy()
        self.touch()

    def undo_transformation(self) -> Optional[Dict[str, Any]]:
        if not self.history:
            return None
        last_step = self.history.pop()
        if last_step["df_snapshot"] is not None:
            self.current_df = last_step["df_snapshot"]
        self.touch()
        return {
            "reverted_action": last_step["action_name"],
            "remaining_history_length": len(self.history)
        }

    def reset_to_raw(self):
        if self.raw_df is not None:
            self.current_df = self.raw_df.copy()
            self.history = []
            self.touch()

class SessionManager:
    def __init__(self):
        self._sessions: Dict[str, Session] = {}
        self._lock = threading.Lock()

    def get_or_create(self, session_id: Optional[str] = None) -> Session:
        with self._lock:
            self._cleanup_expired()
            if not session_id or session_id not in self._sessions:
                new_id = session_id or str(uuid.uuid4())
                session = Session(new_id)
                self._sessions[new_id] = session
                return session
            session = self._sessions[session_id]
            session.touch()
            return session

    def get(self, session_id: str) -> Optional[Session]:
        with self._lock:
            self._cleanup_expired()
            session = self._sessions.get(session_id)
            if session:
                session.touch()
            return session

    def _cleanup_expired(self):
        now = time.time()
        expired_keys = [
            sid for sid, sess in self._sessions.items()
            if (now - sess.last_activity) > SESSION_CLEANUP_TTL_SECONDS
        ]
        for sid in expired_keys:
            del self._sessions[sid]

session_manager = SessionManager()
