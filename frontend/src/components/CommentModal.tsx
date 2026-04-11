// frontend/src/components/CommentModal.tsx
import { useState } from "react";
import type { RowData } from "../types";
import { COL_MANAGEMENT_NUMBER, FIELD_COMMENT } from "../constants";

interface Props {
  row: RowData;
  onSave: (comment: string) => void;
  onClose: () => void;
}

const COMMENT_OPTIONS = [
  "",
  "今月検収",
  "来月以降に検収（仕入先と合意済み）",
];

export default function CommentModal({ row, onSave, onClose }: Props) {
  const [selected, setSelected] = useState(String(row[FIELD_COMMENT] || ""));

  const handleOverlayClick = (e: React.MouseEvent) => {
    if (e.target === e.currentTarget) onClose();
  };

  return (
    <div className="modal-overlay" onClick={handleOverlayClick} id="comment-modal-overlay">
      <div className="modal-content" id="comment-modal">
        <div className="modal-title">コメント入力</div>
        <div className="modal-subtitle">
          {COL_MANAGEMENT_NUMBER}: {String(row[COL_MANAGEMENT_NUMBER])}
        </div>
        <select
          className="modal-select"
          value={selected}
          onChange={(e) => setSelected(e.target.value)}
          id="comment-select"
        >
          {COMMENT_OPTIONS.map((opt) => (
            <option key={opt} value={opt}>
              {opt || "（空欄）"}
            </option>
          ))}
        </select>
        <div className="modal-actions">
          <button className="btn btn-outline" onClick={onClose} id="comment-cancel-btn">
            キャンセル
          </button>
          <button
            className="btn btn-primary"
            onClick={() => onSave(selected)}
            id="comment-save-btn"
          >
            確定
          </button>
        </div>
      </div>
    </div>
  );
}
