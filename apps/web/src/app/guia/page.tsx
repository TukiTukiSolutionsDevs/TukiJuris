"use client";

import { useState } from "react";
import {
  Scale,
  BookOpen,
  Shield,
  Briefcase,
  Landmark,
  Gavel,
  Building2,
  ScrollText,
  FileCheck,
  Globe,
  Lock,
  BadgeCheck,
  HelpCircle,
  ChevronDown,
  ChevronUp,
  MessageSquare,
  Search,
  FileText,
  Users,
  Code2,
  BarChart3,
  Lightbulb,
  CheckCircle2,
  Mail,
  ExternalLink,
} from "lucide-react";
import Link from "next/link";
import Image from "next/image";
import { AppLayout } from "@/components/AppLayout";

// ————————————————————————————————————————————————
// DATA
// ————————————————————————————————————————————————

const LEGAL_AREAS = [
  {
    id: "civil",
    name: "Derecho Civil",
    icon: BookOpen,
    color: "text-blue-400",
    description:
      "Contratos, responsabilidad civil, derechos reales, familia y sucesiones.",
    examples: [
      "Art. 1969 del Código Civil sobre responsabilidad civil",
      "Requisitos para un contrato de compraventa válido",
      "Plazos de prescripción en acciones civiles",
    ],
  },
  {
    id: "penal",
    name: "Derecho Penal",
    icon: Shield,
    color: "text-red-400",
    description:
      "Delitos, penas, proceso penal, medidas cautelares y jurisprudencia del PJ.",
    examples: [
      "Elementos del delito de estafa según el Código Penal",
      "Diferencia entre homicidio culposo y doloso",
      "Plazos de detención preliminar en Perú",
    ],
  },
  {
    id: "laboral",
    name: "Derecho Laboral",
    icon: Briefcase,
    color: "text-green-400",
    description:
      "Contratos laborales, beneficios sociales, CTS, despidos y SUNAFIL.",
    examples: [
      "¿Cómo se calcula la CTS en Perú?",
      "Requisitos para un despido justificado",
      "Beneficios sociales en contratos a tiempo parcial",
    ],
  },
  {
    id: "tributario",
    name: "Derecho Tributario",
    icon: Landmark,
    color: "text-yellow-400",
    description:
      "IGV, Impuesto a la Renta, SUNAT, infracciones tributarias y procedimientos.",
    examples: [
      "Tasa del IGV y excepciones en Perú",
      "Regímenes tributarios para MYPES",
      "Procedimiento de fiscalización SUNAT",
    ],
  },
  {
    id: "constitucional",
    name: "Derecho Constitucional",
    icon: Gavel,
    color: "text-purple-400",
    description:
      "Habeas corpus, amparo, inconstitucionalidad, derechos fundamentales y TC.",
    examples: [
      "¿Cuándo procede un habeas corpus?",
      "Diferencia entre amparo e inconstitucionalidad",
      "Jurisprudencia del TC sobre libertad de expresión",
    ],
  },
  {
    id: "administrativo",
    name: "Derecho Administrativo",
    icon: Building2,
    color: "text-orange-400",
    description:
      "Actos administrativos, silencio administrativo, recursos y Ley 27444.",
    examples: [
      "Plazos del silencio administrativo positivo y negativo",
      "Cómo apelar un acto administrativo",
      "Responsabilidad del Estado por actos administrativos",
    ],
  },
  {
    id: "corporativo",
    name: "Derecho Corporativo",
    icon: ScrollText,
    color: "text-cyan-400",
    description:
      "Sociedades comerciales, M&A, gobierno corporativo, LGS y BCRP.",
    examples: [
      "Requisitos para constituir una SAC en Perú",
      "Diferencia entre directorio y junta general",
      "Responsabilidad de socios en SRL",
    ],
  },
  {
    id: "registral",
    name: "Derecho Registral",
    icon: FileCheck,
    color: "text-pink-400",
    description:
      "Registros Públicos, SUNARP, inscripciones, publicidad registral.",
    examples: [
      "Cómo inscribir una empresa en SUNARP",
      "Principio de prioridad registral",
      "Rectificación de partidas registrales",
    ],
  },
  {
    id: "comercio_exterior",
    name: "Comercio Exterior",
    icon: Globe,
    color: "text-teal-400",
    description:
      "Aduanas, regímenes aduaneros, SUNAT Aduanas, tratados comerciales.",
    examples: [
      "Regímenes de importación temporal en Perú",
      "Drawback: requisitos y cálculo",
      "Valoración aduanera según el acuerdo de la OMC",
    ],
  },
  {
    id: "compliance",
    name: "Compliance",
    icon: Lock,
    color: "text-indigo-400",
    description:
      "LAFT, protección de datos personales, SAGRILAFT, prevención lavado.",
    examples: [
      "Obligaciones de la Ley 29733 de protección de datos",
      "¿Qué empresas deben tener sistema SPLAFT?",
      "Procedimiento de debida diligencia del cliente",
    ],
  },
  {
    id: "competencia",
    name: "Competencia / PI",
    icon: BadgeCheck,
    color: "text-primary",
    description:
      "INDECOPI, marcas, patentes, competencia desleal y publicidad.",
    examples: [
      "Cómo registrar una marca en INDECOPI",
      "Prácticas restrictivas de la competencia",
      "Procedimiento por publicidad engañosa",
    ],
  },
];

