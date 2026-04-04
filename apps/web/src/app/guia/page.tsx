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
  ArrowRight,
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
    bg: "bg-blue-400/10",
    border: "border-blue-400/20",
    description:
      "Contratos, responsabilidad civil, derechos reales, familia y sucesiones.",
    examples: [
      "Art. 1969 del Codigo Civil sobre responsabilidad civil",
      "Requisitos para un contrato de compraventa valido",
      "Plazos de prescripcion en acciones civiles",
    ],
  },
  {
    id: "penal",
    name: "Derecho Penal",
    icon: Shield,
    color: "text-red-400",
    bg: "bg-red-400/10",
    border: "border-red-400/20",
    description:
      "Delitos, penas, proceso penal, medidas cautelares y jurisprudencia del PJ.",
    examples: [
      "Elementos del delito de estafa segun el Codigo Penal",
      "Diferencia entre homicidio culposo y doloso",
      "Plazos de detencion preliminar en Peru",
    ],
  },
  {
    id: "laboral",
    name: "Derecho Laboral",
    icon: Briefcase,
    color: "text-green-400",
    bg: "bg-green-400/10",
    border: "border-green-400/20",
    description:
      "Contratos laborales, beneficios sociales, CTS, despidos y SUNAFIL.",
    examples: [
      "Como se calcula la CTS en Peru?",
      "Requisitos para un despido justificado",
      "Beneficios sociales en contratos a tiempo parcial",
    ],
  },
  {
    id: "tributario",
    name: "Derecho Tributario",
    icon: Landmark,
    color: "text-yellow-400",
    bg: "bg-yellow-400/10",
    border: "border-yellow-400/20",
    description:
      "IGV, Impuesto a la Renta, SUNAT, infracciones tributarias y procedimientos.",
    examples: [
      "Tasa del IGV y excepciones en Peru",
      "Regimenes tributarios para MYPES",
      "Procedimiento de fiscalizacion SUNAT",
    ],
  },
  {
    id: "constitucional",
    name: "Derecho Constitucional",
    icon: Gavel,
    color: "text-purple-400",
    bg: "bg-purple-400/10",
    border: "border-purple-400/20",
    description:
      "Habeas corpus, amparo, inconstitucionalidad, derechos fundamentales y TC.",
    examples: [
      "Cuando procede un habeas corpus?",
      "Diferencia entre amparo e inconstitucionalidad",
      "Jurisprudencia del TC sobre libertad de expresion",
    ],
  },
  {
    id: "administrativo",
    name: "Derecho Administrativo",
    icon: Building2,
    color: "text-orange-400",
    bg: "bg-orange-400/10",
    border: "border-orange-400/20",
    description:
      "Actos administrativos, silencio administrativo, recursos y Ley 27444.",
    examples: [
      "Plazos del silencio administrativo positivo y negativo",
      "Como apelar un acto administrativo",
      "Responsabilidad del Estado por actos administrativos",
    ],
  },
  {
    id: "corporativo",
    name: "Derecho Corporativo",
    icon: ScrollText,
    color: "text-cyan-400",
    bg: "bg-cyan-400/10",
    border: "border-cyan-400/20",
    description:
      "Sociedades comerciales, M&A, gobierno corporativo, LGS y BCRP.",
    examples: [
      "Requisitos para constituir una SAC en Peru",
      "Diferencia entre directorio y junta general",
      "Responsabilidad de socios en SRL",
    ],
  },
  {
    id: "registral",
    name: "Derecho Registral",
    icon: FileCheck,
    color: "text-pink-400",
    bg: "bg-pink-400/10",
    border: "border-pink-400/20",
    description:
      "Registros Publicos, SUNARP, inscripciones, publicidad registral.",
    examples: [
      "Como inscribir una empresa en SUNARP",
      "Principio de prioridad registral",
      "Rectificacion de partidas registrales",
    ],
  },
  {
    id: "comercio_exterior",
    name: "Comercio Exterior",
    icon: Globe,
    color: "text-teal-400",
    bg: "bg-teal-400/10",
    border: "border-teal-400/20",
    description:
      "Aduanas, regimenes aduaneros, SUNAT Aduanas, tratados comerciales.",
    examples: [
      "Regimenes de importacion temporal en Peru",
      "Drawback: requisitos y calculo",
      "Valoracion aduanera segun el acuerdo de la OMC",
    ],
  },
  {
    id: "compliance",
    name: "Compliance",
    icon: Lock,
    color: "text-indigo-400",
    bg: "bg-indigo-400/10",
    border: "border-indigo-400/20",
    description:
      "LAFT, proteccion de datos personales, SAGRILAFT, prevension lavado.",
    examples: [
      "Obligaciones de la Ley 29733 de proteccion de datos",
      "Que empresas deben tener sistema SPLAFT?",
      "Procedimiento de debida diligencia del cliente",
    ],
  },
  {
    id: "competencia",
    name: "Competencia / PI",
    icon: BadgeCheck,
    color: "text-amber-400",
    bg: "bg-amber-400/10",
    border: "border-amber-400/20",
    description:
      "INDECOPI, marcas, patentes, competencia desleal y publicidad.",
    examples: [
      "Como registrar una marca en INDECOPI",
      "Practicas restrictivas de la competencia",
      "Procedimiento por publicidad enganosa",
    ],
  },
];

