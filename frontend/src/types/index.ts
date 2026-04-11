// frontend/src/types/index.ts

/** サーバーから返されるセッション概要（タブ用） */
export interface SessionSummary {
  id: string;
  month: string;
  uploaded_at: string;
  round: number;
  row_count: number;
}

/** CSVの1行 + システム付加フィールド */
export interface RowData {
  _comment: string;
  _checked: boolean;
  _updated_at: string;
  [key: string]: string | number | boolean | undefined;
}

/** セッション詳細データ */
export interface SessionDetail {
  id: string;
  uploaded_at: string;
  round: number;
  rows: RowData[];
}

/** ソート状態 */
export interface SortState {
  column: string;
  direction: "asc" | "desc";
}