const FAQ_ITEMS = [
  {
    q: "¿Es gratis usar TukiJuris?",
    a: "Durante la beta, sí — el acceso a la plataforma es gratuito. TukiJuris no cobra por consultas ni incluye modelos de IA. Necesitás traer tu propia clave API de un proveedor (OpenAI, Anthropic, Google AI o DeepSeek). El costo de uso del modelo lo cobra directamente el proveedor.",
  },
  {
    q: "¿Necesito una clave API para usar TukiJuris?",
    a: "Sí. TukiJuris es una plataforma de asistencia legal que se conecta a proveedores de IA como OpenAI, Anthropic o Google. Necesitás tu propia clave API del proveedor que prefieras. Podés configurarla en Configuración → API Keys. El costo de uso del modelo lo cobra directamente el proveedor, no TukiJuris.",
  },
  {
    q: "¿TukiJuris reemplaza a un abogado?",
    a: "No. TukiJuris brinda orientación jurídica informativa — te ayuda a entender la normativa, identificar artículos relevantes y analizar tu situación. No constituye asesoría legal ni reemplaza la consulta con un abogado colegiado para casos específicos o decisiones importantes.",
  },
  {
    q: "¿Qué normativa incluye la base de conocimiento?",
    a: "Incluye: Constitución Política del Perú, códigos (Civil, Penal, Procesal Civil, Procesal Penal, Tributario, Laboral), leyes orgánicas, decretos legislativos y supremos vigentes, jurisprudencia del Tribunal Constitucional e INDECOPI, y normas sectoriales actualizadas.",
  },
  {
    q: "¿Cómo debo citar las respuestas de TukiJuris?",
    a: "Las citaciones que incluye el sistema son referenciales. Siempre verificá el texto completo en la fuente oficial: el Diario El Peruano, SPIJ (Sistema Peruano de Información Jurídica) o el portal del organismo competente antes de usar en documentos legales formales.",
  },
  {
    q: "¿Puedo usar la API de TukiJuris?",
    a: "Sí. La API pública permite consultas, búsqueda de normativa y análisis de casos. TukiJuris ofrece API Keys para integración. Podés crear y gestionar tus keys desde Configuración > API Keys. Consultá la documentación en /docs para endpoints, ejemplos de código y límites de uso.",
  },
  {
    q: "¿Qué modelos de IA puedo usar?",
    a: "TukiJuris es compatible con los modelos de OpenAI (GPT-4o, GPT-4o Mini), Anthropic (Claude Sonnet 4, Claude Haiku), Google AI (Gemini 2.5 Flash, Gemini 2.5 Pro) y DeepSeek (DeepSeek Chat, DeepSeek Reasoner). Los modelos disponibles en el selector dependen de qué claves API tengas configuradas en Configuración → API Keys.",
  },
  {
    q: "¿Mis consultas son privadas?",
    a: "Sí. Tus consultas son privadas y no se comparten con terceros. No usamos tus consultas para entrenar modelos de IA. Las organizaciones solo pueden ver el agregado anonimizado de uso de sus miembros, no el contenido de cada consulta.",
  },
  {
    q: "¿Cómo reporto un error en una respuesta?",
    a: "Bajo cada respuesta del asistente hay botones de feedback (pulgar arriba / pulgar abajo). Si la respuesta tiene un error, usá el pulgar abajo y podés agregar un comentario describiendo el problema. El equipo revisa todos los reportes.",
  },
  {
    q: "¿Funciona para derecho de otros países?",
    a: "No actualmente. TukiJuris está especializado exclusivamente en derecho peruano. La base de conocimiento, los agentes y los prompts están diseñados para normativa peruana. Para derecho comparado, podés preguntar pero las respuestas tendrán menos precisión.",
  },
  {
    q: "¿Puedo invitar a mi equipo?",
    a: "Sí. Desde /organizacion podés crear una organización, invitar miembros por email y asignar roles (admin, miembro). Las organizaciones tienen un panel de analytics compartido y pueden configurar modelos y preferencias para todo el equipo.",
  },
  {
    q: "¿Hay límite de consultas?",
    a: "TukiJuris no limita el número de consultas. El límite real lo impone el proveedor de IA según tu clave API y plan con ellos. La plataforma cobra solo por acceso, no por consultas.",
  },
  {
    q: "¿Con qué frecuencia se actualiza la normativa?",
    a: "La base de conocimiento se actualiza de dos formas: scrapers automáticos que monitorean el Diario El Peruano y el SPIJ diariamente, y actualizaciones manuales del equipo legal para normas de alta relevancia. Si ves normativa desactualizada, reportalo.",
  },
  {
    q: "¿Puedo descargar o exportar las respuestas?",
    a: "Sí podés copiar el texto de cualquier respuesta. Disponible — hacé clic en el ícono de descarga junto a cualquier respuesta del asistente para generar un PDF profesional. Para la API, las respuestas se retornan en JSON que podés integrar en tus propios sistemas.",
  },
  {
    q: "¿Cómo cambio de plan?",
    a: "Desde /billing podés ver tu plan actual, el uso del mes y las opciones de upgrade. El cambio es inmediato al confirmar el pago. Si tenés preguntas sobre precios o necesitás un plan corporativo, escribinos a soporte@tukijuris.net.pe.",
  },
  {
    q: "¿Necesito crear una cuenta para usar TukiJuris?",
    a: "Sí, se requiere registro gratuito para acceder a la plataforma. El registro toma menos de un minuto — solo email y contraseña. Esto nos permite guardar tu historial de consultas, preferencias y límites de uso.",
  },
];

