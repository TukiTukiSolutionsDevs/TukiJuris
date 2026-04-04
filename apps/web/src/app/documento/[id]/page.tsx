"use client";

import { useState, useEffect } from "react";
import { ArrowLeft, Scale, FileText, BookOpen, Search } from "lucide-react";
import Link from "next/link";
import { useParams } from "next/navigation";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface DocChunk {
  id: string;
  article_number: string | null;
  section_path: string | null;
  content: string;
}

interface DocData {
  document: {
    id: string;
    title: string;
    document_type: string;
    document_number: string | null;
    legal_area: string;
    source: string;
  };
  chunks: DocChunk[];
  total_chunks: number;
}

const AREA_COLORS: Record<string, string> = {
  civil: "bg-blue-500/10 text-blue-400",
  penal: "bg-red-500/10 text-red-400",
  laboral: "bg-green-500/10 text-green-400",
  tributario: "bg-yellow-500/10 text-yellow-400",
  constitucional: "bg-purple-500/10 text-purple-400",
  administrativo: "bg-orange-500/10 text-orange-400",
  corporativo: "bg-cyan-500/10 text-cyan-400",
  registral: "bg-pink-500/10 text-pink-400",
  competencia: "bg-amber-500/10 text-amber-400",
  compliance: "bg-indigo-500/10 text-indigo-400",
  comercio_exterior: "bg-teal-500/10 text-teal-400",
};

export default function DocumentoPage() {
  const params = useParams();
  const [data, setData] = useState<DocData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [searchTerm, setSearchTerm] = useState("");

  useEffect(() => {
    if (!params.id) return;
    fetch(`${API_URL}/api/documents/${params.id}/chunks`)
      .then((r) => {
        if (!r.ok) throw new Error("Documento no encontrado");
        return r.json();
      })
      .then(setData)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [params.id]);

  if (loading) {
    return (
      <div className="min-h-screen bg-[#0A0A0F] flex items-center justify-center text-[#9CA3AF]">
        Cargando documento...
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="min-h-screen bg-[#0A0A0F] flex items-center justify-center text-red-400">
        {error || "Error al cargar"}
      </div>
    );
  }

  const { document: doc, chunks } = data;

  const filteredChunks = searchTerm
    ? chunks.filter(
        (c) =>
          c.content.toLowerCase().includes(searchTerm.toLowerCase()) ||
          (c.article_number && c.article_number.includes(searchTerm))
      )
    : chunks;

  return (
    <div className="min-h-screen bg-[#0A0A0F] text-gray-100">
      {/* Header */}
      <header className="border-b border-[#1E1E2A] bg-[#111116]/80 sticky top-0 z-10">
        <div className="max-w-6xl mx-auto px-6 py-4">
          <div className="flex items-center gap-4 mb-3">
            <Link href="/buscar" className="text-gray-400 hover:text-white">
              <ArrowLeft className="w-5 h-5" />
            </Link>
            <Scale className="w-5 h-5 text-amber-500" />
            <span
              className={`text-[10px] px-2 py-0.5 rounded-full ${AREA_COLORS[doc.legal_area] || "bg-[#1A1A22] text-[#9CA3AF]"}`}
            >
              {doc.legal_area}
            </span>
          </div>
          <h1 className="text-xl font-bold">{doc.title}</h1>
          <div className="flex items-center gap-4 mt-2 text-sm text-[#9CA3AF]">
            {doc.document_number && <span>{doc.document_number}</span>}
            <span>|</span>
            <span>{doc.document_type}</span>
            <span>|</span>
            <span>{data.total_chunks} articulos</span>
          </div>
        </div>
      </header>

      {/* Search bar */}
      <div className="sticky top-[89px] z-10 bg-[#12121a] border-b border-[#1E1E2A] p-3">
        <div className="max-w-6xl mx-auto">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" />
            <input
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder="Buscar en este documento..."
              className="w-full pl-10 pr-4 py-2 bg-[#1A1A22] border border-[#1E1E2A] rounded-lg text-sm text-gray-200 placeholder-gray-500 focus:outline-none focus:border-amber-500/50"
            />
          </div>
          {searchTerm && (
            <p className="text-xs text-gray-500 mt-1">{filteredChunks.length} resultados</p>
          )}
        </div>
      </div>

      {/* Body: TOC + Articles */}
      <div className="max-w-6xl mx-auto px-6 py-6 flex gap-8">
        {/* Left TOC — desktop only */}
        <aside className="hidden lg:block w-56 shrink-0 sticky top-[145px] h-[calc(100vh-145px)] overflow-auto py-2 pr-4 border-r border-[#1E1E2A]">
          <h3 className="text-xs font-medium text-gray-500 uppercase mb-3">Índice</h3>
          <nav className="space-y-1">
            {chunks.filter((c) => c.article_number).map((c) => (
              <a
                key={c.id}
                href={`#art-${c.article_number}`}
                className="block text-xs text-gray-400 hover:text-amber-400 truncate py-0.5 transition-colors"
              >
                Art. {c.article_number}
              </a>
            ))}
          </nav>
        </aside>

        {/* Articles */}
        <div className="flex-1 min-w-0 space-y-6">
          {filteredChunks.map((chunk) => (
            <article
              key={chunk.id}
              id={`art-${chunk.article_number}`}
              className="bg-[#111116] border border-[#1E1E2A] rounded-xl p-6 hover:border-[#2A2A35] transition-colors"
            >
              <div className="flex items-center gap-3 mb-3">
                <BookOpen className="w-4 h-4 text-amber-500" />
                {chunk.article_number && (
                  <span className="text-sm font-medium text-amber-400">
                    Art. {chunk.article_number}
                  </span>
                )}
                {chunk.section_path && (
                  <span className="text-xs text-gray-500">{chunk.section_path}</span>
                )}
                {chunk.article_number && (
                  <Link
                    href={`/?q=${encodeURIComponent(`¿Qué dice el Art. ${chunk.article_number} del ${doc.title}?`)}`}
                    className="ml-auto text-xs text-amber-400/70 hover:text-amber-400 transition-colors shrink-0"
                  >
                    Consultar sobre este artículo →
                  </Link>
                )}
              </div>
              <p className="text-sm text-gray-300 leading-relaxed whitespace-pre-wrap">
                {chunk.content}
              </p>
            </article>
          ))}

          {filteredChunks.length === 0 && searchTerm && (
            <div className="text-center py-12 text-gray-500 text-sm">
              No se encontraron resultados para &ldquo;{searchTerm}&rdquo;
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
