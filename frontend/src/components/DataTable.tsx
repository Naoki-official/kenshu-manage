// frontend/src/components/DataTable.tsx
import { useState, useMemo } from "react";
import type { RowData, SortState } from "../types";
import { COL_MANAGEMENT_NUMBER, COL_DELIVERY_DATE, FIELD_COMMENT, FIELD_CHECKED } from "../constants";

interface Props {
  rows: RowData[];
  showAll: boolean;
  columnFilters: Record<string, string>;
  onCommentClick: (row: RowData) => void;
}

/**
 * 納期が今月かどうか判定
 */
function isCurrentMonth(dateStr: string | undefined): boolean {
  if (!dateStr) return false;
  try {
    const d = new Date(dateStr);
    const now = new Date();
    return d.getFullYear() === now.getFullYear() && d.getMonth() === now.getMonth();
  } catch {
    return false;
  }
}

/**
 * 納期が過去かどうか判定
 */
function isOverdue(dateStr: string | undefined): boolean {
  if (!dateStr) return false;
  try {
    const d = new Date(dateStr);
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    return d < today;
  } catch {
    return false;
  }
}

/**
 * 行のハイライトクラスを決定
 */
function getRowClass(row: RowData): string {
  const comment = String(row[FIELD_COMMENT] || "");
  const delivery = row[COL_DELIVERY_DATE] as string | undefined;

  // コメントあり → 緑
  if (comment) return "row-green";
  // 納期超過・未コメント → 赤
  if (isOverdue(delivery) && !comment) return "row-red";
  // 今月納期・未コメント → 黄
  if (isCurrentMonth(delivery) && !comment) return "row-yellow";
  return "";
}

/**
 * デフォルトフィルタ：今月納期 かつ 未コメント
 */
function defaultFilter(row: RowData): boolean {
  const delivery = row[COL_DELIVERY_DATE] as string | undefined;
  const comment = String(row[FIELD_COMMENT] || "");
  // 今月納期 かつ 未コメント、または納期超過 かつ 未コメント
  return (isCurrentMonth(delivery) || isOverdue(delivery)) && !comment;
}

export default function DataTable({
  rows,
  showAll,
  columnFilters,
  onCommentClick,
}: Props) {
  const [sort, setSort] = useState<SortState | null>(null);

  // CSV列名を取得（_付きは除外）
  const columns = useMemo(() => {
    if (rows.length === 0) return [];
    return Object.keys(rows[0]).filter((c) => !c.startsWith("_"));
  }, [rows]);

  // フィルタ・ソート済みの行
  const filteredRows = useMemo(() => {
    let result = [...rows];

    // デフォルトフィルタ（showAll=falseの場合）
    if (!showAll) {
      result = result.filter(defaultFilter);
    }

    // 列フィルタ
    for (const [col, val] of Object.entries(columnFilters)) {
      if (!val) continue;
      const lower = val.toLowerCase();
      result = result.filter((r) => {
        const cellVal = String(r[col] ?? "").toLowerCase();
        return cellVal.includes(lower);
      });
    }

    // ソート
    if (sort) {
      result.sort((a, b) => {
        const av = String(a[sort.column] ?? "");
        const bv = String(b[sort.column] ?? "");
        const cmp = av.localeCompare(bv, "ja");
        return sort.direction === "asc" ? cmp : -cmp;
      });
    }

    return result;
  }, [rows, showAll, columnFilters, sort]);

  const handleSort = (column: string) => {
    setSort((prev) => {
      if (prev?.column === column) {
        return { column, direction: prev.direction === "asc" ? "desc" : "asc" };
      }
      return { column, direction: "asc" };
    });
  };

  if (rows.length === 0) {
    return (
      <div className="empty-state">
        <p>データがありません。</p>
      </div>
    );
  }

  return (
    <>
      <div className="row-count">
        表示: {filteredRows.length} / {rows.length} 件
      </div>
      <div className="table-wrapper">
        <table className="data-table">
          <thead>
            <tr>
              {columns.map((col) => (
                <th key={col} onClick={() => handleSort(col)} id={`th-${col}`}>
                  {col}
                  {sort?.column === col && (
                    <span className="sort-indicator">
                      {sort.direction === "asc" ? "▲" : "▼"}
                    </span>
                  )}
                </th>
              ))}
              <th>コメント</th>
              <th>済</th>
            </tr>
          </thead>
          <tbody>
            {filteredRows.length === 0 ? (
              <tr>
                <td colSpan={columns.length + 2} style={{ textAlign: "center", padding: "30px", color: "#8a90a0" }}>
                  該当するデータがありません。
                </td>
              </tr>
            ) : (
              filteredRows.map((row, idx) => (
                <tr key={String(row[COL_MANAGEMENT_NUMBER]) || idx} className={getRowClass(row)}>
                  {columns.map((col) => (
                    <td key={col}>{String(row[col] ?? "")}</td>
                  ))}
                  <td>
                    <div
                      className="comment-cell"
                      onClick={() => onCommentClick(row)}
                      id={`comment-cell-${row[COL_MANAGEMENT_NUMBER]}`}
                    >
                      {row[FIELD_COMMENT] ? (
                        <span className="comment-text">{String(row[FIELD_COMMENT])}</span>
                      ) : (
                        <span className="comment-placeholder">クリックして入力</span>
                      )}
                      <svg
                        className="comment-edit-icon"
                        viewBox="0 0 16 16"
                        fill="none"
                        stroke="currentColor"
                        strokeWidth="1.5"
                      >
                        <path d="M11.5 1.5l3 3-9 9H2.5v-3l9-9z" />
                      </svg>
                    </div>
                  </td>
                  <td>
                    {row[FIELD_CHECKED] && <span className="check-mark">&#10003;</span>}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </>
  );
}