const FAQ_ITEMS = [
  {
    q: "Es gratis usar TukiJuris?",
    a: "Durante la beta, si — el acceso a la plataforma es gratuito. TukiJuris no cobra por consultas ni incluye modelos de IA. Necesitas traer tu propia clave API de un proveedor (OpenAI, Anthropic, Google AI o DeepSeek). El costo de uso del modelo lo cobra directamente el proveedor.",
  },
  {
    q: "Necesito una clave API para usar TukiJuris?",
    a: "Si. TukiJuris es una plataforma de asistencia legal que se conecta a proveedores de IA como OpenAI, Anthropic o Google. Necesitas tu propia clave API del proveedor que prefieras. Podes configurarla en Configuracion → API Keys. El costo de uso del modelo lo cobra directamente el proveedor, no TukiJuris.",
  },
  {
    q: "TukiJuris reemplaza a un abogado?",
    a: "No. TukiJuris brinda orientacion juridica informativa — te ayuda a entender la normativa, identificar articulos relevantes y analizar tu situacion. No constituye asesoria legal ni reemplaza la consulta con un abogado colegiado para casos especificos o decisiones importantes.",
  },
  {
    q: "Que normativa incluye la base de conocimiento?",
    a: "Incluye: Constitucion Politica del Peru, codigos (Civil, Penal, Procesal Civil, Procesal Penal, Tributario, Laboral), leyes organicas, decretos legislativos y supremos vigentes, jurisprudencia del Tribunal Constitucional e INDECOPI, y normas sectoriales actualizadas.",
  },
  {
    q: "Como debo citar las respuestas de TukiJuris?",
    a: "Las citaciones que incluye el sistema son referenciales. Siempre verifica el texto completo en la fuente oficial: el Diario El Peruano, SPIJ (Sistema Peruano de Informacion Juridica) o el portal del organismo competente antes de usar en documentos legales formales.",
  },
  {
    q: "Puedo usar la API de TukiJuris?",
    a: "Si. La API publica permite consultas, busqueda de normativa y analisis de casos. Sí, TukiJuris ofrece API Keys para integracion. Podes crear y gestionar tus keys desde Configuracion > API Keys. Consultá la documentacion en /docs para endpoints, ejemplos de codigo y limites de uso.",
  },
  {
    q: "Que modelos de IA puedo usar?",
    a: "TukiJuris es compatible con los modelos de OpenAI (GPT-4o, GPT-4o Mini), Anthropic (Claude Sonnet 4, Claude Haiku), Google AI (Gemini 2.5 Flash, Gemini 2.5 Pro) y DeepSeek (DeepSeek Chat, DeepSeek Reasoner). Los modelos disponibles en el selector dependen de que claves API tengas configuradas en Configuracion → API Keys.",
  },
  {
    q: "Mis consultas son privadas?",
    a: "Si. Tus consultas son privadas y no se comparten con terceros. No usamos tus consultas para entrenar modelos de IA. Las organizaciones solo pueden ver el agregado anonimizado de uso de sus miembros, no el contenido de cada consulta.",
  },
  {
    q: "Como reporto un error en una respuesta?",
    a: "Bajo cada respuesta del asistente hay botones de feedback (pulgar arriba / pulgar abajo). Si la respuesta tiene un error, usa el pulgar abajo y podes agregar un comentario describiendo el problema. El equipo revisa todos los reportes.",
  },
  {
    q: "Funciona para derecho de otros paises?",
    a: "No actualmente. TukiJuris esta especializado exclusivamente en derecho peruano. La base de conocimiento, los agentes y los prompts estan disenados para normativa peruana. Para derecho comparado, podes preguntar pero las respuestas tendran menos precision.",
  },
  {
    q: "Puedo invitar a mi equipo?",
    a: "Si. Desde /organizacion podes crear una organizacion, invitar miembros por email y asignar roles (admin, miembro). Las organizaciones tienen un panel de analytics compartido y pueden configurar modelos y preferencias para todo el equipo.",
  },
  {
    q: "Hay limite de consultas?",
    a: "TukiJuris no limita el numero de consultas. El limite real lo impone el proveedor de IA segun tu clave API y plan con ellos. La plataforma cobra solo por acceso, no por consultas.",
  },
  {
    q: "Con que frecuencia se actualiza la normativa?",
    a: "La base de conocimiento se actualiza de dos formas: scrapers automaticos que monitorean el Diario El Peruano y el SPIJ diariamente, y actualizaciones manuales del equipo legal para normas de alta relevancia. Si ves normativa desactualizada, reportalo.",
  },
  {
    q: "Puedo descargar o exportar las respuestas?",
    a: "Si podes copiar el texto de cualquier respuesta. Disponible — haz clic en el ícono de descarga junto a cualquier respuesta del asistente para generar un PDF profesional. Para la API, las respuestas se retornan en JSON que podes integrar en tus propios sistemas.",
  },
  {
    q: "Como cambio de plan?",
    a: "Desde /billing podes ver tu plan actual, el uso del mes y las opciones de upgrade. El cambio es inmediato al confirmar el pago. Si tenes preguntas sobre precios o necesitas un plan corporativo, escribinos a soporte@tukijuris.net.pe.",
  },
  {
    q: "Necesito crear una cuenta para usar TukiJuris?",
    a: "Si, se requiere registro gratuito para acceder a la plataforma. El registro toma menos de un minuto — solo email y contrasena. Esto nos permite guardar tu historial de consultas, preferencias y limites de uso.",
  },
];

