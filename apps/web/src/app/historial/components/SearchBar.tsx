"use client";

import { Search, Filter, SortDesc, X } from "lucide-react";

// ---------------------------------------------------------------------------
// SearchBar — full-width search + active filter chips + count + sort control
// Used at the top of the historial main column.
// ---------------------------------------------------------------------------

export type FilterChipKind = "tag" | "folder" | "area" | "date";

export interface ActiveFilter {
  key: string; // stable id to pass back on remove
  kind: FilterChipKind;
  label: string;
}

export type SortMode = "recent" | "oldest" | "messages" | "alpha";

const SORT_LABEL: Record<SortMode, string> = {
  recent: "Recientes primero",
  oldest: "Antiguas primero",
  messages: "Más mensajes",
  alpha: "Alfabético",
};

interface SearchBarProps {
  value: string;
  onChange: (next: string) => void;
  placeholder?: string;
  filters: ActiveFilter[];
  onRemoveFilter: (key: string) => void;
  onClearFilters: () => void;
  totalCount: number;
  filteredCount: number | null; // null → no filtering active
  sort: SortMode;
  onSortClick: () => void;
  onFiltersClick?: () => void;
  filtersOpen?: boolean;
  inputRef?: React.RefObject<HTMLInputElement | null>;
}

function cx(...parts: (string | false | null | undefined)[]): string {
  return parts.filter(Boolean).join(" ");
}

export function SearchBar({
  value,
  onChange,
  placeholder = "Buscar en tu historial…",
  filters,
  onRemoveFilter,
  onClearFilters,
  totalCount,
  filteredCount,
  sort,
  onSortClick,
  onFiltersClick,
  filtersOpen = false,
  inputRef,
}: SearchBarProps) {
  const hasFilters = filters.length > 0;
  const displayedCount = filteredCount ?? totalCount;

  return (
    <div className="hst-searchwrap">
      <div className="hst-search">
        <Search size={16} strokeWidth={1.6} className="hst-search__ico" aria-hidden="true" />
        <input
          ref={inputRef}
          type="text"
          placeholder={placeholder}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          aria-label="Buscar"
        />
        {onFiltersClick && (
          <button
            type="button"
            className={cx("hst-search__btn", filtersOpen && "is-on")}
            onClick={onFiltersClick}
            aria-expanded={filtersOpen}
          >
            <Filter size={14} strokeWidth={1.6} />
            Filtros
          </button>
        )}
        <span className="hst-search__kbd" aria-hidden="true">⌘F</span>
      </div>

      {hasFilters && (
        <div className="hst-filters">
          <span className="hst-filters__label">Filtros</span>
          {filters.map((f) => (
            <span
              key={f.key}
              className={cx(
                "hst-fchip",
                f.kind === "tag" && "hst-fchip--tag",
                f.kind === "folder" && "hst-fchip--folder"
              )}
            >
              {f.kind === "tag" && <span className="hst-tag__hash">#</span>}
              {f.label}
              <button
                type="button"
                className="hst-fchip__x"
                onClick={() => onRemoveFilter(f.key)}
                aria-label={`Quitar filtro ${f.label}`}
              >
                <X size={10} strokeWidth={2} />
              </button>
            </span>
          ))}
          <button
            type="button"
            className="hst-filters__clear"
            onClick={onClearFilters}
          >
            Limpiar todo
          </button>
        </div>
      )}

      <div className="hst-meta">
        <span className="hst-meta__count">
          {displayedCount.toLocaleString("es-PE")}{" "}
          {hasFilters
            ? displayedCount === 1 ? "resultado" : "resultados"
            : displayedCount === 1 ? "conversación" : "conversaciones"}
        </span>
        <button type="button" className="hst-sortbtn" onClick={onSortClick}>
          <SortDesc size={13} strokeWidth={1.6} />
          {SORT_LABEL[sort]}
        </button>
      </div>
    </div>
  );
}