const HOW_IT_WORKS = [
  {
    step: 1,
    title: "Escribí tu consulta",
    desc: "Escribí tu pregunta legal en lenguaje natural, tal como se lo preguntarías a un abogado. No necesitás usar términos técnicos.",
    detail: "Ej: '¿Cuáles son los requisitos para despedir a un trabajador de forma justificada?'",
  },
  {
    step: 2,
    title: "Clasificación automática",
    desc: "El orquestador analiza tu consulta y la clasifica en el área del derecho correspondiente. También podés seleccionar el área manualmente desde el sidebar.",
    detail: "El clasificador tiene 95%+ de precisión en las 11 áreas soportadas.",
  },
  {
    step: 3,
    title: "Búsqueda de normativa",
    desc: "El sistema busca en la base de conocimiento los artículos, leyes y jurisprudencia más relevantes usando búsqueda semántica + reranking.",
    detail: "Busca en más de 50,000 fragmentos de normativa peruana.",
  },
  {
    step: 4,
    title: "Respuesta con citaciones",
    desc: "Un agente especializado en el área genera la respuesta en tiempo real, citando las fuentes normativas utilizadas.",
    detail: "Cada respuesta incluye el artículo, norma y organismo de origen.",
  },
];

const FEATURES = [
  {
    icon: MessageSquare,
    title: "Chat con IA",
    desc: "Consultas en lenguaje natural con respuestas en streaming en tiempo real. Historial de conversaciones guardado localmente.",
  },
  {
    icon: Search,
    title: "Búsqueda de normativa",
    desc: "Buscá artículos específicos por número, texto o materia. Accedé al texto completo de leyes, códigos y decretos.",
  },
  {
    icon: Scale,
    title: "Análisis de caso",
    desc: "Describí un caso complejo que involucra múltiples áreas del derecho. El sistema activa agentes especializados en paralelo.",
  },
  {
    icon: FileText,
    title: "Visor de documentos",
    desc: "Leé la normativa completa con navegación por capítulos y artículos. Buscá dentro del documento.",
  },
  {
    icon: Users,
    title: "Organizaciones",
    desc: "Equipos legales con roles, invitaciones, analytics de uso compartido y configuración centralizada.",
  },
  {
    icon: Code2,
    title: "API para integraciones",
    desc: "API REST pública con autenticación por API key. Integrá TukiJuris en tus propias aplicaciones y flujos de trabajo.",
  },
];

