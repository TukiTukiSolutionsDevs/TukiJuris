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
      <div className="min-h-full text-on-surface">
        {/* Page header */}
        <div className="border-b border-[rgba(79,70,51,0.15)] px-6 py-4 flex items-center gap-3 sticky top-0 z-10 bg-[#0e0e12]">
          <Scale className="w-5 h-5 text-primary" />
          <h1 className="font-['Newsreader'] text-4xl font-bold text-on-surface leading-none">
            Análisis de Caso Legal
          </h1>
        </div>

        <div className="max-w-4xl mx-auto px-6 py-8">
          {!analysis ? (
            <div>
              <p className="text-[#a09ba8] mb-6 text-sm leading-relaxed">
                Describe tu situación legal y recibirás un análisis estructurado con las áreas del derecho
                involucradas, normativa aplicable, vías legales y recomendaciones.
              </p>

              <form onSubmit={handleAnalyze}>
                {/* Upload / input zone */}
                <div className="border-2 border-dashed border-[rgba(79,70,51,0.3)] rounded-lg bg-surface hover:border-primary/50 transition-colors p-1">
                  <textarea
                    value={description}
                    onChange={(e) => setDescription(e.target.value)}
                    rows={9}
                    placeholder={
                      "Describe tu caso o situación legal con el mayor detalle posible...\n\nEjemplo: Trabajo en una empresa hace 5 años. Mi empleador me notificó que seré despedido por reducción de personal, pero creo que es una represalia porque denuncié irregularidades internas..."
                    }
                    className="w-full bg-transparent px-4 py-3 text-sm text-on-surface placeholder-[#55535d] focus:outline-none resize-none"
                    disabled={loading}
                  />
                </div>

                <div className="flex items-center justify-between mt-4">
                  <p className="text-xs text-[#55535d]">
                    El análisis toma 15-30 segundos · Basado exclusivamente en derecho peruano
                  </p>
                  <button
                    type="submit"
                    disabled={loading || !description.trim()}
                    className="bg-gradient-to-br from-primary to-primary-container hover:opacity-90 disabled:opacity-40 disabled:cursor-not-allowed text-on-primary px-6 py-2.5 rounded-lg text-sm font-bold flex items-center gap-2 transition-opacity"
                  >
                    {loading ? (
                      <Loader2 className="w-4 h-4 animate-spin" />
                    ) : (
                      <FileText className="w-4 h-4" />
                    )}
                    {loading ? "Analizando..." : "Analizar caso"}
                  </button>
                </div>
              </form>
            </div>
          ) : (
            <div>
              {/* Result header */}
              <div className="flex items-center justify-between mb-6">
                <div className="flex items-center gap-3">
                  <Bot className="w-5 h-5 text-primary" />
                  <span className="font-medium text-on-surface">Análisis completado</span>
                  <span className="text-xs text-[#55535d]">
                    ({(latency / 1000).toFixed(1)}s)
                  </span>
                </div>
                <button
                  onClick={() => {
                    setAnalysis("");
                    setDescription("");
                  }}
                  className="text-sm text-primary hover:text-primary-container transition-colors"
                >
                  Nuevo análisis
                </button>
              </div>

              {/* Area badges */}
              {areas.length > 0 && (
                <div className="flex items-center gap-2 mb-5 flex-wrap">
                  <span className="text-xs text-[#55535d]">Áreas detectadas:</span>
                  {areas.map((a) => (
                    <span
                      key={a}
                      className="text-xs bg-primary/10 text-primary border border-primary/20 px-2.5 py-0.5 rounded-lg font-medium"
                    >
                      {a}
                    </span>
                  ))}
                </div>
              )}

              {/* Analysis content */}
              <div className="bg-surface-container-low border border-[rgba(79,70,51,0.15)] rounded-lg p-6">
                <div
                  className="prose prose-invert max-w-none text-sm text-on-surface leading-relaxed"
                  dangerouslySetInnerHTML={{ __html: renderMarkdown(analysis) }}
                />
              </div>

              <p className="text-[10px] text-[#55535d] mt-4">
                Este análisis es orientativo y no constituye asesoría legal. Consulte con un abogado colegiado.
              </p>
            </div>
          )}
        </div>
      </div>
    </AppLayout>
  );
}
