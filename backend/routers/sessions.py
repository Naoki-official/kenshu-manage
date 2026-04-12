# backend/routers/sessions.py
from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from constants import (
    COL_MANAGEMENT_NUMBER,
    FIELD_COMMENT,
    FIELD_CHECKED,
    FIELD_UPDATED_AT,
)
from database import get_db

router = APIRouter()


class CommentUpdate(BaseModel):
    comment: str


@router.get("/sessions")
def list_sessions(db: sqlite3.Connection = Depends(get_db)):
    """全セッション一覧を返す（タブ表示用）。"""
    cursor = db.cursor()
    
    # sessions を uploaded_at の昇順で全件取得
    cursor.execute("SELECT id, month, uploaded_at, round FROM sessions ORDER BY uploaded_at ASC")
    sessions = cursor.fetchall()
    
    result = []
    for sess in sessions:
        # そのセッションに紐づく行数をカウント
        cursor.execute("SELECT COUNT(*) as cnt FROM records WHERE session_id = ?", (sess["id"],))
        row_count = cursor.fetchone()["cnt"]
        
        result.append({
            "id": sess["id"],
            "month": sess["month"],
            "uploaded_at": sess["uploaded_at"],
            "round": sess["round"],
            "row_count": row_count,
        })
    return result


@router.get("/sessions/{session_id}")
def get_session(session_id: str, db: sqlite3.Connection = Depends(get_db)):
    """特定セッションのデータを返す。"""
    cursor = db.cursor()
    cursor.execute("SELECT id, month, uploaded_at, round FROM sessions WHERE id = ?", (session_id,))
    sess = cursor.fetchone()
    if not sess:
        raise HTTPException(status_code=404, detail="セッションが見つかりません。")
        
    cursor.execute("""
        SELECT management_number, comment, checked, updated_at, data 
        FROM records WHERE session_id = ?
    """, (session_id,))
    records = cursor.fetchall()
    
    # 互換性のため、元のCSVとしての辞書形式に復元する
    rows = []
    for r in records:
        try:
            row_data = json.loads(r["data"])
        except Exception:
            row_data = {}
            
        row_data[COL_MANAGEMENT_NUMBER] = r["management_number"]
        row_data[FIELD_COMMENT] = r["comment"]
        row_data[FIELD_CHECKED] = bool(r["checked"])
        row_data[FIELD_UPDATED_AT] = r["updated_at"]
        rows.append(row_data)
        
    return {
        "id": sess["id"],
        "month": sess["month"],
        "uploaded_at": sess["uploaded_at"],
        "round": sess["round"],
        "rows": rows,
    }


@router.patch("/sessions/{session_id}/rows/{management_number}")
def update_comment(
    session_id: str, 
    management_number: str, 
    body: CommentUpdate, 
    db: sqlite3.Connection = Depends(get_db)
):
    """指定行のコメントを更新する。"""
    cursor = db.cursor()
    
    # 存在確認
    cursor.execute("""
        SELECT management_number, data
        FROM records
        WHERE session_id = ? AND management_number = ?
    """, (session_id, management_number))
    record = cursor.fetchone()
    
    if not record:
        raise HTTPException(
            status_code=404,
            detail=f"{COL_MANAGEMENT_NUMBER} '{management_number}' が見つかりません。",
        )
        
    comment = body.comment
    checked = 1 if body.comment else 0
    updated_at = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    cursor.execute("""
        UPDATE records 
        SET comment = ?, checked = ?, updated_at = ?
        WHERE session_id = ? AND management_number = ?
    """, (comment, checked, updated_at, session_id, management_number))
    db.commit()
    
    # 返却用に整形
    try:
        row_data = json.loads(record["data"])
    except Exception:
        row_data = {}
        
    row_data[COL_MANAGEMENT_NUMBER] = management_number
    row_data[FIELD_COMMENT] = comment
    row_data[FIELD_CHECKED] = bool(checked)
    row_data[FIELD_UPDATED_AT] = updated_at
    
    return row_data
