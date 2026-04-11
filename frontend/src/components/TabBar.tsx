// frontend/src/components/TabBar.tsx
import type { SessionSummary } from "../types";

interface Props {
  sessions: SessionSummary[];
  activeSessionId: string;
  onSelect: (id: string) => void;
}

function formatTabLabel(session: SessionSummary): string {
  const d = new Date(session.uploaded_at);
  const month = d.getMonth() + 1;
  const day = d.getDate();
  return `${month}/${day} ${session.round}回目`;
}

export default function TabBar({ sessions, activeSessionId, onSelect }: Props) {
  return (
    <div className="tab-bar" role="tablist">
      {sessions.map((s) => (
        <button
          key={s.id}
          className={`tab-item ${s.id === activeSessionId ? "active" : ""}`}
          role="tab"
          aria-selected={s.id === activeSessionId}
          onClick={() => onSelect(s.id)}
          id={`tab-${s.id}`}
        >
          {formatTabLabel(s)}
        </button>
      ))}
    </div>
  );
}