const HOW_IT_WORKS = [
  {
    step: 1,
    title: "Escribi tu consulta",
    desc: "Escribe tu pregunta legal en lenguaje natural, tal como se lo preguntarias a un abogado. No necesitas usar terminos tecnicos.",
    detail: "Ej: 'Cuales son los requisitos para despedir a un trabajador de forma justificada?'",
  },
  {
    step: 2,
    title: "Clasificacion automatica",
    desc: "El orquestador analiza tu consulta y la clasifica en el area del derecho correspondiente. Tambien podes seleccionar el area manualmente desde el sidebar.",
    detail: "El clasificador tiene 95%+ de precision en las 11 areas soportadas.",
  },
  {
    step: 3,
    title: "Busqueda de normativa",
    desc: "El sistema busca en la base de conocimiento los articulos, leyes y jurisprudencia mas relevantes usando busqueda semantica + reranking.",
    detail: "Busca en mas de 50,000 fragmentos de normativa peruana.",
  },
  {
    step: 4,
    title: "Respuesta con citaciones",
    desc: "Un agente especializado en el area genera la respuesta en tiempo real, citando las fuentes normativas utilizadas.",
    detail: "Cada respuesta incluye el articulo, norma y organismo de origen.",
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
    title: "Busqueda de normativa",
    desc: "Busca articulos especificos por numero, texto o materia. Accede al texto completo de leyes, codigos y decretos.",
  },
  {
    icon: Scale,
    title: "Analisis de caso",
    desc: "Describe un caso complejo que involucra multiples areas del derecho. El sistema activa agentes especializados en paralelo.",
  },
  {
    icon: FileText,
    title: "Visor de documentos",
    desc: "Lee la normativa completa con navegacion por capitulos y articulos. Busca dentro del documento.",
  },
  {
    icon: Users,
    title: "Organizaciones",
    desc: "Equipos legales con roles, invitaciones, analytics de uso compartido y configuracion centralizada.",
  },
  {
    icon: Code2,
    title: "API para integraciones",
    desc: "API REST publica con autenticacion por API key. Integra TukiJuris en tus propias aplicaciones y flujos de trabajo.",
  },
];

