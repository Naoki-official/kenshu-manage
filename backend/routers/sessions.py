# backend/routers/sessions.py
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from constants import (
    COL_MANAGEMENT_NUMBER,
    FIELD_COMMENT,
    FIELD_CHECKED,
    FIELD_UPDATED_AT,
)

router = APIRouter()
DATA_DIR = Path(__file__).parent.parent / "data"


class CommentUpdate(BaseModel):
    comment: str


def _get_all_month_files() -> list[Path]:
    """data/ 配下の全JSONファイルをソート済みで返す。"""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    files = sorted(DATA_DIR.glob("*.json"))
    return files


def _load_json(filepath: Path) -> dict:
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


def _save_json(filepath: Path, data: dict) -> None:
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


@router.get("/sessions")
def list_sessions():
    """全セッション一覧を返す（タブ表示用）。"""
    result = []
    for fp in _get_all_month_files():
        data = _load_json(fp)
        for sess in data.get("sessions", []):
            result.append({
                "id": sess["id"],
                "month": data["month"],
                "uploaded_at": sess["uploaded_at"],
                "round": sess["round"],
                "row_count": len(sess.get("rows", [])),
            })
    return result


@router.get("/sessions/{session_id}")
def get_session(session_id: str):
    """特定セッションのデータを返す。"""
    for fp in _get_all_month_files():
        data = _load_json(fp)
        for sess in data.get("sessions", []):
            if sess["id"] == session_id:
                return sess
    raise HTTPException(status_code=404, detail="セッションが見つかりません。")


@router.patch("/sessions/{session_id}/rows/{management_number}")
def update_comment(session_id: str, management_number: str, body: CommentUpdate):
    """指定行のコメントを更新する。"""
    for fp in _get_all_month_files():
        data = _load_json(fp)
        for sess in data.get("sessions", []):
            if sess["id"] == session_id:
                for row in sess.get("rows", []):
                    if row.get(COL_MANAGEMENT_NUMBER) == management_number:
                        row[FIELD_COMMENT] = body.comment
                        row[FIELD_CHECKED] = bool(body.comment)
                        row[FIELD_UPDATED_AT] = datetime.now().strftime(
                            "%Y-%m-%d %H:%M"
                        )
                        _save_json(fp, data)
                        return row
                raise HTTPException(
                    status_code=404,
                    detail=f"{COL_MANAGEMENT_NUMBER} '{management_number}' が見つかりません。",
                )
    raise HTTPException(status_code=404, detail="セッションが見つかりません。")