const TOC_LINKS = [
  { href: "#como-funciona", label: "Cómo funciona" },
  { href: "#areas", label: "Áreas del Derecho" },
  { href: "#tips", label: "Consultas efectivas" },
  { href: "#funcionalidades", label: "Funcionalidades" },
  { href: "#faq", label: "Preguntas frecuentes" },
  { href: "#soporte", label: "Soporte" },
];

// ————————————————————————————————————————————————
// COMPONENTS
// ————————————————————————————————————————————————

function FaqItem({ q, a }: { q: string; a: string }) {
  const [open, setOpen] = useState(false);
  return (
    <div
      className="bg-surface-container-low rounded-lg overflow-hidden"
      style={{ border: "1px solid rgba(79,70,51,0.15)" }}
    >
      <button
        onClick={() => setOpen(!open)}
        className="w-full flex items-center justify-between px-5 py-4 text-left hover:bg-surface transition-colors"
      >
        <span className="text-sm font-medium text-on-surface pr-4">{q}</span>
        {open ? (
          <ChevronUp className="w-4 h-4 text-primary shrink-0" />
        ) : (
          <ChevronDown className="w-4 h-4 text-on-surface/30 shrink-0" />
        )}
      </button>
      {open && (
        <div
          className="px-5 pb-5 bg-surface"
          style={{ borderTop: "1px solid rgba(79,70,51,0.15)" }}
        >
          <p className="text-sm text-on-surface/60 leading-relaxed pt-4">{a}</p>
        </div>
      )}
    </div>
  );
}

// ————————————————————————————————————————————————
// PAGE
// ————————————————————————————————————————————————

