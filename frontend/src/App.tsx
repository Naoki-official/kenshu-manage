// frontend/src/App.tsx
import { useState, useEffect, useCallback, useMemo } from "react";
import type { SessionSummary, SessionDetail, RowData } from "./types";
import { COL_MANAGEMENT_NUMBER } from "./constants";
import TabBar from "./components/TabBar";
import FilterBar from "./components/FilterBar";
import DataTable from "./components/DataTable";
import CommentModal from "./components/CommentModal";

function App() {
  const [sessions, setSessions] = useState<SessionSummary[]>([]);
  const [activeMonth, setActiveMonth] = useState<string>("");
  const [activeSessionId, setActiveSessionId] = useState<string>("");
  const [sessionDetail, setSessionDetail] = useState<SessionDetail | null>(
    null
  );
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [successMsg, setSuccessMsg] = useState("");

  // Filter state
  const [showAll, setShowAll] = useState(true);
  const [columnFilters, setColumnFilters] = useState<Record<string, string>>(
    {}
  );

  // Comment modal state
  const [modalRow, setModalRow] = useState<RowData | null>(null);

  // uploading state
  const [uploading, setUploading] = useState(false);

  // Fetch session list
  const fetchSessions = useCallback(async () => {
    try {
      const res = await fetch("/api/sessions");
      if (!res.ok) throw new Error("セッション一覧の取得に失敗しました。");
      const data: SessionSummary[] = await res.json();
      setSessions(data);
      return data;
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "通信エラーが発生しました。");
      return [];
    }
  }, []);

  // Fetch session detail
  const fetchSessionDetail = useCallback(async (sessionId: string) => {
    if (!sessionId) return;
    setLoading(true);
    try {
      const res = await fetch(`/api/sessions/${sessionId}`);
      if (!res.ok) throw new Error("セッションデータの取得に失敗しました。");
      const data: SessionDetail = await res.json();
      setSessionDetail(data);
      setError("");
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "通信エラーが発生しました。");
    } finally {
      setLoading(false);
    }
  }, []);

  // Derive available months and filtered sessions
  const months = useMemo(() => {
    const set = new Set(sessions.map((s) => s.month));
    return Array.from(set).sort().slice(-6);
  }, [sessions]);

  const filteredSessions = useMemo(
    () => sessions.filter((s) => s.month === activeMonth),
    [sessions, activeMonth]
  );

  // Initial load
  useEffect(() => {
    fetchSessions().then((list) => {
      if (list.length > 0) {
        const latest = list[list.length - 1];
        setActiveMonth(latest.month);
        setActiveSessionId(latest.id);
      }
    });
  }, [fetchSessions]);

  // When month changes, select latest session in that month
  useEffect(() => {
    if (!activeMonth) return;
    const inMonth = sessions.filter((s) => s.month === activeMonth);
    if (inMonth.length > 0) {
      setActiveSessionId(inMonth[inMonth.length - 1].id);
    }
  }, [activeMonth, sessions]);

  // When active session changes
  useEffect(() => {
    if (activeSessionId) {
      fetchSessionDetail(activeSessionId);
    }
  }, [activeSessionId, fetchSessionDetail]);

  // Handle CSV upload
  const handleUpload = async (file: File) => {
    setUploading(true);
    setError("");
    setSuccessMsg("");
    const formData = new FormData();
    formData.append("file", file);
    try {
      const res = await fetch("/api/upload", { method: "POST", body: formData });
      if (!res.ok) {
        const errData = await res.json().catch(() => null);
        throw new Error(
          errData?.detail || "アップロードに失敗しました。"
        );
      }
      const result = await res.json();
      setSuccessMsg(
        `アップロード完了: ${result.row_count}件 (第${result.round}回)`
      );
      const newList = await fetchSessions();
      if (newList.length > 0) {
        const latest = newList[newList.length - 1];
        setActiveSessionId(latest.id);
      }
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "アップロードに失敗しました。");
    } finally {
      setUploading(false);
    }
  };

  // Handle comment update
  const handleCommentSave = async (
    managementNumber: string,
    comment: string
  ) => {
    if (!activeSessionId) return;
    try {
      const res = await fetch(
        `/api/sessions/${activeSessionId}/rows/${encodeURIComponent(
          managementNumber
        )}`,
        {
          method: "PATCH",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ comment }),
        }
      );
      if (!res.ok) throw new Error("コメントの保存に失敗しました。");
      const updatedRow: RowData = await res.json();

      // ローカルstateで即時更新
      setSessionDetail((prev) => {
        if (!prev) return prev;
        return {
          ...prev,
          rows: prev.rows.map((r) =>
            r[COL_MANAGEMENT_NUMBER] === managementNumber
              ? { ...r, ...updatedRow }
              : r
          ),
        };
      });
      setModalRow(null);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "通信エラーが発生しました。");
    }
  };

  // Clear messages after 5s
  useEffect(() => {
    if (successMsg) {
      const t = setTimeout(() => setSuccessMsg(""), 5000);
      return () => clearTimeout(t);
    }
  }, [successMsg]);

  return (
    <div className="app-container">
      {/* Header */}
      <header className="app-header">
        <h1>検収管理システム</h1>
        <div className="upload-area">
          {uploading && <span className="upload-status">アップロード中...</span>}
          <label className="upload-label" id="csv-upload-btn">
            CSVアップロード
            <input
              type="file"
              accept=".csv"
              onChange={(e) => {
                const f = e.target.files?.[0];
                if (f) handleUpload(f);
                e.target.value = "";
              }}
            />
          </label>
        </div>
      </header>

      {/* Messages */}
      {error && <div className="message-bar error">{error}</div>}
      {successMsg && <div className="message-bar success">{successMsg}</div>}

      {/* Month Tabs */}
      {months.length > 0 && (
        <div className="month-bar" role="tablist">
          {months.map((m) => {
            const [y, mo] = m.split("-");
            return (
              <button
                key={m}
                className={`month-item ${m === activeMonth ? "active" : ""}`}
                role="tab"
                aria-selected={m === activeMonth}
                onClick={() => setActiveMonth(m)}
                id={`month-${m}`}
              >
                {`${y}年${parseInt(mo, 10)}月`}
              </button>
            );
          })}
        </div>
      )}

      {/* Session Tabs */}
      {filteredSessions.length > 0 && (
        <TabBar
          sessions={filteredSessions}
          activeSessionId={activeSessionId}
          onSelect={setActiveSessionId}
        />
      )}

      {/* Filter bar */}
      {sessionDetail && sessionDetail.rows.length > 0 && (
        <FilterBar
          columns={Object.keys(sessionDetail.rows[0]).filter(
            (c) => !c.startsWith("_")
          )}
          showAll={showAll}
          onToggleShowAll={() => setShowAll((v) => !v)}
          columnFilters={columnFilters}
          onFilterChange={(col, val) =>
            setColumnFilters((prev) => ({ ...prev, [col]: val }))
          }
        />
      )}

      {/* Table */}
      {loading ? (
        <div className="loading">読み込み中...</div>
      ) : sessionDetail ? (
        <DataTable
          rows={sessionDetail.rows}
          showAll={showAll}
          columnFilters={columnFilters}
          sessionMonth={sessionDetail.month}
          onCommentClick={(row) => setModalRow(row)}
        />
      ) : sessions.length === 0 ? (
        <div className="empty-state">
          <p>CSVファイルをアップロードしてください。</p>
        </div>
      ) : null}

      {/* Comment Modal */}
      {modalRow && (
        <CommentModal
          row={modalRow}
          onSave={(comment) =>
            handleCommentSave(String(modalRow[COL_MANAGEMENT_NUMBER]), comment)
          }
          onClose={() => setModalRow(null)}
        />
      )}
      {/* Footer */}
      <footer className="app-footer">
        <span>2026 **部 検収管理システム</span>
        <span>お問い合わせ: [EMAIL_ADDRESS]</span>
      </footer>
    </div>
  );
}

export default App;
