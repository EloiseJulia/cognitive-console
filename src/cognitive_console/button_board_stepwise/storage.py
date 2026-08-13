"""Durable persistence for the public deployment of the V11 stepwise study.

The loopback owner-preview keeps its volatile in-memory behaviour untouched:
persistence is only attached in public deployment mode. A free Render web
instance spins down when idle and loses all in-memory state, so every signed
export must be written to an external store (Postgres) the moment it is
produced, and the owner downloads them through a token-guarded admin endpoint.

Only signed exports are stored. Signed exports never contain expected answers,
scoring keys, or any private derivation field (that invariant is enforced by
the server's export construction), so this layer stores nothing private.
"""

from __future__ import annotations

import json
import threading
from typing import Any, Protocol


class ExportStore(Protocol):
    """Idempotent, attempt-keyed store of signed exports."""

    def save_attempt(
        self,
        attempt_id: str,
        *,
        run_id: str,
        completion_status: str,
        complete: bool,
        signed_export: dict[str, Any],
    ) -> None:
        ...

    def all_attempts(self) -> list[dict[str, Any]]:
        ...


def _clone(value: dict[str, Any]) -> dict[str, Any]:
    return json.loads(json.dumps(value, ensure_ascii=False))


class InMemoryExportStore:
    """Thread-safe in-process store, used for tests and local verification."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._rows: dict[str, dict[str, Any]] = {}

    def save_attempt(
        self,
        attempt_id: str,
        *,
        run_id: str,
        completion_status: str,
        complete: bool,
        signed_export: dict[str, Any],
    ) -> None:
        if not isinstance(attempt_id, str) or not attempt_id:
            raise ValueError("attempt_id must be a non-empty string")
        with self._lock:
            self._rows[attempt_id] = {
                "attempt_id": attempt_id,
                "run_id": run_id,
                "completion_status": completion_status,
                "complete": complete,
                "signed_export": _clone(signed_export),
            }

    def all_attempts(self) -> list[dict[str, Any]]:
        with self._lock:
            return [_clone(row) for row in self._rows.values()]


_SCHEMA = """
CREATE TABLE IF NOT EXISTS stepwise_attempts (
    attempt_id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL,
    completion_status TEXT NOT NULL,
    complete BOOLEAN NOT NULL,
    signed_export_json TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
)
"""

_UPSERT = """
INSERT INTO stepwise_attempts
    (attempt_id, run_id, completion_status, complete, signed_export_json, updated_at)
VALUES (%s, %s, %s, %s, %s, now())
ON CONFLICT (attempt_id) DO UPDATE SET
    run_id = EXCLUDED.run_id,
    completion_status = EXCLUDED.completion_status,
    complete = EXCLUDED.complete,
    signed_export_json = EXCLUDED.signed_export_json,
    updated_at = now()
"""

_SELECT_ALL = """
SELECT attempt_id, run_id, completion_status, complete, signed_export_json
FROM stepwise_attempts
ORDER BY created_at, attempt_id
"""


class PostgresExportStore:
    """Postgres-backed store for public deployment (Render free Postgres)."""

    def __init__(self, dsn: str) -> None:
        try:
            import psycopg  # noqa: F401  (lazy: optional deploy dependency)
        except ModuleNotFoundError as exc:  # pragma: no cover - env dependent
            raise RuntimeError(
                "PostgresExportStore requires the 'deploy' extra: "
                "pip install -e .[deploy]"
            ) from exc
        self._psycopg = psycopg
        self._dsn = dsn
        self._lock = threading.RLock()
        self._init_schema()

    def _connect(self) -> Any:
        return self._psycopg.connect(self._dsn, autocommit=True)

    def _init_schema(self) -> None:
        with self._lock, self._connect() as conn:
            conn.execute(_SCHEMA)

    def save_attempt(
        self,
        attempt_id: str,
        *,
        run_id: str,
        completion_status: str,
        complete: bool,
        signed_export: dict[str, Any],
    ) -> None:
        if not isinstance(attempt_id, str) or not attempt_id:
            raise ValueError("attempt_id must be a non-empty string")
        payload = json.dumps(signed_export, ensure_ascii=False)
        with self._lock, self._connect() as conn:
            conn.execute(
                _UPSERT,
                (attempt_id, run_id, completion_status, bool(complete), payload),
            )

    def all_attempts(self) -> list[dict[str, Any]]:
        with self._lock, self._connect() as conn:
            rows = conn.execute(_SELECT_ALL).fetchall()
        result = []
        for attempt_id, run_id, completion_status, complete, payload in rows:
            result.append(
                {
                    "attempt_id": attempt_id,
                    "run_id": run_id,
                    "completion_status": completion_status,
                    "complete": bool(complete),
                    "signed_export": json.loads(payload),
                }
            )
        return result


def create_store(database_url: str | None) -> ExportStore | None:
    """Return a Postgres store when a URL is configured, else None (volatile)."""

    if not database_url:
        return None
    return PostgresExportStore(database_url)


__all__ = [
    "ExportStore",
    "InMemoryExportStore",
    "PostgresExportStore",
    "create_store",
]
