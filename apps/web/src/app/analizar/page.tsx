"use client";

import { useState } from "react";
import { Scale, FileText, Loader2, Bot } from "lucide-react";
import { AppLayout } from "@/components/AppLayout";
import { renderMarkdown } from "@/lib/markdown";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function AnalizarPage() {
  const [description, setDescription] = useState("");
  const [analysis, setAnalysis] = useState("");
  const [areas, setAreas] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);
  const [latency, setLatency] = useState(0);

  const handleAnalyze = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!description.trim() || loading) return;
    setLoading(true);
    setAnalysis("");

    try {
      const res = await fetch(`${API_URL}/api/analysis/case`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ case_description: description }),
      });
      if (!res.ok) throw new Error("Error");
      const data = await res.json();
      setAnalysis(data.analysis);
      setAreas(data.areas_identified);
      setLatency(data.latency_ms);
    } catch {
      setAnalysis("Error al analizar el caso. Verifica que el servidor este corriendo.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <AppLayout>
      <div className="min-h-full text-[#F5F5F5]">
        <div className="border-b border-[#1E1E2A] px-6 py-4 flex items-center gap-2">
          <Scale className="w-5 h-5 text-[#EAB308]" />
          <h1 className="font-bold text-base">Análisis de Caso Legal</h1>
        </div>

        <div className="max-w-4xl mx-auto px-6 py-8">
        {!analysis ? (
          <div>
            <p className="text-[#9CA3AF] mb-6">
              Describe tu situacion legal y recibiras un analisis estructurado con las areas del derecho
              involucradas, normativa aplicable, vias legales y recomendaciones.
            </p>
            <form onSubmit={handleAnalyze}>
              <textarea
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                rows={8}
                placeholder="Describe tu caso o situacion legal con el mayor detalle posible...&#10;&#10;Ejemplo: Trabajo en una empresa hace 5 anos. Mi empleador me notifico que sera despedido por reduccion de personal, pero creo que es una represalia porque denuncie irregularidades internas..."
                className="w-full bg-[#1A1A22] border border-[#2A2A35] rounded-xl px-4 py-3 text-sm placeholder-[#6B7280] focus:outline-none focus:border-[#EAB308]/50 resize-none"
                disabled={loading}
              />
              <div className="flex items-center justify-between mt-4">
                <p className="text-xs text-[#6B7280]">
                  El analisis toma 15-30 segundos. Se basa exclusivamente en derecho peruano.
                </p>
                <button
                  type="submit"
                  disabled={loading || !description.trim()}
                  className="bg-[#EAB308] hover:bg-[#EAB308] disabled:bg-[#2A2A35] text-white px-6 py-2.5 rounded-xl text-sm font-medium flex items-center gap-2 transition-colors"
                >
                  {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <FileText className="w-4 h-4" />}
                  {loading ? "Analizando..." : "Analizar caso"}
                </button>
              </div>
            </form>
          </div>
        ) : (
          <div>
            <div className="flex items-center justify-between mb-6">
              <div className="flex items-center gap-3">
                <Bot className="w-5 h-5 text-[#EAB308]" />
                <span className="font-medium">Analisis completado</span>
                <span className="text-xs text-[#6B7280]">({(latency / 1000).toFixed(1)}s)</span>
              </div>
              <button
                onClick={() => { setAnalysis(""); setDescription(""); }}
                className="text-sm text-[#EAB308] hover:text-[#EAB308]"
              >
                Nuevo analisis
              </button>
            </div>

            {areas.length > 0 && (
              <div className="flex items-center gap-2 mb-4 flex-wrap">
                <span className="text-xs text-[#6B7280]">Areas detectadas:</span>
                {areas.map((a) => (
                  <span key={a} className="text-xs bg-[#EAB308]/10 text-[#EAB308] px-2 py-0.5 rounded-full">{a}</span>
                ))}
              </div>
            )}

            <div className="bg-[#111116] border border-[#1E1E2A] rounded-xl p-6">
              <div
                className="prose prose-invert max-w-none text-sm text-[#F5F5F5]"
                dangerouslySetInnerHTML={{ __html: renderMarkdown(analysis) }}
              />
            </div>

            <p className="text-[10px] text-[#6B7280] mt-4">
              Este analisis es orientativo y no constituye asesoria legal. Consulte con un abogado colegiado.
            </p>
          </div>
        )}
        </div>
      </div>
    </AppLayout>
  );
}