const TOC_LINKS = [
  { href: "#como-funciona", label: "Como funciona" },
  { href: "#areas", label: "Areas del Derecho" },
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
    <div className="bg-[#111116] border border-[#1E1E2A] rounded-xl overflow-hidden">
      <button
        onClick={() => setOpen(!open)}
        className="w-full flex items-center justify-between px-5 py-4 text-left hover:bg-[#1A1A22] transition-colors"
      >
        <span className="text-sm font-medium text-[#F5F5F5] pr-4">{q}</span>
        {open ? (
          <ChevronUp className="w-4 h-4 text-[#EAB308] shrink-0" />
        ) : (
          <ChevronDown className="w-4 h-4 text-[#6B7280] shrink-0" />
        )}
      </button>
      {open && (
        <div className="px-5 pb-5 border-t border-[#1E1E2A]">
          <p className="text-sm text-[#9CA3AF] leading-relaxed pt-4">{a}</p>
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
      <div className="min-h-full text-white">
        <div className="border-b border-[#1E1E2A] px-4 py-4 flex items-center gap-3">
          <HelpCircle className="w-5 h-5 text-[#EAB308]" />
          <h1 className="font-bold text-base">Guía de Uso</h1>
        </div>

        <div className="max-w-6xl mx-auto px-4 py-12 lg:py-16">
        <div className="lg:grid lg:grid-cols-[220px_1fr] lg:gap-12">

          {/* Sidebar TOC — sticky desktop */}
          <aside className="hidden lg:block">
            <div className="sticky top-24 space-y-1">
              <p className="text-xs uppercase tracking-wider text-[#6B7280] mb-3 px-2">
                Contenido
              </p>
              {TOC_LINKS.map((link) => (
                <a
                  key={link.href}
                  href={link.href}
                  className="block px-2 py-1.5 text-sm text-[#6B7280] hover:text-[#EAB308] transition-colors rounded"
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
              {/* Logo */}
              <div className="mb-6">
                <Image
                  src="/brand/logo-full.png"
                  alt="TukiJuris"
                  width={160}
                  height={40}
                  className="h-9 w-auto"
                />
              </div>
              <div className="inline-flex items-center gap-2 bg-[#EAB308]/10 border border-[#EAB308]/20 rounded-full px-3 py-1 text-xs text-[#EAB308] mb-4">
                <HelpCircle className="w-3.5 h-3.5" />
                Documentacion
              </div>
              <h1 className="text-4xl lg:text-5xl font-bold mb-4 leading-tight">
                Guia de uso de{" "}
                <span className="text-[#EAB308]">TukiJuris</span>
              </h1>
              <p className="text-lg text-[#9CA3AF] max-w-2xl leading-relaxed">
                Todo lo que necesitas saber para sacarle el maximo provecho a la
                plataforma juridica inteligente especializada en derecho peruano.
              </p>
            </section>

            {/* COMO FUNCIONA */}
            <section id="como-funciona" className="scroll-mt-20">
              <h2 className="text-2xl font-bold mb-2">Como funciona</h2>
              <p className="text-[#9CA3AF] text-sm mb-8">
                Cada consulta pasa por un proceso de 4 etapas optimizadas para
                derecho peruano.
              </p>
              <div className="space-y-4">
                {HOW_IT_WORKS.map(({ step, title, desc, detail }) => (
                  <div
                    key={step}
                    className="flex gap-4 p-5 rounded-xl bg-[#111116] border border-[#1E1E2A]"
                  >
                    <div className="w-8 h-8 rounded-full bg-[#EAB308]/20 border border-[#EAB308]/30 flex items-center justify-center shrink-0 mt-0.5">
                      <span className="text-xs font-bold text-[#EAB308]">
                        {step}
                      </span>
                    </div>
                    <div>
                      <h3 className="font-semibold text-white mb-1">{title}</h3>
                      <p className="text-sm text-[#9CA3AF] mb-2">{desc}</p>
                      <p className="text-xs text-[#6B7280] italic">{detail}</p>
                    </div>
                  </div>
                ))}
              </div>
            </section>

            {/* AREAS DEL DERECHO */}
            <section id="areas" className="scroll-mt-20">
              <h2 className="text-2xl font-bold mb-2">Areas del Derecho</h2>
              <p className="text-[#9CA3AF] text-sm mb-8">
                TukiJuris cuenta con 11 agentes especializados, uno por cada
                area del derecho peruano.
              </p>
              <div className="grid sm:grid-cols-2 gap-3">
                {LEGAL_AREAS.map((area) => {
                  const Icon = area.icon;
                  const isOpen = expandedArea === area.id;
                  return (
                    <div
                      key={area.id}
                      className={`rounded-xl border transition-colors ${area.border} ${area.bg}`}
                    >
                      <button
                        onClick={() =>
                          setExpandedArea(isOpen ? null : area.id)
                        }
                        className="w-full flex items-center justify-between p-4 text-left"
                      >
                        <div className="flex items-center gap-3">
                          <Icon className={`w-4 h-4 ${area.color} shrink-0`} />
                          <span className="font-medium text-sm">
                            {area.name}
                          </span>
                        </div>
                        {isOpen ? (
                          <ChevronUp className="w-4 h-4 text-[#6B7280] shrink-0" />
                        ) : (
                          <ChevronDown className="w-4 h-4 text-[#6B7280] shrink-0" />
                        )}
                      </button>
                      {isOpen && (
                        <div className="px-4 pb-4 border-t border-[#2A2A35]/30">
                          <p className="text-sm text-[#9CA3AF] mt-3 mb-3">
                            {area.description}
                          </p>
                          <p className="text-xs text-[#6B7280] uppercase tracking-wider mb-2">
                            Consultas de ejemplo
                          </p>
                          <ul className="space-y-1.5">
                            {area.examples.map((ex) => (
                              <li
                                key={ex}
                                className="flex items-start gap-2 text-xs text-[#6B7280]"
                              >
                                <CheckCircle2 className="w-3 h-3 text-[#6B7280] shrink-0 mt-0.5" />
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
              <h2 className="text-2xl font-bold mb-2">
                Como hacer consultas efectivas
              </h2>
              <p className="text-[#9CA3AF] text-sm mb-8">
                La calidad de la respuesta depende en gran parte de como formulas
                tu consulta. Estos tips te ayudan a obtener mejores resultados.
              </p>
              <div className="grid sm:grid-cols-2 gap-4">
                {[
                  {
                    tip: "Se especifico",
                    bad: "Que dice la ley sobre contratos?",
                    good: "Que dice el Art. 1351 del Codigo Civil sobre la definicion de contrato?",
                  },
                  {
                    tip: "Incluye contexto relevante",
                    bad: "Me deben pagar?",
                    good: "Trabajo 8 meses y me despidieron. El monto de mi remuneracion es S/ 2,500. Tengo derecho a CTS?",
                  },
                  {
                    tip: "Describe los hechos completos",
                    bad: "Me robaron, que hago?",
                    good: "Me sustrajeron el celular en la calle con amenaza. El valor es S/ 1,500. Quiero denunciar. Cual es el proceso?",
                  },
                  {
                    tip: "Usa la seleccion de area",
                    bad: "Dejar que el orquestador elija siempre",
                    good: "Si sabes que tu consulta es laboral, selecciona 'Laboral' en el sidebar para mayor precision.",
                  },
                ].map(({ tip, bad, good }) => (
                  <div
                    key={tip}
                    className="p-4 rounded-xl bg-[#111116] border border-[#1E1E2A]"
                  >
                    <div className="flex items-center gap-2 mb-3">
                      <Lightbulb className="w-4 h-4 text-[#EAB308]" />
                      <span className="text-sm font-semibold text-[#EAB308]">
                        {tip}
                      </span>
                    </div>
                    <div className="space-y-2">
                      <div className="text-xs text-red-400/80 bg-red-500/5 border border-red-500/10 rounded-lg px-3 py-2">
                        <span className="font-medium text-red-400">Evita:</span>{" "}
                        {bad}
                      </div>
                      <div className="text-xs text-green-400/80 bg-green-500/5 border border-green-500/10 rounded-lg px-3 py-2">
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
              <h2 className="text-2xl font-bold mb-2">Funcionalidades</h2>
              <p className="text-[#9CA3AF] text-sm mb-8">
                TukiJuris es mas que un chatbot — es una plataforma completa de
                asistencia juridica.
              </p>
              <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
                {FEATURES.map(({ icon: Icon, title, desc }) => (
                  <div
                    key={title}
                    className="p-4 rounded-xl bg-[#111116] border border-[#1E1E2A]"
                  >
                    <div className="w-8 h-8 rounded-lg bg-[#EAB308]/10 flex items-center justify-center mb-3">
                      <Icon className="w-4 h-4 text-[#EAB308]" />
                    </div>
                    <h3 className="font-semibold text-sm mb-1.5">{title}</h3>
                    <p className="text-xs text-[#6B7280] leading-relaxed">{desc}</p>
                  </div>
                ))}
              </div>
            </section>

            {/* FAQ */}
            <section id="faq" className="scroll-mt-20">
              <h2 className="text-2xl font-bold mb-2">
                Preguntas frecuentes
              </h2>
              <p className="text-[#9CA3AF] text-sm mb-8">
                Las respuestas a las preguntas mas comunes sobre TukiJuris.
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
              className="scroll-mt-20 p-6 rounded-2xl bg-[#2C3E50]/20 border border-[#2C3E50]/30"
            >
              <h2 className="text-xl font-bold mb-1">Soporte y contacto</h2>
              <p className="text-sm text-[#9CA3AF] mb-5">
                Si tenes preguntas que no estan en esta guia o encontraste un
                error, el equipo esta disponible para ayudarte.
              </p>
              <div className="flex flex-col sm:flex-row gap-3">
                <a
                  href="mailto:soporte@tukijuris.net.pe"
                  className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-[#EAB308] hover:bg-[#EAB308]/90 text-[#0A0A0F] text-sm font-medium transition-colors"
                >
                  <Mail className="w-4 h-4" />
                  soporte@tukijuris.net.pe
                </a>
                <a
                  href="/status"
                  className="flex items-center gap-2 px-4 py-2.5 rounded-xl border border-[#2A2A35] text-[#F5F5F5] hover:border-[#EAB308]/30 hover:text-white text-sm font-medium transition-colors"
                >
                  <BarChart3 className="w-4 h-4" />
                  Estado del sistema
                  <ExternalLink className="w-3 h-3 ml-auto text-[#6B7280]" />
                </a>
              </div>
              <p className="text-xs text-[#6B7280] mt-4">
                Tiempo de respuesta habitual: 24-48 horas en dias habiles.
              </p>
            </section>

          </main>
        </div>
        </div>
      </div>
    </AppLayout>
  );
}