export default function GuiaPage() {
  const [expandedArea, setExpandedArea] = useState<string | null>(null);

  return (
    <AppLayout>
      <div className="min-h-full text-on-surface">
        {/* Top bar */}
        <div
          className="px-4 py-4 flex items-center gap-3 sticky top-0 z-10 bg-surface-container-lowest"
          style={{ borderBottom: "1px solid rgba(79,70,51,0.15)" }}
        >
          <HelpCircle className="w-5 h-5 text-primary" />
          <h1 className="font-['Newsreader'] font-bold text-base">Guía de Uso</h1>
        </div>

        <div className="max-w-6xl mx-auto px-4 py-12 lg:py-16">
          <div className="lg:grid lg:grid-cols-[220px_1fr] lg:gap-12">

            {/* Sidebar TOC — sticky desktop */}
            <aside className="hidden lg:block">
              <div className="sticky top-24 space-y-1">
                <p className="text-[10px] uppercase tracking-[0.2em] text-on-surface/40 mb-3 px-2">
                  Contenido
                </p>
                {TOC_LINKS.map((link) => (
                  <a
                    key={link.href}
                    href={link.href}
                    className="block px-2 py-1.5 text-sm text-on-surface/40 hover:text-primary transition-colors rounded-lg"
                  >
                    {link.label}
                  </a>
                ))}
              </div>
            </aside>

            {/* Main content */}
            <main className="space-y-20">

              {/* HERO */}
              <section>
                <div className="mb-6">
                  <Image
                    src="/brand/logo-full.png"
                    alt="TukiJuris"
                    width={160}
                    height={40}
                    className="h-9 w-auto"
                  />
                </div>
                <div
                  className="inline-flex items-center gap-2 bg-primary/10 rounded-lg px-3 py-1 text-xs text-primary mb-4"
                  style={{ border: "1px solid rgba(255,209,101,0.2)" }}
                >
                  <HelpCircle className="w-3.5 h-3.5" />
                  Documentación
                </div>
                <h1 className="font-['Newsreader'] text-4xl lg:text-5xl font-bold mb-4 leading-tight text-on-surface">
                  Guía de uso de{" "}
                  <span className="text-primary">TukiJuris</span>
                </h1>
                <p className="text-lg text-on-surface/50 max-w-2xl leading-relaxed">
                  Todo lo que necesitás saber para sacarle el máximo provecho a la
                  plataforma jurídica inteligente especializada en derecho peruano.
                </p>
              </section>

              {/* COMO FUNCIONA */}
              <section id="como-funciona" className="scroll-mt-20">
                <h2 className="font-['Newsreader'] text-2xl font-bold mb-2 text-on-surface">
                  Cómo funciona
                </h2>
                <p className="text-on-surface/50 text-sm mb-8">
                  Cada consulta pasa por un proceso de 4 etapas optimizadas para derecho peruano.
                </p>
                <div className="space-y-4">
                  {HOW_IT_WORKS.map(({ step, title, desc, detail }) => (
                    <div
                      key={step}
                      className="flex gap-4 p-5 rounded-lg bg-surface-container-low"
                      style={{ border: "1px solid rgba(79,70,51,0.15)" }}
                    >
                      <div
                        className="w-8 h-8 rounded-lg bg-primary/10 flex items-center justify-center shrink-0 mt-0.5"
                        style={{ border: "1px solid rgba(255,209,101,0.2)" }}
                      >
                        <span className="text-xs font-bold text-primary">{step}</span>
                      </div>
                      <div>
                        <h3 className="font-semibold text-on-surface mb-1">{title}</h3>
                        <p className="text-sm text-on-surface/50 mb-2">{desc}</p>
                        <p className="text-xs text-on-surface/30 italic">{detail}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </section>

              {/* AREAS DEL DERECHO */}
              <section id="areas" className="scroll-mt-20">
                <h2 className="font-['Newsreader'] text-2xl font-bold mb-2 text-on-surface">
                  Áreas del Derecho
                </h2>
                <p className="text-on-surface/50 text-sm mb-8">
                  TukiJuris cuenta con 11 agentes especializados, uno por cada área del derecho peruano.
                </p>
                <div className="grid sm:grid-cols-2 gap-3">
                  {LEGAL_AREAS.map((area) => {
                    const Icon = area.icon;
                    const isOpen = expandedArea === area.id;
                    return (
                      <div
                        key={area.id}
                        className="bg-surface-container-low rounded-lg overflow-hidden transition-colors"
                        style={{ border: "1px solid rgba(79,70,51,0.15)" }}
                      >
                        <button
                          onClick={() => setExpandedArea(isOpen ? null : area.id)}
                          className="w-full flex items-center justify-between p-4 text-left hover:bg-surface transition-colors"
                        >
                          <div className="flex items-center gap-3">
                            <Icon className={`w-4 h-4 ${area.color} shrink-0`} />
                            <span className="font-medium text-sm text-on-surface">
                              {area.name}
                            </span>
                          </div>
                          {isOpen ? (
                            <ChevronUp className="w-4 h-4 text-on-surface/30 shrink-0" />
                          ) : (
                            <ChevronDown className="w-4 h-4 text-on-surface/30 shrink-0" />
                          )}
                        </button>
                        {isOpen && (
                          <div
                            className="px-4 pb-4 bg-surface"
                            style={{ borderTop: "1px solid rgba(79,70,51,0.15)" }}
                          >
                            <p className="text-sm text-on-surface/50 mt-3 mb-3">
                              {area.description}
                            </p>
                            <p className="text-[10px] text-on-surface/30 uppercase tracking-[0.15em] mb-2">
                              Consultas de ejemplo
                            </p>
                            <ul className="space-y-1.5">
                              {area.examples.map((ex) => (
                                <li
                                  key={ex}
                                  className="flex items-start gap-2 text-xs text-on-surface/40"
                                >
                                  <CheckCircle2 className="w-3 h-3 text-on-surface/20 shrink-0 mt-0.5" />
                                  {ex}
                                </li>
                              ))}
                            </ul>
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              </section>

              {/* TIPS */}
              <section id="tips" className="scroll-mt-20">
                <h2 className="font-['Newsreader'] text-2xl font-bold mb-2 text-on-surface">
                  Cómo hacer consultas efectivas
                </h2>
                <p className="text-on-surface/50 text-sm mb-8">
                  La calidad de la respuesta depende en gran parte de cómo formulás tu consulta.
                  Estos tips te ayudan a obtener mejores resultados.
                </p>
                <div className="grid sm:grid-cols-2 gap-4">
                  {[
                    {
                      tip: "Sé específico",
                      bad: "¿Qué dice la ley sobre contratos?",
                      good: "¿Qué dice el Art. 1351 del Código Civil sobre la definición de contrato?",
                    },
                    {
                      tip: "Incluí contexto relevante",
                      bad: "¿Me deben pagar?",
                      good: "Trabajo 8 meses y me despidieron. El monto de mi remuneración es S/ 2,500. ¿Tengo derecho a CTS?",
                    },
                    {
                      tip: "Describí los hechos completos",
                      bad: "Me robaron, ¿qué hago?",
                      good: "Me sustrajeron el celular en la calle con amenaza. El valor es S/ 1,500. Quiero denunciar. ¿Cuál es el proceso?",
                    },
                    {
                      tip: "Usá la selección de área",
                      bad: "Dejar que el orquestador elija siempre",
                      good: "Si sabés que tu consulta es laboral, seleccioná 'Laboral' en el sidebar para mayor precisión.",
                    },
                  ].map(({ tip, bad, good }) => (
                    <div
                      key={tip}
                      className="p-4 rounded-lg bg-surface-container-low"
                      style={{ border: "1px solid rgba(79,70,51,0.15)" }}
                    >
                      <div className="flex items-center gap-2 mb-3">
                        <Lightbulb className="w-4 h-4 text-primary" />
                        <span className="text-sm font-semibold text-primary">{tip}</span>
                      </div>
                      <div className="space-y-2">
                        <div
                          className="text-xs text-red-400/80 bg-red-500/5 rounded-lg px-3 py-2"
                          style={{ border: "1px solid rgba(239,68,68,0.1)" }}
                        >
                          <span className="font-medium text-red-400">Evitá:</span>{" "}
                          {bad}
                        </div>
                        <div
                          className="text-xs text-green-400/80 bg-green-500/5 rounded-lg px-3 py-2"
                          style={{ border: "1px solid rgba(16,185,129,0.1)" }}
                        >
                          <span className="font-medium text-green-400">Mejor:</span>{" "}
                          {good}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </section>

              {/* FUNCIONALIDADES */}
              <section id="funcionalidades" className="scroll-mt-20">
                <h2 className="font-['Newsreader'] text-2xl font-bold mb-2 text-on-surface">
                  Funcionalidades
                </h2>
                <p className="text-on-surface/50 text-sm mb-8">
                  TukiJuris es más que un chatbot — es una plataforma completa de asistencia jurídica.
                </p>
                <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
                  {FEATURES.map(({ icon: Icon, title, desc }) => (
                    <div
                      key={title}
                      className="p-4 rounded-lg bg-surface-container-low"
                      style={{ border: "1px solid rgba(79,70,51,0.15)" }}
                    >
                      <div className="w-8 h-8 rounded-lg bg-primary/10 flex items-center justify-center mb-3">
                        <Icon className="w-4 h-4 text-primary" />
                      </div>
                      <h3 className="font-semibold text-sm mb-1.5 text-on-surface">{title}</h3>
                      <p className="text-xs text-on-surface/40 leading-relaxed">{desc}</p>
                    </div>
                  ))}
                </div>
              </section>

              {/* FAQ */}
              <section id="faq" className="scroll-mt-20">
                <h2 className="font-['Newsreader'] text-2xl font-bold mb-2 text-on-surface">
                  Preguntas frecuentes
                </h2>
                <p className="text-on-surface/50 text-sm mb-8">
                  Las respuestas a las preguntas más comunes sobre TukiJuris.
                </p>
                <div className="space-y-2">
                  {FAQ_ITEMS.map((item) => (
                    <FaqItem key={item.q} q={item.q} a={item.a} />
                  ))}
                </div>
              </section>

              {/* SOPORTE */}
              <section
                id="soporte"
                className="scroll-mt-20 p-6 rounded-lg bg-surface-container-low"
                style={{ border: "1px solid rgba(79,70,51,0.15)" }}
              >
                <h2 className="font-['Newsreader'] text-xl font-bold mb-1 text-on-surface">
                  Soporte y contacto
                </h2>
                <p className="text-sm text-on-surface/50 mb-5">
                  Si tenés preguntas que no están en esta guía o encontraste un error, el equipo está
                  disponible para ayudarte.
                </p>
                <div className="flex flex-col sm:flex-row gap-3">
                  <a
                    href="mailto:soporte@tukijuris.net.pe"
                    className="flex items-center gap-2 px-4 py-2.5 rounded-lg bg-primary hover:bg-primary/90 text-background text-sm font-medium transition-colors"
                  >
                    <Mail className="w-4 h-4" />
                    soporte@tukijuris.net.pe
                  </a>
                  <a
                    href="/status"
                    className="flex items-center gap-2 px-4 py-2.5 rounded-lg text-on-surface hover:text-white text-sm font-medium transition-colors"
                    style={{ border: "1px solid rgba(79,70,51,0.15)" }}
                  >
                    <BarChart3 className="w-4 h-4" />
                    Estado del sistema
                    <ExternalLink className="w-3 h-3 ml-auto text-on-surface/30" />
                  </a>
                </div>
                <p className="text-xs text-on-surface/30 mt-4">
                  Tiempo de respuesta habitual: 24-48 horas en días hábiles.
                </p>
              </section>

            </main>
          </div>
        </div>
      </div>
    </AppLayout>
  );
}
