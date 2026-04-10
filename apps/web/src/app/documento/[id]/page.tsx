"use client";

import { useState, useEffect } from "react";
import { ArrowLeft, Scale, BookOpen, Search } from "lucide-react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { AppLayout } from "@/components/AppLayout";

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
      <AppLayout>
        <div className="flex-1 flex items-center justify-center text-[#6B7280] text-sm">
          Cargando documento...
        </div>
      </AppLayout>
    );
  }

  if (error || !data) {
    return (
      <AppLayout>
        <div className="flex-1 flex items-center justify-center text-red-400 text-sm">
          {error || "Error al cargar"}
        </div>
      </AppLayout>
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
    <AppLayout>
      {/* Header */}
      <header className="sticky top-0 z-10 bg-[#111116]/90 backdrop-blur-sm border-b border-[rgba(79,70,51,0.15)]">
        <div className="max-w-5xl mx-auto px-6 py-4">
          <div className="flex items-center gap-3 mb-3">
            <Link
              href="/buscar"
              className="text-[#6B7280] hover:text-on-surface transition-colors"
            >
              <ArrowLeft className="w-4 h-4" />
            </Link>
            <Scale className="w-4 h-4 text-primary-container" />
            <span className="bg-secondary-container text-secondary text-[10px] uppercase tracking-widest rounded px-2 py-0.5">
              {doc.legal_area}
            </span>
            <span className="bg-secondary-container text-secondary text-[10px] uppercase tracking-widest rounded px-2 py-0.5">
              {doc.document_type}
            </span>
          </div>
          <h1 className="font-['Newsreader'] text-3xl text-on-surface leading-snug">
            {doc.title}
          </h1>
          <div className="flex items-center gap-3 mt-2">
            {doc.document_number && (
              <span className="text-xs text-[#6B7280]">{doc.document_number}</span>
            )}
            {doc.document_number && (
              <span className="text-[#2A2A35] text-xs">·</span>
            )}
            <span className="text-xs text-[#6B7280]">
              {data.total_chunks} artículos
            </span>
          </div>
        </div>
      </header>

      {/* Search bar */}
      <div className="sticky top-[89px] z-10 bg-surface-container-lowest border-b border-[rgba(79,70,51,0.15)] px-6 py-3">
        <div className="max-w-5xl mx-auto">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[#4B5563]" />
            <input
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder="Buscar en este documento..."
              className="w-full pl-9 pr-4 py-2 bg-[#111116] border border-[rgba(79,70,51,0.15)] rounded-lg text-sm text-on-surface placeholder-[#4B5563] focus:outline-none focus:border-primary-container/40 transition-colors"
            />
          </div>
          {searchTerm && (
            <p className="text-[10px] text-[#4B5563] mt-1.5">
              {filteredChunks.length} resultado{filteredChunks.length !== 1 ? "s" : ""}
            </p>
          )}
        </div>
      </div>

      {/* Body: TOC sidebar + Articles */}
      <div className="max-w-5xl mx-auto px-6 py-6 flex gap-8 flex-1">
        {/* Left TOC — desktop only */}
        <aside className="hidden lg:block w-52 shrink-0 sticky top-[145px] h-[calc(100vh-145px)] overflow-auto py-1 pr-4 border-r border-[rgba(79,70,51,0.15)]">
          <h3 className="text-[10px] uppercase tracking-widest text-[#4B5563] mb-3 font-medium">
            Índice
          </h3>
          <nav className="space-y-0.5">
            {chunks
              .filter((c) => c.article_number)
              .map((c) => (
                <a
                  key={c.id}
                  href={`#art-${c.article_number}`}
                  className="block text-xs text-[#6B7280] hover:text-primary-container truncate py-0.5 transition-colors"
                >
                  Art. {c.article_number}
                </a>
              ))}
          </nav>
        </aside>

        {/* Articles */}
        <div className="flex-1 min-w-0 space-y-4">
          {filteredChunks.map((chunk) => (
            <article
              key={chunk.id}
              id={`art-${chunk.article_number}`}
              className="bg-[#111116] border border-[rgba(79,70,51,0.15)] rounded-lg p-5 hover:border-[rgba(79,70,51,0.30)] transition-colors"
            >
              <div className="flex items-center gap-3 mb-3">
                <BookOpen className="w-4 h-4 text-primary-container shrink-0" />
                {chunk.article_number && (
                  <span className="text-sm font-medium text-primary-container">
                    Art. {chunk.article_number}
                  </span>
                )}
                {chunk.section_path && (
                  <span className="text-xs text-[#4B5563] truncate">
                    {chunk.section_path}
                  </span>
                )}
                {chunk.article_number && (
                  <Link
                    href={`/?q=${encodeURIComponent(`¿Qué dice el Art. ${chunk.article_number} del ${doc.title}?`)}`}
                    className="ml-auto text-[10px] text-primary-container/60 hover:text-primary-container transition-colors shrink-0"
                  >
                    Consultar sobre este artículo →
                  </Link>
                )}
              </div>
              <p className="text-sm text-on-surface-variant leading-relaxed whitespace-pre-wrap">
                {chunk.content}
              </p>
            </article>
          ))}

          {filteredChunks.length === 0 && searchTerm && (
            <div className="text-center py-16 text-[#4B5563] text-sm">
              No se encontraron resultados para &ldquo;{searchTerm}&rdquo;
            </div>
          )}
        </div>
      </div>
    </AppLayout>
  );
}
