"use client";

import Image from "next/image";
import Link from "next/link";
import { Plus } from "lucide-react";

// ---------------------------------------------------------------------------
// EmptyState — two variants:
//   kind="empty"   → user has NO conversations at all
//   kind="filter"  → user has conversations but current filters match none
// ---------------------------------------------------------------------------

interface EmptyStateProps {
  kind: "empty" | "filter";
  onClearFilters?: () => void;
}

export function EmptyState({ kind, onClearFilters }: EmptyStateProps) {
  if (kind === "empty") {
    return (
      <div className="hst-empty">
        <div className="hst-empty__mark">
          <Image
            src="/brand/logo-tj.png"
            alt=""
            width={52}
            height={52}
            priority
          />
        </div>
        <span className="hst-empty__eye">Historial vacío</span>
        <h1 className="hst-empty__h">Todavía no tenés consultas</h1>
        <p className="hst-empty__p">
          Tu historial se arma a medida que preguntás. Empezá con una consulta y
          después volvé acá para organizar, taggear y exportar.
        </p>
        <Link href="/" className="hst-empty__cta">
          <Plus size={14} strokeWidth={2} />
          Nueva consulta
        </Link>
      </div>
    );
  }

  return (
    <div className="hst-empty">
      <span className="hst-empty__eye">Sin resultados</span>
      <h1 className="hst-empty__h">No encontramos nada con esos filtros</h1>
      <p className="hst-empty__p">
        Probá ajustar la búsqueda, quitar alguna etiqueta o cambiar la carpeta
        seleccionada.
      </p>
      {onClearFilters && (
        <button type="button" className="hst-empty__cta" onClick={onClearFilters}>
          Limpiar filtros
        </button>
      )}
    </div>
  );
}
