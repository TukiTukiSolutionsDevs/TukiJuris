import Link from "next/link";
import { Search, Home } from "lucide-react";

export default function NotFound() {
  return (
    <div className="min-h-screen bg-background flex items-center justify-center px-4">
      <div className="max-w-md w-full text-center">
        {/* Icon */}
        <div className="w-16 h-16 rounded-2xl bg-primary/10 flex items-center justify-center mx-auto mb-6">
          <Search className="w-8 h-8 text-primary" />
        </div>

        {/* 404 */}
        <h1 className="font-['Newsreader'] text-6xl font-bold text-primary mb-2">
          404
        </h1>

        {/* Title */}
        <h2 className="font-['Newsreader'] text-xl font-bold text-on-surface mb-3">
          Pagina no encontrada
        </h2>

        {/* Description */}
        <p className="text-on-surface-variant text-sm leading-relaxed mb-8">
          La pagina que buscas no existe o fue movida. Verifica la URL
          o volve al inicio.
        </p>

        {/* Actions */}
        <div className="flex items-center justify-center gap-3">
          <Link
            href="/landing"
            className="inline-flex items-center gap-2 px-5 py-2.5 rounded-lg text-sm font-bold text-on-primary gold-gradient hover:opacity-90 transition-opacity"
          >
            <Home className="w-4 h-4" />
            Volver al inicio
          </Link>
          <Link
            href="/docs"
            className="inline-flex items-center gap-2 px-5 py-2.5 rounded-lg text-sm text-on-surface-variant hover:text-on-surface ghost-border hover:bg-surface-container-high/40 transition-colors"
          >
            Ver documentacion
          </Link>
        </div>
      </div>
    </div>
  );
}
