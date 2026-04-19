"use client";

/**
 * UsersPagination — reusable pagination control for admin tables.
 * Pure presentational: receives state and callbacks from parent.
 * Per T2.6: page >= 1, per_page 1..100 validated at render level.
 */

import { ChevronLeft, ChevronRight } from "lucide-react";

interface UsersPaginationProps {
  page: number;
  perPage: number;
  total: number;
  onPageChange: (page: number) => void;
  onPerPageChange?: (perPage: number) => void;
}

const PER_PAGE_OPTIONS = [10, 20, 50, 100];

export function UsersPagination({
  page,
  perPage,
  total,
  onPageChange,
  onPerPageChange,
}: UsersPaginationProps) {
  const totalPages = Math.max(1, Math.ceil(total / perPage));
  const isFirst = page <= 1;
  const isLast = page >= totalPages;

  const from = total === 0 ? 0 : (page - 1) * perPage + 1;
  const to = Math.min(page * perPage, total);

  return (
    <div className="flex items-center justify-between px-5 py-3 text-xs text-on-surface/50">
      <span>
        {total === 0
          ? "Sin resultados"
          : `${from}–${to} de ${total.toLocaleString("es-PE")}`}
      </span>

      <div className="flex items-center gap-3">
        {onPerPageChange && (
          <div className="flex items-center gap-1.5">
            <span className="text-on-surface/30">por pág.</span>
            <select
              value={perPage}
              onChange={(e) => onPerPageChange(Number(e.target.value))}
              className="bg-surface-container rounded px-1.5 py-0.5 text-xs text-on-surface border border-on-surface/10 focus:outline-none"
            >
              {PER_PAGE_OPTIONS.map((n) => (
                <option key={n} value={n}>
                  {n}
                </option>
              ))}
            </select>
          </div>
        )}

        <div className="flex items-center gap-1">
          <button
            onClick={() => onPageChange(page - 1)}
            disabled={isFirst}
            aria-label="Página anterior"
            className="p-1 rounded hover:bg-surface-container disabled:opacity-30 disabled:cursor-not-allowed"
          >
            <ChevronLeft className="w-3.5 h-3.5" />
          </button>

          <span className="px-2 tabular-nums">
            {page} / {totalPages}
          </span>

          <button
            onClick={() => onPageChange(page + 1)}
            disabled={isLast}
            aria-label="Página siguiente"
            className="p-1 rounded hover:bg-surface-container disabled:opacity-30 disabled:cursor-not-allowed"
          >
            <ChevronRight className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>
    </div>
  );
}
