# backend/routers/upload.py
from __future__ import annotations

import csv
import io
import json
from datetime import datetime
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, HTTPException

from constants import (
    COL_MANAGEMENT_NUMBER,
    FIELD_COMMENT,
    FIELD_CHECKED,
    FIELD_UPDATED_AT,
)

router = APIRouter()
DATA_DIR = Path(__file__).parent.parent / "data"


def _load_month_data(month_key: str) -> dict | None:
    """月次JSONファイルを読み込む。存在しなければNoneを返す。"""
    filepath = DATA_DIR / f"{month_key}.json"
    if filepath.exists():
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    return None


def _save_month_data(month_key: str, data: dict) -> None:
    """月次JSONファイルを保存する。"""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    filepath = DATA_DIR / f"{month_key}.json"
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


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
async def upload_csv(file: UploadFile = File(...)):
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
    month_key = now.strftime("%Y-%m")
    session_id = now.strftime("%Y%m%d_%H%M%S")

    # 各行にシステムフィールドを追加
    new_rows = []
    for r in rows:
        r[FIELD_COMMENT] = ""
        r[FIELD_CHECKED] = False
        r[FIELD_UPDATED_AT] = ""
        new_rows.append(r)

    # 既存データとの突合
    existing = _load_month_data(month_key)
    if existing and len(existing.get("sessions", [])) > 0:
        prev_session = existing["sessions"][-1]
        prev_rows_map = {
            r[COL_MANAGEMENT_NUMBER]: r for r in prev_session.get("rows", [])
        }

        for nr in new_rows:
            key = nr[COL_MANAGEMENT_NUMBER]
            if key in prev_rows_map:
                prev = prev_rows_map[key]
                nr[FIELD_COMMENT] = prev.get(FIELD_COMMENT, "")
                nr[FIELD_CHECKED] = prev.get(FIELD_CHECKED, False)
                nr[FIELD_UPDATED_AT] = prev.get(FIELD_UPDATED_AT, "")

        round_num = len(existing["sessions"]) + 1
    else:
        round_num = 1

    new_session = {
        "id": session_id,
        "uploaded_at": now.isoformat(timespec="seconds"),
        "round": round_num,
        "rows": new_rows,
    }

    if existing:
        existing["sessions"].append(new_session)
        _save_month_data(month_key, existing)
    else:
        data = {
            "month": month_key,
            "sessions": [new_session],
        }
        _save_month_data(month_key, data)

    return {
        "session_id": session_id,
        "month": month_key,
        "round": round_num,
        "row_count": len(new_rows),
    }
