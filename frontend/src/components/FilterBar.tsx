// frontend/src/components/FilterBar.tsx

interface Props {
  columns: string[];
  showAll: boolean;
  onToggleShowAll: () => void;
  columnFilters: Record<string, string>;
  onFilterChange: (column: string, value: string) => void;
}

export default function FilterBar({
  columns,
  showAll,
  onToggleShowAll,
  columnFilters,
  onFilterChange,
}: Props) {
  return (
    <div className="filter-bar">
      <button
        className={`filter-toggle ${showAll ? "" : "active"}`}
        onClick={onToggleShowAll}
        id="filter-toggle-btn"
      >
        {showAll ? "全件表示中" : "要対応のみ表示"}
      </button>
      <div className="filter-inputs">
        {columns.map((col) => (
          <input
            key={col}
            className="filter-input"
            placeholder={col}
            value={columnFilters[col] || ""}
            onChange={(e) => onFilterChange(col, e.target.value)}
            id={`filter-${col}`}
          />
        ))}
      </div>
    </div>
  );
}
