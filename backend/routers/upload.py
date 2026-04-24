# backend/routers/upload.py
from __future__ import annotations

import csv
import io
import json
import sqlite3
from datetime import datetime
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends

from constants import (
    COL_MANAGEMENT_NUMBER,
    FIELD_COMMENT,
    FIELD_CHECKED,
    FIELD_UPDATED_AT,
    NEXT_MONTH_THRESHOLD,
)
from database import get_db

router = APIRouter()

def _parse_csv(raw_bytes: bytes) -> list[dict]:
    """cp932でCSVをパースし、辞書のリストとして返す。"""
    try:
        text = raw_bytes.decode("cp932")
    except UnicodeDecodeError:
        try:
            text = raw_bytes.decode("utf-8-sig")
        except UnicodeDecodeError:
            text = raw_bytes.decode("utf-8")

    reader = csv.DictReader(io.StringIO(text))
    rows = []
    for row in reader:
        # 空行スキップ
        if all(v.strip() == "" for v in row.values()):
            continue
        cleaned = {}
        for k, v in row.items():
            if k is None:
                continue
            cleaned[k.strip()] = v.strip() if v else ""
        rows.append(cleaned)
    return rows


@router.post("/upload")
async def upload_csv(file: UploadFile = File(...), db: sqlite3.Connection = Depends(get_db)):
    """CSVをアップロードし、新セッションを生成する。"""
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="CSVファイルを選択してください。")

    raw = await file.read()
    if len(raw) == 0:
        raise HTTPException(status_code=400, detail="ファイルが空です。")

    try:
        rows = _parse_csv(raw)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"CSVの解析に失敗しました: {str(e)}")

    if len(rows) == 0:
        raise HTTPException(status_code=400, detail="CSVにデータ行がありません。")

    # キー列の存在チェック
    first_row_keys = list(rows[0].keys())
    if COL_MANAGEMENT_NUMBER not in first_row_keys:
        raise HTTPException(
            status_code=400,
            detail=f"CSVに「{COL_MANAGEMENT_NUMBER}」列が見つかりません。",
        )

    now = datetime.now()
    if now.day <= NEXT_MONTH_THRESHOLD:
        if now.month == 1:
            month_key = f"{now.year - 1}-12"
        else:
            month_key = f"{now.year}-{now.month - 1:02d}"
    else:
        month_key = now.strftime("%Y-%m")
    session_id = now.strftime("%Y%m%d_%H%M%S")

    cursor = db.cursor()
    
    # 既存の最新のセッションを取得
    cursor.execute("""
        SELECT id, round FROM sessions 
        WHERE month = ? 
        ORDER BY round DESC LIMIT 1
    """, (month_key,))
    prev_session = cursor.fetchone()
    
    prev_rows_map = {}
    if prev_session:
        # 過去のレコードを取得
        cursor.execute("SELECT management_number, comment, checked, updated_at FROM records WHERE session_id = ?", (prev_session["id"],))
        prev_records = cursor.fetchall()
        for pr in prev_records:
            prev_rows_map[pr["management_number"]] = {
                "comment": pr["comment"],
                "checked": pr["checked"],
                "updated_at": pr["updated_at"]
            }
        round_num = prev_session["round"] + 1
    else:
        round_num = 1

    # 新セッションの保存
    cursor.execute("""
        INSERT INTO sessions (id, month, uploaded_at, round)
        VALUES (?, ?, ?, ?)
    """, (session_id, month_key, now.isoformat(timespec="seconds"), round_num))
    
    # レコードの作成 (一括挿入を利用)
    records_to_insert = []
    for r in rows:
        key = r[COL_MANAGEMENT_NUMBER]
        
        # 不要な元のフィールドはJSONデータに追いやる
        data_dict = {k: v for k, v in r.items() if k != COL_MANAGEMENT_NUMBER}
        
        pr_info = prev_rows_map.get(key, {})
        comment = pr_info.get("comment", "")
        checked = 1 if pr_info.get("checked", False) else 0
        updated_at = pr_info.get("updated_at", "")
        data_json = json.dumps(data_dict, ensure_ascii=False)
        
        records_to_insert.append((
            session_id,
            key,
            comment,
            checked,
            updated_at,
            data_json
        ))
        
    cursor.executemany("""
        INSERT OR IGNORE INTO records (session_id, management_number, comment, checked, updated_at, data)
        VALUES (?, ?, ?, ?, ?, ?)
    """, records_to_insert)
    
    # # KEEP_DATA_YEARS年前の古いデータを削除（いったん機能OFF）
    # try:
    #     threshold_date = now.replace(year=now.year - KEEP_DATA_YEARS)
    # except ValueError:
    #     # 今日が2月29日の場合は2月28日とする
    #     threshold_date = now.replace(year=now.year - KEEP_DATA_YEARS, month=2, day=28)
    
    # threshold_date_str = threshold_date.isoformat(timespec="seconds")
    # cursor.execute("DELETE FROM records WHERE session_id IN (SELECT id FROM sessions WHERE uploaded_at < ?)", (threshold_date_str,))
    # cursor.execute("DELETE FROM sessions WHERE uploaded_at < ?", (threshold_date_str,))
    
    db.commit()

    return {
        "session_id": session_id,
        "month": month_key,
        "round": round_num,
        "row_count": len(rows),
    }
